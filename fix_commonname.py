#!/usr/bin/env python3
"""
Fix Script: Update CommonName Field
Copies CertificateName → CommonName for all certificates
"""

import boto3
from datetime import datetime

def main():
    print("=" * 70)
    print("🔧 FIX SCRIPT: Update CommonName Field")
    print("=" * 70)
    print()
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('cert-management-dev-certificates')
    
    print("📡 Scanning certificates...")
    response = table.scan()
    certificates = response['Items']
    
    print(f"✅ Found {len(certificates)} certificates\n")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    print("🔍 Updating CommonName field...\n")
    
    for cert in certificates:
        cert_id = cert['CertificateID']
        cert_name = cert.get('CertificateName', '')
        current_common_name = cert.get('CommonName', '')
        
        if not cert_name:
            print(f"⚠️  {cert_id}: No CertificateName to copy")
            skipped_count += 1
            continue
        
        if current_common_name == cert_name:
            # Already correct
            skipped_count += 1
            continue
        
        print(f"🔄 {cert_id}:")
        print(f"   CertificateName: {cert_name}")
        print(f"   Current CommonName: '{current_common_name}'")
        print(f"   New CommonName: '{cert_name}'")
        
        try:
            table.update_item(
                Key={'CertificateID': cert_id},
                UpdateExpression='SET CommonName = :name, LastUpdatedOn = :updated',
                ExpressionAttributeValues={
                    ':name': cert_name,
                    ':updated': datetime.now().isoformat() + 'Z'
                }
            )
            print(f"   ✅ Updated successfully\n")
            updated_count += 1
        except Exception as e:
            print(f"   ❌ Error updating: {e}\n")
            error_count += 1
    
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total Certificates: {len(certificates)}")
    print(f"Updated: {updated_count}")
    print(f"Skipped (already correct or no data): {skipped_count}")
    print(f"Errors: {error_count}")
    print()
    
    if updated_count > 0:
        print(f"✅ Successfully updated {updated_count} certificate(s)")
        print("✅ CommonName field now populated")
        print("✅ Search by certificate name will now work!")
    else:
        print("✅ All certificates already have correct CommonName")
    print()

if __name__ == '__main__':
    main()
