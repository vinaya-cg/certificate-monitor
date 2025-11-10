# Lambda Secure Module - Functions with JWT Validation
# Manages Lambda functions with API Gateway integration (no Function URL)

locals {
  common_name = "${var.project_name}-${var.environment}"
}

# ===================================================================
# LAMBDA ZIP FILES
# ===================================================================

data "archive_file" "dashboard_api" {
  type        = "zip"
  source_file = "${var.lambda_source_path}/dashboard_api.py"
  output_path = "${path.module}/../../environments/${var.environment}/dashboard_api.zip"
}

data "archive_file" "excel_processor" {
  type        = "zip"
  source_file = "${var.lambda_source_path}/excel_processor.py"
  output_path = "${path.module}/../../environments/${var.environment}/excel_processor.zip"
}

data "archive_file" "certificate_monitor" {
  type        = "zip"
  source_file = "${var.lambda_source_path}/certificate_monitor.py"
  output_path = "${path.module}/../../environments/${var.environment}/certificate_monitor.zip"
}

# ===================================================================
# CLOUDWATCH LOG GROUPS
# ===================================================================

resource "aws_cloudwatch_log_group" "dashboard_api" {
  name              = "/aws/lambda/${local.common_name}-dashboard-api"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "excel_processor" {
  name              = "/aws/lambda/${local.common_name}-excel-processor"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "certificate_monitor" {
  name              = "/aws/lambda/${local.common_name}-certificate-monitor"
  retention_in_days = 30
}

# ===================================================================
# LAMBDA FUNCTIONS
# ===================================================================

# Dashboard API - Handles CRUD operations with JWT validation from API Gateway
resource "aws_lambda_function" "dashboard_api" {
  filename         = data.archive_file.dashboard_api.output_path
  function_name    = "${local.common_name}-dashboard-api"
  role             = var.lambda_role_arn
  handler          = "dashboard_api.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 128
  source_code_hash = data.archive_file.dashboard_api.output_base64sha256

  environment {
    variables = {
      CERTIFICATES_TABLE = var.certificates_table_name
      ACM_SYNC_FUNCTION  = var.acm_sync_function_name
      # JWT validation is handled by API Gateway Cognito Authorizer
      # User info is available in event['requestContext']['authorizer']['claims']
    }
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${local.common_name}-dashboard-api"
    }
  )

  depends_on = [aws_cloudwatch_log_group.dashboard_api]
}

# Lambda permission for API Gateway (replaces Function URL)
# API Gateway permission is managed by api_gateway module
# resource "aws_lambda_permission" "api_gateway" {
#   statement_id  = "AllowExecutionFromAPIGateway"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.dashboard_api.function_name
#   principal     = "apigateway.amazonaws.com"
#   source_arn    = "${var.api_gateway_execution_arn}/*/*"
# }

# Excel Processor - Processes uploaded Excel files (unchanged)
resource "aws_lambda_function" "excel_processor" {
  filename         = data.archive_file.excel_processor.output_path
  function_name    = "${local.common_name}-excel-processor"
  role             = var.lambda_role_arn
  handler          = "excel_processor.lambda_handler"
  runtime          = "python3.9"
  timeout          = 300
  memory_size      = 1024
  source_code_hash = data.archive_file.excel_processor.output_base64sha256

  environment {
    variables = {
      CERTIFICATES_TABLE = var.certificates_table_name
      LOGS_TABLE         = var.logs_table_name
      LOGS_BUCKET        = var.logs_bucket_name
      REGION             = var.aws_region
    }
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${local.common_name}-excel-processor"
    }
  )

  depends_on = [aws_cloudwatch_log_group.excel_processor]
}

# Certificate Monitor - Daily monitoring and notifications (unchanged)
resource "aws_lambda_function" "certificate_monitor" {
  filename         = data.archive_file.certificate_monitor.output_path
  function_name    = "${local.common_name}-certificate-monitor"
  role             = var.lambda_role_arn
  handler          = "certificate_monitor.lambda_handler"
  runtime          = "python3.9"
  timeout          = 900
  memory_size      = 512
  source_code_hash = data.archive_file.certificate_monitor.output_base64sha256

  environment {
    variables = {
      CERTIFICATES_TABLE = var.certificates_table_name
      LOGS_TABLE         = var.logs_table_name
      SENDER_EMAIL       = var.sender_email
      EXPIRY_THRESHOLD   = var.expiry_threshold_days
      REGION             = var.aws_region
    }
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${local.common_name}-certificate-monitor"
    }
  )

  depends_on = [aws_cloudwatch_log_group.certificate_monitor]
}

# ===================================================================
# S3 TRIGGER FOR EXCEL PROCESSOR
# ===================================================================

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.excel_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.uploads_bucket_name}"
}

resource "aws_s3_bucket_notification" "excel_upload" {
  bucket = var.uploads_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.excel_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "excel/"
    filter_suffix       = ".xlsx"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}
