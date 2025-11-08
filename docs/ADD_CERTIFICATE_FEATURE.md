# Certificate Addition Feature - Implementation Guide

## 🎉 Overview

The dashboard now supports **adding and updating certificates directly through the web interface** with full DynamoDB persistence!

## ✅ What's New

### 1. Enhanced Lambda API (dashboard_api.py)

The Lambda function now supports multiple HTTP methods:

- **GET** - Fetch all certificates (existing)
- **POST** - Add new certificate ✨ NEW
- **PUT** - Update existing certificate ✨ NEW

#### POST Request - Add Certificate

**Endpoint:** `https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url.eu-west-1.on.aws/`

**Method:** POST

**Request Body:**
```json
{
  "CertificateName": "api.example.com",
  "Environment": "Production",
  "Application": "API Gateway",
  "ExpiryDate": "2026-03-15",
  "Type": "SSL/TLS",
  "OwnerEmail": "owner@example.com",
  "SupportEmail": "support@example.com",
  "AccountNumber": "ACC-12345"
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Certificate added successfully",
  "certificate": {
    "CertificateID": "cert-abc123...",
    "CertificateName": "api.example.com",
    "Status": "Active",
    "DaysUntilExpiry": "142",
    ...
  }
}
```

**Response (Error - 400):**
```json
{
  "error": "Missing required fields",
  "missing": ["CertificateName", "OwnerEmail"]
}
```

#### PUT Request - Update Certificate

**Request Body:**
```json
{
  "CertificateID": "cert-abc123...",
  "ExpiryDate": "2026-06-15",
  "Status": "Active",
  "OwnerEmail": "newemail@example.com"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Certificate updated successfully"
}
```

### 2. Automatic Calculations

The Lambda function automatically calculates:

- **Status**: Based on expiry date
  - `Active` - More than 30 days until expiry
  - `Due for Renewal` - 1-30 days until expiry
  - `Expired` - Past expiry date

- **DaysUntilExpiry**: Calculated from current date to expiry date

### 3. Audit Logging

Every create/update operation is logged to `cert-management-dev-certificate-logs` table:

```json
{
  "LogID": "log-xyz789...",
  "CertificateID": "cert-abc123...",
  "Action": "CREATE",
  "Timestamp": "2025-10-29T01:15:00Z",
  "Details": "Certificate api.example.com added via dashboard",
  "PerformedBy": "owner@example.com"
}
```

### 4. Dashboard Integration

The main dashboard (`index.html`) now:

- ✅ Posts new certificates to DynamoDB via API
- ✅ Updates existing certificates via API
- ✅ Automatically refreshes after add/update
- ✅ Shows success/error messages

### 5. Test Suite

**URL:** http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/test-add-certificate.html

**Features:**
- 6 automated validation tests
- Real-time API integration testing
- 3 pre-configured test scenarios
- Live logging with timestamps
- Visual statistics dashboard

**Tests Performed:**
1. ✅ Validate Required Fields
2. ✅ Validate Email Format
3. ✅ Validate Expiry Date
4. ✅ Status Calculation
5. ✅ Certificate ID Generation
6. ✅ **API POST Request** (actual DynamoDB insertion)

## 🧪 Testing Guide

### Manual Testing

1. **Open Test Suite:**
   ```
   http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/test-add-certificate.html
   ```

2. **Fill Sample Data:**
   - Click "📋 Fill Sample Data" button
   - This populates all fields with valid test data

3. **Add Certificate:**
   - Click "➕ Add Certificate" button
   - Watch all 6 tests execute
   - Test #6 performs actual API POST to DynamoDB

4. **Verify in Dashboard:**
   - Open main dashboard: http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/
   - Search for your test certificate
   - Confirm it appears in the table

### Automated Testing

Click "▶️ Run All Tests" button to execute 3 automated scenarios:

1. **Valid Active Certificate** (90 days expiry)
2. **Certificate Due for Renewal** (15 days expiry)
3. **Test Environment Certificate** (180 days expiry)

### Testing from Main Dashboard

1. Open dashboard: http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com/
2. Click "Add Certificate" button
3. Fill the form with certificate details
4. Click "Save Certificate"
5. Certificate is added to DynamoDB and appears in the table

## 📋 Required Fields

When adding a certificate, these fields are **mandatory**:

- ✅ Certificate Name
- ✅ Environment
- ✅ Application
- ✅ Expiry Date
- ✅ Owner Email

Optional fields:
- Type (defaults to "SSL/TLS")
- Support Email
- Account Number
- Serial Number

## 🔍 Validation Rules

1. **Email Format**: Must be valid email (contains @ and domain)
2. **Expiry Date**: Must be in YYYY-MM-DD format
3. **Required Fields**: Cannot be empty or null
4. **Certificate ID**: Auto-generated if not provided

## 🐛 Error Handling

The API returns clear error messages:

**Missing Fields:**
```json
{
  "error": "Missing required fields",
  "missing": ["CertificateName", "ExpiryDate"]
}
```

**Invalid Request:**
```json
{
  "error": "CertificateID is required"
}
```

**Server Error:**
```json
{
  "error": "Failed to add certificate",
  "message": "Detailed error message here"
}
```

## 📊 Database Schema

Certificates are stored with these fields:

```
CertificateID         : cert-abc123... (auto-generated UUID)
CertificateName       : api.example.com
Environment           : Production
Application           : API Gateway
ExpiryDate            : 2026-03-15
Type                  : SSL/TLS
Status                : Active (auto-calculated)
DaysUntilExpiry       : 142 (auto-calculated)
OwnerEmail            : owner@example.com
SupportEmail          : support@example.com
AccountNumber         : ACC-12345
SerialNumber          : (optional)
LastUpdatedOn         : 2025-10-29T01:15:00Z (auto-set)
CreatedOn             : 2025-10-29T01:15:00Z (auto-set)
Version               : 1
ImportedFrom          : Dashboard
```

## 🔐 Security

- CORS is configured in Lambda Function URL (not in code)
- No authentication currently implemented (add IAM/Cognito if needed)
- All operations logged for audit trail
- DynamoDB encryption at rest enabled

## 🚀 Next Steps

**Recommended Enhancements:**

1. **Authentication**
   - Add AWS Cognito user authentication
   - Require login to add/edit certificates

2. **File Upload**
   - Support uploading actual certificate files (.crt, .pem)
   - Store in S3 uploads bucket

3. **Bulk Import via Dashboard**
   - Excel upload through web interface
   - Preview before importing

4. **Email Notifications**
   - Send email when certificate is added/updated
   - Notify owner of new certificate assignment

5. **Certificate Validation**
   - Validate certificate expiry date against actual file
   - Parse certificate details from uploaded file

## 📞 Support

For issues or questions:
- Check CloudWatch logs: `/aws/lambda/cert-management-dev-dashboard-api`
- Review DynamoDB table: `cert-management-dev-certificates`
- Check audit logs: `cert-management-dev-certificate-logs`

## 📝 Code Files Modified

1. **lambda/dashboard_api.py** - Added POST/PUT handlers
2. **dashboard/dashboard.js** - Updated add/update functions
3. **test-add-certificate.html** - Complete test suite

All files deployed and ready to use! 🎉
