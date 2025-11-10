# Secure Development Environment - Variables

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "cert-management"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev-secure"
}

variable "owner_tag" {
  description = "Owner tag for resources"
  type        = string
  default     = "Certificate-Management-Team"
}

variable "sender_email" {
  description = "Email address for sending notifications (must be verified in SES)"
  type        = string
}

variable "expiry_threshold_days" {
  description = "Number of days before expiry to trigger alerts"
  type        = number
  default     = 30
}

variable "monitoring_schedule" {
  description = "Schedule expression for certificate monitoring"
  type        = string
  default     = "cron(0 9 * * ? *)"
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 30
}

# Cognito User Configuration
variable "admin_user" {
  description = "Admin user configuration"
  type = object({
    username = string
    email    = string
    name     = string
  })
}

variable "operator_user" {
  description = "Operator user configuration"
  type = object({
    username = string
    email    = string
    name     = string
  })
}

variable "viewer_user" {
  description = "Viewer user configuration"
  type = object({
    username = string
    email    = string
    name     = string
  })
}

# API Gateway Configuration
variable "api_throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 5000
}

variable "api_throttling_rate_limit" {
  description = "API Gateway throttling rate limit (requests per second)"
  type        = number
  default     = 2000
}
