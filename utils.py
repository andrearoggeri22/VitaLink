import re
import uuid
from datetime import datetime

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
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

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
        'weight': 'kg',
        # Unità per i nuovi parametri fitness
        'steps': 'steps',
        'calories': 'kcal',
        'distance': 'km',
        'active_minutes': 'min',
        'sleep_duration': 'hours',
        'floors_climbed': 'floors'
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

def get_vital_reference_range(vital_type, patient_age=None, patient_gender=None):
    """
    Get reference ranges for vital signs.
    
    Returns a dictionary with min and max values.
    """
    # Default reference ranges for adults
    reference_ranges = {
        'heart_rate': {'min': 60, 'max': 100, 'unit': 'bpm', 'name': 'Heart Rate'},
        'blood_pressure': {'min': '90/60', 'max': '120/80', 'unit': 'mmHg', 'name': 'Blood Pressure'},
        'oxygen_saturation': {'min': 95, 'max': 100, 'unit': '%', 'name': 'Oxygen Saturation'},
        'temperature': {'min': 36.1, 'max': 37.2, 'unit': '°C', 'name': 'Temperature'},
        'respiratory_rate': {'min': 12, 'max': 20, 'unit': 'breaths/min', 'name': 'Respiratory Rate'},
        'glucose': {'min': 70, 'max': 100, 'unit': 'mg/dL', 'name': 'Glucose (Fasting)'},
        'weight': {'min': None, 'max': None, 'unit': 'kg', 'name': 'Weight'},
        # Reference range per i nuovi parametri fitness
        'steps': {'min': 5000, 'max': 10000, 'unit': 'steps', 'name': 'Steps'},
        'calories': {'min': 1500, 'max': 3000, 'unit': 'kcal', 'name': 'Calories'},
        'distance': {'min': 3, 'max': 8, 'unit': 'km', 'name': 'Distance'},
        'active_minutes': {'min': 30, 'max': 60, 'unit': 'min', 'name': 'Active Minutes'},
        'sleep_duration': {'min': 7, 'max': 9, 'unit': 'hours', 'name': 'Sleep Duration'},
        'floors_climbed': {'min': 5, 'max': 20, 'unit': 'floors', 'name': 'Floors Climbed'}
    }
    
    # Could implement age and gender specific ranges in the future
    
    if vital_type in reference_ranges:
        return reference_ranges[vital_type]
    else:
        return {'min': None, 'max': None, 'unit': ''}

def is_vital_in_range(vital_type, value):
    """
    Check if a vital sign value is within the normal range.
    
    Returns a tuple (is_normal, status) where status is 'normal', 'high', or 'low'
    """
    reference = get_vital_reference_range(vital_type)
    
    if reference['min'] is None or reference['max'] is None:
        return True, 'normal'
    
    if vital_type == 'blood_pressure':
        # Special case for blood pressure
        try:
            # Assuming value is in format "systolic/diastolic"
            parts = value.split('/')
            if len(parts) != 2:
                return False, 'invalid'
            
            systolic = float(parts[0])
            diastolic = float(parts[1])
            
            ref_parts_min = reference['min'].split('/')
            ref_parts_max = reference['max'].split('/')
            
            sys_min = float(ref_parts_min[0])
            dias_min = float(ref_parts_min[1])
            sys_max = float(ref_parts_max[0])
            dias_max = float(ref_parts_max[1])
            
            if systolic < sys_min or diastolic < dias_min:
                return False, 'low'
            elif systolic > sys_max or diastolic > dias_max:
                return False, 'high'
            else:
                return True, 'normal'
        except:
            return False, 'invalid'
    else:
        # For other numeric vital signs
        try:
            value_float = float(value)
            if value_float < reference['min']:
                return False, 'low'
            elif value_float > reference['max']:
                return False, 'high'
            else:
                return True, 'normal'
        except:
            return False, 'invalid'
