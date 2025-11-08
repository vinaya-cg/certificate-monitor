# Certificate Management System - Development Environment
# This file orchestrates all modules for the dev environment

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
  }
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
# STORAGE MODULE
# ===================================================================

module "storage" {
  source = "../../modules/storage"

  project_name  = var.project_name
  environment   = var.environment
  bucket_suffix = random_string.suffix.result
  common_tags   = local.common_tags
}

# ===================================================================
# DATABASE MODULE
# ===================================================================

module "database" {
  source = "../../modules/database"

  project_name = var.project_name
  environment  = var.environment
  common_tags  = local.common_tags
}

# ===================================================================
# IAM MODULE
# ===================================================================

module "iam" {
  source = "../../modules/iam"

  project_name          = var.project_name
  environment           = var.environment
  certificates_table_arn = module.database.certificates_table_arn
  logs_table_arn        = module.database.logs_table_arn
  uploads_bucket_arn    = module.storage.uploads_bucket_arn
  dashboard_bucket_arn  = module.storage.dashboard_bucket_arn
  logs_bucket_arn       = module.storage.logs_bucket_arn
  aws_region            = data.aws_region.current.name
  aws_account_id        = data.aws_caller_identity.current.account_id
  common_tags           = local.common_tags
}

# ===================================================================
# LAMBDA MODULE
# ===================================================================

module "lambda" {
  source = "../../modules/lambda"

  project_name            = var.project_name
  environment             = var.environment
  lambda_role_arn         = module.iam.lambda_role_arn
  certificates_table_name = module.database.certificates_table_name
  logs_table_name         = module.database.logs_table_name
  uploads_bucket_name     = module.storage.uploads_bucket_name
  logs_bucket_name        = module.storage.logs_bucket_name
  sender_email            = var.sender_email
  expiry_threshold_days   = var.expiry_threshold_days
  aws_region              = data.aws_region.current.name
  lambda_source_path      = "${path.module}/../../../lambda"
  common_tags             = local.common_tags

  depends_on = [module.iam]
}

# ===================================================================
# MONITORING MODULE
# ===================================================================

module "monitoring" {
  source = "../../modules/monitoring"

  project_name                      = var.project_name
  environment                       = var.environment
  aws_region                        = data.aws_region.current.name
  certificate_monitor_function_name = module.lambda.certificate_monitor_function_name
  certificates_table_name           = module.database.certificates_table_name
  common_tags                       = local.common_tags
}

# ===================================================================
# EVENTBRIDGE MODULE
# ===================================================================

module "eventbridge" {
  source = "../../modules/eventbridge"

  project_name                      = var.project_name
  environment                       = var.environment
  certificate_monitor_function_name = module.lambda.certificate_monitor_function_name
  certificate_monitor_function_arn  = module.lambda.certificate_monitor_function_arn
  schedule_expression               = var.monitoring_schedule
  common_tags                       = local.common_tags

  depends_on = [module.lambda]
}

# ===================================================================
# DASHBOARD MODULE
# ===================================================================

module "dashboard" {
  source = "../../modules/dashboard"

  dashboard_bucket_name = module.storage.dashboard_bucket_name
  api_url               = module.lambda.dashboard_api_url
  source_files_path     = "${path.module}/../../../dashboard"

  depends_on = [module.storage, module.lambda]
}
