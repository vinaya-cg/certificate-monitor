# ❌ Test Failure Analysis - Dashboard Functionality

**Date:** October 29, 2025  
**Total Tests:** 9  
**Passed:** 6 ✅  
**Failed:** 3 ❌  

---

## 🔴 FAILED TESTS

### ❌ TEST FAILURE #1: CommonName Field Empty

**Issue:** All 191 certificates have empty `CommonName` field

**Details:**
- **Expected:** CommonName should contain certificate CN (e.g., "adfs-aws2.p02.cldsvc.net")
- **Actual:** CommonName field is empty/null on all 191 certificates
- **Impact:** 
  - Search by CommonName doesn't work
  - Dashboard table shows empty values in CommonName column
  - User cannot identify certificates by their CN

**Root Cause:**
The Excel import script (`import_certificates.py`) has a column mapping that includes:
```python
'Common Name': 'CommonName'
```

However, the actual Excel file has a column called **"CertificateName"** (not "Common Name"), which contains the certificate name data.

**Current Data:**
```
✅ CertificateName: "adfs-aws2.p02.cldsvc.net" (populated)
❌ CommonName: "" (empty)
```

**Fix Required:**
Update the import script to map `CertificateName` → `CommonName`

---

### ❌ TEST FAILURE #2: Owner Field Empty

**Issue:** All 191 certificates have empty `Owner` field

**Details:**
- **Expected:** Owner should contain certificate owner/responsible person
- **Actual:** Owner field is empty/null on all 191 certificates
- **Impact:**
  - Cannot filter certificates by owner
  - Cannot assign responsibility
  - Compliance tracking not possible

**Root Cause:**
The Excel file doesn't have an "Owner" column. Available fields are:
- ✅ `OwnerEmail` (populated - e.g., "Vinaya-c.nayanegali@capgemini.com")
- ❌ `Owner` (doesn't exist in source data)

**Current Data:**
```
✅ OwnerEmail: "Vinaya-c.nayanegali@capgemini.com" (populated)
❌ Owner: "" (empty)
```

**Fix Required:**
Map `OwnerEmail` → `Owner` field, or extract owner name from email

---

### ❌ TEST FAILURE #3: Status Logic Incorrect (Expired Certificates)

**Issue:** 6 certificates have past expiry dates but status is NOT "Expired"

**Details:**
- **Expected:** Certificates with `ExpiryDate < Today` should have `Status = "Expired"`
- **Actual:** 
  - 6 certificates have expired dates
  - 0 certificates have status "Expired"
  - They are marked as "Active" or "Due for Renewal" instead
- **Impact:**
  - Expired certificates shown as active
  - Misleading dashboard statistics
  - Security risk (expired certs not flagged)

**Current Statistics:**
```
Total Certificates: 191
├─ Active: 178 (includes 6 expired! ❌)
├─ Due for Renewal: 13
├─ Expired: 0 (should be 6! ❌)
└─ Expiring Soon: 0

Actual Expiry Status:
├─ Future expiry dates: 185 ✅
└─ Past expiry dates: 6 ❌ (incorrectly marked)
```

**Root Cause:**
The import script calculates `DaysUntilExpiry` but the status logic in `import_certificates.py` is:

```python
days_until_expiry = (expiry_date - datetime.now()).days

# Status logic
if days_until_expiry < 0:
    status = 'Expired'  # ✅ Correct logic
elif days_until_expiry <= 30:
    status = 'Expiring Soon'
elif days_until_expiry <= 90:
    status = 'Due for Renewal'
else:
    status = 'Active'
```

**The logic LOOKS correct**, so the issue is likely:
1. **Date parsing error** - expiry dates not parsed correctly
2. **Timezone issue** - dates compared in wrong timezone
3. **Data import issue** - status calculated during import but changed later

**Fix Required:**
Re-run import with corrected status calculation or update existing records

---

## 📊 Detailed Test Results

| Test # | Test Name | Status | Details |
|--------|-----------|--------|---------|
| 1 | API Connectivity | ✅ PASSED | 191 certificates loaded |
| 2 | Data Integrity | ✅ PASSED | All required fields present |
| 3 | **CommonName Population** | ❌ FAILED | 0/191 have CommonName |
| 4 | **Owner Population** | ❌ FAILED | 0/191 have Owner |
| 5 | **Expired Status Logic** | ❌ FAILED | 6 expired marked as Active |
| 6 | Environment Distribution | ✅ PASSED | PRD/ACC/TST/DEV working |
| 7 | Search Functionality | ✅ PASSED | Logic works (no data to search) |
| 8 | CORS Configuration | ✅ PASSED | No duplicate headers |
| 9 | Performance | ✅ PASSED | < 1s response time |

---

## 🔧 FIXES REQUIRED

### Fix #1: Update CommonName Mapping

**File:** `import_certificates.py`

**Change:**
```python
# BEFORE
column_mapping = {
    'Common Name': 'CommonName',  # ❌ Column doesn't exist
    ...
}

# AFTER
column_mapping = {
    'CertificateName': 'CommonName',  # ✅ Use actual column name
    ...
}
```

### Fix #2: Add Owner Field Mapping

**File:** `import_certificates.py`

**Option A - Use OwnerEmail as Owner:**
```python
column_mapping = {
    'OwnerEmail': 'Owner',  # Simple: use email as owner
    ...
}
```

**Option B - Extract Name from Email:**
```python
# Extract name from email (e.g., "Vinaya-c.nayanegali@capgemini.com" → "Vinaya Nayanegali")
owner_email = row.get('OwnerEmail', '')
if owner_email:
    owner_name = owner_email.split('@')[0].replace('-', ' ').replace('.', ' ').title()
    certificate['Owner'] = owner_name
else:
    certificate['Owner'] = 'Unknown'
```

### Fix #3: Correct Expired Status

**File:** `import_certificates.py`

**Debug the status calculation:**
```python
# Add logging to see what's happening
expiry_date = datetime.strptime(row['Expiry Date'], '%Y-%m-%d')
today = datetime.now()
days_until_expiry = (expiry_date - today).days

print(f"Certificate: {row['CertificateName']}")
print(f"  Expiry Date: {expiry_date}")
print(f"  Today: {today}")
print(f"  Days Until Expiry: {days_until_expiry}")

if days_until_expiry < 0:
    status = 'Expired'
    print(f"  Status: EXPIRED (past date)")
else:
    # ... other logic
```

**Or update existing records in DynamoDB:**
```python
# Create update script: update_expired_status.py
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('cert-management-dev-certificates')

# Scan all certificates
response = table.scan()
certificates = response['Items']

today = datetime.now()
updated = 0

for cert in certificates:
    expiry_str = cert.get('ExpiryDate')
    if expiry_str:
        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
        days = (expiry_date - today).days
        
        # Recalculate correct status
        if days < 0:
            new_status = 'Expired'
        elif days <= 30:
            new_status = 'Expiring Soon'
        elif days <= 90:
            new_status = 'Due for Renewal'
        else:
            new_status = 'Active'
        
        # Update if different
        if cert.get('Status') != new_status:
            table.update_item(
                Key={'CertificateID': cert['CertificateID']},
                UpdateExpression='SET #status = :status, DaysUntilExpiry = :days',
                ExpressionAttributeNames={'#status': 'Status'},
                ExpressionAttributeValues={
                    ':status': new_status,
                    ':days': days
                }
            )
            print(f"Updated {cert['CertificateID']}: {cert.get('Status')} → {new_status}")
            updated += 1

print(f"\nTotal updated: {updated}")
```

---

## 🎯 RECOMMENDED ACTION PLAN

### Immediate Fixes (Required):

1. **Fix #1 - CommonName** ⚡ HIGH PRIORITY
   - Update `import_certificates.py` column mapping
   - Re-import Excel file
   - **Impact:** Dashboard will show certificate names
   - **Time:** 5 minutes

2. **Fix #2 - Owner** ⚡ HIGH PRIORITY
   - Add Owner field mapping in import script
   - Re-import Excel file
   - **Impact:** Owner filtering will work
   - **Time:** 5 minutes

3. **Fix #3 - Expired Status** 🔥 CRITICAL
   - Create `update_expired_status.py` script
   - Run once to fix existing 6 records
   - **Impact:** Correct expired certificate detection
   - **Time:** 10 minutes

### After Fixes - Re-run Tests:

```bash
# Re-import with corrected mappings
python import_certificates.py

# Or just fix the 6 expired certificates
python update_expired_status.py

# Verify in dashboard
# All tests should pass ✅
```

---

## 📋 CURRENT DATA SAMPLE

**What we HAVE (working):**
```json
{
  "CertificateID": "cert-b77e9fd4",
  "CertificateName": "adfs-aws2.p02.cldsvc.net",  ✅ Populated
  "OwnerEmail": "Vinaya-c.nayanegali@capgemini.com",  ✅ Populated
  "ExpiryDate": "2026-08-05",  ✅ Populated
  "Status": "Active",  ✅ Populated (but wrong for 6 certs)
  "Environment": "PRD",  ✅ Populated
  "Application": "ADFS+WAP",  ✅ Populated
  "SerialNumber": "123",  ✅ Populated
  "Type": "DigiCert G2 TLS EU RSA4096 SHA384 2022 CA1"  ✅ Populated
}
```

**What we're MISSING:**
```json
{
  "CommonName": "",  ❌ Empty (should be "adfs-aws2.p02.cldsvc.net")
  "Owner": "",  ❌ Empty (should be extracted from OwnerEmail)
  "Status": "Active"  ❌ Wrong for 6 expired certificates
}
```

---

## ✅ AFTER FIX - EXPECTED RESULTS

All 9 tests will pass:
- ✅ CommonName populated: 191/191
- ✅ Owner populated: 191/191  
- ✅ Status correct: 6 expired, 0 incorrectly marked
- ✅ Search by name working
- ✅ Filter by owner working
- ✅ Accurate statistics

---

## 🚀 NEXT STEPS

**Choose one:**

**Option A - Quick Fix (Update Existing Data):**
1. Create `update_expired_status.py` to fix 6 expired certificates
2. Create `update_commonname.py` to copy CertificateName → CommonName
3. Create `update_owner.py` to copy OwnerEmail → Owner
4. Run all 3 scripts
5. Refresh dashboard - all tests pass ✅

**Option B - Clean Re-import (Recommended):**
1. Update `import_certificates.py` with correct mappings
2. Delete all DynamoDB records
3. Re-import Excel file
4. All data correct from start ✅

**I recommend Option B** for clean, reliable data.

Would you like me to create the fix scripts?
