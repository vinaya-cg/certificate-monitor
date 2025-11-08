# Certificate Management System - Main Infrastructure
# Region: eu-west-1
# Purpose: Complete certificate monitoring and management system

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
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner_tag
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Random suffix for unique resource naming
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

locals {
  common_name = "${var.project_name}-${var.environment}"
  bucket_suffix = random_string.suffix.result
}

# ===================================================================
# S3 BUCKETS
# ===================================================================

# S3 bucket for dashboard hosting
resource "aws_s3_bucket" "dashboard" {
  bucket = "${local.common_name}-dashboard-${local.bucket_suffix}"
}

resource "aws_s3_bucket_public_access_block" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_policy" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.dashboard.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.dashboard]
}

# S3 bucket for certificate uploads
resource "aws_s3_bucket" "uploads" {
  bucket        = "${local.common_name}-uploads-${local.bucket_suffix}"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket for logs and archives
resource "aws_s3_bucket" "logs" {
  bucket = "${local.common_name}-logs-${local.bucket_suffix}"
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ===================================================================
# DYNAMODB TABLES
# ===================================================================

# Main certificates table
resource "aws_dynamodb_table" "certificates" {
  name           = "${local.common_name}-certificates"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "CertificateID"

  attribute {
    name = "CertificateID"
    type = "S"
  }

  attribute {
    name = "Status"
    type = "S"
  }

  attribute {
    name = "ExpiryDate"
    type = "S"
  }

  attribute {
    name = "Environment"
    type = "S"
  }

  attribute {
    name = "OwnerEmail"
    type = "S"
  }

  # GSI for status-based queries
  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "Status"
    range_key       = "ExpiryDate"
    projection_type = "ALL"
  }

  # GSI for environment-based queries
  global_secondary_index {
    name            = "EnvironmentIndex"
    hash_key        = "Environment"
    range_key       = "ExpiryDate"
    projection_type = "ALL"
  }

  # GSI for owner-based queries
  global_secondary_index {
    name            = "OwnerIndex"
    hash_key        = "OwnerEmail"
    range_key       = "ExpiryDate"
    projection_type = "ALL"
  }

  # GSI for expiry date queries
  global_secondary_index {
    name            = "ExpiryIndex"
    hash_key        = "ExpiryDate"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${local.common_name}-certificates"
  }
}

# Certificate logs table
resource "aws_dynamodb_table" "certificate_logs" {
  name           = "${local.common_name}-certificate-logs"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LogID"
  range_key      = "Timestamp"

  attribute {
    name = "LogID"
    type = "S"
  }

  attribute {
    name = "Timestamp"
    type = "S"
  }

  attribute {
    name = "CertificateID"
    type = "S"
  }

  attribute {
    name = "Action"
    type = "S"
  }

  # GSI for certificate-based log queries
  global_secondary_index {
    name            = "CertificateLogsIndex"
    hash_key        = "CertificateID"
    range_key       = "Timestamp"
    projection_type = "ALL"
  }

  # GSI for action-based queries
  global_secondary_index {
    name            = "ActionIndex"
    hash_key        = "Action"
    range_key       = "Timestamp"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${local.common_name}-certificate-logs"
  }
}

# ===================================================================
# IAM ROLES AND POLICIES
# ===================================================================

# Lambda execution role
resource "aws_iam_role" "lambda_role" {
  name = "${local.common_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda policy
resource "aws_iam_policy" "lambda_policy" {
  name        = "${local.common_name}-lambda-policy"
  description = "Policy for certificate management Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.certificates.arn,
          "${aws_dynamodb_table.certificates.arn}/*",
          aws_dynamodb_table.certificate_logs.arn,
          "${aws_dynamodb_table.certificate_logs.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.uploads.arn,
          "${aws_s3_bucket.uploads.arn}/*",
          aws_s3_bucket.logs.arn,
          "${aws_s3_bucket.logs.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ===================================================================
# LAMBDA FUNCTIONS
# ===================================================================

# Package Excel processor Lambda
data "archive_file" "excel_processor" {
  type        = "zip"
  source_file = "${path.module}/../lambda/excel_processor.py"
  output_path = "${path.module}/excel_processor.zip"
}

# Excel processor Lambda function
resource "aws_lambda_function" "excel_processor" {
  filename         = data.archive_file.excel_processor.output_path
  function_name    = "${local.common_name}-excel-processor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "excel_processor.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 1024

  source_code_hash = data.archive_file.excel_processor.output_base64sha256

  environment {
    variables = {
      CERTIFICATES_TABLE = aws_dynamodb_table.certificates.name
      LOGS_TABLE        = aws_dynamodb_table.certificate_logs.name
      LOGS_BUCKET       = aws_s3_bucket.logs.bucket
      REGION            = data.aws_region.current.name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_policy,
    aws_cloudwatch_log_group.excel_processor,
  ]
}

# CloudWatch log group for Excel processor
resource "aws_cloudwatch_log_group" "excel_processor" {
  name              = "/aws/lambda/${local.common_name}-excel-processor"
  retention_in_days = var.log_retention_days
}

# Package certificate monitor Lambda
data "archive_file" "certificate_monitor" {
  type        = "zip"
  source_file = "${path.module}/../lambda/certificate_monitor.py"
  output_path = "${path.module}/certificate_monitor.zip"
}

# Certificate monitor Lambda function
resource "aws_lambda_function" "certificate_monitor" {
  filename         = data.archive_file.certificate_monitor.output_path
  function_name    = "${local.common_name}-certificate-monitor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "certificate_monitor.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900
  memory_size     = 512

  source_code_hash = data.archive_file.certificate_monitor.output_base64sha256

  environment {
    variables = {
      CERTIFICATES_TABLE  = aws_dynamodb_table.certificates.name
      LOGS_TABLE         = aws_dynamodb_table.certificate_logs.name
      SENDER_EMAIL       = var.sender_email
      EXPIRY_THRESHOLD   = var.expiry_threshold_days
      REGION             = data.aws_region.current.name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_policy,
    aws_cloudwatch_log_group.certificate_monitor,
  ]
}

# CloudWatch log group for certificate monitor
resource "aws_cloudwatch_log_group" "certificate_monitor" {
  name              = "/aws/lambda/${local.common_name}-certificate-monitor"
  retention_in_days = var.log_retention_days
}

# ===================================================================
# CLOUDWATCH EVENTS
# ===================================================================

# EventBridge rule for daily certificate monitoring
resource "aws_cloudwatch_event_rule" "daily_monitor" {
  name                = "${local.common_name}-daily-monitor"
  description         = "Trigger certificate monitoring daily"
  schedule_expression = var.monitoring_schedule
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_monitor.name
  target_id = "CertificateMonitorTarget"
  arn       = aws_lambda_function.certificate_monitor.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.certificate_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_monitor.arn
}

# ===================================================================
# S3 EVENT NOTIFICATIONS
# ===================================================================

# S3 bucket notification for Excel uploads
resource "aws_s3_bucket_notification" "excel_upload" {
  bucket = aws_s3_bucket.uploads.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.excel_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "excel/"
    filter_suffix       = ".xlsx"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.excel_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.uploads.arn
}

# ===================================================================
# SES EMAIL CONFIGURATION
# ===================================================================

resource "aws_ses_email_identity" "sender" {
  email = var.sender_email
}

# ===================================================================
# CLOUDWATCH DASHBOARD
# ===================================================================

resource "aws_cloudwatch_dashboard" "certificates" {
  dashboard_name = "${local.common_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.certificate_monitor.function_name],
            [".", "Errors", ".", "."],
            [".", "Invocations", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Certificate Monitor Lambda Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.certificates.name],
            [".", "ConsumedWriteCapacityUnits", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "DynamoDB Capacity Metrics"
          period  = 300
        }
      }
    ]
  })
}