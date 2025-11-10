# Complete Deployment Guide - Certificate Management Dashboard

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture Overview](#architecture-overview)
4. [Initial Setup](#initial-setup)
5. [Terraform Deployment](#terraform-deployment)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Feature Enablement](#feature-enablement)
8. [Verification & Testing](#verification--testing)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

---

## Overview

This guide provides complete, step-by-step instructions for deploying the Certificate Management Dashboard from scratch. The deployment is fully automated using Terraform and includes:

- **Core Infrastructure:** DynamoDB, S3, CloudFront, Cognito
- **Lambda Functions:** Dashboard API, Certificate Monitor, Excel Processor
- **API Gateway:** RESTful API with Cognito authorization
- **Optional Features:**
  - ACM Certificate Sync
  - Server Certificate Scanning
  - ServiceNow Integration

**Estimated Deployment Time:** 15-20 minutes

---

## Prerequisites

### Required Tools

1. **Terraform** >= 1.0.0
   ```bash
   terraform version
   # Terraform v1.5.0 or higher
   ```

2. **AWS CLI** >= 2.0
   ```bash
   aws --version
   # aws-cli/2.13.0 or higher
   ```

3. **Git**
   ```bash
   git --version
   ```

4. **Python** 3.9+ (for local testing)
   ```bash
   python --version
   ```

### AWS Account Setup

1. **AWS Account** with Administrator access
2. **AWS Profile** configured
   ```bash
   aws configure --profile cert-management
   # AWS Access Key ID: ***
   # AWS Secret Access Key: ***
   # Default region name: eu-west-1
   # Default output format: json
   ```

3. **S3 Bucket** for Terraform state (optional but recommended)
   ```bash
   aws s3 mb s3://terraform-state-cert-management --region eu-west-1
   ```

### AWS Service Limits

Verify your account has sufficient limits:
- **Lambda Functions:** At least 10
- **API Gateway APIs:** At least 1
- **DynamoDB Tables:** At least 2
- **CloudFront Distributions:** At least 1
- **Cognito User Pools:** At least 1

---

## Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     CloudFront CDN                          │
│              (HTTPS Distribution)                           │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   S3 Dashboard Bucket                       │
│          (index.html, dashboard.js, images)                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                              │
│  /certificates, /sync-acm, /sync-server-certs               │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Cognito User Pool                         │
│         (Authentication & Authorization)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Lambda Functions                         │
│  • Dashboard API      • Certificate Monitor                 │
│  • Excel Processor    • ACM Sync                            │
│  • Server Scanner     • ServiceNow Ticket Creator           │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                      DynamoDB                               │
│  • Certificates Table                                       │
│  • Certificate Logs Table                                   │
└─────────────────────────────────────────────────────────────┘
```

### Terraform Module Structure

```
terraform/
├── environments/
│   └── dev-secure/
│       ├── main.tf           # Main environment configuration
│       ├── variables.tf      # Environment variables
│       ├── terraform.tfvars  # Environment-specific values
│       └── outputs.tf        # Output values
└── modules/
    ├── api_gateway/          # API Gateway configuration
    ├── cloudfront/           # CloudFront distribution
    ├── cognito/              # User authentication
    ├── database/             # DynamoDB tables
    ├── dashboard_secure/     # Dashboard files deployment
    ├── eventbridge/          # Scheduled events
    ├── iam/                  # IAM roles and policies
    ├── lambda_acm_sync/      # ACM synchronization
    ├── lambda_secure/        # Core Lambda functions
    ├── lambda_server_scanner/# Server scanning
    ├── lambda_servicenow/    # ServiceNow integration
    ├── monitoring/           # CloudWatch dashboards
    └── storage_secure/       # S3 buckets
```

---

## Initial Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/vinaya-cg/certificate-monitor.git
cd certificate-monitor
```

### Step 2: Review Configuration Files

#### terraform.tfvars

**Location:** `terraform/environments/dev-secure/terraform.tfvars`

```hcl
# Project Configuration
project_name = "cert-management"
environment  = "dev-secure"
aws_region   = "eu-west-1"

# Email Configuration
sender_email = "vinaya-c.nayanegali@capgemini.com"
admin_email  = "vinaya-c.nayanegali@capgemini.com"

# Feature Flags
enable_acm_sync                = true   # Enable ACM certificate sync
enable_server_certificate_scan = true   # Enable server scanning
enable_servicenow_integration  = true   # Enable ServiceNow tickets
enable_servicenow_webhook      = false  # Disable webhook (optional)

# ServiceNow Configuration (if enabled)
servicenow_instance_url = "https://yourinstance.service-now.com"
servicenow_api_endpoint = "/api/now/table/incident"
servicenow_dry_run      = "false"  # Set to "true" for testing

# Tags
common_tags = {
  Project     = "cert-management"
  Environment = "dev-secure"
  ManagedBy   = "Terraform"
  Owner       = "Certificate-Management-Team"
  Security    = "Enhanced"
}
```

**Important:** Update email addresses and ServiceNow URL for your environment.

#### variables.tf

**Location:** `terraform/environments/dev-secure/variables.tf`

Review variable definitions and defaults. No changes needed unless customizing.

### Step 3: Configure AWS Profile

```bash
export AWS_PROFILE=cert-management
export AWS_REGION=eu-west-1
```

Or add to `~/.bashrc` / `~/.zshrc`:
```bash
echo 'export AWS_PROFILE=cert-management' >> ~/.bashrc
echo 'export AWS_REGION=eu-west-1' >> ~/.bashrc
source ~/.bashrc
```

### Step 4: Configure Terraform Backend (Optional)

**File:** `terraform/environments/dev-secure/backend.tf`

```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state-cert-management"
    key            = "dev-secure/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

**Create DynamoDB table for state locking:**
```bash
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1
```

---

## Terraform Deployment

### Step 1: Initialize Terraform

```bash
cd terraform/environments/dev-secure
terraform init
```

**Expected Output:**
```
Initializing modules...
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully initialized!
```

### Step 2: Validate Configuration

```bash
terraform validate
```

**Expected Output:**
```
Success! The configuration is valid.
```

### Step 3: Review Deployment Plan

```bash
terraform plan -out=tfplan
```

**Review the plan carefully.** You should see approximately:
- **60-70 resources to be created**
- No resources to be destroyed (first deployment)

**Key resources to verify:**
- `aws_cognito_user_pool.main`
- `aws_dynamodb_table.certificates`
- `aws_dynamodb_table.certificate_logs`
- `aws_lambda_function.dashboard_api`
- `aws_api_gateway_rest_api.main`
- `aws_cloudfront_distribution.dashboard`

### Step 4: Apply Terraform Plan

```bash
terraform apply tfplan
```

Or apply directly with auto-approve:
```bash
terraform apply -auto-approve
```

**Deployment Progress:**

1. **Phase 1: Base Resources (2-3 minutes)**
   - IAM roles and policies
   - DynamoDB tables
   - S3 buckets

2. **Phase 2: Lambda Functions (3-4 minutes)**
   - Package and upload Lambda code
   - Create Lambda functions
   - Configure environment variables

3. **Phase 3: API Gateway (1-2 minutes)**
   - Create REST API
   - Configure methods and integrations
   - Deploy to stage

4. **Phase 4: CloudFront (5-10 minutes)**
   - Create distribution (longest step)
   - Configure origin and behaviors
   - Propagate to edge locations

5. **Phase 5: Cognito (1-2 minutes)**
   - Create user pool
   - Create user pool client
   - Create default users

**Total Time:** Approximately 15-20 minutes

### Step 5: Capture Outputs

```bash
terraform output -json > deployment-outputs.json
```

**Important outputs:**
```json
{
  "cloudfront_distribution_url": "https://d3bqyfjow8topp.cloudfront.net",
  "api_gateway_url": "https://8clm33qmf9.execute-api.eu-west-1.amazonaws.com/dev-secure",
  "cognito_user_pool_id": "eu-west-1_cWIxi5SPd",
  "cognito_client_id": "1dq9f0m4fil3fiqcpk0h575kb1",
  "cognito_users": {
    "admin": "vinaya-c.nayanegali@capgemini.com",
    "operator": "vinaya-c.nayanegali+operator@capgemini.com",
    "viewer": "vinaya-c.nayanegali+viewer@capgemini.com"
  }
}
```

Save these values - you'll need them for testing and configuration.

---

## Post-Deployment Configuration

### Step 1: Verify SES Email

1. **Check your email** for AWS SES verification message
2. **Click verification link** in the email
3. **Confirm sender identity** is verified:
   ```bash
   aws ses get-identity-verification-attributes \
     --identities vinaya-c.nayanegali@capgemini.com
   ```

**Note:** Without SES verification, email notifications won't work.

### Step 2: Set Cognito User Passwords

Check email for temporary passwords for three users:
- Admin user
- Operator user
- Viewer user

**First login will require password change.**

### Step 3: Upload Dashboard Files (if not automated)

Dashboard files should be automatically uploaded by Terraform. Verify:

```bash
aws s3 ls s3://cert-management-dev-secure-dashboard-$(terraform output -raw random_suffix)/
```

**Expected files:**
```
index.html
dashboard.js
login.html
error.html
auth.js
auth-cognito.js
images/sogeti-logo.png
images/postnl-logo.png
```

If files are missing, manually upload:
```bash
cd ../../../dashboard
aws s3 sync . s3://cert-management-dev-secure-dashboard-<suffix>/ \
  --exclude "*.backup" \
  --exclude "*.old"
```

### Step 4: Configure ServiceNow Credentials (if enabled)

**Create secret in AWS Secrets Manager:**

```bash
aws secretsmanager create-secret \
  --name cert-management/servicenow/credentials \
  --description "ServiceNow OAuth credentials for certificate management" \
  --secret-string '{
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "username": "your-username",
    "password": "your-password"
  }'
```

**Update dry_run mode in terraform.tfvars:**
```hcl
servicenow_dry_run = "true"  # Test mode (no actual tickets created)
```

**Apply changes:**
```bash
terraform apply -auto-approve
```

**Verify secret:**
```bash
aws secretsmanager get-secret-value \
  --secret-id cert-management/servicenow/credentials \
  --query SecretString \
  --output text | jq
```

### Step 5: Tag EC2 Instances for Scanning (if server scanning enabled)

```bash
# Get instance IDs
INSTANCES=$(aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].InstanceId' \
  --output text)

# Tag instances
for INSTANCE in $INSTANCES; do
  aws ec2 create-tags \
    --resources $INSTANCE \
    --tags Key=CertificateScanning,Value=enabled
done
```

**Verify tags:**
```bash
aws ec2 describe-instances \
  --filters "Name=tag:CertificateScanning,Values=enabled" \
  --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0]]' \
  --output table
```

---

## Feature Enablement

### ACM Certificate Sync

**Enabled by default** in `terraform.tfvars`:
```hcl
enable_acm_sync = true
```

**Schedule:** Daily at 9:00 AM UTC (cron: `0 9 * * ? *`)

**Manual trigger:** Click "Sync from ACM" button in dashboard

**Verify deployment:**
```bash
aws lambda get-function \
  --function-name cert-management-dev-secure-acm-sync \
  --query 'Configuration.[FunctionName,Runtime,Handler]' \
  --output table
```

### Server Certificate Scanning

**Enabled in `terraform.tfvars`:**
```hcl
enable_server_certificate_scan = true
```

**Schedule:** Daily at 9:30 AM UTC (cron: `30 9 * * ? *`)

**Manual trigger:** Click "Sync from Servers" button in dashboard

**Prerequisites:**
1. EC2 instances tagged with `CertificateScanning=enabled`
2. SSM Agent installed and running
3. IAM instance profile with `AmazonSSMManagedInstanceCore` policy

**Verify deployment:**
```bash
aws lambda get-function \
  --function-name cert-management-dev-secure-server-cert-scanner \
  --query 'Configuration.[FunctionName,Runtime,Timeout]' \
  --output table
```

**Test SSM connectivity:**
```bash
aws ssm describe-instance-information \
  --filters "Key=tag:CertificateScanning,Values=enabled" \
  --query 'InstanceInformationList[].[InstanceId,PlatformType,PingStatus]' \
  --output table
```

### ServiceNow Integration

**Enabled in `terraform.tfvars`:**
```hcl
enable_servicenow_integration = true
servicenow_dry_run = "true"  # Test mode first
```

**Schedule:** Daily at 9:05 AM UTC (cron: `5 9 * * ? *`)

**Prerequisites:**
1. ServiceNow instance URL
2. OAuth credentials stored in Secrets Manager
3. Assignment group configured in ServiceNow

**Verify deployment:**
```bash
aws lambda get-function \
  --function-name cert-management-servicenow-ticket-creator \
  --query 'Configuration.[FunctionName,Environment.Variables.DRY_RUN]' \
  --output table
```

**Test in dry-run mode:**
```bash
aws lambda invoke \
  --function-name cert-management-servicenow-ticket-creator \
  --payload '{}' \
  response.json

cat response.json | jq
```

**Enable production mode:**
```hcl
# terraform.tfvars
servicenow_dry_run = "false"
```

```bash
terraform apply -auto-approve
```

---

## Verification & Testing

### Step 1: Access Dashboard

1. **Get CloudFront URL:**
   ```bash
   terraform output cloudfront_distribution_url
   # https://d3bqyfjow8topp.cloudfront.net
   ```

2. **Open in browser:**
   ```
   https://d3bqyfjow8topp.cloudfront.net
   ```

3. **Login with admin credentials**
   - Email: From Cognito temporary password email
   - Password: Temporary password (will be required to change)

### Step 2: Test Core Functionality

#### Test Certificate Management

1. **View existing certificates** (if any from ACM sync)
2. **Filter by status:** Active, Expiring, Expired
3. **Search by domain name**
4. **Sort by expiry date**

#### Test Excel Import

1. **Download sample Excel:**
   - Click "Export" button
   - Save as template

2. **Upload Excel:**
   - Click "Upload Excel" button
   - Select file
   - Verify success message

#### Test Manual Sync

##### ACM Sync
1. Click "Sync from ACM" button
2. Wait for modal to show results
3. Verify certificates appear in dashboard

##### Server Sync
1. Click "Sync from Servers" button
2. Wait 30-60 seconds for scan
3. Review results:
   - Servers scanned
   - Certificates found
   - New certificates added
4. Click "Refresh Dashboard"
5. Verify new certificates appear

### Step 3: Test API Endpoints

#### Get Cognito Token

```bash
# Login and get token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $(terraform output -raw cognito_client_id) \
  --auth-parameters \
    USERNAME=vinaya-c.nayanegali@capgemini.com,PASSWORD='YourPassword123!' \
  --query 'AuthenticationResult.IdToken' \
  --output text > token.txt

TOKEN=$(cat token.txt)
```

#### Test GET /certificates

```bash
curl -X GET \
  "$(terraform output -raw api_gateway_url)/certificates" \
  -H "Authorization: $TOKEN" \
  | jq
```

**Expected:**
```json
{
  "statusCode": 200,
  "body": [
    {
      "CertificateId": "cert-123",
      "CommonName": "example.com",
      "ExpiryDate": "2025-12-31T23:59:59Z",
      "Status": "Active"
    }
  ]
}
```

#### Test POST /sync-acm

```bash
curl -X POST \
  "$(terraform output -raw api_gateway_url)/sync-acm" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  | jq
```

#### Test POST /sync-server-certs

```bash
curl -X POST \
  "$(terraform output -raw api_gateway_url)/sync-server-certs" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  | jq
```

### Step 4: Verify Scheduled Execution

#### Check EventBridge Rules

```bash
# ACM Sync Schedule
aws events describe-rule \
  --name cert-management-dev-secure-acm-sync-schedule

# Server Scan Schedule
aws events describe-rule \
  --name cert-management-dev-secure-server-cert-scan-schedule

# ServiceNow Schedule (if enabled)
aws events describe-rule \
  --name cert-management-servicenow-schedule
```

#### Test Lambda Invocation

```bash
# Test dashboard API
aws lambda invoke \
  --function-name cert-management-dev-secure-dashboard-api \
  --payload '{"httpMethod":"GET","path":"/certificates","headers":{}}' \
  response.json

# Test ACM sync
aws lambda invoke \
  --function-name cert-management-dev-secure-acm-sync \
  --payload '{}' \
  acm-response.json

# Test server scanner (if enabled)
aws lambda invoke \
  --function-name cert-management-dev-secure-server-cert-scanner \
  --payload '{}' \
  scanner-response.json
```

### Step 5: Monitor CloudWatch Logs

```bash
# Dashboard API logs
aws logs tail /aws/lambda/cert-management-dev-secure-dashboard-api --follow

# ACM Sync logs
aws logs tail /aws/lambda/cert-management-dev-secure-acm-sync --follow

# Server Scanner logs
aws logs tail /aws/lambda/cert-management-dev-secure-server-cert-scanner --follow
```

---

## Troubleshooting

### CloudFront Distribution Not Accessible

**Symptom:** 404 Not Found or Access Denied

**Solutions:**
1. **Wait for propagation:** CloudFront takes 10-15 minutes to fully deploy
   ```bash
   aws cloudfront get-distribution \
     --id $(terraform output -raw cloudfront_distribution_id) \
     --query 'Distribution.Status'
   ```
   Wait for status: `Deployed`

2. **Verify S3 files:**
   ```bash
   aws s3 ls s3://$(terraform output -raw dashboard_bucket_name)/
   ```

3. **Check OAI permissions:**
   ```bash
   aws s3api get-bucket-policy \
     --bucket $(terraform output -raw dashboard_bucket_name) \
     | jq '.Policy | fromjson'
   ```

### Cognito Authentication Failing

**Symptom:** Unable to login or 401 Unauthorized

**Solutions:**
1. **Verify user exists:**
   ```bash
   aws cognito-idp admin-get-user \
     --user-pool-id $(terraform output -raw cognito_user_pool_id) \
     --username vinaya-c.nayanegali@capgemini.com
   ```

2. **Reset password:**
   ```bash
   aws cognito-idp admin-set-user-password \
     --user-pool-id $(terraform output -raw cognito_user_pool_id) \
     --username vinaya-c.nayanegali@capgemini.com \
     --password 'NewPassword123!' \
     --permanent
   ```

3. **Check user group membership:**
   ```bash
   aws cognito-idp admin-list-groups-for-user \
     --user-pool-id $(terraform output -raw cognito_user_pool_id) \
     --username vinaya-c.nayanegali@capgemini.com
   ```

### Lambda Function Errors

**Symptom:** 500 Internal Server Error from API

**Solutions:**
1. **Check CloudWatch Logs:**
   ```bash
   aws logs tail /aws/lambda/cert-management-dev-secure-dashboard-api \
     --since 10m \
     --format short
   ```

2. **Verify environment variables:**
   ```bash
   aws lambda get-function-configuration \
     --function-name cert-management-dev-secure-dashboard-api \
     --query 'Environment.Variables'
   ```

3. **Test function directly:**
   ```bash
   aws lambda invoke \
     --function-name cert-management-dev-secure-dashboard-api \
     --payload '{"httpMethod":"GET","path":"/certificates"}' \
     --log-type Tail \
     response.json \
     --query 'LogResult' \
     --output text | base64 -d
   ```

### DynamoDB Access Issues

**Symptom:** No certificates appearing in dashboard

**Solutions:**
1. **Verify tables exist:**
   ```bash
   aws dynamodb list-tables \
     --query 'TableNames[?contains(@, `cert-management`)]'
   ```

2. **Check table contents:**
   ```bash
   aws dynamodb scan \
     --table-name cert-management-dev-secure-certificates \
     --max-items 5
   ```

3. **Verify IAM permissions:**
   ```bash
   aws lambda get-function \
     --function-name cert-management-dev-secure-dashboard-api \
     --query 'Configuration.Role'
   
   # Check role policies
   aws iam list-attached-role-policies \
     --role-name cert-management-dev-secure-lambda-role
   ```

### Server Scanning Not Working

**Symptom:** 0 servers scanned or no certificates found

**Solutions:**
1. **Verify EC2 tags:**
   ```bash
   aws ec2 describe-instances \
     --filters "Name=tag:CertificateScanning,Values=enabled" \
     --query 'Reservations[].Instances[].[InstanceId,State.Name]' \
     --output table
   ```

2. **Check SSM connectivity:**
   ```bash
   aws ssm describe-instance-information \
     --filters "Key=tag:CertificateScanning,Values=enabled"
   ```

3. **Verify SSM Agent:**
   - Linux: `sudo systemctl status amazon-ssm-agent`
   - Windows: `Get-Service AmazonSSMAgent`

4. **Test SSM command:**
   ```bash
   aws ssm send-command \
     --document-name "AWS-RunShellScript" \
     --targets "Key=tag:CertificateScanning,Values=enabled" \
     --parameters 'commands=["echo test"]'
   ```

### ServiceNow Integration Issues

**Symptom:** No tickets created or dry-run errors

**Solutions:**
1. **Verify secret exists:**
   ```bash
   aws secretsmanager describe-secret \
     --secret-id cert-management/servicenow/credentials
   ```

2. **Test credentials:**
   ```bash
   # Get credentials
   CREDS=$(aws secretsmanager get-secret-value \
     --secret-id cert-management/servicenow/credentials \
     --query SecretString \
     --output text)
   
   # Test OAuth
   curl -X POST \
     "https://yourinstance.service-now.com/oauth_token.do" \
     -d "grant_type=password" \
     -d "client_id=$(echo $CREDS | jq -r .client_id)" \
     -d "client_secret=$(echo $CREDS | jq -r .client_secret)" \
     -d "username=$(echo $CREDS | jq -r .username)" \
     -d "password=$(echo $CREDS | jq -r .password)"
   ```

3. **Check Lambda logs:**
   ```bash
   aws logs tail /aws/lambda/cert-management-servicenow-ticket-creator \
     --since 1h \
     --format short
   ```

---

## Maintenance

### Regular Tasks

#### Daily
- **Monitor CloudWatch Dashboards:** Check for errors or anomalies
- **Review scheduled execution logs:** Verify ACM sync, server scan, ServiceNow tickets

#### Weekly
- **Review certificate expiry:** Check dashboard for upcoming expirations
- **Verify backup retention:** Ensure DynamoDB point-in-time recovery is enabled
- **Check S3 lifecycle policies:** Verify old uploads are being cleaned up

#### Monthly
- **Update Lambda functions:** Deploy security patches if available
- **Review IAM permissions:** Ensure least privilege access
- **Analyze costs:** Review AWS Cost Explorer for optimization opportunities
- **Update documentation:** Keep deployment guide current

### Updating Infrastructure

#### Update Lambda Code

```bash
# Update code
cd lambda/
# Make changes to *.py files

# Redeploy via Terraform
cd ../terraform/environments/dev-secure/
terraform apply -auto-approve
```

#### Update Dashboard Files

```bash
# Update files
cd dashboard/
# Make changes to HTML/JS files

# Redeploy via Terraform
cd ../terraform/environments/dev-secure/
terraform apply -auto-approve

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

#### Add New Users

```bash
# Create user
aws cognito-idp admin-create-user \
  --user-pool-id $(terraform output -raw cognito_user_pool_id) \
  --username newuser@example.com \
  --user-attributes Name=email,Value=newuser@example.com \
  --message-action SUPPRESS

# Set password
aws cognito-idp admin-set-user-password \
  --user-pool-id $(terraform output -raw cognito_user_pool_id) \
  --username newuser@example.com \
  --password 'TempPassword123!' \
  --permanent

# Add to group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $(terraform output -raw cognito_user_pool_id) \
  --username newuser@example.com \
  --group-name Operators
```

### Backup & Recovery

#### DynamoDB Backup

```bash
# Create on-demand backup
aws dynamodb create-backup \
  --table-name cert-management-dev-secure-certificates \
  --backup-name cert-management-backup-$(date +%Y%m%d)

# List backups
aws dynamodb list-backups \
  --table-name cert-management-dev-secure-certificates
```

#### Restore from Backup

```bash
aws dynamodb restore-table-from-backup \
  --target-table-name cert-management-dev-secure-certificates-restored \
  --backup-arn arn:aws:dynamodb:eu-west-1:123456789012:table/cert-management-dev-secure-certificates/backup/01234567890123-abcd1234
```

#### Terraform State Backup

```bash
# Export current state
terraform state pull > terraform.tfstate.backup

# Store in S3
aws s3 cp terraform.tfstate.backup \
  s3://terraform-state-cert-management/backups/$(date +%Y%m%d)/
```

### Disaster Recovery

#### Complete Infrastructure Rebuild

```bash
# Backup Terraform state
terraform state pull > state-backup.json

# Destroy all resources (if needed)
terraform destroy -auto-approve

# Rebuild from scratch
terraform init
terraform apply -auto-approve
```

---

## Cost Optimization

### Expected Monthly Costs (dev-secure environment)

| Service | Estimated Cost | Notes |
|---------|----------------|-------|
| Lambda | $5-10 | Based on ~10,000 invocations/month |
| DynamoDB | $2-5 | On-demand pricing, low traffic |
| API Gateway | $3-7 | Based on ~50,000 requests/month |
| CloudFront | $1-3 | Minimal traffic, data transfer costs |
| Cognito | $0 | Under 50,000 MAUs (free tier) |
| S3 | $1-2 | Small storage footprint |
| CloudWatch | $2-5 | Logs and metrics |
| **Total** | **$14-32/month** | Approximate range |

### Cost Reduction Tips

1. **Adjust Lambda memory:** Lower memory for infrequent functions
2. **DynamoDB provisioned capacity:** Switch from on-demand if usage is predictable
3. **CloudWatch log retention:** Reduce from 30 days to 7 days
4. **S3 lifecycle policies:** Move old logs to Glacier
5. **API Gateway caching:** Enable for frequently accessed endpoints

---

## Security Best Practices

1. **Rotate credentials regularly:** Cognito passwords, ServiceNow OAuth
2. **Enable MFA:** For Cognito users with admin access
3. **Restrict CORS:** Change from `*` to specific domain in production
4. **Enable CloudTrail:** Audit all API calls
5. **Use VPC endpoints:** For Lambda to DynamoDB communication
6. **Encrypt at rest:** Ensure all S3 buckets and DynamoDB tables use encryption
7. **Review IAM policies:** Follow principle of least privilege

---

## Support & Resources

### Documentation
- **Main README:** `README.md`
- **Server Sync Feature:** `SERVER_SYNC_FEATURE.md`
- **Quick Reference:** `QUICK_REFERENCE.md`
- **This Guide:** `COMPLETE_DEPLOYMENT_GUIDE.md`

### Useful Commands

```bash
# Get all outputs
terraform output

# Get specific output
terraform output cloudfront_distribution_url

# View Terraform state
terraform state list

# Show specific resource
terraform state show module.lambda_secure.aws_lambda_function.dashboard_api

# Refresh state without apply
terraform refresh
```

### Contact

- **Email:** vinaya-c.nayanegali@capgemini.com
- **Repository:** https://github.com/vinaya-cg/certificate-monitor
- **Issues:** Create GitHub issue for bugs or feature requests

---

## Appendix

### A. Terraform Module Reference

See individual module README files in `terraform/modules/*/README.md`

### B. Lambda Function Reference

See function documentation in `lambda/*/README.md`

### C. API Endpoint Reference

See API documentation in `API_REFERENCE.md`

### D. Troubleshooting Flowcharts

See detailed troubleshooting guides in `TROUBLESHOOTING.md`

---

**End of Deployment Guide**

**Version:** 1.0.0  
**Last Updated:** 2025-11-10  
**Author:** Venkata Narayana (vinaya-c.nayanegali@capgemini.com)
