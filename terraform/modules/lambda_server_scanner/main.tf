# Server Certificate Scanner Module
# Scans certificates from Windows and Linux servers using AWS Systems Manager

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Lambda function for server certificate scanning
resource "aws_lambda_function" "server_cert_scanner" {
  filename         = data.archive_file.scanner_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-server-cert-scanner"
  role            = var.lambda_role_arn
  handler         = "server_certificate_scanner.lambda_handler"
  source_code_hash = data.archive_file.scanner_lambda.output_base64sha256
  runtime         = "python3.9"
  timeout         = 900  # 15 minutes for scanning multiple servers
  memory_size     = 512

  environment {
    variables = {
      CERTIFICATES_TABLE  = var.certificates_table_name
      REGION             = var.aws_region
      SSM_DOCUMENT_WINDOWS = aws_ssm_document.windows_cert_scan.name
      SSM_DOCUMENT_LINUX   = aws_ssm_document.linux_cert_scan.name
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-server-cert-scanner"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Package Lambda function
data "archive_file" "scanner_lambda" {
  type        = "zip"
  source_file = "${path.module}/../../../lambda/server_certificate_scanner.py"
  output_path = "${path.module}/lambda_scanner.zip"
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "scanner_logs" {
  name              = "/aws/lambda/${aws_lambda_function.server_cert_scanner.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-server-scanner-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# EventBridge rule for scheduled scanning (daily at 9:30 AM UTC)
resource "aws_cloudwatch_event_rule" "server_scan_schedule" {
  count               = var.enable_scheduled_scan ? 1 : 0
  name                = "${var.project_name}-${var.environment}-server-cert-scan-schedule"
  description         = "Trigger server certificate scanning daily"
  schedule_expression = var.scan_schedule

  tags = {
    Name        = "${var.project_name}-${var.environment}-server-scan-schedule"
    Environment = var.environment
    Project     = var.project_name
  }
}

# EventBridge target
resource "aws_cloudwatch_event_target" "server_scan_lambda" {
  count = var.enable_scheduled_scan ? 1 : 0
  rule  = aws_cloudwatch_event_rule.server_scan_schedule[0].name
  arn   = aws_lambda_function.server_cert_scanner.arn
}

# Lambda permission for EventBridge
resource "aws_lambda_permission" "allow_eventbridge" {
  count         = var.enable_scheduled_scan ? 1 : 0
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.server_cert_scanner.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.server_scan_schedule[0].arn
}

# SSM Document for Windows certificate scanning
resource "aws_ssm_document" "windows_cert_scan" {
  name            = "${var.project_name}-${var.environment}-windows-cert-scan"
  document_type   = "Command"
  document_format = "JSON"
  
  content = file("${path.module}/../../../ssm-documents/windows-certificate-scan.json")

  tags = {
    Name        = "${var.project_name}-${var.environment}-windows-cert-scan"
    Environment = var.environment
    Project     = var.project_name
    Platform    = "Windows"
  }
}

# SSM Document for Linux certificate scanning
resource "aws_ssm_document" "linux_cert_scan" {
  name            = "${var.project_name}-${var.environment}-linux-cert-scan"
  document_type   = "Command"
  document_format = "JSON"
  
  content = file("${path.module}/../../../ssm-documents/linux-certificate-scan.json")

  tags = {
    Name        = "${var.project_name}-${var.environment}-linux-cert-scan"
    Environment = var.environment
    Project     = var.project_name
    Platform    = "Linux"
  }
}

# IAM policy for Lambda to execute SSM commands
resource "aws_iam_role_policy" "scanner_ssm_policy" {
  name = "${var.project_name}-${var.environment}-scanner-ssm-policy"
  role = var.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:SendCommand",
          "ssm:GetCommandInvocation",
          "ssm:ListCommandInvocations",
          "ssm:DescribeInstanceInformation",
          "ssm:ListInstanceAssociations"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch alarms (optional)
resource "aws_cloudwatch_metric_alarm" "scanner_errors" {
  count               = var.enable_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-server-scanner-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert when server certificate scanner encounters errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.server_cert_scanner.function_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-server-scanner-alarm"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "scanner_duration" {
  count               = var.enable_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-server-scanner-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Maximum"
  threshold           = 840000  # 14 minutes (close to 15-minute timeout)
  alarm_description   = "Alert when server scanner is approaching timeout"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.server_cert_scanner.function_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-server-scanner-duration-alarm"
    Environment = var.environment
  }
}
