# Basic CPU target tracking policies (optional)

resource "aws_autoscaling_policy" "auth_cpu" {
  name                   = "${var.name_prefix}-auth-cpu"
  autoscaling_group_name = aws_autoscaling_group.auth.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}

resource "aws_autoscaling_policy" "users_cpu" {
  name                   = "${var.name_prefix}-users-cpu"
  autoscaling_group_name = aws_autoscaling_group.users.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}

resource "aws_autoscaling_policy" "cases_cpu" {
  name                   = "${var.name_prefix}-cases-cpu"
  autoscaling_group_name = aws_autoscaling_group.cases.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}

resource "aws_autoscaling_policy" "appointments_cpu" {
  name                   = "${var.name_prefix}-appointments-cpu"
  autoscaling_group_name = aws_autoscaling_group.appointments.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}

resource "aws_autoscaling_policy" "audit_cpu" {
  name                   = "${var.name_prefix}-audit-cpu"
  autoscaling_group_name = aws_autoscaling_group.audit.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}

resource "aws_autoscaling_policy" "reports_cpu" {
  name                   = "${var.name_prefix}-reports-cpu"
  autoscaling_group_name = aws_autoscaling_group.reports.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}

resource "aws_autoscaling_policy" "admin_cpu" {
  name                   = "${var.name_prefix}-admin-cpu"
  autoscaling_group_name = aws_autoscaling_group.admin.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}
