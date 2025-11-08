# Certificate Management Dashboard

## 📋 Table of Contents
- [Overview](#overview)
- [Latest Updates](#latest-updates)
- [Architecture](#architecture)
- [AWS Services & Resources](#aws-services--resources)
- [Deployment Details](#deployment-details)
- [CORS Configuration & Fixes](#cors-configuration--fixes)
- [Code Structure & Logic](#code-structure--logic)
- [Manual Import Process](#manual-import-process)
- [Configuration Guide](#configuration-guide)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

A complete AWS-based certificate monitoring and management system with automated expiry notifications, bulk import capabilities, and a real-time web dashboard.

### Key Features
- ✅ **Automated Certificate Monitoring**: Daily Lambda scans for expiring certificates
- ✅ **Email Notifications**: SES-based alerts for certificates expiring within 30 days  
- ✅ **Web Dashboard**: Real-time certificate viewing with filtering and search
- ✅ **Column Sorting**: Click any column header to sort ascending/descending 🆕
- ✅ **Add/Update Certificates**: Web-based interface to add and update certificates directly
- ✅ **Renewal Workflow**: One-click renewal process with status tracking 🆕
- ✅ **Smart Status Validation**: Auto-corrects expired certificates showing as active 🆕
- ✅ **Bulk Import**: Python script for importing certificates from Excel files
- ✅ **Complete Audit Trail**: All changes logged in DynamoDB
- ✅ **Infrastructure as Code**: 100% Terraform-managed AWS infrastructure
- ✅ **REST API**: Full CRUD operations via Lambda Function URL (GET, POST, PUT)

### System Status
- **Environment**: Development (`dev`)
- **Region**: `eu-west-1` (Ireland)
- **Deployment Method**: Terraform + AWS CLI
- **Certificates Imported**: 191 PostNL certificates
- **Dashboard Version**: `20251029-1630`
- **Status**: Production-ready

---

## 🆕 Latest Updates

### October 29, 2025 - UI/UX Enhancements

#### 1. **Improved Button Visibility**
- ✅ Added text labels to all action buttons (Edit, Status, Upload, Renew, Logs)
- ✅ Better spacing and alignment with icons
- ✅ Mobile-responsive button layout

#### 2. **Optimized Table Layout**
- ✅ Removed horizontal scroll - all data fits on one page
- ✅ Hidden Owner column (still available in edit form)
- ✅ Optimized column widths for better readability
- ✅ Added environment badge styling

#### 3. **Column Sorting Feature**
- ✅ Click any column header to sort data
- ✅ Visual indicators (↑↓) show sort direction
- ✅ Supports sorting by:
  - Certificate Name (alphabetical)
  - Environment (alphabetical)
  - Application (alphabetical)
  - Status (alphabetical)
  - Expiry Date (chronological)
  - Days Left (numerical)

#### 4. **Renewal Button Added**
- ✅ New "Renew" button for quick renewal initiation
- ✅ Confirmation dialog before status update
- ✅ Auto-updates status to "Renewal in Progress"
- ✅ Integrated with audit logging

#### 5. **Status Validation Fix** 🐛
- ✅ **Critical Fix**: Expired certificates now display correctly
- ✅ Client-side status recalculation based on expiry date
- ✅ Overrides stale database status while preserving manual statuses
- ✅ Statistics cards show accurate counts
- **Logic**:
  - Days < 0 → Expired (red)
  - Days 0-30 → Due for Renewal (yellow)
  - Days > 30 → Active (green)
  - Manual statuses preserved (Renewal in Progress, Renewal Done)

### Action Buttons Overview
| Button | Icon | Color | Function |
|--------|------|-------|----------|
| **Edit** | ✏️ | Blue | Edit certificate details |
| **Status** | ☑️ | Green | Update certificate status |
| **Upload** | ⬆️ | Yellow | Upload renewed certificate file |
| **Renew** | 🔄 | Info Blue | Start renewal process (new status) |
| **Logs** | 📜 | Gray | View certificate history |

---

## 🏗️ Architecture

### High-Level Architecture
```
┌──────────────┐         ┌─────────────┐         ┌──────────────┐
│   Browser    │────────▶│  S3 Website │────────▶│ Lambda URL   │
│  (Dashboard) │         │   Hosting   │         │ (Dashboard   │
└──────────────┘         └─────────────┘         │     API)     │
                                                  └──────┬───────┘
                                                         │
                         ┌───────────────────────────────┼─────────────┐
                         │                               │             │
                         ▼                               ▼             ▼
                  ┌─────────────┐              ┌─────────────┐  ┌──────────┐
                  │  DynamoDB   │              │     SES     │  │CloudWatch│
                  │ Certificates│              │   Emails    │  │   Logs   │
                  │    Logs     │              └─────────────┘  └──────────┘
                  └─────────────┘
                         ▲
                         │
                  ┌──────┴──────┐
                  │             │
           ┌──────▼──────┐ ┌───▼─────────┐
           │ Certificate │ │   Python    │
           │   Monitor   │ │   Import    │
           │   Lambda    │ │   Script    │
           └─────────────┘ └─────────────┘
                ▲                 ▲
                │                 │
         ┌──────┴─────┐    ┌─────┴──────┐
         │ EventBridge│    │   Manual   │
         │  (Daily)   │    │  Execution │
         └────────────┘    └────────────┘
```

### Data Flow
1. **Dashboard Access**: Browser → S3 Static Website → Lambda Function URL API → DynamoDB
2. **Certificate Import**: Python Script → DynamoDB (bulk write)
3. **Daily Monitoring**: EventBridge → Lambda → DynamoDB → SES Email
4. **Logging**: All operations → DynamoDB Logs Table

---

## 🔧 AWS Services & Resources

### Complete Resource Inventory (28 Resources Deployed)

#### 1. **S3 Buckets** (3 buckets)

**Dashboard Bucket** (`cert-management-dev-dashboard-a3px89bh`)
- **Purpose**: Static website hosting for dashboard UI
- **Configuration**:
  ```json
  {
    "WebsiteConfiguration": {
      "IndexDocument": "index.html",
      "ErrorDocument": "error.html"
    },
    "PublicAccessBlock": {
      "BlockPublicAcls": false,
      "BlockPublicPolicy": false
    },
    "BucketPolicy": {
      "Principal": "*",
      "Action": "s3:GetObject"
    }
  }
  ```
- **CORS Configuration** (Added via AWS CLI):
  ```json
  {
    "CORSRules": [{
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedOrigins": ["*"],
      "MaxAgeSeconds": 3600
    }]
  }
  ```
- **Access URL**: `http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/`

**Uploads Bucket** + **Logs Bucket**:
- Versioning: Enabled
- Encryption: AES-256

#### 2. **DynamoDB Tables** (2 tables with 6 GSIs)

**Certificates Table** (`cert-management-dev-certificates`)
- Capacity: Pay-per-request (on-demand)
- Primary Key: `CertificateID` (MD5 hash of common_name)
- Records: 191 PostNL certificates
- GSIs: StatusIndex, EnvironmentIndex, OwnerIndex, ExpiryIndex
- Point-in-Time Recovery: Enabled

**Certificate Logs Table** (`cert-management-dev-certificate-logs`)
- Tracks all import, update, and email operations
- GSIs: CertificateLogsIndex, ActionIndex

#### 3. **Lambda Functions** (3 functions)

**Dashboard API** (`cert-management-dev-dashboard-api`)
- Runtime: Python 3.9 | Memory: 512 MB | Timeout: 60s
- **Function URL**: `https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url.eu-west-1.on.aws/`
- **Auth**: NONE (public access)
- **Supported Methods**: GET, POST, PUT ✨ NEW
- **CORS** (Configured in Terraform + AWS CLI):
  ```hcl
  cors {
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "PUT", "OPTIONS"]
    allow_headers     = ["date", "keep-alive", "content-type"]
    max_age          = 86400
  }
  ```
- **Endpoints**:
  - **GET**: Fetch all certificates from DynamoDB
  - **POST**: Add new certificate with validation ✨ NEW
  - **PUT**: Update existing certificate ✨ NEW
- **Code Logic**: 
  - Scans DynamoDB
  - Converts Decimal→float
  - Auto-calculates certificate status (Active/Due for Renewal/Expired)
  - Auto-calculates days until expiry
  - Field validation (required fields, email format)
  - Audit logging to certificate-logs table
  - Returns JSON
- **Critical Fix**: NO CORS headers in Lambda code (Function URL handles it)

**Certificate Monitor** (`cert-management-dev-certificate-monitor`)
- Trigger: EventBridge daily at 08:00 UTC
- Purpose: Scan for expiring certificates, send SES emails

**Excel Processor** (`cert-management-dev-excel-processor`)
- Status: ⚠️ Configured but needs openpyxl Lambda layer
- Workaround: Use `import_certificates.py` script

#### 4. **IAM Roles & Policies**

**Lambda Execution Role** (`cert-management-dev-lambda-role`)
- Permissions:
  - DynamoDB: GetItem, PutItem, Scan, Query, BatchWriteItem
  - S3: GetObject, PutObject (uploads/logs buckets)
  - SES: SendEmail, SendRawEmail
  - CloudWatch Logs: CreateLogGroup, PutLogEvents

#### 5. **SES (Simple Email Service)**

- **Verified Email**: `vinaya-c.nayanegali@capgemini.com`
- **Verification Command**:
  ```bash
  aws ses verify-email-identity \
    --email-address vinaya-c.nayanegali@capgemini.com \
    --region eu-west-1
  ```
- **Status**: Sandbox mode (verify recipients or request production access)

#### 6. **EventBridge**

- **Rule**: `cert-management-dev-daily-monitor`
- **Schedule**: `cron(0 8 * * ? *)` (Daily 08:00 UTC)
- **Target**: Certificate Monitor Lambda

#### 7. **CloudWatch**

- **Log Groups**: 3 (retention: 30 days)
- **Dashboard**: `cert-management-dev-dashboard`

---

## 🚀 Deployment Details

### Terraform Deployment

**Command**:
```bash
cd terraform/
terraform init
terraform plan   # Review 28 resources
terraform apply  # Deploy infrastructure
```

**Resources Created**: S3 buckets (3), DynamoDB tables (2), Lambda functions (3), IAM roles, SES, EventBridge, CloudWatch

### Manual AWS CLI Configurations

**1. Lambda Function URL with CORS** (Fixed duplicate header issue)
```bash
# Delete old URL
aws lambda delete-function-url-config \
  --function-name cert-management-dev-dashboard-api \
  --region eu-west-1

# Create new with full CORS
aws lambda create-function-url-config \
  --function-name cert-management-dev-dashboard-api \
  --auth-type NONE \
  --cors '{
    "AllowOrigins": ["*"],
    "AllowMethods": ["GET","POST","OPTIONS"],
    "AllowHeaders": ["date","keep-alive","content-type"],
    "MaxAge": 86400
  }' \
  --region eu-west-1
```

**2. S3 CORS Configuration**
```bash
aws s3api put-bucket-cors \
  --bucket cert-management-dev-dashboard-a3px89bh \
  --cors-configuration file://s3-cors.json \
  --region eu-west-1
```

**3. Dashboard Files Upload**
```bash
aws s3 cp dashboard/index.html s3://cert-management-dev-dashboard-a3px89bh/
aws s3 cp dashboard/dashboard.js s3://cert-management-dev-dashboard-a3px89bh/ \
  --cache-control "no-cache"
```

**4. Lambda Function Updates** (After fixing duplicate CORS headers)
```bash
cd lambda/
zip dashboard_api.zip dashboard_api.py
aws lambda update-function-code \
  --function-name cert-management-dev-dashboard-api \
  --zip-file fileb://dashboard_api.zip \
  --region eu-west-1
```

---

## 🔒 CORS Configuration & Fixes

### The CORS Problem Journey

**Problem 1: JavaScript Crash**
- **Cause**: `dashboard.js` accessed null DOM elements (`uploadArea`, `fileInput`)
- **Fix**: Added defensive null checks before addEventListener

**Problem 2: CORS Blocking**
- **Symptom**: "Failed to fetch" error in browser (PowerShell/curl worked)
- **Root Cause**: **Duplicate `Access-Control-Allow-Origin` headers**
  - Lambda Function URL added: `*`
  - Lambda code also added: `*`
  - Browser rejected response with duplicate headers
  
**Error Message**:
```
The 'Access-Control-Allow-Origin' header contains multiple values 
'*, http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com', 
but only one is allowed.
```

**Final Fix**:
```python
# BEFORE (❌ Duplicate CORS headers)
return {
    'statusCode': 200,
    'headers': {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  # ❌ DUPLICATE
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    },
    'body': json.dumps(data)
}

# AFTER (✅ Single CORS header from Function URL)
return {
    'statusCode': 200,
    'headers': {
        'Content-Type': 'application/json'  # Only content-type
    },
    'body': json.dumps(data)
}
```

### CORS Architecture

```
Browser Request
    ↓
Lambda Function URL (AWS Managed)
    ├─ Checks Terraform CORS config
    ├─ Adds CORS headers automatically:
    │    Access-Control-Allow-Origin: *
    │    Access-Control-Allow-Methods: GET,POST,OPTIONS
    ↓
Lambda Code Execution
    ├─ Returns ONLY Content-Type header
    ↓
Lambda Function URL merges headers
    ↓
Browser receives SINGLE set of CORS headers ✅
```

### Best Practices

**✅ DO**:
- Use Lambda Function URL CORS (Terraform config)
- Let AWS manage CORS headers automatically
- Only return app-specific headers from Lambda

**❌ DON'T**:
- Add CORS headers in Lambda code when using Function URL
- Use `no-cors` fetch mode (prevents reading response)
- Test only with curl/PowerShell (they don't enforce CORS)

---

## 📂 Code Structure & Logic

```
cert-dashboard/
├── terraform/                   # Infrastructure as Code
│   ├── main.tf                 # Core resources (S3, DynamoDB, IAM)
│   ├── dashboard_api.tf        # Dashboard API Lambda + URL
│   ├── variables.tf
│   └── outputs.tf
├── lambda/                      # Lambda function code
│   ├── dashboard_api.py        # REST API (CORS fixed)
│   ├── certificate_monitor.py  # Daily monitoring + emails
│   └── excel_processor.py      # S3-triggered (needs layer)
├── dashboard/                   # Web UI
│   ├── index.html
│   ├── dashboard.js            # Frontend (null checks added)
│   └── styles.css
├── import_certificates.py       # Manual import script ✅
└── README.md
```

### Key Code Logic

**1. dashboard_api.py** ✨ UPDATED
```python
def lambda_handler(event, context):
    """
    Supports GET, POST, PUT methods
    """
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    
    if http_method == 'POST':
        return handle_add_certificate(event, table, logs_table)
    elif http_method == 'PUT':
        return handle_update_certificate(event, table, logs_table)
    else:
        return handle_get_certificates(table)

def handle_get_certificates(table):
    # Scan DynamoDB certificates table
    # Convert Decimal → float (JSON compatibility)
    # Convert datetime → ISO 8601 string
    # Return JSON: {"certificates": [...], "count": 191}

def handle_add_certificate(event, table, logs_table):
    # Parse request body
    # Validate required fields (CertificateName, Environment, Application, ExpiryDate, OwnerEmail)
    # Generate unique CertificateID (UUID)
    # Calculate status based on expiry date
    # Calculate days until expiry
    # Add certificate to DynamoDB
    # Log action to certificate-logs table
    # Return success/error response

def handle_update_certificate(event, table, logs_table):
    # Parse request body
    # Validate CertificateID exists
    # Recalculate status if expiry date changed
    # Update certificate in DynamoDB
    # Log action to certificate-logs table
    # Return success/error response

def calculate_status(expiry_date):
    # Active: > 30 days until expiry
    # Due for Renewal: 1-30 days until expiry
    # Expired: past expiry date
    
def calculate_days_until_expiry(expiry_date):
    # Calculate days from today to expiry
    # Return positive (future) or negative (past)
```

**2. certificate_monitor.py**
```python
# Triggered daily by EventBridge
# Scan all certificates
# Calculate days until expiry
# Filter certificates expiring within 30 days
# Send SES email notifications (grouped by environment)
# Log all actions to DynamoDB logs table
```

**3. import_certificates.py** (Manual script - works!)
```python
# Load Excel file using openpyxl
# Find header row (flexible column names)
# Parse dates (DD/MM/YYYY, YYYY-MM-DD, Excel numeric)
# Calculate status (Active/Expiring Soon/Expired)
# Generate CertificateID (MD5 of common_name)
# Batch write to DynamoDB (25 items per batch)
# Progress: "Batch 1: Imported 25 certificates..."
```

**4. dashboard.js** ✨ UPDATED
```javascript
// API Configuration
const API_URL = 'https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url.eu-west-1.on.aws/';

// Fetch certificates from Lambda Function URL (GET)
async function fetchCertificatesFromAPI() {
    const response = await fetch(API_URL, { method: 'GET' });
    const data = await response.json();
    return data.certificates;
}

// Add new certificate (POST)
async function addNewCertificate(certData) {
    // Calculate status and days until expiry
    const status = calculateStatus(certData.ExpiryDate);
    const daysLeft = calculateDaysLeft(certData.ExpiryDate);
    
    const newCert = {
        ...certData,
        CertificateID: generateUUID(),
        Status: status,
        DaysUntilExpiry: daysLeft.toString(),
        CreatedOn: new Date().toISOString(),
        ImportedFrom: 'Dashboard'
    };
    
    // POST to API
    const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newCert)
    });
    
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    return result;
}

// Update existing certificate (PUT)
async function updateCertificate(certId, certData) {
    const updateData = {
        CertificateID: certId,
        ...certData,
        LastUpdatedOn: new Date().toISOString()
    };
    
    // PUT to API
    const response = await fetch(API_URL, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
    });
    
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    return result;
}

// Defensive DOM element checks (prevent null errors)
const uploadArea = document.getElementById('uploadArea');
if (uploadArea && fileInput) {
    uploadArea.addEventListener('click', () => fileInput.click());
} else {
    console.log('Upload elements not found, skipping');
}

// Render table, calculate statistics
// Filter by status, environment, search term
```

**Critical Fixes Applied**:
- ✅ Defined `API_URL` as constant at top of file
- ✅ Changed all `CONFIG.apiUrl` references to `API_URL`
- ✅ Added POST/PUT request handlers
- ✅ Enhanced error messages with detailed logging
- ✅ Fixed "CONFIG is not defined" error

---

## 📥 Manual Import Process

### Why Manual Import?

- Excel processor Lambda missing openpyxl library
- Lambda layer not created in Terraform
- **Workaround**: Standalone Python script works perfectly ✅

### Execution

**Prerequisites**:
```bash
pip install boto3 openpyxl
aws configure  # Set credentials, region eu-west-1
```

**Run Import**:
```bash
python import_certificates.py --file PostNL_Certificates.xlsx
```

**Results**:
```
✅ Successfully imported 191 certificates
   - 8 batches (25 items each, except last batch: 16)
   - 100% success rate (0 failures)
   - ~5 seconds total time
```

**Validation**:
```bash
# Verify count
aws dynamodb scan --table-name cert-management-dev-certificates --select "COUNT"
# Output: {"Count": 191}

# Sample record
aws dynamodb get-item --table-name cert-management-dev-certificates \
  --key '{"CertificateID": {"S": "..."}}' | jq '.Item.CommonName.S'
# Output: "adfs-aws2.p02.cldsvc.net"
```

### Features

- **Flexible column mapping**: Handles different Excel formats, case-insensitive
- **Multiple date formats**: DD/MM/YYYY, YYYY-MM-DD, Excel numeric
- **Auto status**: Calculates Active/Expiring Soon/Expired based on expiry date
- **Batch writes**: 25 items per API call (DynamoDB limit)
- **Error handling**: Skips bad rows, continues processing, reports summary

---

## ➕ Add/Update Certificates via Dashboard ✨ NEW

### Web-Based Certificate Management

The dashboard now supports **adding and updating certificates** directly through the web interface with full DynamoDB persistence!

### Add New Certificate

**Method**: Click "Add Certificate" button on dashboard

**Required Fields**:
- Certificate Name (e.g., `api.example.com`)
- Environment (Production, Staging, Development, Test)
- Application (e.g., `API Gateway`)
- Expiry Date (YYYY-MM-DD format)
- Owner Email (must be valid email format)

**Optional Fields**:
- Certificate Type (SSL/TLS, Code Signing, etc.)
- Support Email
- Account Number
- Serial Number

**Automatic Calculations**:
- **Status**: Automatically determined based on expiry date
  - `Active`: > 30 days until expiry
  - `Due for Renewal`: 1-30 days until expiry
  - `Expired`: Past expiry date
- **Days Until Expiry**: Calculated from current date
- **Certificate ID**: Auto-generated UUID
- **Timestamps**: CreatedOn and LastUpdatedOn

**Example**:
```
Certificate Name: prod-api.example.com
Environment: Production
Application: Main API
Expiry Date: 2026-03-15
Type: SSL/TLS
Owner Email: admin@example.com

→ Status: Active (automatically calculated)
→ Days Until Expiry: 137 (automatically calculated)
→ Certificate ID: cert-a1b2c3d4... (auto-generated)
```

### Update Existing Certificate

**Method**: Click "Edit" icon next to certificate in table

**Editable Fields**: All certificate fields can be updated

**Auto-Recalculation**: Status and days until expiry recalculated if expiry date changes

### API Endpoints

**Add Certificate** (POST)
```bash
curl -X POST https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url.eu-west-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{
    "CertificateName": "test.example.com",
    "Environment": "Test",
    "Application": "Test App",
    "ExpiryDate": "2026-06-15",
    "Type": "SSL/TLS",
    "OwnerEmail": "test@example.com",
    "SupportEmail": "support@example.com"
  }'
```

**Response (Success - 201)**:
```json
{
  "success": true,
  "message": "Certificate added successfully",
  "certificate": {
    "CertificateID": "cert-abc123...",
    "CertificateName": "test.example.com",
    "Environment": "Test",
    "Status": "Active",
    "DaysUntilExpiry": "229",
    "CreatedOn": "2025-10-29T02:10:00Z",
    ...
  }
}
```

**Response (Error - 400)**:
```json
{
  "error": "Missing required fields",
  "missing": ["CertificateName", "OwnerEmail"]
}
```

**Update Certificate** (PUT)
```bash
curl -X PUT https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url.eu-west-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{
    "CertificateID": "cert-abc123...",
    "ExpiryDate": "2026-09-15",
    "Status": "Active"
  }'
```

**Response (Success - 200)**:
```json
{
  "success": true,
  "message": "Certificate updated successfully"
}
```

### Field Validation

**Email Validation**:
```javascript
// Must match: name@domain.ext
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
```

**Date Validation**:
- Format: YYYY-MM-DD
- Must be a valid date

**Required Field Check**:
- Returns 400 error with list of missing fields

### Audit Logging

Every add/update operation is logged to `cert-management-dev-certificate-logs`:

```json
{
  "LogID": "log-xyz789...",
  "CertificateID": "cert-abc123...",
  "Action": "CREATE",
  "Timestamp": "2025-10-29T02:10:00Z",
  "Details": "Certificate test.example.com added via dashboard",
  "PerformedBy": "test@example.com"
}
```

### Testing Tools

**Test Suite**: Full automated test suite available
```
http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/test-add-certificate.html
```

**Features**:
- 6 automated validation tests
- Test #6 performs actual API POST to DynamoDB
- 3 pre-configured test scenarios
- Live logging and statistics
- Sample data generator

**Simple Diagnostic Test**: Quick API test
```
http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/test-api-simple.html
```

**Features**:
- One-click API POST test
- Detailed request/response logs
- Error diagnosis
- Browser-side validation

### PowerShell Testing

```powershell
# Test adding certificate
$cert = @{
    CertificateName = "powershell-test.example.com"
    Environment = "Test"
    Application = "PowerShell Test"
    ExpiryDate = (Get-Date).AddDays(90).ToString("yyyy-MM-dd")
    Type = "SSL/TLS"
    OwnerEmail = "test@example.com"
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx..." `
  -Method POST `
  -Body $cert `
  -ContentType "application/json" `
  -UseBasicParsing

# Response: 201 Created
```

---

## 📥 Manual Import Process

### Why Manual Import?

- Excel processor Lambda missing openpyxl library
- Lambda layer not created in Terraform
- **Workaround**: Standalone Python script works perfectly ✅

### Execution

**Prerequisites**:
```bash
pip install boto3 openpyxl
aws configure  # Set credentials, region eu-west-1
```

**Run Import**:
```bash
python import_certificates.py --file PostNL_Certificates.xlsx
```

**Results**:
```
✅ Successfully imported 191 certificates
   - 8 batches (25 items each, except last batch: 16)
   - 100% success rate (0 failures)
   - ~5 seconds total time
```

**Validation**:
```bash
# Verify count
aws dynamodb scan --table-name cert-management-dev-certificates --select "COUNT"
# Output: {"Count": 191}

# Sample record
aws dynamodb get-item --table-name cert-management-dev-certificates \
  --key '{"CertificateID": {"S": "..."}}' | jq '.Item.CommonName.S'
# Output: "adfs-aws2.p02.cldsvc.net"
```

### Features

- **Flexible column mapping**: Handles different Excel formats, case-insensitive
- **Multiple date formats**: DD/MM/YYYY, YYYY-MM-DD, Excel numeric
- **Auto status**: Calculates Active/Expiring Soon/Expired based on expiry date
- **Batch writes**: 25 items per API call (DynamoDB limit)
- **Error handling**: Skips bad rows, continues processing, reports summary

---

## ⚙️ Configuration Guide

### Access URLs

**Dashboard**:
```
http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/index.html
```

**API**:
```
https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url.eu-west-1.on.aws/
```

### Testing

**Test GET (Fetch certificates)**:
```bash
# cURL
curl https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url.eu-west-1.on.aws/ | jq '.count'
# Expected: 191

# PowerShell
Invoke-RestMethod "https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx..." | 
  Select count
# Expected: 191
```

**Test POST (Add certificate)** ✨ NEW:
```bash
# cURL
curl -X POST https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url.eu-west-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{
    "CertificateName": "test-api.example.com",
    "Environment": "Test",
    "Application": "API Test",
    "ExpiryDate": "2026-06-15",
    "Type": "SSL/TLS",
    "OwnerEmail": "test@example.com"
  }'
# Expected: 201 Created

# PowerShell
$cert = @{
    CertificateName = "test-powershell.example.com"
    Environment = "Test"
    Application = "PowerShell Test"
    ExpiryDate = (Get-Date).AddDays(90).ToString("yyyy-MM-dd")
    Type = "SSL/TLS"
    OwnerEmail = "test@example.com"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx..." `
  -Method POST `
  -Body $cert `
  -ContentType "application/json" `
  -UseBasicParsing

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
# Expected: {"success": true, "certificate": {...}}
```

**Test PUT (Update certificate)** ✨ NEW:
```bash
# cURL
curl -X PUT https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url.eu-west-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{
    "CertificateID": "cert-abc123...",
    "ExpiryDate": "2026-09-15",
    "OwnerEmail": "newemail@example.com"
  }'
# Expected: 200 OK

# PowerShell
$update = @{
    CertificateID = "cert-abc123..."
    ExpiryDate = "2026-09-15"
    OwnerEmail = "newemail@example.com"
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx..." `
  -Method PUT `
  -Body $update `
  -ContentType "application/json" `
  -UseBasicParsing
# Expected: {"success": true, "message": "Certificate updated successfully"}
```

**Browser Testing**:
- **Dashboard**: http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/
- **Test Suite**: http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/test-add-certificate.html
- **Simple Test**: http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/test-api-simple.html

### Environment Variables

**Lambda Functions**:
```
CERTIFICATES_TABLE=cert-management-dev-certificates
LOGS_TABLE=cert-management-dev-certificate-logs
SENDER_EMAIL=vinaya-c.nayanegali@capgemini.com
EXPIRY_THRESHOLD=30
REGION=eu-west-1
```

---

## 🐛 Troubleshooting

### 1. Dashboard Shows 0 Certificates

**Solutions**:
- Clear browser cache (Ctrl+Shift+R)
- Check API URL in `dashboard.js`
- Verify Lambda Function URL has public access
- Test API directly with curl

### 2. CORS Errors

**Symptoms**: "Failed to fetch", "CORS policy blocked"

**Solutions**:
- ✅ Ensure Lambda code has NO CORS headers
- ✅ Verify Lambda Function URL CORS config
- ✅ Use S3 website URL (HTTP) not REST API (HTTPS)
- ✅ Check browser DevTools Network tab for duplicate headers

### 3. Email Notifications Not Sending

**Solutions**:
- Verify SES email identity:
  ```bash
  aws ses get-identity-verification-attributes \
    --identities vinaya-c.nayanegali@capgemini.com
  ```
- Check SES sandbox mode (verify recipients or request production access)
- Verify Lambda IAM role has SES permissions

### 4. Import Script Fails

**Solutions**:
```bash
pip install boto3 openpyxl
aws configure
python import_certificates.py --file cert.xlsx
```

### 5. "CONFIG is not defined" Error ✨ FIXED

**Symptom**: Error when clicking "Save Certificate" button

**Root Cause**: Dashboard.js referenced `CONFIG.apiUrl` but variable was `API_CONFIG`

**Solution Applied**:
```javascript
// BEFORE (❌ Error)
const response = await fetch(CONFIG.apiUrl, {
    method: 'POST',
    ...
});

// AFTER (✅ Fixed)
const API_URL = 'https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx...';
const response = await fetch(API_URL, {
    method: 'POST',
    ...
});
```

**Fix**:
- Defined `API_URL` as constant at top of file
- Changed all `CONFIG.apiUrl` references to `API_URL`
- Updated index.html version number to force cache refresh

### 6. Certificate Addition Fails

**Symptoms**: "Failed to save certificate. Please try again."

**Solutions**:
- Hard refresh browser (Ctrl+Shift+R or Ctrl+F5)
- Clear all browser cache (Ctrl+Shift+Delete)
- Try in Incognito/Private browsing mode
- Check browser Console (F12) for detailed error messages
- Verify all required fields are filled
- Ensure email format is valid
- Test API directly:
  ```bash
  curl -X POST https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx... \
    -H "Content-Type: application/json" \
    -d '{"CertificateName":"test.com","Environment":"Test",...}'
  ```

### 7. Expired Certificates Showing as "Active" 🆕 FIXED

**Symptom**: Certificates with past expiry dates displaying "Active" status instead of "Expired"

**Root Cause**: Dashboard displayed database status directly without validating against current date. Old certificates had stale "Active" status in database.

**Solution Applied**:
```javascript
// Auto-recalculate status based on actual expiry date
function calculateActualStatus(daysLeft, currentStatus) {
    // Preserve manual statuses
    if (['Renewal in Progress', 'Renewal Done'].includes(currentStatus)) {
        return currentStatus;
    }
    
    // Calculate based on days left
    if (daysLeft < 0) return 'Expired';
    if (daysLeft <= 30) return 'Due for Renewal';
    return 'Active';
}
```

**Fix Details**:
- ✅ Client-side status recalculation on every page load
- ✅ Overrides stale database values
- ✅ Preserves manual statuses (Renewal in Progress)
- ✅ Updates statistics cards with accurate counts
- ✅ Version: 20251029-1630

**Verification**:
```
1. Refresh dashboard (Ctrl+F5)
2. Check statistics cards show accurate counts
3. Expired certificates display red "Expired" badge
4. Days Left shows negative values for expired certs
```

### 8. Browser Cache Issues

**Symptoms**: Changes not appearing, old errors persisting

**Solutions**:
```
1. Hard Refresh:
   - Windows: Ctrl + Shift + R (or Ctrl + F5)
   - Mac: Cmd + Shift + R

2. Clear Cache:
   - Press Ctrl + Shift + Delete
   - Select "Cached images and files"
   - Clear last hour or all time

3. Incognito Mode:
   - Ctrl + Shift + N (Chrome/Edge)
   - Ctrl + Shift + P (Firefox)

4. Version Parameter:
   - Add ?v=timestamp to URL
   - Example: index.html?v=20251029
```

### Diagnostic Tools

**Browser DevTools (F12)**:
```
Console Tab:
- Shows JavaScript errors
- Displays API request/response logs
- Shows "CONFIG is not defined" errors

Network Tab:
- OPTIONS request (preflight) → 200 ✅
- GET request → 200 ✅
- POST request → 201 ✅
- Response headers include Access-Control-Allow-Origin ✅
- Check for duplicate CORS headers ❌

Application Tab:
- Clear cache and storage
- View cookies and session data
```

**CloudWatch Logs**:
```bash
aws logs tail /aws/lambda/cert-management-dev-dashboard-api --follow
```

**Test Pages**:
- Full test suite: `/test-add-certificate.html`
- Simple diagnostic: `/test-api-simple.html`

---

## 📞 Support & Maintenance

### Monitoring

- **CloudWatch Dashboard**: `cert-management-dev-dashboard`
- **Log Groups**: 3 (30-day retention)
- **Metrics**: Lambda duration/errors, DynamoDB capacity

### Backup

- **DynamoDB**: Point-in-time recovery enabled (35-day window)
- **S3**: Versioning enabled on uploads/logs buckets

### Cost Estimate

**Monthly**: ~$2-10 USD
- DynamoDB: $1-3 (on-demand, 191 items)
- Lambda: $0.20-1 (daily invocations)
- S3: $0.10-0.50 (minimal storage)
- CloudWatch: $0.50-2 (logs, metrics)
- SES: $0.10/1000 emails

---

## 📚 Resources

### AWS Documentation
- [Lambda Function URLs](https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html)
- [DynamoDB GSIs](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html)
- [S3 CORS](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cors.html)

### Repository
- **GitHub**: https://github.com/vinaya-cg/certificate-monitor
- **Branch**: main
- **Last Updated**: October 29, 2025

---

## 🎉 Deployment Summary

**✅ Working**:
- Complete AWS infrastructure (28 resources)
- DynamoDB with 191 certificates
- Dashboard API with GET, POST, PUT support ✨ NEW
- Daily monitoring + email notifications
- Web dashboard (S3 static hosting)
- **Add/Update certificates via web interface** ✨ NEW
- **Automatic status calculation** ✨ NEW
- **Field validation and error handling** ✨ NEW
- **Audit logging for all operations** ✨ NEW
- Manual import script
- CORS properly configured
- Complete test suite for certificate addition ✨ NEW

**⚠️ Limitations**:
- Excel processor Lambda needs openpyxl layer
- SES sandbox mode (verify recipients)
- Dashboard Excel upload feature not implemented (use manual import script)

**🔧 Next Steps**:
1. Request SES production access
2. Add Lambda layer with openpyxl for Excel processor
3. Configure CloudWatch alarms
4. Set S3 lifecycle policies
5. Add CloudFront for HTTPS
6. Implement delete certificate functionality
7. Add bulk certificate update feature
8. Create certificate renewal workflow

**📊 Recent Updates** (October 29, 2025):
- ✅ Added POST endpoint to Lambda API for creating certificates
- ✅ Added PUT endpoint to Lambda API for updating certificates
- ✅ Implemented automatic status calculation (Active/Due for Renewal/Expired)
- ✅ Implemented automatic days until expiry calculation
- ✅ Added field validation (required fields, email format)
- ✅ Added audit logging to certificate-logs table
- ✅ Updated dashboard.js to support add/update operations
- ✅ Fixed "CONFIG is not defined" error
- ✅ Added detailed error logging and messages
- ✅ Created comprehensive test suite (test-add-certificate.html)
- ✅ Created simple diagnostic test (test-api-simple.html)
- ✅ Updated CORS configuration to support POST/PUT methods

**🎯 Current Capabilities**:
1. **View Certificates**: Browse all 191 certificates with filtering and search
2. **Add Certificates**: Add new certificates via web form or API
3. **Update Certificates**: Edit existing certificates via web form or API
4. **Monitor Certificates**: Daily automated checks for expiring certificates
5. **Email Alerts**: Automatic notifications for certificates expiring within 30 days
6. **Bulk Import**: Import certificates from Excel files
7. **Audit Trail**: Complete logs of all create/update operations
8. **Testing**: Full test suite to validate all functionality

---

**Author**: Vinaya Nayanegali  
**Email**: vinaya-c.nayanegali@capgemini.com  
**Organization**: Capgemini/Sogeti  
**Version**: 1.0  
**Date**: October 29, 2025
