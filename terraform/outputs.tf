# Certificate Management System - Outputs
# Important information for deployment and access

# ===================================================================
# DEPLOYMENT INFORMATION
# ===================================================================

output "deployment_region" {
  description = "AWS region where resources are deployed"
  value       = data.aws_region.current.name
}

output "account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
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
# S3 BUCKET INFORMATION
# ===================================================================

output "dashboard_bucket_name" {
  description = "Name of the dashboard hosting S3 bucket"
  value       = aws_s3_bucket.dashboard.bucket
}

output "dashboard_website_url" {
  description = "URL of the dashboard website"
  value       = "http://${aws_s3_bucket.dashboard.bucket}.s3-website-${data.aws_region.current.name}.amazonaws.com"
}

output "uploads_bucket_name" {
  description = "Name of the uploads S3 bucket"
  value       = aws_s3_bucket.uploads.bucket
}

output "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = aws_s3_bucket.logs.bucket
}

# ===================================================================
# DYNAMODB INFORMATION
# ===================================================================

output "certificates_table_name" {
  description = "Name of the certificates DynamoDB table"
  value       = aws_dynamodb_table.certificates.name
}

output "certificates_table_arn" {
  description = "ARN of the certificates DynamoDB table"
  value       = aws_dynamodb_table.certificates.arn
}

output "certificate_logs_table_name" {
  description = "Name of the certificate logs DynamoDB table"
  value       = aws_dynamodb_table.certificate_logs.name
}

output "certificate_logs_table_arn" {
  description = "ARN of the certificate logs DynamoDB table"
  value       = aws_dynamodb_table.certificate_logs.arn
}

# ===================================================================
# LAMBDA FUNCTION INFORMATION
# ===================================================================

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

# ===================================================================
# IAM INFORMATION
# ===================================================================

output "lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_role.name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}

# ===================================================================
# MONITORING INFORMATION
# ===================================================================

output "cloudwatch_dashboard_url" {
  description = "URL to CloudWatch dashboard"
  value       = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.certificates.dashboard_name}"
}

output "monitoring_schedule" {
  description = "Schedule for certificate monitoring"
  value       = var.monitoring_schedule
}

output "expiry_threshold_days" {
  description = "Days before expiry when notifications are sent"
  value       = var.expiry_threshold_days
}

# ===================================================================
# EMAIL CONFIGURATION
# ===================================================================

output "sender_email" {
  description = "Email address used for notifications"
  value       = var.sender_email
}

output "ses_identity_verification_required" {
  description = "SES email identity that needs verification"
  value       = "Please verify email identity: ${var.sender_email} in SES console"
}

# ===================================================================
# QUICK START COMMANDS
# ===================================================================

output "quick_start_commands" {
  description = "Commands to get started with the system"
  value = [
    "# 1. Verify SES email identity:",
    "aws ses verify-email-identity --email-address ${var.sender_email}",
    "",
    "# 2. Upload Excel file to trigger processing:",
    "aws s3 cp your-certificates.xlsx s3://${aws_s3_bucket.uploads.bucket}/excel/certificates.xlsx",
    "",
    "# 3. Check processing logs:",
    "aws logs tail /aws/lambda/${aws_lambda_function.excel_processor.function_name} --follow",
    "",
    "# 4. Access dashboard:",
    "open http://${aws_s3_bucket.dashboard.bucket}.s3-website-${data.aws_region.current.name}.amazonaws.com",
    "",
    "# 5. Manually trigger certificate monitoring:",
    "aws lambda invoke --function-name ${aws_lambda_function.certificate_monitor.function_name} response.json"
  ]
}

# ===================================================================
# TROUBLESHOOTING INFORMATION
# ===================================================================

output "troubleshooting_info" {
  description = "Troubleshooting information and resources"
  value = {
    excel_processor_logs     = "/aws/lambda/${aws_lambda_function.excel_processor.function_name}"
    certificate_monitor_logs = "/aws/lambda/${aws_lambda_function.certificate_monitor.function_name}"
    cloudwatch_dashboard     = aws_cloudwatch_dashboard.certificates.dashboard_name
    uploads_bucket          = aws_s3_bucket.uploads.bucket
    certificates_table      = aws_dynamodb_table.certificates.name
    logs_table              = aws_dynamodb_table.certificate_logs.name
  }
}

# ===================================================================
# NEXT STEPS
# ===================================================================

output "next_steps" {
  description = "Next steps after deployment"
  value = [
    "1. Verify SES email identity in AWS console",
    "2. Upload dashboard files to S3 bucket: ${aws_s3_bucket.dashboard.bucket}",
    "3. Upload initial Excel certificate data to: s3://${aws_s3_bucket.uploads.bucket}/excel/",
    "4. Test Lambda functions manually",
    "5. Configure custom domain (optional)",
    "6. Set up additional monitoring alerts",
    "7. Train support team on dashboard usage"
  ]
}

# ===================================================================
# COST INFORMATION
# ===================================================================

output "estimated_monthly_costs" {
  description = "Estimated monthly costs (USD) for typical usage"
  value = {
    dynamodb_approximate    = "$1-5 (pay-per-request for typical certificate volume)"
    lambda_approximate      = "$0.20-2 (daily monitoring + processing)"
    s3_approximate         = "$0.10-1 (storage and requests)"
    cloudwatch_approximate = "$0.50-2 (logs and monitoring)"
    ses_approximate        = "$0.10 per 1,000 emails"
    total_estimate         = "$2-10/month for typical usage"
    note                   = "Costs depend on certificate volume and usage patterns"
  }
}

# ===================================================================
# SECURITY INFORMATION
# ===================================================================

output "security_features" {
  description = "Security features enabled in the deployment"
  value = {
    s3_encryption_enabled        = var.enable_encryption
    dynamodb_point_in_time_recovery = var.enable_point_in_time_recovery
    iam_least_privilege         = "Lambda functions have minimal required permissions"
    s3_versioning_enabled       = var.enable_versioning
    cloudwatch_logging_enabled  = "All Lambda functions log to CloudWatch"
    public_dashboard_access     = "Dashboard is publicly accessible (no authentication)"
  }
}

# ===================================================================
# DASHBOARD API INFORMATION
# ===================================================================

output "dashboard_api_function_name" {
  description = "Name of the dashboard API Lambda function"
  value       = aws_lambda_function.dashboard_api.function_name
}

output "dashboard_api_url" {
  description = "Dashboard API Lambda function URL"
  value       = aws_lambda_function_url.dashboard_api_url.function_url
}