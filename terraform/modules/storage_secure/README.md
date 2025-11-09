# Storage Secure Module

This module creates private S3 buckets with encryption, versioning, and lifecycle policies for secure storage of dashboard files, certificate uploads, and logs.

## Purpose

Provides secure, encrypted S3 storage with proper access controls, lifecycle management, and versioning for application data.

## Resources Created

### Dashboard Bucket (`aws_s3_bucket.dashboard`)
- **Purpose**: Store dashboard static files (HTML, JS, CSS, images)
- **Public Access**: Blocked (private)
- **Access Method**: CloudFront Origin Access Identity (OAI) only
- **Versioning**: Disabled (static files)
- **Lifecycle**: None (files rarely change)

### Uploads Bucket (`aws_s3_bucket.uploads`)
- **Purpose**: Store uploaded Excel files for certificate import
- **Public Access**: Blocked (private)
- **Access Method**: Lambda functions only (via IAM role)
- **Versioning**: Enabled
- **Lifecycle**: 
  - 30 days → STANDARD_IA (Infrequent Access)
  - 90 days → GLACIER
  - 365 days → Delete

### Logs Bucket (`aws_s3_bucket.logs`)
- **Purpose**: Store application logs, CloudFront access logs
- **Public Access**: Blocked (private)
- **Access Method**: AWS services (CloudFront, Lambda) only
- **Versioning**: Enabled
- **Lifecycle**:
  - 90 days → GLACIER
  - 365 days → Delete

## Bucket Configurations

### Encryption (`aws_s3_bucket_server_side_encryption_configuration`)
All buckets use server-side encryption:
- **Algorithm**: AES256 (AWS-managed keys)
- **Default**: Encrypt all objects automatically
- **Cost**: Free (SSE-S3)

### Versioning (`aws_s3_bucket_versioning`)
Enabled for uploads and logs:
- **Benefits**: Accidental deletion protection, audit trail
- **Cost**: Storage charged for all versions
- **Recommendation**: Enable for production, optional for dev

### Public Access Block (`aws_s3_bucket_public_access_block`)
All buckets have public access blocked:
- `block_public_acls = true`
- `block_public_policy = true`
- `ignore_public_acls = true`
- `restrict_public_buckets = true`

### Lifecycle Rules (`aws_s3_bucket_lifecycle_configuration`)

#### Uploads Bucket Lifecycle
```hcl
rule {
  id     = "transition-to-ia"
  status = "Enabled"
  
  transition {
    days          = 30
    storage_class = "STANDARD_IA"
  }
  
  transition {
    days          = 90
    storage_class = "GLACIER"
  }
  
  expiration {
    days = 365
  }
}
```

#### Logs Bucket Lifecycle
```hcl
rule {
  id     = "archive-logs"
  status = "Enabled"
  
  transition {
    days          = 90
    storage_class = "GLACIER"
  }
  
  expiration {
    days = 365
  }
}
```

### CORS Configuration (`aws_s3_bucket_cors_configuration`)
Dashboard bucket only:
```hcl
cors_rule {
  allowed_headers = ["*"]
  allowed_methods = ["GET", "HEAD"]
  allowed_origins = ["https://${var.cloudfront_domain}"]
  expose_headers  = ["ETag"]
  max_age_seconds = 3600
}
```

### Bucket Policies

#### Dashboard Bucket Policy
Allows CloudFront OAI to read objects:
```json
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity E2CPB8IUR80ZRD"
  },
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::cert-management-dev-secure-dashboard-dz243x46/*"
}
```

#### Uploads Bucket Policy
Allows Lambda functions to read/write:
```json
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::123456789012:role/cert-management-dev-secure-lambda-role"
  },
  "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
  "Resource": "arn:aws:s3:::cert-management-dev-secure-uploads-dz243x46/*"
}
```

## Inputs

| Variable | Type | Description | Required |
|----------|------|-------------|----------|
| `project_name` | `string` | Project name prefix | Yes |
| `environment` | `string` | Environment name | Yes |
| `random_suffix` | `string` | Random suffix for unique bucket names | Yes |
| `cloudfront_oai_iam_arn` | `string` | CloudFront OAI IAM ARN for dashboard bucket policy | Yes |
| `cloudfront_domain` | `string` | CloudFront domain for CORS configuration | No (optional) |

## Outputs

| Output | Description | Used By |
|--------|-------------|---------|
| `dashboard_bucket_name` | Dashboard bucket name | Dashboard Secure module, CloudFront |
| `dashboard_bucket_id` | Dashboard bucket ID | CloudFront |
| `dashboard_bucket_arn` | Dashboard bucket ARN | IAM policies |
| `dashboard_bucket_regional_domain_name` | Dashboard bucket regional domain | CloudFront origin |
| `uploads_bucket_name` | Uploads bucket name | Lambda functions |
| `uploads_bucket_arn` | Uploads bucket ARN | IAM policies, S3 notifications |
| `logs_bucket_name` | Logs bucket name | CloudWatch, Lambda |
| `logs_bucket_arn` | Logs bucket ARN | IAM policies |

## Example Usage

```hcl
module "storage_secure" {
  source = "../../modules/storage_secure"

  project_name            = var.project_name
  environment             = var.environment
  random_suffix           = random_string.suffix.result
  cloudfront_oai_iam_arn  = module.cloudfront.cloudfront_oai_iam_arn
  cloudfront_domain       = module.cloudfront.distribution_domain_name
}
```

## Storage Classes

| Class | Use Case | Availability | Retrieval Time | Cost |
|-------|----------|--------------|----------------|------|
| **STANDARD** | Frequently accessed data | 99.99% | Milliseconds | $0.023/GB |
| **STANDARD_IA** | Infrequently accessed (30+ days) | 99.9% | Milliseconds | $0.0125/GB + $0.01/GB retrieval |
| **GLACIER** | Archive (90+ days) | 99.99% | Minutes-hours | $0.004/GB + retrieval fees |
| **DEEP_ARCHIVE** | Long-term archive (180+ days) | 99.99% | 12 hours | $0.00099/GB + retrieval fees |

## Lifecycle Transition Logic

```
Dashboard Bucket:
  Upload → STANDARD (no transitions, files rarely change)

Uploads Bucket:
  Upload → STANDARD (0-30 days)
         → STANDARD_IA (30-90 days)
         → GLACIER (90-365 days)
         → DELETE (365+ days)

Logs Bucket:
  Upload → STANDARD (0-90 days)
         → GLACIER (90-365 days)
         → DELETE (365+ days)
```

## Bucket Naming

Buckets use random suffixes for global uniqueness:

```
{project_name}-{environment}-{bucket_type}-{random_suffix}

Examples:
  cert-management-dev-secure-dashboard-dz243x46
  cert-management-dev-secure-uploads-dz243x46
  cert-management-dev-secure-logs-dz243x46
```

**Why?** S3 bucket names must be globally unique across all AWS accounts.

## Security Features

### Encryption at Rest
- **Method**: SSE-S3 (server-side encryption with S3-managed keys)
- **Algorithm**: AES-256
- **Automatic**: All new objects encrypted by default
- **Cost**: Free

### Encryption in Transit
- **Protocol**: TLS 1.2+
- **Enforcement**: Bucket policies can require HTTPS
- **Example**:
  ```json
  {
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": "arn:aws:s3:::bucket-name/*",
    "Condition": {
      "Bool": {"aws:SecureTransport": "false"}
    }
  }
  ```

### Access Control
- **Public Access**: Blocked at bucket level
- **IAM Policies**: Grant least-privilege access to Lambda
- **OAI**: CloudFront-only access to dashboard bucket
- **Versioning**: Prevent accidental deletions (uploads, logs)

## Monitoring

### S3 Metrics
- **BucketSizeBytes**: Total bucket size
- **NumberOfObjects**: Object count
- **AllRequests**: Request count
- **4xxErrors**: Client errors
- **5xxErrors**: Server errors

View metrics:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name BucketSizeBytes \
  --dimensions Name=BucketName,Value=cert-management-dev-secure-uploads-dz243x46 Name=StorageType,Value=StandardStorage \
  --start-time 2025-11-08T00:00:00Z \
  --end-time 2025-11-09T00:00:00Z \
  --period 86400 \
  --statistics Average
```

### S3 Event Notifications
Uploads bucket triggers Lambda on file upload:
```hcl
resource "aws_s3_bucket_notification" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  lambda_function {
    lambda_function_arn = var.excel_processor_lambda_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".xlsx"
  }
}
```

## Operations

### Upload File to Dashboard Bucket
```bash
aws s3 cp index.html s3://cert-management-dev-secure-dashboard-dz243x46/ \
  --content-type text/html \
  --cache-control "no-cache, no-store, must-revalidate"
```

### Upload Excel File to Uploads Bucket
```bash
aws s3 cp certificates.xlsx s3://cert-management-dev-secure-uploads-dz243x46/
```

### List Objects
```bash
aws s3 ls s3://cert-management-dev-secure-uploads-dz243x46/
```

### Download Object
```bash
aws s3 cp s3://cert-management-dev-secure-uploads-dz243x46/certificates.xlsx ./
```

### Delete Object
```bash
aws s3 rm s3://cert-management-dev-secure-uploads-dz243x46/certificates.xlsx
```

### Empty Bucket (for destroy)
```bash
aws s3 rm s3://cert-management-dev-secure-dashboard-dz243x46/ --recursive
```

### View Object Versions
```bash
aws s3api list-object-versions \
  --bucket cert-management-dev-secure-uploads-dz243x46 \
  --prefix certificates.xlsx
```

### Restore from Version
```bash
aws s3api get-object \
  --bucket cert-management-dev-secure-uploads-dz243x46 \
  --key certificates.xlsx \
  --version-id abc123... \
  ./certificates-restored.xlsx
```

## Cost Estimation

S3 storage costs (eu-west-1):

| Bucket | Storage | Class | Objects | Monthly Cost |
|--------|---------|-------|---------|--------------|
| Dashboard | 10 MB | STANDARD | 20 files | $0.0002 |
| Uploads | 500 MB | STANDARD/IA/GLACIER | 100 files | $0.008 |
| Logs | 1 GB | STANDARD/GLACIER | 1000 files | $0.02 |
| **Total** | | | | **~$0.03/month** |

**Note**: First 5 GB storage free (AWS Free Tier)

## Troubleshooting

### Issue: AccessDenied on dashboard files
**Cause**: CloudFront OAI not in bucket policy  
**Solution**: Verify OAI ARN matches in bucket policy

### Issue: CORS errors when accessing S3 directly
**Cause**: Access must go through CloudFront, not S3 directly  
**Solution**: Use CloudFront URL, not S3 URL

### Issue: Cannot delete bucket (BucketNotEmpty)
**Cause**: Bucket contains objects  
**Solution**: Empty bucket first:
```bash
aws s3 rm s3://bucket-name/ --recursive
```

### Issue: High storage costs
**Cause**: Old versions not deleted, lifecycle not working  
**Solution**: Check lifecycle rules, delete old versions manually if needed

## Best Practices

1. **Encryption**: Always enable SSE-S3 (free, no performance impact)
2. **Versioning**: Enable for important data (uploads, logs)
3. **Lifecycle**: Set up lifecycle rules to reduce costs
4. **Public Access**: Always block public access unless specifically needed
5. **Bucket Policies**: Grant least-privilege access only
6. **Naming**: Use random suffixes for global uniqueness
7. **Monitoring**: Set up CloudWatch alarms for bucket size, errors
8. **CORS**: Restrict to specific domains only

## Dependencies

- **CloudFront**: Requires OAI ARN for dashboard bucket policy
- **Random String**: Requires random suffix for unique bucket names

## Related Modules

- **CloudFront**: Serves dashboard bucket content
- **Dashboard Secure**: Uploads files to dashboard bucket
- **Lambda Secure**: Reads/writes to uploads bucket
- **Monitoring**: Monitors bucket metrics

## References

- [S3 Documentation](https://docs.aws.amazon.com/s3/)
- [S3 Encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html)
- [S3 Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [S3 Pricing](https://aws.amazon.com/s3/pricing/)
