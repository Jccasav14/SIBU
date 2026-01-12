output "data_private_ip" {
  value = aws_instance.data.private_ip
}

output "data_public_ip" {
  value = aws_instance.data.public_ip
}


output "asg_names" {
  value = {
    auth         = aws_autoscaling_group.auth.name
    users        = aws_autoscaling_group.users.name
    cases        = aws_autoscaling_group.cases.name
    appointments = aws_autoscaling_group.appointments.name
    audit        = aws_autoscaling_group.audit.name
    reports      = aws_autoscaling_group.reports.name
    admin        = aws_autoscaling_group.admin.name
  }
}

output "alb_dns_name" {
  value = aws_lb.sibu_alb.dns_name
}
