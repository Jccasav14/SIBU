resource "aws_instance" "gateway" {
  ami           = data.aws_ami.al2023.id
  instance_type = var.app_instance_type
  key_name      = aws_key_pair.qa_sibu.key_name

  # Gateway is the only public entrypoint for the APIs (HTTP 80)
  vpc_security_group_ids = [aws_security_group.gateway_sg.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  user_data = templatefile("${path.module}/../user_data/gateway.sh.tftpl", {
    authusers_ip          = aws_instance.authUsers.private_ip
    appointments_cases_ip = aws_instance.appointments_cases.private_ip
    audit_ip              = aws_instance.audit.private_ip
    reports_ip            = aws_instance.reports.private_ip
    insurance_ip          = aws_instance.notifications.private_ip
    admin_ip              = aws_instance.admin.private_ip
  })

  depends_on = [
    aws_instance.authUsers,
    aws_instance.appointments_cases,
    aws_instance.audit,
    aws_instance.reports,
    aws_instance.notifications,
    aws_instance.admin,
  ]

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
  
  }

  tags = {
    Name = "${var.name_prefix}-gateway"
  }
}
