#!/usr/bin/env python3
"""
Test Lambda functions locally
"""

import sys
import json
sys.path.insert(0, 'lambda')

def test_dashboard_api():
    """Test the dashboard API Lambda function"""
    print("🧪 Testing Dashboard API Lambda Function...")
    
    try:
        from dashboard_api import lambda_handler
        
        # Simulate Lambda event
        event = {}
        context = {}
        
        # Execute Lambda
        result = lambda_handler(event, context)
        
        print(f"✅ Lambda executed successfully")
        print(f"✅ Status Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print(f"✅ Response format: JSON")
            print(f"✅ Certificate count: {body.get('count', 0)}")
            print(f"✅ Timestamp: {body.get('timestamp', 'N/A')}")
            
            if body.get('certificates'):
                sample = body['certificates'][0]
                print(f"\n📋 Sample Certificate:")
                print(f"   ID: {sample.get('CertificateID', 'N/A')}")
                print(f"   Expiry: {sample.get('ExpiryDate', 'N/A')}")
                print(f"   Status: {sample.get('Status', 'N/A')}")
            
            return True
        else:
            print(f"❌ Unexpected status code: {result['statusCode']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing dashboard_api: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_certificate_monitor():
    """Test the certificate monitor Lambda function"""
    print("\n🧪 Testing Certificate Monitor Lambda Function...")
    
    try:
        from certificate_monitor import lambda_handler
        
        # Simulate Lambda event
        event = {}
        context = {}
        
        # Execute Lambda
        result = lambda_handler(event, context)
        
        print(f"✅ Lambda executed successfully")
        print(f"✅ Status Code: {result['statusCode']}")
        print(f"✅ Message: {result.get('message', 'N/A')}")
        
        if 'certificates_checked' in result:
            print(f"✅ Certificates checked: {result['certificates_checked']}")
        if 'expiring_soon' in result:
            print(f"⚠️  Expiring soon: {result['expiring_soon']}")
        if 'emails_sent' in result:
            print(f"📧 Emails sent: {result['emails_sent']}")
        
        return result['statusCode'] == 200
        
    except Exception as e:
        print(f"❌ Error testing certificate_monitor: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TESTING LAMBDA FUNCTIONS LOCALLY")
    print("=" * 60)
    print()
    
    # Test Dashboard API
    api_test = test_dashboard_api()
    
    # Test Certificate Monitor
    monitor_test = test_certificate_monitor()
    
    print("\n" + "=" * 60)
    if api_test and monitor_test:
        print("✅ ALL LAMBDA FUNCTIONS WORKING!")
        print("=" * 60)
        print("\n🎉 Your Python environment is fully configured and")
        print("   all Lambda functions are working correctly!")
    else:
        print("⚠️  Some Lambda tests had issues")
        print("=" * 60)
