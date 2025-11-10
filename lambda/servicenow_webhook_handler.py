"""
ServiceNow Webhook Handler for Certificate Assignment Updates
==============================================================

This Lambda function receives webhooks from ServiceNow when incidents are assigned
and automatically updates the certificate status and assignee information in DynamoDB.

Webhook Flow:
1. Engineer assigns/picks incident in ServiceNow
2. ServiceNow Business Rule triggers webhook to API Gateway
3. This Lambda processes the assignment
4. Updates certificate with assignee details and status

Features:
- Validates webhook signature from ServiceNow
- Updates certificate assignee and status
- Logs all assignment actions
- Handles error cases gracefully
- Supports incident state changes (assigned, in-progress, resolved)

Author: Certificate Management Team
Version: 1.0.0
"""

import json
import boto3
import os
import logging
from datetime import datetime
import hmac
import hashlib
import base64
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')

# Environment variables
CERTIFICATES_TABLE = os.environ['CERTIFICATES_TABLE']
LOGS_TABLE = os.environ['LOGS_TABLE']
WEBHOOK_SECRET_NAME = os.environ.get('WEBHOOK_SECRET_NAME', 'cert-management/servicenow/webhook-secret')

# Cache for webhook secret
_webhook_secret = None

# ServiceNow incident states mapping
INCIDENT_STATES = {
    '1': 'New',
    '2': 'In Progress',
    '3': 'On Hold',
    '6': 'Resolved',
    '7': 'Closed',
    '8': 'Canceled'
}

# Certificate status mapping based on incident state
STATUS_MAPPING = {
    '1': 'Pending Assignment',      # New
    '2': 'Renewal in Progress',     # In Progress
    '3': 'On Hold',                 # On Hold
    '6': 'Renewal Done',            # Resolved
    '7': 'Renewal Done',            # Closed
    '8': 'Renewal Canceled'         # Canceled
}


def lambda_handler(event, context):
    """
    Main Lambda handler for ServiceNow webhook
    
    Expected webhook payload from ServiceNow:
    {
        "incident_number": "INC0123456",
        "sys_id": "abc123...",
        "state": "2",
        "assigned_to": {
            "name": "John Doe",
            "email": "john.doe@company.com",
            "sys_id": "user123"
        },
        "correlation_id": "CERT-12345",
        "short_description": "Certificate expiring...",
        "priority": "2",
        "updated_on": "2025-11-10 10:30:00"
    }
    
    Args:
        event: API Gateway event with webhook payload
        context: Lambda context
        
    Returns:
        dict: API Gateway response
    """
    try:
        logger.info("Received ServiceNow webhook")
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        logger.info(f"Webhook payload: {json.dumps(body, default=str)}")
        
        # Validate webhook signature (optional but recommended)
        if not validate_webhook_signature(event, body):
            logger.warning("Invalid webhook signature")
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid signature'})
            }
        
        # Extract incident details
        incident_number = body.get('incident_number')
        correlation_id = body.get('correlation_id')  # CertificateID
        state = body.get('state')
        assigned_to = body.get('assigned_to', {})
        updated_on = body.get('updated_on', datetime.utcnow().isoformat())
        
        # Validate required fields
        if not correlation_id:
            logger.error("Missing correlation_id in webhook payload")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing correlation_id'})
            }
        
        if not incident_number:
            logger.error("Missing incident_number in webhook payload")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing incident_number'})
            }
        
        # Update certificate in DynamoDB
        result = update_certificate_assignment(
            certificate_id=correlation_id,
            incident_number=incident_number,
            state=state,
            assigned_to=assigned_to,
            updated_on=updated_on
        )
        
        if result['success']:
            logger.info(f"Successfully updated certificate {correlation_id}")
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'message': 'Certificate updated successfully',
                    'certificate_id': correlation_id,
                    'status': result.get('new_status'),
                    'assignee': result.get('assignee')
                })
            }
        else:
            logger.error(f"Failed to update certificate: {result.get('error')}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Failed to update certificate',
                    'details': result.get('error')
                })
            }
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }


def validate_webhook_signature(event, body):
    """
    Validate webhook signature from ServiceNow
    
    ServiceNow can send a signature in the X-ServiceNow-Signature header
    to verify the webhook authenticity.
    
    Args:
        event: API Gateway event
        body: Parsed request body
        
    Returns:
        bool: True if signature is valid or validation is disabled
    """
    try:
        # Get signature from headers
        headers = event.get('headers', {})
        signature = headers.get('X-ServiceNow-Signature') or headers.get('x-servicenow-signature')
        
        # If no signature header, check if validation is required
        if not signature:
            # For now, allow webhooks without signature
            # In production, you should enable signature validation
            logger.info("No signature header found, proceeding without validation")
            return True
        
        # Get webhook secret
        secret = get_webhook_secret()
        if not secret:
            logger.warning("No webhook secret configured, skipping validation")
            return True
        
        # Calculate expected signature
        body_str = json.dumps(body, separators=(',', ':'), sort_keys=True)
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            body_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        logger.error(f"Error validating signature: {str(e)}")
        # On error, allow the request (fail open)
        # In production, you might want to fail closed (return False)
        return True


def get_webhook_secret():
    """
    Retrieve webhook secret from Secrets Manager (cached)
    
    Returns:
        str: Webhook secret or None if not configured
    """
    global _webhook_secret
    
    if _webhook_secret is not None:
        return _webhook_secret
    
    try:
        response = secrets_manager.get_secret_value(SecretId=WEBHOOK_SECRET_NAME)
        secret_data = json.loads(response['SecretString'])
        _webhook_secret = secret_data.get('webhook_secret')
        return _webhook_secret
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.warning(f"Webhook secret not found: {WEBHOOK_SECRET_NAME}")
            return None
        else:
            logger.error(f"Error retrieving webhook secret: {str(e)}")
            return None


def update_certificate_assignment(certificate_id, incident_number, state, assigned_to, updated_on):
    """
    Update certificate with assignment details
    
    Args:
        certificate_id: Certificate ID (correlation_id from ServiceNow)
        incident_number: ServiceNow incident number
        state: ServiceNow incident state
        assigned_to: Dictionary with assignee details
        updated_on: Timestamp of the update
        
    Returns:
        dict: Result with success status and details
    """
    try:
        table = dynamodb.Table(CERTIFICATES_TABLE)
        
        # Determine new status based on incident state
        new_status = STATUS_MAPPING.get(state, 'Unknown')
        state_name = INCIDENT_STATES.get(state, 'Unknown')
        
        # Extract assignee information
        assignee_name = assigned_to.get('name', 'Unassigned')
        assignee_email = assigned_to.get('email', '')
        
        # Prepare update expression
        update_expr_parts = []
        expr_attr_values = {}
        expr_attr_names = {}
        
        # Always update LastUpdatedOn
        update_expr_parts.append('#lu = :lu')
        expr_attr_names['#lu'] = 'LastUpdatedOn'
        expr_attr_values[':lu'] = updated_on
        
        # Update status
        update_expr_parts.append('#status = :status')
        expr_attr_names['#status'] = 'Status'
        expr_attr_values[':status'] = new_status
        
        # Update assignee details if provided
        if assignee_name and assignee_name != 'Unassigned':
            update_expr_parts.append('AssignedTo = :assignee')
            update_expr_parts.append('AssignedToEmail = :assignee_email')
            update_expr_parts.append('AssignedOn = :assigned_on')
            expr_attr_values[':assignee'] = assignee_name
            expr_attr_values[':assignee_email'] = assignee_email
            expr_attr_values[':assigned_on'] = updated_on
        
        # Update incident details
        update_expr_parts.append('IncidentNumber = :incident')
        update_expr_parts.append('IncidentState = :state')
        update_expr_parts.append('IncidentStateText = :state_text')
        expr_attr_values[':incident'] = incident_number
        expr_attr_values[':state'] = state
        expr_attr_values[':state_text'] = state_name
        
        update_expression = 'SET ' + ', '.join(update_expr_parts)
        
        # Update the certificate
        response = table.update_item(
            Key={'CertificateID': certificate_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues='ALL_NEW'
        )
        
        updated_cert = response.get('Attributes', {})
        
        logger.info(f"Certificate {certificate_id} updated - Status: {new_status}, Assignee: {assignee_name}")
        
        # Log the action
        log_assignment_action(
            certificate_id=certificate_id,
            incident_number=incident_number,
            action=f'INCIDENT_{state_name.upper().replace(" ", "_")}',
            assignee=assignee_name,
            assignee_email=assignee_email,
            new_status=new_status
        )
        
        return {
            'success': True,
            'new_status': new_status,
            'assignee': assignee_name,
            'certificate': updated_cert
        }
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            error_msg = f"Certificate {certificate_id} not found"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        else:
            error_msg = f"DynamoDB error: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {'success': False, 'error': error_msg}


def log_assignment_action(certificate_id, incident_number, action, assignee, assignee_email, new_status):
    """
    Log assignment action to certificate logs table
    
    Args:
        certificate_id: Certificate ID
        incident_number: ServiceNow incident number
        action: Action performed
        assignee: Assignee name
        assignee_email: Assignee email
        new_status: New certificate status
    """
    try:
        logs_table = dynamodb.Table(LOGS_TABLE)
        
        timestamp = datetime.utcnow().isoformat()
        log_id = f"{certificate_id}#{timestamp}"
        
        logs_table.put_item(
            Item={
                'LogID': log_id,
                'Timestamp': timestamp,
                'CertificateID': certificate_id,
                'Action': action,
                'IncidentNumber': incident_number,
                'Assignee': assignee,
                'AssigneeEmail': assignee_email,
                'NewStatus': new_status,
                'Source': 'ServiceNow Webhook',
                'Details': f'Certificate assigned to {assignee} via incident {incident_number}'
            }
        )
        
        logger.info(f"Logged action {action} for certificate {certificate_id}")
        
    except Exception as e:
        # Log error but don't fail the main operation
        logger.error(f"Error logging action: {str(e)}", exc_info=True)


# For local testing
if __name__ == "__main__":
    # Sample test event
    test_event = {
        'headers': {},
        'body': json.dumps({
            'incident_number': 'INC0817937',
            'sys_id': 'abc123',
            'state': '2',  # In Progress
            'assigned_to': {
                'name': 'John Doe',
                'email': 'john.doe@sogeti.com',
                'sys_id': 'user123'
            },
            'correlation_id': 'cert-12345',
            'short_description': 'Certificate expiring in 7 days',
            'priority': '2',
            'updated_on': datetime.utcnow().isoformat()
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
