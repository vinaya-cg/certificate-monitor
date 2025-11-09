# CloudFront Distribution for Secure Certificate Dashboard
# Provides HTTPS access to private S3 bucket with caching

# Origin Access Identity for S3
resource "aws_cloudfront_origin_access_identity" "dashboard" {
  comment = "OAI for ${var.project_name}-${var.environment} dashboard"
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "dashboard" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.project_name} ${var.environment} Certificate Dashboard"
  default_root_object = "index.html"
  price_class         = var.price_class
  http_version        = "http2and3"

  # S3 Origin
  origin {
    domain_name = var.s3_bucket_regional_domain_name
    origin_id   = "S3-${var.s3_bucket_id}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.dashboard.cloudfront_access_identity_path
    }

    # Custom headers (optional, for additional security)
    custom_header {
      name  = "X-Origin-Verify"
      value = var.origin_verify_secret
    }
  }

  # Default cache behavior
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "S3-${var.s3_bucket_id}"

    # Forwarding configuration
    forwarded_values {
      query_string = false
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "none"
      }
    }

    # Viewer protocol policy (redirect HTTP to HTTPS)
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600  # 1 hour
    max_ttl                = 86400 # 24 hours
    compress               = true

    # Lambda@Edge functions (if needed later for auth)
    # function_association {
    #   event_type   = "viewer-request"
    #   function_arn = var.lambda_edge_arn
    # }
  }

  # Cache behavior for static assets
  ordered_cache_behavior {
    path_pattern     = "/images/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "S3-${var.s3_bucket_id}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400  # 24 hours
    max_ttl                = 31536000 # 1 year
    compress               = true
  }

  # Cache behavior for JavaScript/CSS
  ordered_cache_behavior {
    path_pattern     = "*.js"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "S3-${var.s3_bucket_id}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600  # 1 hour
    max_ttl                = 86400 # 24 hours
    compress               = true
  }

  # Restrictions (can add geographic restrictions later)
  restrictions {
    geo_restriction {
      restriction_type = "none"
      # locations        = ["US", "CA", "GB", "DE"] # Example: allow only these countries
    }
  }

  # SSL/TLS Certificate
  viewer_certificate {
    cloudfront_default_certificate = var.use_custom_domain ? false : true
    acm_certificate_arn            = var.use_custom_domain ? var.acm_certificate_arn : null
    ssl_support_method             = var.use_custom_domain ? "sni-only" : null
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  # Custom domain (if provided)
  aliases = var.use_custom_domain ? var.custom_domain_names : []

  # Custom error responses
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
    error_caching_min_ttl = 10
  }

  # Logging configuration (optional)
  dynamic "logging_config" {
    for_each = var.enable_logging ? [1] : []
    content {
      include_cookies = false
      bucket          = var.logging_bucket_domain_name
      prefix          = "cloudfront-logs/"
    }
  }

  # WAF Web ACL (optional, can add later)
  web_acl_id = var.web_acl_id
}

# S3 Bucket Policy to allow CloudFront OAI access
resource "aws_s3_bucket_policy" "cloudfront_access" {
  bucket = var.s3_bucket_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAI"
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.dashboard.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${var.s3_bucket_arn}/*"
      }
    ]
  })
}
