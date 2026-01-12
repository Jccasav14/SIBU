resource "aws_security_group" "sibu_sg" {
  name        = "${var.name_prefix}-sg1"
  description = "SIBU QA SG"
  vpc_id      = data.aws_vpc.default.id

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP APIs (Auth 8000, Users 8001, Cases 8002, Appointments 8003, Audit 8004, Reports 8005, Admin 8006)
  # Only allow traffic from the ALB
  ingress {
    from_port       = 8000
    to_port         = 8006
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }
# Postgres (only inside VPC)
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  # Kafka (only inside VPC)
  ingress {
    from_port   = 29092
    to_port     = 29092
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  # Zookeeper (only inside VPC)
  ingress {
    from_port   = 2181
    to_port     = 2181
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-sg"
  }

  # ICMP inside VPC (REQUIRED for ping / network debug)
  ingress {
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }


}
