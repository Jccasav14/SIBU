resource "aws_instance" "data" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.data_instance_type
  key_name               = aws_key_pair.qa_sibu.key_name
  vpc_security_group_ids = [aws_security_group.sibu_sg.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  user_data = templatefile("${path.module}/../../user_data/data.sh.tftpl", {})

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
  }

  tags = {
    Name = "${var.name_prefix}-data"
  }
}
