import json
import boto3
from decimal import Decimal
from datetime import datetime, date

def lambda_handler(event, context):
    """
    Simple API to fetch certificates for the dashboard
    
    NOTE: CORS headers are handled by Lambda Function URL configuration in Terraform.
    DO NOT add CORS headers in the Lambda response - it will cause duplicate header errors!
    """
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('cert-management-dev-certificates')
    
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
        print(f"Error: {str(e)}")
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