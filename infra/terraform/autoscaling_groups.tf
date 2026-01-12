# Auto Scaling Groups for each microservice
# Fix: exclude subnets in us-east-1e because t3.micro is not supported there (AWS Academy common restriction)

# NOTE: data.aws_subnets.default and data.aws_vpc.default already exist in network.tf
# We only need to read each subnet to know its AZ and filter.

data "aws_subnet" "all_default" {
  for_each = toset(data.aws_subnets.default.ids)
  id       = each.value
}

locals {
  allowed_azs = toset([
    "us-east-1a",
    "us-east-1b",
    "us-east-1c",
    "us-east-1d",
    "us-east-1f",
  ])

  asg_subnet_ids = [
    for s in data.aws_subnet.all_default : s.id
    if contains(local.allowed_azs, s.availability_zone)
  ]
}

resource "aws_autoscaling_group" "auth" {
  name                      = "${var.name_prefix}-auth-asg"
  max_size                  = 2
  min_size                  = 1
  desired_capacity          = 1
  health_check_type         = "ELB"
  health_check_grace_period = 600

  vpc_zone_identifier = local.asg_subnet_ids

  launch_template {
    id      = aws_launch_template.auth.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.tg_auth.arn]

  tag { key = "Name" value = "${var.name_prefix}-auth" propagate_at_launch = true }
  tag { key = "App"  value = "sibu"               propagate_at_launch = true }
  tag { key = "Env"  value = "qa"                 propagate_at_launch = true }
  tag { key = "Svc"  value = "auth"               propagate_at_launch = true }
}

resource "aws_autoscaling_group" "users" {
  name                      = "${var.name_prefix}-users-asg"
  max_size                  = 2
  min_size                  = 1
  desired_capacity          = 1
  health_check_type         = "ELB"
  health_check_grace_period = 600

  vpc_zone_identifier = local.asg_subnet_ids

  launch_template {
    id      = aws_launch_template.users.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.tg_users.arn]

  tag { key = "Name" value = "${var.name_prefix}-users" propagate_at_launch = true }
  tag { key = "App"  value = "sibu"                propagate_at_launch = true }
  tag { key = "Env"  value = "qa"                  propagate_at_launch = true }
  tag { key = "Svc"  value = "users"               propagate_at_launch = true }
}

resource "aws_autoscaling_group" "cases" {
  name                      = "${var.name_prefix}-cases-asg"
  max_size                  = 2
  min_size                  = 1
  desired_capacity          = 1
  health_check_type         = "ELB"
  health_check_grace_period = 600

  vpc_zone_identifier = local.asg_subnet_ids

  launch_template {
    id      = aws_launch_template.cases.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.tg_cases.arn]

  tag { key = "Name" value = "${var.name_prefix}-cases" propagate_at_launch = true }
  tag { key = "App"  value = "sibu"               propagate_at_launch = true }
  tag { key = "Env"  value = "qa"                 propagate_at_launch = true }
  tag { key = "Svc"  value = "cases"              propagate_at_launch = true }
}

resource "aws_autoscaling_group" "appointments" {
  name                      = "${var.name_prefix}-appointments-asg"
  max_size                  = 2
  min_size                  = 1
  desired_capacity          = 1
  health_check_type         = "ELB"
  health_check_grace_period = 600

  vpc_zone_identifier = local.asg_subnet_ids

  launch_template {
    id      = aws_launch_template.appointments.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.tg_appointments.arn]

  tag { key = "Name" value = "${var.name_prefix}-appointments" propagate_at_launch = true }
  tag { key = "App"  value = "sibu"                     propagate_at_launch = true }
  tag { key = "Env"  value = "qa"                       propagate_at_launch = true }
  tag { key = "Svc"  value = "appointments"             propagate_at_launch = true }
}

resource "aws_autoscaling_group" "audit" {
  name                      = "${var.name_prefix}-audit-asg"
  max_size                  = 2
  min_size                  = 1
  desired_capacity          = 1
  health_check_type         = "ELB"
  health_check_grace_period = 600

  vpc_zone_identifier = local.asg_subnet_ids

  launch_template {
    id      = aws_launch_template.audit.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.tg_audit.arn]

  tag { key = "Name" value = "${var.name_prefix}-audit" propagate_at_launch = true }
  tag { key = "App"  value = "sibu"               propagate_at_launch = true }
  tag { key = "Env"  value = "qa"                 propagate_at_launch = true }
  tag { key = "Svc"  value = "audit"              propagate_at_launch = true }
}

resource "aws_autoscaling_group" "reports" {
  name                      = "${var.name_prefix}-reports-asg"
  max_size                  = 2
  min_size                  = 1
  desired_capacity          = 1
  health_check_type         = "ELB"
  health_check_grace_period = 600

  vpc_zone_identifier = local.asg_subnet_ids

  launch_template {
    id      = aws_launch_template.reports.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.tg_reports.arn]

  tag { key = "Name" value = "${var.name_prefix}-reports" propagate_at_launch = true }
  tag { key = "App"  value = "sibu"                 propagate_at_launch = true }
  tag { key = "Env"  value = "qa"                   propagate_at_launch = true }
  tag { key = "Svc"  value = "reports"              propagate_at_launch = true }
}

resource "aws_autoscaling_group" "admin" {
  name                      = "${var.name_prefix}-admin-asg"
  max_size                  = 2
  min_size                  = 1
  desired_capacity          = 1
  health_check_type         = "ELB"
  health_check_grace_period = 600

  vpc_zone_identifier = local.asg_subnet_ids

  launch_template {
    id      = aws_launch_template.admin.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.tg_admin.arn]

  tag { key = "Name" value = "${var.name_prefix}-admin" propagate_at_launch = true }
  tag { key = "App"  value = "sibu"               propagate_at_launch = true }
  tag { key = "Env"  value = "qa"                 propagate_at_launch = true }
  tag { key = "Svc"  value = "admin"              propagate_at_launch = true }
}
