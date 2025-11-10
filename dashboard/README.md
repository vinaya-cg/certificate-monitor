# Dashboard Frontend Documentation

Web-based certificate management dashboard with authentication, filtering, and export capabilities.

## Overview

The dashboard provides a user-friendly interface for managing SSL/TLS certificates with real-time filtering, bulk operations, and comprehensive export functionality.

## Features

### Authentication
- **AWS Cognito Integration**: Secure JWT-based authentication
- **Session Management**: Automatic token refresh and session handling
- **Role-Based Access**: Admin, Operator, and Viewer roles

### Certificate Display
- **Statistics Cards**: Real-time counts for Active, Due for Renewal, In Progress, and Expired certificates
- **Sortable Table**: Click column headers to sort (ascending/descending)
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### Advanced Filtering (v1.2.0+)

#### Text Search
- Search across certificate name, application, and owner email
- Real-time filtering as you type

#### Date Range Filter
- **From Date**: Filter certificates expiring from specific date
- **To Date**: Filter certificates expiring until specific date
- **Clear Button**: Reset date range with one click
- Filters based on certificate expiry date

#### Multi-Criteria Filtering
Combine multiple filters simultaneously:
- Text search
- Date range (From/To)
- Status (Active, Expired, Due for Renewal, etc.)
- Environment (Production, Staging, Development, etc.)

### Certificate Operations

#### Add Certificate
- Form with validation for all required fields
- Automatic status calculation based on expiry date
- UUID generation for unique certificate IDs

#### Edit Certificate
- Update certificate details
- Automatic status recalculation
- Audit log creation

#### View Details
- Modal with complete certificate information
- Formatted display of all fields

#### Delete Certificate
- Confirmation dialog before deletion
- Permanent removal from DynamoDB

#### Renewal Process
- Multi-step renewal workflow
- File upload support for new certificate
- Incident tracking integration

### Bulk Operations

#### Excel Upload (v1.2.0+)
- **Supported Formats**: .xlsx, .xls
- **Required Columns**:
  - Certificate Name (or CommonName, Name)
  - Expiry Date (or ExpiryDate)
- **Optional Columns**:
  - Environment
  - Application
  - Status
  - Owner Email
  - Support Email
  - Type
  - Account Number

**Usage**:
1. Click "Upload Excel" button (green)
2. Select .xlsx or .xls file
3. SheetJS library parses file automatically
4. Validation checks for required fields
5. Bulk upload to API
6. Success/error summary displayed

#### CSV Export (Enhanced in v1.2.0)
- **Smart Filename**: Includes applied filters
  - Example: `certificates_export_2025-01-01_to_2025-12-31_Active_Production_2025-11-10.csv`
- **Summary Header**: First rows contain:
  - Total certificates count
  - Applied date range
  - Status and environment filters
  - Export timestamp
- **Filtered Data**: Only exports visible/filtered certificates

## File Structure

```
dashboard/
├── index.html              # Main HTML structure
├── dashboard.js            # Core JavaScript logic
├── auth.js                 # Authentication helpers
├── login.html             # Login page
├── error.html             # Error page
└── images/                # Logo and branding assets
    └── logo.png
```

## API Integration

### Endpoints

**GET /certificates**
- Fetch all certificates
- Returns: Array of certificate objects
```javascript
[
  {
    "CertificateID": "cert-xxx",
    "CommonName": "example.com",
    "Environment": "Production",
    "Status": "Active",
    "ExpiryDate": "2025-12-31",
    ...
  }
]
```

**POST /certificates**
- Add new certificate
- Returns: Status 201 with created certificate
```javascript
{
  "success": true,
  "message": "Certificate added successfully",
  "certificate": { ... }
}
```

**PUT /certificates**
- Update existing certificate
- Returns: Status 200 with success message
```javascript
{
  "success": true,
  "message": "Certificate updated successfully"
}
```

**DELETE /certificates**
- Delete certificate
- Returns: Status 200 with confirmation

### Authentication Flow

1. User enters credentials on login page
2. Cognito authenticates and returns JWT tokens
3. Tokens stored in sessionStorage
4. All API requests include Authorization header
5. Token automatically refreshed when expired

```javascript
// Authorization header format
{
  'Authorization': token,  // Direct token, no "Bearer" prefix
  'Content-Type': 'application/json'
}
```

## Key Functions

### Data Loading
```javascript
async function loadCertificates()
// Fetches all certificates from API
// Updates statistics and table
```

### Filtering
```javascript
function filterCertificates()
// Applies text search, date range, status, and environment filters
// Updates table with filtered results
```

### Date Range Management
```javascript
function clearDateRange()
// Resets From/To date inputs
// Re-applies other filters
```

### Export
```javascript
function exportData()
// Generates CSV from filtered certificates
// Includes summary header with filter metadata
// Downloads file with descriptive filename
```

### Excel Upload
```javascript
async function handleExcelUpload(event)
// Validates file type
// Loads SheetJS library dynamically
// Parses Excel to JSON
// Calls uploadCertificatesFromExcel()

async function uploadCertificatesFromExcel(certificates)
// Maps columns to API fields
// Validates required data
// Bulk uploads via POST requests
// Displays success/error summary
```

## Configuration

### API URL
Located in `dashboard.js` line 7:
```javascript
const API_URL = 'https://API_ID.execute-api.REGION.amazonaws.com/STAGE/certificates';
```

### Cognito Configuration
Located in `auth.js`:
```javascript
const COGNITO_CONFIG = {
    UserPoolId: 'REGION_POOLID',
    ClientId: 'CLIENT_ID',
    Region: 'REGION'
};
```

## Recent Changes (v1.2.0)

### Bug Fixes
1. **Certificate Display Issue**
   - Fixed API response handling for plain array format
   - Added support for both array and object responses
   - Certificates now display immediately after adding

2. **Authorization Header**
   - Removed "Bearer" prefix from Authorization header
   - Now sends token directly as Cognito expects

### New Features
1. **Date Range Filtering**
   - Added From/To date pickers
   - Filters certificates by expiry date
   - Clear button for quick reset

2. **Enhanced Export**
   - Smart filename with filter details
   - CSV summary header
   - Export button renamed to "Export Filtered"

3. **Excel Upload**
   - Bulk upload via .xlsx/.xls files
   - Flexible column mapping
   - Validation and error reporting

## Browser Compatibility

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

**Required Features**:
- ES6 JavaScript (async/await, arrow functions)
- Fetch API
- Blob API
- FileReader API
- Date input type

## Deployment

Dashboard files are deployed to S3 and served via CloudFront:

```bash
# Upload files
aws s3 cp dashboard/index.html s3://BUCKET_NAME/
aws s3 cp dashboard/dashboard.js s3://BUCKET_NAME/
aws s3 cp dashboard/auth.js s3://BUCKET_NAME/
aws s3 cp dashboard/login.html s3://BUCKET_NAME/

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"
```

## Development

### Local Testing
1. Update API_URL in dashboard.js to point to deployed API Gateway
2. Update Cognito config in auth.js
3. Open index.html in browser (won't work due to CORS - use deployed version)
4. Or use local server:
   ```bash
   python -m http.server 8000
   # Open http://localhost:8000
   ```

### Debugging
1. Open browser DevTools (F12)
2. Check Console tab for JavaScript errors
3. Check Network tab for API requests
4. Verify:
   - Request headers include Authorization
   - Response status is 200/201
   - Response body format matches expected

### Common Issues

**Certificates not loading**:
- Check API URL is correct
- Verify CORS headers in API responses
- Check Network tab for failed requests

**Filters not working**:
- Check console for JavaScript errors
- Verify element IDs match in HTML and JS
- Test with browser console: `document.getElementById('fromDate')`

**Export fails**:
- Check if pop-up blocker is enabled
- Verify at least one certificate matches filters
- Check Blob API support

## Security Considerations

1. **Token Storage**: JWT tokens stored in sessionStorage (not localStorage)
2. **HTTPS Only**: All communication over HTTPS
3. **XSS Prevention**: Input sanitization in form fields
4. **CSRF Protection**: Stateless JWT tokens
5. **Content Security Policy**: Set via CloudFront headers

## Performance Optimization

1. **Lazy Loading**: Load certificates on demand
2. **Client-Side Filtering**: No server calls for filter changes
3. **Caching**: CloudFront caches static assets
4. **Minification**: Consider minifying JS for production
5. **Compression**: Enable gzip in CloudFront

## Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast meets WCAG AA standards
- Form validation with clear error messages

## Future Enhancements

- [ ] Pagination for large certificate lists
- [ ] Certificate comparison view
- [ ] Advanced reporting with charts
- [ ] Email notification preferences
- [ ] Certificate upload (actual .crt files)
- [ ] Multi-language support
- [ ] Dark mode theme
- [ ] Mobile app version
