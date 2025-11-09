# IAM Module

This module creates IAM roles and policies for Lambda function execution with least-privilege access.

## Purpose

Provides IAM roles with appropriate permissions for Lambda functions to access DynamoDB, S3, SES, and CloudWatch Logs.

## Resources Created

### Lambda Execution Role (`aws_iam_role.lambda`)
- **Name**: `{project_name}-{environment}-lambda-role`
- **Assume Role Policy**: Allows Lambda service to assume this role
- **Attached Policies**:
  - Custom policy (DynamoDB, S3, SES, CloudWatch Logs)
  - AWS managed policy: `AWSLambdaBasicExecutionRole`

### Custom IAM Policy (`aws_iam_policy.lambda_policy`)
Grants permissions for:
- **DynamoDB**: Read/write to certificates and logs tables
- **S3**: Read from uploads bucket
- **SES**: Send emails
- **CloudWatch Logs**: Create log groups/streams, put log events

## Inputs

| Variable | Type | Description | Required |
|----------|------|-------------|----------|
| `project_name` | `string` | Project name prefix | Yes |
| `environment` | `string` | Environment name | Yes |
| `certificates_table_arn` | `string` | Certificates table ARN | Yes |
| `logs_table_arn` | `string` | Logs table ARN | Yes |
| `uploads_bucket_arn` | `string` | Uploads bucket ARN | Yes |
| `sender_email` | `string` | SES verified email | Yes |
| `aws_region` | `string` | AWS region | Yes |

## Outputs

| Output | Description | Used By |
|--------|-------------|---------|
| `lambda_role_arn` | Lambda execution role ARN | Lambda functions |
| `lambda_role_name` | Lambda execution role name | Reference |

## Example Usage

```hcl
module "iam" {
  source = "../../modules/iam"

  project_name           = var.project_name
  environment            = var.environment
  certificates_table_arn = module.database.certificates_table_arn
  logs_table_arn         = module.database.logs_table_arn
  uploads_bucket_arn     = module.storage_secure.uploads_bucket_arn
  sender_email           = var.sender_email
  aws_region             = var.aws_region
}
```

## IAM Policy Document

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:eu-west-1:123456789012:table/cert-management-dev-secure-certificates",
        "arn:aws:dynamodb:eu-west-1:123456789012:table/cert-management-dev-secure-certificates/index/*",
        "arn:aws:dynamodb:eu-west-1:123456789012:table/cert-management-dev-secure-certificate-logs",
        "arn:aws:dynamodb:eu-west-1:123456789012:table/cert-management-dev-secure-certificate-logs/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::cert-management-dev-secure-uploads-dz243x46/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ses:FromAddress": "vinaya-c.nayanegali@capgemini.com"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:eu-west-1:123456789012:log-group:/aws/lambda/cert-management-dev-secure-*"
    }
  ]
}
```

## Permissions Breakdown

### DynamoDB Permissions
- `GetItem`: Read single certificate
- `PutItem`: Create new certificate
- `UpdateItem`: Update existing certificate
- `DeleteItem`: Delete certificate
- `Query`: Query with GSIs
- `Scan`: Full table scan (avoid when possible)
- `BatchWriteItem`: Bulk import from Excel

### S3 Permissions
- `GetObject`: Download uploaded Excel files

### SES Permissions
- `SendEmail`: Send formatted emails
- `SendRawEmail`: Send raw MIME emails
- **Condition**: Can only send from verified sender email

### CloudWatch Logs Permissions
- `CreateLogGroup`: Create log group for Lambda function
- `CreateLogStream`: Create log stream within log group
- `PutLogEvents`: Write log events

## Best Practices

1. **Least Privilege**: Grant only necessary permissions
2. **Resource-Specific**: Use specific ARNs, not wildcards
3. **Conditions**: Add conditions to restrict SES sender
4. **Managed Policies**: Use AWS managed policies when appropriate
5. **Review Regularly**: Audit IAM policies periodically

## References

- [IAM Documentation](https://docs.aws.amazon.com/iam/)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
