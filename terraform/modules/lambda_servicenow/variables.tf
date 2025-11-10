# ServiceNow Integration Module - Variables

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "certificates_table_name" {
  description = "Name of the DynamoDB certificates table"
  type        = string
}

variable "certificates_table_arn" {
  description = "ARN of the DynamoDB certificates table"
  type        = string
}

variable "logs_table_name" {
  description = "Name of the DynamoDB logs table"
  type        = string
}

variable "logs_table_arn" {
  description = "ARN of the DynamoDB logs table"
  type        = string
}

variable "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  type        = string
}

variable "lambda_execution_role_id" {
  description = "ID of the Lambda execution role (for attaching policies)"
  type        = string
}

variable "snow_secret_name" {
  description = "Name of the Secrets Manager secret containing ServiceNow credentials"
  type        = string
}

variable "snow_secret_arn" {
  description = "ARN of the Secrets Manager secret containing ServiceNow credentials"
  type        = string
}

variable "expiry_threshold_days" {
  description = "Number of days before expiry to create tickets"
  type        = number
  default     = 30
}

variable "dry_run" {
  description = "Enable dry-run mode (no actual tickets created)"
  type        = string
  default     = "false"
}

variable "enable_scheduled_execution" {
  description = "Enable automatic scheduled execution via EventBridge"
  type        = bool
  default     = true
}

variable "schedule_expression" {
  description = "EventBridge schedule expression (cron or rate)"
  type        = string
  default     = "cron(5 9 * * ? *)"  # Daily at 9:05 AM UTC (5 min after cert monitor)
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
}

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for monitoring"
  type        = bool
  default     = false
}
