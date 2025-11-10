# ACM Sync - Quick Deployment Guide

## Prerequisites
- AWS CLI configured with credentials for account 992155623828
- Terraform 1.0+ installed
- Access to ACM in eu-west-1 region

## Deployment Steps

### 1. Review Changes
```bash
cd terraform/environments/dev-secure
terraform plan
```

**Expected Output:**
```
Plan: 5 to add, 1 to change, 0 to destroy

Changes to apply:
  + aws_lambda_function.acm_sync
  + aws_cloudwatch_log_group.acm_sync
  + aws_cloudwatch_event_rule.acm_sync_schedule
  + aws_cloudwatch_event_target.acm_sync_target
  + aws_lambda_permission.allow_eventbridge_acm_sync
  ~ aws_dynamodb_table.certificates (add GSI)
```

### 2. Apply Infrastructure
```bash
terraform apply -auto-approve
```

⚠️ **NOTE:** DynamoDB GSI creation may take 5-10 minutes.

### 3. Verify Lambda Function
```bash
aws lambda get-function --function-name cert-management-dev-secure-acm-sync

Expected output:
{
  "Configuration": {
    "FunctionName": "cert-management-dev-secure-acm-sync",
    "Runtime": "python3.9",
    "Timeout": 900,
    "MemorySize": 512,
    "State": "Active"
  }
}
```

### 4. Test ACM Sync Manually
```bash
# Invoke sync Lambda
aws lambda invoke \
  --function-name cert-management-dev-secure-acm-sync \
  --invocation-type Event \
  --payload '{"source":"manual-test"}' \
  response.json

# Wait 30 seconds, then check logs
aws logs tail /aws/lambda/cert-management-dev-secure-acm-sync --follow

# Look for output like:
# ACM SYNC COMPLETED
# Accounts Scanned: 1
# Certificates Found: X
# Certificates Added: X
# Certificates Updated: X
```

### 5. Verify Certificates in DynamoDB
```bash
# Check total certificates
aws dynamodb scan \
  --table-name cert-management-dev-secure-certificates \
  --select COUNT

# Check ACM-synced certificates
aws dynamodb scan \
  --table-name cert-management-dev-secure-certificates \
  --filter-expression "Source = :source" \
  --expression-attribute-values '{":source":{"S":"ACM"}}' \
  --projection-expression "CommonName, ExpiryDate, ACM_Status"
```

### 6. Update Dashboard API
```bash
cd ../../../lambda

# Add ACM_SYNC_FUNCTION environment variable to dashboard API
aws lambda update-function-configuration \
  --function-name cert-management-dev-secure-dashboard-api \
  --environment Variables="{CERTIFICATES_TABLE=cert-management-dev-secure-certificates,ACM_SYNC_FUNCTION=cert-management-dev-secure-acm-sync}"

# Deploy updated dashboard_api.py
zip dashboard_api.zip dashboard_api.py

aws lambda update-function-code \
  --function-name cert-management-dev-secure-dashboard-api \
  --zip-file fileb://dashboard_api.zip
```

### 7. Test Manual Sync Endpoint
```bash
# Get API endpoint
API_URL="https://8clm33qmf9.execute-api.eu-west-1.amazonaws.com/dev-secure"

# Test sync endpoint (requires authentication)
curl -X POST "$API_URL/sync-acm" \
  -H "Authorization: YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

Expected response:
{
  "success": true,
  "message": "ACM synchronization started",
  "timestamp": "2025-11-10T12:00:00Z"
}
```

## Troubleshooting

### Lambda Not Found
```bash
# Check if Lambda exists
aws lambda list-functions --query 'Functions[?contains(FunctionName, `acm-sync`)].FunctionName'

# If not found, re-run terraform apply
cd terraform/environments/dev-secure
terraform apply
```

### GSI Not Available
```bash
# Check DynamoDB table status
aws dynamodb describe-table \
  --table-name cert-management-dev-secure-certificates \
  --query 'Table.GlobalSecondaryIndexes[?IndexName==`AccountNumber-DomainName-index`].IndexStatus'

# Wait until status is "ACTIVE" (may take 5-10 minutes)
```

### No Certificates Found
```bash
# Check if ACM has certificates in eu-west-1
aws acm list-certificates --region eu-west-1

# If ACM is empty, create a test certificate first or check another region
```

### Lambda Timeout
```bash
# Check CloudWatch logs
aws logs tail /aws/lambda/cert-management-dev-secure-acm-sync --since 10m

# If timing out, increase timeout:
aws lambda update-function-configuration \
  --function-name cert-management-dev-secure-acm-sync \
  --timeout 900
```

## Verification Checklist

- [ ] Terraform apply successful
- [ ] Lambda function created (`cert-management-dev-secure-acm-sync`)
- [ ] EventBridge rule created (schedule: daily 2 AM UTC)
- [ ] DynamoDB GSI active (`AccountNumber-DomainName-index`)
- [ ] Manual sync test successful (Lambda invoked)
- [ ] Certificates imported from ACM
- [ ] Dashboard API updated with sync endpoint
- [ ] Manual sync endpoint returns 202 Accepted

## Next Steps

1. **Monitor First Scheduled Run** - Check logs tomorrow at 2 AM UTC
2. **Update Dashboard UI** - Add "Sync with ACM" button
3. **Create Documentation** - Complete ACM_SYNC_GUIDE.md
4. **Set Up Cross-Account** - Configure IAM roles for additional accounts

## Rollback (If Needed)

```bash
# Remove ACM sync module from terraform
cd terraform/environments/dev-secure

# Comment out the acm_sync module in main.tf, then:
terraform apply

# This will:
# - Delete Lambda function
# - Delete EventBridge rule
# - Keep DynamoDB GSI (cannot be deleted without recreating table)
```

## Cost Estimate

- **Lambda:** $0.10/month (900 invocations @ 1 sec each)
- **DynamoDB GSI:** $0 (PAY_PER_REQUEST billing)
- **CloudWatch Logs:** $0.50/month (1 GB/month @ $0.50/GB)
- **EventBridge:** $0 (1 rule = free)
- **Total:** ~$0.60/month

## Support

For issues or questions:
1. Check CloudWatch Logs: `/aws/lambda/cert-management-dev-secure-acm-sync`
2. Review TROUBLESHOOTING.md
3. Check ACM_SYNC_IMPLEMENTATION.md for architecture details
