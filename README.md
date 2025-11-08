# Certificate Monitor

> **Professional certificate monitoring and management system for AWS**

[![Status](https://img.shields.io/badge/status-production--ready-green)]()
[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20DynamoDB%20%7C%20S3-orange)]()
[![Python](https://img.shields.io/badge/python-3.13-blue)]()

## 📋 Quick Links

- **[📚 Full Documentation](docs/README.md)** - Complete project documentation
- **[🚀 Quick Reference](docs/QUICK_REFERENCE.md)** - Daily workflow and commands
- **[🔧 Deployment Guide](docs/DEPLOYMENT_SUMMARY.md)** - Infrastructure deployment
- **[🐍 Python Setup](docs/PYTHON_ENVIRONMENT_SETUP.md)** - Development environment

## 🎯 Overview

Automated certificate monitoring system with:
- ✅ Daily expiry monitoring
- ✅ Email notifications
- ✅ Web dashboard
- ✅ Audit logging
- ✅ Bulk import from Excel

## 🚀 Quick Start

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Test environment
python tests/python/test_environment.py

# 3. Open dashboard
# http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com
```

## 📁 Project Structure

```
cert-dashboard/
├── src/          # Source code & utilities
├── lambda/       # AWS Lambda functions
├── dashboard/    # Frontend application
├── tests/        # All test files
├── docs/         # Documentation
├── terraform/    # Infrastructure as Code
├── config/       # Configuration files
└── archive/      # Archived scripts
```

## 🔧 Development

### Run Scripts
```powershell
python src/scripts/import_certificates.py
python tests/python/test_aws_connection.py
```

### Use Utilities
```python
from src.utils.aws_helpers import get_table
from src.utils.certificate_helpers import calculate_days_until_expiry
from src.utils.config import get_config
```

## 📊 Dashboard

**Live Dashboard:** http://cert-management-dev-dashboard-a3px89bh.s3-website-eu-west-1.amazonaws.com

Features:
- View all certificates
- Filter by status/environment
- Add/edit certificates
- Sort columns
- View audit logs

## 🌍 Environment

- **Account:** 992155623828 (Sandbox)
- **Region:** eu-west-1
- **Profile:** aws-sandbox
- **Environment:** dev

## 📞 Resources

- **GitHub:** https://github.com/vinaya-cg/certificate-monitor
- **API:** https://rwqmbee3uvlzkogzhxiwg3fvzi0dmgmx.lambda-url.eu-west-1.on.aws/
- **Terraform State:** cert-dashboard/terraform/

## ✅ Status

- **191 certificates** imported
- **All tests passing**
- **Production ready**
- **Code refactored** (November 2025)

---

**For detailed documentation, see [docs/README.md](docs/README.md)**
