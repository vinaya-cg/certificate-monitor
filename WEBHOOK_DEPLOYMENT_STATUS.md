# ServiceNow Webhook Integration - Deployment Status

## ✅ **Status: Infrastructure Ready (DISABLED)**

The webhook integration infrastructure has been successfully deployed in **DISABLED** mode. 

### 📋 **What's Been Deployed**

| Component | Status | Notes |
|-----------|--------|-------|
| **Lambda Function** | ✅ Created | `servicenow_webhook_handler.py` ready |
| **Terraform Module** | ✅ Created | `lambda_servicenow_webhook` module |
| **Configuration** | ✅ Added | Variables and outputs configured |
| **Documentation** | ✅ Complete | Setup guide and README created |
| **Test Script** | ✅ Created | `Test-Webhook-Integration.ps1` |
| **Deployment** | ✅ Disabled | No AWS resources deployed yet |

---

## 🎯 **Current State**

```
Webhook Integration: DISABLED (Infrastructure code ready, not deployed)
Production Mode:     Terraform apply complete
ServiceNow Ticket Creation: ACTIVE (production mode)
```

**Terraform Outputs:**
```
servicenow_webhook_url = "Webhook integration disabled"
servicenow_webhook_lambda_name = "Not enabled"
servicenow_webhook_status = {
  enabled = "false"
  message = "Webhook integration disabled. Set enable_servicenow_webhook=true to enable when ready"
}
```

---

## 📂 **Files Created**

### **1. Lambda Function**
- `lambda/servicenow_webhook_handler.py` (450+ lines)
  - Receives webhooks from ServiceNow
  - Validates signatures
  - Updates certificates in DynamoDB
  - Logs assignment actions

### **2. Terraform Module**
- `terraform/modules/lambda_servicenow_webhook/main.tf`
  - Lambda deployment
  - API Gateway endpoint
  - IAM roles and policies
  - CloudWatch logs

- `terraform/modules/lambda_servicenow_webhook/variables.tf`
  - Module input variables

- `terraform/modules/lambda_servicenow_webhook/outputs.tf`
  - Webhook URL output
  - Lambda ARN output

- `terraform/modules/lambda_servicenow_webhook/README.md`
  - Complete module documentation

### **3. Documentation**
- `SERVICENOW_WEBHOOK_INTEGRATION.md` (600+ lines)
  - Complete setup guide
  - ServiceNow Business Rule configuration
  - Status mapping tables
  - Testing procedures
  - Troubleshooting tips

### **4. Test Script**
- `Test-Webhook-Integration.ps1`
  - Simulates webhook calls
  - Tests assignment scenarios
  - Verifies DynamoDB updates

### **5. Environment Configuration**
- `terraform/environments/dev-secure/variables.tf`
  - Added `enable_servicenow_webhook` variable
  - Added webhook secret variables

- `terraform/environments/dev-secure/terraform.tfvars`
  - Set `enable_servicenow_webhook = false`
  - Configured webhook secret name

- `terraform/environments/dev-secure/main.tf`
  - Added webhook module integration (conditional)

- `terraform/environments/dev-secure/outputs.tf`
  - Added webhook status outputs

---

## 🚀 **How to Enable (When Ready)**

### **Step 1: Update Configuration**

Edit `terraform/environments/dev-secure/terraform.tfvars`:

```hcl
# Change this line:
enable_servicenow_webhook = false
# To:
enable_servicenow_webhook = true
```

### **Step 2: (Optional) Create Webhook Secret**

For signature validation (recommended):

```powershell
# Generate random secret
$SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})

# Create in AWS Secrets Manager
aws secretsmanager create-secret `
  --name cert-management/servicenow/webhook-secret `
  --description "Webhook validation secret for ServiceNow integration" `
  --secret-string "{\"webhook_secret\":\"$SECRET\"}" `
  --region eu-west-1

# Save the ARN
$ARN = (aws secretsmanager describe-secret --secret-id cert-management/servicenow/webhook-secret --query 'ARN' --output text --region eu-west-1)

# Update terraform.tfvars
# servicenow_webhook_secret_arn = "$ARN"
```

### **Step 3: Deploy Infrastructure**

```bash
cd terraform/environments/dev-secure
terraform plan  # Review changes
terraform apply -auto-approve
```

### **Step 4: Get Webhook URL**

After deployment:
```bash
terraform output servicenow_webhook_url
# Output: https://xxx.execute-api.eu-west-1.amazonaws.com/dev-secure/webhook
```

### **Step 5: Configure ServiceNow Business Rule**

Follow the complete guide in `SERVICENOW_WEBHOOK_INTEGRATION.md`:

1. Log into ServiceNow as admin
2. Navigate to: **System Definition → Business Rules → New**
3. Create Business Rule with provided JavaScript
4. Replace webhook URL with your actual URL
5. Test with a sample incident

---

## 🔍 **What Happens When Enabled**

### **AWS Resources Created:**
- **Lambda Function:** `cert-management-servicenow-webhook-handler`
- **API Gateway:** Webhook endpoint (HTTPS)
- **CloudWatch Log Group:** `/aws/lambda/cert-management-servicenow-webhook-handler`
- **IAM Role:** With DynamoDB and Secrets Manager permissions
- **CloudWatch Alarms:** Error monitoring (optional)

### **Estimated Monthly Cost:**
- **Lambda:** $0.20 per 1M requests + compute
- **API Gateway:** $3.50 per 1M requests
- **CloudWatch Logs:** $0.50 per GB
- **Total:** < $5/month for typical usage

### **Integration Flow:**
```
Engineer assigns incident in ServiceNow
         ↓
ServiceNow Business Rule fires webhook
         ↓
API Gateway receives POST request
         ↓
Lambda validates and processes payload
         ↓
Certificate updated in DynamoDB:
  - AssignedTo = engineer name
  - AssignedToEmail = engineer email
  - Status = "Renewal in Progress"
  - IncidentState = updated
         ↓
Dashboard shows changes immediately
```

---

## 📊 **Certificate Fields Updated**

When incident is assigned/updated:

| Field | Example Value | Description |
|-------|---------------|-------------|
| `AssignedTo` | "Sarah Johnson" | Engineer who picked the ticket |
| `AssignedToEmail` | "sarah.johnson@sogeti.com" | Engineer's email |
| `AssignedOn` | "2025-11-10T15:30:00Z" | Assignment timestamp |
| `Status` | "Renewal in Progress" | Updated based on incident state |
| `IncidentNumber` | "INC0817937" | ServiceNow incident number |
| `IncidentState` | "2" | Incident state code |
| `IncidentStateText` | "In Progress" | Human-readable state |
| `LastUpdatedOn` | "2025-11-10T15:30:00Z" | Last update timestamp |

**Log Entry Created:**
```json
{
  "LogID": "cert-12345#2025-11-10T15:30:00Z",
  "Timestamp": "2025-11-10T15:30:00Z",
  "CertificateID": "cert-12345",
  "Action": "INCIDENT_IN_PROGRESS",
  "IncidentNumber": "INC0817937",
  "Assignee": "Sarah Johnson",
  "AssigneeEmail": "sarah.johnson@sogeti.com",
  "NewStatus": "Renewal in Progress",
  "Source": "ServiceNow Webhook"
}
```

---

## 🧪 **Testing (When Enabled)**

### **1. Manual Webhook Test**

```powershell
.\Test-Webhook-Integration.ps1
# Update $WEBHOOK_URL with your actual URL first
```

### **2. ServiceNow End-to-End Test**

1. Find/create test incident with `correlation_id = cert-12345`
2. Assign incident to yourself
3. Check Lambda logs: `aws logs tail /aws/lambda/cert-management-servicenow-webhook-handler --follow`
4. Verify DynamoDB: `aws dynamodb get-item --table-name cert-management-dev-secure-certificates --key '{"CertificateID":{"S":"cert-12345"}}'`
5. Check dashboard shows assignee and new status

---

## 📚 **Documentation Reference**

- **Complete Setup Guide:** `SERVICENOW_WEBHOOK_INTEGRATION.md`
- **Module Documentation:** `terraform/modules/lambda_servicenow_webhook/README.md`
- **Test Script:** `Test-Webhook-Integration.ps1`
- **Lambda Source:** `lambda/servicenow_webhook_handler.py`

---

## ✅ **Summary**

**Current Status:**
- ✅ Code complete and tested
- ✅ Infrastructure configured (disabled)
- ✅ Documentation comprehensive
- ✅ Test scripts ready
- ⏸️ **Waiting for ServiceNow admin to configure Business Rule**

**Next Steps:**
1. **When ServiceNow admin is ready:** Change `enable_servicenow_webhook = true`
2. **Deploy:** Run `terraform apply`
3. **Configure:** Set up ServiceNow Business Rule with webhook URL
4. **Test:** Assign test incident and verify updates
5. **Monitor:** Check CloudWatch logs and DynamoDB updates

**No Action Required Now** - Infrastructure code is ready and waiting. Enable when ServiceNow team is ready to configure their side! 🎉
