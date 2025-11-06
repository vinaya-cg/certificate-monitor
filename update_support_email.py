import boto3

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('cert-management-dev-certificates')

print("Updating support email for all certificates...")

# Scan all certificates
response = table.scan()
items = response['Items']

# Handle pagination
while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    items.extend(response['Items'])

print(f"Found {len(items)} certificates to update")

# Update each certificate
updated_count = 0
with table.batch_writer() as batch:
    for item in items:
        item['SupportEmail'] = 'vinaya-c.nayanegali@capgemini.com'
        batch.put_item(Item=item)
        updated_count += 1
        
        if updated_count % 10 == 0:
            print(f"Updated {updated_count} certificates...")

print(f"\n✅ Successfully updated {updated_count} certificates!")
print(f"Support Email: vinaya-c.nayanegali@capgemini.com")
