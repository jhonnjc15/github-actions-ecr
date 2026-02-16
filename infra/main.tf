provider "aws" {
  region = var.aws_region
}

locals {
  # Nombres con sufijo por ambiente
  lambda_name        = "${var.lambda_name}-${var.environment}"
  state_machine_name = "${var.state_machine_name}-${var.environment}"
  schedule_name      = "${var.schedule_name}-${var.environment}"

  # Imagen ECR
  image_uri = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repo}:${var.image_tag}"

  # (Opcional) tags comunes
  common_tags = {
    environment = var.environment
    managed_by  = "terraform"
    project     = "scraper"
  }
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
  function_name = local.lambda_name
  package_type  = "Image"
  image_uri     = local.image_uri
  role          = data.aws_iam_role.lambda_exec.name

  timeout     = 900
  memory_size = 1024

  tags = local.common_tags

  depends_on = [
    aws_ecr_repository_policy.allow_lambda_pull
  ]
}

# -------------------------
# Step Functions State Machine
# -------------------------
resource "aws_sfn_state_machine" "sm" {
  name     = local.state_machine_name
  role_arn = data.aws_iam_role.sfn_role.name

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

  tags = local.common_tags
}

# -------------------------
# EventBridge Scheduler
# -------------------------
resource "aws_scheduler_schedule" "schedule" {
  name                = local.schedule_name
  schedule_expression = var.schedule_expression
  state               = "ENABLED"

  flexible_time_window { mode = "OFF" }

  target {
    arn      = aws_sfn_state_machine.sm.arn
    role_arn = data.aws_iam_role.scheduler_role.name
    input    = jsonencode({ source = "scheduler", env = var.environment })
  }
}

# -------------------------
# IMPORTANT (permissions)
# -------------------------
# This stack assumes the *pre-created shared roles* already have the needed permissions:
# - Lambda exec role: basic logs + ECR read
# - SFN role: lambda:InvokeFunction on the target Lambda(s)
# - Scheduler role: states:StartExecution on the target StateMachine(s)
