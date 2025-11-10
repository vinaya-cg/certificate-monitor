# Test ServiceNow Webhook Integration
# This script tests the webhook endpoint that receives assignment updates from ServiceNow

$ErrorActionPreference = "Stop"

# Configuration
$WEBHOOK_URL = "YOUR_WEBHOOK_URL_HERE"  # Get this from Terraform output: servicenow_webhook_url
$CERTIFICATE_ID = "cert-test-12345"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ServiceNow Webhook Integration Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Incident Assigned (New → In Progress)
Write-Host "[Test 1] Simulating incident assignment..." -ForegroundColor Yellow
$payload1 = @{
    incident_number = "INC0999001"
    sys_id = "test123"
    state = "2"  # In Progress
    assigned_to = @{
        name = "Sarah Johnson"
        email = "sarah.johnson@sogeti.com"
        sys_id = "user123"
    }
    correlation_id = $CERTIFICATE_ID
    short_description = "Certificate expiring in 7 days - test.example.com"
    priority = "2"
    updated_on = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
} | ConvertTo-Json

try {
    $response1 = Invoke-RestMethod `
        -Uri $WEBHOOK_URL `
        -Method POST `
        -Body $payload1 `
        -ContentType "application/json"
    
    Write-Host "✅ Test 1 PASSED" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    Write-Host ($response1 | ConvertTo-Json -Depth 10) -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Test 1 FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 2

# Test 2: Incident On Hold
Write-Host "[Test 2] Simulating incident on hold..." -ForegroundColor Yellow
$payload2 = @{
    incident_number = "INC0999001"
    sys_id = "test123"
    state = "3"  # On Hold
    assigned_to = @{
        name = "Sarah Johnson"
        email = "sarah.johnson@sogeti.com"
        sys_id = "user123"
    }
    correlation_id = $CERTIFICATE_ID
    short_description = "Certificate expiring in 7 days - test.example.com"
    priority = "2"
    updated_on = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
} | ConvertTo-Json

try {
    $response2 = Invoke-RestMethod `
        -Uri $WEBHOOK_URL `
        -Method POST `
        -Body $payload2 `
        -ContentType "application/json"
    
    Write-Host "✅ Test 2 PASSED" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    Write-Host ($response2 | ConvertTo-Json -Depth 10) -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Test 2 FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 2

# Test 3: Incident Resolved
Write-Host "[Test 3] Simulating incident resolution..." -ForegroundColor Yellow
$payload3 = @{
    incident_number = "INC0999001"
    sys_id = "test123"
    state = "6"  # Resolved
    assigned_to = @{
        name = "Sarah Johnson"
        email = "sarah.johnson@sogeti.com"
        sys_id = "user123"
    }
    correlation_id = $CERTIFICATE_ID
    short_description = "Certificate expiring in 7 days - test.example.com"
    priority = "2"
    updated_on = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
} | ConvertTo-Json

try {
    $response3 = Invoke-RestMethod `
        -Uri $WEBHOOK_URL `
        -Method POST `
        -Body $payload3 `
        -ContentType "application/json"
    
    Write-Host "✅ Test 3 PASSED" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    Write-Host ($response3 | ConvertTo-Json -Depth 10) -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Test 3 FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 2

# Test 4: Reassignment to another engineer
Write-Host "[Test 4] Simulating reassignment..." -ForegroundColor Yellow
$payload4 = @{
    incident_number = "INC0999001"
    sys_id = "test123"
    state = "2"  # In Progress
    assigned_to = @{
        name = "Michael Chen"
        email = "michael.chen@sogeti.com"
        sys_id = "user456"
    }
    correlation_id = $CERTIFICATE_ID
    short_description = "Certificate expiring in 7 days - test.example.com"
    priority = "2"
    updated_on = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
} | ConvertTo-Json

try {
    $response4 = Invoke-RestMethod `
        -Uri $WEBHOOK_URL `
        -Method POST `
        -Body $payload4 `
        -ContentType "application/json"
    
    Write-Host "✅ Test 4 PASSED" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    Write-Host ($response4 | ConvertTo-Json -Depth 10) -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Test 4 FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Check DynamoDB certificate record for: $CERTIFICATE_ID" -ForegroundColor White
Write-Host "2. Verify AssignedTo field shows: Michael Chen" -ForegroundColor White
Write-Host "3. Verify Status field shows: Renewal in Progress" -ForegroundColor White
Write-Host "4. Check certificate-logs table for action entries" -ForegroundColor White
Write-Host "5. View CloudWatch logs: /aws/lambda/cert-management-servicenow-webhook-handler" -ForegroundColor White
Write-Host ""

# Provide DynamoDB query command
Write-Host "DynamoDB Query Command:" -ForegroundColor Cyan
Write-Host "aws dynamodb get-item --table-name cert-management-dev-secure-certificates --key '{\"CertificateID\":{\"S\":\"$CERTIFICATE_ID\"}}' --region eu-west-1" -ForegroundColor Gray
