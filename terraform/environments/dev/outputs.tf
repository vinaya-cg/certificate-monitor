# Development Environment - Outputs

# ===================================================================
# GENERAL INFORMATION
# ===================================================================

output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "deployment_region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}

output "project_info" {
  description = "Project information"
  value = {
    name        = var.project_name
    environment = var.environment
    owner       = var.owner_tag
  }
}

# ===================================================================
# STORAGE OUTPUTS
# ===================================================================

output "dashboard_bucket_name" {
  description = "Name of the dashboard S3 bucket"
  value       = module.storage.dashboard_bucket_name
}

output "dashboard_website_url" {
  description = "URL of the dashboard website"
  value       = "http://${module.storage.dashboard_website_endpoint}"
}

output "uploads_bucket_name" {
  description = "Name of the uploads S3 bucket"
  value       = module.storage.uploads_bucket_name
}

output "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = module.storage.logs_bucket_name
}

# ===================================================================
# DATABASE OUTPUTS
# ===================================================================

output "certificates_table_name" {
  description = "Name of the certificates DynamoDB table"
  value       = module.database.certificates_table_name
}

output "certificates_table_arn" {
  description = "ARN of the certificates DynamoDB table"
  value       = module.database.certificates_table_arn
}

output "certificate_logs_table_name" {
  description = "Name of the certificate logs DynamoDB table"
  value       = module.database.logs_table_name
}

output "certificate_logs_table_arn" {
  description = "ARN of the certificate logs DynamoDB table"
  value       = module.database.logs_table_arn
}

# ===================================================================
# IAM OUTPUTS
# ===================================================================

output "lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = module.iam.lambda_role_name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = module.iam.lambda_role_arn
}

# ===================================================================
# LAMBDA OUTPUTS
# ===================================================================

output "dashboard_api_function_name" {
  description = "Name of the dashboard API Lambda function"
  value       = module.lambda.dashboard_api_function_name
}

output "dashboard_api_url" {
  description = "URL of the dashboard API"
  value       = module.lambda.dashboard_api_url
}

output "excel_processor_function_name" {
  description = "Name of the Excel processor Lambda function"
  value       = module.lambda.excel_processor_function_name
}

output "excel_processor_function_arn" {
  description = "ARN of the Excel processor Lambda function"
  value       = module.lambda.excel_processor_function_arn
}

output "certificate_monitor_function_name" {
  description = "Name of the certificate monitor Lambda function"
  value       = module.lambda.certificate_monitor_function_name
}

output "certificate_monitor_function_arn" {
  description = "ARN of the certificate monitor Lambda function"
  value       = module.lambda.certificate_monitor_function_arn
}

# ===================================================================
# MONITORING OUTPUTS
# ===================================================================

output "cloudwatch_dashboard_url" {
  description = "URL to CloudWatch dashboard"
  value       = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${module.monitoring.cloudwatch_dashboard_name}"
}

# ===================================================================
# EVENTBRIDGE OUTPUTS
# ===================================================================

output "monitoring_schedule" {
  description = "Schedule expression for certificate monitoring"
  value       = var.monitoring_schedule
}

output "expiry_threshold_days" {
  description = "Number of days before expiry to trigger alerts"
  value       = var.expiry_threshold_days
}

# ===================================================================
# SES OUTPUTS
# ===================================================================

output "sender_email" {
  description = "Email address for notifications"
  value       = var.sender_email
}

output "ses_identity_verification_required" {
  description = "SES email identity verification reminder"
  value       = "Please verify email identity: ${var.sender_email} in SES console"
}

# ===================================================================
# COST ESTIMATES
# ===================================================================

output "estimated_monthly_costs" {
  description = "Estimated monthly costs"
  value = {
    s3_approximate         = "$0.10-1 (storage and requests)"
    dynamodb_approximate   = "$1-5 (pay-per-request for typical certificate volume)"
    lambda_approximate     = "$0.20-2 (daily monitoring + processing)"
    cloudwatch_approximate = "$0.50-2 (logs and monitoring)"
    ses_approximate        = "$0.10 per 1,000 emails"
    total_estimate         = "$2-10/month for typical usage"
    note                   = "Costs depend on certificate volume and usage patterns"
  }
}

# ===================================================================
# QUICK START COMMANDS
# ===================================================================

output "quick_start_commands" {
  description = "Quick start commands"
  value = [
    "# 1. Verify SES email identity:",
    "aws ses verify-email-identity --email-address ${var.sender_email}",
    "",
    "# 2. Upload Excel file to trigger processing:",
    "aws s3 cp your-certificates.xlsx s3://${module.storage.uploads_bucket_name}/excel/certificates.xlsx",
    "",
    "# 3. Check processing logs:",
    "aws logs tail /aws/lambda/${module.lambda.excel_processor_function_name} --follow",
    "",
    "# 4. Access dashboard:",
    "open http://${module.storage.dashboard_website_endpoint}",
    "",
    "# 5. Manually trigger certificate monitoring:",
    "aws lambda invoke --function-name ${module.lambda.certificate_monitor_function_name} response.json"
  ]
}

# ===================================================================
# TROUBLESHOOTING INFO
# ===================================================================

output "troubleshooting_info" {
  description = "Troubleshooting information"
  value = {
    certificates_table        = module.database.certificates_table_name
    logs_table                = module.database.logs_table_name
    uploads_bucket            = module.storage.uploads_bucket_name
    excel_processor_logs      = "/aws/lambda/${module.lambda.excel_processor_function_name}"
    certificate_monitor_logs  = "/aws/lambda/${module.lambda.certificate_monitor_function_name}"
    cloudwatch_dashboard      = module.monitoring.cloudwatch_dashboard_name
  }
}
