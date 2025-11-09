# Lambda Secure Module

This module creates AWS Lambda functions for certificate processing with proper IAM roles, CloudWatch logging, and S3 event triggers.

## Purpose

Provides serverless compute functions for:
1. Daily certificate expiry monitoring and email notifications
2. Excel file processing and certificate import
3. REST API backend for dashboard CRUD operations

## Resources Created

### Lambda Functions

#### 1. Certificate Monitor (`aws_lambda_function.certificate_monitor`)
- **Purpose**: Daily scheduled check for expiring certificates
- **Runtime**: Python 3.9
- **Handler**: `certificate_monitor.lambda_handler`
- **Memory**: 512 MB
- **Timeout**: 300 seconds (5 minutes)
- **Trigger**: EventBridge rule (daily at 9 AM UTC)
- **Permissions**: Read DynamoDB, send SES emails

#### 2. Excel Processor (`aws_lambda_function.excel_processor`)
- **Purpose**: Process uploaded Excel files and import certificates
- **Runtime**: Python 3.9
- **Handler**: `excel_processor.lambda_handler`
- **Memory**: 1024 MB (needs memory for pandas/openpyxl)
- **Timeout**: 900 seconds (15 minutes)
- **Trigger**: S3 upload event (*.xlsx files)
- **Permissions**: Read S3, write DynamoDB, write CloudWatch Logs

#### 3. Dashboard API (`aws_lambda_function.dashboard_api`)
- **Purpose**: REST API backend for certificate CRUD operations
- **Runtime**: Python 3.9
- **Handler**: `dashboard_api.lambda_handler`
- **Memory**: 256 MB
- **Timeout**: 30 seconds
- **Trigger**: API Gateway requests
- **Permissions**: Read/write DynamoDB, write CloudWatch Logs

### CloudWatch Log Groups
- `/aws/lambda/{project_name}-{environment}-certificate-monitor`
- `/aws/lambda/{project_name}-{environment}-excel-processor`
- `/aws/lambda/{project_name}-{environment}-dashboard-api`
- **Retention**: 30 days
- **Encryption**: AWS-managed keys

### S3 Event Notification (`aws_s3_bucket_notification.uploads`)
- **Bucket**: Uploads bucket
- **Event**: `s3:ObjectCreated:*`
- **Filter**: `*.xlsx` files only
- **Target**: excel-processor Lambda function

### Lambda Permissions
- **EventBridge to certificate-monitor**: Allows scheduled invocations
- **S3 to excel-processor**: Allows S3 event invocations
- **API Gateway to dashboard-api**: Allows HTTP request invocations

## Inputs

| Variable | Type | Description | Required |
|----------|------|-------------|----------|
| `project_name` | `string` | Project name prefix | Yes |
| `environment` | `string` | Environment name | Yes |
| `lambda_role_arn` | `string` | IAM role ARN for Lambda execution | Yes |
| `certificates_table_name` | `string` | DynamoDB certificates table name | Yes |
| `logs_table_name` | `string` | DynamoDB logs table name | Yes |
| `uploads_bucket_name` | `string` | S3 uploads bucket name | Yes |
| `uploads_bucket_arn` | `string` | S3 uploads bucket ARN | Yes |
| `sender_email` | `string` | SES verified email for notifications | Yes |
| `aws_region` | `string` | AWS region | Yes |

## Outputs

| Output | Description | Used By |
|--------|-------------|---------|
| `certificate_monitor_function_arn` | Certificate monitor ARN | EventBridge target |
| `certificate_monitor_function_name` | Certificate monitor name | CloudWatch, monitoring |
| `excel_processor_function_arn` | Excel processor ARN | S3 notification |
| `excel_processor_function_name` | Excel processor name | CloudWatch, monitoring |
| `dashboard_api_function_arn` | Dashboard API ARN | API Gateway integration |
| `dashboard_api_function_name` | Dashboard API name | CloudWatch, monitoring |

## Example Usage

```hcl
module "lambda_secure" {
  source = "../../modules/lambda_secure"

  project_name             = var.project_name
  environment              = var.environment
  lambda_role_arn          = module.iam.lambda_role_arn
  certificates_table_name  = module.database.certificates_table_name
  logs_table_name          = module.database.logs_table_name
  uploads_bucket_name      = module.storage_secure.uploads_bucket_name
  uploads_bucket_arn       = module.storage_secure.uploads_bucket_arn
  sender_email             = var.sender_email
  aws_region               = var.aws_region
}
```

## Lambda Function Details

### certificate_monitor.py

**Purpose**: Check for certificates expiring within threshold and send email notifications

**Environment Variables**:
```python
CERTIFICATES_TABLE = 'cert-management-dev-secure-certificates'
LOGS_TABLE = 'cert-management-dev-secure-certificate-logs'
SENDER_EMAIL = 'vinaya-c.nayanegali@capgemini.com'
REGION = 'eu-west-1'
EXPIRY_THRESHOLD_DAYS = 30
```

**Logic**:
```python
def lambda_handler(event, context):
    # 1. Calculate expiry threshold (now + 30 days)
    # 2. Query DynamoDB for certificates expiring within threshold
    # 3. Group certificates by owner email
    # 4. Send SES email to each owner with list of expiring certificates
    # 5. Log actions to certificate_logs table
    # 6. Return summary
```

**Email Template**:
```
Subject: Certificate Expiry Alert - {count} certificates expiring soon

Dear {owner},

The following certificates owned by you will expire within the next 30 days:

1. *.example.com - Expires: 2025-12-15 (25 days remaining)
2. *.test.com - Expires: 2025-12-20 (30 days remaining)

Please renew these certificates before they expire.

Best regards,
Certificate Management System
```

**Invocation**:
- **Scheduled**: Daily at 9 AM UTC via EventBridge
- **Manual**: `aws lambda invoke --function-name cert-management-dev-secure-certificate-monitor response.json`

### excel_processor.py

**Purpose**: Parse uploaded Excel files and import certificates to DynamoDB

**Environment Variables**:
```python
CERTIFICATES_TABLE = 'cert-management-dev-secure-certificates'
LOGS_TABLE = 'cert-management-dev-secure-certificate-logs'
REGION = 'eu-west-1'
```

**Logic**:
```python
def lambda_handler(event, context):
    # 1. Extract bucket and key from S3 event
    # 2. Download Excel file from S3
    # 3. Parse using openpyxl/pandas
    # 4. Validate each row (required fields, date format, email format)
    # 5. Generate CertificateID (UUID) for each row
    # 6. Batch write to DynamoDB certificates table
    # 7. Log import action to logs table
    # 8. Return summary (success count, error count)
```

**Excel Format**:
| CommonName | ExpiryDate | Environment | OwnerEmail | SupportEmail | Status |
|------------|------------|-------------|------------|--------------|--------|
| *.example.com | 2025-12-31 | PROD | owner@example.com | support@example.com | active |

**Validation**:
- CommonName: Required, string
- ExpiryDate: Required, valid date (YYYY-MM-DD)
- Environment: Required, one of [DEV, TEST, PROD]
- OwnerEmail: Required, valid email format
- SupportEmail: Optional, valid email format if provided
- Status: Required, one of [active, expired, expiring-soon, revoked]

**Invocation**:
- **Automatic**: Triggered when *.xlsx file uploaded to uploads bucket
- **Event Example**:
  ```json
  {
    "Records": [{
      "s3": {
        "bucket": {"name": "cert-management-dev-secure-uploads-dz243x46"},
        "object": {"key": "certificates.xlsx"}
      }
    }]
  }
  ```

### dashboard_api.py

**Purpose**: Handle REST API requests from dashboard (GET, POST, PUT, DELETE)

**Environment Variables**:
```python
CERTIFICATES_TABLE = 'cert-management-dev-secure-certificates'
LOGS_TABLE = 'cert-management-dev-secure-certificate-logs'
REGION = 'eu-west-1'
```

**Logic**:
```python
def lambda_handler(event, context):
    # 1. Parse HTTP method and path from event
    # 2. Extract user context from Cognito authorizer
    # 3. Route request to appropriate handler:
    #    - GET    → list_certificates() or get_certificate()
    #    - POST   → create_certificate()
    #    - PUT    → update_certificate()
    #    - DELETE → delete_certificate()
    # 4. Validate user permissions (RBAC check)
    # 5. Perform DynamoDB operation
    # 6. Log action to logs table
    # 7. Return JSON response
```

**Request Handlers**:

```python
def list_certificates(query_params, user):
    # Query DynamoDB with filters (status, environment, owner)
    # Return list of certificates as JSON

def get_certificate(cert_id, user):
    # Get single certificate by ID
    # Return certificate details as JSON

def create_certificate(body, user):
    # Validate input
    # Check user has CREATE permission (Admin, Operator)
    # Generate CertificateID
    # Put item to DynamoDB
    # Log CREATE action
    # Return success response

def update_certificate(cert_id, body, user):
    # Check user has UPDATE permission (Admin, Operator)
    # Update DynamoDB item
    # Log UPDATE action with changes
    # Return success response

def delete_certificate(cert_id, user):
    # Check user has DELETE permission (Admin only)
    # Delete DynamoDB item
    # Log DELETE action
    # Return success response
```

**Invocation**:
- **API Gateway**: Triggered by HTTPS requests to API Gateway endpoints
- **Event Example**:
  ```json
  {
    "requestContext": {
      "http": {"method": "GET", "path": "/certificates"},
      "authorizer": {
        "jwt": {
          "claims": {
            "sub": "user-uuid",
            "email": "admin@example.com",
            "cognito:groups": ["Admins"]
          }
        }
      }
    },
    "queryStringParameters": {"status": "active"}
  }
  ```

## Deployment Package

Lambda functions are deployed from local source code:

```
lambda/
├── certificate_monitor.py
├── excel_processor.py
└── dashboard_api.py
```

Terraform zips these files automatically:

```hcl
data "archive_file" "certificate_monitor" {
  type        = "zip"
  source_file = "${path.module}/../../../lambda/certificate_monitor.py"
  output_path = "${path.module}/certificate_monitor.zip"
}

resource "aws_lambda_function" "certificate_monitor" {
  filename      = data.archive_file.certificate_monitor.output_path
  source_code_hash = data.archive_file.certificate_monitor.output_base64sha256
  # ...
}
```

## Dependencies & Layers

**Python Libraries Needed**:
- `boto3` - AWS SDK (included in Lambda runtime)
- `pandas` - Excel parsing (excel_processor only)
- `openpyxl` - Excel file format (excel_processor only)

**Lambda Layer** (for excel_processor):
```bash
# Create layer
mkdir -p python/lib/python3.9/site-packages
pip install pandas openpyxl -t python/lib/python3.9/site-packages
zip -r pandas-layer.zip python

# Upload layer
aws lambda publish-layer-version \
  --layer-name pandas-openpyxl \
  --zip-file fileb://pandas-layer.zip \
  --compatible-runtimes python3.9

# Attach to function
resource "aws_lambda_function" "excel_processor" {
  # ...
  layers = [aws_lambda_layer_version.pandas.arn]
}
```

## Monitoring

### CloudWatch Logs
View logs:
```bash
# Certificate monitor logs
aws logs tail /aws/lambda/cert-management-dev-secure-certificate-monitor --follow

# Excel processor logs
aws logs tail /aws/lambda/cert-management-dev-secure-excel-processor --follow

# Dashboard API logs
aws logs tail /aws/lambda/cert-management-dev-secure-dashboard-api --follow
```

### CloudWatch Metrics
- **Invocations**: Number of times function invoked
- **Duration**: Execution time (milliseconds)
- **Errors**: Number of invocation errors
- **Throttles**: Number of throttled invocations
- **ConcurrentExecutions**: Number of simultaneous executions

### CloudWatch Alarms
Set up alarms for errors:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name cert-monitor-errors \
  --alarm-description "Alert on certificate monitor errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=cert-management-dev-secure-certificate-monitor
```

## Testing

### Test certificate_monitor
```bash
aws lambda invoke \
  --function-name cert-management-dev-secure-certificate-monitor \
  --region eu-west-1 \
  response.json

cat response.json
```

### Test excel_processor
```bash
# Upload test Excel file
aws s3 cp test-certificates.xlsx s3://cert-management-dev-secure-uploads-dz243x46/

# Check logs
aws logs tail /aws/lambda/cert-management-dev-secure-excel-processor --follow
```

### Test dashboard_api
```bash
# Via API Gateway
curl -H "Authorization: Bearer <JWT_TOKEN>" \
  https://8clm33qmf9.execute-api.eu-west-1.amazonaws.com/dev-secure/certificates

# Direct invocation (for testing)
aws lambda invoke \
  --function-name cert-management-dev-secure-dashboard-api \
  --payload '{"requestContext":{"http":{"method":"GET","path":"/certificates"}},"queryStringParameters":{}}' \
  response.json
```

## Troubleshooting

### Issue: "Task timed out after X seconds"
**Cause**: Function exceeds timeout  
**Solution**: Increase timeout in Terraform:
```hcl
timeout = 900  # 15 minutes
```

### Issue: "Unable to import module"
**Cause**: Missing dependencies (pandas, openpyxl)  
**Solution**: Create Lambda layer with dependencies

### Issue: "AccessDenied" on DynamoDB
**Cause**: Missing IAM permissions  
**Solution**: Check IAM role has DynamoDB read/write permissions

### Issue: "Unable to marshall response"
**Cause**: Response not JSON-serializable  
**Solution**: Convert datetime objects to strings before returning

## Best Practices

1. **Logging**: Use structured logging with context (request ID, user email)
2. **Error Handling**: Catch exceptions, log errors, return meaningful messages
3. **Timeouts**: Set appropriate timeouts (API: 30s, Batch: 15min)
4. **Memory**: Monitor memory usage, adjust as needed
5. **Cold Starts**: Keep functions warm with provisioned concurrency (if needed)
6. **Environment Variables**: Store configuration, not secrets
7. **Idempotency**: Handle duplicate invocations gracefully
8. **Testing**: Write unit tests, integration tests

## Cost Estimation

Lambda pricing (eu-west-1):

| Function | Invocations/month | Duration | Memory | Cost |
|----------|-------------------|----------|--------|------|
| certificate_monitor | 30 | 5s | 512 MB | $0.0003 |
| excel_processor | 10 | 30s | 1024 MB | $0.0006 |
| dashboard_api | 10,000 | 100ms | 256 MB | $0.20 |
| **Total** | | | | **~$0.20/month** |

**Note**: First 1 million requests + 400,000 GB-seconds free per month (AWS Free Tier)

## Dependencies

- **IAM**: Requires Lambda execution role
- **DynamoDB**: Requires certificates and logs tables
- **S3**: Requires uploads bucket (excel_processor)
- **SES**: Requires verified sender email (certificate_monitor)

## Related Modules

- **IAM**: Provides Lambda execution role
- **Database**: Provides DynamoDB tables
- **Storage Secure**: Provides S3 uploads bucket
- **API Gateway**: Invokes dashboard_api function
- **EventBridge**: Invokes certificate_monitor function

## References

- [Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html)
- [Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
