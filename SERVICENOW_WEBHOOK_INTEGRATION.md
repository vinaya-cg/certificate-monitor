# ServiceNow Webhook Integration - Complete Setup Guide

## 📋 Overview

This guide explains how to set up **bidirectional integration** between ServiceNow and the Certificate Management Dashboard. When an engineer picks/assigns a ServiceNow incident, the certificate is automatically updated with:

- **Assignee details** (name, email)
- **Status change** to "Renewal in Progress"  
- **Assignment timestamp**
- **Incident state tracking**

---

## 🏗️ Architecture

```
ServiceNow Incident Assignment
         ↓
ServiceNow Business Rule (triggers webhook)
         ↓
API Gateway (webhook endpoint)
         ↓
Lambda Function (servicenow_webhook_handler)
         ↓
DynamoDB Update (certificates + logs tables)
         ↓
Dashboard Reflects Changes (real-time)
```

---

## 🚀 Deployment Steps

### **Step 1: Deploy Infrastructure**

Add the webhook module to your Terraform configuration:

```hcl
# In terraform/environments/dev-secure/main.tf

# ServiceNow Webhook Handler Module
module "servicenow_webhook" {
  count  = var.enable_servicenow_integration ? 1 : 0
  source = "../../modules/lambda_servicenow_webhook"

  project_name            = var.project_name
  environment             = var.environment
  aws_region              = var.aws_region
  certificates_table_name = module.main.certificates_table_name
  certificates_table_arn  = module.main.certificates_table_arn
  logs_table_name         = module.main.logs_table_name
  logs_table_arn          = module.main.logs_table_arn
  webhook_secret_name     = var.servicenow_webhook_secret_name
  webhook_secret_arn      = var.servicenow_webhook_secret_arn
  log_retention_days      = 30
  enable_alarms           = true
}

output "servicenow_webhook_url" {
  description = "ServiceNow webhook endpoint URL"
  value       = var.enable_servicenow_integration ? module.servicenow_webhook[0].webhook_endpoint : null
}
```

Add variables to `terraform.tfvars`:

```hcl
# ServiceNow webhook integration settings
enable_servicenow_webhook        = true
servicenow_webhook_secret_name   = "cert-management/servicenow/webhook-secret"
servicenow_webhook_secret_arn    = "arn:aws:secretsmanager:eu-west-1:992155623828:secret:cert-management/servicenow/webhook-secret-xxxxxx"
```

### **Step 2: Create Webhook Secret (Optional but Recommended)**

For security, create a shared secret to validate webhooks:

```bash
# Generate a random secret
$SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})

# Create secret in AWS Secrets Manager
aws secretsmanager create-secret `
  --name cert-management/servicenow/webhook-secret `
  --description "Webhook validation secret for ServiceNow integration" `
  --secret-string "{\"webhook_secret\":\"$SECRET\"}" `
  --region eu-west-1

# Save the secret - you'll need it for ServiceNow configuration
Write-Host "Webhook Secret: $SECRET"
```

### **Step 3: Deploy**

```bash
cd terraform/environments/dev-secure
terraform init
terraform plan
terraform apply -auto-approve
```

**Output will include:**
```
servicenow_webhook_url = "https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com/dev-secure/webhook"
```

**Copy this URL** - you'll configure it in ServiceNow.

---

## 🔧 ServiceNow Configuration

### **Step 1: Create Business Rule**

In ServiceNow, create a Business Rule to trigger the webhook when incidents are assigned:

**Navigation:** System Definition → Business Rules → New

**Configuration:**
- **Name:** `Certificate Assignment Webhook`
- **Table:** `Incident [incident]`
- **Active:** ✅ True
- **When:** `after`
- **Insert:** ❌ False
- **Update:** ✅ True
- **Delete:** ❌ False
- **Filter Conditions:**
  ```
  Assigned to CHANGES
  OR
  State CHANGES
  AND
  Correlation ID IS NOT EMPTY
  AND
  Correlation ID STARTS WITH cert-
  ```

**Script:**
```javascript
(function executeRule(current, previous /*null when async*/) {
    
    // Only process incidents related to certificates
    if (!current.correlation_id || !current.correlation_id.toString().startsWith('cert-')) {
        return;
    }
    
    // Prepare webhook payload
    var payload = {
        incident_number: current.number.toString(),
        sys_id: current.sys_id.toString(),
        state: current.state.toString(),
        correlation_id: current.correlation_id.toString(),
        short_description: current.short_description.toString(),
        priority: current.priority.toString(),
        updated_on: current.sys_updated_on.toString()
    };
    
    // Add assigned_to information if available
    if (current.assigned_to) {
        var assignee = current.assigned_to.getRefRecord();
        payload.assigned_to = {
            name: assignee.name.toString(),
            email: assignee.email.toString(),
            sys_id: assignee.sys_id.toString()
        };
    } else {
        payload.assigned_to = {
            name: 'Unassigned',
            email: '',
            sys_id: ''
        };
    }
    
    // Send webhook
    try {
        var request = new sn_ws.RESTMessageV2();
        request.setEndpoint('https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com/dev-secure/webhook'); // Replace with your webhook URL
        request.setHttpMethod('POST');
        request.setRequestHeader('Content-Type', 'application/json');
        
        // Optional: Add signature header for security
        // var secret = gs.getProperty('cert.management.webhook.secret');
        // if (secret) {
        //     var signature = new GlideSPScriptable().getSignature(JSON.stringify(payload), secret);
        //     request.setRequestHeader('X-ServiceNow-Signature', signature);
        // }
        
        request.setRequestBody(JSON.stringify(payload));
        
        var response = request.execute();
        var httpStatus = response.getStatusCode();
        
        gs.info('Certificate webhook sent for ' + current.correlation_id + ' - HTTP ' + httpStatus);
        
        if (httpStatus != 200) {
            gs.error('Certificate webhook failed: ' + response.getBody());
        }
        
    } catch (ex) {
        gs.error('Error sending certificate webhook: ' + ex.message);
    }
    
})(current, previous);
```

**Important:** Replace the endpoint URL with your actual webhook URL from Terraform output.

### **Step 2: Test the Business Rule**

1. Find or create a test incident with `correlation_id` = `cert-12345`
2. Assign it to yourself
3. Check Business Rule execution logs
4. Verify certificate updated in dashboard

---

## 📊 Status Mapping

The integration automatically maps ServiceNow incident states to certificate statuses:

| ServiceNow State | State Number | Certificate Status     |
|------------------|--------------|------------------------|
| New              | 1            | Pending Assignment     |
| In Progress      | 2            | Renewal in Progress    |
| On Hold          | 3            | On Hold                |
| Resolved         | 6            | Renewal Done           |
| Closed           | 7            | Renewal Done           |
| Canceled         | 8            | Renewal Canceled       |

---

## 🔍 Monitoring & Troubleshooting

### **CloudWatch Logs**

Monitor webhook processing:
```bash
aws logs tail /aws/lambda/cert-management-servicenow-webhook-handler --follow --region eu-west-1
```

### **Test Webhook Manually**

```powershell
# Test payload
$payload = @{
    incident_number = "INC0817937"
    sys_id = "abc123"
    state = "2"
    assigned_to = @{
        name = "John Doe"
        email = "john.doe@sogeti.com"
        sys_id = "user123"
    }
    correlation_id = "cert-12345"
    short_description = "Certificate expiring in 7 days"
    priority = "2"
    updated_on = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
} | ConvertTo-Json

# Send webhook
Invoke-RestMethod `
  -Uri "https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com/dev-secure/webhook" `
  -Method POST `
  -Body $payload `
  -ContentType "application/json"
```

### **Check DynamoDB Update**

```bash
# Query certificate to verify update
aws dynamodb get-item `
  --table-name cert-management-dev-secure-certificates `
  --key '{"CertificateID":{"S":"cert-12345"}}' `
  --region eu-west-1
```

### **Common Issues**

**Problem:** Webhook returns 401 Unauthorized
- **Cause:** Signature validation failing
- **Solution:** Disable signature validation in Lambda or configure correct secret in ServiceNow

**Problem:** Certificate not found (404)
- **Cause:** `correlation_id` doesn't match a certificate
- **Solution:** Verify `CertificateID` in DynamoDB matches `correlation_id` in ServiceNow

**Problem:** Webhook not firing
- **Cause:** Business Rule filter conditions not met
- **Solution:** Check incident has `correlation_id` starting with `cert-`

---

## 🔐 Security Considerations

### **Webhook Signature Validation**

For production, enable signature validation:

1. **Configure secret in ServiceNow:**
   ```javascript
   // In ServiceNow System Properties
   // Create property: cert.management.webhook.secret
   // Value: <your-webhook-secret>
   ```

2. **Update Business Rule** to include signature header (uncomment signature code)

3. **Lambda automatically validates** if signature header is present

### **IP Whitelisting (Optional)**

Add IP restrictions to API Gateway if needed:
```hcl
resource "aws_api_gateway_method" "webhook_post" {
  # ... existing config ...
  
  request_parameters = {
    "method.request.header.X-Forwarded-For" = true
  }
}
```

---

## 📈 What Gets Updated

When an engineer picks an incident, the certificate record is updated with:

### **Certificate Table Fields:**
- `AssignedTo` - Engineer's name
- `AssignedToEmail` - Engineer's email
- `AssignedOn` - Assignment timestamp
- `Status` - Updated based on incident state
- `IncidentNumber` - ServiceNow incident number
- `IncidentState` - Incident state code (1-8)
- `IncidentStateText` - Human-readable state
- `LastUpdatedOn` - Update timestamp

### **Logs Table Entry:**
- `Action` - `INCIDENT_IN_PROGRESS`, `INCIDENT_RESOLVED`, etc.
- `Assignee` - Engineer's name
- `AssigneeEmail` - Engineer's email
- `IncidentNumber` - ServiceNow incident number
- `NewStatus` - Updated certificate status
- `Source` - `ServiceNow Webhook`

---

## 🎯 Complete Integration Flow

### **Scenario: Certificate Expiring Soon**

1. **Daily at 9:05 AM UTC:**
   - ServiceNow ticket creator Lambda scans for expiring certificates
   - Creates incident `INC0123456` for certificate `cert-aws-prod-api-12345`
   - Sets `correlation_id` = `cert-aws-prod-api-12345`
   - Updates DynamoDB: `IncidentNumber` = `INC0123456`

2. **Engineer picks ticket (9:30 AM):**
   - Engineer assigns incident to themselves in ServiceNow
   - Business Rule fires webhook to API Gateway
   - Lambda updates certificate:
     - `AssignedTo` = "Sarah Johnson"
     - `AssignedToEmail` = "sarah.johnson@sogeti.com"
     - `Status` = "Renewal in Progress"

3. **Engineer resolves ticket (next day 2:00 PM):**
   - Engineer marks incident as Resolved in ServiceNow
   - Business Rule fires webhook again
   - Lambda updates certificate:
     - `Status` = "Renewal Done"
     - `IncidentState` = "6"

4. **Dashboard reflects changes:**
   - Real-time status updates visible to all users
   - Complete audit trail in logs table
   - Filtering by assignee now possible

---

## 🆘 Support & Next Steps

### **Enable the Integration:**
```bash
# Update terraform.tfvars
enable_servicenow_webhook = true

# Deploy
terraform apply -auto-approve
```

### **Test End-to-End:**
1. Deploy infrastructure
2. Configure ServiceNow Business Rule
3. Manually assign a test incident
4. Verify certificate update in dashboard
5. Check logs for successful webhook processing

### **Production Readiness:**
- ✅ Enable signature validation
- ✅ Configure CloudWatch alarms
- ✅ Test error scenarios (invalid payload, missing fields)
- ✅ Document webhook endpoint for operations team
- ✅ Set up monitoring dashboard

---

**The integration is now fully bidirectional:**
- **AWS → ServiceNow:** Automated ticket creation for expiring certificates
- **ServiceNow → AWS:** Real-time certificate updates when incidents are assigned/updated

Both systems stay in sync automatically! 🎉
