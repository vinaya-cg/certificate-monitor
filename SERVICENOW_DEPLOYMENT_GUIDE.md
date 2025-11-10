# ServiceNow Integration - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the ServiceNow ticket creation integration for the Certificate Management System. This integration automatically creates ServiceNow incidents for expiring certificates **without** modifying the existing certificate monitoring infrastructure.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Steps](#deployment-steps)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Enabling Production Mode](#enabling-production-mode)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Access

- AWS CLI configured with appropriate credentials
- Terraform v1.0+ installed
- Access to ServiceNow test instance (`sogetinltest.service-now.com`)
- Permissions to create/manage:
  - Lambda functions
  - EventBridge rules
  - Secrets Manager secrets
  - IAM policies
  - CloudWatch Logs

### ServiceNow Credentials

You will need the following from ServiceNow:

| Credential | Description | Example |
|------------|-------------|---------|
| Instance Name | ServiceNow instance (without .service-now.com) | `sogetinltest` |
| Client ID | OAuth2 client ID | `d3168ff13a90d210...` |
| Client Secret | OAuth2 client secret | `(Y!!fpXH\|T` |
| Username | API user username | `AWSMonitoring.apiUserDev` |
| Password | API user password | (Secure password) |

### Existing Infrastructure

This integration requires:
- ✅ DynamoDB `cert-management-dev-secure-certificates` table
- ✅ DynamoDB `cert-management-dev-secure-logs` table
- ✅ Lambda execution role with DynamoDB access
- ✅ Certificate monitor Lambda (existing - will not be modified)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│          EXISTING INFRASTRUCTURE (Unchanged)                     │
│                                                                  │
│  EventBridge (9:00 AM) → Certificate Monitor Lambda             │
│         ↓                                                        │
│    Scan DynamoDB → Send Email → Update Status                   │
└─────────────────────────────────────────────────────────────────┘

                              ↓
                       (5 minutes later)
                              ↓

┌─────────────────────────────────────────────────────────────────┐
│          NEW SERVICENOW INTEGRATION (Independent)                │
│                                                                  │
│  EventBridge (9:05 AM) → ServiceNow Ticket Creator Lambda       │
│         ↓                                                        │
│    Query DynamoDB for certs without tickets                     │
│         ↓                                                        │
│    Create ServiceNow ticket via OAuth2 API                      │
│         ↓                                                        │
│    Update DynamoDB with IncidentNumber                          │
│         ↓                                                        │
│    Log action to audit table                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- ✅ **Zero disruption** to existing monitoring
- ✅ **Independent execution** (separate Lambda & EventBridge rule)
- ✅ **Feature flag controlled** (can enable/disable instantly)
- ✅ **Dry-run mode** for safe testing

---

## Deployment Steps

### Step 1: Create Secrets Manager Secret

First, store your ServiceNow credentials in AWS Secrets Manager:

```bash
# Navigate to your workspace
cd "c:\Users\vnayaneg\OneDrive - Capgemini\Desktop\Sogeti\Automation and Innovation\Run factory\certificate monitor\cert-dashboard"

# Create the secret (replace placeholders with actual values)
aws secretsmanager create-secret \
  --name cert-management/servicenow/credentials \
  --description "ServiceNow credentials for certificate management integration" \
  --secret-string '{
    "instance": "sogetinltest",
    "client_id": "YOUR_CLIENT_ID_HERE",
    "client_secret": "YOUR_CLIENT_SECRET_HERE",
    "username": "AWSMonitoring.apiUserDev",
    "password": "YOUR_PASSWORD_HERE",
    "caller": "AWSMonitoring.apiUserDev",
    "business_service": "PostNL Generic SecOps AWS",
    "service_offering": "PostNL Generic SecOps AWS",
    "company": "PostNL B.V."
  }' \
  --region eu-west-1
```

**Expected Output:**
```json
{
    "ARN": "arn:aws:secretsmanager:eu-west-1:992155623828:secret:cert-management/servicenow/credentials-AbCdEf",
    "Name": "cert-management/servicenow/credentials",
    "VersionId": "..."
}
```

**Important:** Copy the ARN from the output - you'll need it in the next step.

### Step 2: Update Terraform Variables

Edit your `terraform.tfvars` file to include the ServiceNow configuration:

```bash
cd terraform/environments/dev-secure
```

Add/update these variables in `terraform.tfvars`:

```hcl
# ServiceNow Integration Configuration
enable_servicenow_integration = false  # Keep false for initial deployment
servicenow_secret_arn         = "arn:aws:secretsmanager:eu-west-1:992155623828:secret:cert-management/servicenow/credentials-AbCdEf"
servicenow_dry_run            = "true"   # Start in dry-run mode
servicenow_enable_schedule    = true     # Enable automatic scheduling
servicenow_schedule           = "cron(5 9 * * ? *)"  # 9:05 AM UTC daily
servicenow_enable_alarms      = false    # Disable alarms initially
```

### Step 3: Deploy Infrastructure (Dry-Run Mode)

```bash
# Initialize Terraform (if not already done)
terraform init

# Review the plan - this should show NO changes to existing resources
terraform plan

# Apply the changes
terraform apply
```

**What happens:**
- ✅ No resources are created yet (because `enable_servicenow_integration = false`)
- ✅ Terraform validates module configuration
- ✅ No impact on existing infrastructure

### Step 4: Enable ServiceNow Integration

Update `terraform.tfvars`:

```hcl
enable_servicenow_integration = true   # Enable the integration
servicenow_dry_run            = "true" # Keep dry-run enabled for testing
```

Apply the changes:

```bash
terraform plan -out=tfplan
terraform apply tfplan
```

**Expected Resources Created:**
```
Plan: 6 to add, 0 to change, 0 to destroy.

# aws_cloudwatch_log_group.servicenow_lambda
# aws_lambda_function.servicenow_ticket_creator
# aws_cloudwatch_event_rule.servicenow_schedule
# aws_cloudwatch_event_target.servicenow_schedule
# aws_lambda_permission.allow_eventbridge_servicenow
# aws_iam_role_policy.servicenow_lambda_policy
```

### Step 5: Verify Deployment

Check that resources were created successfully:

```bash
# Check Lambda function
aws lambda get-function \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --query 'Configuration.{Name:FunctionName,State:State,Runtime:Runtime}' \
  --output table

# Check EventBridge rule
aws events describe-rule \
  --name cert-management-dev-secure-servicenow-schedule \
  --query '{Name:Name,State:State,Schedule:ScheduleExpression}' \
  --output table

# Check CloudWatch Logs
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/cert-management-dev-secure-servicenow \
  --query 'logGroups[*].logGroupName' \
  --output table
```

---

## Configuration

### Feature Flags

The integration is controlled by several feature flags:

| Variable | Purpose | Default | When to Change |
|----------|---------|---------|----------------|
| `enable_servicenow_integration` | Master switch for the entire integration | `false` | Set to `true` to deploy |
| `servicenow_dry_run` | Prevents actual ticket creation | `"true"` | Set to `"false"` after testing |
| `servicenow_enable_schedule` | Enables automatic daily execution | `true` | Keep `true` for automation |
| `servicenow_enable_alarms` | Enables CloudWatch alarms | `false` | Set to `true` after stable |

### Priority Mapping

Tickets are automatically assigned priorities based on days until expiry:

| Days Until Expiry | Priority | Label | Action Required |
|-------------------|----------|-------|-----------------|
| Already expired | 1 | Critical | Immediate action |
| < 7 days | 2 | High | Urgent renewal needed |
| 7-14 days | 3 | Medium | Plan renewal soon |
| 15-30 days | 4 | Low | Schedule renewal |
| > 30 days | 5 | Planning | Early notification |

### Schedule Configuration

Default schedule: **9:05 AM UTC daily** (5 minutes after certificate monitor)

To change the schedule:

```hcl
# Every 6 hours
servicenow_schedule = "cron(0 */6 * * ? *)"

# Twice daily (9 AM and 9 PM UTC)
servicenow_schedule = "cron(0 9,21 * * ? *)"

# Monday-Friday only
servicenow_schedule = "cron(0 9 ? * MON-FRI *)"
```

---

## Testing

### Phase 1: Manual Invocation (Dry-Run)

Test the Lambda function manually to verify it works:

```bash
# Invoke Lambda function manually
aws lambda invoke \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  response.json

# Check the response
cat response.json | jq .

# Expected output (dry-run mode):
{
  "statusCode": 200,
  "body": {
    "message": "ServiceNow ticket creation completed",
    "summary": {
      "timestamp": "2025-11-10T...",
      "expiry_threshold_days": 30,
      "dry_run": true,
      "certificates": {
        "total_expiring": 5,
        "needing_tickets": 3,
        "already_have_tickets": 2
      },
      "tickets": {
        "created": 0,
        "failed": 0,
        "skipped": 3
      }
    }
  }
}
```

**Verify in CloudWatch Logs:**

```bash
# View Lambda logs
aws logs tail /aws/lambda/cert-management-dev-secure-servicenow-ticket-creator --follow
```

**Expected log entries:**
```
[INFO] ServiceNow Ticket Creator started
[INFO] DRY_RUN mode: True
[INFO] Found 5 expiring certificates
[INFO] Filtered to 3 certificates needing tickets
[INFO] DRY_RUN: Would create ticket for wildcard.example.com
[INFO] Ticket creation completed
```

### Phase 2: Test with Single Certificate

Update **one test certificate** to trigger ticket creation:

```bash
# Remove IncidentNumber from a test certificate in DynamoDB
aws dynamodb update-item \
  --table-name cert-management-dev-secure-certificates \
  --key '{"CertificateID":{"S":"YOUR_TEST_CERT_ID"}}' \
  --update-expression "REMOVE IncidentNumber" \
  --return-values ALL_NEW
```

Now invoke Lambda again and check that it identifies this certificate.

### Phase 3: Enable Actual Ticket Creation

After confirming dry-run works correctly, enable actual ticket creation:

**Update terraform.tfvars:**
```hcl
servicenow_dry_run = "false"  # Disable dry-run mode
```

**Apply changes:**
```bash
terraform apply -auto-approve
```

**Test with ONE certificate:**
```bash
aws lambda invoke \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

**Verify ticket creation:**

1. **Check Lambda response:**
   ```bash
   cat response.json | jq '.body.summary.tickets'
   ```
   
   Expected:
   ```json
   {
     "created": 1,
     "failed": 0,
     "skipped": 0
   }
   ```

2. **Check DynamoDB for IncidentNumber:**
   ```bash
   aws dynamodb get-item \
     --table-name cert-management-dev-secure-certificates \
     --key '{"CertificateID":{"S":"YOUR_TEST_CERT_ID"}}' \
     --query 'Item.IncidentNumber.S'
   ```

3. **Check ServiceNow:**
   - Login to https://sogetinltest.service-now.com
   - Navigate to Incidents
   - Search for incident with correlation ID = CertificateID
   - Verify ticket details match certificate information

### Phase 4: Automated Schedule Test

Let the EventBridge rule trigger automatically at 9:05 AM UTC:

**Monitor execution:**
```bash
# Wait until 9:05 AM UTC, then check CloudWatch Logs
aws logs tail /aws/lambda/cert-management-dev-secure-servicenow-ticket-creator \
  --since 10m \
  --follow
```

**Verify execution history:**
```bash
# Check Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=cert-management-dev-secure-servicenow-ticket-creator \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

---

## Enabling Production Mode

### Gradual Rollout Strategy

**Step 1: Test Environment Only (Week 1)**

Filter to only create tickets for test environment:

Temporarily modify the Lambda code or add an environment variable filter.

**Step 2: Specific Application (Week 2)**

Monitor results for a specific application:
- Check ticket quality
- Verify no duplicates
- Confirm priority mapping is correct

**Step 3: Full Production (Week 3+)**

After successful testing, enable for all environments:

```hcl
# terraform.tfvars
servicenow_dry_run = "false"
servicenow_enable_alarms = true
```

Apply:
```bash
terraform apply
```

---

## Monitoring

### CloudWatch Dashboards

Create a custom dashboard to monitor the integration:

```bash
# Example: View Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=cert-management-dev-secure-servicenow-ticket-creator \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average,Maximum
```

### Key Metrics to Monitor

1. **Lambda Invocations**: Should be 1/day (unless manually triggered)
2. **Lambda Errors**: Should be 0
3. **Lambda Duration**: Should be < 60 seconds
4. **Tickets Created**: Check audit logs

### Audit Trail

Query the logs table for ticket creation history:

```bash
aws dynamodb query \
  --table-name cert-management-dev-secure-logs \
  --index-name ActionIndex \
  --key-condition-expression "Action = :action" \
  --expression-attribute-values '{":action":{"S":"SERVICENOW_TICKET_CREATED"}}' \
  --scan-index-forward false \
  --limit 10
```

### CloudWatch Alarms (When Enabled)

```bash
# Check alarm status
aws cloudwatch describe-alarms \
  --alarm-name-prefix cert-management-dev-secure-servicenow \
  --query 'MetricAlarms[*].{Name:AlarmName,State:StateValue}' \
  --output table
```

---

## Troubleshooting

### Issue: Lambda Function Not Creating Tickets

**Symptoms:**
- Lambda runs successfully
- No tickets created in ServiceNow
- Logs show "skipped" count

**Diagnosis:**
```bash
# Check if dry-run is still enabled
aws lambda get-function-configuration \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --query 'Environment.Variables.DRY_RUN'
```

**Solution:**
If output is `"true"`, update terraform.tfvars and re-deploy:
```hcl
servicenow_dry_run = "false"
```

---

### Issue: "Failed to retrieve ServiceNow credentials"

**Symptoms:**
- Lambda fails with error about credentials
- CloudWatch shows "Error retrieving secret"

**Diagnosis:**
```bash
# Check if secret exists
aws secretsmanager describe-secret \
  --secret-id cert-management/servicenow/credentials

# Check Lambda has permission
aws lambda get-policy \
  --function-name cert-management-dev-secure-servicenow-ticket-creator
```

**Solution:**
Ensure the secret ARN in terraform.tfvars matches the actual secret ARN.

---

### Issue: "ServiceNow API returned status 401"

**Symptoms:**
- Lambda gets 401 Unauthorized from ServiceNow
- OAuth token retrieval fails

**Diagnosis:**
```bash
# Test credentials manually
aws secretsmanager get-secret-value \
  --secret-id cert-management/servicenow/credentials \
  --query SecretString \
  --output text | jq .
```

**Solution:**
1. Verify credentials in ServiceNow
2. Check if password has expired
3. Ensure client_id and client_secret are correct
4. Update secret if needed:
   ```bash
   aws secretsmanager update-secret \
     --secret-id cert-management/servicenow/credentials \
     --secret-string '{...updated credentials...}'
   ```

---

### Issue: Duplicate Tickets Being Created

**Symptoms:**
- Multiple tickets for same certificate
- IncidentNumber not being updated in DynamoDB

**Diagnosis:**
```bash
# Check if IncidentNumber field is being updated
aws dynamodb get-item \
  --table-name cert-management-dev-secure-certificates \
  --key '{"CertificateID":{"S":"CERT_ID"}}' \
  --query 'Item.{IncidentNumber:IncidentNumber,LastUpdatedOn:LastUpdatedOn}'
```

**Solution:**
- Check Lambda has DynamoDB UpdateItem permission
- Verify no errors in CloudWatch Logs during update
- Manually set IncidentNumber if needed to prevent duplicates

---

### Issue: EventBridge Rule Not Triggering

**Symptoms:**
- No automatic executions at scheduled time
- Lambda only runs when manually invoked

**Diagnosis:**
```bash
# Check EventBridge rule status
aws events describe-rule \
  --name cert-management-dev-secure-servicenow-schedule \
  --query '{State:State,Schedule:ScheduleExpression}'

# Check targets
aws events list-targets-by-rule \
  --rule cert-management-dev-secure-servicenow-schedule
```

**Solution:**
If rule is DISABLED:
```bash
aws events enable-rule \
  --name cert-management-dev-secure-servicenow-schedule
```

Or via Terraform:
```hcl
servicenow_enable_schedule = true
```

---

## Rollback Procedures

### Emergency Disable (Immediate)

**Option 1: Disable EventBridge Rule** (Stops automatic execution, Lambda still exists)
```bash
aws events disable-rule \
  --name cert-management-dev-secure-servicenow-schedule
```

**Option 2: Update to Dry-Run Mode** (Lambda runs but creates no tickets)
```bash
aws lambda update-function-configuration \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --environment "Variables={CERTIFICATES_TABLE=cert-management-dev-secure-certificates,LOGS_TABLE=cert-management-dev-secure-logs,SNOW_SECRET_NAME=cert-management/servicenow/credentials,EXPIRY_THRESHOLD_DAYS=30,DRY_RUN=true}"
```

**Option 3: Feature Flag Disable** (Cleanest - use Terraform)
```hcl
# Update terraform.tfvars
enable_servicenow_integration = false
```

```bash
terraform apply -auto-approve
```

This removes all ServiceNow integration resources while keeping existing infrastructure intact.

### Verify Existing Monitoring Still Works

After rollback, verify the original certificate monitoring continues:

```bash
# Check certificate monitor Lambda
aws lambda get-function \
  --function-name cert-management-dev-secure-certificate-monitor \
  --query 'Configuration.{State:State,LastModified:LastModified}'

# Check its EventBridge rule
aws events describe-rule \
  --name cert-management-dev-secure-monitor \
  --query '{State:State,Schedule:ScheduleExpression}'

# Manually trigger a test
aws lambda invoke \
  --function-name cert-management-dev-secure-certificate-monitor \
  --payload '{}' \
  test-response.json
```

**Expected:** Certificate monitor works exactly as before, no impact from ServiceNow integration removal.

---

## Post-Deployment Checklist

- [ ] Secrets Manager secret created with correct credentials
- [ ] Terraform variables updated with secret ARN
- [ ] Infrastructure deployed with `enable_servicenow_integration = true`
- [ ] Lambda function created and showing "Active" state
- [ ] EventBridge rule created and in "ENABLED" state
- [ ] IAM permissions verified (Lambda can access DynamoDB, Secrets Manager)
- [ ] Manual invocation tested successfully (dry-run mode)
- [ ] ServiceNow ticket created for test certificate
- [ ] IncidentNumber updated in DynamoDB
- [ ] Audit log entry created in logs table
- [ ] CloudWatch Logs showing successful execution
- [ ] Existing certificate monitor still functioning
- [ ] No disruption to email notifications
- [ ] Automated schedule tested (wait for 9:05 AM UTC)
- [ ] Monitoring dashboards configured
- [ ] Team trained on new integration
- [ ] Rollback procedure documented and tested

---

## Support and Escalation

### Common Issues

| Issue | Check | Fix |
|-------|-------|-----|
| No tickets created | DRY_RUN mode | Set `servicenow_dry_run = "false"` |
| 401 Unauthorized | ServiceNow credentials | Update secret with correct credentials |
| Duplicate tickets | DynamoDB updates | Check IAM permissions for UpdateItem |
| Missing logs | CloudWatch Logs | Check Lambda execution role has logs:PutLogEvents |
| Schedule not running | EventBridge rule | Enable rule with `aws events enable-rule` |

### Escalation Path

1. **Check CloudWatch Logs first** - 90% of issues visible here
2. **Review Terraform state** - Verify resources are deployed
3. **Test ServiceNow connectivity** - Manually test OAuth flow
4. **Rollback if critical** - Use feature flag to disable
5. **Contact team** - Provide logs and error messages

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-10 | Initial deployment guide |

---

**End of Deployment Guide**
