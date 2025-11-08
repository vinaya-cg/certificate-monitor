# Dashboard Files Upload
# Automatically upload dashboard files to S3 with correct API URL

# Upload index.html
resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.dashboard.id
  key          = "index.html"
  source       = "${path.module}/../dashboard/index.html"
  content_type = "text/html"
  etag         = filemd5("${path.module}/../dashboard/index.html")
}

# Upload login.html
resource "aws_s3_object" "login_html" {
  bucket       = aws_s3_bucket.dashboard.id
  key          = "login.html"
  source       = "${path.module}/../dashboard/login.html"
  content_type = "text/html"
  etag         = filemd5("${path.module}/../dashboard/login.html")
}

# Upload error.html
resource "aws_s3_object" "error_html" {
  bucket       = aws_s3_bucket.dashboard.id
  key          = "error.html"
  source       = "${path.module}/../dashboard/error.html"
  content_type = "text/html"
  etag         = filemd5("${path.module}/../dashboard/error.html")
}

# Upload auth.js
resource "aws_s3_object" "auth_js" {
  bucket       = aws_s3_bucket.dashboard.id
  key          = "auth.js"
  source       = "${path.module}/../dashboard/auth.js"
  content_type = "application/javascript"
  etag         = filemd5("${path.module}/../dashboard/auth.js")
}

# Upload dashboard.js with API URL dynamically injected
resource "aws_s3_object" "dashboard_js" {
  bucket       = aws_s3_bucket.dashboard.id
  key          = "dashboard.js"
  content_type = "application/javascript"
  
  # Read the file and replace the placeholder with the actual Lambda Function URL
  content = replace(
    file("${path.module}/../dashboard/dashboard.js"),
    "$${LAMBDA_FUNCTION_URL}",
    aws_lambda_function_url.dashboard_api_url.function_url
  )
  
  # Force update when Lambda URL changes
  etag = md5(replace(
    file("${path.module}/../dashboard/dashboard.js"),
    "$${LAMBDA_FUNCTION_URL}",
    aws_lambda_function_url.dashboard_api_url.function_url
  ))
  
  depends_on = [
    aws_lambda_function_url.dashboard_api_url
  ]
}

# Upload PostNL logo
resource "aws_s3_object" "postnl_logo" {
  bucket       = aws_s3_bucket.dashboard.id
  key          = "images/postnl-logo.png"
  source       = "${path.module}/../dashboard/images/postnl-logo.png"
  content_type = "image/png"
  etag         = filemd5("${path.module}/../dashboard/images/postnl-logo.png")
}

# Upload Sogeti logo
resource "aws_s3_object" "sogeti_logo" {
  bucket       = aws_s3_bucket.dashboard.id
  key          = "images/sogeti-logo.png"
  source       = "${path.module}/../dashboard/images/sogeti-logo.png"
  content_type = "image/png"
  etag         = filemd5("${path.module}/../dashboard/images/sogeti-logo.png")
}
