output "data_private_ip" {
  value = aws_instance.data.private_ip
}

output "data_public_ip" {
  value = aws_instance.data.public_ip
}

output "service_public_ips" {
  value = {
    authUsers    = aws_instance.authUsers.public_ip
    # cases + appointments now share the same EC2 instance
    cases        = aws_instance.appointments_cases.public_ip
    appointments = aws_instance.appointments_cases.public_ip
    audit        = aws_instance.audit.public_ip
    reports      = aws_instance.reports.public_ip
    notifications = aws_instance.notifications.public_ip
    admin        = aws_instance.admin.public_ip
    bastion      = aws_instance.bastion.public_ip
  }
}
