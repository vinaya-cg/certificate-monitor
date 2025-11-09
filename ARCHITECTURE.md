# System Architecture

This document describes the complete architecture of the Certificate Management Dashboard system.

## Table of Contents

- [Overview](#overview)
- [High-Level Architecture](#high-level-architecture)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)
- [Network Architecture](#network-architecture)
- [Technology Stack](#technology-stack)

## Overview

The Certificate Management Dashboard is a serverless, event-driven system built entirely on AWS managed services. It follows a microservices architecture with clear separation of concerns:

- **Frontend**: Static web application served via CloudFront CDN
- **Authentication**: AWS Cognito for user management and JWT-based API security
- **API Layer**: API Gateway with Lambda integration for REST endpoints
- **Business Logic**: Lambda functions for certificate processing
- **Data Storage**: DynamoDB for NoSQL storage, S3 for file storage
- **Monitoring**: EventBridge for scheduling, CloudWatch for observability

**Key Architectural Principles**:
- **Serverless First**: No servers to manage, automatic scaling
- **Security by Design**: Encryption everywhere, least-privilege IAM, zero-trust network
- **Infrastructure as Code**: 100% Terraform-managed, version-controlled
- **Cost Optimization**: Pay-per-use pricing, lifecycle policies, caching
- **High Availability**: Multi-AZ deployment, automatic failover

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USERS (Browser)                             │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ HTTPS (TLS 1.2+)
                                 │
                    ┌────────────▼────────────┐
                    │     CloudFront CDN      │ ← Global Edge Locations
                    │  (HTTPS Distribution)   │   Low Latency, DDoS Protection
                    └────────────┬────────────┘
                                 │
                     ┌───────────┴───────────┐
                     │                       │
          ┌──────────▼─────────┐   ┌────────▼──────────┐
          │   S3 Bucket        │   │   CloudFront OAI  │
          │  (Dashboard Files)  │   │  (Origin Access   │
          │  - index.html       │   │   Identity)       │
          │  - login.html       │   └───────────────────┘
          │  - dashboard.js     │
          │  - auth-cognito.js  │
          └─────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                       AUTHENTICATION LAYER                               │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌────────────────────────┐
                    │   Cognito User Pool    │
                    │  - User Directory      │
                    │  - Password Policies   │
                    │  - MFA Support         │
                    │  - Groups (RBAC)       │
                    └────────────┬───────────┘
                                 │
                                 │ JWT Tokens
                                 │
                    ┌────────────▼───────────┐
                    │  Cognito Identity Pool │
                    │  (AWS Credentials)     │
                    └────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                           API LAYER                                      │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌────────────────────────┐
                    │   API Gateway (HTTP)   │
                    │  - /certificates       │
                    │  - Cognito Authorizer  │
                    │  - CORS Configuration  │
                    │  - Throttling          │
                    └────────────┬───────────┘
                                 │
                                 │ AWS_PROXY Integration
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
    ┌──────▼──────┐     ┌───────▼────────┐   ┌───────▼────────┐
    │  Lambda     │     │   Lambda       │   │   Lambda       │
    │ certificate │     │   excel-       │   │  dashboard-    │
    │  -monitor   │     │   processor    │   │    api         │
    └──────┬──────┘     └───────┬────────┘   └───────┬────────┘
           │                    │                     │
           └────────────────────┼─────────────────────┘
                                │

┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                       │
└─────────────────────────────────────────────────────────────────────────┘

         ┌──────────────────┐              ┌──────────────────┐
         │   DynamoDB       │              │   S3 Buckets     │
         │  - certificates  │              │  - uploads/      │
         │  - logs          │              │  - logs/         │
         │  - GSIs (4+2)    │              │  - dashboard/    │
         └──────────────────┘              └──────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    MONITORING & SCHEDULING                               │
└─────────────────────────────────────────────────────────────────────────┘

    ┌────────────────┐           ┌────────────────┐
    │  EventBridge   │           │   CloudWatch   │
    │  - Daily 9AM   │           │  - Logs        │
    │  - Cron Rule   │           │  - Metrics     │
    └───────┬────────┘           │  - Dashboard   │
            │                    └────────────────┘
            │ Trigger Lambda
            │
    ┌───────▼─────────┐
    │  certificate-   │
    │    monitor      │ ───────► SES Email
    └─────────────────┘          Notifications
```

## Component Details

### 1. Frontend Layer

#### CloudFront Distribution
- **Purpose**: Global CDN for fast, secure dashboard delivery
- **Features**:
  - HTTPS-only (TLS 1.2+)
  - Origin Access Identity (OAI) for S3 security
  - Custom error pages (404 → error.html)
  - Compression (gzip/brotli)
  - HTTP/2 and HTTP/3 support
- **Performance**:
  - Edge caching (TTL: 1 hour)
  - Geographic distribution (Price Class 100: North America, Europe)
  - Query string caching
- **Security**:
  - Redirect HTTP to HTTPS
  - Private S3 origin (no public access)
  - SNI for SSL/TLS

#### S3 Dashboard Bucket
- **Purpose**: Store static dashboard files
- **Access**: CloudFront OAI only (no public access)
- **Files**:
  - `index.html` - Main dashboard
  - `login.html` - Authentication page
  - `error.html` - Error page
  - `dashboard.js` - Dashboard logic (templated with API URL)
  - `auth.js` - Auth utilities (templated with Cognito config)
  - `auth-cognito.js` - Cognito SDK (templated with complete config)
  - `images/*` - Logos
- **Templating**: JavaScript files auto-generated by Terraform with environment-specific configuration

### 2. Authentication Layer

#### Cognito User Pool
- **Purpose**: User directory and authentication service
- **Features**:
  - Email-based authentication
  - Password policies (8 chars, complexity requirements)
  - Email verification
  - MFA support (optional)
  - Advanced security (AUDIT mode)
  - Account recovery via email
- **User Groups**:
  - **Admins**: Full access (CRUD)
  - **Operators**: Create, read, update (no delete)
  - **Viewers**: Read-only
- **Tokens**:
  - ID Token: 60 minutes (user identity)
  - Access Token: 60 minutes (API authorization)
  - Refresh Token: 30 days (token renewal)

#### Cognito Identity Pool
- **Purpose**: Provide AWS credentials to authenticated users
- **Use Case**: Future features requiring direct AWS SDK access
- **Authentication**: Cognito User Pool only (no unauthenticated access)

#### SES Integration
- **Purpose**: Send user registration emails, password resets
- **Configuration**: Sender email verified in SES
- **Sandbox Mode Limitation**: Can only send TO verified emails
- **Production Mode**: Send to any email (requires approval)

### 3. API Layer

#### API Gateway (HTTP API)
- **Protocol**: HTTP/2
- **Endpoints**:
  - `GET /certificates` - List/search certificates
  - `POST /certificates` - Create certificate
  - `PUT /certificates/{id}` - Update certificate
  - `DELETE /certificates/{id}` - Delete certificate
  - `OPTIONS /certificates` - CORS preflight
- **Authorization**: Cognito JWT authorizer on all endpoints
- **CORS**: Configured for CloudFront domain
- **Throttling**: 5000 burst, 10000/sec rate limit
- **Logging**: CloudWatch access logs, execution logs

### 4. Business Logic Layer

#### Lambda Functions

**certificate-monitor**
- **Purpose**: Daily expiry monitoring
- **Trigger**: EventBridge (daily at 9 AM UTC)
- **Runtime**: Python 3.9
- **Memory**: 512 MB
- **Timeout**: 5 minutes
- **Logic**:
  1. Query DynamoDB for certificates expiring within 30 days
  2. Group certificates by owner email
  3. Send SES email to each owner
  4. Log actions to DynamoDB
- **Permissions**: Read DynamoDB, send SES emails

**excel-processor**
- **Purpose**: Parse Excel files, import certificates
- **Trigger**: S3 upload (*.xlsx files)
- **Runtime**: Python 3.9
- **Memory**: 1024 MB (for pandas/openpyxl)
- **Timeout**: 15 minutes
- **Logic**:
  1. Download Excel file from S3
  2. Parse with pandas/openpyxl
  3. Validate rows (schema, data types)
  4. Batch write to DynamoDB
  5. Log import summary
- **Dependencies**: pandas, openpyxl (via Lambda Layer)
- **Permissions**: Read S3, write DynamoDB

**dashboard-api**
- **Purpose**: REST API backend
- **Trigger**: API Gateway requests
- **Runtime**: Python 3.9
- **Memory**: 256 MB
- **Timeout**: 30 seconds
- **Logic**:
  1. Parse HTTP method and path
  2. Extract user context from Cognito
  3. Check RBAC permissions
  4. Perform DynamoDB operation
  5. Log action to DynamoDB
  6. Return JSON response
- **RBAC**: Group-based permission checks
- **Permissions**: Read/write DynamoDB

### 5. Data Layer

#### DynamoDB Tables

**certificates** table
- **Partition Key**: CertificateID (String, UUID)
- **Attributes**: CommonName, ExpiryDate, Environment, OwnerEmail, SupportEmail, Status, CreatedAt, UpdatedAt
- **GSIs**:
  - StatusIndex: (Status, ExpiryDate) - Find active/expired certs
  - EnvironmentIndex: (Environment, ExpiryDate) - Find certs by environment
  - OwnerIndex: (OwnerEmail, ExpiryDate) - Find certs by owner
  - ExpiryIndex: (Status, ExpiryDate) - Find expiring certs
- **Billing**: PAY_PER_REQUEST (auto-scaling)
- **Encryption**: AWS-managed keys (SSE-S3)
- **PITR**: Enabled (35 days retention)

**certificate-logs** table
- **Partition Key**: LogID (String, UUID)
- **Attributes**: Timestamp, CertificateID, Action, UserEmail, Changes, IpAddress
- **GSIs**:
  - CertificateIndex: (CertificateID, Timestamp) - Audit trail for cert
  - ActionIndex: (Action, Timestamp) - Find operations by type
- **Billing**: PAY_PER_REQUEST
- **Encryption**: AWS-managed keys
- **PITR**: Enabled

#### S3 Buckets

**uploads** bucket
- **Purpose**: Store uploaded Excel files
- **Access**: Lambda functions only (IAM role)
- **Versioning**: Enabled
- **Lifecycle**:
  - 30 days → STANDARD_IA
  - 90 days → GLACIER
  - 365 days → DELETE
- **Encryption**: SSE-S3 (AES-256)
- **Public Access**: Blocked

**logs** bucket
- **Purpose**: Store application logs
- **Access**: AWS services (CloudFront, Lambda)
- **Versioning**: Enabled
- **Lifecycle**:
  - 90 days → GLACIER
  - 365 days → DELETE
- **Encryption**: SSE-S3
- **Public Access**: Blocked

### 6. Monitoring & Scheduling

#### EventBridge Rule
- **Schedule**: `cron(0 9 * * ? *)` (daily at 9 AM UTC)
- **Target**: certificate-monitor Lambda
- **State**: ENABLED
- **Retry**: Automatic retries on failure

#### CloudWatch
- **Dashboards**: Real-time metrics visualization
- **Logs**: Lambda execution logs (30 days retention)
- **Metrics**:
  - Lambda: Invocations, Duration, Errors, Throttles
  - DynamoDB: Read/Write Capacity, Errors, Throttling
  - API Gateway: Request Count, Latency, Errors
- **Alarms**: (Recommended) Lambda errors, DynamoDB throttling

## Data Flow

### 1. User Authentication Flow

```
1. User navigates to CloudFront URL
   ↓
2. CloudFront serves login.html from S3
   ↓
3. User enters email + password
   ↓
4. auth-cognito.js → Cognito User Pool
   ↓
5. Cognito validates credentials
   ↓
6. If FORCE_CHANGE_PASSWORD:
   - Show password change modal
   - User sets new password
   - Cognito updates user status
   ↓
7. Cognito returns JWT tokens:
   - ID Token (user identity)
   - Access Token (API authorization)
   - Refresh Token (token renewal)
   ↓
8. dashboard.js stores tokens in sessionStorage
   ↓
9. Redirect to index.html (dashboard)
```

### 2. Certificate CRUD Flow

```
1. User performs action in dashboard (add/edit/delete)
   ↓
2. dashboard.js calls API Gateway
   Headers: Authorization: Bearer <JWT_TOKEN>
   Body: Certificate data (JSON)
   ↓
3. API Gateway receives request
   ↓
4. Cognito Authorizer validates JWT:
   - Verify signature
   - Check expiration
   - Validate audience
   - Validate issuer
   ↓
5. If valid → Forward to Lambda with user context
   If invalid → Return 401 Unauthorized
   ↓
6. dashboard-api Lambda:
   - Extract user email, groups from JWT
   - Check RBAC permissions
   - Perform DynamoDB operation
   - Log action to logs table
   ↓
7. Lambda returns JSON response
   ↓
8. API Gateway forwards response
   ↓
9. dashboard.js updates UI
```

### 3. Excel Import Flow

```
1. User uploads Excel file in dashboard
   ↓
2. File uploaded to S3 uploads bucket
   ↓
3. S3 triggers excel-processor Lambda
   Event: s3:ObjectCreated:*
   Filter: *.xlsx
   ↓
4. Lambda downloads file from S3
   ↓
5. Parse Excel with pandas/openpyxl
   ↓
6. Validate each row:
   - Required fields present
   - Date format correct
   - Email format valid
   - Environment in [DEV, TEST, PROD]
   - Status in [active, expired, etc.]
   ↓
7. Generate CertificateID (UUID) for each
   ↓
8. Batch write to DynamoDB certificates table
   (Up to 25 items per batch)
   ↓
9. Log import summary to logs table
   ↓
10. Lambda returns success count, error count
    ↓
11. Dashboard polls for completion (optional)
    or relies on S3 event completion
```

### 4. Daily Monitoring Flow

```
1. EventBridge rule triggers at 9 AM UTC daily
   ↓
2. Invokes certificate-monitor Lambda
   ↓
3. Lambda calculates expiry threshold (now + 30 days)
   ↓
4. Query DynamoDB ExpiryIndex:
   Status = 'active' AND ExpiryDate < threshold
   ↓
5. Group certificates by OwnerEmail
   ↓
6. For each owner:
   - Build email body with cert list
   - Send via SES
   - Log email sent to logs table
   ↓
7. Lambda returns summary:
   - Certificates checked
   - Emails sent
   - Errors encountered
   ↓
8. CloudWatch logs results
```

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Network Security                                   │
│ - HTTPS only (TLS 1.2+)                                     │
│ - CloudFront DDoS protection                                │
│ - Private S3 buckets (no public access)                     │
│ - VPC endpoints (future enhancement)                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Identity & Authentication                          │
│ - Cognito User Pool (password policies, MFA)                │
│ - JWT tokens (short-lived, signed)                          │
│ - Email verification required                               │
│ - Advanced security (AUDIT mode)                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Authorization                                      │
│ - API Gateway Cognito Authorizer (JWT validation)           │
│ - Role-Based Access Control (Admins, Operators, Viewers)    │
│ - Lambda function permission checks                         │
│ - IAM least-privilege policies                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Data Security                                      │
│ - Encryption at rest (S3 SSE-S3, DynamoDB encryption)        │
│ - Encryption in transit (HTTPS/TLS)                         │
│ - S3 versioning (prevent accidental deletion)               │
│ - DynamoDB PITR (35-day recovery window)                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Audit & Monitoring                                 │
│ - All operations logged to DynamoDB                         │
│ - CloudWatch Logs (30-day retention)                        │
│ - CloudWatch metrics and alarms                             │
│ - User context in every log entry                           │
└─────────────────────────────────────────────────────────────┘
```

### IAM Permissions Model

**Principle**: Least Privilege

```
Lambda Execution Role:
  - DynamoDB: Read/Write certificates, logs tables only
  - S3: Read uploads bucket only
  - SES: Send emails from verified sender only
  - CloudWatch: Create log groups/streams, put log events

CloudFront OAI:
  - S3: GetObject on dashboard bucket only

API Gateway:
  - Lambda: InvokeFunction on dashboard-api only

EventBridge:
  - Lambda: InvokeFunction on certificate-monitor only
```

### Encryption

**At Rest**:
- S3: SSE-S3 (AES-256, AWS-managed keys)
- DynamoDB: Default encryption (AWS-managed keys)
- CloudWatch Logs: Encrypted by default

**In Transit**:
- CloudFront → Browser: HTTPS (TLS 1.2+)
- Dashboard → API Gateway: HTTPS (TLS 1.2+)
- Lambda → DynamoDB: TLS (AWS internal network)
- Lambda → S3: TLS (AWS internal network)

## Deployment Architecture

### Multi-Environment Strategy

```
Environments:
  - dev: Development testing
  - dev-secure: Secure development with Cognito
  - staging: Pre-production testing (future)
  - prod: Production deployment (future)

Isolation:
  - Separate AWS accounts (recommended for prod)
  - Separate Terraform workspaces
  - Environment-specific variable files
  - Unique resource naming (random suffixes)

Promotion:
  - dev → dev-secure: Feature testing
  - dev-secure → staging: Integration testing
  - staging → prod: Production release
```

### Disaster Recovery

**RTO (Recovery Time Objective)**: 1 hour  
**RPO (Recovery Point Objective)**: 24 hours

**Backup Strategy**:
- DynamoDB PITR: 35-day recovery window
- S3 Versioning: Unlimited version history
- Terraform State: Versioned in S3 backend

**Recovery Procedures**:
1. **DynamoDB corruption**: Restore from PITR to point before corruption
2. **S3 accidental deletion**: Restore from S3 version history
3. **Complete environment loss**: `terraform apply` recreates all resources
4. **Regional outage**: Deploy to different region (portable Terraform)

## Network Architecture

### Current Architecture (Serverless)

```
Internet
   ↓
CloudFront (Global Edge Locations)
   ↓
AWS Public Services:
   - S3 (Public endpoint, private bucket)
   - API Gateway (Public endpoint)
   - Lambda (AWS-managed VPC)
   - DynamoDB (Public endpoint)
   - Cognito (Public endpoint)
```

**Note**: No VPC required for serverless architecture. All traffic encrypted with TLS.

### Future Enhancement: VPC Integration

```
Internet
   ↓
CloudFront
   ↓
API Gateway (Public)
   ↓
Lambda (in VPC)
   ↓
   ├→ DynamoDB (via VPC Endpoint)
   ├→ S3 (via VPC Endpoint)
   └→ SES (via NAT Gateway)

Benefits:
  - Private IP addressing
  - Network isolation
  - VPC Flow Logs
  - Network ACLs
  - Security Groups

Trade-offs:
  - Increased complexity
  - NAT Gateway costs
  - Cold start latency
```

## Technology Stack

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Responsive design, flexbox/grid
- **JavaScript (ES6+)**: Modern JavaScript features
- **Amazon Cognito SDK**: User authentication
- **Fetch API**: REST API calls

### Backend
- **Python 3.9**: Lambda runtime
- **boto3**: AWS SDK for Python
- **pandas**: Excel file parsing (excel-processor)
- **openpyxl**: Excel file format (excel-processor)

### Infrastructure
- **Terraform**: Infrastructure as Code
- **AWS Provider**: AWS resource management
- **Random Provider**: Unique resource naming

### AWS Services
- **CloudFront**: CDN and HTTPS delivery
- **S3**: Object storage
- **Cognito**: User authentication
- **API Gateway**: REST API
- **Lambda**: Serverless compute
- **DynamoDB**: NoSQL database
- **SES**: Email delivery
- **EventBridge**: Event scheduling
- **CloudWatch**: Logging and monitoring
- **IAM**: Access management

### Development Tools
- **VS Code**: Code editor
- **AWS CLI**: Command-line management
- **Git**: Version control
- **GitHub**: Code repository

## Scalability

### Automatic Scaling

| Service | Scaling Method | Limits |
|---------|----------------|--------|
| **CloudFront** | Global edge locations | No hard limit |
| **S3** | Automatic | No limit |
| **API Gateway** | Automatic | 10K requests/sec (soft limit) |
| **Lambda** | Concurrent executions | 1000 default (increasable) |
| **DynamoDB** | PAY_PER_REQUEST | No limit |
| **Cognito** | Automatic | 50K MAU free tier |

### Performance Targets

- **Dashboard Load Time**: < 2 seconds (first visit), < 500ms (cached)
- **API Response Time**: < 200ms (p50), < 500ms (p95), < 1s (p99)
- **Lambda Cold Start**: < 3 seconds
- **Lambda Warm Execution**: < 100ms
- **DynamoDB Query**: < 50ms

### Capacity Planning

**Current Capacity** (dev-secure):
- Users: < 100
- Certificates: < 1,000
- API Requests: < 10,000/month
- Excel Imports: < 10/month

**Production Estimates**:
- Users: 500-1,000
- Certificates: 10,000-50,000
- API Requests: 1,000,000/month
- Excel Imports: 100/month

**Scaling Considerations**:
- Lambda concurrent executions: Monitor and increase limit if needed
- DynamoDB: Consider provisioned capacity for predictable workloads
- CloudFront: Add more edge locations (Price Class All)
- API Gateway: Request limit increase if approaching 10K/sec

## Cost Optimization

### Current Monthly Cost (dev-secure)

| Service | Usage | Cost |
|---------|-------|------|
| CloudFront | 10 GB, 10K requests | $0.86 |
| S3 | 1 GB storage, 10K requests | $0.03 |
| API Gateway | 10K requests | $1.09 |
| Lambda | 10K invocations | $0.20 |
| DynamoDB | 1M reads, 100K writes | $1.50 |
| Cognito | 100 MAU | Free |
| CloudWatch | Logs, metrics, dashboard | $2.00 |
| **Total** | | **~$5.68/month** |

### Cost Optimization Strategies

1. **S3 Lifecycle**: Transition old files to GLACIER, delete after 365 days
2. **CloudFront Caching**: Increase TTL to reduce origin requests
3. **Lambda Memory**: Right-size memory for optimal price/performance
4. **DynamoDB**: Use PAY_PER_REQUEST for variable workloads
5. **CloudWatch Logs**: 30-day retention, export old logs to S3
6. **Reserved Capacity**: Future consideration for production

## Future Enhancements

1. **Multi-Region Deployment**: Active-active for global redundancy
2. **Advanced Monitoring**: X-Ray tracing, anomaly detection, custom metrics
3. **CI/CD Pipeline**: Automated testing and deployment
4. **Certificate Validation**: Verify cert chains, check revocation status
5. **Auto-Renewal Integration**: Let's Encrypt, ACM integration
6. **Advanced Notifications**: Slack, Teams, PagerDuty integration
7. **Analytics Dashboard**: Certificate trends, usage analytics
8. **API Rate Limiting**: Per-user rate limits
9. **Caching Layer**: ElastiCache for frequently accessed data
10. **WAF Integration**: Web Application Firewall for CloudFront

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Maintained by**: Sogeti Run Factory Team
