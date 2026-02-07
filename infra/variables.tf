variable "aws_region" { type = string }
variable "aws_account_id" { type = string }

variable "ecr_repo" { type = string }
variable "lambda_name" { type = string }
variable "state_machine_name" { type = string }
variable "schedule_name" { type = string }
variable "schedule_expression" { type = string }

# Bootstrap: primera vez apunta a latest (luego el workflow lo cambia a sha)
variable "image_tag" {
  type    = string
  default = "latest"
}

variable "lambda_exec_role_arn" {
  type = string
}

variable "sfn_role_arn" {
  type = string
}

variable "scheduler_role_arn" {
  type = string
}