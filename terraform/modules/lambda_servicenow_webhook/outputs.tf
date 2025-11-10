output "lambda_function_arn" {
  description = "ARN of the webhook handler Lambda function"
  value       = aws_lambda_function.webhook_handler.arn
}

output "lambda_function_name" {
  description = "Name of the webhook handler Lambda function"
  value       = aws_lambda_function.webhook_handler.function_name
}

output "api_gateway_url" {
  description = "URL of the API Gateway endpoint for webhooks"
  value       = "${aws_api_gateway_deployment.webhook.invoke_url}/webhook"
}

output "api_gateway_id" {
  description = "ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.webhook.id
}

output "webhook_endpoint" {
  description = "Complete webhook endpoint URL (configure this in ServiceNow)"
  value       = "${aws_api_gateway_deployment.webhook.invoke_url}/webhook"
}
