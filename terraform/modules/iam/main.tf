# IAM Module - Roles and Policies
# Manages Lambda execution role and policies

locals {
  common_name = "${var.project_name}-${var.environment}"
}

# ===================================================================
# LAMBDA EXECUTION ROLE
# ===================================================================

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

# ===================================================================
# LAMBDA POLICY
# ===================================================================

resource "aws_iam_policy" "lambda_policy" {
  name        = "${local.common_name}-lambda-policy"
  description = "Policy for certificate management Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs permissions
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:*"
      },
      # DynamoDB permissions
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
          var.certificates_table_arn,
          "${var.certificates_table_arn}/*",
          var.logs_table_arn,
          "${var.logs_table_arn}/*"
        ]
      },
      # S3 permissions
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.uploads_bucket_arn,
          "${var.uploads_bucket_arn}/*",
          var.logs_bucket_arn,
          "${var.logs_bucket_arn}/*"
        ]
      },
      # SES permissions
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

# ===================================================================
# POLICY ATTACHMENTS
# ===================================================================

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
