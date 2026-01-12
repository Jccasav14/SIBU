# Launch Templates for each microservice

resource "aws_launch_template" "auth" {
  name_prefix   = "${var.name_prefix}-auth-lt-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.app_instance_type
  key_name      = aws_key_pair.qa_sibu.key_name

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.sibu_sg.id]
  }

  user_data = base64encode(templatefile("${path.module}/../user_data/auth.sh.tftpl", {
    data_ip = aws_instance.data.private_ip
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type = "gp3"
      volume_size = 20
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.name_prefix}-auth"
      App  = "sibu"
      Env  = "qa"
      Svc  = "auth"
    }
  }
}

resource "aws_launch_template" "users" {
  name_prefix   = "${var.name_prefix}-users-lt-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.app_instance_type
  key_name      = aws_key_pair.qa_sibu.key_name

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.sibu_sg.id]
  }

  user_data = base64encode(templatefile("${path.module}/../user_data/users.sh.tftpl", {
    data_ip = aws_instance.data.private_ip
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type = "gp3"
      volume_size = 20
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.name_prefix}-users"
      App  = "sibu"
      Env  = "qa"
      Svc  = "users"
    }
  }
}

resource "aws_launch_template" "cases" {
  name_prefix   = "${var.name_prefix}-cases-lt-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.app_instance_type
  key_name      = aws_key_pair.qa_sibu.key_name

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.sibu_sg.id]
  }

  user_data = base64encode(templatefile("${path.module}/../user_data/cases.sh.tftpl", {
    data_ip = aws_instance.data.private_ip
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type = "gp3"
      volume_size = 20
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.name_prefix}-cases"
      App  = "sibu"
      Env  = "qa"
      Svc  = "cases"
    }
  }
}

resource "aws_launch_template" "appointments" {
  name_prefix   = "${var.name_prefix}-appointments-lt-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.app_instance_type
  key_name      = aws_key_pair.qa_sibu.key_name

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.sibu_sg.id]
  }

  user_data = base64encode(templatefile("${path.module}/../user_data/appointments.sh.tftpl", {
    data_ip = aws_instance.data.private_ip
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type = "gp3"
      volume_size = 20
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.name_prefix}-appointments"
      App  = "sibu"
      Env  = "qa"
      Svc  = "appointments"
    }
  }
}

resource "aws_launch_template" "audit" {
  name_prefix   = "${var.name_prefix}-audit-lt-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.app_instance_type
  key_name      = aws_key_pair.qa_sibu.key_name

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.sibu_sg.id]
  }

  user_data = base64encode(templatefile("${path.module}/../user_data/audit.sh.tftpl", {
    data_ip = aws_instance.data.private_ip
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type = "gp3"
      volume_size = 20
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.name_prefix}-audit"
      App  = "sibu"
      Env  = "qa"
      Svc  = "audit"
    }
  }
}

resource "aws_launch_template" "reports" {
  name_prefix   = "${var.name_prefix}-reports-lt-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.app_instance_type
  key_name      = aws_key_pair.qa_sibu.key_name

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.sibu_sg.id]
  }

  user_data = base64encode(templatefile("${path.module}/../user_data/reports.sh.tftpl", {
    data_ip = aws_instance.data.private_ip
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type = "gp3"
      volume_size = 20
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.name_prefix}-reports"
      App  = "sibu"
      Env  = "qa"
      Svc  = "reports"
    }
  }
}

resource "aws_launch_template" "admin" {
  name_prefix   = "${var.name_prefix}-admin-lt-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.app_instance_type
  key_name      = aws_key_pair.qa_sibu.key_name

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.sibu_sg.id]
  }

  user_data = base64encode(templatefile("${path.module}/../user_data/admin.sh.tftpl", {
    data_ip = aws_instance.data.private_ip
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type = "gp3"
      volume_size = 20
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.name_prefix}-admin"
      App  = "sibu"
      Env  = "qa"
      Svc  = "admin"
    }
  }
}
