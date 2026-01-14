output "data_private_ip" {
  value = aws_instance.data.private_ip
}

output "data_public_ip" {
  value = aws_instance.data.public_ip
}

output "service_public_ips" {
  value = {
    auth         = aws_instance.auth.public_ip
    users        = aws_instance.users.public_ip
    cases        = aws_instance.cases.public_ip
    appointments = aws_instance.appointments.public_ip
    audit        = aws_instance.audit.public_ip
    reports      = aws_instance.reports.public_ip
    admin        = aws_instance.admin.public_ip
  }
}
