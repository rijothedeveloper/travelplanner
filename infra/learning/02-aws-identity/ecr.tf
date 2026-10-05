resource "aws_ecr_repository" "travel_planner" {
  provider = aws.adoption

  name                 = "travel-planner"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false

  encryption_configuration {
    encryption_type = "AES256"
  }

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = {}

  lifecycle {
    prevent_destroy = true
  }
}