# Secure Development Environment - Configuration
# Configure these values for secure deployment

# Basic Configuration
project_name = "cert-management"
environment  = "dev-secure"
aws_region   = "eu-west-1"
owner_tag    = "Certificate-Management-Team"

# Email Configuration (IMPORTANT: Must be verified in SES)
sender_email = "vinaya-c.nayanegali@capgemini.com"

# Certificate Monitoring
expiry_threshold_days = 30
monitoring_schedule   = "cron(0 9 * * ? *)"  # Daily at 9 AM UTC

# Admin User Configuration
admin_user = {
  username = "vinaya-c.nayanegali@capgemini.com"  # Must be email when using email authentication
  email    = "vinaya-c.nayanegali@capgemini.com"
  name     = "System Administrator"
}

# Operator User Configuration
operator_user = {
  username = "vinaya-c.nayanegali+operator@capgemini.com"  # Must be email
  email    = "vinaya-c.nayanegali+operator@capgemini.com"
  name     = "Certificate Operator"
}

# Viewer User Configuration
viewer_user = {
  username = "vinaya-c.nayanegali+viewer@capgemini.com"  # Must be email
  email    = "vinaya-c.nayanegali+viewer@capgemini.com"
  name     = "Certificate Viewer"
}

# API Gateway Throttling
api_throttling_burst_limit = 5000
api_throttling_rate_limit  = 2000

# ===================================================================
# SERVICENOW INTEGRATION CONFIGURATION
# ===================================================================

# Enable ServiceNow ticket creation for expiring certificates
enable_servicenow_integration = true

# ServiceNow credentials stored in Secrets Manager
servicenow_secret_name = "cert-management/servicenow/credentials"
servicenow_secret_arn  = "arn:aws:secretsmanager:eu-west-1:992155623828:secret:cert-management/servicenow/credentials-agnpGG"

# PRODUCTION MODE - Credentials verified and working
# ServiceNow integration fully operational with azure_monitoring sender
servicenow_dry_run = "false"

# Enable automatic daily execution
servicenow_enable_schedule = true

# Run at 9:05 AM UTC daily (5 minutes after certificate monitor)
servicenow_schedule = "cron(5 9 * * ? *)"

# Disable CloudWatch alarms initially (enable after testing)
servicenow_enable_alarms = false

# ===================================================================
# SERVICENOW WEBHOOK INTEGRATION (BIDIRECTIONAL)
# ===================================================================

# Enable webhook handler for receiving ServiceNow incident updates
# DISABLED - Infrastructure ready but not active until ServiceNow Business Rule configured
enable_servicenow_webhook = false

# Webhook secret for signature validation (optional but recommended)
servicenow_webhook_secret_name = "cert-management/servicenow/webhook-secret"
# servicenow_webhook_secret_arn will be created when secret is set up

# ===================================================================
# SERVER CERTIFICATE SCANNER CONFIGURATION
# ===================================================================

# Enable server certificate scanning via SSM for Windows and Linux servers
enable_server_certificate_scan = true

# Run at 9:30 AM UTC daily (30 minutes after ACM sync, 25 minutes after ServiceNow tickets)
server_scan_schedule = "cron(30 9 * * ? *)"

# Disable CloudWatch alarms initially (enable after testing)
server_scan_enable_alarms = false
