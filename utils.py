import re
import uuid
import json
from datetime import datetime
from flask_babel import gettext as _
def validate_email(email):
    """Validate email format."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def is_valid_password(password):
    """
    Validate password strength.
    
    Password must:
    - Be at least 8 characters long
    - Contain at least one uppercase letter
    - Contain at least one lowercase letter
    - Contain at least one digit
    - Contain at least one special character
    """    
    if len(password) < 8:
        return False, _("The password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        return False, _("The password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        return False, _("The password must contain at least one lowercase letter")
    
    if not re.search(r'[0-9]', password):
        return False, _("The password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, _("The password must contain at least one special character")
    
    return True, _("The password is strong")

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
        raise ValueError(_("Invalid date format. Please use YYYY-MM-DD"))



def to_serializable_dict(obj):
    """
    Convert an object to a JSON serializable dictionary.
    Useful for creating JSON-safe dictionaries from SQLAlchemy objects
    and handling datetime serialization.
    """
    if isinstance(obj, dict):
        return {k: to_serializable_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_serializable_dict(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    else:
        return obj