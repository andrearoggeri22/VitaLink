"""
Utility Module.

This module provides common utility functions used throughout the VitaLink application.
It includes helpers for:

1. Data validation (email, UUID, password strength)
2. Date parsing and formatting
3. Data serialization for API responses and JSON conversion
4. Common string manipulation utilities

These functions are designed to be reusable across the application and provide
consistent behavior for frequently needed operations.
"""

import re
import uuid
from datetime import datetime, date
from flask_babel import gettext as _
def validate_email(email):
    """
    Validate if a string is a correctly formatted email address.
    
    This function uses a regular expression pattern to check if the provided 
    string conforms to standard email format requirements.
    
    Args:
        email (str): The email address string to validate
        
    Returns:
        bool: True if the email is valid, False otherwise
        
    Example:
        >>> validate_email("doctor@example.com")
        True
        >>> validate_email("invalid-email")
        False
        >>> validate_email(None)
        False
    """
    if email is None:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def is_valid_password(password):
    """
    Validate password strength against security requirements.
    
    This function checks if a password meets the minimum security requirements:
    - At least 8 characters long
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password (str): The password string to validate
        
    Returns:
        tuple: A tuple containing:
            - bool: True if password meets all requirements, False otherwise
            - str: A message describing the validation result or the specific requirement not met
            
    Example:
        >>> is_valid_password("Abc123!")
        (True, "The password is strong")
        >>> is_valid_password("password")
        (False, "The password must contain at least one uppercase letter")
        >>> is_valid_password(None)
        (False, "The password must be at least 8 characters long")
    """
    if password is None:
        return False, _("The password must be at least 8 characters long")
        
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
    """
    Validate if a string is a correctly formatted UUID.
    
    This function attempts to parse the provided string as a UUID and then
    compares the resulting string representation to ensure it matches the
    original input. This approach catches malformed UUIDs as well as
    strings that might parse but don't strictly follow UUID format.
    
    Args:
        uuid_string (str): The UUID string to validate
        
    Returns:
        bool: True if the string is a valid UUID, False otherwise
        
    Example:
        >>> validate_uuid("123e4567-e89b-12d3-a456-426614174000")
        True
        >>> validate_uuid("invalid-uuid")
        False
        >>> validate_uuid(None)
        False
    """
    if uuid_string is None:
        return False
        
    try:
        uuid_obj = uuid.UUID(uuid_string)
        return str(uuid_obj) == uuid_string
    except (ValueError, AttributeError, TypeError):
        return False

def parse_date(date_string):
    """
    Parse a date string in YYYY-MM-DD format to a date object.
    
    This function converts a string representation of a date in YYYY-MM-DD
    format to a Python date object. If the string cannot be parsed in the
    expected format, it raises a ValueError with a user-friendly message.
    
    Args:
        date_string (str): The date string in YYYY-MM-DD format
        
    Returns:
        date: A Python date object representing the parsed date
        
    Raises:
        ValueError: If the date string is not in the expected format or is None
        
    Example:
        >>> parse_date("2023-05-15")
        datetime.date(2023, 5, 15)
        >>> parse_date("15/05/2023")
        ValueError: Invalid date format. Please use YYYY-MM-DD
        >>> parse_date(None)
        ValueError: Invalid date format. Please use YYYY-MM-DD
    """
    if date_string is None:
        raise ValueError(_("Invalid date format. Please use YYYY-MM-DD"))
        
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(_("Invalid date format. Please use YYYY-MM-DD"))



def to_serializable_dict(obj):
    """
    Convert an object to a JSON serializable dictionary.
    
    This utility function recursively transforms complex objects into simple
    data types that can be safely serialized to JSON. It handles:
    - Dictionaries (recursively converts each value)
    - Lists (recursively converts each element)
    - Datetime objects (converts to ISO format strings)
    - Date objects (converts to ISO format strings YYYY-MM-DD)
    - Objects with to_dict() method (calls that method)
    - Other types are returned as-is
    
    Args:
        obj: The object to convert to a serializable form
        
    Returns:
        A JSON-serializable representation of the input object
        
    Example:
        >>> to_serializable_dict({'date': datetime(2023, 1, 1), 'values': [1, 2, 3]})
        {'date': '2023-01-01T00:00:00', 'values': [1, 2, 3]}
        >>> to_serializable_dict(patient_obj)  # where patient_obj has a to_dict method
        {'id': 1, 'name': 'John Smith', ...}
    """
    if isinstance(obj, dict):
        return {k: to_serializable_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_serializable_dict(i) for i in obj]    
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    else:
        return obj