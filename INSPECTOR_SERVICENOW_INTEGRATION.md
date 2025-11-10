# AWS Inspector to ServiceNow Integration

## Overview

This document describes the current integration between AWS Inspector findings and ServiceNow incident management in the PostNL AWS environment (account: 992155623828).

## Architecture

```
┌─────────────────┐
│  AWS Inspector  │
│   Findings      │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Security Hub   │ (Aggregator)
│   Findings      │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────┐
│     EventBridge Rule                │
│  "SecurityHub-ServiceNow-API"       │
│  (Currently DISABLED)               │
│                                     │
│  Event Pattern:                     │
│  - Source: aws.securityhub          │
│  - Type: Security Hub Findings      │
│  - Product: Inspector               │
│  - Severity: HIGH                   │
│  - Workflow Status: NEW             │
└────────┬────────────────────────────┘
         │
         ├─────────────────┬─────────────────┐
         │                 │                 │
         v                 v                 v
┌────────────────┐  ┌──────────────────┐  ┌────────────────┐
│ Lambda:        │  │ Lambda:          │  │ Dead Letter    │
│ test-hasan     │  │ pnl-sandbox-lmb- │  │ Queue (SQS):   │
│                │  │ snow-integration │  │ Inspector-     │
│ (Primary)      │  │                  │  │ standardQ      │
└────────────────┘  └────────┬─────────┘  └────────────────┘
                             │
                             │ OAuth2 (Password Grant)
                             v
                    ┌─────────────────┐
                    │  ServiceNow     │
                    │  Instance:      │
                    │  sogetinltest   │
                    │                 │
                    │  Creates:       │
                    │  - Incident     │
                    │  - Updates      │
                    │    Workflow     │
                    └─────────────────┘
```

## Components

### 1. EventBridge Rule: `SecurityHub-ServiceNow-API`

**Status:** DISABLED
**ARN:** `arn:aws:events:eu-west-1:992155623828:rule/SecurityHub-ServiceNow-API`

#### Event Pattern
```json
{
  "source": ["aws.securityhub"],
  "detail-type": ["Security Hub Findings - Imported"],
  "detail": {
    "findings": {
      "ProductFields": {
        "aws/securityhub/ProductName": ["Inspector"]
      },
      "Severity": {
        "Label": ["HIGH"]
      },
      "Workflow": {
        "Status": ["NEW"]
      }
    }
  }
}
```

**Filter Criteria:**
- ✅ Only Inspector findings (not other Security Hub sources)
- ✅ Only HIGH severity findings
- ✅ Only NEW workflow status (not NOTIFIED, SUPPRESSED, or RESOLVED)

#### Targets

1. **Lambda Function: test-hasan**
   - ARN: `arn:aws:lambda:eu-west-1:992155623828:function:test-hasan`
   - Dead Letter Queue: `Inspector-standardQ`
   - Max Retry Attempts: 1

2. **Lambda Function: pnl-sandbox-lmb-snow-integration**
   - ARN: `arn:aws:lambda:eu-west-1:992155623828:function:pnl-sandbox-lmb-snow-integration`
   - Runtime: Python 3.9
   - Handler: lambda_function.lambda_handler
   - Timeout: 60 seconds
   - Memory: 128 MB

### 2. Lambda Function: `pnl-sandbox-lmb-snow-integration`

**Purpose:** Create ServiceNow incidents from AWS Inspector findings via Security Hub

#### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `serviceNowUser_ssmlocation` | `/servicenow/user` | SSM Parameter for ServiceNow username |
| `serviceNowPass_ssmlocation` | `/servicenow/password` | SSM Parameter for ServiceNow password |
| `servicenow_instance` | `sogetinltest` | ServiceNow instance name (TEST) |
| `snow_customer_name` | `PostNL B.V.` | Customer name in ServiceNow |
| `service_table` | `customer_account` | ServiceNow table name |
| `ACCOUNT_MAPPING` | JSON object | Maps AWS Account IDs to friendly names |

#### Account Mapping (Excerpt)
```json
{
  "992155623828": "postnl-aws-sdb",
  "992382754156": "postnl-aws-vfm-prd",
  "653203554104": "postnl-aws-prd",
  "537496672861": "postnl-aws-acc",
  "527945431616": "postnl-aws-tst",
  ...
}
```

#### ServiceNow Configuration

**Test Environment:**
- Instance URL: `https://sogetinltest.service-now.com`
- OAuth Token URL: `https://sogetinltest.service-now.com/oauth_token.do`
- API Endpoint: `https://sogetinltest.service-now.com/api/x_lsmcb_sca/sc`
- Client ID: `d3168ff13a90d210d69932fd03ea9695`
- OAuth Username: `AWSMonitoring.apiUserDev`
- Grant Type: `password` (OAuth2 Password Grant Flow)
- Scope: `useraccount`

**UAT Environment (Commented out in code):**
- Instance URL: `https://sogetinluat.service-now.com`
- OAuth Username: `AWSMonitoring.apiUserUAT`
- Client ID: `51664735fe90d2105d9f1c8037d2117b`

### 3. Lambda Function Logic

#### Key Functions

1. **`get_snow_token()`**
   - Authenticates with ServiceNow using OAuth2 password grant
   - Returns access token for API calls
   - Uses HTTPBasicAuth with client credentials

2. **`fetch_data(event)`**
   - Extracts findings from EventBridge event
   - Maps AWS Account ID to friendly account name
   - Formats vulnerability reports with:
     - Account Name
     - Finding ARN
     - Description
     - Affected Resource ID
     - Remediation steps
   - Returns JSON formatted findings

3. **`create_snow_incident()` (Currently Disabled)**
   - Creates ServiceNow incident with POST request
   - Incident data includes:
     - Interface: `incident`
     - Sender: `azure_monitoring` (legacy naming)
     - Short Description: Finding description
     - Full Description: Vulnerability reports
     - Caller: API user
     - Correlation ID: EventBridge event ID
     - Business Service: `PostNL Generic SecOps AWS`
     - Service Offering: `PostNL Generic SecOps AWS`
     - Company: `PostNL B.V.`
     - Priority: `4` (hardcoded)

4. **`update_finding_status(finding)`**
   - Updates Security Hub finding workflow status to `NOTIFIED`
   - Uses boto3 SecurityHub client
   - Prevents duplicate incident creation

#### Current Implementation Status

**ACTIVE CODE:**
- ✅ Event parsing and data extraction
- ✅ Account ID to name mapping
- ✅ Vulnerability report formatting
- ✅ Security Hub workflow status update to NOTIFIED
- ❌ ServiceNow incident creation (commented out)

**NOTE:** The `create_snow_incident()` function call is commented out in `lambda_handler()`. The Lambda currently:
1. Extracts and formats Inspector findings
2. Updates Security Hub workflow to NOTIFIED
3. **Does NOT** create actual ServiceNow incidents

### 4. Dead Letter Queue: `Inspector-standardQ`

**ARN:** `arn:aws:sqs:eu-west-1:992155623828:Inspector-standardQ`
**Type:** Standard SQS Queue

**Configuration:**
- Visibility Timeout: 30 seconds
- Message Retention: 4 days (345,600 seconds)
- Max Message Size: 256 KB
- Encryption: SQS Managed SSE (enabled)
- Current Messages: 0

**Purpose:**
- Captures failed Lambda invocations from EventBridge
- Allows retry and debugging of failed integrations
- Prevents data loss for critical security findings

### 5. IAM Role: `test-hasan-role-boelfu89`

**ARN:** `arn:aws:iam::992155623828:role/service-role/test-hasan-role-boelfu89`

**Required Permissions:**
- `lambda:InvokeFunction` (granted via EventBridge)
- `ssm:GetParameter` (for ServiceNow credentials)
- `securityhub:BatchUpdateFindings` (for workflow updates)
- `sqs:SendMessage` (for dead letter queue)
- CloudWatch Logs (for Lambda logging)

## Integration Flow

### Normal Operation (When Enabled)

1. **Inspector Scan**
   - AWS Inspector scans EC2, ECR, Lambda for vulnerabilities
   - Findings are generated in Inspector

2. **Security Hub Import**
   - Inspector findings are automatically imported to Security Hub
   - Security Hub normalizes findings to AWS Security Finding Format (ASFF)

3. **EventBridge Trigger**
   - EventBridge rule matches on:
     - Source: `aws.securityhub`
     - Detail Type: `Security Hub Findings - Imported`
     - Product: `Inspector`
     - Severity: `HIGH`
     - Workflow: `NEW`

4. **Lambda Processing**
   - Lambda receives EventBridge event with finding details
   - Extracts account ID, finding ARN, description, resource ID, remediation
   - Maps account ID to friendly name (e.g., `postnl-aws-prd`)
   - Formats vulnerability report

5. **ServiceNow Integration** (Currently Disabled)
   - ~~Authenticates with ServiceNow using OAuth2~~
   - ~~Creates incident via REST API~~
   - ~~Returns incident number~~

6. **Workflow Update**
   - Updates Security Hub finding status from `NEW` to `NOTIFIED`
   - Prevents duplicate processing

7. **Error Handling**
   - Failed invocations are sent to `Inspector-standardQ`
   - Maximum 1 retry attempt
   - Errors logged to CloudWatch Logs

### Current State (Rule Disabled)

❌ EventBridge rule is **DISABLED**
- No automatic incident creation
- Inspector findings flow to Security Hub but no downstream actions
- Manual remediation required

## Sample Event

```json
{
  "id": "abc123-event-id",
  "account": "992155623828",
  "detail": {
    "findings": [
      {
        "Id": "arn:aws:inspector2:eu-west-1:992155623828:finding/abc123",
        "Description": "CVE-2023-12345 found in package xyz",
        "ProductFields": {
          "aws/securityhub/ProductName": "Inspector"
        },
        "Severity": {
          "Label": "HIGH"
        },
        "Workflow": {
          "Status": "NEW"
        },
        "Resources": [
          {
            "Id": "arn:aws:ec2:eu-west-1:992155623828:instance/i-abc123",
            "Details": {
              "AwsEc2Instance": {
                "Type": "t3.medium",
                "ImageId": "ami-xyz789"
              }
            }
          }
        ],
        "Remediation": {
          "Recommendation": {
            "Text": "Update package xyz to version 2.0 or later"
          }
        }
      }
    ]
  }
}
```

## Sample ServiceNow Incident

**When integration is enabled, incidents are created with:**

```
Incident Number: INCxxxxxxx
Short Description: CVE-2023-12345 found in package xyz
Description:
--- Sechub Inspector Vulnerability ---

Account Name: postnl-aws-prd

Finding ARN: arn:aws:inspector2:eu-west-1:992155623828:finding/abc123

Description: CVE-2023-12345 found in package xyz

Affected Resource ID: arn:aws:ec2:eu-west-1:992155623828:instance/i-abc123

Remediation: Update package xyz to version 2.0 or later
-----------------------------

Caller: AWSMonitoring.apiUserDev
Correlation ID: abc123-event-id
Business Service: PostNL Generic SecOps AWS
Service Offering: PostNL Generic SecOps AWS
Company: PostNL B.V.
Priority: 4
```

## Troubleshooting

### EventBridge Rule is Disabled

**Symptom:** No incidents created in ServiceNow
**Resolution:**
```bash
# Enable the rule
aws events enable-rule --name SecurityHub-ServiceNow-API
```

### ServiceNow Incident Creation Commented Out

**Symptom:** Lambda runs successfully but no ServiceNow incidents
**Cause:** Lines 127-128 in `lambda_function.py` are commented:
```python
# access_token = get_snow_token()
# incident_number = create_snow_incident(...)
```

**Resolution:**
1. Uncomment ServiceNow integration code
2. Verify credentials in SSM Parameter Store:
   - `/servicenow/user`
   - `/servicenow/password`
3. Test OAuth token retrieval
4. Update Lambda function

### Failed Lambda Invocations

**Check Dead Letter Queue:**
```bash
aws sqs receive-message \
  --queue-url https://sqs.eu-west-1.amazonaws.com/992155623828/Inspector-standardQ \
  --max-number-of-messages 10
```

**Check CloudWatch Logs:**
```bash
aws logs tail /aws/lambda/pnl-sandbox-lmb-snow-integration --follow
```

### OAuth Token Failures

**Common Issues:**
- Expired credentials
- Incorrect client ID/secret
- Wrong ServiceNow instance URL
- SSM Parameter Store access denied

**Verify Token:**
```bash
# Test token retrieval manually
curl -X POST https://sogetinltest.service-now.com/oauth_token.do \
  -u "CLIENT_ID:CLIENT_SECRET" \
  -d "grant_type=password&username=USER&password=PASS&scope=useraccount"
```

### Finding Not Matching Event Pattern

**Verify:**
- Severity is HIGH (not MEDIUM, LOW, or CRITICAL)
- Workflow Status is NEW (not NOTIFIED)
- Product is Inspector (not GuardDuty, Config, etc.)

## Monitoring

### CloudWatch Metrics

**Lambda Metrics:**
- Invocations: Number of times Lambda is triggered
- Errors: Failed executions
- Duration: Execution time
- Throttles: Rate limit hits

**SQS Metrics:**
- ApproximateNumberOfMessagesVisible: Messages in DLQ
- ApproximateAgeOfOldestMessage: Oldest message age

### CloudWatch Alarms (Recommended)

1. **High DLQ Messages**
   ```
   Metric: ApproximateNumberOfMessagesVisible
   Threshold: > 5
   Action: SNS notification to security team
   ```

2. **Lambda Errors**
   ```
   Metric: Errors
   Threshold: > 2 in 5 minutes
   Action: SNS notification
   ```

### CloudWatch Logs

**Log Group:** `/aws/lambda/pnl-sandbox-lmb-snow-integration`

**Key Log Patterns:**
```
"Received Event:" - Full event payload
"Sent data" - Formatted findings JSON
"Updated finding X to NOTIFIED" - Workflow update success
"Failed to create incident" - ServiceNow API error
"Failed to retrieve token" - OAuth error
```

## Security Considerations

### Credentials Management

✅ **GOOD:**
- ServiceNow credentials stored in SSM Parameter Store
- OAuth2 password grant flow (better than API keys)
- Client secrets not hardcoded (in SSM)

⚠️ **CONCERNS:**
- Credentials visible in code comments (should be removed)
- Hardcoded URLs and client IDs in Lambda code
- Consider using AWS Secrets Manager instead of SSM

### IAM Least Privilege

**Current permissions should be reviewed:**
- Lambda execution role may have broader permissions than needed
- Consider dedicated role for ServiceNow integration only

### Network Security

- Lambda runs in default VPC (check if VPC endpoints needed)
- ServiceNow API accessed over public internet (HTTPS)
- Consider PrivateLink if available

## Cost Estimation

### Monthly Costs (Estimated for 100 HIGH findings/month)

| Service | Usage | Cost |
|---------|-------|------|
| EventBridge | 100 events/month | $0.00 (free tier) |
| Lambda | 100 invocations × 60s × 128MB | ~$0.01 |
| SQS | Minimal DLQ messages | $0.00 |
| CloudWatch Logs | 5 MB/month | $0.00 |
| **Total** | | **~$0.01/month** |

**Note:** Security Hub and Inspector costs are separate

## Future Enhancements

### Recommended Improvements

1. **Enable the Integration**
   - Uncomment ServiceNow incident creation code
   - Enable EventBridge rule
   - Test with non-production findings first

2. **Dynamic Priority Mapping**
   ```python
   severity_to_priority = {
       "CRITICAL": "1",
       "HIGH": "2",
       "MEDIUM": "3",
       "LOW": "4"
   }
   priority = severity_to_priority.get(finding['Severity']['Label'], "4")
   ```

3. **Support Multiple Severity Levels**
   - Update EventBridge pattern to include CRITICAL, MEDIUM
   - Add separate rules for different severity levels

4. **Idempotency**
   - Check if incident already exists before creating
   - Use correlation_id to prevent duplicates
   - Store incident number in Security Hub finding notes

5. **Bi-directional Sync**
   - Webhook from ServiceNow back to Security Hub
   - Update Security Hub when ServiceNow incident is resolved
   - Sync status: NEW → NOTIFIED → RESOLVED

6. **Enhanced Error Handling**
   - Exponential backoff for retries
   - Structured error logging
   - Alerting on repeated failures

7. **Environment Configuration**
   - Use environment variable for ServiceNow instance URL
   - Support prod/uat/test environments dynamically
   - Externalize all configuration

8. **Metrics and Dashboards**
   - Custom CloudWatch metrics for incident creation rate
   - Dashboard showing findings → incidents pipeline
   - SLA tracking for time-to-notify

9. **Cross-Account Support**
   - Aggregate findings from multiple AWS accounts
   - Organization-level Security Hub integration
   - Account mapping expansion

10. **Compliance Reporting**
    - Track MTTD (Mean Time To Detect)
    - Track MTTR (Mean Time To Remediate)
    - Export metrics for compliance audits

## Related AWS Services

- **AWS Inspector:** Vulnerability scanning service
- **AWS Security Hub:** Security findings aggregation
- **Amazon EventBridge:** Event-driven automation
- **AWS Lambda:** Serverless compute
- **Amazon SQS:** Dead letter queue for failed events
- **AWS Systems Manager:** Parameter Store for credentials
- **IAM:** Identity and access management

## Documentation Links

- [AWS Inspector Documentation](https://docs.aws.amazon.com/inspector/)
- [AWS Security Hub Documentation](https://docs.aws.amazon.com/securityhub/)
- [EventBridge Event Patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html)
- [ServiceNow OAuth 2.0](https://docs.servicenow.com/bundle/tokyo-platform-security/page/administer/security/concept/c_OAuthApplications.html)
- [AWS Security Finding Format](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-findings-format.html)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-11-10 | Initial documentation - Integration discovered and documented |

## Contact

**Team:** PostNL SecOps AWS
**Lambda Function Owner:** See IAM role tags
**ServiceNow Integration:** AWSMonitoring.apiUserDev

---

**Status:** Integration infrastructure exists but is currently **DISABLED**
- EventBridge rule: DISABLED
- ServiceNow incident creation: Commented out in code
- Finding workflow updates: ACTIVE
