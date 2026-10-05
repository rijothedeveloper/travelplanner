variable "expected_account_id" {
  description = "AWS account permitted for this configuration."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^[0-9]{12}$", var.expected_account_id))
    error_message = "Provide a 12-digit AWS account ID."
  }
}

variable "aws_region" {
  description = "AWS region for the learning deployment."
  type        = string
  default     = "us-west-2"
  nullable    = false

  validation {
    condition     = var.aws_region == "us-west-2"
    error_message = "This learning configuration currently supports us-west-2."
  }
}

variable "environment" {
  description = "Environment label."
  type        = string
  default     = "dev"
  nullable    = false

  validation {
    condition     = contains(["dev", "staging"], var.environment)
    error_message = "Environment must be dev or staging."
  }
}

variable "owner" {
  description = "Person or team responsible for the deployment."
  type        = string
  nullable    = false

  validation {
    condition     = length(trimspace(var.owner)) > 0
    error_message = "Owner must not be empty."
  }
}