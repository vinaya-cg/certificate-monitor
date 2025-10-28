# Certificate Management Dashboard

A complete certificate monitoring and management system built on AWS with automated Excel processing, real-time status tracking, and email notifications.

## 🎯 **System Overview**

This system provides:
- **Automated Excel Processing**: Upload Excel files → Lambda processes → DynamoDB populated
- **Real-time Dashboard**: View all certificates with status, expiry dates, and filtering
- **Automated Monitoring**: Daily Lambda scans for expiring certificates (30-day threshold)
- **Email Notifications**: Automatic alerts to certificate owners and support teams
- **Manual Workflow**: Support team can update status, add incident numbers, upload renewals
- **Complete Audit Trail**: All changes logged with timestamps and details

## 🏗️ **Architecture**

```
Excel Upload → S3 → Lambda Processor → DynamoDB → Dashboard (S3)
                                    ↓
              Daily Monitor Lambda → Email Notifications (SES)
                                    ↓
                            Certificate Logs Table
```

### **Certificate Status Workflow**
1. **Active** → **Due for Renewal** (30 days before expiry)
2. **Due for Renewal** → **Renewal in Progress** (manual update by support)
3. **Renewal in Progress** → **Renewal Done** (after certificate upload)
4. **Renewal Done** → **Active** (new certificate becomes active)

## 📋 **Prerequisites**

- AWS CLI configured with appropriate permissions
- Terraform >= 1.0
- Email address for SES notifications
- Excel file with certificate data

### **Required AWS Permissions**
- S3: CreateBucket, PutObject, GetObject, DeleteObject
- DynamoDB: CreateTable, PutItem, GetItem, Query, Scan
- Lambda: CreateFunction, InvokeFunction, UpdateFunctionCode
- IAM: CreateRole, AttachRolePolicy, PassRole
- SES: VerifyEmailIdentity, SendEmail
- CloudWatch: CreateLogGroup, PutEvents, CreateDashboard

## 🚀 **Quick Deployment**

### **1. Configure Email**
Edit `terraform.tfvars`:
```hcl
sender_email = "certificates@yourcompany.com"  # Update this!
```

### **2. Deploy Infrastructure**
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### **3. Verify SES Email**
```bash
aws ses verify-email-identity --email-address certificates@yourcompany.com --region eu-west-1
```

### **4. Upload Dashboard Files**
```bash
# Get the dashboard bucket name from terraform output
DASHBOARD_BUCKET=$(terraform output -raw dashboard_bucket_name)

# Upload dashboard files
aws s3 cp ../dashboard/index.html s3://$DASHBOARD_BUCKET/
aws s3 cp ../dashboard/dashboard.js s3://$DASHBOARD_BUCKET/
```

### **5. Upload Excel File**
```bash
# Get the uploads bucket name
UPLOADS_BUCKET=$(terraform output -raw uploads_bucket_name)

# Upload your Excel file (triggers automatic processing)
aws s3 cp "your-certificates.xlsx" s3://$UPLOADS_BUCKET/excel/certificates.xlsx
```

### **6. Access Dashboard**
```bash
# Get dashboard URL
terraform output dashboard_website_url
```

## 📊 **Excel File Format**

Your Excel file should contain these columns (flexible column names supported):

| Column | Required | Description |
|--------|----------|-------------|
| Certificate Name | Yes | Domain or certificate identifier |
| Expiry Date | Yes | Certificate expiration date |
| Environment | Yes | Production, Test, Development, etc. |
| Application | Yes | Application or service name |
| Owner Email | Yes | Certificate owner's email |
| Support Email | No | Support team email |
| Type | No | SSL/TLS, Code Signing, etc. |
| Account Number | No | Account or cost center |
| Status | No | Will be calculated automatically |

### **Supported Column Name Variations**
- **Certificate Name**: certificate_name, cert_name, name, domain
- **Expiry Date**: exp_date, expiration_date, expires
- **Owner Email**: owner_email, owner, contact_email
- **Environment**: env, stage
- **Application**: app, service, system

## 🔧 **Configuration Options**

### **Email Settings**
```hcl
# In terraform.tfvars
sender_email = "certificates@yourcompany.com"
expiry_threshold_days = 30  # Days before expiry to send alerts
monitoring_schedule = "cron(0 9 * * ? *)"  # Daily at 9 AM UTC
```

### **Environment Settings**
```hcl
environment = "dev"    # dev, test, prod
aws_region = "eu-west-1"
project_name = "cert-management"
```

### **Cost Optimization**
```hcl
log_retention_days = 30        # CloudWatch log retention
lambda_memory_size = 512       # Lambda memory in MB
enable_cost_optimization = true
```

## 📈 **Usage Examples**

### **1. Upload New Certificates**
```bash
# Upload Excel file - triggers automatic processing
aws s3 cp certificates.xlsx s3://your-uploads-bucket/excel/certificates.xlsx

# Monitor processing
aws logs tail /aws/lambda/cert-management-dev-excel-processor --follow
```

### **2. Manual Certificate Monitoring**
```bash
# Trigger certificate monitoring manually
aws lambda invoke --function-name cert-management-dev-certificate-monitor \
  --region eu-west-1 response.json

# Check results
cat response.json
```

### **3. Check Certificate Status**
```bash
# Query certificates by status
aws dynamodb query --table-name cert-management-dev-certificates \
  --index-name StatusIndex \
  --key-condition-expression "Status = :status" \
  --expression-attribute-values '{":status":{"S":"Due for Renewal"}}'
```

### **4. Dashboard Operations**
- **View Certificates**: Access dashboard URL from terraform output
- **Add New Certificate**: Click "Add Certificate" button
- **Update Status**: Click status button on certificate row
- **Upload Excel**: Click "Upload Excel" button
- **Export Data**: Click "Export" button for CSV download

## 🔍 **Monitoring and Troubleshooting**

### **CloudWatch Logs**
```bash
# Excel processing logs
aws logs tail /aws/lambda/cert-management-dev-excel-processor

# Certificate monitoring logs
aws logs tail /aws/lambda/cert-management-dev-certificate-monitor

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/cert-management-dev-excel-processor \
  --filter-pattern "ERROR"
```

### **DynamoDB Queries**
```bash
# Count all certificates
aws dynamodb scan --table-name cert-management-dev-certificates --select "COUNT"

# Get certificates expiring soon
aws dynamodb query --table-name cert-management-dev-certificates \
  --index-name StatusIndex \
  --key-condition-expression "Status = :status" \
  --expression-attribute-values '{":status":{"S":"Due for Renewal"}}'
```

### **S3 Operations**
```bash
# List uploaded files
aws s3 ls s3://your-uploads-bucket/excel/ --recursive

# Check dashboard files
aws s3 ls s3://your-dashboard-bucket/
```

## 🔒 **Security Features**

- **IAM Roles**: Minimal permissions for Lambda functions
- **S3 Encryption**: AES-256 encryption for uploaded files
- **DynamoDB**: Point-in-time recovery enabled
- **VPC Support**: Can be deployed in VPC for additional security
- **Audit Trail**: Complete logging of all operations

## 💰 **Cost Estimation**

**Estimated Monthly Costs (USD):**
- DynamoDB: $1-5 (pay-per-request)
- Lambda: $0.20-2 (daily monitoring + processing)
- S3: $0.10-1 (storage and requests)
- CloudWatch: $0.50-2 (logs and monitoring)
- SES: $0.10 per 1,000 emails
- **Total: ~$2-10/month** for typical usage

## 🔧 **Common Issues**

### **1. Email Notifications Not Working**
```bash
# Check SES verification
aws ses get-identity-verification-attributes \
  --identities certificates@yourcompany.com

# Verify email if needed
aws ses verify-email-identity \
  --email-address certificates@yourcompany.com
```

### **2. Excel Processing Fails**
```bash
# Check file was uploaded correctly
aws s3 ls s3://your-uploads-bucket/excel/

# Check Lambda logs for errors
aws logs tail /aws/lambda/cert-management-dev-excel-processor --start-time 1h
```

### **3. Dashboard Not Loading**
```bash
# Check dashboard files are uploaded
aws s3 ls s3://your-dashboard-bucket/

# Test S3 website endpoint
curl -I $(terraform output -raw dashboard_website_url)
```

## 📚 **API Reference**

### **Certificate Status Values**
- `Active`: Certificate is valid and not expiring soon
- `Due for Renewal`: Certificate expires within 30 days
- `Renewal in Progress`: Support team is working on renewal
- `Renewal Done`: New certificate ready to be activated
- `Expired`: Certificate has already expired

### **Email Notification Triggers**
- Daily scan at 9 AM UTC
- Certificates expiring within 30 days
- Status changes (logged)
- Processing completion/errors

### **Log Entry Types**
- `INITIAL_IMPORT`: Certificate imported from Excel
- `STATUS_CHANGED`: Manual status update
- `EMAIL_NOTIFICATION_SENT`: Notification sent
- `CERTIFICATE_RENEWED`: New certificate uploaded

## 🆘 **Support**

### **Getting Help**
1. Check CloudWatch logs for detailed error information
2. Verify AWS permissions and service limits
3. Test individual components (Lambda, SES, DynamoDB)
4. Review configuration in terraform.tfvars

### **Cleanup**
```bash
# Remove all resources
terraform destroy

# Manually clean up any remaining S3 objects if needed
aws s3 rm s3://your-bucket-name --recursive
```

## 📞 **Contact**

- **Dashboard**: Access via terraform output URL
- **Logs**: CloudWatch Logs in AWS Console
- **Monitoring**: CloudWatch Dashboard (cert-management-dev-dashboard)

---

**🎉 Your certificate management system is ready!**

The system automatically processes certificates from Excel, monitors expiry dates, sends notifications, and provides a comprehensive dashboard for certificate lifecycle management.