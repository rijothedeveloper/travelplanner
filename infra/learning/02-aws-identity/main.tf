locals {
  project     = "travel-planner"
  name_prefix = "${local.project}-${var.environment}"

  common_tags = {
    Project     = local.project
    Environment = var.environment
    Owner       = trimspace(var.owner)
    ManagedBy   = "Terraform"
  }
}

provider "aws" {
  profile = "travel-terraform"
  region  = var.aws_region

  allowed_account_ids = [var.expected_account_id]

  default_tags {
    tags = local.common_tags
  }
}

provider "aws" {
  alias = "adoption"

  profile = "travel-terraform"
  region  = var.aws_region

  allowed_account_ids = [var.expected_account_id]
}

data "aws_caller_identity" "current" {}