"""
ACM Certificate Synchronization Lambda Function

This Lambda function synchronizes certificates from AWS Certificate Manager (ACM)
across multiple AWS accounts into the centralized certificate management dashboard.

Features:
- Scans ACM certificates from the deployment account (can be extended to cross-account)
- Prevents duplicates using AccountNumber + CommonName composite key
- Preserves manually entered data (OwnerEmail, SupportEmail, notes)
- Updates ACM-specific fields (ExpiryDate, Status, ARN)
- Supports both scheduled (EventBridge) and manual (API) triggers

Environment Variables:
- CERTIFICATES_TABLE: DynamoDB table name for certificates
- REGION: AWS region
- SYNC_CONFIG_TABLE: (Optional) DynamoDB table storing account configuration
"""

import json
import boto3
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
acm_client = boto3.client('acm')
sts_client = boto3.client('sts')

# Environment variables
CERTIFICATES_TABLE = os.environ.get('CERTIFICATES_TABLE', 'cert-management-dev-secure-certificates')
REGION = os.environ.get('REGION', 'eu-west-1')

# Preserve these fields from manual entries - never overwrite
PRESERVE_FIELDS = [
    'OwnerEmail',
    'SupportEmail',
    'Application',
    'Notes',
    'RenewalHistory',
    'CustomTags',
    'IncidentNumber'
]


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal to int/float for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Main Lambda handler for ACM certificate synchronization
    
    Args:
        event: Lambda event (can be EventBridge scheduled event or API Gateway request)
        context: Lambda context
        
    Returns:
        dict: Sync results including counts and any errors
    """
    print(f"ACM Sync Lambda started at {datetime.now(timezone.utc).isoformat()}")
    print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")
    
    try:
        # Determine if this is a manual trigger or scheduled
        is_manual = event.get('httpMethod') == 'POST' or event.get('source') != 'aws.events'
        
        # Get current AWS account
        current_account = sts_client.get_caller_identity()['Account']
        print(f"Current AWS Account: {current_account}")
        
        # Initialize sync statistics
        stats = {
            'startTime': datetime.now(timezone.utc).isoformat(),
            'accountsScanned': 0,
            'certificatesFound': 0,
            'certificatesAdded': 0,
            'certificatesUpdated': 0,
            'certificatesSkipped': 0,
            'errors': []
        }
        
        # Get accounts to scan (start with current account only)
        accounts_to_scan = get_accounts_to_scan(current_account)
        
        # Scan each account
        for account_config in accounts_to_scan:
            account_id = account_config['accountId']
            regions = account_config.get('regions', [REGION])
            
            print(f"\n{'='*60}")
            print(f"Scanning Account: {account_id} ({account_config.get('accountName', 'Unknown')})")
            print(f"Regions: {', '.join(regions)}")
            print(f"{'='*60}")
            
            try:
                account_stats = sync_account_certificates(account_id, regions, account_config)
                
                # Aggregate statistics
                stats['accountsScanned'] += 1
                stats['certificatesFound'] += account_stats['found']
                stats['certificatesAdded'] += account_stats['added']
                stats['certificatesUpdated'] += account_stats['updated']
                stats['certificatesSkipped'] += account_stats['skipped']
                
            except Exception as account_error:
                error_msg = f"Error scanning account {account_id}: {str(account_error)}"
                print(f"ERROR: {error_msg}")
                stats['errors'].append(error_msg)
        
        # Finalize statistics
        stats['endTime'] = datetime.now(timezone.utc).isoformat()
        stats['success'] = len(stats['errors']) == 0
        
        print(f"\n{'='*60}")
        print("ACM SYNC COMPLETED")
        print(f"{'='*60}")
        print(f"Accounts Scanned: {stats['accountsScanned']}")
        print(f"Certificates Found: {stats['certificatesFound']}")
        print(f"Certificates Added: {stats['certificatesAdded']}")
        print(f"Certificates Updated: {stats['certificatesUpdated']}")
        print(f"Certificates Skipped: {stats['certificatesSkipped']}")
        print(f"Errors: {len(stats['errors'])}")
        print(f"{'='*60}\n")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(stats, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"CRITICAL ERROR in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'ACM sync failed'
            })
        }


def get_accounts_to_scan(current_account: str) -> List[Dict]:
    """
    Get list of AWS accounts to scan for ACM certificates
    
    For now, returns only the current account. Future enhancement: 
    Read from DynamoDB config table or SSM Parameter Store
    
    Args:
        current_account: Current AWS account ID
        
    Returns:
        List of account configuration dictionaries
    """
    # Start with current deployment account only
    # Future: Query DynamoDB or SSM for cross-account configuration
    accounts = [
        {
            'accountId': current_account,
            'accountName': 'Current Deployment Account',
            'regions': [REGION],  # Scan only current region for now
            'roleArn': None  # No AssumeRole needed for current account
        }
    ]
    
    # Future enhancement: Read from DynamoDB config table
    # table = dynamodb.Table(os.environ.get('SYNC_CONFIG_TABLE'))
    # response = table.scan()
    # accounts.extend(response['Items'])
    
    return accounts


def sync_account_certificates(account_id: str, regions: List[str], account_config: Dict) -> Dict:
    """
    Sync ACM certificates from a specific AWS account
    
    Args:
        account_id: AWS account ID
        regions: List of regions to scan
        account_config: Account configuration including roleArn
        
    Returns:
        dict: Statistics for this account (found, added, updated, skipped)
    """
    stats = {'found': 0, 'added': 0, 'updated': 0, 'skipped': 0}
    
    for region in regions:
        print(f"\n  Region: {region}")
        
        try:
            # Get ACM client (with AssumeRole for cross-account, direct for current)
            acm = get_acm_client(account_id, region, account_config.get('roleArn'))
            
            # List all ACM certificates in this region
            acm_certificates = list_acm_certificates(acm, region)
            stats['found'] += len(acm_certificates)
            
            print(f"  Found {len(acm_certificates)} ACM certificates in {region}")
            
            # Process each certificate
            for acm_cert in acm_certificates:
                try:
                    result = process_certificate(acm_cert, account_id, region)
                    
                    if result == 'added':
                        stats['added'] += 1
                    elif result == 'updated':
                        stats['updated'] += 1
                    else:
                        stats['skipped'] += 1
                        
                except Exception as cert_error:
                    print(f"  ERROR processing certificate {acm_cert.get('DomainName', 'Unknown')}: {str(cert_error)}")
                    stats['skipped'] += 1
                    
        except Exception as region_error:
            print(f"  ERROR scanning region {region}: {str(region_error)}")
    
    return stats


def get_acm_client(account_id: str, region: str, role_arn: Optional[str]):
    """
    Get ACM client (with AssumeRole for cross-account access)
    
    Args:
        account_id: Target AWS account ID
        region: AWS region
        role_arn: IAM role ARN to assume (None for current account)
        
    Returns:
        boto3 ACM client
    """
    if role_arn:
        # Cross-account: AssumeRole
        print(f"  Assuming role: {role_arn}")
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f'ACMSync-{account_id}-{region}'
        )
        
        credentials = assumed_role['Credentials']
        return boto3.client(
            'acm',
            region_name=region,
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
    else:
        # Current account: Direct access
        return boto3.client('acm', region_name=region)


def list_acm_certificates(acm_client, region: str) -> List[Dict]:
    """
    List all ACM certificates from ACM in a region
    
    Args:
        acm_client: boto3 ACM client
        region: AWS region
        
    Returns:
        List of certificate dictionaries with full details
    """
    certificates = []
    
    try:
        # List all certificates (paginated)
        paginator = acm_client.get_paginator('list_certificates')
        page_iterator = paginator.paginate(
            CertificateStatuses=['ISSUED', 'PENDING_VALIDATION', 'INACTIVE', 'EXPIRED']
        )
        
        for page in page_iterator:
            for cert_summary in page.get('CertificateSummaryList', []):
                cert_arn = cert_summary['CertificateArn']
                
                try:
                    # Get detailed certificate information
                    cert_details = acm_client.describe_certificate(CertificateArn=cert_arn)
                    certificate = cert_details['Certificate']
                    
                    # Extract relevant fields
                    cert_data = {
                        'ARN': certificate['CertificateArn'],
                        'DomainName': certificate['DomainName'],
                        'SubjectAlternativeNames': certificate.get('SubjectAlternativeNames', []),
                        'Status': certificate['Status'],
                        'Type': certificate.get('Type', 'UNKNOWN'),
                        'CreatedAt': certificate.get('CreatedAt'),
                        'IssuedAt': certificate.get('IssuedAt'),
                        'NotBefore': certificate.get('NotBefore'),
                        'NotAfter': certificate.get('NotAfter'),
                        'KeyAlgorithm': certificate.get('KeyAlgorithm', 'UNKNOWN'),
                        'InUseBy': certificate.get('InUseBy', [])
                    }
                    
                    certificates.append(cert_data)
                    
                except Exception as detail_error:
                    print(f"  Warning: Could not get details for {cert_arn}: {str(detail_error)}")
                    
    except Exception as list_error:
        print(f"  ERROR listing certificates in {region}: {str(list_error)}")
    
    return certificates


def process_certificate(acm_cert: Dict, account_id: str, region: str) -> str:
    """
    Process a single ACM certificate - add or update in DynamoDB
    
    Args:
        acm_cert: ACM certificate data
        account_id: AWS account ID
        region: AWS region
        
    Returns:
        str: 'added', 'updated', or 'skipped'
    """
    domain_name = acm_cert['DomainName']
    
    # Check if certificate already exists in DynamoDB
    existing_cert = find_existing_certificate(domain_name, account_id)
    
    if existing_cert:
        # Certificate exists - update ACM fields only
        return update_existing_certificate(existing_cert, acm_cert, account_id, region)
    else:
        # New certificate - add to DynamoDB
        return add_new_certificate(acm_cert, account_id, region)


def find_existing_certificate(domain_name: str, account_id: str) -> Optional[Dict]:
    """
    Find existing certificate in DynamoDB by AccountNumber + CommonName
    
    Uses GSI: AccountNumber-DomainName-index (to be created)
    Fallback: Scan with filter if GSI not available yet
    
    Args:
        domain_name: Certificate domain name (CommonName)
        account_id: AWS account ID
        
    Returns:
        Existing certificate dict or None
    """
    table = dynamodb.Table(CERTIFICATES_TABLE)
    
    try:
        # Try using GSI (will fail if not created yet)
        response = table.query(
            IndexName='AccountNumber-DomainName-index',
            KeyConditionExpression='AccountNumber = :account AND CommonName = :domain',
            ExpressionAttributeValues={
                ':account': account_id,
                ':domain': domain_name
            },
            Limit=1
        )
        
        if response['Items']:
            print(f"    Found existing cert: {domain_name} (Account: {account_id})")
            return response['Items'][0]
            
    except Exception as gsi_error:
        # GSI doesn't exist yet - fall back to scan
        print(f"    GSI not available, using scan (slower): {str(gsi_error)}")
        
        try:
            response = table.scan(
                FilterExpression='AccountNumber = :account AND CommonName = :domain',
                ExpressionAttributeValues={
                    ':account': account_id,
                    ':domain': domain_name
                },
                Limit=1
            )
            
            if response['Items']:
                print(f"    Found existing cert via scan: {domain_name} (Account: {account_id})")
                return response['Items'][0]
                
        except Exception as scan_error:
            print(f"    ERROR scanning for existing cert: {str(scan_error)}")
    
    return None


def update_existing_certificate(existing_cert: Dict, acm_cert: Dict, account_id: str, region: str) -> str:
    """
    Update existing certificate with ACM data
    Preserves manual fields (OwnerEmail, SupportEmail, etc.)
    
    Args:
        existing_cert: Existing certificate from DynamoDB
        acm_cert: ACM certificate data
        account_id: AWS account ID
        region: AWS region
        
    Returns:
        str: 'updated' or 'skipped'
    """
    table = dynamodb.Table(CERTIFICATES_TABLE)
    cert_id = existing_cert['CertificateID']
    
    # Determine if update is needed
    needs_update = False
    update_expression_parts = []
    expression_values = {}
    
    # Update ACM-specific fields only
    acm_fields = {
        'ACM_ARN': acm_cert['ARN'],
        'ACM_Status': acm_cert['Status'],
        'ExpiryDate': acm_cert['NotAfter'].strftime('%Y-%m-%d') if acm_cert.get('NotAfter') else None,
        'Region': region,
        'LastSyncedFromACM': datetime.now(timezone.utc).isoformat(),
        'ACM_Type': acm_cert.get('Type', 'UNKNOWN'),
        'ACM_KeyAlgorithm': acm_cert.get('KeyAlgorithm', 'UNKNOWN')
    }
    
    # Check if Source field exists, if not set to 'ACM'
    if 'Source' not in existing_cert:
        acm_fields['Source'] = 'ACM'
    
    # Build update expression
    for field, value in acm_fields.items():
        if value is not None and existing_cert.get(field) != value:
            needs_update = True
            update_expression_parts.append(f"{field} = :{field.replace('_', '')}")
            expression_values[f":{field.replace('_', '')}"] = value
    
    if needs_update:
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        try:
            table.update_item(
                Key={'CertificateID': cert_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            print(f"    ✓ Updated: {acm_cert['DomainName']} (ID: {cert_id})")
            return 'updated'
            
        except Exception as update_error:
            print(f"    ERROR updating certificate {cert_id}: {str(update_error)}")
            return 'skipped'
    else:
        print(f"    ⊘ No changes needed: {acm_cert['DomainName']}")
        return 'skipped'


def add_new_certificate(acm_cert: Dict, account_id: str, region: str) -> str:
    """
    Add new certificate from ACM to DynamoDB
    
    Args:
        acm_cert: ACM certificate data
        account_id: AWS account ID
        region: AWS region
        
    Returns:
        str: 'added' or 'skipped'
    """
    table = dynamodb.Table(CERTIFICATES_TABLE)
    
    # Generate unique Certificate ID
    cert_id = f"acm-{account_id}-{region}-{acm_cert['DomainName'][:50]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # Calculate days until expiry
    days_until_expiry = None
    status = 'Unknown'
    
    if acm_cert.get('NotAfter'):
        expiry_date = acm_cert['NotAfter']
        days_until_expiry = (expiry_date.date() - datetime.now(timezone.utc).date()).days
        
        # Determine status based on expiry
        if days_until_expiry < 0:
            status = 'Expired'
        elif days_until_expiry <= 30:
            status = 'Due for Renewal'
        else:
            status = 'Active'
    
    # Build certificate item
    new_cert = {
        'CertificateID': cert_id,
        'CommonName': acm_cert['DomainName'],
        'CertificateName': acm_cert['DomainName'],  # Backward compatibility
        'AccountNumber': account_id,
        'Region': region,
        'Environment': 'Unknown',  # To be updated manually
        'Application': 'Unknown',  # To be updated manually
        'Status': status,
        'Source': 'ACM',
        'ACM_ARN': acm_cert['ARN'],
        'ACM_Status': acm_cert['Status'],
        'ACM_Type': acm_cert.get('Type', 'UNKNOWN'),
        'ACM_KeyAlgorithm': acm_cert.get('KeyAlgorithm', 'UNKNOWN'),
        'Type': acm_cert.get('Type', 'UNKNOWN'),
        'ExpiryDate': acm_cert['NotAfter'].strftime('%Y-%m-%d') if acm_cert.get('NotAfter') else None,
        'DaysUntilExpiry': str(days_until_expiry) if days_until_expiry is not None else '0',
        'CreatedOn': datetime.now(timezone.utc).isoformat(),
        'LastUpdatedOn': datetime.now(timezone.utc).isoformat(),
        'LastSyncedFromACM': datetime.now(timezone.utc).isoformat(),
        'ImportedFrom': 'ACM-Sync',
        'Version': 1
    }
    
    try:
        table.put_item(Item=new_cert)
        print(f"    ✓ Added new certificate: {acm_cert['DomainName']} (Account: {account_id}, Region: {region})")
        return 'added'
        
    except Exception as add_error:
        print(f"    ERROR adding certificate {acm_cert['DomainName']}: {str(add_error)}")
        return 'skipped'


# Helper function for manual testing
if __name__ == '__main__':
    # Test locally
    test_event = {
        'httpMethod': 'POST',
        'body': json.dumps({})
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
