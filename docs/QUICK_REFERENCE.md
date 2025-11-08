# 🚀 Quick Reference - Python Environment

## ✅ Environment Status: FULLY CONFIGURED

### Current Session
- **Status:** Virtual environment ACTIVE
- **Python:** 3.13.5
- **boto3:** 1.40.60 ✅
- **openpyxl:** 3.1.5 ✅
- **AWS Region:** eu-west-1
- **DynamoDB:** 191 certificates accessible

---

## 🔄 Daily Workflow

### Start Working (New Terminal)
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# You'll see: (venv) PS C:\...\cert-dashboard>
```

### Run Scripts
```powershell
# Import certificates
python import_certificates.py

# Test environment
python test_environment.py

# Test AWS connection
python test_aws_connection.py

# Test Lambda functions locally
python test_lambda_functions.py
```

### Stop Working
```powershell
# Deactivate virtual environment
deactivate
```

---

## 🧪 Test Scripts Available

| Script | Purpose | Expected Result |
|--------|---------|-----------------|
| `test_environment.py` | Verify Python packages | 4/4 tests passed ✅ |
| `test_aws_connection.py` | Test DynamoDB & Excel | Connect to 191 certs ✅ |
| `test_lambda_functions.py` | Test Lambda locally | 2/2 functions working ✅ |

---

## 📦 Installed Packages

```
boto3==1.40.60           # AWS SDK
botocore==1.40.60        # AWS core
openpyxl==3.1.5          # Excel support
et_xmlfile==2.0.0        # XML for Excel
jmespath==1.0.1          # JSON queries
python-dateutil==2.9.0   # Date utilities
s3transfer==0.14.0       # S3 transfers
six==1.17.0              # Python 2/3 compat
urllib3==2.5.0           # HTTP library
pip==25.3                # Package manager
```

---

## 🔧 Environment Variables (for Certificate Monitor)

When testing certificate_monitor.py locally, set these first:

```powershell
$env:CERTIFICATES_TABLE = "cert-management-dev-certificates"
$env:LOGS_TABLE = "cert-management-dev-certificate-logs"
$env:SENDER_EMAIL = "vinaya-c.nayanegali@capgemini.com"
$env:EXPIRY_THRESHOLD = "30"
$env:REGION = "eu-west-1"
```

---

## 🎯 VS Code Integration

### Select Python Interpreter
1. Press: `Ctrl + Shift + P`
2. Type: "Python: Select Interpreter"
3. Choose: `.\venv\Scripts\python.exe`

### Auto-Activation
- VS Code will detect `venv` folder
- New terminals will auto-activate
- Look for `(venv)` in terminal prompt

---

## 📚 Documentation Files

- **PYTHON_ENVIRONMENT_SETUP.md** - Complete setup guide
- **requirements.txt** - All package versions
- **README.md** - Project documentation
- **TEST_RESULTS.md** - Dashboard test results

---

## ✅ Verified Working

| Component | Status | Details |
|-----------|--------|---------|
| Python Environment | ✅ | Virtual env active |
| AWS DynamoDB | ✅ | 191 certificates accessible |
| boto3 SDK | ✅ | Version 1.40.60 |
| openpyxl | ✅ | Version 3.1.5 |
| Dashboard API | ✅ | Returns 191 certs |
| Certificate Monitor | ✅ | Checks expiry |
| Excel Read/Write | ✅ | Fully functional |

---

## 🆘 Troubleshooting

### "python: command not found"
```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1
```

### "Module not found: boto3"
```powershell
# Make sure venv is active (you should see (venv) in prompt)
# If not, activate it:
.\venv\Scripts\Activate.ps1

# Verify installation:
pip list
```

### "Cannot activate script"
```powershell
# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Need to reinstall packages
```powershell
# Activate environment
.\venv\Scripts\Activate.ps1

# Install from requirements.txt
pip install -r requirements.txt
```

---

## 🎉 Success Indicators

When everything is working correctly, you should see:

1. ✅ `(venv)` prefix in PowerShell prompt
2. ✅ `python --version` returns "Python 3.13.5"
3. ✅ `pip list` shows boto3 and openpyxl
4. ✅ `python test_environment.py` → 4/4 tests passed
5. ✅ `python test_aws_connection.py` → All tests passed
6. ✅ `python test_lambda_functions.py` → 2/2 functions working

---

**Last Updated:** October 29, 2025  
**Status:** ✅ Production Ready
