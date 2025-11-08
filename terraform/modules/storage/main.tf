# Storage Module - S3 Buckets
# Manages dashboard hosting, file uploads, and logging buckets

locals {
  common_name = "${var.project_name}-${var.environment}"
}

# ===================================================================
# DASHBOARD HOSTING BUCKET (Public Website)
# ===================================================================

resource "aws_s3_bucket" "dashboard" {
  bucket = "${local.common_name}-dashboard-${var.bucket_suffix}"
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

# ===================================================================
# UPLOADS BUCKET (Certificate file uploads)
# ===================================================================

resource "aws_s3_bucket" "uploads" {
  bucket        = "${local.common_name}-uploads-${var.bucket_suffix}"
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

# ===================================================================
# LOGS BUCKET (Application logs and processing logs)
# ===================================================================

resource "aws_s3_bucket" "logs" {
  bucket = "${local.common_name}-logs-${var.bucket_suffix}"
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
