"""
Certificate Business Logic Helper Functions
Certificate status calculation, validation, and formatting
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_days_until_expiry(expiry_date: str) -> int:
    """
    Calculate days until certificate expiry
    
    Args:
        expiry_date: Expiry date in YYYY-MM-DD format
    
    Returns:
        Number of days until expiry (negative if expired)
    """
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        delta = expiry - today
        return delta.days
    except Exception as e:
        logger.error(f"Error calculating days until expiry for {expiry_date}: {str(e)}")
        return 0


def determine_certificate_status(expiry_date: str, current_status: Optional[str] = None) -> str:
    """
    Determine certificate status based on expiry date
    Preserves manual statuses like "Renewal in Progress" and "Renewal Done"
    
    Args:
        expiry_date: Expiry date in YYYY-MM-DD format
        current_status: Current status (if any)
    
    Returns:
        Certificate status: "Active", "Due for Renewal", "Expired", 
        "Renewal in Progress", or "Renewal Done"
    """
    # Preserve manual statuses
    manual_statuses = ["Renewal in Progress", "Renewal Done"]
    if current_status in manual_statuses:
        return current_status
    
    days_left = calculate_days_until_expiry(expiry_date)
    
    if days_left < 0:
        return "Expired"
    elif days_left <= 30:
        return "Due for Renewal"
    else:
        return "Active"


def is_certificate_expiring(expiry_date: str, current_date: str, threshold_date: str) -> bool:
    """
    Check if certificate is expiring within threshold
    
    Args:
        expiry_date: Certificate expiry date (YYYY-MM-DD)
        current_date: Current date (YYYY-MM-DD)
        threshold_date: Threshold date (YYYY-MM-DD)
    
    Returns:
        True if certificate expires between current_date and threshold_date
    """
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        current = datetime.strptime(current_date, '%Y-%m-%d')
        threshold = datetime.strptime(threshold_date, '%Y-%m-%d')
        
        return current <= expiry <= threshold
    except Exception as e:
        logger.error(f"Error checking expiry: {str(e)}")
        return False


def validate_certificate_data(data: Dict) -> Tuple[bool, Optional[str]]:
    """
    Validate certificate data for required fields
    
    Args:
        data: Certificate data dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['CommonName', 'ExpiryDate', 'Environment']
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"
    
    # Validate expiry date format
    try:
        datetime.strptime(data['ExpiryDate'], '%Y-%m-%d')
    except ValueError:
        return False, "ExpiryDate must be in YYYY-MM-DD format"
    
    # Validate environment
    valid_environments = ['PRD', 'ACC', 'TST', 'DEV']
    if data.get('Environment') not in valid_environments:
        return False, f"Environment must be one of: {', '.join(valid_environments)}"
    
    return True, None


def generate_certificate_id() -> str:
    """
    Generate unique certificate ID
    
    Returns:
        Unique certificate ID (e.g., cert-abc123)
    """
    return f"cert-{uuid.uuid4().hex[:8]}"


def format_certificate_for_display(cert: Dict) -> Dict:
    """
    Format certificate data for frontend display
    Adds calculated fields like DaysUntilExpiry
    
    Args:
        cert: Raw certificate data from database
    
    Returns:
        Formatted certificate data
    """
    formatted = cert.copy()
    
    # Add days until expiry
    if 'ExpiryDate' in cert:
        formatted['DaysUntilExpiry'] = calculate_days_until_expiry(cert['ExpiryDate'])
    
    # Ensure status is current (recalculate based on expiry date)
    if 'ExpiryDate' in cert:
        current_status = cert.get('Status')
        formatted['Status'] = determine_certificate_status(cert['ExpiryDate'], current_status)
    
    # Add LastUpdated if not present
    if 'LastUpdated' not in formatted:
        formatted['LastUpdated'] = datetime.utcnow().isoformat()
    
    return formatted


def create_audit_log_entry(certificate_id: str, action: str, 
                          old_values: Optional[Dict] = None, 
                          new_values: Optional[Dict] = None,
                          user: str = 'system') -> Dict:
    """
    Create audit log entry for certificate changes
    
    Args:
        certificate_id: ID of the certificate
        action: Action performed (e.g., 'created', 'updated', 'status_changed')
        old_values: Previous values (for updates)
        new_values: New values
        user: User who performed the action
    
    Returns:
        Audit log entry dictionary
    """
    log_entry = {
        'LogID': str(uuid.uuid4()),
        'CertificateID': certificate_id,
        'Action': action,
        'Timestamp': datetime.utcnow().isoformat(),
        'User': user
    }
    
    if old_values:
        log_entry['OldValues'] = old_values
    
    if new_values:
        log_entry['NewValues'] = new_values
    
    # Calculate what changed
    if old_values and new_values:
        changes = {}
        for key in new_values:
            if key in old_values and old_values[key] != new_values[key]:
                changes[key] = {
                    'old': old_values[key],
                    'new': new_values[key]
                }
        if changes:
            log_entry['Changes'] = changes
    
    return log_entry


def get_certificate_status_color(status: str) -> str:
    """
    Get color code for certificate status
    
    Args:
        status: Certificate status
    
    Returns:
        Color name or hex code
    """
    status_colors = {
        'Active': 'green',
        'Due for Renewal': 'yellow',
        'Expired': 'red',
        'Renewal in Progress': 'blue',
        'Renewal Done': 'green'
    }
    return status_colors.get(status, 'gray')


def format_expiry_notification(cert: Dict) -> Dict:
    """
    Format certificate data for expiry notification email
    
    Args:
        cert: Certificate data
    
    Returns:
        Formatted notification data
    """
    days_left = calculate_days_until_expiry(cert.get('ExpiryDate', ''))
    
    return {
        'certificate_name': cert.get('CommonName', 'Unknown'),
        'certificate_id': cert.get('CertificateID', ''),
        'expiry_date': cert.get('ExpiryDate', ''),
        'days_until_expiry': days_left,
        'environment': cert.get('Environment', ''),
        'application': cert.get('Application', ''),
        'owner': cert.get('Owner', 'Unassigned'),
        'urgency': 'HIGH' if days_left <= 7 else 'MEDIUM' if days_left <= 14 else 'LOW'
    }


def sort_certificates_by_expiry(certificates: list, ascending: bool = True) -> list:
    """
    Sort certificates by expiry date
    
    Args:
        certificates: List of certificate dictionaries
        ascending: Sort ascending (soonest first) if True
    
    Returns:
        Sorted list of certificates
    """
    def get_expiry_date(cert):
        try:
            return datetime.strptime(cert.get('ExpiryDate', '9999-12-31'), '%Y-%m-%d')
        except:
            return datetime.max
    
    return sorted(certificates, key=get_expiry_date, reverse=not ascending)


def group_certificates_by_status(certificates: list) -> Dict[str, list]:
    """
    Group certificates by their status
    
    Args:
        certificates: List of certificate dictionaries
    
    Returns:
        Dictionary with status as key and list of certificates as value
    """
    grouped = {}
    for cert in certificates:
        status = cert.get('Status', 'Unknown')
        if status not in grouped:
            grouped[status] = []
        grouped[status].append(cert)
    
    return grouped


def group_certificates_by_environment(certificates: list) -> Dict[str, list]:
    """
    Group certificates by environment
    
    Args:
        certificates: List of certificate dictionaries
    
    Returns:
        Dictionary with environment as key and list of certificates as value
    """
    grouped = {}
    for cert in certificates:
        env = cert.get('Environment', 'Unknown')
        if env not in grouped:
            grouped[env] = []
        grouped[env].append(cert)
    
    return grouped
