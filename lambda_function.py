import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses', region_name='eu-west-1')
table_name = os.environ.get('CERTIFICATES_TABLE', 'cert-management-dev-certificates')
table = dynamodb.Table(table_name)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def send_status_change_notification(certificate, old_status, new_status, notes='', incident_number=''):
    """Send email notification when certificate status changes"""
    try:
        owner_email = certificate.get('Owner', '')
        support_email = certificate.get('SupportEmail', '')
        cert_name = certificate.get('CertificateName', 'Unknown')
        environment = certificate.get('Environment', 'Unknown')
        
        # Build email recipients
        recipients = []
        if owner_email and '@' in owner_email:
            recipients.append(owner_email)
        if support_email and '@' in support_email and support_email not in recipients:
            recipients.append(support_email)
        
        if not recipients:
            print(f"No valid email recipients for certificate {cert_name}")
            return
        
        # Build email subject
        subject = f"Certificate Status Changed: {cert_name} ({environment})"
        
        # Build email body
        body_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #667eea; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .info-table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                .info-table th {{ background-color: #f2f2f2; padding: 10px; text-align: left; border: 1px solid #ddd; }}
                .info-table td {{ padding: 10px; border: 1px solid #ddd; }}
                .status-change {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
                .footer {{ color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Certificate Status Change Notification</h2>
            </div>
            <div class="content">
                <p>The status of the following certificate has been updated:</p>
                
                <table class="info-table">
                    <tr>
                        <th>Certificate Name</th>
                        <td>{cert_name}</td>
                    </tr>
                    <tr>
                        <th>Environment</th>
                        <td>{environment}</td>
                    </tr>
                    <tr>
                        <th>Application</th>
                        <td>{certificate.get('ApplicationName', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>Expiry Date</th>
                        <td>{certificate.get('ExpiryDate', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>Days Until Expiry</th>
                        <td>{certificate.get('DaysUntilExpiry', 'N/A')}</td>
                    </tr>
                </table>
                
                <div class="status-change">
                    <h3>Status Change Details</h3>
                    <p><strong>Previous Status:</strong> {old_status or 'N/A'}</p>
                    <p><strong>New Status:</strong> <span style="color: #667eea; font-weight: bold;">{new_status}</span></p>
                    {f'<p><strong>Incident Number:</strong> {incident_number}</p>' if incident_number else ''}
                    {f'<p><strong>Notes:</strong> {notes}</p>' if notes else ''}
                    <p><strong>Changed At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                
                <p>Please take appropriate action if required.</p>
                
                <div class="footer">
                    <p>This is an automated notification from the Certificate Management System.</p>
                    <p>Dashboard: <a href="https://cert-management-dev-dashboard-a3px89bh.s3.eu-west-1.amazonaws.com/index.html">View Dashboard</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
Certificate Status Change Notification

The status of the following certificate has been updated:

Certificate Name: {cert_name}
Environment: {environment}
Application: {certificate.get('ApplicationName', 'N/A')}
Expiry Date: {certificate.get('ExpiryDate', 'N/A')}
Days Until Expiry: {certificate.get('DaysUntilExpiry', 'N/A')}

Status Change Details:
Previous Status: {old_status or 'N/A'}
New Status: {new_status}
{f'Incident Number: {incident_number}' if incident_number else ''}
{f'Notes: {notes}' if notes else ''}
Changed At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please take appropriate action if required.

This is an automated notification from the Certificate Management System.
        """
        
        # Send email via SES
        response = ses.send_email(
            Source='vinaya-c.nayanegali@capgemini.com',  # Must be verified in SES
            Destination={
                'ToAddresses': recipients
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body_text,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': body_html,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        print(f"Email notification sent to {recipients}. MessageId: {response['MessageId']}")
        return response
        
    except Exception as e:
        print(f"Error sending email notification: {str(e)}")
        # Don't fail the whole operation if email fails
        return None

def lambda_handler(event, context):
    try:
        print('Event:', json.dumps(event))
        
        http_method = event.get('requestContext', {}).get('http', {}).get('method')
        
        # Handle GET request - list all certificates
        if http_method == 'GET':
            response = table.scan()
            items = response.get('Items', [])
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(items, default=decimal_default)
            }
        
        # Handle POST request - add new certificate
        elif http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            # Add timestamps
            body['CreatedAt'] = datetime.now().isoformat()
            body['UpdatedAt'] = datetime.now().isoformat()
            
            table.put_item(Item=body)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Certificate added successfully', 'data': body}, default=decimal_default)
            }
        
        # Handle PUT request - update certificate or status
        elif http_method == 'PUT':
            body = json.loads(event.get('body', '{}'))
            cert_id = body.get('CertificateID')
            
            if not cert_id:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'CertificateID is required'})
                }
            
            # Get current certificate for comparison
            current_cert = table.get_item(Key={'CertificateID': cert_id}).get('Item', {})
            old_status = current_cert.get('Status', '')
            
            # Check if this is a status update
            new_status = body.get('Status')
            notes = body.get('Notes', '')
            incident_number = ''
            
            # Extract incident number from notes if present
            if notes and 'Incident:' in notes:
                parts = notes.split('.')
                if parts:
                    incident_part = parts[0].replace('Incident:', '').strip()
                    incident_number = incident_part
            
            # Update the certificate
            body['UpdatedAt'] = datetime.now().isoformat()
            
            # Build update expression
            update_expr = 'SET '
            expr_attr_values = {}
            expr_attr_names = {}
            
            for key, value in body.items():
                if key != 'CertificateID':
                    attr_name = f'#{key}'
                    attr_value = f':{key}'
                    expr_attr_names[attr_name] = key
                    expr_attr_values[attr_value] = value
                    update_expr += f'{attr_name} = {attr_value}, '
            
            update_expr = update_expr.rstrip(', ')
            
            table.update_item(
                Key={'CertificateID': cert_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values
            )
            
            # Send notification if status changed
            if new_status and new_status != old_status:
                print(f"Status changed from '{old_status}' to '{new_status}'. Sending notification...")
                send_status_change_notification(
                    certificate=current_cert,
                    old_status=old_status,
                    new_status=new_status,
                    notes=notes,
                    incident_number=incident_number
                )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Certificate updated successfully'})
            }
        
        # Handle DELETE request
        elif http_method == 'DELETE':
            cert_id = event.get('pathParameters', {}).get('id')
            
            if not cert_id:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Certificate ID is required'})
                }
            
            table.delete_item(Key={'CertificateID': cert_id})
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Certificate deleted successfully'})
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
    
    except Exception as e:
        print(f'Error: {str(e)}')
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to update certificate',
                'message': str(e)
            })
        }
