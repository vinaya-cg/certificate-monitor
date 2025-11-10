# ServiceNow Integration Module - Outputs

output "lambda_function_arn" {
  description = "ARN of the ServiceNow ticket creator Lambda function"
  value       = aws_lambda_function.servicenow_ticket_creator.arn
}

output "lambda_function_name" {
  description = "Name of the ServiceNow ticket creator Lambda function"
  value       = aws_lambda_function.servicenow_ticket_creator.function_name
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge schedule rule (if enabled)"
  value       = var.enable_scheduled_execution ? aws_cloudwatch_event_rule.servicenow_schedule[0].arn : null
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge schedule rule (if enabled)"
  value       = var.enable_scheduled_execution ? aws_cloudwatch_event_rule.servicenow_schedule[0].name : null
}

output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.servicenow_lambda.name
}
