# Server Certificate Sync Feature

## Overview

The **Server Certificate Sync** feature provides on-demand, manual synchronization of certificates from Windows and Linux servers into the certificate management dashboard. This complements the automated daily server scans and gives administrators immediate control over certificate discovery.

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Components](#components)
4. [How It Works](#how-it-works)
5. [Deployment](#deployment)
6. [Usage](#usage)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## Features

### User Interface
- ✅ **Green "Sync from Servers" button** - Prominent placement next to "Sync from ACM" button
- ✅ **Real-time progress modal** - Shows scanning status with loading spinner
- ✅ **Detailed results display** - Shows metrics after scan completion:
  - Total servers scanned
  - Total certificates found
  - New certificates added
  - Error count
  - Platform breakdown (Windows/Linux)
- ✅ **Error handling** - User-friendly error messages with technical details
- ✅ **Dashboard refresh** - One-click refresh to view newly discovered certificates

### Backend Capabilities
- ✅ **Synchronous execution** - Returns real-time scan results (not fire-and-forget)
- ✅ **Cross-Lambda invocation** - Dashboard API invokes server scanner Lambda
- ✅ **Cognito authentication** - Secured with JWT token validation
- ✅ **CORS support** - Proper cross-origin resource sharing configuration
- ✅ **SSM integration** - Uses AWS Systems Manager to scan EC2 instances
- ✅ **Duplicate prevention** - Won't create duplicate certificates in DynamoDB
- ✅ **Modular Terraform** - Fully automated infrastructure deployment

---

## Architecture

### High-Level Flow

```
┌─────────────┐
│   User      │
│  Browser    │
└──────┬──────┘
       │ 1. Click "Sync from Servers"
       ▼
┌─────────────────────────────────┐
│  Dashboard (index.html)         │
│  - triggerServerSync()          │
│  - Shows modal with progress    │
└──────┬──────────────────────────┘
       │ 2. POST /sync-server-certs
       │    (with Cognito JWT token)
       ▼
┌─────────────────────────────────┐
│  API Gateway                    │
│  - /dev-secure/sync-server-certs│
│  - Cognito Authorizer           │
│  - CORS enabled                 │
└──────┬──────────────────────────┘
       │ 3. Invoke Lambda (AWS_PROXY)
       ▼
┌─────────────────────────────────┐
│  Dashboard API Lambda           │
│  - dashboard_api.py             │
│  - handle_server_cert_sync()    │
└──────┬──────────────────────────┘
       │ 4. Invoke server scanner
       │    (RequestResponse mode)
       ▼
┌─────────────────────────────────┐
│  Server Scanner Lambda          │
│  - server_certificate_scanner.py│
│  - Scans via SSM                │
└──────┬──────────────────────────┘
       │ 5. Execute SSM commands
       ▼
┌─────────────────────────────────┐
│  EC2 Instances                  │
│  - Windows (certutil)           │
│  - Linux (openssl)              │
└──────┬──────────────────────────┘
       │ 6. Return cert data
       ▼
┌─────────────────────────────────┐
│  DynamoDB                       │
│  - Store certificates           │
│  - Update existing entries      │
└─────────────────────────────────┘
```

### Data Flow

1. **User initiates scan** → Click button in dashboard
2. **API Gateway authenticates** → Validates Cognito JWT token
3. **Dashboard API invokes scanner** → Synchronous Lambda invocation
4. **Scanner executes SSM commands** → Runs on tagged EC2 instances
5. **Certificates parsed** → Extracts details (CN, expiry, thumbprint, etc.)
6. **DynamoDB updated** → New certs added, existing preserved
7. **Results returned** → Real-time feedback to user via modal

---

## Components

### Frontend Components

#### 1. Button (index.html)
```html
<button class="btn btn-success" onclick="triggerServerSync()" id="serverSyncBtn">
    <i class="fas fa-server"></i> Sync from Servers
</button>
```

**Location:** Line 466-468 in `dashboard/index.html`  
**Style:** Bootstrap `btn-success` (green)  
**Icon:** Font Awesome server icon

#### 2. Modal (index.html)
```html
<div class="modal" id="serverSyncModal">
    <!-- Progress section -->
    <div id="serverSyncProgress">...</div>
    
    <!-- Results section -->
    <div id="serverSyncResults">...</div>
    
    <!-- Error section -->
    <div id="serverSyncError">...</div>
</div>
```

**Location:** Lines 738-828 in `dashboard/index.html`  
**States:** Progress → Results or Error  
**Features:** 
- Loading spinner during scan
- Metrics grid (4 columns)
- Platform details
- Refresh dashboard button

#### 3. JavaScript Functions (dashboard.js)

**triggerServerSync()**
- Makes POST request to `/sync-server-certs`
- Includes Cognito JWT in Authorization header
- Handles response parsing
- Updates modal with results or errors

**showServerSyncResults()**
- Updates modal DOM elements
- Displays scan metrics
- Shows platform breakdown

**Location:** Lines 1605-1700 in `dashboard/dashboard.js`

### Backend Components

#### 1. API Gateway Endpoint

**Resource:** `/sync-server-certs`  
**Methods:** 
- `POST` - Trigger scan (Cognito authorized)
- `OPTIONS` - CORS preflight (no auth)

**Integration:** AWS_PROXY to Dashboard API Lambda  
**Authorization:** Cognito User Pool (ID: dmhpjj)  
**CORS Headers:**
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: POST,OPTIONS`
- `Access-Control-Allow-Headers: Content-Type,Authorization,...`

**Terraform Resources:**
- `aws_api_gateway_resource.sync_server_certs`
- `aws_api_gateway_method.post_sync_server_certs`
- `aws_api_gateway_method.options_sync_server_certs`
- `aws_api_gateway_integration.post_sync_server_certs`
- `aws_api_gateway_integration.options_sync_server_certs`
- `aws_api_gateway_method_response.options_sync_server_certs_200`
- `aws_api_gateway_integration_response.options_sync_server_certs_200`

**Location:** `terraform/modules/api_gateway/main.tf` lines 246-320

#### 2. Dashboard API Lambda Handler

**Function:** `handle_server_cert_sync()`  
**File:** `lambda/dashboard_api.py` lines 382-431  

**Key Features:**
- Gets `SERVER_SCANNER_FUNCTION` from environment variables
- Invokes scanner with `RequestResponse` (synchronous)
- Parses JSON response from scanner
- Returns results to API Gateway

**Environment Variable:**
```python
SERVER_SCANNER_FUNCTION = os.environ.get(
    'SERVER_SCANNER_FUNCTION', 
    'cert-management-dev-secure-server-cert-scanner'
)
```

**Invocation:**
```python
response = lambda_client.invoke(
    FunctionName=scanner_function_name,
    InvocationType='RequestResponse',  # Synchronous!
    Payload=json.dumps({})
)
```

#### 3. Server Scanner Lambda

**Function:** `cert-management-dev-secure-server-cert-scanner`  
**File:** `lambda/server_certificate_scanner.py`  

**Process:**
1. Query EC2 instances with tag `CertificateScanning=enabled`
2. Filter by platform (Windows/Linux)
3. Execute SSM documents:
   - Windows: `cert-management-dev-secure-windows-cert-scan`
   - Linux: `cert-management-dev-secure-linux-cert-scan`
4. Parse certificate data from SSM output
5. Store in DynamoDB (duplicate prevention via ServerID + Thumbprint)
6. Return summary statistics

**SSM Commands:**
- **Windows:** `certutil -store My` (Personal certificate store)
- **Linux:** `openssl x509` (PEM files in /etc/ssl/certs, /etc/pki/tls)

#### 4. IAM Permissions

**Lambda Invoke Policy:**
```hcl
{
  "Effect": "Allow",
  "Action": "lambda:InvokeFunction",
  "Resource": [
    "arn:aws:lambda:${region}:${account}:function:${name}-acm-sync",
    "arn:aws:lambda:${region}:${account}:function:${name}-server-cert-scanner"
  ]
}
```

**Location:** `terraform/modules/iam/main.tf`

---

## How It Works

### Step-by-Step Execution

1. **User clicks "Sync from Servers" button**
   - Button disabled, text changes to "Scanning..."
   - Modal opens with progress indicator

2. **JavaScript makes API call**
   ```javascript
   const response = await fetch(`${API_BASE_URL}/sync-server-certs`, {
       method: 'POST',
       headers: await getAuthHeaders()  // Includes Cognito JWT
   });
   ```

3. **API Gateway validates token**
   - Cognito authorizer checks JWT
   - If invalid → 401 Unauthorized
   - If valid → Forward to Lambda

4. **Dashboard API invokes scanner**
   ```python
   response = lambda_client.invoke(
       FunctionName='cert-management-dev-secure-server-cert-scanner',
       InvocationType='RequestResponse',  # Wait for results
       Payload=json.dumps({})
   )
   ```

5. **Server scanner executes**
   - Finds EC2 instances with `CertificateScanning=enabled` tag
   - Splits by platform (Windows/Linux)
   - Runs SSM commands on each instance
   - Waits for all SSM commands to complete (30-60 seconds)

6. **Certificate data processed**
   - Parse thumbprint, common name, expiry, issuer
   - Check DynamoDB for duplicates (ServerID + Thumbprint)
   - Insert new certificates or update metadata
   - Preserve manual fields (Owner, SupportEmail, Priority)

7. **Results returned**
   - Scanner returns JSON: `{serversScanned, certificatesFound, certificatesAdded, errors, windowsServers, linuxServers}`
   - Dashboard API forwards to API Gateway
   - API Gateway returns to browser

8. **Modal updated**
   - Progress hidden
   - Results displayed in grid
   - "Refresh Dashboard" button enabled
   - Original button re-enabled

### Synchronous vs Asynchronous

**Why Synchronous?**
- Users want immediate feedback
- Scan typically completes in 30-60 seconds
- Real-time results more valuable than background job

**Implementation:**
```python
# Synchronous (current)
InvocationType='RequestResponse'  # Waits for completion

# Asynchronous (alternative)
InvocationType='Event'  # Fire-and-forget
```

### Duplicate Prevention

**Composite Key:** `ServerID` + `Thumbprint`

```python
# Check if certificate already exists
existing_cert = table.get_item(
    Key={
        'CertificateId': f"{server_id}_{thumbprint}"
    }
)

if existing_cert:
    # Update only automated fields
    # Preserve: Owner, SupportEmail, Priority, Notes
else:
    # Insert new certificate
```

---

## Deployment

### Prerequisites

1. **Server scanning enabled**
   ```hcl
   # terraform/environments/dev-secure/terraform.tfvars
   enable_server_certificate_scan = true
   ```

2. **EC2 instances tagged**
   ```
   Tag: CertificateScanning = enabled
   ```

3. **SSM Agent installed** on all target EC2 instances

4. **IAM role attached** to EC2 instances with SSM permissions

### Terraform Deployment

The feature is fully modular and deployed via Terraform:

#### Step 1: Environment Configuration

**File:** `terraform/environments/dev-secure/main.tf`

```hcl
module "lambda_secure" {
  source = "../../modules/lambda_secure"
  
  # ... other variables ...
  
  # Pass server scanner function name
  server_scanner_function_name = var.enable_server_certificate_scan ? 
    module.server_certificate_scanner[0].lambda_function_name : ""
}
```

**Variable passed:** `server_scanner_function_name`  
**Conditional:** Only if server scanning is enabled

#### Step 2: Lambda Module Variables

**File:** `terraform/modules/lambda_secure/variables.tf`

```hcl
variable "server_scanner_function_name" {
  description = "Name of the server certificate scanner Lambda function"
  type        = string
  default     = ""
}
```

#### Step 3: Lambda Environment Variable

**File:** `terraform/modules/lambda_secure/main.tf`

```hcl
resource "aws_lambda_function" "dashboard_api" {
  # ... other config ...
  
  environment {
    variables = {
      CERTIFICATES_TABLE    = var.certificates_table_name
      LOGS_TABLE           = var.logs_table_name
      SERVER_SCANNER_FUNCTION = var.server_scanner_function_name  # New!
    }
  }
}
```

#### Step 4: API Gateway Resources

**File:** `terraform/modules/api_gateway/main.tf`

7 new resources created:
1. `aws_api_gateway_resource.sync_server_certs` - Resource path
2. `aws_api_gateway_method.post_sync_server_certs` - POST method
3. `aws_api_gateway_integration.post_sync_server_certs` - Lambda integration
4. `aws_api_gateway_method.options_sync_server_certs` - OPTIONS method
5. `aws_api_gateway_integration.options_sync_server_certs` - MOCK integration
6. `aws_api_gateway_method_response.options_sync_server_certs_200` - CORS response
7. `aws_api_gateway_integration_response.options_sync_server_certs_200` - CORS headers

#### Step 5: Deployment Triggers

**File:** `terraform/modules/api_gateway/main.tf`

```hcl
resource "aws_api_gateway_deployment" "main" {
  triggers = {
    redeployment = sha1(jsonencode([
      # ... existing resources ...
      aws_api_gateway_resource.sync_server_certs.id,
      aws_api_gateway_method.post_sync_server_certs.id,
      aws_api_gateway_integration.post_sync_server_certs.id,
    ]))
  }
}
```

**Important:** This ensures new API Gateway deployment is created when endpoint changes

#### Step 6: IAM Permissions

**File:** `terraform/modules/iam/main.tf`

```hcl
{
  "Effect": "Allow",
  "Action": "lambda:InvokeFunction",
  "Resource": [
    "arn:aws:lambda:${var.aws_region}:${var.aws_account_id}:function:${local.common_name}-acm-sync",
    "arn:aws:lambda:${var.aws_region}:${var.aws_account_id}:function:${local.common_name}-server-cert-scanner"
  ]
}
```

### Deploy Commands

```bash
cd terraform/environments/dev-secure

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Apply changes
terraform apply -auto-approve
```

### Deployment Output

```
Apply complete! Resources: 7 added, 16 changed, 0 destroyed.

Resources added:
- aws_api_gateway_resource.sync_server_certs
- aws_api_gateway_method.post_sync_server_certs
- aws_api_gateway_method.options_sync_server_certs
- aws_api_gateway_integration.post_sync_server_certs
- aws_api_gateway_integration.options_sync_server_certs
- aws_api_gateway_method_response.options_sync_server_certs_200
- aws_api_gateway_integration_response.options_sync_server_certs_200
```

### Frontend Deployment

Dashboard files are automatically deployed to S3 via Terraform module:

**File:** `terraform/modules/dashboard_secure/main.tf`

```hcl
resource "aws_s3_object" "index_html" {
  bucket       = var.dashboard_bucket_name
  key          = "index.html"
  source       = "${path.module}/../../../dashboard/index.html"
  content_type = "text/html"
}

resource "aws_s3_object" "dashboard_js" {
  bucket       = var.dashboard_bucket_name
  key          = "dashboard.js"
  source       = "${path.module}/../../../dashboard/dashboard.js"
  content_type = "application/javascript"
}
```

**Cache Invalidation:**
CloudFront cache is automatically invalidated on file changes.

---

## Usage

### For End Users

1. **Login to dashboard**
   - URL: https://d3bqyfjow8topp.cloudfront.net
   - Use Cognito credentials

2. **Click "Sync from Servers" button**
   - Green button next to "Sync from ACM"
   - Icon: Server symbol

3. **Wait for scan to complete**
   - Modal shows "Scanning Servers..." with spinner
   - Typical duration: 30-60 seconds
   - Depends on number of servers

4. **Review results**
   - Servers Scanned: Total EC2 instances checked
   - Certificates Found: All certs discovered
   - New Certificates: Newly added to database
   - Errors: Failed scans (if any)
   - Windows Servers: Count of Windows instances
   - Linux Servers: Count of Linux instances

5. **Refresh dashboard**
   - Click "Refresh Dashboard" button in modal
   - New certificates appear in main table
   - Apply filters as needed

### For Administrators

#### Enable Server Scanning

**Tag EC2 instances:**
```bash
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=CertificateScanning,Value=enabled
```

#### Monitor Execution

**CloudWatch Logs:**
- Dashboard API: `/aws/lambda/cert-management-dev-secure-dashboard-api`
- Server Scanner: `/aws/lambda/cert-management-dev-secure-server-cert-scanner`

**Filter pattern for server sync:**
```
{ $.event = "server_cert_sync" }
```

#### Test API Directly

```bash
# Get Cognito JWT token
TOKEN=$(aws cognito-idp initiate-auth ...)

# Call endpoint
curl -X POST \
  https://8clm33qmf9.execute-api.eu-west-1.amazonaws.com/dev-secure/sync-server-certs \
  -H "Authorization: $TOKEN"
```

---

## API Reference

### POST /sync-server-certs

Trigger manual server certificate synchronization.

**Endpoint:** `POST /dev-secure/sync-server-certs`

**Authentication:** Cognito JWT token (required)

**Headers:**
```
Authorization: <JWT_TOKEN>
Content-Type: application/json
```

**Request Body:** None (empty payload)

**Response (Success - 200):**
```json
{
  "statusCode": 200,
  "body": {
    "message": "Server certificate sync completed",
    "serversScanned": 10,
    "certificatesFound": 14,
    "certificatesAdded": 7,
    "windowsServers": 3,
    "linuxServers": 7,
    "errors": []
  }
}
```

**Response (Error - 500):**
```json
{
  "statusCode": 500,
  "body": {
    "error": "Failed to invoke server scanner Lambda",
    "details": "Error message here"
  }
}
```

**Response Codes:**
- `200` - Success
- `401` - Unauthorized (invalid/missing JWT)
- `403` - Forbidden (insufficient permissions)
- `500` - Internal server error

### OPTIONS /sync-server-certs

CORS preflight request.

**Endpoint:** `OPTIONS /dev-secure/sync-server-certs`

**Authentication:** None required

**Response (200):**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST,OPTIONS
Access-Control-Allow-Headers: Content-Type,Authorization,...
```

---

## Troubleshooting

### Button Not Visible

**Symptom:** "Sync from Servers" button doesn't appear

**Solutions:**
1. **Hard refresh browser:** Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. **Clear browser cache:** Settings → Privacy → Clear browsing data
3. **Check CloudFront:** Verify `index.html` version in S3
4. **Wait for propagation:** CloudFront cache invalidation takes 2-5 minutes

### "Failed to Fetch" Error

**Symptom:** Modal shows "Scan Failed - Failed to fetch"

**Causes:**
1. API Gateway endpoint not deployed
2. CORS configuration missing
3. Network connectivity issues

**Solutions:**
1. **Verify endpoint exists:**
   ```bash
   curl -X OPTIONS \
     https://8clm33qmf9.execute-api.eu-west-1.amazonaws.com/dev-secure/sync-server-certs
   ```
   Should return 200 with CORS headers

2. **Check Terraform deployment:**
   ```bash
   terraform state list | grep sync_server_certs
   ```
   Should show 7 resources

3. **Verify API Gateway deployment:**
   ```bash
   aws apigateway get-deployments \
     --rest-api-id 8clm33qmf9 \
     --region eu-west-1
   ```
   Check recent deployment timestamp

### Scan Returns No Results

**Symptom:** Modal shows 0 servers scanned

**Causes:**
1. No EC2 instances tagged with `CertificateScanning=enabled`
2. SSM Agent not running on instances
3. IAM role missing SSM permissions

**Solutions:**
1. **Check EC2 tags:**
   ```bash
   aws ec2 describe-instances \
     --filters "Name=tag:CertificateScanning,Values=enabled" \
     --query 'Reservations[].Instances[].InstanceId'
   ```

2. **Verify SSM connectivity:**
   ```bash
   aws ssm describe-instance-information \
     --filters "Key=tag:CertificateScanning,Values=enabled"
   ```

3. **Check instance IAM role:**
   - Required policy: `AmazonSSMManagedInstanceCore`

### Authentication Errors

**Symptom:** 401 Unauthorized or 403 Forbidden

**Causes:**
1. JWT token expired
2. User not in correct Cognito group
3. API Gateway authorizer misconfigured

**Solutions:**
1. **Logout and login again** - Refreshes JWT token
2. **Verify user group:**
   ```bash
   aws cognito-idp admin-list-groups-for-user \
     --user-pool-id eu-west-1_cWIxi5SPd \
     --username user@example.com
   ```
   User should be in `Admins` or `Operators` group

3. **Check authorizer configuration:**
   - API Gateway → Authorizers → Cognito User Pool
   - Token Source: `Authorization` header

### Long Scan Times

**Symptom:** Scan takes >2 minutes

**Causes:**
1. Many servers being scanned
2. Network latency to SSM
3. Timeout in Lambda

**Solutions:**
1. **Increase Lambda timeout:**
   ```hcl
   # terraform/modules/lambda_server_scanner/main.tf
   timeout = 300  # 5 minutes
   ```

2. **Batch servers differently** - Process in smaller groups

3. **Monitor CloudWatch Logs** - Check for slow SSM executions

### No Certificates Found

**Symptom:** Servers scanned but 0 certificates found

**Causes:**
1. No certificates installed on servers
2. Certificates in non-standard locations
3. SSM document execution failed

**Solutions:**
1. **Manually verify certificates exist:**
   - Windows: `certutil -store My`
   - Linux: `ls /etc/ssl/certs/*.crt`

2. **Check SSM document execution:**
   ```bash
   aws ssm list-command-invocations \
     --command-id <command-id> \
     --details
   ```

3. **Review CloudWatch Logs** - Check parsing logic

### DynamoDB Errors

**Symptom:** Certificates scanned but not appearing in dashboard

**Causes:**
1. DynamoDB permissions missing
2. Table name mismatch
3. Duplicate key violations

**Solutions:**
1. **Verify Lambda permissions:**
   ```bash
   aws lambda get-function \
     --function-name cert-management-dev-secure-server-cert-scanner \
     --query 'Configuration.Role'
   ```
   Check role has DynamoDB:PutItem permission

2. **Check table name in environment:**
   ```bash
   aws lambda get-function-configuration \
     --function-name cert-management-dev-secure-server-cert-scanner \
     --query 'Environment.Variables.CERTIFICATES_TABLE'
   ```

3. **Review DynamoDB errors in CloudWatch Logs**

---

## Best Practices

### Operational

1. **Schedule regular automated scans** - Don't rely solely on manual sync
2. **Tag servers consistently** - Use `CertificateScanning=enabled` tag
3. **Monitor scan results** - Review errors and investigate failures
4. **Keep SSM Agent updated** - Ensure latest version on all instances
5. **Test in dev/staging first** - Validate before production deployment

### Security

1. **Limit Cognito groups** - Only Admins and Operators should trigger scans
2. **Use least privilege IAM** - Grant only required permissions
3. **Enable CloudWatch Logs** - Maintain audit trail
4. **Rotate credentials** - Follow AWS best practices
5. **Review CORS settings** - Restrict origins in production

### Performance

1. **Tag selectively** - Only scan servers that host certificates
2. **Increase Lambda memory** - Faster execution for large fleets
3. **Use Regional endpoints** - Reduce latency
4. **Monitor costs** - SSM commands and Lambda invocations count
5. **Optimize SSM documents** - Reduce command execution time

---

## Future Enhancements

### Planned Features

1. **Progress percentage** - Show scan progress in real-time
2. **Individual server status** - Display which servers are being scanned
3. **Scan history** - Log all manual sync operations
4. **Scheduled scans from UI** - Configure recurring scans
5. **Export scan results** - Download as CSV/Excel
6. **Selective scanning** - Choose specific servers or environments
7. **Webhook notifications** - Alert on scan completion
8. **Detailed error reporting** - Better troubleshooting information

### Integration Opportunities

1. **Slack notifications** - Post scan results to channel
2. **Teams integration** - Similar to Slack
3. **PagerDuty** - Alert on scan failures
4. **Datadog/NewRelic** - Send metrics for monitoring
5. **JIRA** - Create tickets for expired certificates found

---

## Support

### Documentation

- **Main README:** `README.md`
- **Deployment Guide:** `DEPLOYMENT_SUMMARY.md`
- **Quick Reference:** `QUICK_REFERENCE.md`
- **This Document:** `SERVER_SYNC_FEATURE.md`

### Logs

- **Dashboard API:** `/aws/lambda/cert-management-dev-secure-dashboard-api`
- **Server Scanner:** `/aws/lambda/cert-management-dev-secure-server-cert-scanner`
- **API Gateway:** `/aws/apigateway/cert-management-dev-secure-api`

### Contact

For issues or questions:
- **Email:** vinaya-c.nayanegali@capgemini.com
- **Repository:** https://github.com/vinaya-cg/certificate-monitor
- **Branch:** `feature/server-sync-button`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-10 | Initial release of server sync button feature |

---

**End of Document**
