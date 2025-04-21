import re
import uuid
from datetime import datetime

def validate_email(email):
    """Validate email format."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_uuid(uuid_string):
    """Validate UUID format."""
    try:
        uuid_obj = uuid.UUID(uuid_string)
        return str(uuid_obj) == uuid_string
    except (ValueError, AttributeError):
        return False

def parse_date(date_string):
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD")

def get_vital_sign_unit(vital_type):
    """Get the appropriate unit for a vital sign type."""
    vital_type_units = {
        'heart_rate': 'bpm',
        'blood_pressure': 'mmHg',
        'oxygen_saturation': '%',
        'temperature': '°C',
        'respiratory_rate': 'breaths/min',
        'glucose': 'mg/dL',
        'weight': 'kg'
    }
    
    return vital_type_units.get(vital_type, '')

def format_vital_sign_value(vital_type, value, unit):
    """Format a vital sign value with its unit."""
    if not unit:
        unit = get_vital_sign_unit(vital_type)
    
    if vital_type == 'blood_pressure':
        # Special case for blood pressure which is often systolic/diastolic
        return value
    
    return f"{value} {unit}"
