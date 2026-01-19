#############################################
# PROD ONLY: Frontend behind ALB + ASG
# - Public entrypoint: ALB DNS
# - Instances: Auto Scaling Group (Amazon Linux 2023) running the frontend container
#############################################

# Public ALB SG: allow HTTP from the internet
resource "aws_security_group" "alb_frontend_sg" {
  name        = "${var.name_prefix}-alb-frontend-sg"
  description = "ALB SG for ${var.name_prefix} frontend"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-alb-frontend-sg"
  }
}

# Frontend instances SG: only allow HTTP from the ALB
resource "aws_security_group" "frontend_sg" {
  name        = "${var.name_prefix}-frontend-sg1"
  description = "Frontend SG for ${var.name_prefix} (only from ALB)"
  vpc_id      = data.aws_vpc.default.id

  # HTTP from ALB (normal path)
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_frontend_sg.id]
  }

  # TEMP (debug / compatibility): allow direct access to instances via Public IP too.
  # You can remove this later and keep only the ALB.
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH only via bastion (kept like QA)
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-frontend-sg"
  }
}

# Application Load Balancer
resource "aws_lb" "frontend" {
  name               = "${var.name_prefix}-frontend-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_frontend_sg.id]

  # ALB needs at least 2 subnets (different AZs). Default VPC has them.
  subnets = slice(data.aws_subnets.default.ids, 0, 2)

  tags = {
    Name = "${var.name_prefix}-frontend-alb"
  }
}

resource "aws_lb_target_group" "frontend" {
  name        = "${var.name_prefix}-frontend-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "instance"

  health_check {
    protocol            = "HTTP"
    path                = "/"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name = "${var.name_prefix}-frontend-tg"
  }
}

resource "aws_lb_listener" "frontend_http" {
  load_balancer_arn = aws_lb.frontend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# Launch Template for frontend instances
resource "aws_launch_template" "frontend" {
  name_prefix   = "${var.name_prefix}-frontend-lt-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.app_instance_type
  key_name      = aws_key_pair.qa_sibu.key_name

  # Ensure instances get a public IP in default VPC public subnets
  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.frontend_sg.id]
  }

  user_data = base64encode(templatefile("${path.module}/../user_data/frontend.sh.tftpl", {
    auth_users_ip    = aws_instance.authUsers.private_ip
    cases_ip         = aws_instance.cases.private_ip
    appointments_ip  = aws_instance.appointments.private_ip
    audit_ip         = aws_instance.audit.private_ip
    admin_reports_ip = aws_instance.admin_reports.private_ip
    insurance_ip     = aws_instance.notifications.private_ip
    # For now we keep QA tag as you requested
    frontend_image   = "jccasav/sibu-front:qa"
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type           = "gp3"
      volume_size           = 30
      delete_on_termination = true
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.name_prefix}-frontend"
    }
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "frontend" {
  name                = "${var.name_prefix}-frontend-asg"
  max_size            = var.frontend_asg_max
  min_size            = var.frontend_asg_min
  desired_capacity    = var.frontend_asg_desired
  vpc_zone_identifier = slice(data.aws_subnets.default.ids, 0, 2)

  health_check_type         = "ELB"
  health_check_grace_period = 120

  launch_template {
    id      = aws_launch_template.frontend.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.frontend.arn]

  tag {
    key                 = "Name"
    value               = "${var.name_prefix}-frontend"
    propagate_at_launch = true
  }
}
