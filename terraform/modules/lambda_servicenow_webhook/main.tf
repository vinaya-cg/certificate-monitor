# ServiceNow Webhook Handler Lambda Module
# Receives webhooks when incidents are assigned/updated in ServiceNow
# Automatically updates certificate status and assignee information

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
  }
}

locals {
  function_name = "${var.project_name}-servicenow-webhook-handler"
  lambda_file   = "${path.module}/../../lambda/servicenow_webhook_handler.py"
}

# Package Lambda function
data "archive_file" "webhook_handler" {
  type        = "zip"
  source_file = local.lambda_file
  output_path = "${path.module}/webhook_handler.zip"
}

# IAM Role for Lambda
resource "aws_iam_role" "webhook_handler" {
  name = "${local.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${local.function_name}-role"
  }
}

# CloudWatch Logs policy
resource "aws_iam_role_policy" "webhook_handler_logs" {
  name = "${local.function_name}-logs-policy"
  role = aws_iam_role.webhook_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/${local.function_name}:*"
      }
    ]
  })
}

# DynamoDB access policy
resource "aws_iam_role_policy" "webhook_handler_dynamodb" {
  name = "${local.function_name}-dynamodb-policy"
  role = aws_iam_role.webhook_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBReadWrite"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:PutItem"
        ]
        Resource = [
          var.certificates_table_arn,
          var.logs_table_arn
        ]
      }
    ]
  })
}

# Secrets Manager access policy (for webhook secret)
resource "aws_iam_role_policy" "webhook_handler_secrets" {
  name = "${local.function_name}-secrets-policy"
  role = aws_iam_role.webhook_handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SecretsManagerRead"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = var.webhook_secret_arn
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "webhook_handler" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.function_name}-logs"
  }
}

# Lambda Function
resource "aws_lambda_function" "webhook_handler" {
  filename         = data.archive_file.webhook_handler.output_path
  function_name    = local.function_name
  role            = aws_iam_role.webhook_handler.arn
  handler         = "servicenow_webhook_handler.lambda_handler"
  source_code_hash = data.archive_file.webhook_handler.output_base64sha256
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      CERTIFICATES_TABLE   = var.certificates_table_name
      LOGS_TABLE          = var.logs_table_name
      WEBHOOK_SECRET_NAME = var.webhook_secret_name
    }
  }

  tags = {
    Name = local.function_name
  }

  depends_on = [
    aws_cloudwatch_log_group.webhook_handler,
    aws_iam_role_policy.webhook_handler_logs,
    aws_iam_role_policy.webhook_handler_dynamodb,
    aws_iam_role_policy.webhook_handler_secrets
  ]
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "webhook" {
  name        = "${var.project_name}-servicenow-webhook"
  description = "API Gateway for ServiceNow webhook integration"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${var.project_name}-servicenow-webhook"
  }
}

# API Gateway Resource
resource "aws_api_gateway_resource" "webhook" {
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  parent_id   = aws_api_gateway_rest_api.webhook.root_resource_id
  path_part   = "webhook"
}

# API Gateway Method (POST)
resource "aws_api_gateway_method" "webhook_post" {
  rest_api_id   = aws_api_gateway_rest_api.webhook.id
  resource_id   = aws_api_gateway_resource.webhook.id
  http_method   = "POST"
  authorization = "NONE"
}

# API Gateway Integration
resource "aws_api_gateway_integration" "webhook_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.webhook.id
  resource_id             = aws_api_gateway_resource.webhook.id
  http_method             = aws_api_gateway_method.webhook_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.webhook_handler.invoke_arn
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "webhook" {
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  stage_name  = var.environment

  depends_on = [
    aws_api_gateway_integration.webhook_lambda
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.webhook.execution_arn}/*/*"
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "webhook_errors" {
  count               = var.enable_alarms ? 1 : 0
  alarm_name          = "${local.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Alert when webhook handler has too many errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.webhook_handler.function_name
  }

  tags = {
    Name = "${local.function_name}-errors-alarm"
  }
}
