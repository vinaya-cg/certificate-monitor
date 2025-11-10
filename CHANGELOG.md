# Changelog

All notable changes to the Certificate Management Dashboard project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-11-10

### Added
- **ACM Certificate Synchronization Feature**
  - Automated daily sync from AWS Certificate Manager at 2:00 AM UTC via EventBridge
  - Manual sync button in dashboard UI with real-time progress modal
  - DynamoDB Global Secondary Index (AccountNumber-DomainName-index) for efficient account-based queries
  - New certificate attributes: AccountNumber, ACM_ARN, ACM_Status, LastSyncedFromACM
  - Smart update logic that preserves manually entered data (OwnerEmail, SupportEmail, Application, Notes)
  - Version tracking to distinguish new vs updated certificates
  - Interactive modal with three states: Progress, Results (4-metric grid), and Error views
  - Real-time polling to detect sync completion (checks every 1 second for up to 60 seconds)
  - Color-coded metrics: Found (blue), Added (green), Updated (orange), Errors (red)
  
- **Lambda Functions**
  - `acm_certificate_sync.py`: Scans ACM certificates and syncs to DynamoDB (512MB, 900s timeout)
  - Enhanced `dashboard_api.py` with `/sync-acm` endpoint for manual triggers
  - Successfully tested with 64 certificates in ~6 seconds
  
- **API Gateway Endpoint**
  - POST /sync-acm with Cognito authentication
  - CORS support (OPTIONS method) for dashboard integration
  - Returns 202 Accepted for asynchronous sync operations
  
- **EventBridge Scheduled Rule**
  - Daily automated sync: `cron(0 2 * * ? *)`
  - Rule name: cert-management-dev-secure-acm-sync-schedule
  
- **IAM Permissions**
  - lambda:InvokeFunction permission for dashboard API to trigger ACM sync
  - ACM read permissions (ListCertificates, DescribeCertificate)
  - DynamoDB read/write permissions for certificate data
  
- **Documentation**
  - Comprehensive ACM Sync Feature documentation (ACM_SYNC_FEATURE.md)
  - Architecture diagrams and component descriptions
  - Troubleshooting guide with common issues and solutions
  - Cost estimates and performance metrics
  - Testing procedures and monitoring instructions

- **Date Range Filtering**: Added From/To date pickers in dashboard controls to filter certificates by expiry date
- **Clear Date Range Button**: Quick reset button (X) to clear date range filters
- **Enhanced CSV Export**: 
  - Export filename now includes applied filters (date range, status, environment)
  - CSV includes summary header with total count, filters applied, and export timestamp
  - Button renamed to "Export Filtered" for clarity
- **Excel Upload Feature**: Bulk upload certificates via Excel files (.xlsx, .xls)
  - Supports flexible column mapping
  - Automatic validation and error reporting
  - Progress tracking for bulk uploads

### Changed
- Updated `dashboard.js` with API_BASE_URL constant for correct /sync-acm endpoint routing
- Modified cache-busting version parameter to v20251110-1525
- Enhanced error handling with detailed console logging for debugging
- Improved modal UI with responsive design and better user feedback
- Export button text changed from "Export" to "Export Filtered" to clarify functionality
- Date filtering now applies to certificate expiry dates

### Fixed
- **ACM Sync API URL**: Fixed endpoint construction (was /certificates/sync-acm, now /sync-acm)
- **IAM Permission Issue**: Added lambda:InvokeFunction permission preventing dashboard API from invoking ACM sync Lambda
- **CloudFront Cache**: Implemented proper cache invalidation strategy for UI updates
- **Modal Element Verification**: Added null checks to prevent JavaScript errors
- **Critical Bug - Certificate Display**: Fixed Lambda function HTTP method detection
  - Lambda was not properly detecting POST requests from API Gateway
  - Changed from `event.get('requestContext', {}).get('http', {}).get('method')` to `event.get('httpMethod')`
  - All POST/PUT requests were being treated as GET, returning full certificate list instead of operation confirmation
- **Dashboard API Response Handling**: Updated `fetchCertificatesFromAPI()` to handle plain array responses
  - Lambda returns array directly: `[cert1, cert2, ...]`
  - Dashboard was expecting wrapped object: `{certificates: [...]}`
  - Added support for both formats for backward compatibility
- **CORS Headers**: Ensured all Lambda responses include proper CORS headers for browser compatibility

### Security
- All API calls authenticated via Cognito User Pool JWT tokens
- Lambda execution uses least-privilege IAM role
- HTTPS-only communication enforced across all endpoints
- DynamoDB encryption at rest enabled
- CloudFront enforces TLS 1.2+

### Performance
- Successfully tested with 64 certificates
- Average ACM sync time: ~6 seconds for 64 certificates
- Memory usage: ~86 MB peak during sync
- Efficient GSI queries for duplicate detection
- Parallel ACM API calls within rate limits

### Infrastructure
- **Terraform Resources Deployed**
  - 8 resources added (ACM sync Lambda, EventBridge, GSI, API Gateway endpoint)
  - 11 resources changed (updated policies, configurations)
  - 1 resource destroyed (old API deployment)
  
- **Terraform Modules**
  - `modules/lambda_acm_sync/`: Complete infrastructure for ACM sync
  - Updated `modules/api_gateway/`: Added /sync-acm resource with CORS
  - Updated `modules/iam/`: Added lambda:InvokeFunction permission

## [1.1.0] - 2025-11-09

### Added
- Comprehensive documentation for all modules
- ARCHITECTURE.md with detailed system design
- Module-specific README files (13 modules)

### Changed
- Improved code organization and structure
- Enhanced error handling in Lambda functions

## [1.0.0] - 2025-11-01

### Added
- Initial release of Certificate Management Dashboard
- AWS Cognito authentication with JWT tokens
- Role-based access control (Admin, Operator, Viewer)
- Certificate CRUD operations via REST API
- CloudFront distribution for dashboard hosting
- DynamoDB for certificate and log storage
- EventBridge scheduled monitoring (daily at 9 AM UTC)
- SES email notifications for expiring certificates
- Terraform infrastructure-as-code (100% portable)
- Search and filter capabilities (text, status, environment)
- Responsive web interface
- CloudWatch monitoring and logging

### Security
- HTTPS-only access (TLS 1.2+)
- S3 server-side encryption (AES-256)
- Private S3 buckets with CloudFront OAI
- Secure password policies (8+ chars, complexity requirements)

---

## Bug Fix Details

### Certificate Display Issue (Fixed 2025-11-10)

**Problem**: Certificates were not appearing in dashboard despite successful upload to DynamoDB.

**Root Cause**: 
1. Lambda function was checking incorrect event property for HTTP method
2. API Gateway sends method in `event['httpMethod']` but Lambda checked `event['requestContext']['http']['method']`
3. All requests defaulted to GET, causing POST/PUT operations to return full certificate list instead of confirmation

**Solution**:
```python
# Before (incorrect)
http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')

# After (correct)
http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', 'GET')
```

**Files Modified**:
- `lambda/dashboard_api.py` - Fixed HTTP method detection
- `dashboard/dashboard.js` - Enhanced response handling for both array and object formats

**Impact**: 
- POST operations now return correct status (201) with new certificate data
- PUT operations properly update certificates
- Dashboard displays certificates immediately after adding/updating
