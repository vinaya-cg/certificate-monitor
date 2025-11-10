# ServiceNow Integration Module

## Overview

This Terraform module creates an automated ServiceNow ticket creation system for expiring SSL/TLS certificates. It operates **independently** from the existing certificate monitoring infrastructure to ensure zero disruption.

## Features

✅ **Automated Ticket Creation** - Automatically creates ServiceNow incidents for expiring certificates  
✅ **Duplicate Prevention** - Checks existing `IncidentNumber` field to avoid duplicate tickets  
✅ **Priority-Based** - Assigns ticket priority based on days until expiry  
✅ **OAuth2 Authentication** - Secure authentication with ServiceNow REST API  
✅ **Dry-Run Mode** - Test without creating actual tickets  
✅ **Feature Flag Control** - Enable/disable entire module without code changes  
✅ **Independent Execution** - Separate Lambda and EventBridge schedule  
✅ **Comprehensive Logging** - Full audit trail in DynamoDB and CloudWatch  
✅ **Zero Impact** - Does not modify existing certificate monitoring

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Daily Execution                           │
│  EventBridge (9:05 AM UTC) → ServiceNow Lambda               │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│                  ServiceNow Lambda Function                  │
│                                                               │
│  1. Query DynamoDB for expiring certificates                 │
│     - ExpiryDate within threshold (default: 30 days)         │
│     - IncidentNumber is null/empty                           │
│     - Status != 'Renewal Done'                               │
│                                                               │
│  2. For each certificate needing a ticket:                   │
│     - Calculate priority (1-5 based on days left)            │
│     - Get ServiceNow OAuth token from Secrets Manager        │
│     - Format ticket with certificate details                 │
│     - Create ServiceNow incident via REST API                │
│     - Update DynamoDB with IncidentNumber                    │
│     - Log action to audit table                              │
│                                                               │
│  3. Return summary report                                    │
└──────────────────────────────────────────────────────────────┘
```

## Resources Created

This module creates the following AWS resources:

| Resource | Description |
|----------|-------------|
| **Lambda Function** | Python 3.9 function for ticket creation |
| **CloudWatch Log Group** | Lambda execution logs (30-day retention) |
| **EventBridge Rule** | Daily schedule trigger (9:05 AM UTC) |
| **EventBridge Target** | Connects rule to Lambda function |
| **Lambda Permission** | Allows EventBridge to invoke Lambda |
| **IAM Policy** | Permissions for DynamoDB, Secrets Manager, CloudWatch |
| **CloudWatch Alarms** | (Optional) Alerts for errors and performance |

## Usage

### Basic Usage

```hcl
module "servicenow_integration" {
  source = "../../modules/lambda_servicenow"

  project_name               = "cert-management"
  common_tags                = local.common_tags
  certificates_table_name    = module.database.certificates_table_name
  certificates_table_arn     = module.database.certificates_table_arn
  logs_table_name            = module.database.logs_table_name
  logs_table_arn             = module.database.logs_table_arn
  lambda_execution_role_arn  = module.iam.lambda_role_arn
  lambda_execution_role_id   = module.iam.lambda_role_name
  snow_secret_name           = "cert-management/servicenow/credentials"
  snow_secret_arn            = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:cert-management/servicenow/credentials-AbCdEf"
  expiry_threshold_days      = 30
  dry_run                    = "true"
  enable_scheduled_execution = true
  schedule_expression        = "cron(5 9 * * ? *)"
  log_retention_days         = 30
  enable_cloudwatch_alarms   = false
}
```

### With Feature Flag (Recommended)

```hcl
module "servicenow_integration" {
  count  = var.enable_servicenow_integration ? 1 : 0
  source = "../../modules/lambda_servicenow"

  # ... all parameters ...
}
```

This allows you to enable/disable the entire module by toggling one variable.

## Input Variables

### Required Variables

| Name | Type | Description |
|------|------|-------------|
| `project_name` | string | Project name for resource naming |
| `certificates_table_name` | string | DynamoDB certificates table name |
| `certificates_table_arn` | string | DynamoDB certificates table ARN |
| `logs_table_name` | string | DynamoDB logs table name |
| `logs_table_arn` | string | DynamoDB logs table ARN |
| `lambda_execution_role_arn` | string | Lambda execution role ARN |
| `lambda_execution_role_id` | string | Lambda execution role ID/name |
| `snow_secret_name` | string | Secrets Manager secret name |
| `snow_secret_arn` | string | Secrets Manager secret ARN |

### Optional Variables

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `common_tags` | map(string) | `{}` | Tags applied to all resources |
| `expiry_threshold_days` | number | `30` | Days before expiry to create tickets |
| `dry_run` | string | `"true"` | Enable dry-run mode (no actual tickets) |
| `enable_scheduled_execution` | bool | `true` | Enable EventBridge scheduled execution |
| `schedule_expression` | string | `"cron(5 9 * * ? *)"` | EventBridge cron schedule |
| `log_retention_days` | number | `30` | CloudWatch log retention period |
| `enable_cloudwatch_alarms` | bool | `false` | Enable performance/error alarms |

## Outputs

| Name | Description |
|------|-------------|
| `lambda_function_arn` | ARN of the ServiceNow Lambda function |
| `lambda_function_name` | Name of the ServiceNow Lambda function |
| `eventbridge_rule_arn` | ARN of the EventBridge schedule rule |
| `eventbridge_rule_name` | Name of the EventBridge schedule rule |
| `log_group_name` | CloudWatch log group name |

## ServiceNow Credentials

### Secret Structure

Store credentials in AWS Secrets Manager with this JSON structure:

```json
{
  "instance": "sogetinltest",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "username": "AWSMonitoring.apiUserDev",
  "password": "YOUR_PASSWORD",
  "caller": "AWSMonitoring.apiUserDev",
  "business_service": "PostNL Generic SecOps AWS",
  "service_offering": "PostNL Generic SecOps AWS",
  "company": "PostNL B.V."
}
```

### Creating the Secret

```bash
aws secretsmanager create-secret \
  --name cert-management/servicenow/credentials \
  --description "ServiceNow credentials for certificate management" \
  --secret-string file://servicenow-credentials.json \
  --region eu-west-1
```

See [SECRETS_MANAGER_CONFIG.md](./SECRETS_MANAGER_CONFIG.md) for detailed instructions.

## Priority Mapping

Tickets are automatically assigned priorities based on certificate expiry:

| Days Until Expiry | ServiceNow Priority | Label | Description |
|-------------------|---------------------|-------|-------------|
| Already expired | 1 - Critical | CRITICAL - EXPIRED | Immediate action required |
| < 7 days | 2 - High | HIGH - Less than 1 week | Urgent renewal needed |
| 7-14 days | 3 - Medium | MEDIUM - 1-2 weeks | Plan renewal soon |
| 15-30 days | 4 - Low | LOW - 2-4 weeks | Schedule renewal |
| > 30 days | 5 - Planning | PLANNING - More than 30 days | Early notification |

## Ticket Format

### Example ServiceNow Ticket

```
Incident Number: INCxxxxxxx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Short Description: 
  Certificate Expiring: wildcard.postnl.nl (Production)

Description:
  CERTIFICATE EXPIRY ALERT
  
  A certificate is approaching its expiration date and requires renewal.
  
  Certificate Details:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Certificate Name: wildcard.postnl.nl
  • Environment: Production
  • Application: PostNL Web Platform
  • Current Status: Due for Renewal
  
  Expiry Information:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Expiry Date: 2025-12-05
  • Days Until Expiry: 25 days
  • Urgency: MEDIUM
  
  [... full details ...]

Priority: 3 (Medium)
Business Service: PostNL Generic SecOps AWS
Correlation ID: cert-abc123def456
```

## DynamoDB Schema Requirements

### Certificates Table

Required fields:

| Field | Type | Description |
|-------|------|-------------|
| `CertificateID` | String (Key) | Unique certificate identifier |
| `CertificateName` | String | Certificate common name |
| `ExpiryDate` | String | Expiry date (YYYY-MM-DD) |
| `Environment` | String | Environment (Production, Test, etc.) |
| `Application` | String | Application name |
| `Status` | String | Current status |
| `OwnerEmail` | String | Certificate owner email |
| `SupportEmail` | String | Support team email |
| `IncidentNumber` | String | ServiceNow incident number (optional) |
| `AccountNumber` | String | AWS account number (optional) |
| `DomainName` | String | Domain name (optional) |
| `ACM_ARN` | String | ACM certificate ARN (optional) |

### Logs Table

Required fields:

| Field | Type | Description |
|-------|------|-------------|
| `LogID` | String (Key) | Unique log entry ID |
| `CertificateID` | String | Related certificate ID |
| `Timestamp` | String | ISO 8601 timestamp |
| `Action` | String | Action performed |
| `Details` | Map | Action details |
| `Metadata` | Map | Additional metadata |

## Testing

### Dry-Run Mode

Start with dry-run enabled to test without creating actual tickets:

```hcl
dry_run = "true"
```

**Behavior:**
- ✅ Lambda executes normally
- ✅ Certificates are scanned
- ✅ Logs show which tickets would be created
- ❌ No actual ServiceNow API calls
- ❌ No DynamoDB updates
- ❌ No tickets created

**CloudWatch Logs:**
```
[INFO] DRY_RUN mode: True
[INFO] Found 5 expiring certificates
[INFO] Filtered to 3 certificates needing tickets
[INFO] DRY_RUN: Would create ticket for wildcard.example.com
[INFO] DRY_RUN: Would create ticket for api.example.com
[INFO] DRY_RUN: Would create ticket for admin.example.com
```

### Manual Invocation

Test the Lambda function manually:

```bash
aws lambda invoke \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json | jq .
```

### Production Mode

After successful testing, disable dry-run:

```hcl
dry_run = "false"
```

## Monitoring

### CloudWatch Logs

View real-time logs:

```bash
aws logs tail /aws/lambda/cert-management-dev-secure-servicenow-ticket-creator --follow
```

### Lambda Metrics

Check Lambda performance:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=cert-management-dev-secure-servicenow-ticket-creator \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average,Maximum
```

### Audit Trail

Query ticket creation history:

```bash
aws dynamodb query \
  --table-name cert-management-dev-secure-logs \
  --filter-expression "Action = :action" \
  --expression-attribute-values '{":action":{"S":"SERVICENOW_TICKET_CREATED"}}' \
  --limit 20
```

## Troubleshooting

### Common Issues

#### 1. No Tickets Created (Dry-Run Enabled)

**Check:**
```bash
aws lambda get-function-configuration \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --query 'Environment.Variables.DRY_RUN'
```

**Fix:** Set `dry_run = "false"` in Terraform

#### 2. ServiceNow Authentication Failure

**Symptoms:** 401 Unauthorized errors in logs

**Check:**
```bash
aws secretsmanager get-secret-value \
  --secret-id cert-management/servicenow/credentials \
  --query SecretString --output text | jq .
```

**Fix:** Update credentials in Secrets Manager

#### 3. Duplicate Tickets

**Symptoms:** Multiple tickets for same certificate

**Check:** Verify IncidentNumber is being updated in DynamoDB

**Fix:** Ensure Lambda has `dynamodb:UpdateItem` permission

#### 4. EventBridge Not Triggering

**Check:**
```bash
aws events describe-rule \
  --name cert-management-dev-secure-servicenow-schedule \
  --query '{State:State,Schedule:ScheduleExpression}'
```

**Fix:** Enable the rule:
```bash
aws events enable-rule \
  --name cert-management-dev-secure-servicenow-schedule
```

## IAM Permissions

The Lambda function requires these IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Scan",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:PutItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/cert-management-*-certificates",
        "arn:aws:dynamodb:*:*:table/cert-management-*-logs"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:*:*:secret:cert-management/servicenow/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/cert-management-*-servicenow-*"
    }
  ]
}
```

## Cost Estimate

Monthly cost for typical usage (100 expiring certificates/month):

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 30 invocations × 30s × 256MB | $0.01 |
| CloudWatch Logs | 50 MB storage | $0.00 |
| Secrets Manager | 1 secret | $0.40 |
| EventBridge | 30 events | $0.00 (free tier) |
| DynamoDB | Reads/Writes | Covered by existing table |
| **Total** | | **~$0.41/month** |

## Security Best Practices

1. ✅ **Credentials in Secrets Manager** - Never hardcode credentials
2. ✅ **Least Privilege IAM** - Lambda has minimal required permissions
3. ✅ **Encrypted Secrets** - Secrets Manager uses AWS KMS encryption
4. ✅ **VPC Deployment** - (Optional) Deploy Lambda in VPC for added security
5. ✅ **CloudTrail Logging** - All secret access is logged
6. ✅ **Dry-Run Testing** - Test thoroughly before enabling production mode
7. ✅ **Regular Rotation** - Rotate ServiceNow credentials every 90 days

## Rollback

To disable the integration:

### Option 1: Disable EventBridge Rule (Quickest)

```bash
aws events disable-rule \
  --name cert-management-dev-secure-servicenow-schedule
```

### Option 2: Enable Dry-Run Mode

```bash
aws lambda update-function-configuration \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --environment "Variables={...,DRY_RUN=true}"
```

### Option 3: Feature Flag (Cleanest)

```hcl
enable_servicenow_integration = false
```

```bash
terraform apply
```

## Dependencies

### Python Packages

- `boto3` - AWS SDK
- `requests` - HTTP library for ServiceNow API
- `urllib3` - HTTP client

See [servicenow_requirements.txt](../../../lambda/servicenow_requirements.txt)

### Terraform Modules

- `storage_secure` - Provides DynamoDB tables
- `iam` - Provides Lambda execution role

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-10 | Initial module creation |

## Support

For issues or questions:

1. Check CloudWatch Logs for errors
2. Review [SERVICENOW_DEPLOYMENT_GUIDE.md](../../../SERVICENOW_DEPLOYMENT_GUIDE.md)
3. Test with dry-run mode enabled
4. Verify ServiceNow credentials
5. Check IAM permissions

## Related Documentation

- [ServiceNow Deployment Guide](../../../SERVICENOW_DEPLOYMENT_GUIDE.md)
- [Secrets Manager Configuration](./SECRETS_MANAGER_CONFIG.md)
- [Inspector ServiceNow Integration](../../../INSPECTOR_SERVICENOW_INTEGRATION.md)

## License

This module is part of the Certificate Management System.

---

**End of README**
