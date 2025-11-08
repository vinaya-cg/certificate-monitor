#!/usr/bin/env python3
"""
Fix Script: Update Expired Certificate Status
Corrects the 6 certificates that have past expiry dates but wrong status
"""

import boto3
from datetime import datetime
from decimal import Decimal

def main():
    print("=" * 70)
    print("🔧 FIX SCRIPT: Update Expired Certificate Status")
    print("=" * 70)
    print()
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('cert-management-dev-certificates')
    
    print("📡 Scanning certificates...")
    response = table.scan()
    certificates = response['Items']
    
    print(f"✅ Found {len(certificates)} certificates\n")
    
    today = datetime.now()
    updated_count = 0
    expired_count = 0
    expiring_count = 0
    renewal_count = 0
    active_count = 0
    
    print("🔍 Checking expiry status...\n")
    
    for cert in certificates:
        cert_id = cert['CertificateID']
        expiry_str = cert.get('ExpiryDate')
        current_status = cert.get('Status', 'Unknown')
        
        if not expiry_str:
            print(f"⚠️  {cert_id}: No expiry date")
            continue
        
        # Parse expiry date
        try:
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
        except ValueError:
            print(f"⚠️  {cert_id}: Invalid date format: {expiry_str}")
            continue
        
        # Calculate days until expiry
        days_until_expiry = (expiry_date - today).days
        
        # Determine correct status
        if days_until_expiry < 0:
            new_status = 'Expired'
            expired_count += 1
        elif days_until_expiry <= 30:
            new_status = 'Expiring Soon'
            expiring_count += 1
        elif days_until_expiry <= 90:
            new_status = 'Due for Renewal'
            renewal_count += 1
        else:
            new_status = 'Active'
            active_count += 1
        
        # Update if status is different
        if current_status != new_status:
            print(f"🔄 {cert_id}:")
            print(f"   Certificate: {cert.get('CertificateName', 'N/A')}")
            print(f"   Expiry Date: {expiry_str}")
            print(f"   Days Until Expiry: {days_until_expiry}")
            print(f"   Current Status: {current_status}")
            print(f"   New Status: {new_status}")
            
            try:
                table.update_item(
                    Key={'CertificateID': cert_id},
                    UpdateExpression='SET #status = :status, DaysUntilExpiry = :days, LastUpdatedOn = :updated',
                    ExpressionAttributeNames={'#status': 'Status'},
                    ExpressionAttributeValues={
                        ':status': new_status,
                        ':days': Decimal(str(days_until_expiry)),
                        ':updated': datetime.now().isoformat() + 'Z'
                    }
                )
                print(f"   ✅ Updated successfully\n")
                updated_count += 1
            except Exception as e:
                print(f"   ❌ Error updating: {e}\n")
    
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total Certificates: {len(certificates)}")
    print(f"Updated: {updated_count}")
    print()
    print("New Status Distribution:")
    print(f"  ✅ Active: {active_count}")
    print(f"  🔄 Due for Renewal: {renewal_count}")
    print(f"  ⚠️  Expiring Soon: {expiring_count}")
    print(f"  ❌ Expired: {expired_count}")
    print()
    
    if updated_count > 0:
        print(f"✅ Successfully updated {updated_count} certificate(s)")
    else:
        print("✅ All certificates already have correct status")
    print()

if __name__ == '__main__':
    main()
