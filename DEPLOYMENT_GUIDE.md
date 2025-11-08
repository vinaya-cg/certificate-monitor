# Certificate Dashboard - Deployment Guide

## Overview
This guide explains how to deploy the Certificate Management Dashboard to any AWS account. The deployment is fully automated using Terraform and requires minimal manual configuration.

## Prerequisites

### Required Tools
- **Terraform** >= 1.0
- **AWS CLI** configured with valid credentials
- **Git** (to clone the repository)

### AWS Account Requirements
- AWS account with appropriate permissions
- IAM permissions to create:
  - S3 buckets
  - Lambda functions
  - DynamoDB tables
  - IAM roles and policies
  - CloudWatch resources
  - EventBridge rules
  - SES email identities

## Quick Start Deployment

### Step 1: Clone the Repository
```bash
git clone https://github.com/vinaya-cg/certificate-monitor.git
cd certificate-monitor
```

### Step 2: Configure Terraform Variables
Edit `terraform/terraform.tfvars` with your configuration:

```hcl
# AWS Configuration
aws_region = "eu-west-1"  # Change to your preferred region

# Project Configuration
project_name = "cert-management"
environment  = "dev"  # or "prod", "staging", etc.

# Email Configuration
sender_email = "your-email@company.com"  # Must be a valid email for SES

# Owner Tag
owner_tag = "Your-Team-Name"

# Monitoring Configuration
expiry_threshold_days = 30  # Alert when certificate expires within this many days
```

### Step 3: Initialize Terraform
```bash
cd terraform
terraform init
```

### Step 4: Review Deployment Plan
```bash
terraform plan
```

This will show you:
- All resources that will be created
- Estimated monthly costs ($3-10/month)
- Configuration details

### Step 5: Deploy Infrastructure
```bash
terraform apply
```

Type `yes` when prompted to confirm deployment.

**Deployment time:** ~2-3 minutes

### Step 6: Verify SES Email Identity
After deployment, verify your sender email address:

```bash
# AWS will send a verification email to the address you specified
aws ses verify-email-identity --email-address your-email@company.com
```

Check your inbox and click the verification link.

### Step 7: Access Your Dashboard
After deployment completes, Terraform will output the dashboard URL:

```
Dashboard URL: http://cert-management-dev-dashboard-xxxxx.s3-website-{region}.amazonaws.com
API URL: https://xxxxx.lambda-url.{region}.on.aws/
```

## What Gets Deployed

### Infrastructure Components
1. **S3 Buckets (3)**
   - Dashboard hosting (public website)
   - Certificate file uploads
   - CloudWatch logs storage

2. **Lambda Functions (3)**
   - Dashboard API (handles certificate CRUD operations)
   - Excel processor (processes uploaded Excel files)
   - Certificate monitor (daily expiry checks and notifications)

3. **DynamoDB Tables (2)**
   - Certificates table (main data store)
   - Certificate logs table (audit trail)

4. **CloudWatch Resources**
   - Log groups for each Lambda function
   - CloudWatch dashboard for monitoring

5. **EventBridge Rule**
   - Daily schedule for certificate monitoring (9 AM UTC)

6. **IAM Resources**
   - Lambda execution role
   - Necessary policies for DynamoDB, S3, SES access

### Automatic Configuration
The deployment automatically:
- ✅ Uploads all dashboard files to S3
- ✅ Injects the correct API URL into dashboard.js
- ✅ Configures CORS for API access
- ✅ Sets up DynamoDB tables with indexes
- ✅ Creates CloudWatch log groups
- ✅ Configures daily monitoring schedule

## Post-Deployment Steps

### 1. Test the Dashboard
Open the dashboard URL in your browser and verify:
- Dashboard loads correctly
- You can add/view certificates
- Filtering and sorting works

### 2. Upload Initial Certificate Data (Optional)
If you have existing certificates in Excel format:

```bash
aws s3 cp certificates.xlsx s3://cert-management-dev-uploads-xxxxx/excel/certificates.xlsx
```

The Excel processor Lambda will automatically:
- Parse the Excel file
- Import certificates to DynamoDB
- Log the import process

### 3. Test Email Notifications (Optional)
Manually trigger the certificate monitor:

```bash
aws lambda invoke \
  --function-name cert-management-dev-certificate-monitor \
  response.json
```

Check the logs:
```bash
aws logs tail /aws/lambda/cert-management-dev-certificate-monitor --follow
```

## Deploy to Different Environments

### Development Environment
```hcl
# terraform.tfvars
environment = "dev"
project_name = "cert-management"
```

### Production Environment
```hcl
# terraform.tfvars
environment = "prod"
project_name = "cert-management"
```

Each environment creates completely separate resources with different names.

## Deploy to Different AWS Accounts

### Account A (Sandbox)
```bash
# Configure AWS CLI for Account A
aws configure --profile account-a

# Deploy
cd terraform
terraform init
AWS_PROFILE=account-a terraform apply
```

### Account B (Production)
```bash
# Configure AWS CLI for Account B
aws configure --profile account-b

# Deploy
cd terraform
terraform init
AWS_PROFILE=account-b terraform apply
```

## Troubleshooting

### Issue: Dashboard shows "Failed to load certificates"
**Solution:**
1. Check API URL is accessible:
   ```bash
   curl https://your-api-url.lambda-url.region.on.aws/
   ```
2. Verify CORS is configured correctly
3. Check Lambda function logs in CloudWatch

### Issue: Email notifications not working
**Solution:**
1. Verify SES email identity is confirmed
2. Check you're not in SES sandbox mode (limits sending)
3. Review certificate monitor Lambda logs

### Issue: Terraform apply fails
**Solution:**
1. Check AWS credentials are valid:
   ```bash
   aws sts get-caller-identity
   ```
2. Verify IAM permissions
3. Check if bucket names are globally unique

### Issue: API returns 403 Forbidden
**Solution:**
1. Verify Lambda Function URL is configured with auth type "NONE"
2. Check CORS settings in dashboard_api.tf
3. Review Lambda execution role permissions

## Cost Optimization

### Current Costs ($3-10/month)
- S3: ~$0.10-1/month
- DynamoDB: ~$1-5/month (pay-per-request)
- Lambda: ~$0.20-2/month
- CloudWatch: ~$0.50-2/month

### To Reduce Costs:
1. **Reduce CloudWatch retention:**
   ```hcl
   retention_in_days = 7  # Instead of 30
   ```

2. **Use DynamoDB on-demand billing** (already configured)

3. **Disable daily monitoring if not needed:**
   Comment out EventBridge rule in terraform

## Cleanup / Destroy

To completely remove all resources:

```bash
cd terraform
terraform destroy
```

Type `yes` to confirm.

**Note:** This will:
- Delete all S3 buckets and their contents
- Remove all DynamoDB tables and data
- Delete all Lambda functions
- Remove all CloudWatch logs

## Security Considerations

### Current Configuration
- ✅ S3 buckets encrypted at rest
- ✅ DynamoDB point-in-time recovery enabled
- ✅ CloudWatch logging enabled
- ✅ IAM least privilege principle
- ⚠️ Dashboard is publicly accessible (no authentication)
- ⚠️ API endpoint is public (no authentication)

### To Add Authentication
For production use, consider implementing:
1. **CloudFront + AWS Cognito** (user authentication)
2. **API Gateway with API Keys** (API protection)
3. **VPC deployment** (network isolation)

See the previous implementation history for CloudFront + Cognito setup.

## Support

### Get Terraform Outputs
```bash
cd terraform
terraform output
```

### View Resource Details
```bash
# List all deployed resources
terraform state list

# Show specific resource
terraform show aws_lambda_function.dashboard_api
```

### Access Logs
```bash
# Dashboard API logs
aws logs tail /aws/lambda/cert-management-dev-dashboard-api --follow

# Certificate monitor logs
aws logs tail /aws/lambda/cert-management-dev-certificate-monitor --follow

# Excel processor logs
aws logs tail /aws/lambda/cert-management-dev-excel-processor --follow
```

## Next Steps

1. ✅ Customize email templates (in Lambda code)
2. ✅ Adjust monitoring thresholds
3. ✅ Configure custom domain (optional)
4. ✅ Set up additional CloudWatch alarms
5. ✅ Train support team on dashboard usage

---

**Last Updated:** November 8, 2025
**Version:** 2.0
**Terraform Version:** >= 1.0
**AWS Provider Version:** ~> 4.0
