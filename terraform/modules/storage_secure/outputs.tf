# Secure Storage Module Outputs

output "dashboard_bucket_id" {
  description = "ID of the dashboard S3 bucket"
  value       = aws_s3_bucket.dashboard.id
}

output "dashboard_bucket_name" {
  description = "Name of the dashboard S3 bucket"
  value       = aws_s3_bucket.dashboard.id
}

output "dashboard_bucket_arn" {
  description = "ARN of the dashboard S3 bucket"
  value       = aws_s3_bucket.dashboard.arn
}

output "dashboard_bucket_regional_domain_name" {
  description = "Regional domain name of the dashboard bucket"
  value       = aws_s3_bucket.dashboard.bucket_regional_domain_name
}

output "uploads_bucket_id" {
  description = "ID of the uploads S3 bucket"
  value       = aws_s3_bucket.uploads.id
}

output "uploads_bucket_name" {
  description = "Name of the uploads S3 bucket"
  value       = aws_s3_bucket.uploads.id
}

output "uploads_bucket_arn" {
  description = "ARN of the uploads S3 bucket"
  value       = aws_s3_bucket.uploads.arn
}

output "logs_bucket_id" {
  description = "ID of the logs S3 bucket"
  value       = aws_s3_bucket.logs.id
}

output "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = aws_s3_bucket.logs.id
}

output "logs_bucket_arn" {
  description = "ARN of the logs S3 bucket"
  value       = aws_s3_bucket.logs.arn
}

output "logs_bucket_domain_name" {
  description = "Domain name of logs bucket (for CloudFront logging)"
  value       = aws_s3_bucket.logs.bucket_domain_name
}
