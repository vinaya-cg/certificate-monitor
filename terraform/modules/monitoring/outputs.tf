# Monitoring Module - Outputs

output "cloudwatch_dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.certificates.dashboard_name
}
