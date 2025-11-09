# Secure Dashboard Module Variables

variable "bucket_name" {
  description = "Name of the S3 bucket to upload dashboard files to"
  type        = string
}

variable "dashboard_source_path" {
  description = "Path to dashboard source files"
  type        = string
}

variable "api_gateway_url" {
  description = "API Gateway invoke URL"
  type        = string
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  type        = string
}

variable "cognito_client_id" {
  description = "Cognito App Client ID"
  type        = string
}

variable "cognito_identity_pool_id" {
  description = "Cognito Identity Pool ID"
  type        = string
}

variable "cognito_domain" {
  description = "Cognito User Pool domain"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}
