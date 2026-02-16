data "aws_iam_role" "lambda_exec" {
  name = var.lambda_role_name
}

data "aws_iam_role" "sfn_role" {
  name = var.step_function_role_name
}

data "aws_iam_role" "scheduler_role" {
  name = var.eventbridge_role_name
}