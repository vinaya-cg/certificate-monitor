# ServiceNow Integration Module - Main Configuration
# Creates Lambda function and EventBridge rule for automated ticket creation

# ===================================================================
# DATA SOURCES
# ===================================================================

data "archive_file" "servicenow_lambda" {
  type        = "zip"
  source_file = "${path.module}/../../../lambda/servicenow_ticket_creator.py"
  output_path = "${path.module}/servicenow_ticket_creator.zip"
}

# ===================================================================
# CLOUDWATCH LOG GROUP
# ===================================================================

resource "aws_cloudwatch_log_group" "servicenow_lambda" {
  name              = "/aws/lambda/${var.project_name}-servicenow-ticket-creator"
  retention_in_days = var.log_retention_days

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-servicenow-logs"
      Component   = "ServiceNow Integration"
      Function    = "Ticket Creation"
    }
  )
}

# ===================================================================
# LAMBDA FUNCTION
# ===================================================================

resource "aws_lambda_function" "servicenow_ticket_creator" {
  filename         = data.archive_file.servicenow_lambda.output_path
  function_name    = "${var.project_name}-servicenow-ticket-creator"
  role            = var.lambda_execution_role_arn
  handler         = "servicenow_ticket_creator.lambda_handler"
  source_code_hash = data.archive_file.servicenow_lambda.output_base64sha256
  runtime         = "python3.9"
  timeout         = 120
  memory_size     = 256

  environment {
    variables = {
      CERTIFICATES_TABLE    = var.certificates_table_name
      LOGS_TABLE           = var.logs_table_name
      SNOW_SECRET_NAME     = var.snow_secret_name
      EXPIRY_THRESHOLD_DAYS = var.expiry_threshold_days
      DRY_RUN              = var.dry_run
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.servicenow_lambda
  ]

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-servicenow-ticket-creator"
      Component   = "ServiceNow Integration"
      Function    = "Ticket Creation"
    }
  )
}

# ===================================================================
# EVENTBRIDGE SCHEDULE - Daily at 9:05 AM UTC (5 min after cert monitor)
# ===================================================================

resource "aws_cloudwatch_event_rule" "servicenow_schedule" {
  count = var.enable_scheduled_execution ? 1 : 0

  name                = "${var.project_name}-servicenow-schedule"
  description         = "Trigger ServiceNow ticket creation for expiring certificates"
  schedule_expression = var.schedule_expression

  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-servicenow-schedule"
      Component = "ServiceNow Integration"
    }
  )
}

resource "aws_cloudwatch_event_target" "servicenow_schedule" {
  count = var.enable_scheduled_execution ? 1 : 0

  rule      = aws_cloudwatch_event_rule.servicenow_schedule[0].name
  target_id = "ServiceNowTicketCreator"
  arn       = aws_lambda_function.servicenow_ticket_creator.arn
}

resource "aws_lambda_permission" "allow_eventbridge_servicenow" {
  count = var.enable_scheduled_execution ? 1 : 0

  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.servicenow_ticket_creator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.servicenow_schedule[0].arn
}

# ===================================================================
# IAM POLICY FOR SERVICENOW LAMBDA
# ===================================================================

resource "aws_iam_role_policy" "servicenow_lambda_policy" {
  name = "${var.project_name}-servicenow-lambda-policy"
  role = var.lambda_execution_role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBReadWrite"
        Effect = "Allow"
        Action = [
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:PutItem"
        ]
        Resource = [
          var.certificates_table_arn,
          var.logs_table_arn
        ]
      },
      {
        Sid    = "SecretsManagerRead"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.snow_secret_arn
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.servicenow_lambda.arn}:*"
      }
    ]
  })
}

# ===================================================================
# CLOUDWATCH ALARMS (Optional Monitoring)
# ===================================================================

resource "aws_cloudwatch_metric_alarm" "servicenow_errors" {
  count = var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.project_name}-servicenow-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "2"
  alarm_description   = "Alert when ServiceNow ticket creation fails repeatedly"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.servicenow_ticket_creator.function_name
  }

  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-servicenow-errors-alarm"
      Component = "ServiceNow Integration"
    }
  )
}

resource "aws_cloudwatch_metric_alarm" "servicenow_duration" {
  count = var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.project_name}-servicenow-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "100000"  # 100 seconds (approaching 120s timeout)
  alarm_description   = "Alert when ServiceNow ticket creation takes too long"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.servicenow_ticket_creator.function_name
  }

  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-servicenow-duration-alarm"
      Component = "ServiceNow Integration"
    }
  )
}
