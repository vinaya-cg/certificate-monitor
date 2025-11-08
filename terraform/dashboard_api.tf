# Create ZIP file for dashboard API Lambda
data "archive_file" "dashboard_api_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/dashboard_api.py"
  output_path = "${path.module}/dashboard_api.zip"
}

# CloudWatch Log Group for Dashboard API
resource "aws_cloudwatch_log_group" "dashboard_api" {
  name              = "/aws/lambda/${local.common_name}-dashboard-api"
  retention_in_days = 30
}

# Dashboard API Lambda function
resource "aws_lambda_function" "dashboard_api" {
  filename         = data.archive_file.dashboard_api_zip.output_path
  function_name    = "${local.common_name}-dashboard-api"
  role            = aws_iam_role.lambda_role.arn
  handler         = "dashboard_api.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30

  source_code_hash = data.archive_file.dashboard_api_zip.output_base64sha256

  environment {
    variables = {
      CERTIFICATES_TABLE = aws_dynamodb_table.certificates.name
    }
  }

  tags = {
    Name = "${local.common_name}-dashboard-api"
  }

  depends_on = [
    aws_cloudwatch_log_group.dashboard_api,
    aws_iam_role_policy_attachment.lambda_basic
  ]
}

# Lambda function URL for dashboard API
resource "aws_lambda_function_url" "dashboard_api_url" {
  function_name      = aws_lambda_function.dashboard_api.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["*"]
    allow_headers     = ["*"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }
}