# Certificate Management System - Secure Development Environment
# This file orchestrates all modules for the dev-secure environment with full security

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Local backend - state stored locally
  backend "local" {
    path = "terraform.tfstate"
  }
}

# ===================================================================
# PROVIDER CONFIGURATION
# ===================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# ===================================================================
# DATA SOURCES
# ===================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ===================================================================
# LOCALS
# ===================================================================

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = var.owner_tag
    Security    = "Enhanced"
  }
  
  # CloudFront callback URLs
  cloudfront_url = "https://${module.cloudfront.distribution_domain_name}"
  callback_urls  = [
    "${local.cloudfront_url}/index.html",
    "${local.cloudfront_url}/dashboard.html"
  ]
  logout_urls = [
    "${local.cloudfront_url}/login.html"
  ]
}

# ===================================================================
# RANDOM SUFFIX FOR UNIQUE NAMING
# ===================================================================

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# ===================================================================
# SES EMAIL IDENTITY
# ===================================================================

resource "aws_ses_email_identity" "sender" {
  email = var.sender_email
}

# ===================================================================
# SECURE STORAGE MODULE (Private S3 Buckets)
# ===================================================================

module "storage_secure" {
  source = "../../modules/storage_secure"

  project_name  = var.project_name
  environment   = var.environment
  bucket_suffix = random_string.suffix.result
  common_tags   = local.common_tags
}

# ===================================================================
# DATABASE MODULE (Reused from original)
# ===================================================================

module "database" {
  source = "../../modules/database"

  project_name = var.project_name
  environment  = var.environment
  common_tags  = local.common_tags
}

# ===================================================================
# IAM MODULE (Reused from original)
# ===================================================================

module "iam" {
  source = "../../modules/iam"

  project_name          = var.project_name
  environment           = var.environment
  certificates_table_arn = module.database.certificates_table_arn
  logs_table_arn        = module.database.logs_table_arn
  uploads_bucket_arn    = module.storage_secure.uploads_bucket_arn
  dashboard_bucket_arn  = module.storage_secure.dashboard_bucket_arn
  logs_bucket_arn       = module.storage_secure.logs_bucket_arn
  aws_region            = data.aws_region.current.name
  aws_account_id        = data.aws_caller_identity.current.account_id
  common_tags           = local.common_tags
}

# ===================================================================
# COGNITO MODULE (User Authentication)
# ===================================================================

module "cognito" {
  source = "../../modules/cognito"

  project_name        = var.project_name
  environment         = var.environment
  domain_suffix       = random_string.suffix.result
  ses_identity_arn    = aws_ses_email_identity.sender.arn
  sender_email        = var.sender_email
  admin_user          = var.admin_user
  operator_user       = var.operator_user
  viewer_user         = var.viewer_user
  callback_urls       = local.callback_urls
  logout_urls         = local.logout_urls
  common_tags         = local.common_tags
}

# ===================================================================
# SECURE LAMBDA MODULE (API Gateway Integration)
# ===================================================================

module "lambda_secure" {
  source = "../../modules/lambda_secure"

  project_name               = var.project_name
  environment                = var.environment
  lambda_role_arn            = module.iam.lambda_role_arn
  certificates_table_name    = module.database.certificates_table_name
  logs_table_name            = module.database.logs_table_name
  uploads_bucket_name        = module.storage_secure.uploads_bucket_name
  logs_bucket_name           = module.storage_secure.logs_bucket_name
  sender_email               = var.sender_email
  expiry_threshold_days      = var.expiry_threshold_days
  aws_region                 = data.aws_region.current.name
  lambda_source_path         = "${path.module}/../../../lambda"
  api_gateway_execution_arn  = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*/*/*"
  common_tags                = local.common_tags

  depends_on = [module.iam]
}

# ===================================================================
# API GATEWAY MODULE (Cognito Authorization)
# ===================================================================

module "api_gateway" {
  source = "../../modules/api_gateway"

  project_name                    = var.project_name
  environment                     = var.environment
  cognito_user_pool_arn           = module.cognito.user_pool_arn
  dashboard_api_lambda_name       = module.lambda_secure.dashboard_api_function_name
  dashboard_api_lambda_invoke_arn = module.lambda_secure.dashboard_api_invoke_arn
  throttling_burst_limit          = var.api_throttling_burst_limit
  throttling_rate_limit           = var.api_throttling_rate_limit
  common_tags                     = local.common_tags

  depends_on = [module.cognito, module.lambda_secure]
}

# ===================================================================
# CLOUDFRONT MODULE (HTTPS Distribution)
# ===================================================================

module "cloudfront" {
  source = "../../modules/cloudfront"

  project_name                   = var.project_name
  environment                    = var.environment
  s3_bucket_id                   = module.storage_secure.dashboard_bucket_id
  s3_bucket_arn                  = module.storage_secure.dashboard_bucket_arn
  s3_bucket_regional_domain_name = module.storage_secure.dashboard_bucket_regional_domain_name
  common_tags                    = local.common_tags

  depends_on = [module.storage_secure]
}

# ===================================================================
# MONITORING MODULE (Reused from original)
# ===================================================================

module "monitoring" {
  source = "../../modules/monitoring"

  project_name                      = var.project_name
  environment                       = var.environment
  aws_region                        = data.aws_region.current.name
  certificate_monitor_function_name = module.lambda_secure.certificate_monitor_function_name
  certificates_table_name           = module.database.certificates_table_name
  common_tags                       = local.common_tags
}

# ===================================================================
# EVENTBRIDGE MODULE (Reused from original)
# ===================================================================

module "eventbridge" {
  source = "../../modules/eventbridge"

  project_name                      = var.project_name
  environment                       = var.environment
  certificate_monitor_function_name = module.lambda_secure.certificate_monitor_function_name
  certificate_monitor_function_arn  = module.lambda_secure.certificate_monitor_function_arn
  schedule_expression               = var.monitoring_schedule
  common_tags                       = local.common_tags

  depends_on = [module.lambda_secure]
}

# ===================================================================
# SECURE DASHBOARD MODULE (Auto-inject Cognito Config)
# ===================================================================

module "dashboard_secure" {
  source = "../../modules/dashboard_secure"

  bucket_name              = module.storage_secure.dashboard_bucket_name
  dashboard_source_path    = "${path.module}/../../../dashboard"
  api_gateway_url          = module.api_gateway.api_endpoint
  cognito_user_pool_id     = module.cognito.user_pool_id
  cognito_client_id        = module.cognito.web_client_id
  cognito_identity_pool_id = module.cognito.identity_pool_id
  cognito_domain           = module.cognito.user_pool_domain_url
  aws_region               = data.aws_region.current.name

  depends_on = [
    module.storage_secure,
    module.cognito,
    module.api_gateway,
    module.cloudfront
  ]
}
