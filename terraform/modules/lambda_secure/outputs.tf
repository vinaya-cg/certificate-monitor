# Lambda Secure Module - Outputs

output "dashboard_api_function_name" {
  description = "Name of the dashboard API Lambda function"
  value       = aws_lambda_function.dashboard_api.function_name
}

output "dashboard_api_function_arn" {
  description = "ARN of the dashboard API Lambda function"
  value       = aws_lambda_function.dashboard_api.arn
}

output "dashboard_api_invoke_arn" {
  description = "Invoke ARN of the dashboard API Lambda function (for API Gateway integration)"
  value       = aws_lambda_function.dashboard_api.invoke_arn
}

output "excel_processor_function_name" {
  description = "Name of the Excel processor Lambda function"
  value       = aws_lambda_function.excel_processor.function_name
}

output "excel_processor_function_arn" {
  description = "ARN of the Excel processor Lambda function"
  value       = aws_lambda_function.excel_processor.arn
}

output "certificate_monitor_function_name" {
  description = "Name of the certificate monitor Lambda function"
  value       = aws_lambda_function.certificate_monitor.function_name
}

output "certificate_monitor_function_arn" {
  description = "ARN of the certificate monitor Lambda function"
  value       = aws_lambda_function.certificate_monitor.arn
}

output "log_groups" {
  description = "Map of CloudWatch log groups"
  value = {
    dashboard_api        = aws_cloudwatch_log_group.dashboard_api.name
    excel_processor      = aws_cloudwatch_log_group.excel_processor.name
    certificate_monitor  = aws_cloudwatch_log_group.certificate_monitor.name
  }
}
