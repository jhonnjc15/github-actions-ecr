provider "aws" {
  region = var.aws_region
}

locals {
  image_uri = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repo}:${var.image_tag}"
}

## NOTE (Option 1 - simple):
## We intentionally do NOT create the ECR repository here.
## Reason: bootstrap is smoother if the GitHub Actions workflow creates the repo
## and pushes the first image tag (latest) before Terraform creates the Lambda.
## If you want "infra-owned" ECR, add aws_ecr_repository + remove the workflow
## step that creates the repo.

# -------------------------
# IAM - Lambda Exec Role
# -------------------------
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${var.lambda_name}-exec-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# -------------------------
# Lambda (Image)
# -------------------------
resource "aws_lambda_function" "fn" {
  function_name = var.lambda_name
  role          = aws_iam_role.lambda_exec.arn

  package_type = "Image"
  image_uri    = local.image_uri

  timeout     = 900
  memory_size = 1024
}

# -------------------------
# IAM - Step Functions Role
# -------------------------
data "aws_iam_policy_document" "sfn_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sfn_role" {
  name               = "${var.state_machine_name}-role"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume.json
}

data "aws_iam_policy_document" "sfn_invoke_lambda" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.fn.arn]
  }
}

resource "aws_iam_role_policy" "sfn_policy" {
  name   = "${var.state_machine_name}-invoke-lambda"
  role   = aws_iam_role.sfn_role.id
  policy = data.aws_iam_policy_document.sfn_invoke_lambda.json
}

# -------------------------
# Step Functions State Machine
# -------------------------
resource "aws_sfn_state_machine" "sm" {
  name     = var.state_machine_name
  role_arn = aws_iam_role.sfn_role.arn

  definition = templatefile("${path.module}/templates/state_machine.asl.json.tpl", {
    lambda_arn = aws_lambda_function.fn.arn
  })
}

# -------------------------
# IAM - Scheduler Role
# -------------------------
data "aws_iam_policy_document" "scheduler_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler_role" {
  name               = "${var.schedule_name}-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume.json
}

data "aws_iam_policy_document" "scheduler_start_exec" {
  statement {
    actions   = ["states:StartExecution"]
    resources = [aws_sfn_state_machine.sm.arn]
  }
}

resource "aws_iam_role_policy" "scheduler_policy" {
  name   = "${var.schedule_name}-start-exec"
  role   = aws_iam_role.scheduler_role.id
  policy = data.aws_iam_policy_document.scheduler_start_exec.json
}

# -------------------------
# EventBridge Scheduler
# -------------------------
resource "aws_scheduler_schedule" "schedule" {
  name                = var.schedule_name
  schedule_expression = var.schedule_expression

  flexible_time_window { mode = "OFF" }

  target {
    arn      = aws_sfn_state_machine.sm.arn
    role_arn = aws_iam_role.scheduler_role.arn
    input    = jsonencode({ source = "scheduler" })
  }
}
