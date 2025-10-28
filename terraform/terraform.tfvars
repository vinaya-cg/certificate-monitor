# Certificate Management System - Configuration
# Configure these values for your deployment

# Basic Configuration
project_name = "cert-management"
environment  = "dev"
aws_region   = "eu-west-1"
owner_tag    = "Certificate-Management-Team"

# Email Configuration (IMPORTANT: Update with your email)
sender_email = "vinaya-c.nayanegali@capgemini.com"

# Certificate Monitoring
expiry_threshold_days = 30
monitoring_schedule   = "cron(0 9 * * ? *)"  # Daily at 9 AM UTC

# Infrastructure Settings
log_retention_days = 30
lambda_memory_size = 512
lambda_timeout     = 300

# Security Settings
enable_versioning               = true
enable_encryption              = true
enable_point_in_time_recovery  = true

# Dashboard Configuration
dashboard_title       = "Certificate Management Dashboard"
dashboard_description = "Monitor and manage SSL/TLS certificates across environments"

# Cost Optimization
enable_cost_optimization    = true
lifecycle_transition_days   = 30
backup_retention_days      = 90

# Notification Settings
notification_settings = {
  send_owner_notifications    = true
  send_support_notifications  = true
  escalation_days            = 7
  reminder_frequency_days    = 7
}

# Excel Upload Settings
excel_upload_settings = {
  max_file_size_mb          = 50
  allowed_file_extensions   = [".xlsx", ".xls"]
  auto_process_uploads      = true
  backup_uploaded_files     = true
}