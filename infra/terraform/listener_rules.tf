# Path-based routing rules
# Examples:
#   http://<ALB_DNS>/auth/...
#   http://<ALB_DNS>/users/...
#
# If your FastAPI routes DON'T include those prefixes, you have 2 options:
# 1) Update your services to use a prefix (recommended for microservices)
# 2) Change the conditions below to match your real paths

resource "aws_lb_listener_rule" "auth" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_auth.arn
  }

  condition {
    path_pattern {
      values = ["/auth*", "/auth/*"]
    }
  }
}

resource "aws_lb_listener_rule" "users" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_users.arn
  }

  condition {
    path_pattern {
      values = ["/users*", "/users/*"]
    }
  }
}

resource "aws_lb_listener_rule" "cases" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 30

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_cases.arn
  }

  condition {
    path_pattern {
      values = ["/cases*", "/cases/*"]
    }
  }
}

resource "aws_lb_listener_rule" "appointments" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 40

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_appointments.arn
  }

  condition {
    path_pattern {
      values = ["/appointments*", "/appointments/*", "/appt*", "/appt/*"]
    }
  }
}

resource "aws_lb_listener_rule" "audit" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 50

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_audit.arn
  }

  condition {
    path_pattern {
      values = ["/audit*", "/audit/*", "/audit-log*", "/audit-log/*"]
    }
  }
}

resource "aws_lb_listener_rule" "reports" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 60

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_reports.arn
  }

  condition {
    path_pattern {
      values = ["/reports*", "/reports/*"]
    }
  }
}

resource "aws_lb_listener_rule" "admin" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 70

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_admin.arn
  }

  condition {
    path_pattern {
      values = ["/admin*", "/admin/*"]
    }
  }
}
