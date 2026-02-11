provider "aws" {
  region = var.aws_region
}

locals {
  image_uri = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repo}:${var.image_tag}"
}

resource "aws_ecr_repository_policy" "allow_lambda_pull" {
  repository = var.ecr_repo

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaPull"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchCheckLayerAvailability"
        ]
      }
    ]
  })
}


# -------------------------
# Lambda (Image)
# -------------------------
resource "aws_lambda_function" "fn" {
  function_name = var.lambda_name
  package_type  = "Image"
  image_uri     = local.image_uri
  role = aws_iam_role.lambda_exec.arn

  timeout     = 900
  memory_size = 1024
  
  depends_on = [
    aws_ecr_repository_policy.allow_lambda_pull,
    aws_iam_role_policy_attachment.lambda_ecr_readonly,
    aws_iam_role_policy_attachment.lambda_basic_logs
  ]
}

# -------------------------
# Step Functions State Machine
# -------------------------
resource "aws_sfn_state_machine" "sm" {
  name     = var.state_machine_name
  role_arn = aws_iam_role.sfn_role.arn

  definition = jsonencode({
    Comment = "Scraper workflow"
    StartAt = "RunLambda"
    States = {
      RunLambda = {
        Type     = "Task"
        Resource = aws_lambda_function.fn.arn
        End      = true
      }
    }
  })
}

# -------------------------
# EventBridge Scheduler
# -------------------------
resource "aws_scheduler_schedule" "schedule" {
  name                = var.schedule_name
  schedule_expression = var.schedule_expression
  state               = "ENABLED"

  flexible_time_window { mode = "OFF" }

  target {
    arn      = aws_sfn_state_machine.sm.arn
    role_arn = aws_iam_role.scheduler_role.arn
    input    = jsonencode({ source = "scheduler" })
  }
}


# -------------------------
# Permissions (depend on created resources)
# -------------------------

# SFN can invoke the Lambda
resource "aws_iam_role_policy" "sfn_invoke_lambda" {
  name = "${var.state_machine_name}-invoke-lambda"
  role = aws_iam_role.sfn_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["lambda:InvokeFunction"]
      Resource = [
        aws_lambda_function.fn.arn,
        "${aws_lambda_function.fn.arn}:*"
      ]
    }]
  })
}

# Scheduler can start the SFN execution
resource "aws_iam_role_policy" "scheduler_start_sfn" {
  name = "${var.schedule_name}-start-sfn"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["states:StartExecution"]
      Resource = aws_sfn_state_machine.sm.arn
    }]
  })
}