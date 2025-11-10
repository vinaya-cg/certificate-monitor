# Lambda Secure Module - Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "lambda_source_path" {
  description = "Path to Lambda function source files"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the IAM role for Lambda functions"
  type        = string
}

variable "certificates_table_name" {
  description = "Name of the certificates DynamoDB table"
  type        = string
}

variable "logs_table_name" {
  description = "Name of the logs DynamoDB table"
  type        = string
}

variable "uploads_bucket_name" {
  description = "Name of the S3 bucket for Excel uploads"
  type        = string
}

variable "logs_bucket_name" {
  description = "Name of the S3 bucket for logs"
  type        = string
}

variable "sender_email" {
  description = "SES verified sender email address"
  type        = string
}

variable "expiry_threshold_days" {
  description = "Number of days before expiry to send notifications"
  type        = number
  default     = 30
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "api_gateway_execution_arn" {
  description = "Execution ARN of the API Gateway (for Lambda permission)"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "acm_sync_function_name" {
  description = "Name of the ACM sync Lambda function"
  type        = string
}
