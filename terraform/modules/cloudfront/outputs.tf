# CloudFront Module Outputs

output "distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.dashboard.id
}

output "distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.dashboard.arn
}

output "distribution_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.dashboard.domain_name
}

output "distribution_url" {
  description = "HTTPS URL of the CloudFront distribution"
  value       = "https://${aws_cloudfront_distribution.dashboard.domain_name}"
}

output "distribution_hosted_zone_id" {
  description = "CloudFront Route 53 zone ID (for Route53 alias records)"
  value       = aws_cloudfront_distribution.dashboard.hosted_zone_id
}

output "oai_iam_arn" {
  description = "IAM ARN of the Origin Access Identity"
  value       = aws_cloudfront_origin_access_identity.dashboard.iam_arn
}

output "oai_cloudfront_path" {
  description = "CloudFront access identity path"
  value       = aws_cloudfront_origin_access_identity.dashboard.cloudfront_access_identity_path
}
