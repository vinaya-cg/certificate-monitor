# 🐍 Python Environment Setup Guide - Certificate Monitor Project

**Date:** October 29, 2025  
**Python Version:** 3.13.5  
**Project:** Certificate Management Dashboard

---

## 📋 Table of Contents

1. [Current Status](#current-status)
2. [Option 1: Virtual Environment (Recommended)](#option-1-virtual-environment-recommended)
3. [Option 2: Conda Environment](#option-2-conda-environment)
4. [Option 3: Global Python Installation](#option-3-global-python-installation)
5. [Required Python Packages](#required-python-packages)
6. [VS Code Configuration](#vs-code-configuration)
7. [Testing the Environment](#testing-the-environment)
8. [Troubleshooting](#troubleshooting)

---

## 🔍 Current Status

### Installed Python Version
```powershell
# Check installed Python
py --version
# Output: Python 3.13.5
```

### Current Issue
- Python is installed but not in PATH as `python`
- Using `py` launcher instead
- No virtual environment currently activated
- boto3 and openpyxl packages need to be installed

---

## ✅ Option 1: Virtual Environment (Recommended)

### Why Virtual Environment?
- ✅ Isolates project dependencies
- ✅ Prevents package conflicts
- ✅ Easy to replicate across machines
- ✅ Clean project organization
- ✅ Best practice for Python projects

### Step-by-Step Setup

#### 1. Create Virtual Environment

```powershell
# Navigate to project directory
cd "C:\Users\vnayaneg\OneDrive - Capgemini\Desktop\Sogeti\Automation and Innovation\Run factory\certificate monitor\cert-dashboard"

# Create virtual environment using py launcher
py -m venv venv

# Alternative: Specify Python version
py -3.13 -m venv venv
```

**What this does:**
- Creates a `venv` folder in your project
- Contains isolated Python installation
- Includes pip for package management

#### 2. Activate Virtual Environment

```powershell
# Activate the virtual environment
.\venv\Scripts\Activate.ps1
```

**Expected Output:**
```
(venv) PS C:\Users\vnayaneg\...\cert-dashboard>
```

**Troubleshooting Activation:**
If you get an execution policy error:
```powershell
# Check current policy
Get-ExecutionPolicy

# Set policy for current user (run as needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activating again
.\venv\Scripts\Activate.ps1
```

#### 3. Verify Virtual Environment

```powershell
# Check Python location (should point to venv)
Get-Command python

# Check Python version
python --version

# Check pip version
pip --version
```

**Expected Output:**
```
python.exe : C:\Users\vnayaneg\...\cert-dashboard\venv\Scripts\python.exe
Python 3.13.5
pip 24.x from ...\venv\Lib\site-packages\pip (python 3.13)
```

#### 4. Install Required Packages

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install boto3 (AWS SDK)
pip install boto3

# Install openpyxl (Excel support)
pip install openpyxl

# Install all at once (recommended)
pip install boto3 openpyxl
```

#### 5. Verify Installation

```powershell
# List installed packages
pip list

# Check specific packages
pip show boto3
pip show openpyxl
```

**Expected Output:**
```
Package    Version
---------- -------
boto3      1.35.x
openpyxl   3.1.x
pip        24.x
setuptools xx.x
```

#### 6. Create Requirements File

```powershell
# Generate requirements.txt
pip freeze > requirements.txt
```

**requirements.txt will contain:**
```
boto3==1.35.x
botocore==1.35.x
jmespath==1.x.x
openpyxl==3.1.x
python-dateutil==2.x.x
s3transfer==0.x.x
six==1.x.x
urllib3==2.x.x
```

#### 7. Deactivate (when done)

```powershell
# Deactivate virtual environment
deactivate
```

---

## 🐍 Option 2: Conda Environment

### If you prefer Anaconda/Miniconda

#### 1. Check if Conda is installed

```powershell
conda --version
```

#### 2. Create Conda Environment

```powershell
# Create environment with Python 3.13
conda create -n cert-monitor python=3.13

# Activate environment
conda activate cert-monitor
```

#### 3. Install Packages

```powershell
# Install using conda
conda install -c conda-forge boto3 openpyxl

# Or use pip within conda environment
pip install boto3 openpyxl
```

#### 4. Export Environment

```powershell
# Export to environment.yml
conda env export > environment.yml
```

#### 5. Deactivate

```powershell
conda deactivate
```

---

## 🌐 Option 3: Global Python Installation

### ⚠️ Not Recommended (but possible)

#### Install Packages Globally

```powershell
# Using py launcher
py -m pip install boto3 openpyxl

# Verify installation
py -m pip list
```

**Drawbacks:**
- ❌ Affects all Python projects
- ❌ Potential version conflicts
- ❌ Harder to manage dependencies
- ❌ Not isolated

---

## 📦 Required Python Packages

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **boto3** | >= 1.35.0 | AWS SDK for Python - DynamoDB, S3, SES, Lambda |
| **openpyxl** | >= 3.1.0 | Excel file reading/writing (.xlsx) |

### Indirect Dependencies (auto-installed)

- **botocore**: Low-level AWS SDK
- **jmespath**: JSON query language for Python
- **python-dateutil**: Extensions to datetime
- **s3transfer**: S3 transfer manager
- **urllib3**: HTTP client
- **et-xmlfile**: XML handling for openpyxl

---

## 🔧 VS Code Configuration

### 1. Select Python Interpreter

**Method 1: Command Palette**
```
1. Press: Ctrl + Shift + P
2. Type: "Python: Select Interpreter"
3. Choose: .\venv\Scripts\python.exe
```

**Method 2: Status Bar**
```
1. Click Python version in bottom-left status bar
2. Select virtual environment
```

### 2. Create .vscode/settings.json

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
  "python.terminal.activateEnvironment": true,
  "python.analysis.typeCheckingMode": "basic",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": false,
  "python.formatting.provider": "autopep8",
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### 3. Create .vscode/launch.json (for debugging)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: Import Certificates",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/import_certificates.py",
      "console": "integratedTerminal",
      "args": []
    }
  ]
}
```

### 4. Install VS Code Python Extension

```
Extension ID: ms-python.python
```

**Features:**
- IntelliSense (auto-completion)
- Linting and error detection
- Debugging support
- Virtual environment detection
- Jupyter notebook support

---

## ✅ Testing the Environment

### Test Script

Create `test_environment.py`:

```python
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
```

### Run Test

```powershell
# Activate environment first
.\venv\Scripts\Activate.ps1

# Run test script
python test_environment.py
```

**Expected Output:**
```
============================================================
🐍 PYTHON ENVIRONMENT TEST
============================================================

✅ Python Version: 3.13.5
✅ Python Executable: ...\venv\Scripts\python.exe
✅ Platform: Windows-10-...

✅ boto3 installed: 1.35.x
✅ AWS Session created (Region: eu-west-1)

✅ openpyxl installed: 3.1.x

✅ openpyxl can create workbooks

✅ DynamoDB client created successfully

============================================================
📊 RESULTS: 4/4 tests passed
============================================================
✅ Environment configured correctly!
```

---

## 🔧 Troubleshooting

### Issue 1: "Python was not found"

**Problem:** `python` command not recognized

**Solutions:**

**Option A: Use `py` launcher**
```powershell
# Instead of python
py script.py

# Instead of pip
py -m pip install package
```

**Option B: Add Python to PATH**
```powershell
# Find Python installation
py -0p

# Add to PATH (adjust path as needed)
$env:Path += ";C:\Users\vnayaneg\AppData\Local\Programs\Python\Python313"

# Make permanent (run as Administrator)
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Python313", "Machine")
```

**Option C: Use virtual environment** (automatically handles this)

---

### Issue 2: Execution Policy Error

**Problem:** Cannot activate virtual environment

```
.\venv\Scripts\Activate.ps1 : File cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
# Check current policy
Get-ExecutionPolicy

# Set to RemoteSigned (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or use Bypass for current session only
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

---

### Issue 3: pip Not Found After Activation

**Problem:** `pip: command not found` in virtual environment

**Solution:**
```powershell
# Use python -m pip instead
python -m pip install boto3

# Or reinstall pip
python -m ensurepip --upgrade
```

---

### Issue 4: Package Import Fails

**Problem:** `ModuleNotFoundError: No module named 'boto3'`

**Checks:**
```powershell
# Verify you're in virtual environment
# You should see (venv) in prompt

# Check where Python is running from
Get-Command python

# Should point to venv folder, not system Python

# List installed packages
pip list

# Reinstall if missing
pip install boto3 openpyxl
```

---

### Issue 5: AWS Credentials Not Found

**Problem:** `NoCredentialsError` when running scripts

**Solution:**

**Option 1: AWS CLI Configure**
```powershell
aws configure
# Enter:
# AWS Access Key ID
# AWS Secret Access Key
# Default region: eu-west-1
# Default output: json
```

**Option 2: Environment Variables**
```powershell
$env:AWS_ACCESS_KEY_ID = "your-access-key"
$env:AWS_SECRET_ACCESS_KEY = "your-secret-key"
$env:AWS_DEFAULT_REGION = "eu-west-1"
```

**Option 3: Credentials File**
Create: `C:\Users\vnayaneg\.aws\credentials`
```ini
[default]
aws_access_key_id = your-access-key
aws_secret_access_key = your-secret-key
region = eu-west-1
```

---

## 🚀 Quick Start Commands

### Complete Setup in One Go

```powershell
# 1. Navigate to project
cd "C:\Users\vnayaneg\OneDrive - Capgemini\Desktop\Sogeti\Automation and Innovation\Run factory\certificate monitor\cert-dashboard"

# 2. Create virtual environment
py -m venv venv

# 3. Activate
.\venv\Scripts\Activate.ps1

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install packages
pip install boto3 openpyxl

# 6. Save requirements
pip freeze > requirements.txt

# 7. Verify
pip list
```

### Daily Workflow

```powershell
# Activate environment
.\venv\Scripts\Activate.ps1

# Run your script
python import_certificates.py

# Or run Lambda function locally
python lambda/dashboard_api.py

# Deactivate when done
deactivate
```

---

## 📝 Best Practices

### 1. Always Use Virtual Environment
- ✅ Create venv for each project
- ✅ Activate before working
- ✅ Keep requirements.txt updated

### 2. Version Control
```gitignore
# Add to .gitignore
venv/
__pycache__/
*.pyc
.env
.aws/
```

### 3. Requirements Management

**Save requirements:**
```powershell
pip freeze > requirements.txt
```

**Install from requirements:**
```powershell
pip install -r requirements.txt
```

### 4. Documentation
- Document Python version in README
- List all dependencies
- Include setup instructions

---

## 🎯 Summary

### Recommended Setup
1. ✅ Create virtual environment (`py -m venv venv`)
2. ✅ Activate it (`.\venv\Scripts\Activate.ps1`)
3. ✅ Install packages (`pip install boto3 openpyxl`)
4. ✅ Configure VS Code to use venv
5. ✅ Save requirements (`pip freeze > requirements.txt`)

### Why This Matters for Our Project
- **boto3**: Required for AWS DynamoDB, S3, SES, Lambda interactions
- **openpyxl**: Required for reading Excel files with certificate data
- **Isolation**: Prevents conflicts with other Python projects
- **Reproducibility**: Easy to set up on another machine or deploy to Lambda

---

## 📞 Need Help?

### Useful Commands

```powershell
# Check Python installation
py --version
py -0p  # List all Python installations

# Virtual environment
py -m venv --help
Get-Command python  # Check which Python is active

# Package management
pip list  # List installed packages
pip show package_name  # Package details
pip install --upgrade package_name  # Upgrade
pip uninstall package_name  # Remove

# AWS
aws configure list  # Check AWS config
aws sts get-caller-identity  # Verify credentials
```

### Resources
- Python Virtual Environments: https://docs.python.org/3/library/venv.html
- boto3 Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- openpyxl Documentation: https://openpyxl.readthedocs.io/

---

**Last Updated:** October 29, 2025  
**Environment:** Windows 10, Python 3.13.5, PowerShell
