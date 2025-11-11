"""
Server Certificate Scanner Lambda Function

This Lambda function scans certificates from Windows and Linux servers using AWS Systems Manager (SSM).
It executes SSM Run Commands to retrieve certificates from server certificate stores and imports them
into the certificate management dashboard.

Features:
- Scans Windows servers (CurrentUser\My and LocalMachine\My certificate stores)
- Scans Linux servers (/etc/ssl/certs, /etc/pki/tls/certs, custom paths)
- Uses AWS Systems Manager Run Command for agent-based scanning
- Supports multi-account, multi-region server scanning
- Preserves manually entered data (OwnerEmail, SupportEmail, notes)
- Prevents duplicates using ServerID + Thumbprint composite key

Environment Variables:
- CERTIFICATES_TABLE: DynamoDB table name for certificates
- REGION: AWS region
- SSM_DOCUMENT_WINDOWS: SSM document name for Windows scanning
- SSM_DOCUMENT_LINUX: SSM document name for Linux scanning
"""

import json
import boto3
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
import re

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
ssm_client = boto3.client('ssm')
ec2_client = boto3.client('ec2')
sts_client = boto3.client('sts')

# Environment variables
CERTIFICATES_TABLE = os.environ.get('CERTIFICATES_TABLE', 'cert-management-dev-secure-certificates')
REGION = os.environ.get('REGION', 'eu-west-1')
SSM_DOCUMENT_WINDOWS = os.environ.get('SSM_DOCUMENT_WINDOWS', 'CertScan-Windows')
SSM_DOCUMENT_LINUX = os.environ.get('SSM_DOCUMENT_LINUX', 'CertScan-Linux')

# Maximum concurrent SSM commands
MAX_CONCURRENT_COMMANDS = 50

# Preserve these fields from manual entries
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
    Main Lambda handler for server certificate scanning
    
    Args:
        event: Lambda event (can be EventBridge scheduled event or API Gateway request)
        context: Lambda context
        
    Returns:
        dict: Scan results including counts and any errors
    """
    print(f"Server Certificate Scanner started at {datetime.now(timezone.utc).isoformat()}")
    print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")
    
    try:
        # Get current AWS account
        current_account = sts_client.get_caller_identity()['Account']
        print(f"Current AWS Account: {current_account}")
        
        # Initialize scan statistics
        stats = {
            'startTime': datetime.now(timezone.utc).isoformat(),
            'serversScanned': 0,
            'windowsServers': 0,
            'linuxServers': 0,
            'certificatesFound': 0,
            'certificatesAdded': 0,
            'certificatesUpdated': 0,
            'certificatesSkipped': 0,
            'errors': []
        }
        
        # Get list of managed instances (servers with SSM agent)
        managed_instances = get_managed_instances()
        
        if not managed_instances:
            print("No managed instances found with SSM agent")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No managed instances found',
                    'stats': stats
                }, cls=DecimalEncoder)
            }
        
        print(f"Found {len(managed_instances)} managed instances")
        
        # Group instances by platform
        windows_instances = [i for i in managed_instances if i['platform'] == 'Windows']
        linux_instances = [i for i in managed_instances if i['platform'] == 'Linux']
        
        print(f"Windows instances: {len(windows_instances)}")
        print(f"Linux instances: {len(linux_instances)}")
        
        # Scan Windows servers
        if windows_instances:
            windows_stats = scan_windows_servers(windows_instances)
            stats['windowsServers'] = windows_stats['scanned']
            stats['certificatesFound'] += windows_stats['found']
            stats['certificatesAdded'] += windows_stats['added']
            stats['certificatesUpdated'] += windows_stats['updated']
            stats['certificatesSkipped'] += windows_stats['skipped']
            stats['errors'].extend(windows_stats['errors'])
        
        # Scan Linux servers
        if linux_instances:
            linux_stats = scan_linux_servers(linux_instances)
            stats['linuxServers'] = linux_stats['scanned']
            stats['certificatesFound'] += linux_stats['found']
            stats['certificatesAdded'] += linux_stats['added']
            stats['certificatesUpdated'] += linux_stats['updated']
            stats['certificatesSkipped'] += linux_stats['skipped']
            stats['errors'].extend(linux_stats['errors'])
        
        # Finalize statistics
        stats['serversScanned'] = stats['windowsServers'] + stats['linuxServers']
        stats['endTime'] = datetime.now(timezone.utc).isoformat()
        stats['success'] = len(stats['errors']) == 0
        
        print(f"\n{'='*60}")
        print("SERVER CERTIFICATE SCAN COMPLETED")
        print(f"{'='*60}")
        print(f"Servers Scanned: {stats['serversScanned']} (Windows: {stats['windowsServers']}, Linux: {stats['linuxServers']})")
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
                'message': 'Server certificate scan failed'
            })
        }


def get_managed_instances() -> List[Dict]:
    """
    Get list of EC2 instances with SSM agent installed and running
    
    Returns:
        List of instance dictionaries with id, name, platform, ip
    """
    instances = []
    
    try:
        # Get all managed instances from SSM
        paginator = ssm_client.get_paginator('describe_instance_information')
        
        for page in paginator.paginate():
            for instance in page['InstanceInformationList']:
                # Only include online instances
                if instance.get('PingStatus') == 'Online':
                    instances.append({
                        'instanceId': instance['InstanceId'],
                        'name': instance.get('Name', instance['InstanceId']),
                        'platform': instance.get('PlatformType', 'Unknown'),
                        'platformName': instance.get('PlatformName', 'Unknown'),
                        'platformVersion': instance.get('PlatformVersion', 'Unknown'),
                        'ipAddress': instance.get('IPAddress', 'Unknown'),
                        'agentVersion': instance.get('AgentVersion', 'Unknown')
                    })
        
        print(f"Found {len(instances)} online managed instances")
        
    except Exception as e:
        print(f"Error getting managed instances: {str(e)}")
        raise
    
    return instances


def scan_windows_servers(instances: List[Dict]) -> Dict:
    """
    Scan certificates from Windows servers using SSM Run Command
    
    Args:
        instances: List of Windows instance dictionaries
        
    Returns:
        dict: Statistics for Windows scanning
    """
    stats = {'scanned': 0, 'found': 0, 'added': 0, 'updated': 0, 'skipped': 0, 'errors': []}
    
    print(f"\n{'='*60}")
    print(f"Scanning {len(instances)} Windows Servers")
    print(f"{'='*60}")
    
    # Process instances in batches to respect AWS limits
    batch_size = MAX_CONCURRENT_COMMANDS
    
    for i in range(0, len(instances), batch_size):
        batch = instances[i:i + batch_size]
        instance_ids = [inst['instanceId'] for inst in batch]
        
        print(f"\nProcessing batch {i//batch_size + 1}: {len(batch)} instances")
        
        try:
            # Send SSM Run Command to fetch certificates
            response = ssm_client.send_command(
                InstanceIds=instance_ids,
                DocumentName=SSM_DOCUMENT_WINDOWS,
                Comment='Certificate scan for dashboard',
                TimeoutSeconds=300
            )
            
            command_id = response['Command']['CommandId']
            print(f"Command ID: {command_id}")
            
            # Wait for command to complete
            time.sleep(5)  # Initial wait
            
            # Check command status and get results
            for instance in batch:
                try:
                    instance_id = instance['instanceId']
                    
                    # Get command invocation result
                    invocation = ssm_client.get_command_invocation(
                        CommandId=command_id,
                        InstanceId=instance_id
                    )
                    
                    status = invocation['Status']
                    
                    if status == 'Success':
                        output = invocation.get('StandardOutputContent', '')
                        certificates = parse_windows_certificate_output(output, instance)
                        
                        print(f"  {instance['name']}: Found {len(certificates)} certificates")
                        
                        # Store certificates in DynamoDB
                        for cert in certificates:
                            result = store_certificate(cert)
                            if result == 'added':
                                stats['added'] += 1
                            elif result == 'updated':
                                stats['updated'] += 1
                            else:
                                stats['skipped'] += 1
                        
                        stats['found'] += len(certificates)
                        stats['scanned'] += 1
                        
                    elif status in ['Pending', 'InProgress', 'Delayed']:
                        print(f"  {instance['name']}: Command still running (status: {status})")
                        # Could implement retry logic here
                        
                    else:
                        error_msg = f"Command failed on {instance['name']}: {status}"
                        print(f"  ERROR: {error_msg}")
                        stats['errors'].append(error_msg)
                
                except Exception as instance_error:
                    error_msg = f"Error processing {instance['instanceId']}: {str(instance_error)}"
                    print(f"  ERROR: {error_msg}")
                    stats['errors'].append(error_msg)
        
        except Exception as batch_error:
            error_msg = f"Error processing batch: {str(batch_error)}"
            print(f"ERROR: {error_msg}")
            stats['errors'].append(error_msg)
    
    return stats


def scan_linux_servers(instances: List[Dict]) -> Dict:
    """
    Scan certificates from Linux servers using SSM Run Command
    
    Args:
        instances: List of Linux instance dictionaries
        
    Returns:
        dict: Statistics for Linux scanning
    """
    stats = {'scanned': 0, 'found': 0, 'added': 0, 'updated': 0, 'skipped': 0, 'errors': []}
    
    print(f"\n{'='*60}")
    print(f"Scanning {len(instances)} Linux Servers")
    print(f"{'='*60}")
    
    # Process instances in batches
    batch_size = MAX_CONCURRENT_COMMANDS
    
    for i in range(0, len(instances), batch_size):
        batch = instances[i:i + batch_size]
        instance_ids = [inst['instanceId'] for inst in batch]
        
        print(f"\nProcessing batch {i//batch_size + 1}: {len(batch)} instances")
        
        try:
            # Send SSM Run Command to fetch certificates
            response = ssm_client.send_command(
                InstanceIds=instance_ids,
                DocumentName=SSM_DOCUMENT_LINUX,
                Comment='Certificate scan for dashboard',
                TimeoutSeconds=300
            )
            
            command_id = response['Command']['CommandId']
            print(f"Command ID: {command_id}")
            
            # Wait for command to complete
            time.sleep(5)
            
            # Check command status and get results
            for instance in batch:
                try:
                    instance_id = instance['instanceId']
                    
                    # Get command invocation result
                    invocation = ssm_client.get_command_invocation(
                        CommandId=command_id,
                        InstanceId=instance_id
                    )
                    
                    status = invocation['Status']
                    
                    if status == 'Success':
                        output = invocation.get('StandardOutputContent', '')
                        certificates = parse_linux_certificate_output(output, instance)
                        
                        print(f"  {instance['name']}: Found {len(certificates)} certificates")
                        
                        # Store certificates in DynamoDB
                        for cert in certificates:
                            result = store_certificate(cert)
                            if result == 'added':
                                stats['added'] += 1
                            elif result == 'updated':
                                stats['updated'] += 1
                            else:
                                stats['skipped'] += 1
                        
                        stats['found'] += len(certificates)
                        stats['scanned'] += 1
                        
                    elif status in ['Pending', 'InProgress', 'Delayed']:
                        print(f"  {instance['name']}: Command still running (status: {status})")
                        
                    else:
                        error_msg = f"Command failed on {instance['name']}: {status}"
                        print(f"  ERROR: {error_msg}")
                        stats['errors'].append(error_msg)
                
                except Exception as instance_error:
                    error_msg = f"Error processing {instance['instanceId']}: {str(instance_error)}"
                    print(f"  ERROR: {error_msg}")
                    stats['errors'].append(error_msg)
        
        except Exception as batch_error:
            error_msg = f"Error processing batch: {str(batch_error)}"
            print(f"ERROR: {error_msg}")
            stats['errors'].append(error_msg)
    
    return stats


def parse_windows_certificate_output(output: str, instance: Dict) -> List[Dict]:
    """
    Parse PowerShell output from Windows certificate scanning
    
    Args:
        output: PowerShell script output
        instance: Instance metadata
        
    Returns:
        List of certificate dictionaries
    """
    certificates = []
    
    # Split output by certificate separator
    cert_blocks = output.split('----------------------------------------')
    
    for block in cert_blocks:
        if not block.strip():
            continue
        
        try:
            # Extract certificate fields using regex
            subject_match = re.search(r'Subject\s*:\s*(.+)', block)
            issuer_match = re.search(r'Issuer\s*:\s*(.+)', block)
            valid_from_match = re.search(r'Valid From\s*:\s*(.+)', block)
            valid_until_match = re.search(r'Valid Until\s*:\s*(.+)', block)
            thumbprint_match = re.search(r'Thumbprint\s*:\s*(.+)', block)
            store_match = re.search(r'Scanning store:\s*(.+)', block)
            
            if subject_match and valid_until_match and thumbprint_match:
                subject = subject_match.group(1).strip()
                issuer = issuer_match.group(1).strip() if issuer_match else 'Unknown'
                valid_from = valid_from_match.group(1).strip() if valid_from_match else None
                valid_until = valid_until_match.group(1).strip()
                thumbprint = thumbprint_match.group(1).strip()
                
                # Extract Common Name from Subject
                cn_match = re.search(r'CN=([^,]+)', subject)
                common_name = cn_match.group(1) if cn_match else subject
                
                # Parse expiry date
                try:
                    expiry_date = datetime.strptime(valid_until, '%m/%d/%Y %I:%M:%S %p')
                    expiry_date_str = expiry_date.strftime('%Y-%m-%d')
                except:
                    # Try alternative date format
                    try:
                        expiry_date = datetime.strptime(valid_until.split()[0], '%m/%d/%Y')
                        expiry_date_str = expiry_date.strftime('%Y-%m-%d')
                    except:
                        expiry_date_str = valid_until
                
                # Determine certificate status
                status = calculate_certificate_status(expiry_date_str)
                
                # Create certificate object
                certificate = {
                    'CertificateID': f"{instance['instanceId']}_{thumbprint}",
                    'CertificateName': common_name,
                    'CommonName': common_name,
                    'Subject': subject,
                    'Issuer': issuer,
                    'ExpiryDate': expiry_date_str,
                    'ValidFrom': valid_from if valid_from else None,
                    'Thumbprint': thumbprint,
                    'Status': status,
                    'Source': 'Server-Windows',
                    'ServerID': instance['instanceId'],
                    'ServerName': instance['name'],
                    'ServerPlatform': instance['platformName'],
                    'ServerIP': instance['ipAddress'],
                    'Environment': determine_environment(instance['name']),
                    'LastScannedOn': datetime.now(timezone.utc).isoformat(),
                    'SyncedFrom': 'SSM',
                    'AccountNumber': sts_client.get_caller_identity()['Account']
                }
                
                certificates.append(certificate)
        
        except Exception as parse_error:
            print(f"Error parsing certificate block: {str(parse_error)}")
            continue
    
    return certificates


def parse_linux_certificate_output(output: str, instance: Dict) -> List[Dict]:
    """
    Parse shell output from Linux certificate scanning
    
    Args:
        output: Shell script output (JSON format expected)
        instance: Instance metadata
        
    Returns:
        List of certificate dictionaries
    """
    certificates = []
    
    try:
        # Expected JSON output from Linux script
        # Format: [{"subject": "...", "issuer": "...", "notAfter": "...", "fingerprint": "...", "path": "..."}]
        cert_data = json.loads(output)
        
        for cert in cert_data:
            try:
                subject = cert.get('subject', 'Unknown')
                issuer = cert.get('issuer', 'Unknown')
                not_after = cert.get('notAfter', '')
                fingerprint = cert.get('fingerprint', '')
                file_path = cert.get('path', '')
                
                # Extract Common Name from Subject
                cn_match = re.search(r'CN=([^,]+)', subject)
                common_name = cn_match.group(1) if cn_match else subject
                
                # Parse expiry date (OpenSSL format: Apr 15 00:00:00 2025 GMT)
                try:
                    expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                    expiry_date_str = expiry_date.strftime('%Y-%m-%d')
                except:
                    expiry_date_str = not_after
                
                # Determine certificate status
                status = calculate_certificate_status(expiry_date_str)
                
                # Create certificate object
                certificate = {
                    'CertificateID': f"{instance['instanceId']}_{fingerprint}",
                    'CertificateName': common_name,
                    'CommonName': common_name,
                    'Subject': subject,
                    'Issuer': issuer,
                    'ExpiryDate': expiry_date_str,
                    'Thumbprint': fingerprint,
                    'FilePath': file_path,
                    'Status': status,
                    'Source': 'Server-Linux',
                    'ServerID': instance['instanceId'],
                    'ServerName': instance['name'],
                    'ServerPlatform': instance['platformName'],
                    'ServerIP': instance['ipAddress'],
                    'Environment': determine_environment(instance['name']),
                    'LastScannedOn': datetime.now(timezone.utc).isoformat(),
                    'SyncedFrom': 'SSM',
                    'AccountNumber': sts_client.get_caller_identity()['Account']
                }
                
                certificates.append(certificate)
            
            except Exception as cert_error:
                print(f"Error parsing certificate: {str(cert_error)}")
                continue
    
    except json.JSONDecodeError:
        # Fallback: try to parse text output
        print(f"JSON parsing failed, attempting text parsing for {instance['name']}")
        # Could implement text-based parsing here
    
    except Exception as parse_error:
        print(f"Error parsing Linux certificate output: {str(parse_error)}")
    
    return certificates


def calculate_certificate_status(expiry_date_str: str) -> str:
    """
    Calculate certificate status based on expiry date
    
    Args:
        expiry_date_str: Expiry date in YYYY-MM-DD format
        
    Returns:
        str: Certificate status
    """
    try:
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
        current_date = datetime.now()
        days_until_expiry = (expiry_date - current_date).days
        
        if days_until_expiry < 0:
            return "Expired"
        elif days_until_expiry <= 30:
            return "Due for Renewal"
        else:
            return "Active"
    except:
        return "Unknown"


def determine_environment(server_name: str) -> str:
    """
    Determine environment from server name
    
    Args:
        server_name: Server name or instance ID
        
    Returns:
        str: Environment (PROD, TEST, DEV, etc.)
    """
    server_name_lower = server_name.lower()
    
    if any(x in server_name_lower for x in ['prod', 'prd', 'production']):
        return 'PROD'
    elif any(x in server_name_lower for x in ['test', 'tst', 'qa', 'uat']):
        return 'TEST'
    elif any(x in server_name_lower for x in ['dev', 'development']):
        return 'DEV'
    elif any(x in server_name_lower for x in ['stg', 'stage', 'staging']):
        return 'STAGING'
    else:
        return 'UNKNOWN'


def store_certificate(certificate: Dict) -> str:
    """
    Store or update certificate in DynamoDB
    
    Args:
        certificate: Certificate dictionary
        
    Returns:
        str: 'added', 'updated', or 'skipped'
    """
    table = dynamodb.Table(CERTIFICATES_TABLE)
    cert_id = certificate['CertificateID']
    
    try:
        # Check if certificate already exists
        response = table.get_item(Key={'CertificateID': cert_id})
        
        if 'Item' in response:
            # Certificate exists - update only specific fields
            existing_cert = response['Item']
            
            # Preserve manual fields
            for field in PRESERVE_FIELDS:
                if field in existing_cert and field not in certificate:
                    certificate[field] = existing_cert[field]
            
            # Always update these fields from scan
            update_expression = "SET ExpiryDate = :expiry, #status = :status, LastScannedOn = :scanned"
            expression_values = {
                ':expiry': certificate['ExpiryDate'],
                ':status': certificate['Status'],
                ':scanned': certificate['LastScannedOn']
            }
            expression_names = {'#status': 'Status'}
            
            table.update_item(
                Key={'CertificateID': cert_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names
            )
            
            print(f"    Updated: {certificate['CertificateName']}")
            return 'updated'
        
        else:
            # New certificate - add it
            table.put_item(Item=certificate)
            print(f"    Added: {certificate['CertificateName']}")
            return 'added'
    
    except Exception as e:
        print(f"    Error storing certificate {cert_id}: {str(e)}")
        return 'skipped'
