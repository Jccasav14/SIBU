resource "aws_instance" "coverage" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.app_instance_type
  key_name               = aws_key_pair.qa_sibu.key_name
  vpc_security_group_ids = [aws_security_group.sibu_sg.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  user_data = <<EOF
#!/bin/bash
set -euxo pipefail
echo "BOOT OK $(date -Is)" | tee /var/log/user-data-noop.log
# No-op: instance created intentionally empty. Service will be added later via Terraform user_data update.
EOF

  instance_initiated_shutdown_behavior = "stop"
  disable_api_termination              = true

  depends_on = [aws_instance.claims]

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
  }

  tags = {
    Name = "${var.name_prefix}-coverage"
  }
}
