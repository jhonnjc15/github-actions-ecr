provider "aws" {
  region = var.aws_region
}

locals {
  image_uri = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repo}:${var.image_tag}"

  # Extrae el nombre del role desde el ARN:
  # arn:aws:iam::<acct>:role/<ROLE_NAME>
  lambda_exec_role_name = regex("role/(.+)$", var.lambda_exec_role_arn)[0]
}

## NOTE (Option 1 - simple):
## We intentionally do NOT create the ECR repository here.
## Reason: bootstrap is smoother if the GitHub Actions workflow creates the repo
## and pushes the first image tag (latest) before Terraform creates the Lambda.
## If you want "infra-owned" ECR, add aws_ecr_repository + remove the workflow
## step that creates the repo.

# resource "aws_ecr_repository_policy" "allow_lambda_pull" {
#   repository = var.ecr_repo
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Sid    = "AllowLambdaPull"
#         Effect = "Allow"
#         Principal = {
#           AWS = var.lambda_exec_role_arn
#         }
#         Action = [
#           "ecr:BatchGetImage",
#           "ecr:GetDownloadUrlForLayer",
#           "ecr:BatchCheckLayerAvailability"
#         ]
#       }
#     ]
#   })
# }

data "aws_iam_role" "lambda_exec" {
  name = local.lambda_exec_role_name
}

resource "aws_iam_role_policy_attachment" "lambda_ecr_readonly" {
  role       = data.aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "lambda_basic_logs" {
  role       = data.aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# -------------------------
# Lambda (Image)
# -------------------------
resource "aws_lambda_function" "fn" {
  function_name = var.lambda_name
  package_type  = "Image"
  image_uri     = local.image_uri
  role          = var.lambda_exec_role_arn

  timeout     = 900
  memory_size = 1024
}

# -------------------------
# Step Functions State Machine
# -------------------------
resource "aws_sfn_state_machine" "sm" {
  name     = var.state_machine_name
  role_arn = var.sfn_role_arn

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
    role_arn = var.scheduler_role_arn
    input    = jsonencode({ source = "scheduler" })
  }
}
