# Cognito Module Outputs

output "user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.arn
}

output "user_pool_endpoint" {
  description = "Endpoint of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.endpoint
}

output "user_pool_domain" {
  description = "Cognito User Pool domain"
  value       = aws_cognito_user_pool_domain.main.domain
}

output "user_pool_domain_url" {
  description = "Full URL of the Cognito hosted UI"
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
}

output "web_client_id" {
  description = "ID of the web application client"
  value       = aws_cognito_user_pool_client.web_client.id
}

output "web_client_secret" {
  description = "Secret of the web application client (if enabled)"
  value       = aws_cognito_user_pool_client.web_client.client_secret
  sensitive   = true
}

output "identity_pool_id" {
  description = "ID of the Cognito Identity Pool"
  value       = aws_cognito_identity_pool.main.id
}

output "admin_username" {
  description = "Username of the admin user"
  value       = aws_cognito_user.admin.username
}

output "operator_username" {
  description = "Username of the operator user"
  value       = aws_cognito_user.operator.username
}

output "viewer_username" {
  description = "Username of the viewer user"
  value       = aws_cognito_user.viewer.username
}

output "user_group_names" {
  description = "Names of created user groups"
  value = {
    admins    = aws_cognito_user_group.admins.name
    operators = aws_cognito_user_group.operators.name
    viewers   = aws_cognito_user_group.viewers.name
  }
}

# Data source for current region
data "aws_region" "current" {}
