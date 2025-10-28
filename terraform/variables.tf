# Certificate Management System - Variables
# Configuration for the complete certificate monitoring system

# ===================================================================
# BASIC CONFIGURATION
# ===================================================================

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "cert-management"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, test, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "test", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, test, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-1"
}

variable "owner_tag" {
  description = "Owner tag for resources"
  type        = string
  default     = "Certificate-Management-Team"
}

# ===================================================================
# EMAIL CONFIGURATION
# ===================================================================

variable "sender_email" {
  description = "Email address for sending notifications (must be verified in SES)"
  type        = string
  default     = "certificates@company.com"
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.sender_email))
    error_message = "Sender email must be a valid email address."
  }
}

# ===================================================================
# CERTIFICATE MONITORING CONFIGURATION
# ===================================================================

variable "expiry_threshold_days" {
  description = "Number of days before certificate expiry to trigger notifications"
  type        = number
  default     = 30
  
  validation {
    condition     = var.expiry_threshold_days > 0 && var.expiry_threshold_days <= 365
    error_message = "Expiry threshold must be between 1 and 365 days."
  }
}

variable "monitoring_schedule" {
  description = "CloudWatch Events schedule expression for certificate monitoring"
  type        = string
  default     = "cron(0 9 * * ? *)"  # Daily at 9 AM UTC
  
  validation {
    condition     = can(regex("^(rate|cron)\\(.*\\)$", var.monitoring_schedule))
    error_message = "Monitoring schedule must be a valid CloudWatch Events schedule expression."
  }
}

# ===================================================================
# INFRASTRUCTURE CONFIGURATION
# ===================================================================

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
  
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch log retention value."
  }
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in MB"
  type        = number
  default     = 512
  
  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory size must be between 128 and 10240 MB."
  }
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 300
  
  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds."
  }
}

# ===================================================================
# SECURITY CONFIGURATION
# ===================================================================

variable "enable_versioning" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Enable encryption for S3 buckets"
  type        = bool
  default     = true
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for DynamoDB tables"
  type        = bool
  default     = true
}

# ===================================================================
# DASHBOARD CONFIGURATION
# ===================================================================

variable "dashboard_title" {
  description = "Title for the certificate management dashboard"
  type        = string
  default     = "Certificate Management Dashboard"
}

variable "dashboard_description" {
  description = "Description for the certificate management dashboard"
  type        = string
  default     = "Monitor and manage SSL/TLS certificates across environments"
}

# ===================================================================
# CERTIFICATE STATUS CONFIGURATION
# ===================================================================

variable "certificate_statuses" {
  description = "Valid certificate statuses"
  type        = list(string)
  default     = [
    "Active",
    "Due for Renewal",
    "Renewal in Progress", 
    "Renewal Done"
  ]
}

# ===================================================================
# BACKUP AND COMPLIANCE
# ===================================================================

variable "enable_backups" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 90
  
  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Backup retention must be between 1 and 365 days."
  }
}

# ===================================================================
# COST OPTIMIZATION
# ===================================================================

variable "enable_cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = true
}

variable "lifecycle_transition_days" {
  description = "Days after which to transition S3 objects to IA storage"
  type        = number
  default     = 30
  
  validation {
    condition     = var.lifecycle_transition_days >= 30
    error_message = "Lifecycle transition must be at least 30 days."
  }
}

# ===================================================================
# NOTIFICATION CONFIGURATION
# ===================================================================

variable "notification_settings" {
  description = "Notification settings for different certificate events"
  type = object({
    send_owner_notifications    = bool
    send_support_notifications  = bool
    escalation_days            = number
    reminder_frequency_days    = number
  })
  default = {
    send_owner_notifications    = true
    send_support_notifications  = true
    escalation_days            = 7
    reminder_frequency_days    = 7
  }
}

# ===================================================================
# EXCEL UPLOAD CONFIGURATION
# ===================================================================

variable "excel_upload_settings" {
  description = "Settings for Excel file uploads"
  type = object({
    max_file_size_mb          = number
    allowed_file_extensions   = list(string)
    auto_process_uploads      = bool
    backup_uploaded_files     = bool
  })
  default = {
    max_file_size_mb          = 50
    allowed_file_extensions   = [".xlsx", ".xls"]
    auto_process_uploads      = true
    backup_uploaded_files     = true
  }
}