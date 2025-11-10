# Troubleshooting Guide

Common issues and their solutions for the Certificate Management Dashboard.

## Table of Contents
- [Dashboard Issues](#dashboard-issues)
- [API Issues](#api-issues)
- [Authentication Issues](#authentication-issues)
- [Certificate Upload Issues](#certificate-upload-issues)
- [Deployment Issues](#deployment-issues)
- [Performance Issues](#performance-issues)

---

## Dashboard Issues

### Certificates Not Displaying

**Symptoms**: Dashboard loads but shows 0 certificates, even after adding new ones.

**Common Causes & Solutions**:

1. **Browser Cache Issue**
   - **Solution**: Clear browser cache or open in incognito/private window
   - Press `Ctrl+Shift+Delete` → Clear cache
   - Or use incognito: `Ctrl+Shift+N` (Chrome/Edge) or `Ctrl+Shift+P` (Firefox)

2. **CloudFront Cache Not Invalidated**
   - **Solution**: Manually invalidate CloudFront cache
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id YOUR_DISTRIBUTION_ID \
     --paths "/*"
   ```

3. **Lambda HTTP Method Detection Issue** (Fixed in v1.2.0)
   - **Symptoms**: POST/PUT requests return full certificate list instead of confirmation
   - **Verification**: Check Lambda logs in CloudWatch
   ```bash
   aws logs tail /aws/lambda/cert-management-dev-secure-dashboard-api --follow
   ```
   - **Solution**: Ensure Lambda uses correct event property for HTTP method
   ```python
   # Correct implementation
   http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', 'GET')
   ```

4. **API Response Format Mismatch**
   - **Symptoms**: Console error: "certificatesData.slice is not a function"
   - **Solution**: Dashboard should handle both array and object responses
   ```javascript
   // In dashboard.js - fetchCertificatesFromAPI()
   if (Array.isArray(data)) {
       return data;
   } else if (data.certificates && Array.isArray(data.certificates)) {
       return data.certificates;
   }
   ```

### Filters Not Working

**Issue**: Date range, status, or environment filters don't filter certificates.

**Solutions**:
1. Check browser console for JavaScript errors (F12 → Console tab)
2. Verify filter elements exist in DOM:
   ```javascript
   document.getElementById('fromDate')
   document.getElementById('toDate')
   document.getElementById('statusFilter')
   ```
3. Ensure `filterCertificates()` function is defined and called on change events

### Export Not Working

**Issue**: Clicking "Export Filtered" doesn't download CSV file.

**Solutions**:
1. **Browser Pop-up Blocker**: Disable for dashboard URL
2. **No Filtered Data**: Ensure at least one certificate matches filters
3. **JavaScript Error**: Check console (F12) for errors
4. **Blob API Not Supported**: Update browser to latest version

---

## API Issues

### 401 Unauthorized Errors

**Symptoms**: API calls return 401 status code.

**Causes & Solutions**:

1. **Expired JWT Token**
   - **Solution**: Logout and login again to get fresh token
   - JWT tokens expire after 60 minutes by default

2. **Missing Authorization Header**
   - **Check**: Browser DevTools → Network tab → Request Headers
   - **Should see**: `Authorization: <token>` (without "Bearer" prefix)
   - **Fix in dashboard.js**:
   ```javascript
   async function getAuthHeaders() {
       const token = await getIdToken();
       return {
           'Authorization': token,  // No "Bearer" prefix
           'Content-Type': 'application/json'
       };
   }
   ```

3. **Cognito Authorizer Misconfigured**
   - **Verify**: API Gateway → Authorizers → Check Cognito User Pool ID
   ```bash
   aws apigateway get-authorizers --rest-api-id YOUR_API_ID
   ```

### 500 Internal Server Error

**Symptoms**: API returns 500 error for valid requests.

**Debug Steps**:

1. **Check Lambda Logs**:
   ```bash
   aws logs tail /aws/lambda/cert-management-dev-secure-dashboard-api --follow
   ```

2. **Common Causes**:
   - Missing environment variables (CERTIFICATES_TABLE)
   - DynamoDB permission issues
   - Invalid JSON in request body
   - Python syntax errors

3. **Verify Lambda Configuration**:
   ```bash
   aws lambda get-function-configuration \
     --function-name cert-management-dev-secure-dashboard-api
   ```

### CORS Errors

**Symptoms**: Browser console shows "CORS policy" error.

**Solutions**:

1. **Missing CORS Headers in Lambda Response**:
   ```python
   # Ensure all Lambda responses include these headers
   CORS_HEADERS = {
       'Content-Type': 'application/json',
       'Access-Control-Allow-Origin': '*',
       'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
       'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
   }
   
   return {
       'statusCode': 200,
       'headers': CORS_HEADERS,
       'body': json.dumps(data)
   }
   ```

2. **API Gateway CORS Configuration**:
   - Verify OPTIONS method exists with Mock integration
   - Check method response headers include CORS headers

---

## Authentication Issues

### Cannot Login

**Issue**: Login button does nothing or shows error.

**Solutions**:

1. **Verify Cognito User Exists**:
   ```bash
   aws cognito-idp list-users \
     --user-pool-id YOUR_USER_POOL_ID \
     --region eu-west-1
   ```

2. **Check User Status**:
   - User must be CONFIRMED status
   - Password must meet complexity requirements (8+ chars, upper, lower, number)

3. **Create User Manually**:
   ```bash
   aws cognito-idp admin-create-user \
     --user-pool-id YOUR_USER_POOL_ID \
     --username user@example.com \
     --user-attributes Name=email,Value=user@example.com \
     --temporary-password TempPass123! \
     --region eu-west-1
   
   # Set permanent password
   aws cognito-idp admin-set-user-password \
     --user-pool-id YOUR_USER_POOL_ID \
     --username user@example.com \
     --password Admin@123 \
     --permanent
   ```

### Session Expires Too Quickly

**Issue**: User gets logged out frequently.

**Solution**: Increase token expiration in Cognito:
- Default: 60 minutes (ID token), 30 days (refresh token)
- Increase via Terraform: `id_token_validity` in Cognito User Pool Client configuration

---

## Certificate Upload Issues

### Excel Upload Fails

**Issue**: Excel file upload shows error or doesn't process.

**Common Issues**:

1. **Invalid File Format**:
   - **Supported**: .xlsx, .xls
   - **Not Supported**: .csv, .txt, .numbers

2. **Missing Required Columns**:
   - **Required**: Certificate Name (or CommonName/Name), Expiry Date
   - **Optional**: Environment, Application, Status, Owner Email, etc.

3. **Date Format Issues**:
   - **Supported**: Excel serial numbers, ISO dates (YYYY-MM-DD)
   - **Fix**: Ensure Expiry Date column is formatted as Date in Excel

4. **Large File Size**:
   - **Limit**: Browser memory constraints
   - **Solution**: Split into smaller files (recommended <500 rows per file)

### Manual Certificate Add Fails

**Issue**: Add Certificate form submission fails.

**Debug**:
1. Check browser console for validation errors
2. Verify all required fields filled:
   - Certificate Name
   - Expiry Date
   - Environment
3. Check API response in Network tab (F12)

---

## Deployment Issues

### Terraform Apply Fails

**Common Errors**:

1. **AWS Credentials Not Configured**:
   ```bash
   aws configure
   # Or use environment variables
   export AWS_ACCESS_KEY_ID=xxx
   export AWS_SECRET_ACCESS_KEY=xxx
   export AWS_DEFAULT_REGION=eu-west-1
   ```

2. **S3 Bucket Name Already Exists**:
   - **Error**: "BucketAlreadyExists"
   - **Solution**: S3 bucket names are globally unique. Change `project_name` or add random suffix

3. **SES Email Not Verified**:
   - **Error**: Email sending fails
   - **Solution**: Verify email in SES
   ```bash
   aws ses verify-email-identity \
     --email-address your-email@example.com \
     --region eu-west-1
   ```

4. **IAM Permission Issues**:
   - **Error**: "AccessDenied" during terraform apply
   - **Solution**: Ensure AWS user has admin permissions or specific IAM policies

### CloudFront Distribution Not Working

**Issue**: Dashboard URL returns 403 Forbidden.

**Solutions**:

1. **Check S3 Bucket Policy**: Should allow CloudFront OAI
2. **Verify index.html Exists**:
   ```bash
   aws s3 ls s3://cert-management-dev-secure-dashboard-xxx/
   ```
3. **Upload Dashboard Files**:
   ```bash
   aws s3 cp dashboard/index.html s3://YOUR_BUCKET/
   aws s3 cp dashboard/dashboard.js s3://YOUR_BUCKET/
   ```

---

## Performance Issues

### Dashboard Loads Slowly

**Optimizations**:

1. **Enable CloudFront Caching**:
   - Default TTL: 86400 seconds (24 hours)
   - Increase for static assets

2. **Reduce Certificate Count**:
   - Use pagination (implement client-side)
   - Archive expired certificates to separate table

3. **Optimize Lambda**:
   - Increase memory (more memory = more CPU)
   - Add DynamoDB indexes for common queries

### API Response Slow

**Debug Steps**:

1. **Check Lambda Duration**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Duration \
     --dimensions Name=FunctionName,Value=cert-management-dev-secure-dashboard-api \
     --start-time 2025-11-10T00:00:00Z \
     --end-time 2025-11-10T23:59:59Z \
     --period 3600 \
     --statistics Average,Maximum
   ```

2. **DynamoDB Performance**:
   - Check if using scan vs query (scan is slower)
   - Consider adding GSI for frequent queries
   - Use pagination for large result sets

---

## Getting Help

If issues persist:

1. **Check Logs**:
   - Lambda: CloudWatch Logs Groups
   - API Gateway: Enable execution logging
   - CloudFront: Access logs in S3

2. **Enable Debug Mode**:
   - Add `console.log()` statements in dashboard.js
   - Add `print()` statements in Lambda functions
   - View in browser console (F12) or CloudWatch

3. **Contact Support**:
   - GitHub Issues: https://github.com/vinaya-cg/certificate-monitor/issues
   - Include: Error messages, logs, terraform version, AWS region

---

## Quick Diagnostics Checklist

Use this checklist for initial troubleshooting:

- [ ] Browser cache cleared or using incognito window
- [ ] User authenticated and token not expired
- [ ] Lambda functions deployed and active
- [ ] DynamoDB tables exist and have data
- [ ] API Gateway endpoints configured correctly
- [ ] CORS headers present in API responses
- [ ] CloudFront distribution deployed and accessible
- [ ] S3 bucket contains dashboard files (index.html, dashboard.js)
- [ ] Cognito user pool and client configured
- [ ] Environment variables set in Lambda functions
- [ ] IAM roles have necessary permissions
- [ ] CloudWatch logs reviewed for errors
