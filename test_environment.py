#!/usr/bin/env python3
"""
Test script to verify Python environment configuration
"""

import sys
import platform

def test_python_version():
    """Check Python version"""
    print(f"✅ Python Version: {sys.version}")
    print(f"✅ Python Executable: {sys.executable}")
    print(f"✅ Platform: {platform.platform()}")

def test_boto3():
    """Test boto3 import"""
    try:
        import boto3
        print(f"✅ boto3 installed: {boto3.__version__}")
        
        # Test AWS connection (optional)
        try:
            session = boto3.Session()
            region = session.region_name or 'eu-west-1'
            print(f"✅ AWS Session created (Region: {region})")
        except Exception as e:
            print(f"⚠️  AWS credentials not configured: {e}")
        
        return True
    except ImportError as e:
        print(f"❌ boto3 NOT installed: {e}")
        return False

def test_openpyxl():
    """Test openpyxl import"""
    try:
        import openpyxl
        print(f"✅ openpyxl installed: {openpyxl.__version__}")
        return True
    except ImportError as e:
        print(f"❌ openpyxl NOT installed: {e}")
        return False

def test_excel_read():
    """Test Excel reading capability"""
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws['A1'] = "Test"
        print(f"✅ openpyxl can create workbooks")
        return True
    except Exception as e:
        print(f"❌ openpyxl test failed: {e}")
        return False

def test_dynamodb_client():
    """Test DynamoDB client creation"""
    try:
        import boto3
        dynamodb = boto3.client('dynamodb', region_name='eu-west-1')
        print(f"✅ DynamoDB client created successfully")
        return True
    except Exception as e:
        print(f"❌ DynamoDB client failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🐍 PYTHON ENVIRONMENT TEST")
    print("=" * 60)
    print()
    
    test_python_version()
    print()
    
    results = []
    results.append(("boto3", test_boto3()))
    print()
    results.append(("openpyxl", test_openpyxl()))
    print()
    results.append(("Excel Operations", test_excel_read()))
    print()
    results.append(("DynamoDB Client", test_dynamodb_client()))
    print()
    
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✅ Environment configured correctly!")
        sys.exit(0)
    else:
        print("❌ Some tests failed - check installation")
        sys.exit(1)
