"""
AWS Service Helper Functions
Centralized AWS service interactions for DynamoDB, S3, and SES
"""
import boto3
import logging
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# AWS Clients (lazy initialization)
_dynamodb_resource = None
_dynamodb_client = None
_s3_client = None
_ses_client = None


def get_dynamodb_resource(region: str = 'eu-west-1'):
    """Get or create DynamoDB resource"""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = boto3.resource('dynamodb', region_name=region)
    return _dynamodb_resource


def get_dynamodb_client(region: str = 'eu-west-1'):
    """Get or create DynamoDB client"""
    global _dynamodb_client
    if _dynamodb_client is None:
        _dynamodb_client = boto3.client('dynamodb', region_name=region)
    return _dynamodb_client


def get_s3_client(region: str = 'eu-west-1'):
    """Get or create S3 client"""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client('s3', region_name=region)
    return _s3_client


def get_ses_client(region: str = 'eu-west-1'):
    """Get or create SES client"""
    global _ses_client
    if _ses_client is None:
        _ses_client = boto3.client('ses', region_name=region)
    return _ses_client


def get_table(table_name: str, region: str = 'eu-west-1'):
    """
    Get DynamoDB table object
    
    Args:
        table_name: Name of the DynamoDB table
        region: AWS region (default: eu-west-1)
    
    Returns:
        DynamoDB Table resource
    """
    dynamodb = get_dynamodb_resource(region)
    return dynamodb.Table(table_name)


def scan_table_with_pagination(table_name: str, filter_expression=None, region: str = 'eu-west-1') -> List[Dict]:
    """
    Scan DynamoDB table with automatic pagination
    
    Args:
        table_name: Name of the table to scan
        filter_expression: Optional filter expression
        region: AWS region
    
    Returns:
        List of all items from the table
    """
    table = get_table(table_name, region)
    items = []
    
    try:
        scan_kwargs = {}
        if filter_expression:
            scan_kwargs['FilterExpression'] = filter_expression
        
        response = table.scan(**scan_kwargs)
        items.extend(response.get('Items', []))
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = table.scan(**scan_kwargs)
            items.extend(response.get('Items', []))
        
        logger.info(f"Scanned {len(items)} items from {table_name}")
        return items
        
    except Exception as e:
        logger.error(f"Error scanning table {table_name}: {str(e)}")
        raise


def put_item(table_name: str, item: Dict, region: str = 'eu-west-1') -> Dict:
    """
    Put item into DynamoDB table
    
    Args:
        table_name: Name of the table
        item: Item to insert
        region: AWS region
    
    Returns:
        Response from DynamoDB
    """
    table = get_table(table_name, region)
    
    try:
        response = table.put_item(Item=item)
        logger.info(f"Successfully added item to {table_name}")
        return response
    except Exception as e:
        logger.error(f"Error putting item to {table_name}: {str(e)}")
        raise


def update_item(table_name: str, key: Dict, update_expression: str, 
                expression_attribute_values: Dict, region: str = 'eu-west-1') -> Dict:
    """
    Update item in DynamoDB table
    
    Args:
        table_name: Name of the table
        key: Primary key of item to update
        update_expression: DynamoDB update expression
        expression_attribute_values: Values for update expression
        region: AWS region
    
    Returns:
        Response from DynamoDB
    """
    table = get_table(table_name, region)
    
    try:
        response = table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        logger.info(f"Successfully updated item in {table_name}")
        return response
    except Exception as e:
        logger.error(f"Error updating item in {table_name}: {str(e)}")
        raise


def get_item(table_name: str, key: Dict, region: str = 'eu-west-1') -> Optional[Dict]:
    """
    Get single item from DynamoDB table
    
    Args:
        table_name: Name of the table
        key: Primary key of item to retrieve
        region: AWS region
    
    Returns:
        Item if found, None otherwise
    """
    table = get_table(table_name, region)
    
    try:
        response = table.get_item(Key=key)
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting item from {table_name}: {str(e)}")
        raise


def send_email(sender: str, recipients: List[str], subject: str, 
               body_text: str, body_html: str = None, region: str = 'eu-west-1') -> Dict:
    """
    Send email using AWS SES
    
    Args:
        sender: Email address of sender (must be verified in SES)
        recipients: List of recipient email addresses
        subject: Email subject
        body_text: Plain text email body
        body_html: HTML email body (optional)
        region: AWS region
    
    Returns:
        Response from SES
    """
    ses = get_ses_client(region)
    
    try:
        message = {
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': body_text}}
        }
        
        if body_html:
            message['Body']['Html'] = {'Data': body_html}
        
        response = ses.send_email(
            Source=sender,
            Destination={'ToAddresses': recipients},
            Message=message
        )
        
        logger.info(f"Email sent successfully to {recipients}")
        return response
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise


def upload_to_s3(bucket: str, key: str, body: bytes, 
                content_type: str = 'application/octet-stream', region: str = 'eu-west-1') -> Dict:
    """
    Upload object to S3
    
    Args:
        bucket: S3 bucket name
        key: Object key (file path in S3)
        body: File content as bytes
        content_type: MIME type
        region: AWS region
    
    Returns:
        Response from S3
    """
    s3 = get_s3_client(region)
    
    try:
        response = s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType=content_type
        )
        logger.info(f"Uploaded {key} to s3://{bucket}/")
        return response
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise


def convert_decimal(obj: Any) -> Any:
    """
    Convert Decimal types to regular numbers for JSON serialization
    Also handles datetime objects
    
    Args:
        obj: Object to convert
    
    Returns:
        Converted object safe for JSON serialization
    """
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    return obj


def batch_write_items(table_name: str, items: List[Dict], region: str = 'eu-west-1') -> None:
    """
    Batch write items to DynamoDB (max 25 items per batch)
    
    Args:
        table_name: Name of the table
        items: List of items to write
        region: AWS region
    """
    dynamodb = get_dynamodb_resource(region)
    table = dynamodb.Table(table_name)
    
    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
        
        logger.info(f"Batch wrote {len(items)} items to {table_name}")
    except Exception as e:
        logger.error(f"Error in batch write to {table_name}: {str(e)}")
        raise
