output "ecr_repo_url" {
  value = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repo}"
}
output "lambda_name"        { value = aws_lambda_function.fn.function_name }
output "state_machine_arn"  { value = aws_sfn_state_machine.sm.arn }
output "schedule_name"      { value = aws_scheduler_schedule.schedule.name }


output "lambda_exec_role_arn" { value = data.aws_iam_role.lambda_exec.arn }
output "sfn_role_arn"         { value = data.aws_iam_role.sfn_role.arn }
output "scheduler_role_arn"   { value = data.aws_iam_role.scheduler_role.arn }