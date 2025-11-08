# Lambda Module - Outputs

output "dashboard_api_function_name" {
  description = "Name of the dashboard API Lambda function"
  value       = aws_lambda_function.dashboard_api.function_name
}

output "dashboard_api_function_arn" {
  description = "ARN of the dashboard API Lambda function"
  value       = aws_lambda_function.dashboard_api.arn
}

output "dashboard_api_url" {
  description = "URL of the dashboard API Lambda function"
  value       = aws_lambda_function_url.dashboard_api_url.function_url
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
