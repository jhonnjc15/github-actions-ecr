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

variable "schedule_enabled" {
  description = "Si es true, crea el EventBridge Scheduler; si es false, no se crea."
  type        = bool
  default     = true
}

variable "schedule_timezone" {
  description = "Zona horaria para interpretar el cron del scheduler."
  type        = string
  default     = "America/Lima"
}

variable "github_repository" {
  description = "Repositorio GitHub que ejecuta el deploy"
  type        = string
}