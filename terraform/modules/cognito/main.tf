# Cognito User Pool for Certificate Management Authentication
# Provides user authentication and authorization

# User Pool
resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-${var.environment}-user-pool"

  # Username configuration
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Password policy
  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # User attribute schema
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  schema {
    name                = "name"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  # Email configuration
  email_configuration {
    email_sending_account = "DEVELOPER"
    source_arn            = var.ses_identity_arn
    from_email_address    = var.sender_email
  }

  # Admin create user config
  admin_create_user_config {
    allow_admin_create_user_only = false

    invite_message_template {
      email_subject = "Your Certificate Management Dashboard login"
      email_message = "Welcome! Your username is {username} and temporary password is {####}. Please change it on first login."
      sms_message   = "Your username is {username} and temporary password is {####}"
    }
  }

  # User pool add-ons
  user_pool_add_ons {
    advanced_security_mode = "AUDIT"
  }

  # Verification message templates
  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "Verify your email for Certificate Dashboard"
    email_message        = "Your verification code is {####}"
  }
}

# User Pool Domain (for hosted UI if needed later)
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.project_name}-${var.environment}-${var.domain_suffix}"
  user_pool_id = aws_cognito_user_pool.main.id
}

# User Pool Client (for web application)
resource "aws_cognito_user_pool_client" "web_client" {
  name         = "${var.project_name}-${var.environment}-web-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # OAuth settings
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code", "implicit"]
  allowed_oauth_scopes                 = ["email", "openid", "profile", "aws.cognito.signin.user.admin"]

  # Callback URLs (will be CloudFront URL)
  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls

  # Token validity
  access_token_validity  = 1  # 1 hour
  id_token_validity      = 1  # 1 hour
  refresh_token_validity = 30 # 30 days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  # Security settings
  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true

  # Explicit auth flows
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  # Read/Write attributes
  read_attributes = [
    "email",
    "email_verified",
    "name"
  ]

  write_attributes = [
    "email",
    "name"
  ]
}

# User Groups
resource "aws_cognito_user_group" "admins" {
  name         = "Admins"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Administrators with full access to all certificate operations"
  precedence   = 1
}

resource "aws_cognito_user_group" "operators" {
  name         = "Operators"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Operators who can view and update certificate status"
  precedence   = 2
}

resource "aws_cognito_user_group" "viewers" {
  name         = "Viewers"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Viewers with read-only access to certificates"
  precedence   = 3
}

# Admin User
resource "aws_cognito_user" "admin" {
  user_pool_id = aws_cognito_user_pool.main.id
  username     = var.admin_user.username

  attributes = {
    email          = var.admin_user.email
    email_verified = true
    name           = var.admin_user.name
  }

  desired_delivery_mediums = ["EMAIL"]
  force_alias_creation     = false

  lifecycle {
    ignore_changes = [
      attributes["email_verified"]
    ]
  }
}

resource "aws_cognito_user_in_group" "admin_group_membership" {
  user_pool_id = aws_cognito_user_pool.main.id
  group_name   = aws_cognito_user_group.admins.name
  username     = aws_cognito_user.admin.username

  depends_on = [aws_cognito_user.admin, aws_cognito_user_group.admins]
}

# Operator User
resource "aws_cognito_user" "operator" {
  user_pool_id = aws_cognito_user_pool.main.id
  username     = var.operator_user.username

  attributes = {
    email          = var.operator_user.email
    email_verified = true
    name           = var.operator_user.name
  }

  desired_delivery_mediums = ["EMAIL"]
  force_alias_creation     = false

  lifecycle {
    ignore_changes = [
      attributes["email_verified"]
    ]
  }
}

resource "aws_cognito_user_in_group" "operator_group_membership" {
  user_pool_id = aws_cognito_user_pool.main.id
  group_name   = aws_cognito_user_group.operators.name
  username     = aws_cognito_user.operator.username

  depends_on = [aws_cognito_user.operator, aws_cognito_user_group.operators]
}

# Viewer User
resource "aws_cognito_user" "viewer" {
  user_pool_id = aws_cognito_user_pool.main.id
  username     = var.viewer_user.username

  attributes = {
    email          = var.viewer_user.email
    email_verified = true
    name           = var.viewer_user.name
  }

  desired_delivery_mediums = ["EMAIL"]
  force_alias_creation     = false

  lifecycle {
    ignore_changes = [
      attributes["email_verified"]
    ]
  }
}

resource "aws_cognito_user_in_group" "viewer_group_membership" {
  user_pool_id = aws_cognito_user_pool.main.id
  group_name   = aws_cognito_user_group.viewers.name
  username     = aws_cognito_user.viewer.username

  depends_on = [aws_cognito_user.viewer, aws_cognito_user_group.viewers]
}

# Identity Pool (for AWS service access if needed later)
resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = "${var.project_name}-${var.environment}-identity-pool"
  allow_unauthenticated_identities = false

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.web_client.id
    provider_name           = aws_cognito_user_pool.main.endpoint
    server_side_token_check = true
  }
}
