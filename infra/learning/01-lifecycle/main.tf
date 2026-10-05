terraform {
  required_version = ">= 1.4.0, < 2.0.0"
}

variable "environment" {
  type        = string
  description = "Environment label for this local exercise."
  default     = "staging"

  validation {
    condition     = contains(["dev", "staging"], var.environment)
    error_message = "Environment must be dev or staging."
  }
}

resource "terraform_data" "travel_planner" {
  input = {
    application = "travel-planner"
    environment = var.environment
  }
}

output "deployment_description" {
  value = terraform_data.travel_planner.output
}