resource "aws_instance" "notifications" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.app_instance_type
  key_name               = aws_key_pair.qa_sibu.key_name
  vpc_security_group_ids = [aws_security_group.sibu_sg.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  # Runs 3 services on a single instance (notifications + claims + coverage)
  user_data = templatefile("${path.module}/../user_data/insurance.sh.tftpl", {
    data_ip = aws_instance.data.private_ip
  })

  depends_on = [aws_instance.data]

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
  }

  tags = {
    Name = "${var.name_prefix}-insurance"
  }
}
