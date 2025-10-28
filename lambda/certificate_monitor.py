import json
import boto3
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

# Environment variables
CERTIFICATES_TABLE = os.environ['CERTIFICATES_TABLE']
LOGS_TABLE = os.environ['LOGS_TABLE']
SENDER_EMAIL = os.environ['SENDER_EMAIL']
EXPIRY_THRESHOLD = int(os.environ['EXPIRY_THRESHOLD'])
REGION = os.environ['REGION']

def lambda_handler(event, context):
    """
    Monitor certificates for expiry and send notifications
    """
    logger.info("Certificate monitor started")
    
    try:
        # Scan certificates table for expiring certificates
        expiring_certificates = scan_expiring_certificates()
        
        # Process notifications
        notification_results = process_notifications(expiring_certificates)
        
        # Update certificate statuses
        status_update_results = update_certificate_statuses(expiring_certificates)
        
        # Create summary report
        summary = create_summary_report(expiring_certificates, notification_results, status_update_results)
        
        logger.info(f"Certificate monitoring completed. Summary: {summary}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Certificate monitoring completed successfully',
                'summary': summary,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in certificate monitoring: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def scan_expiring_certificates():
    """
    Scan DynamoDB for certificates that are expiring within the threshold
    """
    certificates_table = dynamodb.Table(CERTIFICATES_TABLE)
    
    # Calculate threshold date
    threshold_date = (datetime.utcnow() + timedelta(days=EXPIRY_THRESHOLD)).strftime('%Y-%m-%d')
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    logger.info(f"Scanning for certificates expiring between {current_date} and {threshold_date}")
    
    expiring_certificates = []
    
    try:
        # Scan all certificates (for now - can be optimized with GSI)
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
    
    logger.info(f"Found {len(expiring_certificates)} expiring certificates")
    return expiring_certificates

def is_certificate_expiring(expiry_date, current_date, threshold_date):
    """
    Check if certificate is expiring within the threshold period
    """
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        current = datetime.strptime(current_date, '%Y-%m-%d')
        threshold = datetime.strptime(threshold_date, '%Y-%m-%d')
        
        # Certificate is expiring if:
        # 1. It expires within the threshold period
        # 2. It's not already expired (we handle expired separately)
        return current <= expiry <= threshold
        
    except ValueError as e:
        logger.warning(f"Invalid date format for certificate expiry: {expiry_date}")
        return False

def process_notifications(expiring_certificates):
    """
    Send email notifications for expiring certificates
    """
    notification_results = {
        'sent': 0,
        'failed': 0,
        'errors': []
    }
    
    # Group certificates by owner for batched notifications
    certificates_by_owner = group_certificates_by_owner(expiring_certificates)
    
    for owner_email, certificates in certificates_by_owner.items():
        try:
            if owner_email and '@' in owner_email:
                send_expiry_notification(owner_email, certificates)
                notification_results['sent'] += 1
                logger.info(f"Notification sent to {owner_email} for {len(certificates)} certificates")
            else:
                logger.warning(f"Invalid or missing owner email for certificates: {[cert.get('CertificateName') for cert in certificates]}")
                
        except Exception as e:
            error_msg = f"Failed to send notification to {owner_email}: {str(e)}"
            logger.error(error_msg)
            notification_results['failed'] += 1
            notification_results['errors'].append(error_msg)
    
    return notification_results

def group_certificates_by_owner(certificates):
    """
    Group certificates by owner email for batched notifications
    """
    certificates_by_owner = {}
    
    for cert in certificates:
        owner_email = cert.get('OwnerEmail', '').strip()
        support_email = cert.get('SupportEmail', '').strip()
        
        # Primary notification to owner
        if owner_email:
            if owner_email not in certificates_by_owner:
                certificates_by_owner[owner_email] = []
            certificates_by_owner[owner_email].append(cert)
        
        # Secondary notification to support team if different
        if support_email and support_email != owner_email:
            if support_email not in certificates_by_owner:
                certificates_by_owner[support_email] = []
            certificates_by_owner[support_email].append(cert)
    
    return certificates_by_owner

def send_expiry_notification(recipient_email, certificates):
    """
    Send email notification about expiring certificates
    """
    # Create email content
    subject = f"Certificate Expiry Alert - {len(certificates)} Certificate(s) Expiring Soon"
    
    # Generate email body
    body_text = generate_email_body_text(certificates)
    body_html = generate_email_body_html(certificates)
    
    # Send email via SES
    response = ses.send_email(
        Source=SENDER_EMAIL,
        Destination={'ToAddresses': [recipient_email]},
        Message={
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': {
                'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                'Html': {'Data': body_html, 'Charset': 'UTF-8'}
            }
        }
    )
    
    # Log the notification
    for cert in certificates:
        log_notification(cert['CertificateID'], recipient_email, 'EMAIL_NOTIFICATION_SENT')
    
    return response

def generate_email_body_text(certificates):
    """
    Generate plain text email body
    """
    body = f"""
Certificate Expiry Alert

This is an automated notification that {len(certificates)} certificate(s) are expiring within the next {EXPIRY_THRESHOLD} days.

Please take immediate action to renew the following certificates:

"""
    
    for cert in certificates:
        expiry_date = cert.get('ExpiryDate', 'Unknown')
        days_until_expiry = calculate_days_until_expiry(expiry_date)
        
        body += f"""
Certificate: {cert.get('CertificateName', 'Unknown')}
Environment: {cert.get('Environment', 'Unknown')}
Application: {cert.get('Application', 'Unknown')}
Expiry Date: {expiry_date}
Days Until Expiry: {days_until_expiry}
Status: {cert.get('Status', 'Unknown')}
---
"""
    
    body += f"""

Next Steps:
1. Create a ServiceNow ticket for certificate renewal
2. Update the certificate status to "Renewal in Progress" in the dashboard
3. Coordinate with the certificate authority for renewal
4. Upload the new certificate once renewed

Dashboard: Access the certificate management dashboard for more details

This is an automated message from the Certificate Management System.
"""
    
    return body

def generate_email_body_html(certificates):
    """
    Generate HTML email body
    """
    html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f44336; color: white; padding: 15px; border-radius: 5px; }}
        .certificate {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 4px solid #ff9800; }}
        .urgent {{ border-left-color: #f44336; }}
        .warning {{ border-left-color: #ff9800; }}
        .footer {{ background-color: #e0e0e0; padding: 10px; margin-top: 20px; border-radius: 5px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🚨 Certificate Expiry Alert</h2>
        <p>This is an automated notification that {len(certificates)} certificate(s) are expiring within the next {EXPIRY_THRESHOLD} days.</p>
    </div>
    
    <h3>Certificates Requiring Immediate Attention:</h3>
    
    <table>
        <tr>
            <th>Certificate Name</th>
            <th>Environment</th>
            <th>Application</th>
            <th>Expiry Date</th>
            <th>Days Until Expiry</th>
            <th>Owner</th>
            <th>Status</th>
        </tr>
"""
    
    for cert in certificates:
        expiry_date = cert.get('ExpiryDate', 'Unknown')
        days_until_expiry = calculate_days_until_expiry(expiry_date)
        
        # Determine urgency class
        urgency_class = "urgent" if days_until_expiry < 7 else "warning"
        
        html += f"""
        <tr class="{urgency_class}">
            <td>{cert.get('CertificateName', 'Unknown')}</td>
            <td>{cert.get('Environment', 'Unknown')}</td>
            <td>{cert.get('Application', 'Unknown')}</td>
            <td>{expiry_date}</td>
            <td>{days_until_expiry}</td>
            <td>{cert.get('OwnerEmail', 'Unknown')}</td>
            <td>{cert.get('Status', 'Unknown')}</td>
        </tr>
"""
    
    html += """
    </table>
    
    <div class="footer">
        <h4>Next Steps:</h4>
        <ol>
            <li>Create a ServiceNow ticket for certificate renewal</li>
            <li>Update the certificate status to "Renewal in Progress" in the dashboard</li>
            <li>Coordinate with the certificate authority for renewal</li>
            <li>Upload the new certificate once renewed</li>
        </ol>
        
        <p><strong>Important:</strong> This is an automated message from the Certificate Management System.</p>
    </div>
</body>
</html>
"""
    
    return html

def calculate_days_until_expiry(expiry_date):
    """
    Calculate days until certificate expiry
    """
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        current = datetime.utcnow()
        return (expiry - current).days
    except ValueError:
        return "Unknown"

def update_certificate_statuses(expiring_certificates):
    """
    Update certificate statuses based on expiry dates
    """
    certificates_table = dynamodb.Table(CERTIFICATES_TABLE)
    
    update_results = {
        'updated': 0,
        'failed': 0,
        'errors': []
    }
    
    for cert in expiring_certificates:
        try:
            cert_id = cert['CertificateID']
            expiry_date = cert.get('ExpiryDate')
            current_status = cert.get('Status', '')
            
            # Calculate new status
            new_status = calculate_new_status(expiry_date, current_status)
            
            if new_status != current_status:
                # Update certificate status
                certificates_table.update_item(
                    Key={'CertificateID': cert_id},
                    UpdateExpression='SET #status = :status, LastUpdatedOn = :timestamp',
                    ExpressionAttributeNames={'#status': 'Status'},
                    ExpressionAttributeValues={
                        ':status': new_status,
                        ':timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                # Log the status change
                log_notification(cert_id, 'system', f'STATUS_CHANGED_FROM_{current_status}_TO_{new_status}')
                
                update_results['updated'] += 1
                logger.info(f"Updated certificate {cert.get('CertificateName')} status from {current_status} to {new_status}")
            
        except Exception as e:
            error_msg = f"Failed to update status for certificate {cert.get('CertificateID')}: {str(e)}"
            logger.error(error_msg)
            update_results['failed'] += 1
            update_results['errors'].append(error_msg)
    
    return update_results

def calculate_new_status(expiry_date, current_status):
    """
    Calculate new certificate status based on expiry date
    """
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        current = datetime.utcnow()
        days_until_expiry = (expiry - current).days
        
        if days_until_expiry < 0:
            return "Expired"
        elif days_until_expiry <= EXPIRY_THRESHOLD and current_status not in ["Renewal in Progress", "Renewal Done"]:
            return "Due for Renewal"
        elif current_status in ["Renewal in Progress", "Renewal Done"]:
            return current_status  # Don't change manual statuses
        else:
            return "Active"
            
    except ValueError:
        return current_status  # Keep current status if date parsing fails

def log_notification(cert_id, recipient, action):
    """
    Log notification or status change to the logs table
    """
    logs_table = dynamodb.Table(LOGS_TABLE)
    
    log_entry = {
        'LogID': str(uuid.uuid4()),
        'CertificateID': cert_id,
        'Timestamp': datetime.utcnow().isoformat(),
        'Action': action,
        'Details': {
            'recipient': recipient,
            'expiry_threshold': EXPIRY_THRESHOLD,
            'monitoring_source': 'automated_monitor'
        },
        'Metadata': {
            'source': 'CertificateMonitor',
            'version': '1.0'
        }
    }
    
    try:
        logs_table.put_item(Item=log_entry)
    except Exception as e:
        logger.error(f"Failed to log notification: {str(e)}")

def create_summary_report(expiring_certificates, notification_results, status_update_results):
    """
    Create a summary report of the monitoring run
    """
    return {
        'monitoring_timestamp': datetime.utcnow().isoformat(),
        'expiry_threshold_days': EXPIRY_THRESHOLD,
        'certificates_found': len(expiring_certificates),
        'notifications': notification_results,
        'status_updates': status_update_results,
        'certificate_breakdown': {
            'by_environment': count_by_field(expiring_certificates, 'Environment'),
            'by_status': count_by_field(expiring_certificates, 'Status'),
            'by_urgency': categorize_by_urgency(expiring_certificates)
        }
    }

def count_by_field(certificates, field):
    """
    Count certificates by a specific field
    """
    counts = {}
    for cert in certificates:
        value = cert.get(field, 'Unknown')
        counts[value] = counts.get(value, 0) + 1
    return counts

def categorize_by_urgency(certificates):
    """
    Categorize certificates by urgency (days until expiry)
    """
    urgent = 0  # < 7 days
    warning = 0  # 7-30 days
    
    for cert in certificates:
        days_until_expiry = calculate_days_until_expiry(cert.get('ExpiryDate', ''))
        if isinstance(days_until_expiry, int):
            if days_until_expiry < 7:
                urgent += 1
            else:
                warning += 1
    
    return {
        'urgent_less_than_7_days': urgent,
        'warning_7_to_30_days': warning
    }