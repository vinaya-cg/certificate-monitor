# Lambda ACM Sync Module - ACM Certificate Synchronization
# Automated and manual synchronization from AWS Certificate Manager

locals {
  common_name      = "${var.project_name}-${var.environment}"
  lambda_name      = "${local.common_name}-acm-sync"
  lambda_source    = "${path.module}/../../../lambda/acm_certificate_sync.py"
}

# ===================================================================
# DATA SOURCE - Package Lambda Function
# ===================================================================

data "archive_file" "acm_sync_zip" {
  type        = "zip"
  source_file = local.lambda_source
  output_path = "${path.module}/acm_sync.zip"
}

# ===================================================================
# LAMBDA FUNCTION - ACM Sync
# ===================================================================

resource "aws_lambda_function" "acm_sync" {
  filename         = data.archive_file.acm_sync_zip.output_path
  function_name    = local.lambda_name
  role            = var.lambda_role_arn
  handler         = "acm_certificate_sync.lambda_handler"
  source_code_hash = data.archive_file.acm_sync_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 900  # 15 minutes for multi-account scanning
  memory_size     = 512

  environment {
    variables = {
      CERTIFICATES_TABLE = var.certificates_table_name
      REGION            = var.aws_region
      LOG_LEVEL         = "INFO"
    }
  }

  tags = merge(
    var.common_tags,
    {
      Name        = local.lambda_name
      Description = "Synchronize certificates from ACM"
    }
  )

  depends_on = [var.lambda_log_group_arn]
}

# ===================================================================
# CLOUDWATCH LOG GROUP
# ===================================================================

resource "aws_cloudwatch_log_group" "acm_sync" {
  name              = "/aws/lambda/${local.lambda_name}"
  retention_in_days = var.log_retention_days
}

# ===================================================================
# EVENTBRIDGE SCHEDULE - Daily at 2 AM UTC
# ===================================================================

resource "aws_cloudwatch_event_rule" "acm_sync_schedule" {
  name                = "${local.common_name}-acm-sync-schedule"
  description         = "Trigger ACM certificate sync daily at 2 AM UTC"
  schedule_expression = "cron(0 2 * * ? *)"  # Daily at 2 AM UTC

  tags = merge(
    var.common_tags,
    {
      Name = "${local.common_name}-acm-sync-schedule"
    }
  )
}

resource "aws_cloudwatch_event_target" "acm_sync_target" {
  rule      = aws_cloudwatch_event_rule.acm_sync_schedule.name
  target_id = "ACMSyncLambda"
  arn       = aws_lambda_function.acm_sync.arn
}

resource "aws_lambda_permission" "allow_eventbridge_acm_sync" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.acm_sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.acm_sync_schedule.arn
}

# ===================================================================
# IAM POLICY - Additional ACM and STS permissions
# ===================================================================

resource "aws_iam_policy" "acm_sync_policy" {
  name        = "${local.common_name}-acm-sync-policy"
  description = "Additional permissions for ACM sync Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "acm:ListCertificates",
          "acm:DescribeCertificate",
          "acm:GetCertificate"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sts:AssumeRole"
        ]
        Resource = "arn:aws:iam::*:role/ACMReadRole"  # Cross-account role
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          var.certificates_table_arn,
          "${var.certificates_table_arn}/index/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "acm_sync_policy_attach" {
  role       = var.lambda_role_name
  policy_arn = aws_iam_policy.acm_sync_policy.arn
}
