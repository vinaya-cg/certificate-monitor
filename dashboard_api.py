import json
import boto3
import uuid
from decimal import Decimal
from datetime import datetime, date

def lambda_handler(event, context):
    """
    API to fetch and add certificates for the dashboard
    
    NOTE: CORS headers are handled by Lambda Function URL configuration in Terraform.
    DO NOT add CORS headers in the Lambda response - it will cause duplicate header errors!
    
    Supports:
    - GET: Fetch all certificates
    - POST: Add new certificate
    - PUT: Update existing certificate
    """
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('cert-management-dev-certificates')
    logs_table = dynamodb.Table('cert-management-dev-certificate-logs')
    
    # Get HTTP method
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    
    try:
        # Handle different HTTP methods
        if http_method == 'POST':
            return handle_add_certificate(event, table, logs_table)
        elif http_method == 'PUT':
            return handle_update_certificate(event, table, logs_table)
        else:  # GET or default
            return handle_get_certificates(table)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Request failed',
                'message': str(e)
            })
        }

def handle_get_certificates(table):
    """Handle GET request - fetch all certificates"""
    try:
        # Get all certificates
        response = table.scan()
        certificates = response['Items']
        
        # Convert Decimal types to regular numbers for JSON serialization
        def convert_decimal(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal(item) for item in obj]
            return obj
        
        # Convert all certificates
        json_certificates = convert_decimal(certificates)
        
        # Return response WITHOUT CORS headers (handled by Lambda Function URL config)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'certificates': json_certificates,
                'count': len(certificates),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        }
        
    except Exception as e:
        print(f"Error fetching certificates: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Failed to fetch certificates',
                'message': str(e)
            })
        }

def handle_add_certificate(event, table, logs_table):
    """Handle POST request - add new certificate"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        required_fields = ['CertificateName', 'Environment', 'Application', 'ExpiryDate', 'OwnerEmail']
        missing_fields = [field for field in required_fields if not body.get(field)]
        
        if missing_fields:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Missing required fields',
                    'missing': missing_fields
                })
            }
        
        # Generate certificate ID
        cert_id = body.get('CertificateID') or f"cert-{str(uuid.uuid4())}"
        
        # Calculate status based on expiry date
        expiry_date = body.get('ExpiryDate')
        status = calculate_status(expiry_date)
        days_until_expiry = calculate_days_until_expiry(expiry_date)
        
        # Prepare certificate data
        current_time = datetime.utcnow().isoformat() + 'Z'
        certificate = {
            'CertificateID': cert_id,
            'CertificateName': body.get('CertificateName'),
            'Environment': body.get('Environment'),
            'Application': body.get('Application'),
            'ExpiryDate': expiry_date,
            'Type': body.get('Type', 'SSL/TLS'),
            'Status': status,
            'DaysUntilExpiry': str(days_until_expiry),
            'OwnerEmail': body.get('OwnerEmail'),
            'SupportEmail': body.get('SupportEmail', ''),
            'AccountNumber': body.get('AccountNumber', ''),
            'SerialNumber': body.get('SerialNumber', ''),
            'LastUpdatedOn': current_time,
            'CreatedOn': current_time,
            'Version': 1,
            'ImportedFrom': body.get('ImportedFrom', 'Dashboard'),
        }
        
        # Remove empty fields
        certificate = {k: v for k, v in certificate.items() if v not in [None, '', 'None']}
        
        # Add to DynamoDB
        table.put_item(Item=certificate)
        
        # Log the action
        log_entry = {
            'LogID': f"log-{str(uuid.uuid4())}",
            'CertificateID': cert_id,
            'Action': 'CREATE',
            'Timestamp': current_time,
            'Details': f"Certificate {body.get('CertificateName')} added via dashboard",
            'PerformedBy': body.get('OwnerEmail', 'Unknown')
        }
        logs_table.put_item(Item=log_entry)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': True,
                'message': 'Certificate added successfully',
                'certificate': convert_decimal(certificate)
            })
        }
        
    except Exception as e:
        print(f"Error adding certificate: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Failed to add certificate',
                'message': str(e)
            })
        }

def handle_update_certificate(event, table, logs_table):
    """Handle PUT request - update existing certificate"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        cert_id = body.get('CertificateID')
        
        if not cert_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'CertificateID is required'})
            }
        
        # Calculate status if expiry date is provided
        if body.get('ExpiryDate'):
            body['Status'] = calculate_status(body['ExpiryDate'])
            body['DaysUntilExpiry'] = str(calculate_days_until_expiry(body['ExpiryDate']))
        
        # Update timestamp
        body['LastUpdatedOn'] = datetime.utcnow().isoformat() + 'Z'
        
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        for key, value in body.items():
            if key != 'CertificateID' and value not in [None, '', 'None']:
                attr_name = f"#{key}"
                attr_value = f":{key}"
                update_expr += f"{attr_name} = {attr_value}, "
                expr_attr_names[attr_name] = key
                expr_attr_values[attr_value] = value
        
        # Remove trailing comma
        update_expr = update_expr.rstrip(', ')
        
        # Update in DynamoDB
        table.update_item(
            Key={'CertificateID': cert_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        
        # Log the action
        log_entry = {
            'LogID': f"log-{str(uuid.uuid4())}",
            'CertificateID': cert_id,
            'Action': 'UPDATE',
            'Timestamp': datetime.utcnow().isoformat() + 'Z',
            'Details': f"Certificate updated via dashboard",
            'PerformedBy': body.get('OwnerEmail', 'Unknown')
        }
        logs_table.put_item(Item=log_entry)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': True,
                'message': 'Certificate updated successfully'
            })
        }
        
    except Exception as e:
        print(f"Error updating certificate: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Failed to update certificate',
                'message': str(e)
            })
        }

def calculate_status(expiry_date):
    """Calculate certificate status based on expiry date"""
    try:
        expiry = datetime.fromisoformat(expiry_date.replace('Z', ''))
        today = datetime.utcnow()
        days_left = (expiry - today).days
        
        if days_left < 0:
            return 'Expired'
        elif days_left <= 30:
            return 'Due for Renewal'
        else:
            return 'Active'
    except:
        return 'Unknown'

def calculate_days_until_expiry(expiry_date):
    """Calculate days until expiry"""
    try:
        expiry = datetime.fromisoformat(expiry_date.replace('Z', ''))
        today = datetime.utcnow()
        days_left = (expiry - today).days
        return days_left
    except:
        return 0

def convert_decimal(obj):
    """Convert Decimal types to regular numbers for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    return obj
