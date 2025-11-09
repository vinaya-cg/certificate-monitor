# API Gateway Module

This module creates a REST API with AWS API Gateway and Cognito authorization for secure certificate management operations.

## Purpose

Provides a RESTful API for CRUD operations on certificates with JWT-based authentication and authorization using Cognito User Pool.

## Resources Created

### REST API (`aws_apigatewayv2_api.main`)
- **Protocol**: HTTP API (API Gateway v2)
- **CORS**: Configured for CloudFront domain
- **Name**: `{project_name}-{environment}-api`

### Cognito Authorizer (`aws_apigatewayv2_authorizer.cognito`)
- **Type**: JWT authorizer
- **Identity Source**: `$request.header.Authorization`
- **JWT Configuration**:
  - **Audience**: Cognito Client ID
  - **Issuer**: Cognito User Pool URL
- **Authorization**: Validates JWT tokens on every request

### API Routes
All routes use `/certificates` resource path with different HTTP methods:

- **GET /certificates** - List/search certificates
- **POST /certificates** - Create new certificate
- **PUT /certificates/{id}** - Update certificate
- **DELETE /certificates/{id}** - Delete certificate
- **OPTIONS /certificates** - CORS preflight

### Lambda Integration (`aws_apigatewayv2_integration.dashboard_api`)
- **Type**: AWS_PROXY
- **Integration Method**: POST
- **Target**: dashboard-api Lambda function
- **Payload Format**: 2.0

### API Stage (`aws_apigatewayv2_stage.main`)
- **Name**: `{environment}`
- **Auto Deploy**: `true`
- **Access Logging**: Enabled (CloudWatch Logs)
- **Throttling**:
  - Burst Limit: 5000 requests
  - Rate Limit: 10000 requests/second

### Lambda Permission (`aws_lambda_permission.api_gateway`)
- **Action**: `lambda:InvokeFunction`
- **Principal**: `apigateway.amazonaws.com`
- **Source ARN**: API Gateway execution ARN

## Inputs

| Variable | Type | Description | Required |
|----------|------|-------------|----------|
| `project_name` | `string` | Project name prefix | Yes |
| `environment` | `string` | Environment name | Yes |
| `cognito_user_pool_id` | `string` | Cognito User Pool ID for authorization | Yes |
| `cognito_client_id` | `string` | Cognito Client ID for JWT validation | Yes |
| `lambda_function_arn` | `string` | dashboard-api Lambda function ARN | Yes |
| `lambda_function_name` | `string` | dashboard-api Lambda function name | Yes |
| `cloudfront_domain` | `string` | CloudFront domain for CORS | Yes |
| `aws_region` | `string` | AWS region | Yes |

## Outputs

| Output | Description | Used By |
|--------|-------------|---------|
| `api_gateway_id` | API Gateway ID | Monitoring, logging |
| `api_gateway_url` | API Gateway invoke URL | Dashboard JavaScript configuration |

## Example Usage

```hcl
module "api_gateway" {
  source = "../../modules/api_gateway"

  project_name          = var.project_name
  environment           = var.environment
  cognito_user_pool_id  = module.cognito.user_pool_id
  cognito_client_id     = module.cognito.client_id
  lambda_function_arn   = module.lambda_secure.dashboard_api_function_arn
  lambda_function_name  = module.lambda_secure.dashboard_api_function_name
  cloudfront_domain     = module.cloudfront.distribution_domain_name
  aws_region            = var.aws_region
}
```

## API Endpoints

### GET /certificates
**Purpose**: List or search certificates

**Request**:
```http
GET /dev-secure/certificates HTTP/1.1
Host: 8clm33qmf9.execute-api.eu-west-1.amazonaws.com
Authorization: Bearer <JWT_TOKEN>
```

**Query Parameters** (optional):
- `status` - Filter by status (active, expired, expiring-soon)
- `environment` - Filter by environment (DEV, TEST, PROD)
- `owner` - Filter by owner email
- `search` - Search by common name

**Response**:
```json
{
  "certificates": [
    {
      "CertificateID": "cert-123",
      "CommonName": "*.example.com",
      "ExpiryDate": "2025-12-31",
      "Environment": "PROD",
      "OwnerEmail": "owner@example.com",
      "Status": "active"
    }
  ]
}
```

### POST /certificates
**Purpose**: Create new certificate

**Request**:
```http
POST /dev-secure/certificates HTTP/1.1
Host: 8clm33qmf9.execute-api.eu-west-1.amazonaws.com
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "CommonName": "*.newcert.com",
  "ExpiryDate": "2026-01-15",
  "Environment": "PROD",
  "OwnerEmail": "owner@example.com",
  "SupportEmail": "support@example.com",
  "Status": "active"
}
```

**Response**:
```json
{
  "message": "Certificate created successfully",
  "certificateId": "cert-456"
}
```

### PUT /certificates/{id}
**Purpose**: Update existing certificate

**Request**:
```http
PUT /dev-secure/certificates/cert-123 HTTP/1.1
Host: 8clm33qmf9.execute-api.eu-west-1.amazonaws.com
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "Status": "expired",
  "ExpiryDate": "2025-12-31"
}
```

**Response**:
```json
{
  "message": "Certificate updated successfully"
}
```

### DELETE /certificates/{id}
**Purpose**: Delete certificate

**Request**:
```http
DELETE /dev-secure/certificates/cert-123 HTTP/1.1
Host: 8clm33qmf9.execute-api.eu-west-1.amazonaws.com
Authorization: Bearer <JWT_TOKEN>
```

**Response**:
```json
{
  "message": "Certificate deleted successfully"
}
```

## Authentication Flow

```
1. User logs in via Cognito (dashboard)
   ↓
2. Cognito returns JWT tokens (ID token, Access token)
   ↓
3. Dashboard stores tokens in sessionStorage
   ↓
4. API request includes token in Authorization header:
   Authorization: Bearer eyJraWQiOiJ...
   ↓
5. API Gateway receives request
   ↓
6. API Gateway validates JWT:
   - Verifies signature using Cognito public keys
   - Checks token expiration
   - Validates audience (client ID)
   - Validates issuer (Cognito User Pool)
   ↓
7. If valid:
   - Forwards request to Lambda with user context
   - Lambda receives: user sub, email, groups
   ↓
8. If invalid:
   - Returns 401 Unauthorized
   - Dashboard redirects to login
```

## CORS Configuration

API Gateway automatically handles CORS for the CloudFront domain:

```javascript
// Allowed in CORS
Origin: https://d3bqyfjow8topp.cloudfront.net

// Blocked
Origin: https://malicious-site.com
```

**Preflight Request** (OPTIONS):
```http
OPTIONS /dev-secure/certificates HTTP/1.1
Origin: https://d3bqyfjow8topp.cloudfront.net
Access-Control-Request-Method: POST
Access-Control-Request-Headers: authorization,content-type
```

**Preflight Response**:
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://d3bqyfjow8topp.cloudfront.net
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
Access-Control-Allow-Headers: authorization,content-type
Access-Control-Max-Age: 3600
```

## Authorization & RBAC

### User Context in Lambda
Lambda function receives user information in `event.requestContext.authorizer`:

```python
def lambda_handler(event, context):
    user_sub = event['requestContext']['authorizer']['jwt']['claims']['sub']
    user_email = event['requestContext']['authorizer']['jwt']['claims']['email']
    user_groups = event['requestContext']['authorizer']['jwt']['claims'].get('cognito:groups', [])
    
    # Check permissions
    if 'Admins' in user_groups:
        # Full access
        pass
    elif 'Operators' in user_groups:
        # Can create, read, update (no delete)
        if event['requestMethod'] == 'DELETE':
            return {'statusCode': 403, 'body': 'Permission denied'}
    elif 'Viewers' in user_groups:
        # Read-only
        if event['requestMethod'] in ['POST', 'PUT', 'DELETE']:
            return {'statusCode': 403, 'body': 'Permission denied'}
```

### Permission Matrix

| Group | GET | POST | PUT | DELETE |
|-------|-----|------|-----|--------|
| Admins | ✅ | ✅ | ✅ | ✅ |
| Operators | ✅ | ✅ | ✅ | ❌ |
| Viewers | ✅ | ❌ | ❌ | ❌ |

## Throttling & Rate Limiting

**Burst Limit**: 5,000 requests  
**Rate Limit**: 10,000 requests/second  

If exceeded:
```json
{
  "message": "Too Many Requests"
}
```

HTTP Status: `429 Too Many Requests`

## Monitoring

### CloudWatch Logs
API Gateway logs all requests to CloudWatch:
- Request/response bodies
- Latency metrics
- Error messages
- User context

View logs:
```bash
aws logs tail /aws/apigateway/cert-management-dev-secure-api --follow
```

### CloudWatch Metrics
- **Count**: Total number of requests
- **4XXError**: Client errors (400-499)
- **5XXError**: Server errors (500-599)
- **IntegrationLatency**: Lambda execution time
- **Latency**: Total request latency

## Error Handling

### 400 Bad Request
**Cause**: Invalid request body, missing required fields  
**Response**:
```json
{
  "error": "Invalid request",
  "message": "Missing required field: CommonName"
}
```

### 401 Unauthorized
**Cause**: Missing or invalid JWT token  
**Response**:
```json
{
  "message": "Unauthorized"
}
```

### 403 Forbidden
**Cause**: User lacks permission for operation  
**Response**:
```json
{
  "error": "Permission denied",
  "message": "Viewer role cannot create certificates"
}
```

### 404 Not Found
**Cause**: Certificate ID not found  
**Response**:
```json
{
  "error": "Not found",
  "message": "Certificate cert-123 does not exist"
}
```

### 500 Internal Server Error
**Cause**: Lambda function error, DynamoDB error  
**Response**:
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

## Testing

### Using curl
```bash
# Get JWT token (from browser devtools or login response)
TOKEN="eyJraWQiOiJ..."

# List certificates
curl -H "Authorization: Bearer $TOKEN" \
  https://8clm33qmf9.execute-api.eu-west-1.amazonaws.com/dev-secure/certificates

# Create certificate
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"CommonName":"*.test.com","ExpiryDate":"2026-01-01","Environment":"DEV","OwnerEmail":"test@example.com","Status":"active"}' \
  https://8clm33qmf9.execute-api.eu-west-1.amazonaws.com/dev-secure/certificates

# Update certificate
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"Status":"expired"}' \
  https://8clm33qmf9.execute-api.eu-west-1.amazonaws.com/dev-secure/certificates/cert-123

# Delete certificate
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  https://8clm33qmf9.execute-api.eu-west-1.amazonaws.com/dev-secure/certificates/cert-123
```

### Using Postman
1. Import API Gateway URL as base URL
2. Create environment variable: `jwt_token`
3. Set Authorization header: `Bearer {{jwt_token}}`
4. Test all endpoints

## Troubleshooting

### Issue: 401 Unauthorized despite valid login
**Cause**: Token expired (60-minute TTL)  
**Solution**: Refresh token or re-login

### Issue: CORS errors in browser
**Cause**: CloudFront domain not in CORS config  
**Solution**: Verify `cloudfront_domain` variable matches actual CloudFront URL

### Issue: 500 errors on all requests
**Cause**: Lambda function error  
**Solution**: Check Lambda CloudWatch logs:
```bash
aws logs tail /aws/lambda/cert-management-dev-secure-dashboard-api --follow
```

### Issue: Slow API responses
**Cause**: Cold start, DynamoDB throttling  
**Solution**: 
- Enable provisioned concurrency for Lambda
- Check DynamoDB metrics for throttling

## Cost Estimation

API Gateway HTTP API pricing:

| Component | Usage | Price | Monthly Cost |
|-----------|-------|-------|--------------|
| API Calls | 1 million | $1.00 per million | $1.00 |
| Data Transfer | 1 GB | $0.09/GB | $0.09 |
| **Total** | | | **~$1.09/month** |

**Note**: First 1 million requests free for first 12 months (AWS Free Tier)

## Best Practices

1. **JWT Validation**: Always validate tokens on API Gateway, not Lambda
2. **RBAC**: Implement role checks in Lambda for fine-grained control
3. **Error Handling**: Return meaningful error messages with proper HTTP status codes
4. **Logging**: Log all requests for auditing and debugging
5. **Throttling**: Set appropriate burst/rate limits based on expected traffic
6. **CORS**: Restrict to known domains only
7. **Monitoring**: Set up CloudWatch alarms for 4XX/5XX error rates

## Dependencies

- **Cognito User Pool**: Required for JWT validation
- **Lambda Function**: dashboard-api function must exist
- **CloudFront**: For CORS configuration

## Related Modules

- **Cognito**: Provides User Pool for authorization
- **Lambda Secure**: Provides dashboard-api Lambda function
- **Dashboard Secure**: Consumes API Gateway URL

## References

- [API Gateway HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html)
- [JWT Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)
- [CORS for HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html)
- [API Gateway Pricing](https://aws.amazon.com/api-gateway/pricing/)
