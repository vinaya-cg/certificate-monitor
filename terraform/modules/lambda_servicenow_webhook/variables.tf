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

variable "webhook_secret_name" {
  description = "Name of the Secrets Manager secret for webhook validation"
  type        = string
  default     = "cert-management/servicenow/webhook-secret"
}

variable "webhook_secret_arn" {
  description = "ARN of the Secrets Manager secret for webhook validation"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms for the Lambda function"
  type        = bool
  default     = true
}
