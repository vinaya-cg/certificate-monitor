# Lambda ACM Sync Module - Outputs

output "lambda_function_arn" {
  description = "ARN of the ACM sync Lambda function"
  value       = aws_lambda_function.acm_sync.arn
}

output "lambda_function_name" {
  description = "Name of the ACM sync Lambda function"
  value       = aws_lambda_function.acm_sync.function_name
}

output "schedule_rule_name" {
  description = "Name of the EventBridge schedule rule"
  value       = aws_cloudwatch_event_rule.acm_sync_schedule.name
}

output "schedule_expression" {
  description = "Schedule expression for ACM sync"
  value       = aws_cloudwatch_event_rule.acm_sync_schedule.schedule_expression
}

output "log_group_name" {
  description = "CloudWatch log group name for ACM sync"
  value       = aws_cloudwatch_log_group.acm_sync.name
}
