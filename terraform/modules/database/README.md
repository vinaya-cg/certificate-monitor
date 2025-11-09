# Database Module

This module creates DynamoDB tables for storing certificate data and audit logs with Global Secondary Indexes for efficient querying.

## Purpose

Provides NoSQL data storage for certificate records and audit trail with flexible querying capabilities and automatic scaling.

## Resources Created

### Certificates Table (`aws_dynamodb_table.certificates`)
- **Name**: `{project_name}-{environment}-certificates`
- **Billing Mode**: PAY_PER_REQUEST (auto-scaling)
- **Partition Key**: `CertificateID` (String)
- **Attributes**:
  - `CertificateID` - Unique identifier (UUID)
  - `CommonName` - Certificate common name (e.g., `*.example.com`)
  - `ExpiryDate` - Expiration date (ISO 8601 format)
  - `Environment` - DEV, TEST, PROD
  - `OwnerEmail` - Certificate owner email
  - `SupportEmail` - Support contact email
  - `Status` - active, expired, expiring-soon, revoked
  - `CreatedAt` - Timestamp
  - `UpdatedAt` - Timestamp

#### Global Secondary Indexes (GSIs)

1. **StatusIndex**
   - Partition Key: `Status`
   - Sort Key: `ExpiryDate`
   - Projection: ALL
   - Use Case: Find all active/expired certificates sorted by expiry

2. **EnvironmentIndex**
   - Partition Key: `Environment`
   - Sort Key: `ExpiryDate`
   - Projection: ALL
   - Use Case: Find all certificates in specific environment

3. **OwnerIndex**
   - Partition Key: `OwnerEmail`
   - Sort Key: `ExpiryDate`
   - Projection: ALL
   - Use Case: Find all certificates owned by specific user

4. **ExpiryIndex**
   - Partition Key: `Status`
   - Sort Key: `ExpiryDate`
   - Projection: ALL
   - Use Case: Find certificates expiring soon

### Certificate Logs Table (`aws_dynamodb_table.certificate_logs`)
- **Name**: `{project_name}-{environment}-certificate-logs`
- **Billing Mode**: PAY_PER_REQUEST
- **Partition Key**: `LogID` (String)
- **Attributes**:
  - `LogID` - Unique identifier (UUID)
  - `Timestamp` - Operation timestamp (ISO 8601)
  - `CertificateID` - Related certificate ID
  - `Action` - CREATE, UPDATE, DELETE, IMPORT
  - `UserEmail` - User who performed action
  - `Changes` - JSON of what changed
  - `IpAddress` - Client IP address

#### Global Secondary Indexes (GSIs)

1. **CertificateIndex**
   - Partition Key: `CertificateID`
   - Sort Key: `Timestamp`
   - Projection: ALL
   - Use Case: View audit trail for specific certificate

2. **ActionIndex**
   - Partition Key: `Action`
   - Sort Key: `Timestamp`
   - Projection: ALL
   - Use Case: Find all operations of specific type

### Encryption
- **Server-Side Encryption**: AWS-managed keys (SSE-S3)
- **Encryption at Rest**: Enabled by default
- **Encryption in Transit**: TLS 1.2+

### Point-in-Time Recovery (PITR)
- **Enabled**: Yes
- **Retention**: 35 days
- **Use Case**: Restore table to any point in last 35 days

### Tags
- **Environment**: {environment}
- **Project**: {project_name}
- **ManagedBy**: Terraform

## Inputs

| Variable | Type | Description | Required |
|----------|------|-------------|----------|
| `project_name` | `string` | Project name prefix | Yes |
| `environment` | `string` | Environment name | Yes |

## Outputs

| Output | Description | Used By |
|--------|-------------|---------|
| `certificates_table_name` | Certificates table name | Lambda functions |
| `certificates_table_arn` | Certificates table ARN | IAM policies |
| `logs_table_name` | Logs table name | Lambda functions |
| `logs_table_arn` | Logs table ARN | IAM policies |

## Example Usage

```hcl
module "database" {
  source = "../../modules/database"

  project_name = var.project_name
  environment  = var.environment
}
```

## Data Model

### Certificate Record Example
```json
{
  "CertificateID": "cert-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "CommonName": "*.example.com",
  "ExpiryDate": "2025-12-31T23:59:59Z",
  "Environment": "PROD",
  "OwnerEmail": "owner@example.com",
  "SupportEmail": "support@example.com",
  "Status": "active",
  "CreatedAt": "2024-01-15T10:30:00Z",
  "UpdatedAt": "2024-06-20T14:45:00Z",
  "IssuerCA": "Let's Encrypt",
  "SerialNumber": "03ABC123...",
  "SubjectAlternativeNames": ["example.com", "www.example.com"]
}
```

### Log Record Example
```json
{
  "LogID": "log-b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "Timestamp": "2024-06-20T14:45:00Z",
  "CertificateID": "cert-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "Action": "UPDATE",
  "UserEmail": "admin@example.com",
  "Changes": {
    "Status": {"old": "active", "new": "expired"},
    "UpdatedAt": {"old": "2024-01-15T10:30:00Z", "new": "2024-06-20T14:45:00Z"}
  },
  "IpAddress": "203.0.113.42"
}
```

## Query Patterns

### Query by Certificate ID (Primary Key)
```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('cert-management-dev-secure-certificates')

response = table.get_item(
    Key={'CertificateID': 'cert-a1b2c3d4-e5f6-7890-abcd-ef1234567890'}
)
certificate = response['Item']
```

### Query by Status (GSI)
```python
response = table.query(
    IndexName='StatusIndex',
    KeyConditionExpression='#status = :status',
    ExpressionAttributeNames={'#status': 'Status'},
    ExpressionAttributeValues={':status': 'active'}
)
certificates = response['Items']
```

### Query Expiring Certificates
```python
from datetime import datetime, timedelta

expiry_threshold = (datetime.now() + timedelta(days=30)).isoformat()

response = table.query(
    IndexName='ExpiryIndex',
    KeyConditionExpression='#status = :status AND ExpiryDate < :expiry',
    ExpressionAttributeNames={'#status': 'Status'},
    ExpressionAttributeValues={
        ':status': 'active',
        ':expiry': expiry_threshold
    }
)
expiring_certs = response['Items']
```

### Query by Environment
```python
response = table.query(
    IndexName='EnvironmentIndex',
    KeyConditionExpression='Environment = :env',
    ExpressionAttributeValues={':env': 'PROD'}
)
prod_certificates = response['Items']
```

### Query Audit Trail for Certificate
```python
logs_table = dynamodb.Table('cert-management-dev-secure-certificate-logs')

response = logs_table.query(
    IndexName='CertificateIndex',
    KeyConditionExpression='CertificateID = :cert_id',
    ExpressionAttributeValues={':cert_id': 'cert-a1b2c3d4-e5f6-7890-abcd-ef1234567890'},
    ScanIndexForward=False  # Descending order (newest first)
)
audit_trail = response['Items']
```

## CRUD Operations

### Create Certificate
```python
import uuid
from datetime import datetime

table.put_item(
    Item={
        'CertificateID': f'cert-{uuid.uuid4()}',
        'CommonName': '*.newcert.com',
        'ExpiryDate': '2026-01-15T23:59:59Z',
        'Environment': 'PROD',
        'OwnerEmail': 'owner@example.com',
        'SupportEmail': 'support@example.com',
        'Status': 'active',
        'CreatedAt': datetime.now().isoformat(),
        'UpdatedAt': datetime.now().isoformat()
    }
)
```

### Read Certificate
```python
response = table.get_item(Key={'CertificateID': 'cert-123'})
if 'Item' in response:
    certificate = response['Item']
else:
    print("Certificate not found")
```

### Update Certificate
```python
table.update_item(
    Key={'CertificateID': 'cert-123'},
    UpdateExpression='SET #status = :status, UpdatedAt = :updated',
    ExpressionAttributeNames={'#status': 'Status'},
    ExpressionAttributeValues={
        ':status': 'expired',
        ':updated': datetime.now().isoformat()
    }
)
```

### Delete Certificate
```python
table.delete_item(Key={'CertificateID': 'cert-123'})
```

### Batch Write
```python
with table.batch_writer() as batch:
    for cert in certificates:
        batch.put_item(Item=cert)
```

## Monitoring

### CloudWatch Metrics
DynamoDB publishes metrics automatically:

- **ConsumedReadCapacityUnits**: Read capacity consumed
- **ConsumedWriteCapacityUnits**: Write capacity consumed
- **UserErrors**: 400-level errors
- **SystemErrors**: 500-level errors
- **ThrottledRequests**: Requests throttled

View metrics:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=cert-management-dev-secure-certificates \
  --start-time 2025-11-08T00:00:00Z \
  --end-time 2025-11-09T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Backup & Recovery

### Point-in-Time Recovery (PITR)
Restore table to any point in last 35 days:

```bash
aws dynamodb restore-table-to-point-in-time \
  --source-table-name cert-management-dev-secure-certificates \
  --target-table-name cert-management-dev-secure-certificates-restored \
  --restore-date-time 2025-11-08T12:00:00Z
```

### On-Demand Backups
Create manual backup:

```bash
aws dynamodb create-backup \
  --table-name cert-management-dev-secure-certificates \
  --backup-name cert-backup-2025-11-09
```

Restore from backup:

```bash
aws dynamodb restore-table-from-backup \
  --target-table-name cert-management-dev-secure-certificates-restored \
  --backup-arn arn:aws:dynamodb:eu-west-1:123456789012:table/cert-management-dev-secure-certificates/backup/01234567890123-abcd1234
```

## Performance Optimization

### PAY_PER_REQUEST vs PROVISIONED
- **PAY_PER_REQUEST**: Auto-scales, pay per request, best for variable workloads
- **PROVISIONED**: Fixed capacity, cheaper for predictable workloads

Current configuration: **PAY_PER_REQUEST** (best for certificate monitoring with variable access patterns)

### GSI Best Practices
- Use sparse indexes (only items with index attributes)
- Project only needed attributes to save storage
- Monitor GSI throttling separately from base table

### Query vs Scan
- **Query**: Fast, uses primary key or GSI (O(log n))
- **Scan**: Slow, reads entire table (O(n))
- **Always use Query when possible**

## Cost Estimation

DynamoDB pricing (PAY_PER_REQUEST):

| Operation | Price | Monthly Usage | Cost |
|-----------|-------|---------------|------|
| Write Requests | $1.25 per million | 100,000 | $0.13 |
| Read Requests | $0.25 per million | 1,000,000 | $0.25 |
| Storage | $0.25 per GB | 1 GB | $0.25 |
| Backup Storage | $0.10 per GB | 1 GB | $0.10 |
| **Total** | | | **~$0.73/month** |

**Note**: First 25 GB storage free, 25 WCU/25 RCU free (AWS Free Tier)

## Troubleshooting

### Issue: ProvisionedThroughputExceededException
**Cause**: Too many requests for PAY_PER_REQUEST mode (rare)  
**Solution**: Implement exponential backoff in application code

### Issue: Query returns no results
**Cause**: Wrong GSI or partition key  
**Solution**: Verify IndexName and KeyConditionExpression match table schema

### Issue: Item size too large
**Cause**: DynamoDB item limit is 400 KB  
**Solution**: Store large data (certificates) in S3, reference in DynamoDB

### Issue: High costs
**Cause**: Excessive scans, unused GSIs  
**Solution**: 
- Replace scans with queries
- Remove unused GSIs
- Consider switching to provisioned capacity

## Best Practices

1. **Partition Key Design**: Use high-cardinality keys (UUID, not status)
2. **GSI Usage**: Create GSIs for common query patterns
3. **Sparse Indexes**: Only index items that need querying
4. **Batch Operations**: Use batch_writer for bulk operations
5. **Error Handling**: Implement retries with exponential backoff
6. **Monitoring**: Set up CloudWatch alarms for throttling
7. **Backup**: Enable PITR for production tables
8. **Encryption**: Always enable encryption at rest

## Dependencies

None (standalone module)

## Related Modules

- **Lambda Secure**: Lambda functions read/write to these tables
- **IAM**: IAM policies grant Lambda access to tables
- **API Gateway**: API endpoints trigger Lambda functions that use these tables

## References

- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [DynamoDB GSIs](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html)
- [DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/)
