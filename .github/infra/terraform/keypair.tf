resource "aws_key_pair" "qa_sibu" {
  key_name   = "${var.name_prefix}-key"
  public_key = file("${path.module}/../keys/qa-sibu.pub")
}
