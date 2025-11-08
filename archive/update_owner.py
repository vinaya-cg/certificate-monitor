import boto3
from boto3.dynamodb.conditions import Attr

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('cert-management-dev-certificates')

print("Updating all certificates with new owner email...")

# Scan all certificates
response = table.scan()
items = response['Items']

# Handle pagination if there are more items
while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    items.extend(response['Items'])

print(f"Found {len(items)} certificates to update")

# Update each certificate
updated_count = 0
with table.batch_writer() as batch:
    for item in items:
        item['Owner'] = 'vinaya-c.nayanegali@capgemini.com'
        item['SupportTeam'] = 'Support Team'
        batch.put_item(Item=item)
        updated_count += 1
        
        if updated_count % 10 == 0:
            print(f"Updated {updated_count} certificates...")

print(f"\n✅ Successfully updated {updated_count} certificates!")
print(f"Owner: vinaya-c.nayanegali@capgemini.com")
print(f"Support Team: Support Team")
