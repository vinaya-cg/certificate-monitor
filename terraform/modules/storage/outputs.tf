# Storage Module - Outputs

output "dashboard_bucket_name" {
  description = "Name of the dashboard S3 bucket"
  value       = aws_s3_bucket.dashboard.id
}

output "dashboard_bucket_arn" {
  description = "ARN of the dashboard S3 bucket"
  value       = aws_s3_bucket.dashboard.arn
}

output "dashboard_website_endpoint" {
  description = "Website endpoint for dashboard bucket"
  value       = aws_s3_bucket_website_configuration.dashboard.website_endpoint
}

output "uploads_bucket_name" {
  description = "Name of the uploads S3 bucket"
  value       = aws_s3_bucket.uploads.id
}

output "uploads_bucket_arn" {
  description = "ARN of the uploads S3 bucket"
  value       = aws_s3_bucket.uploads.arn
}

output "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = aws_s3_bucket.logs.id
}

output "logs_bucket_arn" {
  description = "ARN of the logs S3 bucket"
  value       = aws_s3_bucket.logs.arn
}
