#!/usr/bin/env python3
"""
Fix Script: Update Owner Field
Copies OwnerEmail → Owner for all certificates
Option to extract name from email or use email directly
"""

import boto3
from datetime import datetime

def extract_name_from_email(email):
    """
    Extract a readable name from email address
    Example: Vinaya-c.nayanegali@capgemini.com → Vinaya C Nayanegali
    """
    if not email or '@' not in email:
        return 'Unknown'
    
    # Get the part before @
    name_part = email.split('@')[0]
    
    # Replace separators with spaces
    name_part = name_part.replace('.', ' ').replace('-', ' ').replace('_', ' ')
    
    # Title case each word
    name = ' '.join(word.capitalize() for word in name_part.split())
    
    return name

def main():
    print("=" * 70)
    print("🔧 FIX SCRIPT: Update Owner Field")
    print("=" * 70)
    print()
    
    # Ask user for preference
    print("Choose Owner format:")
    print("1. Extract name from email (e.g., 'Vinaya C Nayanegali')")
    print("2. Use full email (e.g., 'Vinaya-c.nayanegali@capgemini.com')")
    choice = input("\nEnter choice (1 or 2, default=1): ").strip() or '1'
    use_extracted_name = (choice == '1')
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
    
    print("🔍 Updating Owner field...\n")
    
    for cert in certificates:
        cert_id = cert['CertificateID']
        owner_email = cert.get('OwnerEmail', '')
        current_owner = cert.get('Owner', '')
        
        if not owner_email:
            print(f"⚠️  {cert_id}: No OwnerEmail to copy")
            skipped_count += 1
            continue
        
        # Determine new owner value
        if use_extracted_name:
            new_owner = extract_name_from_email(owner_email)
        else:
            new_owner = owner_email
        
        if current_owner == new_owner:
            # Already correct
            skipped_count += 1
            continue
        
        print(f"🔄 {cert_id}:")
        print(f"   Certificate: {cert.get('CertificateName', 'N/A')}")
        print(f"   OwnerEmail: {owner_email}")
        print(f"   Current Owner: '{current_owner}'")
        print(f"   New Owner: '{new_owner}'")
        
        try:
            table.update_item(
                Key={'CertificateID': cert_id},
                UpdateExpression='SET #owner = :owner, LastUpdatedOn = :updated',
                ExpressionAttributeNames={'#owner': 'Owner'},
                ExpressionAttributeValues={
                    ':owner': new_owner,
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
        print("✅ Owner field now populated")
        print("✅ Filter by owner will now work!")
    else:
        print("✅ All certificates already have correct Owner")
    print()

if __name__ == '__main__':
    main()
