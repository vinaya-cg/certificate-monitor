import json
import boto3
import pandas as pd
import os
import uuid
from datetime import datetime, timedelta
from io import BytesIO
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Environment variables
CERTIFICATES_TABLE = os.environ['CERTIFICATES_TABLE']
LOGS_TABLE = os.environ['LOGS_TABLE']
LOGS_BUCKET = os.environ['LOGS_BUCKET']
REGION = os.environ['REGION']

def lambda_handler(event, context):
    """
    Process Excel file uploaded to S3 and populate DynamoDB certificates table
    """
    logger.info(f"Excel processor triggered with event: {json.dumps(event)}")
    
    try:
        # Get S3 event details
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            logger.info(f"Processing file: s3://{bucket}/{key}")
            
            # Download and process Excel file
            process_excel_file(bucket, key)
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Excel file processed successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def process_excel_file(bucket, key):
    """
    Download Excel file from S3, parse it, and populate DynamoDB
    """
    # Download file from S3
    logger.info(f"Downloading file from S3: {bucket}/{key}")
    response = s3.get_object(Bucket=bucket, Key=key)
    excel_data = response['Body'].read()
    
    # Read Excel file with pandas
    df = pd.read_excel(BytesIO(excel_data))
    logger.info(f"Excel file read successfully. Rows: {len(df)}, Columns: {list(df.columns)}")
    
    # Map columns to standardized names
    column_mapping = map_excel_columns(df.columns)
    logger.info(f"Column mapping: {column_mapping}")
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Process each row
    certificates_table = dynamodb.Table(CERTIFICATES_TABLE)
    logs_table = dynamodb.Table(LOGS_TABLE)
    
    processed_count = 0
    errors = []
    
    for index, row in df.iterrows():
        try:
            # Generate unique certificate ID
            cert_id = str(uuid.uuid4())
            
            # Parse and prepare certificate data
            cert_data = prepare_certificate_data(row, cert_id)
            
            # Insert into certificates table
            certificates_table.put_item(Item=cert_data)
            
            # Create log entry
            log_entry = create_log_entry(cert_id, "INITIAL_IMPORT", cert_data)
            logs_table.put_item(Item=log_entry)
            
            processed_count += 1
            logger.info(f"Processed certificate {processed_count}: {cert_data.get('CertificateName', 'Unknown')}")
            
        except Exception as e:
            error_msg = f"Error processing row {index}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Create processing summary
    summary = {
        'total_rows': len(df),
        'processed_successfully': processed_count,
        'errors': len(errors),
        'error_details': errors[:10],  # Limit error details
        'processing_timestamp': datetime.utcnow().isoformat(),
        'source_file': f"s3://{bucket}/{key}"
    }
    
    # Save processing log to S3
    save_processing_log(summary, bucket, key)
    
    logger.info(f"Processing completed. Summary: {summary}")
    return summary

def map_excel_columns(columns):
    """
    Map Excel columns to standardized column names
    """
    column_mapping = {}
    
    # Define possible column mappings
    mappings = {
        'SN': ['sn', 'serial_number', 'serialnumber', 'number', 'id'],
        'CertificateName': ['certificate_name', 'certificatename', 'cert_name', 'name', 'certificate', 'domain'],
        'ExpiryDate': ['exp_date', 'expiry_date', 'expirydate', 'expiration_date', 'expires', 'expiry'],
        'AccountNumber': ['account_number', 'accountnumber', 'account', 'acc_number'],
        'Application': ['application', 'app', 'service', 'system'],
        'Environment': ['env', 'environment', 'stage'],
        'Type': ['type', 'certificate_type', 'cert_type', 'ssl_type'],
        'Status': ['status', 'state', 'condition'],
        'OwnerEmail': ['owner_email', 'owneremail', 'owner', 'contact_email', 'contact'],
        'SupportEmail': ['support_email', 'supportemail', 'support'],
        'IncidentNumber': ['incident_number', 'incidentnumber', 'incident', 'ticket_number'],
        'RenewedBy': ['renewed_by', 'renewedby', 'renewed_by_user'],
        'RenewalLog': ['renewal_log', 'renewallog', 'log'],
        'UploadS3Key': ['upload_s3_key', 'uploads3key', 's3_key'],
        'LastUpdatedOn': ['last_updated_on', 'lastupdatedon', 'updated_on', 'last_updated']
    }
    
    # Normalize column names and find matches
    for col in columns:
        col_lower = str(col).lower().strip().replace(' ', '_')
        
        # Direct match first
        for standard_name, variants in mappings.items():
            if col_lower == standard_name.lower():
                column_mapping[col] = standard_name
                break
            elif col_lower in variants:
                column_mapping[col] = standard_name
                break
        
        # If no match found, keep original column name
        if col not in column_mapping:
            column_mapping[col] = col
    
    return column_mapping

def prepare_certificate_data(row, cert_id):
    """
    Prepare certificate data for DynamoDB insertion
    """
    # Current timestamp
    current_time = datetime.utcnow().isoformat()
    
    # Parse expiry date
    expiry_date = parse_expiry_date(row.get('ExpiryDate'))
    
    # Calculate status based on expiry date
    status = calculate_certificate_status(expiry_date)
    
    # Prepare the certificate data
    cert_data = {
        'CertificateID': cert_id,
        'SN': str(row.get('SN', '')),
        'CertificateName': str(row.get('CertificateName', '')),
        'ExpiryDate': expiry_date,
        'AccountNumber': str(row.get('AccountNumber', '')),
        'Application': str(row.get('Application', '')),
        'Environment': str(row.get('Environment', 'Unknown')),
        'Type': str(row.get('Type', '')),
        'Status': status,
        'OwnerEmail': str(row.get('OwnerEmail', '')),
        'SupportEmail': str(row.get('SupportEmail', '')),
        'IncidentNumber': str(row.get('IncidentNumber', '')),
        'RenewedBy': str(row.get('RenewedBy', '')),
        'RenewalLog': str(row.get('RenewalLog', '')),
        'UploadS3Key': str(row.get('UploadS3Key', '')),
        'LastUpdatedOn': current_time,
        'CreatedOn': current_time,
        'ImportedFrom': 'Excel',
        'Version': 1
    }
    
    # Remove empty strings and None values
    cert_data = {k: v for k, v in cert_data.items() if v is not None and v != ''}
    
    return cert_data

def parse_expiry_date(date_value):
    """
    Parse expiry date from various formats
    """
    if pd.isna(date_value) or date_value is None:
        return None
    
    # If it's already a datetime object
    if isinstance(date_value, datetime):
        return date_value.strftime('%Y-%m-%d')
    
    # Try to parse string dates
    date_str = str(date_value).strip()
    
    # Common date formats
    date_formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%d %B %Y',
        '%B %d, %Y',
        '%d %b %Y'
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If no format matches, return the original value
    logger.warning(f"Could not parse date: {date_value}")
    return date_str

def calculate_certificate_status(expiry_date):
    """
    Calculate certificate status based on expiry date
    """
    if not expiry_date:
        return "Unknown"
    
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        current = datetime.utcnow()
        days_until_expiry = (expiry - current).days
        
        if days_until_expiry < 0:
            return "Expired"
        elif days_until_expiry <= 30:  # 30 days threshold
            return "Due for Renewal"
        else:
            return "Active"
            
    except ValueError:
        return "Unknown"

def create_log_entry(cert_id, action, data):
    """
    Create a log entry for the certificate operation
    """
    log_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    return {
        'LogID': log_id,
        'CertificateID': cert_id,
        'Timestamp': timestamp,
        'Action': action,
        'Details': {
            'certificate_name': data.get('CertificateName'),
            'status': data.get('Status'),
            'environment': data.get('Environment'),
            'owner_email': data.get('OwnerEmail')
        },
        'Metadata': {
            'source': 'ExcelProcessor',
            'version': '1.0'
        }
    }

def save_processing_log(summary, source_bucket, source_key):
    """
    Save processing summary to S3 logs bucket
    """
    try:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        log_key = f"excel_processing/{timestamp}_processing_log.json"
        
        log_content = {
            'summary': summary,
            'source_bucket': source_bucket,
            'source_key': source_key,
            'processor_version': '1.0'
        }
        
        s3.put_object(
            Bucket=LOGS_BUCKET,
            Key=log_key,
            Body=json.dumps(log_content, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Processing log saved to s3://{LOGS_BUCKET}/{log_key}")
        
    except Exception as e:
        logger.error(f"Failed to save processing log: {str(e)}")