"""
Configuration Management
Centralized configuration for the Certificate Monitor application
"""
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for Certificate Monitor"""
    
    # Default values
    DEFAULT_REGION = 'eu-west-1'
    DEFAULT_EXPIRY_THRESHOLD = 30
    DEFAULT_ENVIRONMENT = 'dev'
    
    # Table names
    CERTIFICATES_TABLE_TEMPLATE = 'cert-management-{env}-certificates'
    LOGS_TABLE_TEMPLATE = 'cert-management-{env}-certificate-logs'
    
    # S3 buckets
    DASHBOARD_BUCKET_TEMPLATE = 'cert-management-{env}-dashboard'
    UPLOADS_BUCKET_TEMPLATE = 'cert-management-{env}-uploads'
    LOGS_BUCKET_TEMPLATE = 'cert-management-{env}-logs'
    
    # Lambda functions
    CERTIFICATE_MONITOR_FUNCTION_TEMPLATE = 'cert-management-{env}-certificate-monitor'
    DASHBOARD_API_FUNCTION_TEMPLATE = 'cert-management-{env}-dashboard-api'
    EXCEL_PROCESSOR_FUNCTION_TEMPLATE = 'cert-management-{env}-excel-processor'
    
    # Valid environments
    VALID_ENVIRONMENTS = ['PRD', 'ACC', 'TST', 'DEV']
    
    # Certificate statuses
    VALID_STATUSES = [
        'Active',
        'Due for Renewal',
        'Expired',
        'Renewal in Progress',
        'Renewal Done'
    ]
    
    def __init__(self, environment: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            environment: Deployment environment (dev, prod, etc.)
        """
        self.environment = environment or os.environ.get('ENVIRONMENT', self.DEFAULT_ENVIRONMENT)
        self.region = os.environ.get('AWS_REGION', self.DEFAULT_REGION)
    
    def get_certificates_table_name(self) -> str:
        """Get certificates table name"""
        return os.environ.get('CERTIFICATES_TABLE') or \
               self.CERTIFICATES_TABLE_TEMPLATE.format(env=self.environment)
    
    def get_logs_table_name(self) -> str:
        """Get logs table name"""
        return os.environ.get('LOGS_TABLE') or \
               self.LOGS_TABLE_TEMPLATE.format(env=self.environment)
    
    def get_dashboard_bucket_name(self) -> str:
        """Get dashboard S3 bucket name"""
        return os.environ.get('DASHBOARD_BUCKET') or \
               self.DASHBOARD_BUCKET_TEMPLATE.format(env=self.environment)
    
    def get_uploads_bucket_name(self) -> str:
        """Get uploads S3 bucket name"""
        return os.environ.get('UPLOADS_BUCKET') or \
               self.UPLOADS_BUCKET_TEMPLATE.format(env=self.environment)
    
    def get_logs_bucket_name(self) -> str:
        """Get logs S3 bucket name"""
        return os.environ.get('LOGS_BUCKET') or \
               self.LOGS_BUCKET_TEMPLATE.format(env=self.environment)
    
    def get_sender_email(self) -> str:
        """Get SES sender email"""
        return os.environ.get('SENDER_EMAIL', 'vinaya-c.nayanegali@capgemini.com')
    
    def get_expiry_threshold_days(self) -> int:
        """Get expiry threshold in days"""
        return int(os.environ.get('EXPIRY_THRESHOLD', self.DEFAULT_EXPIRY_THRESHOLD))
    
    def get_region(self) -> str:
        """Get AWS region"""
        return self.region
    
    def get_environment(self) -> str:
        """Get deployment environment"""
        return self.environment
    
    def to_dict(self) -> Dict:
        """Get all configuration as dictionary"""
        return {
            'environment': self.get_environment(),
            'region': self.get_region(),
            'certificates_table': self.get_certificates_table_name(),
            'logs_table': self.get_logs_table_name(),
            'dashboard_bucket': self.get_dashboard_bucket_name(),
            'uploads_bucket': self.get_uploads_bucket_name(),
            'logs_bucket': self.get_logs_bucket_name(),
            'sender_email': self.get_sender_email(),
            'expiry_threshold_days': self.get_expiry_threshold_days()
        }
    
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if valid, raises exception otherwise
        """
        # Check required environment variables for Lambda
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            required_vars = ['CERTIFICATES_TABLE', 'LOGS_TABLE']
            missing = [var for var in required_vars if not os.environ.get(var)]
            if missing:
                raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        logger.info("Configuration validated successfully")
        return True


# Global configuration instance
_config = None


def get_config(environment: Optional[str] = None) -> Config:
    """
    Get or create global configuration instance
    
    Args:
        environment: Deployment environment
    
    Returns:
        Config instance
    """
    global _config
    if _config is None or (environment and environment != _config.environment):
        _config = Config(environment)
    return _config


def get_table_names(environment: Optional[str] = None) -> Dict[str, str]:
    """
    Get all table names
    
    Args:
        environment: Deployment environment
    
    Returns:
        Dictionary of table names
    """
    config = get_config(environment)
    return {
        'certificates': config.get_certificates_table_name(),
        'logs': config.get_logs_table_name()
    }


def get_email_config(environment: Optional[str] = None) -> Dict:
    """
    Get email configuration
    
    Args:
        environment: Deployment environment
    
    Returns:
        Dictionary of email configuration
    """
    config = get_config(environment)
    return {
        'sender': config.get_sender_email(),
        'region': config.get_region()
    }


def get_bucket_names(environment: Optional[str] = None) -> Dict[str, str]:
    """
    Get all S3 bucket names
    
    Args:
        environment: Deployment environment
    
    Returns:
        Dictionary of bucket names
    """
    config = get_config(environment)
    return {
        'dashboard': config.get_dashboard_bucket_name(),
        'uploads': config.get_uploads_bucket_name(),
        'logs': config.get_logs_bucket_name()
    }


# Environment detection
def is_lambda_environment() -> bool:
    """Check if running in AWS Lambda"""
    return 'AWS_LAMBDA_FUNCTION_NAME' in os.environ


def is_local_environment() -> bool:
    """Check if running locally"""
    return not is_lambda_environment()
