# Server Certificate Scanner Module

This Terraform module deploys the server certificate scanner infrastructure for scanning certificates from Windows and Linux servers using AWS Systems Manager (SSM).

## Features

- **Windows Certificate Scanning**: Scans certificates from `CurrentUser\My` and `LocalMachine\My` stores
- **Linux Certificate Scanning**: Scans certificates from common paths (`/etc/ssl/certs`, `/etc/pki/tls/certs`, etc.)
- **SSM-Based**: Uses AWS Systems Manager Run Command for agent-based scanning
- **Automated Scheduling**: Daily scheduled scans via EventBridge (9:30 AM UTC by default)
- **Manual Triggers**: Can be triggered manually via Lambda invoke
- **Duplicate Prevention**: Uses ServerID + Thumbprint as composite key
- **Data Preservation**: Preserves manually entered fields (OwnerEmail, SupportEmail, Notes)

## Architecture

```
EventBridge Schedule (9:30 AM UTC)
         ↓
Lambda Function (server_certificate_scanner)
         ↓
AWS Systems Manager (SSM)
         ↓
    SSM Documents
    ├── Windows (PowerShell)
    └── Linux (Bash)
         ↓
  EC2 Instances (with SSM Agent)
         ↓
Certificate Stores
├── Windows: Cert:\CurrentUser\My, Cert:\LocalMachine\My
└── Linux: /etc/ssl/certs, /etc/pki/tls/certs, etc.
         ↓
DynamoDB (Certificates Table)
```

## Prerequisites

1. **SSM Agent** must be installed on target servers
2. **EC2 instances** must have IAM role with `AmazonSSMManagedInstanceCore` policy
3. **Managed instances** must show as "Online" in Systems Manager
4. **Lambda execution role** must have SSM permissions

## Usage

```hcl
module "server_certificate_scanner" {
  source = "../../modules/lambda_server_scanner"

  project_name            = var.project_name
  environment             = var.environment
  aws_region              = var.aws_region
  certificates_table_name = module.database.certificates_table_name
  certificates_table_arn  = module.database.certificates_table_arn
  lambda_role_arn         = module.iam.lambda_role_arn
  lambda_role_name        = module.iam.lambda_role_name

  # Optional: Enable scheduled scanning
  enable_scheduled_scan = true
  scan_schedule         = "cron(30 9 * * ? *)"  # Daily at 9:30 AM UTC

  # Optional: CloudWatch alarms
  enable_alarms = true

  # Optional: Log retention
  log_retention_days = 7
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_name | Name of the project | string | - | yes |
| environment | Environment name | string | - | yes |
| aws_region | AWS region | string | - | yes |
| certificates_table_name | DynamoDB table name | string | - | yes |
| certificates_table_arn | DynamoDB table ARN | string | - | yes |
| lambda_role_arn | Lambda execution role ARN | string | - | yes |
| lambda_role_name | Lambda role name | string | - | yes |
| enable_scheduled_scan | Enable automatic scanning | bool | true | no |
| scan_schedule | Cron expression for schedule | string | cron(30 9 * * ? *) | no |
| log_retention_days | CloudWatch log retention | number | 7 | no |
| enable_alarms | Enable CloudWatch alarms | bool | false | no |

## Outputs

| Name | Description |
|------|-------------|
| lambda_function_arn | ARN of the scanner Lambda |
| lambda_function_name | Name of the scanner Lambda |
| windows_ssm_document_name | Windows SSM document name |
| linux_ssm_document_name | Linux SSM document name |
| scan_schedule | EventBridge schedule expression |

## SSM Documents

### Windows Certificate Scan (`windows-certificate-scan.json`)

Scans Windows certificate stores using PowerShell:

```powershell
Get-ChildItem -Path Cert:\CurrentUser\My
Get-ChildItem -Path Cert:\LocalMachine\My
```

**Output Fields**:
- Subject
- Issuer
- Valid From / Valid Until
- Thumbprint
- Serial Number
- Has Private Key

### Linux Certificate Scan (`linux-certificate-scan.json`)

Scans Linux certificate paths using OpenSSL:

```bash
Paths:
- /etc/ssl/certs
- /etc/pki/tls/certs
- /etc/pki/ca-trust/extracted/pem
- /usr/local/share/ca-certificates
- /opt/certificates
- /var/certificates
```

**Output Format**: JSON array of certificate objects

## Manual Execution

### Via AWS CLI

```bash
# Invoke Lambda function manually
aws lambda invoke \
  --function-name cert-management-dev-secure-server-cert-scanner \
  --invocation-type Event \
  response.json

# Check specific server
aws ssm send-command \
  --instance-ids "i-1234567890abcdef0" \
  --document-name "cert-management-dev-secure-windows-cert-scan" \
  --comment "Manual certificate scan"
```

### Via AWS Console

1. Navigate to **Lambda** → `cert-management-dev-secure-server-cert-scanner`
2. Click **Test** tab
3. Click **Invoke** (no event data needed)
4. Check **CloudWatch Logs** for results

## Certificate Data Structure

```json
{
  "CertificateID": "i-1234567890abcdef0_ABC123...",
  "CertificateName": "example.com",
  "CommonName": "example.com",
  "Subject": "CN=example.com, O=Organization",
  "Issuer": "CN=CA, O=CA Org",
  "ExpiryDate": "2025-12-31",
  "Thumbprint": "ABC123...",
  "Status": "Active",
  "Source": "Server-Windows",
  "ServerID": "i-1234567890abcdef0",
  "ServerName": "web-prod-01",
  "ServerPlatform": "Windows Server 2022",
  "ServerIP": "10.0.1.50",
  "Environment": "PROD",
  "LastScannedOn": "2025-11-10T09:30:00Z",
  "SyncedFrom": "SSM",
  "AccountNumber": "123456789012"
}
```

## Environment Detection

Automatically determines environment from server name:
- `prod`, `prd`, `production` → PROD
- `test`, `tst`, `qa`, `uat` → TEST
- `dev`, `development` → DEV
- `stg`, `stage`, `staging` → STAGING

## Data Preservation

Preserves manually entered fields during sync:
- OwnerEmail
- SupportEmail
- Application
- Notes
- RenewalHistory
- CustomTags
- IncidentNumber

## Monitoring

### CloudWatch Logs

Logs available at: `/aws/lambda/cert-management-dev-secure-server-cert-scanner`

**Log Events**:
- Scan start/completion
- Servers discovered
- Certificates found per server
- Errors and warnings

### CloudWatch Alarms (if enabled)

1. **Scanner Errors**: Alerts on Lambda errors
2. **Scanner Duration**: Alerts when approaching timeout (15 min)

### Metrics

View in CloudWatch dashboard:
- Servers scanned
- Certificates found/added/updated
- Scan duration
- Error rate

## Troubleshooting

### No Instances Found

**Issue**: "No managed instances found with SSM agent"

**Solutions**:
1. Verify SSM agent installed on servers
2. Check IAM role has `AmazonSSMManagedInstanceCore`
3. Verify instances show as "Online" in Systems Manager console
4. Check security groups allow SSM endpoints (port 443)

### Command Fails on Instance

**Issue**: SSM command shows "Failed" status

**Solutions**:
1. Check SSM agent is running: `systemctl status amazon-ssm-agent`
2. Review command output in SSM console
3. Verify permissions to read certificate stores
4. Check PowerShell/Bash availability

### No Certificates Found

**Issue**: Scan completes but finds 0 certificates

**Solutions**:
1. Verify certificates exist in scanned locations
2. Check file permissions (Linux)
3. Review SSM command output for errors
4. Ensure certificate format is correct (.crt, .pem, .cer)

### Lambda Timeout

**Issue**: Function times out before completing

**Solutions**:
1. Reduce number of instances scanned per execution
2. Increase Lambda timeout (currently 15 min)
3. Implement pagination for large fleets
4. Run multiple executions for different instance groups

## Security Considerations

1. **IAM Permissions**: Lambda needs SSM execute permissions
2. **Server Access**: SSM uses secure channels (no SSH/RDP needed)
3. **Private Keys**: Not extracted, only certificate metadata
4. **Data in Transit**: SSM commands use TLS encryption
5. **Audit Trail**: All SSM commands logged in CloudTrail

## Cost Estimation

**AWS Systems Manager**:
- SSM Run Command: $0.00 per command (free tier)
- SSM Session Manager: $0.00 (free)

**Lambda**:
- Invocations: ~$0.20/month (1 daily execution)
- Compute: ~$0.001/GB-second

**CloudWatch**:
- Log storage: ~$0.50/month (7-day retention)

**Total**: ~$0.71/month (excluding data transfer)

## Future Enhancements

- [ ] Support for custom certificate paths (configurable)
- [ ] Certificate chain validation
- [ ] Private key detection and warnings
- [ ] Integration with AWS Certificate Manager
- [ ] Support for certificate revocation lists (CRLs)
- [ ] Automatic renewal reminders
- [ ] Cross-account server scanning
- [ ] Export certificates to S3

## Related Documentation

- [Lambda Function Code](../../../lambda/server_certificate_scanner.py)
- [Windows SSM Document](../../../ssm-documents/windows-certificate-scan.json)
- [Linux SSM Document](../../../ssm-documents/linux-certificate-scan.json)
- [SSM Agent Installation Guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-agent.html)

## Support

For issues or questions:
1. Check CloudWatch Logs for error details
2. Verify SSM agent status on target instances
3. Review SSM command history in console
4. Contact infrastructure team for assistance
