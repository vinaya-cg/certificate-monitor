# ServiceNow Credentials Secret Configuration
# This file documents the structure of the Secrets Manager secret

## Secret Name
cert-management/servicenow/credentials

## Secret Structure (JSON)
```json
{
  "instance": "sogetinltest",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "username": "AWSMonitoring.apiUserDev",
  "password": "YOUR_PASSWORD",
  "caller": "AWSMonitoring.apiUserDev",
  "business_service": "PostNL Generic SecOps AWS",
  "service_offering": "PostNL Generic SecOps AWS",
  "company": "PostNL B.V."
}
```

## Field Descriptions

| Field | Description | Example |
|-------|-------------|---------|
| `instance` | ServiceNow instance name (without .service-now.com) | `sogetinltest` |
| `client_id` | OAuth2 client ID | `d3168ff13a90d210d69932fd03ea9695` |
| `client_secret` | OAuth2 client secret | `(Y!!fpXH\|T` |
| `username` | ServiceNow API user | `AWSMonitoring.apiUserDev` |
| `password` | ServiceNow API password | Stored securely |
| `caller` | Default caller for tickets | `AWSMonitoring.apiUserDev` |
| `business_service` | Business service name | `PostNL Generic SecOps AWS` |
| `service_offering` | Service offering | `PostNL Generic SecOps AWS` |
| `company` | Company name in ServiceNow | `PostNL B.V.` |

## AWS CLI Commands to Create Secret

### Create the secret (replace with actual values)
```bash
aws secretsmanager create-secret \
  --name cert-management/servicenow/credentials \
  --description "ServiceNow credentials for certificate management integration" \
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

### Update existing secret
```bash
aws secretsmanager update-secret \
  --secret-id cert-management/servicenow/credentials \
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

### Retrieve secret (for testing)
```bash
aws secretsmanager get-secret-value \
  --secret-id cert-management/servicenow/credentials \
  --region eu-west-1 \
  --query SecretString \
  --output text | jq .
```

### Delete secret (with recovery window)
```bash
aws secretsmanager delete-secret \
  --secret-id cert-management/servicenow/credentials \
  --recovery-window-in-days 7 \
  --region eu-west-1
```

## Security Best Practices

1. **Rotation**: Enable automatic rotation every 90 days
2. **Access**: Limit access to Lambda execution role only
3. **Audit**: Enable CloudTrail logging for secret access
4. **Encryption**: Use KMS customer-managed key (optional)

## Terraform Resource (if creating via Terraform)

```hcl
resource "aws_secretsmanager_secret" "servicenow_credentials" {
  name        = "cert-management/servicenow/credentials"
  description = "ServiceNow credentials for certificate management integration"

  tags = {
    Name        = "cert-management-servicenow-credentials"
    Environment = "dev-secure"
    Component   = "ServiceNow Integration"
  }
}

resource "aws_secretsmanager_secret_version" "servicenow_credentials" {
  secret_id = aws_secretsmanager_secret.servicenow_credentials.id
  secret_string = jsonencode({
    instance          = "sogetinltest"
    client_id         = var.servicenow_client_id
    client_secret     = var.servicenow_client_secret
    username          = var.servicenow_username
    password          = var.servicenow_password
    caller            = "AWSMonitoring.apiUserDev"
    business_service  = "PostNL Generic SecOps AWS"
    service_offering  = "PostNL Generic SecOps AWS"
    company           = "PostNL B.V."
  })
}
```

## Testing Secret Access

Create a test Lambda or use existing one to verify access:

```python
import boto3
import json

secrets_client = boto3.client('secretsmanager', region_name='eu-west-1')

try:
    response = secrets_client.get_secret_value(
        SecretId='cert-management/servicenow/credentials'
    )
    credentials = json.loads(response['SecretString'])
    print(f"Successfully retrieved credentials for instance: {credentials['instance']}")
except Exception as e:
    print(f"Error: {str(e)}")
```

## Cost

- **Storage**: $0.40/month per secret
- **API Calls**: $0.05 per 10,000 API calls
- **Estimated monthly cost**: ~$0.40 (assuming 100-200 API calls/month)
