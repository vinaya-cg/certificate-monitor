# Certificate Management Dashboard

## 📋 Table of Contents
- [Overview](#overview)
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
- ✅ **Bulk Import**: Python script for importing certificates from Excel files
- ✅ **Complete Audit Trail**: All changes logged in DynamoDB
- ✅ **Infrastructure as Code**: 100% Terraform-managed AWS infrastructure

### System Status
- **Environment**: Development (`dev`)
- **Region**: `eu-west-1` (Ireland)
- **Deployment Method**: Terraform + AWS CLI
- **Certificates Imported**: 191 PostNL certificates
- **Status**: Production-ready

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
- **CORS** (Configured in Terraform + AWS CLI):
  ```hcl
  cors {
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "OPTIONS"]
    allow_headers     = ["date", "keep-alive", "content-type"]
    max_age          = 86400
  }
  ```
- **Code Logic**: Scans DynamoDB, converts Decimal→float, returns JSON
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

**1. dashboard_api.py**
```python
# Scan DynamoDB certificates table
# Convert Decimal → float (JSON compatibility)
# Convert datetime → ISO 8601 string
# Return JSON: {"certificates": [...], "count": 191}
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

**4. dashboard.js**
```javascript
// Fetch certificates from Lambda Function URL
// Defensive DOM element checks (prevent null errors)
// Render table, calculate statistics
// Filter by status, environment, search term
```

**Fixed Null Check Example**:
```javascript
// BEFORE: uploadArea.addEventListener(...) → null error
// AFTER:
const uploadArea = document.getElementById('uploadArea');
if (uploadArea && fileInput) {
    uploadArea.addEventListener('click', () => fileInput.click());
} else {
    console.log('Upload elements not found, skipping');
}
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

```bash
# Test API
curl https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url... | jq '.count'
# Expected: 191

# PowerShell
Invoke-RestMethod "https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx..." | 
  Select count
# Expected: 191
```

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

### Diagnostic Tools

**Browser DevTools (F12)**:
```
Network Tab:
- OPTIONS request (preflight) → 200 ✅
- GET request → 200 ✅
- Response headers include Access-Control-Allow-Origin ✅
```

**CloudWatch Logs**:
```bash
aws logs tail /aws/lambda/cert-management-dev-dashboard-api --follow
```

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
- Dashboard API (Lambda Function URL)
- Daily monitoring + email notifications
- Web dashboard (S3 static hosting)
- Manual import script
- CORS properly configured

**⚠️ Limitations**:
- Excel processor Lambda needs openpyxl layer
- SES sandbox mode (verify recipients)
- Dashboard upload feature not implemented

**🔧 Next Steps**:
1. Request SES production access
2. Add Lambda layer with openpyxl
3. Configure CloudWatch alarms
4. Set S3 lifecycle policies
5. Add CloudFront for HTTPS

---

**Author**: Vinaya Nayanegali  
**Email**: vinaya-c.nayanegali@capgemini.com  
**Organization**: Capgemini/Sogeti  
**Version**: 1.0  
**Date**: October 29, 2025
