output "data_private_ip" {
  value = aws_instance.data.private_ip
}

output "data_public_ip" {
  value = aws_instance.data.public_ip
}

output "service_public_ips" {
  value = {
    authUsers    = aws_instance.authUsers.public_ip
    cases        = aws_instance.cases.public_ip
    appointments = aws_instance.appointments.public_ip
    audit        = aws_instance.audit.public_ip
    # Admin + Reports now share the same EC2
    reports      = aws_instance.admin_reports.public_ip
    notifications = aws_instance.notifications.public_ip
    admin        = aws_instance.admin_reports.public_ip
    frontend     = aws_instance.frontend.public_ip
    bastion      = aws_instance.bastion.public_ip
  }
}
