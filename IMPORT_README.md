# Certificate Import Tool

This tool imports certificates from the PostNL Excel file into your DynamoDB certificate management system.

## 📋 Requirements

- Python 3.7+
- AWS CLI configured with appropriate credentials
- Access to DynamoDB table `cert-management-dev-certificates`

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
# Navigate to the project directory
cd "c:\Users\vnayaneg\OneDrive - Capgemini\Desktop\Sogeti\Automation and Innovation\Run factory\certificate monitor\cert-dashboard"

# Install required Python packages
py -m pip install -r requirements.txt
```

### 2. Preview Your Data (Dry Run)

```powershell
# Preview the first 5 certificates without importing
py import_certificates.py --file "..\POSTNL Certficate Master Data.xlsx" --dry-run

# Preview more certificates
py import_certificates.py --file "..\POSTNL Certficate Master Data.xlsx" --dry-run --preview 10
```

### 3. Import Certificates

```powershell
# Import all certificates to DynamoDB
py import_certificates.py --file "..\POSTNL Certficate Master Data.xlsx"

# Import to a different table or region
py import_certificates.py --file "..\POSTNL Certficate Master Data.xlsx" --table "my-table" --region "us-east-1"
```

## 🔧 Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--file` | Path to Excel file (required) | - |
| `--table` | DynamoDB table name | `cert-management-dev-certificates` |
| `--region` | AWS region | `eu-west-1` |
| `--dry-run` | Preview without importing | `false` |
| `--preview` | Number of certificates to preview | `5` |

## 📊 What the Script Does

### Data Mapping
The script maps Excel columns to DynamoDB attributes:

| Excel Column | DynamoDB Attribute | Notes |
|--------------|-------------------|-------|
| Serial Number | SerialNumber | String |
| Certificate Name | CertificateName | String |
| Expiry Date | ExpiryDate | Parsed to YYYY-MM-DD format |
| AccountNumber | AccountNumber | String |
| Application | Application | String |
| ENVIRONMENT | Environment | String |
| Type | Type | String |
| Status | Status | String |
| OwnerEmail | OwnerEmail | String |
| Support team Email | SupportEmail | String |
| IncidentNumber | IncidentNumber | Optional |
| RenewedBy | RenewedBy | Optional |
| RenewalLog | RenewalLog | Optional |
| UploadS3Key | UploadS3Key | Optional |
| - | CertificateID | Auto-generated UUID |
| - | LastUpdatedOn | Current timestamp |

### Features
- ✅ **Batch processing** - Imports in batches of 25 for efficiency
- ✅ **Data validation** - Parses dates, handles empty values
- ✅ **Unique IDs** - Generates unique CertificateID for each certificate
- ✅ **Error handling** - Continues on errors, reports success/failure counts
- ✅ **Dry run mode** - Preview data before importing
- ✅ **Progress tracking** - Shows batch progress during import

## 🔐 Required AWS Permissions

Your AWS credentials need these DynamoDB permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:BatchWriteItem",
                "dynamodb:DescribeTable"
            ],
            "Resource": "arn:aws:dynamodb:eu-west-1:*:table/cert-management-dev-certificates"
        }
    ]
}
```

## 🎯 After Import

Once imported, your certificates will be available in:

1. **Dashboard**: http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com
2. **DynamoDB Console**: Check the `cert-management-dev-certificates` table
3. **Monitoring**: Lambda function will monitor for expiring certificates

## 🔍 Verification

Check the import was successful:

```powershell
# Count certificates in DynamoDB
aws dynamodb scan --table-name cert-management-dev-certificates --region eu-west-1 --select "COUNT" --query "Count"

# View first few certificates
aws dynamodb scan --table-name cert-management-dev-certificates --region eu-west-1 --limit 5
```

## 🐛 Troubleshooting

### Common Issues

**"AWS credentials not found"**
```powershell
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region (eu-west-1)
```

**"Table does not exist"**
- Ensure the Terraform infrastructure is deployed
- Check the table name and region are correct

**"Date parsing errors"**
- The script handles most date formats automatically
- Check the Excel file for unusual date formats

**"Empty certificates"**
- Ensure your Excel file has data in the expected columns
- Check that Certificate Name column isn't empty

## 📈 Example Output

```
🔧 PostNL Certificate Import Tool
==================================================
📖 Reading Excel file: ..\POSTNL Certficate Master Data.xlsx
📋 Found 15 columns: ['Serial Number', 'Certificate  Name', ...]
📊 Total rows in Excel: 192
✅ Processed 190 certificates (2 empty rows skipped)

📋 PREVIEW: First 5 certificates:
================================================================================

🔖 Certificate 1:
   ID: cert-a1b2c3d4
   Name: api.postnl.nl
   Environment: PRD
   Application: APT
   Expiry: 2025-11-03
   Status: Active
   Owner: Vinaya-c.nayanegali@capgemini.com

... and 185 more certificates
================================================================================

✅ Connected to DynamoDB table: cert-management-dev-certificates in eu-west-1

⚠️  Import 190 certificates to cert-management-dev-certificates? (y/N): y

🚀 Starting import of 190 certificates...
📦 Processing batch 1/8 (25 items)...
✅ Batch 1 completed successfully
📦 Processing batch 2/8 (25 items)...
✅ Batch 2 completed successfully
...

📊 Import Summary:
   ✅ Successfully imported: 190
   ❌ Failed: 0
   📈 Success rate: 100.0%

🎉 Import completed! Certificates are now available in your dashboard:
   🌐 Dashboard: http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com
```