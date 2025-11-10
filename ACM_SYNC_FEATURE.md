# ACM Certificate Synchronization Feature

## Overview

The ACM Sync feature automatically synchronizes SSL/TLS certificates from AWS Certificate Manager (ACM) into the Certificate Management Dashboard, providing centralized visibility and management of certificates across your AWS infrastructure.

## Features

### Automated Synchronization
- **Scheduled Sync**: Runs daily at 2:00 AM UTC via EventBridge
- **Manual Sync**: On-demand synchronization via dashboard UI button
- **Multi-Region Support**: Scans ACM certificates in specified AWS regions
- **Account Scanning**: Supports current account with provision for cross-account scanning

### Certificate Data Captured
- Certificate Common Name (CN)
- Expiry Date
- ACM ARN
- AWS Account Number
- Region
- ACM Status (ISSUED, PENDING_VALIDATION, etc.)
- Last Sync Timestamp
- Version tracking (new vs updated)

### Smart Update Logic
- Preserves manually entered fields (OwnerEmail, SupportEmail, Application, Notes)
- Updates only ACM-specific fields on re-sync
- Tracks certificate versions to distinguish new vs updated certificates
- Handles certificate lifecycle changes automatically

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     ACM Sync System                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  EventBridge Schedule  ──►  ACM Sync Lambda                 │
│  (Daily 2 AM UTC)           │                                │
│                             │                                │
│  Dashboard UI Button  ──►  Dashboard API Lambda  ──►  ACM   │
│  (Manual Trigger)          │                        Sync     │
│                            ▼                        Lambda   │
│                      DynamoDB                        │       │
│                      (Certificates)  ◄───────────────┘       │
│                      - AccountNumber                         │
│                      - ACM_ARN                               │
│                      - ACM_Status                            │
│                      - LastSyncedFromACM                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### AWS Resources

#### Lambda Functions
1. **acm_certificate_sync.py** (cert-management-dev-secure-acm-sync)
   - Runtime: Python 3.9
   - Memory: 512 MB
   - Timeout: 900 seconds (15 minutes)
   - Permissions: ACM:ListCertificates, ACM:DescribeCertificate, DynamoDB:PutItem/UpdateItem/Query

2. **dashboard_api.py** (cert-management-dev-secure-dashboard-api)
   - Enhanced with `/sync-acm` endpoint handler
   - Invokes ACM sync Lambda asynchronously
   - Returns 202 Accepted response

#### DynamoDB
- **Table**: cert-management-dev-secure-certificates
- **New Attributes**:
  - `AccountNumber` (String) - AWS account ID
  - `ACM_ARN` (String) - Full ACM certificate ARN
  - `ACM_Status` (String) - Certificate status from ACM
  - `LastSyncedFromACM` (String) - ISO timestamp of last sync
- **Global Secondary Index**: AccountNumber-DomainName-index
  - Partition Key: AccountNumber (S)
  - Sort Key: CommonName (S)
  - Projection: ALL
  - Status: ACTIVE

#### API Gateway
- **Endpoint**: POST /sync-acm
- **Authentication**: Cognito User Pool JWT
- **CORS**: Enabled (OPTIONS method)
- **Response**: 202 Accepted with sync initiation confirmation

#### EventBridge
- **Rule**: cert-management-dev-secure-acm-sync-schedule
- **Schedule**: cron(0 2 * * ? *) - Daily at 2:00 AM UTC
- **Target**: ACM Sync Lambda function

#### IAM Permissions
- **Lambda Execution Role**: cert-management-dev-secure-lambda-role
- **New Permissions**:
  ```json
  {
    "Effect": "Allow",
    "Action": ["lambda:InvokeFunction"],
    "Resource": "arn:aws:lambda:eu-west-1:992155623828:function:cert-management-dev-secure-acm-sync"
  }
  ```

## Dashboard UI

### Sync Button
Located in the main dashboard toolbar:
```html
<button class="btn btn-info" onclick="triggerACMSync()" id="acmSyncBtn">
    <i class="fas fa-cloud-download-alt"></i> Sync from ACM v2
</button>
```

### Progress Modal
Interactive modal with three states:

#### 1. Progress View
- Displays spinning loader
- Shows message: "Synchronizing certificates from AWS ACM..."
- Button disabled during sync

#### 2. Results View
Four-metric grid display:
- **Certificates Found** (Blue) - Total ACM certificates discovered
- **Newly Added** (Green) - New certificates added to dashboard
- **Updated** (Orange) - Existing certificates updated
- **Errors** (Red) - Any synchronization errors

#### 3. Error View
- Displays error message if sync fails
- Includes close button to dismiss

### JavaScript Functions

#### triggerACMSync()
```javascript
async function triggerACMSync()
```
- Shows confirmation dialog
- Opens progress modal
- Calls API endpoint: `POST /sync-acm`
- Initiates polling for completion
- Handles errors with detailed messages

#### pollACMSyncStatus()
```javascript
async function pollACMSyncStatus()
```
- Polls every 1 second for up to 60 seconds
- Queries certificates with `LastSyncedFromACM` < 2 minutes
- Distinguishes new (Version=1) vs updated certificates
- Displays results when count stabilizes

#### showACMSyncResults(found, added, updated, errors)
```javascript
function showACMSyncResults(found, added, updated, errors)
```
- Switches modal from progress to results view
- Updates metric counters
- Provides refresh dashboard option

## Usage

### Manual Sync from Dashboard

1. **Login** to the certificate dashboard
2. **Click** the "Sync from ACM v2" button in the toolbar
3. **Confirm** the synchronization action
4. **Wait** for the progress modal (typically 5-15 seconds)
5. **Review** the sync results:
   - Certificates Found
   - Newly Added
   - Updated
   - Errors (if any)
6. **Click** "Refresh Dashboard" to see updated certificates

### Automated Daily Sync

The system automatically runs at 2:00 AM UTC daily. To verify:

```bash
# Check EventBridge rule
aws events describe-rule --name cert-management-dev-secure-acm-sync-schedule

# View recent execution logs
aws logs tail /aws/lambda/cert-management-dev-secure-acm-sync --since 1d
```

### Monitor Sync Execution

#### CloudWatch Logs
```bash
# Tail live logs
aws logs tail /aws/lambda/cert-management-dev-secure-acm-sync --follow

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/cert-management-dev-secure-acm-sync \
  --filter-pattern "ERROR"
```

#### DynamoDB Queries
```bash
# Check recently synced certificates
aws dynamodb query \
  --table-name cert-management-dev-secure-certificates \
  --index-name AccountNumber-DomainName-index \
  --key-condition-expression "AccountNumber = :account" \
  --expression-attribute-values '{":account":{"S":"992155623828"}}'
```

## Configuration

### Regions to Scan
Modify `lambda/acm_certificate_sync.py`:
```python
REGIONS_TO_SCAN = ['eu-west-1', 'us-east-1']  # Add regions as needed
```

### Sync Schedule
Update `terraform/modules/lambda_acm_sync/main.tf`:
```hcl
resource "aws_cloudwatch_event_rule" "acm_sync_schedule" {
  schedule_expression = "cron(0 2 * * ? *)"  # Modify schedule
}
```

### Cross-Account Scanning (Future Enhancement)
To enable cross-account scanning:

1. Create IAM role in target account with ACM read permissions
2. Update `lambda/acm_certificate_sync.py` accounts list:
```python
CROSS_ACCOUNT_ROLES = {
    '123456789012': 'arn:aws:iam::123456789012:role/ACMReadRole'
}
```
3. Add STS:AssumeRole permission to Lambda execution role

## Deployment

### Initial Deployment
```bash
cd terraform/environments/dev-secure
terraform init
terraform apply
```

This deploys:
- ACM Sync Lambda function
- EventBridge scheduled rule
- DynamoDB GSI (AccountNumber-DomainName-index)
- API Gateway /sync-acm endpoint
- IAM policies
- Dashboard UI updates

### Update Deployment
```bash
# Update Lambda code only
cd terraform/environments/dev-secure
terraform apply -target=module.acm_sync

# Update API Gateway
terraform apply -target=module.api_gateway

# Update dashboard files
aws s3 cp dashboard/index.html s3://cert-management-dev-secure-dashboard-dz243x46/
aws s3 cp dashboard/dashboard.js s3://cert-management-dev-secure-dashboard-dz243x46/
aws cloudfront create-invalidation --distribution-id E2CPB8IUR80ZRD --paths "/*"
```

## Troubleshooting

### Sync Button Not Working

**Symptom**: "Failed to fetch" error

**Solution**:
1. Check browser console (F12) for detailed errors
2. Verify API Gateway endpoint exists:
   ```bash
   aws apigateway get-resources --rest-api-id 8clm33qmf9
   ```
3. Ensure CloudFront cache is cleared:
   ```bash
   aws cloudfront create-invalidation --distribution-id E2CPB8IUR80ZRD --paths "/*"
   ```

### IAM Permission Errors

**Symptom**: "AccessDeniedException: User is not authorized to perform: lambda:InvokeFunction"

**Solution**:
1. Verify IAM policy includes lambda:InvokeFunction:
   ```bash
   aws iam get-policy-version \
     --policy-arn arn:aws:iam::992155623828:policy/cert-management-dev-secure-lambda-policy \
     --version-id v1
   ```
2. Re-apply Terraform:
   ```bash
   terraform apply -target=module.iam
   ```

### No Certificates Found

**Symptom**: Modal shows 0 certificates found

**Possible Causes**:
1. ACM has no certificates in scanned regions
2. Lambda timeout (increase from 900s if needed)
3. ACM API rate limiting (add exponential backoff)

**Verification**:
```bash
# Check ACM certificates directly
aws acm list-certificates --region eu-west-1

# Check Lambda execution logs
aws logs tail /aws/lambda/cert-management-dev-secure-acm-sync --since 1h
```

### Certificates Not Updating

**Symptom**: LastSyncedFromACM not updating

**Check**:
1. Verify DynamoDB write permissions
2. Check for throttling in CloudWatch metrics
3. Review Lambda execution logs for errors

## Performance

### Tested Capacity
- **Certificates**: Successfully synced 64 certificates
- **Execution Time**: ~6 seconds for 64 certificates
- **Memory Usage**: ~86 MB peak
- **API Calls**: ~65 ACM API calls (1 List + 64 Describe)

### Optimization
- Batch DynamoDB writes (up to 25 items)
- Parallel ACM API calls within rate limits
- Efficient GSI queries for duplicate detection

### Scaling Considerations
- EventBridge: Unlimited scalability
- Lambda: Concurrent execution limits (default 1000)
- DynamoDB: On-demand pricing scales automatically
- ACM API: Rate limits apply (5 requests per second per region)

## Security

### Authentication
- Dashboard: Cognito User Pool JWT tokens
- API Gateway: Cognito authorizer validates all requests
- Lambda: IAM execution role with least-privilege permissions

### Data Protection
- DynamoDB: Encryption at rest enabled
- CloudWatch Logs: Encrypted with AWS managed keys
- S3 Dashboard: Private bucket with CloudFront OAI access

### Network Security
- API Gateway: HTTPS only (TLS 1.2+)
- Lambda: Executes in AWS VPC (optional)
- CloudFront: HTTPS enforced

## Testing

### Manual Test
```bash
# Invoke ACM sync Lambda directly
aws lambda invoke \
  --function-name cert-management-dev-secure-acm-sync \
  --invocation-type RequestResponse \
  response.json

# Check response
cat response.json
```

### API Gateway Test
```bash
# Test /sync-acm endpoint
aws apigateway test-invoke-method \
  --rest-api-id 8clm33qmf9 \
  --resource-id 8mceor \
  --http-method POST \
  --headers "Authorization=test"
```

### Expected Output
```json
{
  "statusCode": 202,
  "message": "ACM synchronization started",
  "details": "The sync process is running in the background.",
  "timestamp": "2025-11-10T10:17:42.501892+00:00"
}
```

## Maintenance

### Regular Tasks
- **Weekly**: Review sync logs for errors
- **Monthly**: Verify EventBridge schedule is active
- **Quarterly**: Review and optimize scanned regions

### Monitoring Alerts
Consider setting up CloudWatch alarms for:
- Lambda execution failures
- High error rates in sync operations
- DynamoDB throttling events
- API Gateway 5xx errors

### Backup and Recovery
- DynamoDB: Point-in-time recovery enabled
- Lambda: Version all code deployments
- Terraform: State stored in S3 with versioning

## Cost Estimate

### Monthly Costs (based on 64 certificates)
- **Lambda**: ~$0.01 (30 executions/month @ 6s each)
- **DynamoDB**: ~$0.25 (on-demand, 64 items, 4 writes/day)
- **EventBridge**: $0.00 (first 1M events free)
- **API Gateway**: $0.00 (within free tier for low volume)
- **CloudWatch Logs**: ~$0.50 (log retention)

**Total**: ~$1/month for automated ACM sync

## Version History

### v1.2.0 (November 10, 2025)
- ✅ Initial ACM sync feature release
- ✅ Dashboard UI with sync button and progress modal
- ✅ Automated daily sync via EventBridge
- ✅ DynamoDB GSI for account-based queries
- ✅ Comprehensive error handling and logging
- ✅ Smart update logic preserving user data

### Future Enhancements
- [ ] Cross-account certificate scanning
- [ ] Certificate expiry notifications
- [ ] Auto-renewal integration
- [ ] Multi-region dashboard aggregation
- [ ] Export ACM inventory to Excel/CSV
- [ ] Certificate compliance reporting

## Support

### Documentation
- [Main README](README.md)
- [Deployment Guide](DEPLOYMENT_SUMMARY.md)
- [Quick Reference](QUICK_REFERENCE.md)

### Logs and Monitoring
- CloudWatch Logs: `/aws/lambda/cert-management-dev-secure-acm-sync`
- Dashboard URL: `https://d3bqyfjow8topp.cloudfront.net`
- API Endpoint: `https://8clm33qmf9.execute-api.eu-west-1.amazonaws.com/dev-secure`

### Contact
- Project: Certificate Management System
- Environment: dev-secure
- Deployed: November 10, 2025
- Version: 1.2.0
