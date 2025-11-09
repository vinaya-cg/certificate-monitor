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
