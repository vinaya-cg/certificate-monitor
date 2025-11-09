# CloudFront Module

This module creates an AWS CloudFront distribution for serving the certificate dashboard over HTTPS with optimal performance and security.

## Purpose

Provides a secure, fast, globally-distributed CDN for the static dashboard files stored in S3, with HTTPS enforcement and Origin Access Identity (OAI) for S3 bucket security.

## Resources Created

### CloudFront Origin Access Identity (`aws_cloudfront_origin_access_identity.main`)
- **Purpose**: Allows CloudFront to access private S3 bucket
- **Comment**: `{project_name}-{environment} OAI`
- **Security**: S3 bucket policy grants access only to this OAI

### CloudFront Distribution (`aws_cloudfront_distribution.main`)
- **Origin**: S3 bucket (dashboard files)
- **Default Root Object**: `index.html`
- **Price Class**: `PriceClass_100` (North America, Europe)
- **Enabled**: `true`
- **HTTP Version**: `http2and3` (HTTP/2 and HTTP/3 support)

#### Cache Behavior
- **Allowed Methods**: `GET`, `HEAD`, `OPTIONS`
- **Cached Methods**: `GET`, `HEAD`
- **Viewer Protocol Policy**: `redirect-to-https` (force HTTPS)
- **Compress**: `true` (gzip/brotli compression)
- **TTL**:
  - Min: 0 seconds
  - Default: 3600 seconds (1 hour)
  - Max: 86400 seconds (24 hours)
- **Query String Forwarding**: Enabled
- **Cookie Forwarding**: None

#### Custom Error Responses
- **404 Errors**: Redirect to `/error.html` with 200 status code
- **403 Errors**: Redirect to `/error.html` with 200 status code

#### SSL/TLS Configuration
- **Certificate**: CloudFront default certificate
- **Minimum Protocol Version**: `TLSv1.2_2021`
- **SSL Support Method**: `sni-only` (Server Name Indication)

#### Geographic Restrictions
- **Type**: None (available worldwide)

#### Logging
- **Access Logs**: Disabled (can be enabled by adding logging configuration)

## Inputs

| Variable | Type | Description | Required |
|----------|------|-------------|----------|
| `bucket_id` | `string` | S3 bucket ID for origin | Yes |
| `bucket_regional_domain_name` | `string` | S3 bucket regional domain name | Yes |
| `project_name` | `string` | Project name prefix | Yes |
| `environment` | `string` | Environment name | Yes |

## Outputs

| Output | Description | Used By |
|--------|-------------|---------|
| `distribution_id` | CloudFront distribution ID | Cache invalidation, monitoring |
| `distribution_arn` | CloudFront distribution ARN | IAM policies, tagging |
| `distribution_domain_name` | CloudFront domain name | Dashboard access URL |
| `cloudfront_oai_iam_arn` | OAI IAM ARN | S3 bucket policy |

## Example Usage

```hcl
module "cloudfront" {
  source = "../../modules/cloudfront"

  bucket_id                   = module.storage_secure.dashboard_bucket_id
  bucket_regional_domain_name = module.storage_secure.dashboard_bucket_regional_domain_name
  project_name                = var.project_name
  environment                 = var.environment
}
```

## Security Features

### HTTPS Enforcement
- **Redirect to HTTPS**: All HTTP requests automatically redirected to HTTPS
- **TLS 1.2+**: Only modern TLS versions supported (TLS 1.0/1.1 disabled)
- **SNI**: Server Name Indication reduces costs and improves compatibility

### Origin Access Identity (OAI)
- **Private S3 Bucket**: S3 bucket not publicly accessible
- **OAI-Only Access**: S3 bucket policy allows reads only from CloudFront OAI
- **Prevents Direct Access**: Users cannot bypass CloudFront to access S3 directly

### Content Security
- **Compression**: Automatic gzip/brotli compression reduces bandwidth
- **HTTP/2 and HTTP/3**: Modern protocols for improved performance
- **Custom Error Pages**: Prevents information disclosure from default error messages

## Performance Features

### Global Distribution
- **Edge Locations**: Deployed to AWS edge locations worldwide
- **Low Latency**: Content served from nearest edge location
- **Price Class 100**: Optimized for North America and Europe

### Caching
- **Default TTL**: 1 hour (3600 seconds)
- **Max TTL**: 24 hours (86400 seconds)
- **Query String Caching**: Enabled (different query strings = different cache entries)
- **Compression**: Automatic gzip/brotli for text files

### HTTP/2 and HTTP/3
- **Multiplexing**: Multiple requests over single connection
- **Header Compression**: Reduced overhead
- **Server Push**: (if configured) push resources before requested

## Cache Invalidation

When updating dashboard files, invalidate the CloudFront cache:

```bash
# Invalidate all files
aws cloudfront create-invalidation \
  --distribution-id E2CPB8IUR80ZRD \
  --paths "/*"

# Invalidate specific files
aws cloudfront create-invalidation \
  --distribution-id E2CPB8IUR80ZRD \
  --paths "/dashboard.js" "/auth-cognito.js" "/index.html"

# Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id E2CPB8IUR80ZRD \
  --id <invalidation-id>
```

**Note**: First 1,000 invalidation paths per month are free, then $0.005 per path.

## Accessing the Dashboard

After deployment, access the dashboard at the CloudFront URL:

```
https://d3bqyfjow8topp.cloudfront.net
```

This URL is provided in Terraform outputs:
```hcl
output "cloudfront_distribution_url" {
  value = "https://${module.cloudfront.distribution_domain_name}"
}
```

## Custom Domain (Optional)

To use a custom domain (e.g., `dashboard.example.com`):

1. **Request ACM Certificate** in `us-east-1` region:
   ```bash
   aws acm request-certificate \
     --domain-name dashboard.example.com \
     --validation-method DNS \
     --region us-east-1
   ```

2. **Update CloudFront Distribution**:
   ```hcl
   resource "aws_cloudfront_distribution" "main" {
     # ... existing configuration ...
     
     aliases = ["dashboard.example.com"]
     
     viewer_certificate {
       acm_certificate_arn      = "arn:aws:acm:us-east-1:123456789012:certificate/abc..."
       ssl_support_method       = "sni-only"
       minimum_protocol_version = "TLSv1.2_2021"
     }
   }
   ```

3. **Create Route53 Record** (or update DNS):
   ```hcl
   resource "aws_route53_record" "dashboard" {
     zone_id = "Z123456789ABC"
     name    = "dashboard.example.com"
     type    = "A"
     
     alias {
       name                   = aws_cloudfront_distribution.main.domain_name
       zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
       evaluate_target_health = false
     }
   }
   ```

## Monitoring

### CloudWatch Metrics
CloudFront automatically publishes metrics to CloudWatch:

- **Requests**: Total number of requests
- **BytesDownloaded**: Total bytes served
- **BytesUploaded**: Total bytes uploaded
- **4xxErrorRate**: Client error rate
- **5xxErrorRate**: Server error rate
- **TotalErrorRate**: Combined error rate

View metrics:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value=E2CPB8IUR80ZRD \
  --start-time 2025-11-08T00:00:00Z \
  --end-time 2025-11-09T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### Access Logs (Optional)

Enable access logs to track all requests:

```hcl
resource "aws_cloudfront_distribution" "main" {
  # ... existing configuration ...
  
  logging_config {
    include_cookies = false
    bucket          = "${var.logs_bucket_name}.s3.amazonaws.com"
    prefix          = "cloudfront/"
  }
}
```

## Troubleshooting

### Issue: CloudFront shows old content after update
**Cause**: Cached content not invalidated  
**Solution**: Create invalidation:
```bash
aws cloudfront create-invalidation --distribution-id E2CPB8IUR80ZRD --paths "/*"
```

### Issue: 403 Forbidden errors
**Cause**: S3 bucket policy doesn't allow OAI access  
**Solution**: Check S3 bucket policy includes OAI ARN:
```json
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity E2CPB8IUR80ZRD"
  },
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::bucket-name/*"
}
```

### Issue: Slow initial load times
**Cause**: Cold cache, edge location hasn't cached content yet  
**Solution**: Normal behavior, subsequent requests will be fast

### Issue: Custom domain not working
**Cause**: ACM certificate not in us-east-1 region  
**Solution**: CloudFront requires ACM certificates in us-east-1 only

## Cost Estimation

CloudFront pricing (us-east-1):

| Component | Usage | Price | Monthly Cost |
|-----------|-------|-------|--------------|
| Data Transfer | 10 GB to internet | $0.085/GB | $0.85 |
| HTTP/HTTPS Requests | 10,000 requests | $0.0075 per 10K | $0.01 |
| Invalidations | 1,000 paths | Free | $0.00 |
| **Total** | | | **~$0.86/month** |

**Note**: Costs vary by region and usage. Use [AWS Pricing Calculator](https://calculator.aws) for accurate estimates.

## Best Practices

1. **Cache Invalidation**: Invalidate only changed files, not entire distribution
2. **Versioned Filenames**: Use version hashes in filenames (e.g., `app.v2.js`) to avoid cache issues
3. **Compression**: Ensure compression enabled for text files (HTML, CSS, JS)
4. **HTTPS Only**: Always redirect HTTP to HTTPS
5. **Custom Error Pages**: Provide user-friendly error pages
6. **Monitoring**: Set up CloudWatch alarms for error rates
7. **Access Logs**: Enable for production environments
8. **Custom Domain**: Use custom domain with ACM certificate for branding

## Dependencies

- **S3 Bucket**: Requires dashboard S3 bucket created first
- **Dashboard Files**: S3 bucket must contain index.html, error.html

## Related Modules

- **Storage Secure**: Provides S3 bucket for CloudFront origin
- **Dashboard Secure**: Uploads dashboard files to S3
- **Cognito**: Provides callback URL for OAuth flows

## References

- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/)
- [Using OAI with S3](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [Cache Invalidation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html)
