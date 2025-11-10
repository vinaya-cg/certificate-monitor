# ServiceNow Webhook Handler Lambda Module

This Terraform module deploys a webhook handler that receives ServiceNow incident assignment updates and automatically updates certificate records in DynamoDB.

## Purpose

Creates **bidirectional integration** between ServiceNow and the Certificate Management Dashboard:
- **AWS → ServiceNow:** Automated ticket creation (via `lambda_servicenow` module)
- **ServiceNow → AWS:** Real-time certificate updates when incidents are assigned (this module)

## What It Does

When an engineer picks/assigns a ServiceNow incident:
1. ServiceNow Business Rule sends webhook to API Gateway
2. Lambda function validates and processes the webhook
3. Certificate updated in DynamoDB with:
   - Assignee name and email
   - Status changed to "Renewal in Progress"
   - Assignment timestamp
   - Incident state tracking
4. Action logged in certificate-logs table

## Architecture

```
ServiceNow Incident Assignment
         ↓
Business Rule (JavaScript)
         ↓
API Gateway Webhook Endpoint
         ↓
Lambda Function (webhook_handler)
         ↓
DynamoDB Update
         ↓
Dashboard Shows Changes
```

## Resources Created

- **Lambda Function:** Processes webhook payloads
- **API Gateway:** HTTPS webhook endpoint
- **CloudWatch Log Group:** Lambda execution logs
- **IAM Roles & Policies:** DynamoDB and Secrets Manager access
- **CloudWatch Alarms:** Error monitoring (optional)

## Usage

```hcl
module "servicenow_webhook" {
  source = "../../modules/lambda_servicenow_webhook"

  project_name            = "cert-management"
  environment             = "dev-secure"
  aws_region              = "eu-west-1"
  certificates_table_name = "cert-management-certificates"
  certificates_table_arn  = "arn:aws:dynamodb:..."
  logs_table_name         = "cert-management-logs"
  logs_table_arn          = "arn:aws:dynamodb:..."
  webhook_secret_name     = "cert-management/servicenow/webhook-secret"
  webhook_secret_arn      = "arn:aws:secretsmanager:..."
  log_retention_days      = 30
  enable_alarms           = true
}
```

## Outputs

- `webhook_endpoint` - URL to configure in ServiceNow Business Rule
- `lambda_function_name` - Name of the Lambda function
- `lambda_function_arn` - ARN of the Lambda function
- `api_gateway_id` - API Gateway REST API ID

## ServiceNow Configuration Required

**This module only deploys AWS infrastructure.** You must manually configure ServiceNow:

1. **Create Business Rule** in ServiceNow
2. **Configure webhook URL** (from Terraform output)
3. **Set trigger conditions** (incident assigned/state changed)
4. **Test the integration**

See `SERVICENOW_WEBHOOK_INTEGRATION.md` for complete setup instructions.

## Status Mapping

| ServiceNow State | Certificate Status |
|------------------|-------------------|
| New (1) | Pending Assignment |
| In Progress (2) | Renewal in Progress |
| On Hold (3) | On Hold |
| Resolved (6) | Renewal Done |
| Closed (7) | Renewal Done |
| Canceled (8) | Renewal Canceled |

## Security

- **Webhook signature validation** (optional but recommended)
- **IAM least-privilege access** (DynamoDB update only)
- **CloudWatch logging** for audit trail
- **API Gateway throttling** (default limits)

## Cost

- **Lambda:** Pay-per-invocation (~$0.20 per 1M requests)
- **API Gateway:** Pay-per-request (~$3.50 per 1M requests)
- **CloudWatch Logs:** $0.50 per GB ingested
- **Estimated monthly cost:** <$5 for typical usage

## Variables

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `project_name` | Project name | `string` | Required |
| `environment` | Environment name | `string` | Required |
| `aws_region` | AWS region | `string` | Required |
| `certificates_table_name` | DynamoDB certificates table | `string` | Required |
| `certificates_table_arn` | DynamoDB certificates ARN | `string` | Required |
| `logs_table_name` | DynamoDB logs table | `string` | Required |
| `logs_table_arn` | DynamoDB logs ARN | `string` | Required |
| `webhook_secret_name` | Secrets Manager secret name | `string` | `cert-management/servicenow/webhook-secret` |
| `webhook_secret_arn` | Secrets Manager secret ARN | `string` | Required |
| `log_retention_days` | CloudWatch log retention | `number` | `30` |
| `enable_alarms` | Enable CloudWatch alarms | `bool` | `true` |

## Testing

```powershell
# Use the provided test script
.\Test-Webhook-Integration.ps1

# Or manually test with curl/Invoke-RestMethod
$payload = @{
    incident_number = "INC0123456"
    correlation_id = "cert-test-12345"
    state = "2"
    assigned_to = @{
        name = "John Doe"
        email = "john.doe@company.com"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://xxx.execute-api.eu-west-1.amazonaws.com/dev-secure/webhook" -Method POST -Body $payload -ContentType "application/json"
```

## Monitoring

```bash
# View Lambda logs
aws logs tail /aws/lambda/cert-management-servicenow-webhook-handler --follow

# Check recent invocations
aws lambda list-versions-by-function --function-name cert-management-servicenow-webhook-handler
```

## Troubleshooting

**Webhook returns 401:** Signature validation failing or disabled
**Webhook returns 404:** Certificate not found - check correlation_id
**No response:** Check API Gateway and Lambda execution logs
**Certificate not updated:** Check DynamoDB permissions

## Dependencies

- DynamoDB certificates table (must exist)
- DynamoDB logs table (must exist)
- Secrets Manager secret (can be empty for testing)
- ServiceNow Business Rule (manual configuration)

## Related Modules

- `lambda_servicenow` - Creates ServiceNow tickets for expiring certificates
- `database` - Provides DynamoDB tables
- `iam` - Provides Lambda execution role

## Documentation

- `SERVICENOW_WEBHOOK_INTEGRATION.md` - Complete setup guide
- `Test-Webhook-Integration.ps1` - Testing script
- `servicenow_webhook_handler.py` - Lambda function source code
