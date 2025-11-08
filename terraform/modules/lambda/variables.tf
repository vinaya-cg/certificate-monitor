# Lambda Module - Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
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
  description = "Name of the uploads S3 bucket"
  type        = string
}

variable "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  type        = string
}

variable "sender_email" {
  description = "Email address for sending notifications"
  type        = string
}

variable "expiry_threshold_days" {
  description = "Number of days before expiry to trigger alerts"
  type        = number
  default     = 30
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "lambda_source_path" {
  description = "Path to Lambda source code directory"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
