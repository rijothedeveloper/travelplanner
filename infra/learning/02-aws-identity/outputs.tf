output "aws_identity" {
  description = "Identity used by the AWS provider."

  value = {
    account_id = data.aws_caller_identity.current.account_id
    arn        = data.aws_caller_identity.current.arn
  }
}

output "deployment_configuration" {
  description = "Calculated configuration for this environment."

  value = {
    region      = var.aws_region
    name_prefix = local.name_prefix
    tags        = local.common_tags
  }
}

output "ecr_repository_url" {
  description = "URL of the existing Travel Planner ECR repository."
  value       = aws_ecr_repository.travel_planner.repository_url
}

output "network_ids" {
  description = "Imported Travel Planner network resources."

  value = {
    vpc_id            = aws_vpc.travel_lab.id
    public_subnet_id  = aws_subnet.travel-subnet-public-A.id
    private_subnet_id = aws_subnet.travel-subnet-private-A.id
  }
}