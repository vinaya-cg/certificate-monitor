# Database Module - Outputs

output "certificates_table_name" {
  description = "Name of the certificates DynamoDB table"
  value       = aws_dynamodb_table.certificates.name
}

output "certificates_table_arn" {
  description = "ARN of the certificates DynamoDB table"
  value       = aws_dynamodb_table.certificates.arn
}

output "logs_table_name" {
  description = "Name of the certificate logs DynamoDB table"
  value       = aws_dynamodb_table.certificate_logs.name
}

output "logs_table_arn" {
  description = "ARN of the certificate logs DynamoDB table"
  value       = aws_dynamodb_table.certificate_logs.arn
}
