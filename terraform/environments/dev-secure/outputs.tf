# Secure Development Environment - Outputs

# ===================================================================
# CLOUDFRONT OUTPUTS
# ===================================================================

output "cloudfront_distribution_url" {
  description = "CloudFront distribution URL (use this to access the dashboard)"
  value       = "https://${module.cloudfront.distribution_domain_name}"
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.distribution_id
}

# ===================================================================
# COGNITO OUTPUTS
# ===================================================================

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.cognito.user_pool_id
}

output "cognito_client_id" {
  description = "Cognito App Client ID"
  value       = module.cognito.web_client_id
}

output "cognito_domain_url" {
  description = "Cognito hosted UI domain URL"
  value       = module.cognito.user_pool_domain_url
}

output "cognito_users" {
  description = "Created Cognito users (check email for temporary passwords)"
  value = {
    admin    = module.cognito.admin_username
    operator = module.cognito.operator_username
    viewer   = module.cognito.viewer_username
  }
}

# ===================================================================
# API GATEWAY OUTPUTS
# ===================================================================

output "api_gateway_url" {
  description = "API Gateway invoke URL (requires authentication)"
  value       = module.api_gateway.api_endpoint
}

output "api_gateway_id" {
  description = "API Gateway REST API ID"
  value       = module.api_gateway.api_id
}

# ===================================================================
# STORAGE OUTPUTS
# ===================================================================

output "dashboard_bucket_name" {
  description = "Dashboard S3 bucket name (private - CloudFront access only)"
  value       = module.storage_secure.dashboard_bucket_name
}

output "uploads_bucket_name" {
  description = "Excel uploads S3 bucket name (private)"
  value       = module.storage_secure.uploads_bucket_name
}

# ===================================================================
# DATABASE OUTPUTS
# ===================================================================

output "certificates_table_name" {
  description = "Certificates DynamoDB table name"
  value       = module.database.certificates_table_name
}

output "logs_table_name" {
  description = "Logs DynamoDB table name"
  value       = module.database.logs_table_name
}

# ===================================================================
# LAMBDA OUTPUTS
# ===================================================================

output "dashboard_api_function_name" {
  description = "Dashboard API Lambda function name"
  value       = module.lambda_secure.dashboard_api_function_name
}

output "excel_processor_function_name" {
  description = "Excel processor Lambda function name"
  value       = module.lambda_secure.excel_processor_function_name
}

output "certificate_monitor_function_name" {
  description = "Certificate monitor Lambda function name"
  value       = module.lambda_secure.certificate_monitor_function_name
}

# ===================================================================
# DEPLOYMENT INFORMATION
# ===================================================================

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = <<-EOT
  
  ╔════════════════════════════════════════════════════════════════════╗
  ║     CERTIFICATE MANAGEMENT SYSTEM - SECURE DEPLOYMENT              ║
  ╚════════════════════════════════════════════════════════════════════╝
  
  🌐 DASHBOARD URL (HTTPS):
     ${module.cloudfront.distribution_domain_name}
  
  🔐 AUTHENTICATION:
     User Pool: ${module.cognito.user_pool_id}
     Client ID: ${module.cognito.web_client_id}
     
  👥 USERS (check email for temporary passwords):
     • Admin:    ${module.cognito.admin_username}
     • Operator: ${module.cognito.operator_username}
     • Viewer:   ${module.cognito.viewer_username}
  
  🔗 API ENDPOINT:
     ${module.api_gateway.api_endpoint}
  
  📊 DATABASES:
     • Certificates: ${module.database.certificates_table_name}
     • Logs:         ${module.database.logs_table_name}
  
  🔒 SECURITY FEATURES:
     ✓ Cognito Authentication (3 user groups)
     ✓ CloudFront HTTPS Distribution (TLS 1.2+)
     ✓ API Gateway with JWT Authorization
     ✓ Private S3 Buckets (OAI access only)
     ✓ Lambda JWT Validation
     ✓ Role-Based Access Control
  
  📝 NEXT STEPS:
     1. Check your email for Cognito temporary passwords
     2. Access dashboard via CloudFront URL
     3. Login with your credentials
     4. Change temporary password on first login
     5. Start managing certificates!
  
  EOT
}

# ===================================================================
# SERVICENOW INTEGRATION OUTPUTS
# ===================================================================

output "servicenow_lambda_function_name" {
  description = "Name of the ServiceNow ticket creator Lambda function"
  value       = var.enable_servicenow_integration ? module.servicenow_integration[0].lambda_function_name : "Not enabled"
}

output "servicenow_lambda_function_arn" {
  description = "ARN of the ServiceNow ticket creator Lambda function"
  value       = var.enable_servicenow_integration ? module.servicenow_integration[0].lambda_function_arn : null
}

output "servicenow_eventbridge_rule_name" {
  description = "Name of the ServiceNow EventBridge schedule rule"
  value       = var.enable_servicenow_integration ? module.servicenow_integration[0].eventbridge_rule_name : "Not enabled"
}

output "servicenow_status" {
  description = "ServiceNow integration status and configuration"
  value = var.enable_servicenow_integration ? {
    enabled     = true
    dry_run     = var.servicenow_dry_run
    schedule    = var.servicenow_schedule
    secret_name = var.servicenow_secret_name
  } : {
    enabled = false
    message = "ServiceNow integration is disabled. Set enable_servicenow_integration=true to enable"
  }
}

# ===================================================================
# SERVICENOW WEBHOOK INTEGRATION OUTPUTS
# ===================================================================

output "servicenow_webhook_url" {
  description = "ServiceNow webhook endpoint URL (configure this in ServiceNow Business Rule)"
  value       = var.enable_servicenow_webhook ? module.servicenow_webhook[0].webhook_endpoint : "Webhook integration disabled"
}

output "servicenow_webhook_lambda_name" {
  description = "Name of the ServiceNow webhook handler Lambda function"
  value       = var.enable_servicenow_webhook ? module.servicenow_webhook[0].lambda_function_name : "Not enabled"
}

output "servicenow_webhook_status" {
  description = "ServiceNow webhook integration status"
  value = var.enable_servicenow_webhook ? {
    enabled              = true
    webhook_endpoint     = module.servicenow_webhook[0].webhook_endpoint
    lambda_function_name = module.servicenow_webhook[0].lambda_function_name
    api_gateway_id       = module.servicenow_webhook[0].api_gateway_id
    next_steps          = "Configure Business Rule in ServiceNow using the webhook_endpoint URL"
  } : {
    enabled = false
    message = "Webhook integration disabled. Set enable_servicenow_webhook=true to enable when ready"
  }
}
