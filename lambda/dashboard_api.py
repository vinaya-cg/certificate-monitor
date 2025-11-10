import json
import boto3
import uuid
import os
from decimal import Decimal
from datetime import datetime, date

# Get table names from environment variables
CERTIFICATES_TABLE = os.environ.get('CERTIFICATES_TABLE', 'cert-management-dev-secure-certificates')

# CORS headers for all responses
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

def lambda_handler(event, context):
    """
    API to fetch and add certificates for the dashboard
    
    NOTE: When using AWS_PROXY integration with API Gateway, Lambda MUST return CORS headers.
    
    Supports:
    - GET: Fetch all certificates
    - POST: Add new certificate
    - PUT: Update existing certificate
    """
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(CERTIFICATES_TABLE)
    logs_table = dynamodb.Table(f"{CERTIFICATES_TABLE.rsplit('-', 1)[0]}-certificate-logs")
    
    # Get HTTP method - check multiple locations for compatibility
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    
    # Get path for routing
    path = event.get('path', event.get('rawPath', ''))
    
    print(f"HTTP Method: {http_method}")
    print(f"Path: {path}")
    print(f"Event: {json.dumps(event)}")
    
    try:
        # Check if this is a sync-acm request
        if 'sync-acm' in path and http_method == 'POST':
            return handle_acm_sync(event)
        
        # Handle different HTTP methods for certificates
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
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
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
        
        # Return response WITH CORS headers (required for AWS_PROXY integration)
        # Return just the array of certificates (dashboard expects array, not wrapped object)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps(json_certificates)
        }
        
    except Exception as e:
        print(f"Error fetching certificates: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
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
                'headers': CORS_HEADERS,
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
            'headers': CORS_HEADERS,
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
            'headers': CORS_HEADERS,
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
                'headers': CORS_HEADERS,
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
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'message': 'Certificate updated successfully'
            })
        }
        
    except Exception as e:
        print(f"Error updating certificate: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
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

def handle_acm_sync(event):
    """
    Handle manual ACM sync trigger - invokes ACM sync Lambda function
    This endpoint allows users to manually trigger ACM certificate synchronization
    """
    try:
        # Get ACM sync Lambda function name from environment
        acm_sync_function = os.environ.get('ACM_SYNC_FUNCTION', 'cert-management-dev-secure-acm-sync')
        
        print(f"Triggering manual ACM sync via Lambda: {acm_sync_function}")
        
        # Invoke ACM sync Lambda asynchronously
        lambda_client = boto3.client('lambda')
        
        response = lambda_client.invoke(
            FunctionName=acm_sync_function,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps({
                'httpMethod': 'POST',
                'source': 'manual-trigger',
                'triggeredBy': event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('email', 'unknown')
            })
        )
        
        print(f"ACM sync Lambda invoked. Status: {response['StatusCode']}")
        
        return {
            'statusCode': 202,  # Accepted
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'message': 'ACM synchronization started',
                'details': 'The sync process is running in the background. Check back in a few minutes to see new certificates.',
                'function': acm_sync_function,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error triggering ACM sync: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': 'Failed to trigger ACM sync',
                'message': str(e)
            })
        }

