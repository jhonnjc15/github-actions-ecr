variable "aws_region" { type = string }
variable "aws_account_id" { type = string }

variable "ecr_repo" { type = string }
variable "lambda_name" { type = string }
variable "state_machine_name" { 
  type = string 
}
variable "schedule_name" { 
  type = string 
}
variable "schedule_expression" { 
  type = string 
}

# Bootstrap: primera vez apunta a latest (luego el workflow lo cambia a sha)
variable "image_tag" {
  type    = string
  default = "latest"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev|qa)"
}

variable "stack_id" {
  type        = string
  description = "Unique stack identifier (from config id)."
}

variable "lambda_role_name" {
  type        = string
  description = "Pre-created IAM role name for Lambda execution (from GitHub secrets)."
}

variable "step_function_role_name" {
  type        = string
  description = "Pre-created IAM role name for Step Functions (from GitHub secrets)."
}

variable "eventbridge_role_name" {
  type        = string
  description = "Pre-created IAM role name for EventBridge Scheduler (from GitHub secrets)."
}