resource "aws_security_group" "frontend_sg" {
  name        = "${var.name_prefix}-frontend-sg1"
  description = "SIBU QA Frontend SG"
  vpc_id      = data.aws_vpc.default.id

  # HTTP for the frontend
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH only via bastion
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-frontend-sg"
  }
}

resource "aws_instance" "frontend" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.app_instance_type
  key_name               = aws_key_pair.qa_sibu.key_name
  vpc_security_group_ids = [aws_security_group.frontend_sg.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  user_data = templatefile("${path.module}/../user_data/frontend.sh.tftpl", {})

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
  }

  tags = {
    Name = "${var.name_prefix}-frontend"
  }
}