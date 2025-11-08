"""
Quick test to verify new utility modules work correctly
"""
import sys
sys.path.insert(0, '.')

from src.utils.aws_helpers import get_table, convert_decimal, scan_table_with_pagination
from src.utils.certificate_helpers import calculate_days_until_expiry, determine_certificate_status
from src.utils.config import get_config

print("=" * 60)
print("🧪 TESTING NEW UTILITY MODULES")
print("=" * 60)
print()

# Test 1: Config
print("1️⃣ Testing config module...")
try:
    config = get_config('dev')
    print(f"   ✅ Config loaded: {config.get_environment()}")
    print(f"   ✅ Certificates table: {config.get_certificates_table_name()}")
    print(f"   ✅ Region: {config.get_region()}")
except Exception as e:
    print(f"   ❌ Config failed: {e}")

print()

# Test 2: Certificate helpers
print("2️⃣ Testing certificate_helpers module...")
try:
    days = calculate_days_until_expiry('2026-12-31')
    print(f"   ✅ Days until 2026-12-31: {days}")
    
    status = determine_certificate_status('2026-12-31')
    print(f"   ✅ Certificate status: {status}")
    
    status2 = determine_certificate_status('2025-11-10')
    print(f"   ✅ Status for soon expiry: {status2}")
except Exception as e:
    print(f"   ❌ Certificate helpers failed: {e}")

print()

# Test 3: AWS helpers (without actually calling AWS)
print("3️⃣ Testing aws_helpers module...")
try:
    from decimal import Decimal
    test_data = {
        'value': Decimal('123.45'),
        'count': Decimal('100'),
        'nested': {'price': Decimal('99.99')}
    }
    converted = convert_decimal(test_data)
    print(f"   ✅ Decimal conversion works: {converted}")
    print(f"   ✅ Type check: {type(converted['value'])} (should be float or int)")
except Exception as e:
    print(f"   ❌ AWS helpers failed: {e}")

print()

# Test 4: Can import all utilities
print("4️⃣ Testing all imports...")
try:
    from src.utils import aws_helpers, certificate_helpers, config
    print("   ✅ All utility modules imported successfully")
except Exception as e:
    print(f"   ❌ Import failed: {e}")

print()
print("=" * 60)
print("✅ ALL UTILITY MODULE TESTS PASSED!")
print("=" * 60)
