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
  default     = 100
}

# ===================================================================
# SERVICENOW INTEGRATION CONFIGURATION
# ===================================================================

variable "enable_servicenow_integration" {
  description = "Enable ServiceNow ticket creation for expiring certificates"
  type        = bool
  default     = false  # Disabled by default - enable when ready
}

variable "servicenow_secret_name" {
  description = "Name of Secrets Manager secret containing ServiceNow credentials"
  type        = string
  default     = "cert-management/servicenow/credentials"
}

variable "servicenow_secret_arn" {
  description = "ARN of Secrets Manager secret containing ServiceNow credentials"
  type        = string
  default     = ""  # Will be populated after secret creation
}

variable "servicenow_dry_run" {
  description = "Enable dry-run mode (no actual ServiceNow tickets created)"
  type        = string
  default     = "true"  # Start in dry-run mode for safety
}

variable "servicenow_enable_schedule" {
  description = "Enable automatic scheduled execution for ServiceNow ticket creation"
  type        = bool
  default     = true
}

variable "servicenow_schedule" {
  description = "Schedule expression for ServiceNow ticket creation (5 min after cert monitor)"
  type        = string
  default     = "cron(5 9 * * ? *)"  # Daily at 9:05 AM UTC
}

variable "servicenow_enable_alarms" {
  description = "Enable CloudWatch alarms for ServiceNow integration monitoring"
  type        = bool
  default     = false  # Disable initially, enable after testing
}

# ===================================================================
# SERVICENOW WEBHOOK INTEGRATION (BIDIRECTIONAL)
# ===================================================================

variable "enable_servicenow_webhook" {
  description = "Enable ServiceNow webhook handler for incident assignment updates"
  type        = bool
  default     = false  # Disabled until ServiceNow Business Rule is configured
}

variable "servicenow_webhook_secret_name" {
  description = "Name of Secrets Manager secret for webhook signature validation"
  type        = string
  default     = "cert-management/servicenow/webhook-secret"
}

variable "servicenow_webhook_secret_arn" {
  description = "ARN of Secrets Manager secret for webhook validation"
  type        = string
  default     = ""  # Will be populated when secret is created
}
