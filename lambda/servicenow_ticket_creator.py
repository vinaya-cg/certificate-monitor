"""
ServiceNow Ticket Creator for Certificate Expiry Management
=============================================================

This Lambda function creates ServiceNow incidents for expiring certificates.
It runs independently from the main certificate monitoring system to avoid
disruption to existing functionality.

Features:
- Automatic ticket creation for expiring certificates
- Duplicate detection (checks existing IncidentNumber in DynamoDB)
- Priority calculation based on days until expiry
- OAuth2 authentication with ServiceNow
- Comprehensive logging and error handling
- Updates DynamoDB with incident number after creation

Author: Certificate Management Team
Version: 1.0.0
"""

import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import urllib3
from urllib.parse import urlencode
import base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')

# Initialize HTTP client
http = urllib3.PoolManager()

# Environment variables
CERTIFICATES_TABLE = os.environ['CERTIFICATES_TABLE']
LOGS_TABLE = os.environ['LOGS_TABLE']
SNOW_SECRET_NAME = os.environ['SNOW_SECRET_NAME']
EXPIRY_THRESHOLD_DAYS = int(os.environ.get('EXPIRY_THRESHOLD_DAYS', '30'))
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true'

# Cache for ServiceNow credentials
_snow_credentials = None


def lambda_handler(event, context):
    """
    Main Lambda handler for ServiceNow ticket creation
    
    Args:
        event: Lambda event (EventBridge scheduled event)
        context: Lambda context
        
    Returns:
        dict: Status and summary of ticket creation
    """
    logger.info("ServiceNow Ticket Creator started")
    logger.info(f"DRY_RUN mode: {DRY_RUN}")
    
    try:
        # Get expiring certificates from DynamoDB
        expiring_certificates = scan_expiring_certificates()
        logger.info(f"Found {len(expiring_certificates)} expiring certificates")
        
        # Filter certificates that need tickets
        certs_needing_tickets = filter_certificates_needing_tickets(expiring_certificates)
        logger.info(f"Filtered to {len(certs_needing_tickets)} certificates needing tickets")
        
        # Create ServiceNow tickets
        results = process_ticket_creation(certs_needing_tickets)
        
        # Create summary
        summary = create_summary(expiring_certificates, certs_needing_tickets, results)
        logger.info(f"Ticket creation completed. Summary: {json.dumps(summary)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'ServiceNow ticket creation completed',
                'summary': summary,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in ServiceNow ticket creation: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }


def scan_expiring_certificates():
    """
    Scan DynamoDB for certificates expiring within the threshold
    
    Returns:
        list: Certificates expiring within threshold period
    """
    certificates_table = dynamodb.Table(CERTIFICATES_TABLE)
    
    # Calculate threshold date
    threshold_date = (datetime.utcnow() + timedelta(days=EXPIRY_THRESHOLD_DAYS)).strftime('%Y-%m-%d')
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    logger.info(f"Scanning for certificates expiring between {current_date} and {threshold_date}")
    
    expiring_certificates = []
    
    try:
        # Scan all certificates
        response = certificates_table.scan()
        
        for item in response['Items']:
            expiry_date = item.get('ExpiryDate')
            if expiry_date and is_certificate_expiring(expiry_date, current_date, threshold_date):
                expiring_certificates.append(item)
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = certificates_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            for item in response['Items']:
                expiry_date = item.get('ExpiryDate')
                if expiry_date and is_certificate_expiring(expiry_date, current_date, threshold_date):
                    expiring_certificates.append(item)
    
    except Exception as e:
        logger.error(f"Error scanning certificates: {str(e)}")
        raise
    
    return expiring_certificates


def is_certificate_expiring(expiry_date, current_date, threshold_date):
    """
    Check if certificate is expiring within the threshold period
    
    Args:
        expiry_date: Certificate expiry date (YYYY-MM-DD)
        current_date: Current date (YYYY-MM-DD)
        threshold_date: Threshold date (YYYY-MM-DD)
        
    Returns:
        bool: True if certificate is expiring within threshold
    """
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        current = datetime.strptime(current_date, '%Y-%m-%d')
        threshold = datetime.strptime(threshold_date, '%Y-%m-%d')
        
        # Certificate is expiring if it expires within the threshold period
        # and is not already expired
        return current <= expiry <= threshold
        
    except ValueError as e:
        logger.warning(f"Invalid date format: {expiry_date}")
        return False


def filter_certificates_needing_tickets(certificates):
    """
    Filter certificates that need ServiceNow tickets
    
    Criteria:
    - No existing IncidentNumber OR IncidentNumber is empty
    - Status is 'Due for Renewal' or 'Expired' or 'Active'
    - Not in 'Renewal Done' status
    
    Args:
        certificates: List of expiring certificates
        
    Returns:
        list: Filtered certificates needing tickets
    """
    needing_tickets = []
    
    for cert in certificates:
        # Skip if ticket already exists
        incident_number = cert.get('IncidentNumber', '').strip()
        if incident_number:
            logger.info(f"Certificate {cert.get('CertificateName')} already has ticket: {incident_number}")
            continue
        
        # Skip if renewal is already done
        status = cert.get('Status', '')
        if status in ['Renewal Done', 'Renewed']:
            logger.info(f"Certificate {cert.get('CertificateName')} renewal already done, skipping ticket")
            continue
        
        # Certificate needs a ticket
        needing_tickets.append(cert)
    
    return needing_tickets


def process_ticket_creation(certificates):
    """
    Create ServiceNow tickets for certificates
    
    Args:
        certificates: List of certificates needing tickets
        
    Returns:
        dict: Results summary with success/failure counts
    """
    results = {
        'created': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    if not certificates:
        logger.info("No certificates need tickets")
        return results
    
    # Get ServiceNow credentials
    try:
        snow_creds = get_servicenow_credentials()
    except Exception as e:
        logger.error(f"Failed to retrieve ServiceNow credentials: {str(e)}")
        results['failed'] = len(certificates)
        results['errors'].append(f"Credential retrieval failed: {str(e)}")
        return results
    
    # Process each certificate
    for cert in certificates:
        try:
            cert_id = cert.get('CertificateID')
            cert_name = cert.get('CertificateName', 'Unknown')
            
            logger.info(f"Processing certificate: {cert_name} (ID: {cert_id})")
            
            if DRY_RUN:
                logger.info(f"DRY_RUN: Would create ticket for {cert_name}")
                results['skipped'] += 1
                continue
            
            # Create ServiceNow ticket
            incident_number = create_servicenow_ticket(cert, snow_creds)
            
            # Update DynamoDB with incident number
            update_certificate_incident_number(cert_id, incident_number)
            
            # Log the ticket creation
            log_ticket_creation(cert_id, incident_number, cert)
            
            results['created'] += 1
            logger.info(f"Successfully created ticket {incident_number} for {cert_name}")
            
        except Exception as e:
            error_msg = f"Failed to create ticket for {cert.get('CertificateName')}: {str(e)}"
            logger.error(error_msg)
            results['failed'] += 1
            results['errors'].append(error_msg)
    
    return results


def get_servicenow_credentials():
    """
    Retrieve ServiceNow credentials from Secrets Manager
    
    Returns:
        dict: ServiceNow credentials
    """
    global _snow_credentials
    
    # Return cached credentials if available
    if _snow_credentials:
        return _snow_credentials
    
    try:
        response = secrets_manager.get_secret_value(SecretId=SNOW_SECRET_NAME)
        secret_string = response['SecretString']
        _snow_credentials = json.loads(secret_string)
        
        logger.info(f"Retrieved ServiceNow credentials for instance: {_snow_credentials.get('instance')}")
        return _snow_credentials
        
    except ClientError as e:
        logger.error(f"Error retrieving secret: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing secret JSON: {str(e)}")
        raise


def get_servicenow_token(snow_creds):
    """
    Get OAuth2 access token from ServiceNow
    
    Args:
        snow_creds: ServiceNow credentials dictionary
        
    Returns:
        str: OAuth2 access token
    """
    instance = snow_creds['instance']
    token_url = f"https://{instance}.service-now.com/oauth_token.do"
    
    # Create Basic Auth header
    credentials = f"{snow_creds['client_id']}:{snow_creds['client_secret']}"
    auth_header = 'Basic ' + base64.b64encode(credentials.encode()).decode()
    
    token_data = {
        'grant_type': 'password',
        'username': snow_creds['username'],
        'password': snow_creds['password'],
        'scope': 'useraccount'
    }
    
    logger.info(f"Requesting OAuth token from {instance}")
    
    try:
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            token_url,
            headers={'Authorization': auth_header, 'Content-Type': 'application/x-www-form-urlencoded'},
            body=urlencode(token_data),
            timeout=30
        )
        
        if response.status != 200:
            raise Exception(f"HTTP {response.status}: {response.data.decode('utf-8')}")
        
        response_data = json.loads(response.data.decode('utf-8'))
        token = response_data.get('access_token')
        if not token:
            raise Exception("No access_token in response")
        
        logger.info("Successfully obtained OAuth token")
        return token
        
    except Exception as e:
        logger.error(f"Failed to get OAuth token: {str(e)}")
        raise


def create_servicenow_ticket(certificate, snow_creds):
    """
    Create ServiceNow incident for certificate expiry
    
    Args:
        certificate: Certificate dictionary from DynamoDB
        snow_creds: ServiceNow credentials
        
    Returns:
        str: Incident number (e.g., INC0012345)
    """
    # Get OAuth token
    access_token = get_servicenow_token(snow_creds)
    
    # Calculate priority based on days until expiry
    days_until_expiry = calculate_days_until_expiry(certificate.get('ExpiryDate'))
    priority = calculate_priority(days_until_expiry)
    
    # Build ticket description
    description = format_ticket_description(certificate, days_until_expiry)
    short_description = format_short_description(certificate)
    
    # Prepare incident data
    instance = snow_creds['instance']
    api_url = f"https://{instance}.service-now.com/api/x_lsmcb_sca/sc"
    
    incident_data = {
        'interface': 'incident',
        'sender': 'certificate_monitoring',
        'short_description': short_description,
        'description': description,
        'caller': snow_creds.get('caller', snow_creds['username']),
        'correlation_id': certificate.get('CertificateID'),
        'business_service': snow_creds.get('business_service', 'PostNL Generic SecOps AWS'),
        'service_offering': snow_creds.get('service_offering', 'PostNL Generic SecOps AWS'),
        'company': snow_creds.get('company', 'PostNL B.V.'),
        'priority': priority
    }
    
    # Add custom fields if supported
    incident_data.update({
        'u_certificate_id': certificate.get('CertificateID'),
        'u_expiry_date': certificate.get('ExpiryDate'),
        'u_environment': certificate.get('Environment'),
        'u_application': certificate.get('Application', 'Unknown'),
        'u_days_until_expiry': str(days_until_expiry)
    })
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    logger.info(f"Creating ServiceNow ticket for certificate: {certificate.get('CertificateName')}")
    
    try:
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            api_url,
            body=json.dumps(incident_data).encode('utf-8'),
            headers=headers,
            timeout=30
        )
        
        if response.status == 201:
            incident_response = json.loads(response.data.decode('utf-8'))
            incident_number = incident_response.get('result', {}).get('number')
            
            if not incident_number:
                raise Exception("No incident number in response")
            
            logger.info(f"Successfully created incident: {incident_number}")
            return incident_number
        else:
            error_msg = f"ServiceNow API returned status {response.status}: {response.data.decode('utf-8')}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        logger.error(f"Error creating ServiceNow ticket: {str(e)}")
        raise


def calculate_days_until_expiry(expiry_date):
    """
    Calculate days until certificate expiry
    
    Args:
        expiry_date: Certificate expiry date (YYYY-MM-DD)
        
    Returns:
        int: Days until expiry (negative if expired)
    """
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        current = datetime.utcnow()
        return (expiry - current).days
    except (ValueError, TypeError):
        return 0


def calculate_priority(days_until_expiry):
    """
    Calculate ServiceNow ticket priority based on days until expiry
    
    Priority mapping:
    - < 7 days: Priority 2 (High)
    - 7-14 days: Priority 3 (Medium)
    - 15-30 days: Priority 4 (Low)
    - > 30 days: Priority 5 (Planning)
    - Expired: Priority 1 (Critical)
    
    Args:
        days_until_expiry: Days until certificate expires
        
    Returns:
        str: ServiceNow priority level (1-5)
    """
    if days_until_expiry < 0:
        return '1'  # Critical - Already expired
    elif days_until_expiry < 7:
        return '2'  # High - Less than 1 week
    elif days_until_expiry < 14:
        return '3'  # Medium - 1-2 weeks
    elif days_until_expiry < 30:
        return '4'  # Low - 2-4 weeks
    else:
        return '5'  # Planning - More than 30 days


def format_short_description(certificate):
    """
    Format short description for ServiceNow ticket
    
    Args:
        certificate: Certificate dictionary
        
    Returns:
        str: Short description
    """
    cert_name = certificate.get('CertificateName', 'Unknown')
    environment = certificate.get('Environment', 'Unknown')
    
    return f"Certificate Expiring: {cert_name} ({environment})"


def format_ticket_description(certificate, days_until_expiry):
    """
    Format detailed description for ServiceNow ticket
    
    Args:
        certificate: Certificate dictionary
        days_until_expiry: Days until expiry
        
    Returns:
        str: Formatted ticket description
    """
    urgency = get_urgency_label(days_until_expiry)
    
    description = f"""CERTIFICATE EXPIRY ALERT

A certificate is approaching its expiration date and requires renewal action.

Certificate Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Certificate Name: {certificate.get('CertificateName', 'Unknown')}
• Environment: {certificate.get('Environment', 'Unknown')}
• Application: {certificate.get('Application', 'Unknown')}
• Current Status: {certificate.get('Status', 'Unknown')}

Expiry Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Expiry Date: {certificate.get('ExpiryDate', 'Unknown')}
• Days Until Expiry: {days_until_expiry} days
• Urgency: {urgency}

Certificate Owner:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Owner Email: {certificate.get('OwnerEmail', 'Not specified')}
• Support Email: {certificate.get('SupportEmail', 'Not specified')}

AWS Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Certificate ID: {certificate.get('CertificateID', 'Unknown')}
• Account Number: {certificate.get('AccountNumber', 'Not specified')}
• Domain Name: {certificate.get('DomainName', 'Not specified')}
• ACM ARN: {certificate.get('ACM_ARN', 'Not specified')}

Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Review certificate renewal requirements
2. Coordinate with certificate authority for renewal
3. Generate new Certificate Signing Request (CSR) if needed
4. Install renewed certificate in AWS ACM
5. Update certificate status to "Renewal Done" in the dashboard
6. Verify certificate is working correctly
7. Close this ticket once renewal is complete

Dashboard Access:
The Certificate Management Dashboard provides detailed information and
allows you to track the renewal progress.

Important Notes:
• This ticket was automatically created by the Certificate Monitoring System
• Please update the ticket with progress and any issues encountered
• Contact the Security team if you need assistance with renewal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Auto-generated by Certificate Management System
Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
    
    return description


def get_urgency_label(days_until_expiry):
    """
    Get urgency label based on days until expiry
    
    Args:
        days_until_expiry: Days until certificate expires
        
    Returns:
        str: Urgency label
    """
    if days_until_expiry < 0:
        return "CRITICAL - EXPIRED"
    elif days_until_expiry < 7:
        return "HIGH - Less than 1 week"
    elif days_until_expiry < 14:
        return "MEDIUM - 1-2 weeks"
    elif days_until_expiry < 30:
        return "LOW - 2-4 weeks"
    else:
        return "PLANNING - More than 30 days"


def update_certificate_incident_number(cert_id, incident_number):
    """
    Update DynamoDB with ServiceNow incident number
    
    Args:
        cert_id: Certificate ID
        incident_number: ServiceNow incident number
    """
    certificates_table = dynamodb.Table(CERTIFICATES_TABLE)
    
    try:
        certificates_table.update_item(
            Key={'CertificateID': cert_id},
            UpdateExpression='SET IncidentNumber = :incident, LastUpdatedOn = :timestamp',
            ExpressionAttributeValues={
                ':incident': incident_number,
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Updated certificate {cert_id} with incident number {incident_number}")
        
    except Exception as e:
        logger.error(f"Failed to update DynamoDB: {str(e)}")
        raise


def log_ticket_creation(cert_id, incident_number, certificate):
    """
    Log ticket creation to audit table
    
    Args:
        cert_id: Certificate ID
        incident_number: ServiceNow incident number
        certificate: Certificate dictionary
    """
    logs_table = dynamodb.Table(LOGS_TABLE)
    
    import uuid
    
    log_entry = {
        'LogID': str(uuid.uuid4()),
        'CertificateID': cert_id,
        'Timestamp': datetime.utcnow().isoformat(),
        'Action': 'SERVICENOW_TICKET_CREATED',
        'Details': {
            'incident_number': incident_number,
            'certificate_name': certificate.get('CertificateName'),
            'environment': certificate.get('Environment'),
            'expiry_date': certificate.get('ExpiryDate'),
            'days_until_expiry': calculate_days_until_expiry(certificate.get('ExpiryDate')),
            'priority': calculate_priority(calculate_days_until_expiry(certificate.get('ExpiryDate')))
        },
        'Metadata': {
            'source': 'ServiceNowTicketCreator',
            'version': '1.0',
            'dry_run': DRY_RUN
        }
    }
    
    try:
        logs_table.put_item(Item=log_entry)
        logger.info(f"Logged ticket creation for certificate {cert_id}")
    except Exception as e:
        logger.error(f"Failed to log ticket creation: {str(e)}")


def create_summary(all_certs, certs_needing_tickets, results):
    """
    Create summary report
    
    Args:
        all_certs: All expiring certificates
        certs_needing_tickets: Certificates that needed tickets
        results: Ticket creation results
        
    Returns:
        dict: Summary report
    """
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'expiry_threshold_days': EXPIRY_THRESHOLD_DAYS,
        'dry_run': DRY_RUN,
        'certificates': {
            'total_expiring': len(all_certs),
            'needing_tickets': len(certs_needing_tickets),
            'already_have_tickets': len(all_certs) - len(certs_needing_tickets)
        },
        'tickets': {
            'created': results['created'],
            'failed': results['failed'],
            'skipped': results['skipped']
        },
        'errors': results['errors']
    }
