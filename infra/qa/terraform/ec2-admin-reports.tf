resource "aws_instance" "admin_reports" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.app_instance_type
  key_name               = aws_key_pair.qa_sibu.key_name
  vpc_security_group_ids = [aws_security_group.sibu_sg.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  # Runs BOTH Admin (host 8006) and Reports (host 8005) on the same EC2
  user_data = templatefile("${path.module}/../user_data/admin_reports.sh.tftpl", {
    data_ip              = aws_instance.data.private_ip
    admin_host_port      = 8006
    admin_container_port = 8008
    reports_host_port    = 8005
    reports_container_port = 8007
  })
#
  depends_on = [aws_instance.data]

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
  }

  tags = {
    Name = "${var.name_prefix}-admin-reports"
  }
}
