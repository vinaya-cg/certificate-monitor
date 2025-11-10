# ServiceNow Integration - Quick Reference

## 🚀 Quick Start

### 1. Create Secret (One-time setup)
```bash
aws secretsmanager create-secret \
  --name cert-management/servicenow/credentials \
  --secret-string '{
    "instance": "sogetinltest",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "username": "AWSMonitoring.apiUserDev",
    "password": "YOUR_PASSWORD",
    "caller": "AWSMonitoring.apiUserDev",
    "business_service": "PostNL Generic SecOps AWS",
    "service_offering": "PostNL Generic SecOps AWS",
    "company": "PostNL B.V."
  }' \
  --region eu-west-1
```

### 2. Update terraform.tfvars
```hcl
enable_servicenow_integration = true
servicenow_secret_arn         = "arn:aws:secretsmanager:eu-west-1:992155623828:secret:cert-management/servicenow/credentials-AbCdEf"
servicenow_dry_run            = "true"  # Start in dry-run mode
```

### 3. Deploy
```bash
cd terraform/environments/dev-secure
terraform init
terraform plan
terraform apply
```

### 4. Test
```bash
# Manual invocation
aws lambda invoke \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --payload '{}' \
  response.json

# Check logs
aws logs tail /aws/lambda/cert-management-dev-secure-servicenow-ticket-creator --follow
```

### 5. Enable Production
```hcl
servicenow_dry_run = "false"  # Disable dry-run
```
```bash
terraform apply
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `lambda/servicenow_ticket_creator.py` | Lambda function code (600+ lines) |
| `terraform/modules/lambda_servicenow/main.tf` | Terraform module infrastructure |
| `terraform/modules/lambda_servicenow/variables.tf` | Module input variables |
| `terraform/modules/lambda_servicenow/outputs.tf` | Module outputs |
| `terraform/modules/lambda_servicenow/README.md` | Module documentation |
| `terraform/modules/lambda_servicenow/SECRETS_MANAGER_CONFIG.md` | Secret configuration guide |
| `SERVICENOW_DEPLOYMENT_GUIDE.md` | Complete deployment guide |

---

## ⚙️ Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `enable_servicenow_integration` | `false` | Master on/off switch |
| `servicenow_dry_run` | `"true"` | Prevent actual ticket creation |
| `servicenow_enable_schedule` | `true` | Enable automatic daily execution |
| `servicenow_schedule` | `cron(5 9 * * ? *)` | Daily at 9:05 AM UTC |
| `servicenow_enable_alarms` | `false` | Enable CloudWatch alarms |
| `expiry_threshold_days` | `30` | Days before expiry to create tickets |

---

## 🎯 Priority Mapping

| Days Left | Priority | Label |
|-----------|----------|-------|
| Expired | 1 | CRITICAL |
| < 7 | 2 | HIGH |
| 7-14 | 3 | MEDIUM |
| 15-30 | 4 | LOW |
| > 30 | 5 | PLANNING |

---

## 🔍 Monitoring Commands

### Check Lambda Status
```bash
aws lambda get-function \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --query 'Configuration.{State:State,Runtime:Runtime,Timeout:Timeout}'
```

### View Logs
```bash
aws logs tail /aws/lambda/cert-management-dev-secure-servicenow-ticket-creator --follow
```

### Check EventBridge Rule
```bash
aws events describe-rule \
  --name cert-management-dev-secure-servicenow-schedule
```

### Query Ticket Creation History
```bash
aws dynamodb query \
  --table-name cert-management-dev-secure-logs \
  --filter-expression "Action = :action" \
  --expression-attribute-values '{":action":{"S":"SERVICENOW_TICKET_CREATED"}}'
```

---

## 🚨 Emergency Disable

### Option 1: Disable EventBridge (Fastest)
```bash
aws events disable-rule \
  --name cert-management-dev-secure-servicenow-schedule
```

### Option 2: Enable Dry-Run
```bash
aws lambda update-function-configuration \
  --function-name cert-management-dev-secure-servicenow-ticket-creator \
  --environment "Variables={DRY_RUN=true,...}"
```

### Option 3: Terraform Disable (Cleanest)
```hcl
enable_servicenow_integration = false
```
```bash
terraform apply -auto-approve
```

---

## ✅ Verification Checklist

- [ ] Secrets Manager secret created
- [ ] terraform.tfvars updated with secret ARN
- [ ] `terraform apply` successful
- [ ] Lambda function shows "Active" state
- [ ] EventBridge rule enabled
- [ ] Dry-run test successful
- [ ] ServiceNow test ticket created
- [ ] IncidentNumber updated in DynamoDB
- [ ] Existing cert monitor still works
- [ ] Email notifications unchanged

---

## 🐛 Common Issues

| Issue | Fix |
|-------|-----|
| No tickets created | Check `DRY_RUN=false` |
| 401 Unauthorized | Update ServiceNow credentials in secret |
| Duplicate tickets | Verify DynamoDB UpdateItem permission |
| Schedule not running | Enable EventBridge rule |
| Missing logs | Check Lambda execution role |

---

## 📊 Expected Behavior

### Dry-Run Mode
- ✅ Lambda executes
- ✅ Scans certificates
- ✅ Logs "would create ticket"
- ❌ No API calls to ServiceNow
- ❌ No DynamoDB updates

### Production Mode
- ✅ Lambda executes
- ✅ Scans certificates
- ✅ Creates ServiceNow tickets
- ✅ Updates DynamoDB IncidentNumber
- ✅ Logs all actions

---

## 📈 Success Metrics

After 1 week in production:

- [ ] All expiring certs have ServiceNow tickets
- [ ] Zero duplicate tickets created
- [ ] Ticket priorities match urgency
- [ ] No Lambda errors in CloudWatch
- [ ] Existing email notifications still sent
- [ ] Certificate monitor unchanged
- [ ] Average Lambda duration < 30s

---

## 📞 Support

1. **Check CloudWatch Logs** - 90% of issues visible here
2. **Review Deployment Guide** - Detailed troubleshooting steps
3. **Test in Dry-Run** - Safe testing without tickets
4. **Rollback if needed** - Use feature flag to disable

---

## 🔗 Documentation Links

- [Full Deployment Guide](./SERVICENOW_DEPLOYMENT_GUIDE.md)
- [Module README](./terraform/modules/lambda_servicenow/README.md)
- [Secrets Manager Config](./terraform/modules/lambda_servicenow/SECRETS_MANAGER_CONFIG.md)
- [Inspector Integration (Reference)](./INSPECTOR_SERVICENOW_INTEGRATION.md)

---

**Version:** 1.0.0  
**Last Updated:** November 10, 2025  
**Status:** Ready for Deployment
