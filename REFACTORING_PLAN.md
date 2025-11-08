# 🧹 Code Refactoring Plan - Certificate Monitor

## Current Issues Identified

### 🗑️ Files to Remove (Duplicates/Temporary/Test Files)

#### Root Directory
- `dashboard.js.backup` - Backup file, not needed
- `README.old.md` - Old readme, not needed
- `response.json` - Test response file
- `test-response.json` - Test response file
- `dashboard_api.zip` - Build artifact (can regenerate)
- `lambda_function.zip` - Build artifact (can regenerate)
- `dummy_certificates_100.xlsx` - Test data (move to test-data/)
- `images.png` - Unused image
- `postNl.jfif` - Duplicate (we have PostNl.png)
- `index-from-s3.html` - Old test file
- `test-add-certificate.html` - Test file (move to tests/)
- `test-status-logic.html` - Test file (move to tests/)

#### Dashboard Directory (13 test files!)
- `browser-test.html`
- `cors-diagnostic.html`
- `debug-dashboard.html`
- `direct-test.html`
- `inline-test.html`
- `minimal-test.html`
- `simple-api-test.html`
- `simple-test.html`
- `step-by-step-test.html`
- `test-api-simple.html`
- `test-dashboard-functionality.html`
- `test-fixed-dashboard.html`
- `ultimate-debug.html`
- `dashboard.js.backup`
- `dashboard-from-s3.js` (if not used)
- `response.json` - Duplicate

**Keep in dashboard/:**
- `complete-test-suite.html` - Most comprehensive test suite

#### Scripts to Organize
- `fix_all_tests.py` - One-time fix script (archive)
- `fix_commonname.py` - One-time fix script (archive)
- `fix_expired_status.py` - One-time fix script (archive)
- `fix_owner.py` - One-time fix script (archive)
- `update_owner.py` - One-time utility (archive)
- `update_support_email.py` - One-time utility (archive)
- `create_dummy_certs.py` - Utility script (move to scripts/)
- `upload_dummy_certs.py` - Utility script (move to scripts/)

---

## 🏗️ Proposed Professional Structure

```
cert-dashboard/
├── 📁 src/                          # Source code (production)
│   ├── 📁 lambda/                   # Lambda functions
│   │   ├── certificate_monitor.py
│   │   ├── dashboard_api.py
│   │   ├── excel_processor.py
│   │   └── __init__.py
│   ├── 📁 utils/                    # Shared utilities
│   │   ├── __init__.py
│   │   ├── aws_helpers.py          # DynamoDB, S3, SES helpers
│   │   ├── certificate_helpers.py  # Certificate logic
│   │   └── config.py               # Configuration management
│   └── 📁 scripts/                  # Operational scripts
│       ├── import_certificates.py
│       ├── create_dummy_certs.py
│       ├── upload_dummy_certs.py
│       └── README.md
│
├── 📁 dashboard/                    # Frontend (production)
│   ├── 📁 css/
│   │   └── styles.css              # Extracted styles
│   ├── 📁 js/
│   │   ├── dashboard.js            # Main dashboard logic
│   │   ├── auth.js                 # Authentication
│   │   └── config.js               # Frontend config
│   ├── 📁 images/
│   │   ├── postnl-logo.png
│   │   └── sogeti-logo.png
│   ├── index.html
│   ├── login.html
│   └── error.html
│
├── 📁 tests/                        # All test files
│   ├── 📁 python/
│   │   ├── test_environment.py
│   │   ├── test_aws_connection.py
│   │   └── test_lambda_functions.py
│   ├── 📁 frontend/
│   │   └── complete-test-suite.html
│   └── 📁 test-data/
│       └── dummy_certificates_100.xlsx
│
├── 📁 docs/                         # Documentation
│   ├── README.md                    # Main documentation
│   ├── DEPLOYMENT_GUIDE.md
│   ├── PYTHON_ENVIRONMENT_SETUP.md
│   ├── QUICK_REFERENCE.md
│   ├── ADD_CERTIFICATE_FEATURE.md
│   ├── IMPORT_README.md
│   └── 📁 reports/
│       ├── COMPLETE_FUNCTIONALITY_TEST_REPORT.md
│       ├── TEST_RESULTS.md
│       ├── TEST_FAILURES.md
│       └── TEST_FIXES_REPORT.md
│
├── 📁 terraform/                    # Infrastructure as Code
│   ├── main.tf
│   ├── dashboard_api.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars
│
├── 📁 config/                       # Configuration files
│   ├── s3-cors.json
│   └── lambda-policy.json
│
├── 📁 archive/                      # Old/one-time scripts
│   ├── fix_all_tests.py
│   ├── fix_commonname.py
│   ├── fix_expired_status.py
│   ├── fix_owner.py
│   ├── update_owner.py
│   └── update_support_email.py
│
├── 📁 build/                        # Build artifacts (gitignored)
│   ├── dashboard_api.zip
│   └── lambda_function.zip
│
├── .gitignore
├── requirements.txt
├── certificate-monitor.code-workspace
└── WORKSPACE_SETUP.md
```

---

## 🎯 Modularization Strategy

### 1. Extract Common Utilities

#### `src/utils/aws_helpers.py`
```python
"""AWS service helper functions"""
- get_dynamodb_client()
- get_dynamodb_table()
- scan_table_with_pagination()
- put_item_with_retry()
- send_email_via_ses()
- upload_to_s3()
```

#### `src/utils/certificate_helpers.py`
```python
"""Certificate business logic"""
- calculate_days_until_expiry()
- determine_certificate_status()
- validate_certificate_data()
- format_certificate_for_display()
```

#### `src/utils/config.py`
```python
"""Configuration management"""
- get_table_names()
- get_email_config()
- get_region()
- validate_environment()
```

### 2. Refactor Lambda Functions

Make them thin wrappers that use shared utilities:

```python
# src/lambda/dashboard_api.py
from utils.aws_helpers import get_dynamodb_table, scan_table_with_pagination
from utils.certificate_helpers import calculate_days_until_expiry

def lambda_handler(event, context):
    # Thin orchestration layer
    table = get_dynamodb_table()
    items = scan_table_with_pagination(table)
    # ... process using shared utilities
```

### 3. Frontend Modularization

#### Extract CSS to separate file
- Move inline styles from HTML to `dashboard/css/styles.css`

#### Split JavaScript
- `dashboard.js` - Main logic
- `auth.js` - Authentication (already done)
- `config.js` - API endpoints, constants

---

## 📋 Implementation Steps

### Phase 1: Safety First (Backup & Test)
1. ✅ Create this plan
2. Run all tests to confirm current state works
3. Create git branch for refactoring
4. Document current working state

### Phase 2: Remove Clutter
1. Delete test files in dashboard/ (keep complete-test-suite.html)
2. Delete backup files (.backup, .old)
3. Delete temporary response.json files
4. Delete duplicate images
5. Move build artifacts to build/ folder

### Phase 3: Create New Structure
1. Create new folders (src/, docs/, tests/, config/, archive/)
2. Move files to appropriate locations
3. Update import paths in Python files
4. Update relative paths in HTML/JS files

### Phase 4: Modularize Code
1. Extract AWS helpers to utils/aws_helpers.py
2. Extract certificate logic to utils/certificate_helpers.py
3. Create config.py for configuration management
4. Refactor lambda functions to use utilities
5. Extract frontend CSS to separate file

### Phase 5: Update Configuration
1. Update .gitignore for new structure
2. Update workspace file paths
3. Update Terraform for new lambda paths
4. Update documentation for new structure

### Phase 6: Test Everything
1. Run Python tests
2. Test lambda functions locally
3. Test dashboard functionality
4. Deploy and verify in AWS
5. Run complete-test-suite.html

---

## 🚨 Risk Mitigation

### What NOT to Touch (Core Working Logic)
- ✅ Certificate status calculation logic in dashboard.js
- ✅ DynamoDB query logic
- ✅ CORS configuration (it's working!)
- ✅ Authentication flow
- ✅ Terraform infrastructure code

### Safe Changes
- ✅ Moving files to new folders
- ✅ Extracting utilities (with proper imports)
- ✅ Deleting test/backup files
- ✅ Organizing documentation

### Testing After Each Phase
- Run: `python tests/python/test_environment.py`
- Run: `python tests/python/test_aws_connection.py`
- Open: Dashboard and verify it loads
- Check: Can add/edit/view certificates

---

## 📊 Expected Benefits

### Code Quality
- ✅ Single Responsibility Principle (SRP)
- ✅ Don't Repeat Yourself (DRY)
- ✅ Easier to test individual components
- ✅ Better code reusability

### Developer Experience
- ✅ Clear folder structure
- ✅ Easy to find files
- ✅ Reduced clutter (40+ files → ~25 organized files)
- ✅ Professional appearance

### Maintenance
- ✅ Easier to add new features
- ✅ Easier to fix bugs
- ✅ Better separation of concerns
- ✅ Clearer documentation

---

## 🎯 Success Criteria

- [ ] All tests passing (test_environment.py, test_aws_connection.py)
- [ ] Dashboard loads and displays certificates
- [ ] Can add new certificate via dashboard
- [ ] Can edit existing certificate
- [ ] Authentication still works
- [ ] API returns data correctly
- [ ] No broken imports or paths
- [ ] Build artifacts can be regenerated
- [ ] Documentation updated

---

**Ready to proceed?**
1. Review this plan
2. Confirm approach
3. Execute phase by phase
4. Test after each phase
