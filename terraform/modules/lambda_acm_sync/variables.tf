# Lambda ACM Sync Module - Variables

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "certificates_table_name" {
  description = "DynamoDB certificates table name"
  type        = string
}

variable "certificates_table_arn" {
  description = "DynamoDB certificates table ARN"
  type        = string
}

variable "lambda_role_arn" {
  description = "IAM role ARN for Lambda execution"
  type        = string
}

variable "lambda_role_name" {
  description = "IAM role name for Lambda execution"
  type        = string
}

variable "lambda_log_group_arn" {
  description = "CloudWatch log group ARN for Lambda"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch logs retention in days"
  type        = number
  default     = 30
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
