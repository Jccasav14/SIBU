# One target group per microservice (instance targets).
# IMPORTANT: Ensure each service responds 200 on /health (recommended).
# If you don't have /health, change health_check.path to /docs or /.

resource "aws_lb_target_group" "tg_auth" {
  name        = "${var.name_prefix}-tg-auth"
  port        = 8000
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    enabled             = true
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    path                = "/auth/docs"
    matcher             = "200-399"
  }
}

resource "aws_lb_target_group" "tg_users" {
  name        = "${var.name_prefix}-tg-users"
  port        = 8001
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    enabled             = true
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    path                = "/users/docs"
    matcher             = "200-399"
  }
}

resource "aws_lb_target_group" "tg_cases" {
  name        = "${var.name_prefix}-tg-cases"
  port        = 8002
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    enabled             = true
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    path                = "/cases/docs"
    matcher             = "200-399"
  }
}

resource "aws_lb_target_group" "tg_appointments" {
  name        = "${var.name_prefix}-tg-appt"
  port        = 8003
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    enabled             = true
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    path                = "/appointments/docs"
    matcher             = "200-399"
  }
}

resource "aws_lb_target_group" "tg_audit" {
  name        = "${var.name_prefix}-tg-audit"
  port        = 8004
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    enabled             = true
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    path                = "/audit/docs"
    matcher             = "200-399"
  }
}

resource "aws_lb_target_group" "tg_reports" {
  name        = "${var.name_prefix}-tg-reports"
  port        = 8005
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    enabled             = true
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    path                = "/reports/docs"
    matcher             = "200-399"
  }
}

resource "aws_lb_target_group" "tg_admin" {
  name        = "${var.name_prefix}-tg-admin"
  port        = 8006
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    enabled             = true
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    path                = "/admin/docs"
    matcher             = "200-399"
  }
}

# Attach EC2 instances to their target groups






