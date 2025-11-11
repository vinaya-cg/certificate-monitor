variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
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
  description = "IAM role name for attaching additional policies"
  type        = string
}

variable "enable_scheduled_scan" {
  description = "Enable scheduled server certificate scanning"
  type        = bool
  default     = true
}

variable "scan_schedule" {
  description = "EventBridge cron expression for scan schedule"
  type        = string
  default     = "cron(30 9 * * ? *)"  # Daily at 9:30 AM UTC
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms for monitoring"
  type        = bool
  default     = false
}
