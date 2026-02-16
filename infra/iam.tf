# -------------------------
# IAM Roles (shared, pre-created)
# -------------------------
#
# IMPORTANT:
# - These roles MUST already exist in the AWS account.
# - Terraform in this stack will NOT create/replace IAM roles.
# - Names are fixed per environment only.

data "aws_iam_role" "lambda_exec" {
  name = "scraper-${var.environment}-lambda-exec-2"
}

data "aws_iam_role" "sfn_role" {
  name = "scraper-${var.environment}-sfn-role"
}

data "aws_iam_role" "scheduler_role" {
  name = "scraper-${var.environment}-scheduler-role"
}
