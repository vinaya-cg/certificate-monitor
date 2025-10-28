# Create ZIP file for dashboard API Lambda
data "archive_file" "dashboard_api_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/dashboard_api.py"
  output_path = "${path.module}/dashboard_api.zip"
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
}

# Lambda function URL for dashboard API
resource "aws_lambda_function_url" "dashboard_api_url" {
  function_name      = aws_lambda_function.dashboard_api.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "OPTIONS"]
    allow_headers     = ["date", "keep-alive", "content-type"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }
}