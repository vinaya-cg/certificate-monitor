# EventBridge Module - Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "certificate_monitor_function_name" {
  description = "Name of the certificate monitor Lambda function"
  type        = string
}

variable "certificate_monitor_function_arn" {
  description = "ARN of the certificate monitor Lambda function"
  type        = string
}

variable "schedule_expression" {
  description = "Schedule expression for monitoring (cron or rate)"
  type        = string
  default     = "cron(0 9 * * ? *)"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
