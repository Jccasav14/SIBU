variable "aws_region" {
  type    = string
  default = "us-east-1"
}

# Change if you want different instance sizes
variable "app_instance_type" {
  type    = string
  default = "t3.micro"
}

variable "data_instance_type" {
  type    = string
  default = "t3.small"
}

variable "name_prefix" {
  type    = string
  default = "sibu-prod"
}

# PROD: Frontend Auto Scaling Group sizing
variable "frontend_asg_min" {
  type    = number
  default = 1
}

variable "frontend_asg_desired" {
  type    = number
  default = 2
}

variable "frontend_asg_max" {
  type    = number
  default = 3
}
