# Certificate Management Dashboard

A comprehensive, enterprise-grade certificate monitoring and management system built on AWS serverless architecture with Terraform infrastructure-as-code.

## 🚀 Quick Start

Deploy the complete infrastructure in 3 steps:

```bash
cd terraform/environments/dev-secure
terraform init
terraform apply -auto-approve
```

That's it! The system is 100% portable - works in any AWS account/region without code modifications.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Deployment](#deployment)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Portability](#portability)
- [Security](#security)
- [Contributing](#contributing)

## Overview

This project provides a complete solution for monitoring SSL/TLS certificates across multiple environments. It features:

- **Web Dashboard**: Secure, authenticated interface for certificate management
- **ACM Synchronization**: Automated sync from AWS Certificate Manager with manual trigger option
- **Automated Monitoring**: Daily checks for expiring certificates with email notifications
- **Excel Import**: Bulk certificate upload via Excel files
- **REST API**: Full CRUD operations with JWT authentication
- **Role-Based Access Control**: Admin, Operator, and Viewer roles
- **Infrastructure as Code**: 100% Terraform-managed AWS resources

### Latest Features (v1.2.0)
- 🔄 **ACM Certificate Sync**: One-click sync from AWS Certificate Manager
- 📊 **Real-time Progress Modal**: Visual feedback with certificate counts
- ⏰ **Scheduled Daily Sync**: Automated sync at 2 AM UTC via EventBridge
- 🎯 **Smart Updates**: Preserves manual data while updating ACM info
- 📈 **Performance**: Syncs 64 certificates in ~6 seconds

## Architecture

```
┌─────────────────┐
│   CloudFront    │ ← HTTPS (TLS 1.2+)
│  Distribution   │
└────────┬────────┘
         │
    ┌────▼────┐
    │   S3    │ ← Dashboard Files
    │ Bucket  │
    └─────────┘

┌─────────────────┐
│     Users       │
└────────┬────────┘
         │
    ┌────▼────────┐
    │   Cognito   │ ← Authentication
    │  User Pool  │
    └────────┬────┘
             │
        ┌────▼────────┐
        │ API Gateway │ ← REST API
        └────────┬────┘
                 │
            ┌────▼─────────┐
            │   Lambda     │ ← Business Logic
            │  Functions   │
            └────────┬─────┘
                     │
                ┌────▼────────┐
                │  DynamoDB   │ ← Data Storage
                │   Tables    │
                └─────────────┘

┌─────────────────┐
│  EventBridge    │ ← Daily Schedule
│     Rule        │
└────────┬────────┘
         │
    ┌────▼─────────────┐
    │ certificate-     │ ← Monitoring
    │   monitor        │
    └──────────────────┘
```

### Key Components

1. **Frontend Layer**: CloudFront → S3 (static dashboard)
2. **Authentication Layer**: Cognito User Pool (JWT tokens, RBAC)
3. **API Layer**: API Gateway (REST endpoints with Cognito authorization)
4. **Business Logic Layer**: Lambda functions (Python 3.9)
5. **Data Layer**: DynamoDB (certificates, logs)
6. **Monitoring Layer**: EventBridge (scheduled triggers), CloudWatch (metrics/logs)

## Features

### 🔐 Security
- **Authentication**: AWS Cognito with JWT tokens
- **Authorization**: Role-based access control (Admins, Operators, Viewers)
- **Encryption**: HTTPS only (TLS 1.2+), S3 server-side encryption (AES-256)
- **Network Security**: Private S3 buckets, CloudFront OAI, API Gateway authorizer
- **Credential Management**: Secure password policies (8 chars, complexity requirements)

### 📊 Certificate Management
- **CRUD Operations**: Create, Read, Update, Delete certificates via dashboard or API
- **Advanced Search & Filter**: 
  - Text search by certificate name, application, owner
  - Status filter (Active, Expired, Due for Renewal, etc.)
  - Environment filter (Production, Staging, Development, etc.)
  - **Date Range Filter**: Filter by certificate expiry date (From/To dates)
- **Bulk Import**: Excel file upload (.xlsx, .xls) with automatic parsing and validation
- **Smart Export**: 
  - Export filtered certificates to CSV
  - Filename includes applied filters for easy identification
  - CSV includes summary header with filter details and export metadata
- **Status Tracking**: Active, Expired, Due for Renewal, Renewal in Progress, Revoked
- **Audit Logging**: All operations logged to DynamoDB with timestamps

### 🔔 Automated Monitoring
- **Daily Scans**: EventBridge triggers Lambda function at 9 AM UTC
- **Expiry Notifications**: Email alerts via SES for certificates expiring within threshold
- **CloudWatch Dashboard**: Real-time metrics for Lambda performance, DynamoDB capacity

### 🌐 User Interface
- **Responsive Design**: Works on desktop, tablet, mobile devices
- **Real-time Validation**: Password strength indicators, form input validation
- **Advanced Filtering**:
  - Multi-criteria search (text, status, environment)
  - Date range picker for expiry date filtering
  - Clear filters with one click
- **Data Export**: Export filtered results to CSV with smart naming and summary headers
- **Professional UI**: Sogeti/PostNL branding with modern, intuitive styling
- **Password Management**: Secure password change with complexity requirements
- **Excel Upload**: Drag-and-drop or click to upload certificate data in bulk

## Prerequisites

Before deploying, ensure you have:

1. **AWS Account** with administrative access
2. **AWS CLI** configured with credentials (`aws configure`)
3. **Terraform** v1.0+ installed ([download](https://www.terraform.io/downloads))
4. **Verified SES Email** (for sending notifications):
   ```bash
   aws ses verify-email-identity --email-address your-email@example.com --region eu-west-1
   ```
5. **Git** (for cloning repository)

## Deployment

### Step 1: Clone Repository
```bash
git clone https://github.com/vinaya-cg/certificate-monitor
cd cert-dashboard
```

### Step 2: Configure Environment
Edit `terraform/environments/dev-secure/terraform.tfvars`:

```hcl
# AWS Configuration
aws_region = "eu-west-1"  # Change to your preferred region

# Email Configuration
sender_email = "your-email@example.com"  # Must be verified in SES

# User Configuration
admin_user    = "admin@example.com"
operator_user = "operator@example.com"
viewer_user   = "viewer@example.com"
```

### Step 3: Deploy Infrastructure
```bash
cd terraform/environments/dev-secure
terraform init       # Download providers and modules
terraform plan       # Review changes
terraform apply      # Deploy (takes ~5-7 minutes)
```

### Step 4: Access Dashboard
After deployment completes, Terraform outputs the dashboard URL:

```
cloudfront_distribution_url = "https://d3bqyfjow8topp.cloudfront.net"
```

Users receive temporary passwords via email. On first login, they must change their password.

For detailed deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

## Usage

### Accessing the Dashboard

1. Navigate to the CloudFront URL provided in Terraform outputs
2. Login with your email and temporary password
3. Change your password (must meet complexity requirements)
4. Access the certificate dashboard

### Managing Certificates

#### Add Certificate (Web UI)
1. Click "Add Certificate" button
2. Fill in certificate details
3. Click "Save"

#### Upload Certificates (Excel)
1. Prepare Excel file with columns: CommonName, ExpiryDate, Environment, OwnerEmail, SupportEmail, Status
2. Click "Upload Excel" button
3. Select file
4. System automatically parses and imports certificates

#### Search & Filter
- Use search bar to find certificates by common name
- Filter by status: Active, Expired, Expiring Soon
- Filter by environment: DEV, TEST, PROD
- Sort by any column (click column header)

### User Roles

| Role | View | Add | Edit | Delete |
|------|------|-----|------|--------|
| **Admin** | ✅ | ✅ | ✅ | ✅ |
| **Operator** | ✅ | ✅ | ✅ | ❌ |
| **Viewer** | ✅ | ❌ | ❌ | ❌ |

For complete user guide, see [USER_GUIDE.md](USER_GUIDE.md).

## Project Structure

```
cert-dashboard/
├── README.md                       # This file
├── ARCHITECTURE.md                 # System architecture documentation
├── DEPLOYMENT_GUIDE.md             # Detailed deployment instructions
├── WORKFLOW.md                     # Development workflow
├── USER_GUIDE.md                   # End-user documentation
├── API_DOCUMENTATION.md            # REST API reference
├── CONTRIBUTING.md                 # Contribution guidelines
│
├── dashboard/                      # Frontend files
│   ├── README.md                   # Dashboard documentation
│   ├── index.html                  # Main dashboard page
│   ├── login.html                  # Login page
│   ├── error.html                  # Error page
│   ├── dashboard.js                # Dashboard logic (templated)
│   ├── auth.js                     # Auth utilities (templated)
│   ├── auth-cognito.js             # Cognito integration (templated)
│   └── images/                     # Logo images
│
├── lambda/                         # Backend Lambda functions
│   ├── README.md                   # Lambda documentation
│   ├── certificate_monitor.py      # Daily expiry monitoring
│   ├── excel_processor.py          # Excel file processing
│   └── dashboard_api.py            # REST API handler
│
└── terraform/                      # Infrastructure as Code
    ├── environments/               # Environment configurations
    │   └── dev-secure/
    │       ├── main.tf             # Orchestrates all modules
    │       ├── terraform.tfvars    # Configuration (edit this only)
    │       ├── variables.tf        # Variable declarations
    │       └── outputs.tf          # Output definitions
    │
    └── modules/                    # Reusable Terraform modules
        ├── api_gateway/            # REST API with Cognito auth
        ├── cloudfront/             # HTTPS CDN distribution
        ├── cognito/                # User authentication
        ├── dashboard_secure/       # S3 file upload with templating
        ├── database/               # DynamoDB tables
        ├── eventbridge/            # Scheduled monitoring
        ├── iam/                    # Lambda execution roles
        ├── lambda_secure/          # Lambda functions
        ├── monitoring/             # CloudWatch dashboard
        └── storage_secure/         # S3 buckets with encryption
```

## Documentation

Comprehensive documentation is organized as follows:

- **[README.md](README.md)** (this file) - Project overview and quick start
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design, components, data flow
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Step-by-step deployment, troubleshooting
- **[WORKFLOW.md](WORKFLOW.md)** - Development processes, CI/CD, testing
- **[USER_GUIDE.md](USER_GUIDE.md)** - End-user documentation for dashboard
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - REST API reference
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

### Module Documentation
Each Terraform module has its own README:

- [modules/api_gateway/README.md](terraform/modules/api_gateway/README.md)
- [modules/cloudfront/README.md](terraform/modules/cloudfront/README.md)
- [modules/cognito/README.md](terraform/modules/cognito/README.md)
- [modules/dashboard_secure/README.md](terraform/modules/dashboard_secure/README.md)
- [modules/database/README.md](terraform/modules/database/README.md)
- [modules/eventbridge/README.md](terraform/modules/eventbridge/README.md)
- [modules/iam/README.md](terraform/modules/iam/README.md)
- [modules/lambda_secure/README.md](terraform/modules/lambda_secure/README.md)
- [modules/monitoring/README.md](terraform/modules/monitoring/README.md)
- [modules/storage_secure/README.md](terraform/modules/storage_secure/README.md)

### Component Documentation
- [dashboard/README.md](dashboard/README.md) - Frontend architecture
- [lambda/README.md](lambda/README.md) - Lambda functions overview

## Portability

This project is designed for **100% portability** - it can be deployed to any AWS account or region without code modifications.

### Portability Features

✅ **Random Suffixes** - S3 buckets use random suffixes for global uniqueness  
✅ **Data Sources** - AWS account/region auto-detected dynamically  
✅ **No Hardcoded Values** - All ARNs, URLs, IDs generated at runtime  
✅ **Templated Configuration** - Dashboard files auto-generated with correct Cognito/API values  
✅ **Modular Structure** - 13 reusable Terraform modules  
✅ **Environment Isolation** - dev, dev-secure, staging, prod

### Deploy to New Account/Region

1. Edit `terraform/environments/dev-secure/terraform.tfvars`:
   ```hcl
   aws_region = "us-east-1"  # Change region
   sender_email = "new-email@example.com"  # Change email
   ```

2. Deploy:
   ```bash
   terraform init
   terraform apply
   ```

**That's it!** All resources created with new unique IDs, no manual configuration needed.

## Security

### Authentication & Authorization
- **AWS Cognito** user pool with JWT tokens
- **Password Policy**: Minimum 8 characters, uppercase, lowercase, number, symbol
- **MFA Support**: Optional multi-factor authentication
- **Role-Based Access Control**: Admin, Operator, Viewer groups
- **Session Management**: Automatic token refresh, secure logout

### Network Security
- **HTTPS Only**: TLS 1.2+ enforced on CloudFront
- **Private S3**: Buckets not publicly accessible, OAI (Origin Access Identity) only
- **API Gateway Authorization**: Cognito authorizer validates JWT on every request
- **CORS Configuration**: Restricted to CloudFront domain

### Data Security
- **Encryption at Rest**: S3 server-side encryption (AES-256), DynamoDB encryption
- **Encryption in Transit**: HTTPS/TLS for all communications
- **Secrets Management**: No hardcoded credentials, IAM roles for Lambda
- **Audit Logging**: All certificate operations logged to DynamoDB

## Troubleshooting

### Common Issues

**Issue**: Users not receiving temporary password emails  
**Cause**: SES in Sandbox Mode (can only send to verified addresses)  
**Solution**: Request Production Access in SES console (free, 24-48 hours)

**Issue**: "Email address is not verified" error during deployment  
**Cause**: SES identity not yet verified  
**Solution**: Verify email first: `aws ses verify-email-identity --email-address your-email@example.com --region eu-west-1`

**Issue**: CloudFront shows old dashboard version  
**Cause**: CloudFront caching  
**Solution**: Invalidate cache: `aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"`

For more troubleshooting, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting).

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- How to submit pull requests
- Code style guidelines
- Testing requirements
- Documentation standards

## Support

For questions or issues:
- **Email**: vinaya-c.nayanegali@capgemini.com
- **GitHub**: https://github.com/vinaya-cg/certificate-monitor

---

**Status**: ✅ Production-ready  
**Version**: 2.0.0  
**Last Updated**: November 2025  
**Maintained by**: Sogeti Run Factory Team
