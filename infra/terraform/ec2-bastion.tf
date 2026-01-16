resource "aws_instance" "bastion" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.app_instance_type
  key_name               = aws_key_pair.qa_sibu.key_name
  vpc_security_group_ids = [aws_security_group.bastion_sg.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  # Lightweight bastion: only SSH jump host
  user_data = <<-EOF
    #!/bin/bash
    set -eux
    dnf update -y
    dnf install -y htop nmap-ncat
  EOF

  root_block_device {
  volume_size           = 30
  volume_type           = "gp3"
  delete_on_termination = true
  }


  tags = {
    Name = "${var.name_prefix}-bastion"
  }
}
