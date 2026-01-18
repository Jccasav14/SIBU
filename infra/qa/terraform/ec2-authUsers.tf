resource "aws_instance" "authUsers" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.app_instance_type
  key_name               = aws_key_pair.qa_sibu.key_name
  vpc_security_group_ids = [aws_security_group.sibu_sg.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  # Runs BOTH containers on the same host:
  # - Auth  -> host port 8000
  # - Users -> host port 8001
  user_data = templatefile("${path.module}/../../user_data/authUsers.sh.tftpl", {
    data_ip = aws_instance.data.private_ip
  })

  depends_on = [aws_instance.data]

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
  }

  tags = {
    Name = "${var.name_prefix}-authUsers"
  }
}
