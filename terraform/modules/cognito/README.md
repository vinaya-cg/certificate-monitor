# Cognito Module

This module manages AWS Cognito resources for user authentication and authorization.

## Purpose

Provides secure user authentication, password management, and role-based access control (RBAC) for the certificate dashboard using AWS Cognito User Pool.

## Resources Created

### Cognito User Pool (`aws_cognito_user_pool.main`)
- **Purpose**: Central user directory with authentication capabilities
- **Password Policy**:
  - Minimum length: 8 characters
  - Requires: uppercase, lowercase, number, symbol
  - Password expiry: Never (users manage their own passwords)
- **User Attributes**:
  - Email (required, mutable)
  - Name (optional, mutable)
  - Email verification required
- **Account Recovery**: Email-only recovery
- **MFA Configuration**: Optional (can be enabled per user)
- **Advanced Security**: AUDIT mode (logs suspicious activity)

### Cognito User Pool Client (`aws_cognito_user_pool_client.main`)
- **Purpose**: Application client for dashboard authentication
- **Auth Flows Enabled**:
  - `ALLOW_USER_PASSWORD_AUTH` - Username/password authentication
  - `ALLOW_REFRESH_TOKEN_AUTH` - Token refresh
  - `ALLOW_USER_SRP_AUTH` - Secure Remote Password protocol
- **Token Validity**:
  - Access Token: 60 minutes
  - ID Token: 60 minutes
  - Refresh Token: 30 days
- **OAuth Configuration**:
  - Allowed flows: `code` (authorization code grant)
  - Scopes: `email`, `openid`, `profile`
  - Callback URLs: CloudFront URL, localhost (for development)
  - Logout URLs: CloudFront URL, localhost

### Cognito Identity Pool (`aws_cognito_identity_pool.main`)
- **Purpose**: Provides AWS credentials for authenticated users
- **Authentication Providers**: Cognito User Pool
- **Unauthenticated Access**: Disabled (only authenticated users)

### Cognito User Pool Domain (`aws_cognito_user_pool_domain.main`)
- **Purpose**: Provides hosted UI for authentication (optional)
- **Domain**: `{project_name}-{environment}-{random_suffix}`
- **Example**: `cert-management-dev-secure-dz243x46.auth.eu-west-1.amazoncognito.com`

### Cognito User Groups
Three groups for role-based access control:

#### 1. Admins Group (`aws_cognito_user_group.admins`)
- **Permissions**: Full access (view, add, edit, delete)
- **Precedence**: 1 (highest priority)
- **Use Case**: System administrators, project owners

#### 2. Operators Group (`aws_cognito_user_group.operators`)
- **Permissions**: View, add, edit (no delete)
- **Precedence**: 2
- **Use Case**: Certificate managers, support teams

#### 3. Viewers Group (`aws_cognito_user_group.viewers`)
- **Permissions**: View only
- **Precedence**: 3 (lowest priority)
- **Use Case**: Auditors, stakeholders

### Cognito Users
Three default users (one per group):

#### 1. Admin User (`aws_cognito_user.admin`)
- **Email**: `var.admin_user`
- **Attributes**: `email_verified = true`, `name = "Admin User"`
- **Initial State**: `FORCE_CHANGE_PASSWORD` (must change password on first login)
- **Group**: Admins
- **Temporary Password**: Sent via SES email

#### 2. Operator User (`aws_cognito_user.operator`)
- **Email**: `var.operator_user`
- **Attributes**: `email_verified = true`, `name = "Operator User"`
- **Initial State**: `FORCE_CHANGE_PASSWORD`
- **Group**: Operators
- **Temporary Password**: Sent via SES email

#### 3. Viewer User (`aws_cognito_user.viewer`)
- **Email**: `var.viewer_user`
- **Attributes**: `email_verified = true`, `name = "Viewer User"`
- **Initial State**: `FORCE_CHANGE_PASSWORD`
- **Group**: Viewers
- **Temporary Password**: Sent via SES email

### Group Memberships (`aws_cognito_user_in_group`)
- **admin_group_membership**: Adds admin user to Admins group
- **operator_group_membership**: Adds operator user to Operators group
- **viewer_group_membership**: Adds viewer user to Viewers group

### SES Email Identity (`aws_ses_email_identity.sender`)
- **Purpose**: Verify sender email for user registration notifications
- **Email**: `var.sender_email`
- **Required**: Must be verified before Cognito can send emails
- **Note**: In SES Sandbox Mode, recipient emails must also be verified

## Inputs

| Variable | Type | Description | Required | Default |
|----------|------|-------------|----------|---------|
| `project_name` | `string` | Project name prefix for resources | Yes | - |
| `environment` | `string` | Environment name (dev, dev-secure, prod) | Yes | - |
| `sender_email` | `string` | Email address for sending Cognito notifications | Yes | - |
| `admin_user` | `string` | Email address for admin user | Yes | - |
| `operator_user` | `string` | Email address for operator user | Yes | - |
| `viewer_user` | `string` | Email address for viewer user | Yes | - |
| `cloudfront_url` | `string` | CloudFront distribution URL for OAuth callbacks | Yes | - |
| `random_suffix` | `string` | Random suffix for unique resource names | Yes | - |
| `aws_region` | `string` | AWS region for deployment | Yes | - |

## Outputs

| Output | Description | Used By |
|--------|-------------|---------|
| `user_pool_id` | Cognito User Pool ID | API Gateway authorizer, Dashboard auth config |
| `user_pool_arn` | Cognito User Pool ARN | IAM policies, resource references |
| `client_id` | Cognito User Pool Client ID | Dashboard auth config |
| `identity_pool_id` | Cognito Identity Pool ID | Dashboard AWS SDK config |
| `domain_url` | Cognito hosted UI domain URL | OAuth flows (optional) |
| `users` | Map of username → email for created users | Documentation, testing |

## Example Usage

```hcl
module "cognito" {
  source = "../../modules/cognito"

  project_name   = "cert-management"
  environment    = "dev-secure"
  sender_email   = "vinaya-c.nayanegali@capgemini.com"
  admin_user     = "admin@example.com"
  operator_user  = "operator@example.com"
  viewer_user    = "viewer@example.com"
  cloudfront_url = "https://d3bqyfjow8topp.cloudfront.net"
  random_suffix  = "dz243x46"
  aws_region     = "eu-west-1"
}
```

## Authentication Flow

```
1. User navigates to CloudFront URL
   ↓
2. Dashboard redirects to login.html
   ↓
3. User enters email + password
   ↓
4. auth-cognito.js calls Cognito User Pool
   ↓
5. Cognito validates credentials
   ↓
6. If FORCE_CHANGE_PASSWORD status:
   - Show password change modal
   - User sets new password
   - Cognito updates user status to CONFIRMED
   ↓
7. Cognito returns JWT tokens:
   - ID Token (user identity)
   - Access Token (API authorization)
   - Refresh Token (token renewal)
   ↓
8. Dashboard stores tokens in sessionStorage
   ↓
9. API requests include Access Token in Authorization header
   ↓
10. API Gateway validates token with Cognito
    ↓
11. Lambda function receives authenticated user context
```

## Security Features

### Password Policy
- **Minimum Length**: 8 characters
- **Complexity**: Requires uppercase, lowercase, number, symbol
- **Expiry**: Never (users manage passwords)
- **Temporary Password**: Auto-generated, sent via SES email

### Token Security
- **Short-lived Tokens**: Access/ID tokens valid for 60 minutes
- **Refresh Token**: Valid for 30 days
- **Secure Storage**: sessionStorage (cleared on browser close)
- **HTTPS Only**: Tokens never transmitted over HTTP

### Advanced Security
- **Mode**: AUDIT (logs suspicious activity)
- **Detections**:
  - Compromised credentials
  - Unusual sign-in attempts
  - Account takeover attempts
- **Actions**: Log events to CloudWatch (does not block)

### Email Verification
- **Required**: Email must be verified before login
- **Process**:
  1. Admin creates user via Terraform
  2. Cognito sends verification email via SES
  3. User verifies email (automatic if admin sets email_verified = true)
  4. User can now log in

### MFA (Multi-Factor Authentication)
- **Status**: Optional (not enforced by default)
- **Types**: SMS, TOTP (Time-based One-Time Password)
- **Configuration**: Users can enable MFA in their profile

## SES Integration

### Email Requirements
- **Sender Email**: Must be verified in SES before deployment
- **SES Sandbox Mode**:
  - Can only send TO verified email addresses
  - Recipient emails (admin_user, operator_user, viewer_user) must be verified
  - Limitation: Cannot send to arbitrary emails
- **SES Production Mode**:
  - Can send to any email address
  - Request access: AWS Console → SES → Account Dashboard → Request Production Access
  - Approval: Usually 24-48 hours
  - Cost: Free (pay only for emails sent)

### Verify Email Address
```bash
aws ses verify-email-identity \
  --email-address your-email@example.com \
  --region eu-west-1
```

Check verification status:
```bash
aws ses get-identity-verification-attributes \
  --identities your-email@example.com \
  --region eu-west-1
```

## User Management

### Create Additional Users (CLI)
```bash
aws cognito-idp admin-create-user \
  --user-pool-id eu-west-1_cWIxi5SPd \
  --username new-user@example.com \
  --user-attributes Name=email,Value=new-user@example.com Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --region eu-west-1
```

### Add User to Group
```bash
aws cognito-idp admin-add-user-to-group \
  --user-pool-id eu-west-1_cWIxi5SPd \
  --username new-user@example.com \
  --group-name Operators \
  --region eu-west-1
```

### Reset User Password
```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id eu-west-1_cWIxi5SPd \
  --username user@example.com \
  --password "NewPass123!" \
  --permanent \
  --region eu-west-1
```

### List Users
```bash
aws cognito-idp list-users \
  --user-pool-id eu-west-1_cWIxi5SPd \
  --region eu-west-1
```

### Delete User
```bash
aws cognito-idp admin-delete-user \
  --user-pool-id eu-west-1_cWIxi5SPd \
  --username user@example.com \
  --region eu-west-1
```

## Troubleshooting

### Issue: "Email address is not verified"
**Cause**: SES email identity not verified  
**Solution**: Verify sender email in SES:
```bash
aws ses verify-email-identity --email-address sender@example.com --region eu-west-1
```

### Issue: Users not receiving temporary passwords
**Cause**: SES in Sandbox Mode, recipient email not verified  
**Solution**:
1. Verify recipient emails in SES, OR
2. Request Production Access for SES

### Issue: "Cannot modify an already provided email"
**Cause**: Attempting to update read-only Cognito attribute  
**Solution**: Don't pass user attributes during password change (fixed in current version)

### Issue: Password doesn't meet requirements
**Cause**: Password lacks required complexity  
**Solution**: Ensure password has:
- At least 8 characters
- Uppercase letter (A-Z)
- Lowercase letter (a-z)
- Number (0-9)
- Special character (!@#$%^&*)

### Issue: Token expired errors
**Cause**: Access token expired after 60 minutes  
**Solution**: Dashboard automatically refreshes tokens using refresh token

## Best Practices

1. **Email Verification**: Always verify SES emails before deployment
2. **SES Production**: Request production access for real-world usage
3. **Password Policy**: Keep strong password requirements
4. **Token Storage**: Use sessionStorage (not localStorage) for automatic cleanup
5. **Group Membership**: Add users to appropriate groups for RBAC
6. **MFA**: Enable MFA for admin users
7. **Advanced Security**: Monitor CloudWatch logs for suspicious activity
8. **Temporary Passwords**: Use strong temporary passwords, force change on first login

## Dependencies

- **AWS Provider**: Requires AWS provider configured
- **SES Email**: Sender email must be verified before user creation
- **Random Suffix**: Provided by parent module for unique domain names

## Cost

**Cognito User Pool**: Free for first 50,000 MAUs (Monthly Active Users)  
**Cognito Identity Pool**: Free  
**SES**: $0.10 per 1,000 emails sent (production mode)  

Total estimated cost: **$0-5/month** (depending on user count and email volume)

## Related Modules

- **API Gateway**: Uses Cognito User Pool as authorizer
- **Dashboard Secure**: Receives Cognito config for frontend authentication
- **CloudFront**: Provides callback URL for OAuth flows

## References

- [Cognito User Pools Documentation](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html)
- [Cognito Password Policies](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-policies.html)
- [SES Sandbox Mode](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html)
- [JWT Authentication](https://jwt.io/introduction)
