# Dashboard Module - Website File Uploads
# Manages upload of dashboard files to S3 with dynamic API URL injection

# ===================================================================
# HTML FILES
# ===================================================================

resource "aws_s3_object" "index_html" {
  bucket       = var.dashboard_bucket_name
  key          = "index.html"
  source       = "${var.source_files_path}/index.html"
  content_type = "text/html"
  etag         = filemd5("${var.source_files_path}/index.html")
}

resource "aws_s3_object" "login_html" {
  bucket       = var.dashboard_bucket_name
  key          = "login.html"
  source       = "${var.source_files_path}/login.html"
  content_type = "text/html"
  etag         = filemd5("${var.source_files_path}/login.html")
}

resource "aws_s3_object" "error_html" {
  bucket       = var.dashboard_bucket_name
  key          = "error.html"
  source       = "${var.source_files_path}/error.html"
  content_type = "text/html"
  etag         = filemd5("${var.source_files_path}/error.html")
}

# ===================================================================
# JAVASCRIPT FILES
# ===================================================================

resource "aws_s3_object" "auth_js" {
  bucket       = var.dashboard_bucket_name
  key          = "auth.js"
  source       = "${var.source_files_path}/auth.js"
  content_type = "application/javascript"
  etag         = filemd5("${var.source_files_path}/auth.js")
}

# Dashboard.js with dynamic API URL injection
resource "aws_s3_object" "dashboard_js" {
  bucket       = var.dashboard_bucket_name
  key          = "dashboard.js"
  content_type = "application/javascript"

  # Read the file and replace the placeholder with the actual Lambda Function URL
  content = replace(
    file("${var.source_files_path}/dashboard.js"),
    "$${LAMBDA_FUNCTION_URL}",
    var.api_url
  )

  # Force update when API URL or file content changes
  etag = md5(replace(
    file("${var.source_files_path}/dashboard.js"),
    "$${LAMBDA_FUNCTION_URL}",
    var.api_url
  ))
}

# ===================================================================
# IMAGE FILES
# ===================================================================

resource "aws_s3_object" "postnl_logo" {
  bucket       = var.dashboard_bucket_name
  key          = "images/postnl-logo.png"
  source       = "${var.source_files_path}/images/postnl-logo.png"
  content_type = "image/png"
  etag         = filemd5("${var.source_files_path}/images/postnl-logo.png")
}

resource "aws_s3_object" "sogeti_logo" {
  bucket       = var.dashboard_bucket_name
  key          = "images/sogeti-logo.png"
  source       = "${var.source_files_path}/images/sogeti-logo.png"
  content_type = "image/png"
  etag         = filemd5("${var.source_files_path}/images/sogeti-logo.png")
}
