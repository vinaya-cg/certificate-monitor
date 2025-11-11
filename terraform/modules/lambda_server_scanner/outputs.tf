output "lambda_function_arn" {
  description = "ARN of the server certificate scanner Lambda function"
  value       = aws_lambda_function.server_cert_scanner.arn
}

output "lambda_function_name" {
  description = "Name of the server certificate scanner Lambda function"
  value       = aws_lambda_function.server_cert_scanner.function_name
}

output "windows_ssm_document_name" {
  description = "Name of the Windows certificate scanning SSM document"
  value       = aws_ssm_document.windows_cert_scan.name
}

output "linux_ssm_document_name" {
  description = "Name of the Linux certificate scanning SSM document"
  value       = aws_ssm_document.linux_cert_scan.name
}

output "scan_schedule" {
  description = "EventBridge schedule expression for server scanning"
  value       = var.enable_scheduled_scan ? aws_cloudwatch_event_rule.server_scan_schedule[0].schedule_expression : "Disabled"
}
