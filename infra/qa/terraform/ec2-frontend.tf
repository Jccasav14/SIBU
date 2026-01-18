resource "aws_security_group" "frontend_sg" {
  name        = "${var.name_prefix}-frontend-sg1"
  description = "SIBU QA Frontend SG"
  vpc_id      = data.aws_vpc.default.id

  # HTTP for the frontend
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH only via bastion
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

resource "aws_instance" "frontend" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.app_instance_type
  key_name               = aws_key_pair.qa_sibu.key_name
  vpc_security_group_ids = [aws_security_group.frontend_sg.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  user_data = templatefile("${path.module}/../../user_data/frontend.sh.tftpl", {
    auth_users_ip   = aws_instance.authUsers.private_ip
    cases_ip        = aws_instance.cases.private_ip
    appointments_ip = aws_instance.appointments.private_ip
    audit_ip        = aws_instance.audit.private_ip
    admin_reports_ip = aws_instance.admin_reports.private_ip
    insurance_ip    = aws_instance.notifications.private_ip
    # Docker image/tag to deploy
    frontend_image  = "jccasav/sibu-front:qa"
  })

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
  }

  tags = {
    Name = "${var.name_prefix}-frontend"
  }
}