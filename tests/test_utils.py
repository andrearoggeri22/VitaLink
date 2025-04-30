import pytest
from datetime import datetime
import uuid
import re
from app.utils import validate_email, parse_date, to_serializable_dict, validate_uuid, is_valid_password

def test_validate_email():
    """Verifica la funzione di validazione email."""
    # Email valide
    assert validate_email('test@example.com') is True
    assert validate_email('user.name+tag@example.co.uk') is True
    assert validate_email('user-name@domain.org') is True
    
    # Email non valide
    assert validate_email('test@') is False
    assert validate_email('test@.com') is False
    assert validate_email('test') is False
    assert validate_email('') is False
    assert validate_email(None) is False

def test_parse_date():
    """Verifica la funzione di parsing delle date."""
    # Date valide
    assert parse_date('2023-04-15') == datetime(2023, 4, 15, 0, 0)
    assert parse_date('15/04/2023', '%d/%m/%Y') == datetime(2023, 4, 15, 0, 0)
    
    # Date non valide
    assert parse_date('invalid-date') is None
    assert parse_date('') is None
    assert parse_date(None) is None

def test_to_serializable_dict():
    """Verifica la funzione che converte oggetti in dizionari JSON serializzabili."""
    # Dizionario semplice
    simple_dict = {'name': 'Test', 'age': 30}
    assert to_serializable_dict(simple_dict) == simple_dict
    
    # Data
    date_obj = datetime(2023, 4, 15, 10, 30, 45)
    serialized = to_serializable_dict(date_obj)
    assert isinstance(serialized, str)
    assert '2023-04-15' in serialized
    
    # Dizionario con data
    complex_dict = {'name': 'Test', 'date': date_obj}
    serialized = to_serializable_dict(complex_dict)
    assert 'name' in serialized and serialized['name'] == 'Test'
    assert 'date' in serialized and isinstance(serialized['date'], str)
    
    # Lista di oggetti
    obj_list = [{'name': 'Test1'}, {'name': 'Test2', 'date': date_obj}]
    serialized = to_serializable_dict(obj_list)
    assert len(serialized) == 2
    assert serialized[0]['name'] == 'Test1'
    assert 'date' in serialized[1] and isinstance(serialized[1]['date'], str)

def test_validate_uuid():
    """Verifica la funzione di validazione UUID."""
    # UUID validi
    valid_uuid = str(uuid.uuid4())
    assert validate_uuid(valid_uuid) is True
    
    # UUID non validi
    assert validate_uuid('not-a-uuid') is False
    assert validate_uuid('12345') is False
    assert validate_uuid('') is False
    assert validate_uuid(None) is False

def test_is_valid_password():
    """Verifica la funzione di validazione delle password."""
    # Password valide
    valid, _ = is_valid_password('Password123!')
    assert valid is True
    
    valid, _ = is_valid_password('ComplexP@ssw0rd')
    assert valid is True
    
    # Password troppo corta
    valid, message = is_valid_password('Short1!')
    assert valid is False
    assert 'lunghezza' in message.lower() or 'length' in message.lower()
    
    # Password senza numeri
    valid, message = is_valid_password('PasswordOnly!')
    assert valid is False
    assert 'numeri' in message.lower() or 'number' in message.lower()
    
    # Password senza caratteri speciali
    valid, message = is_valid_password('Password123')
    assert valid is False
    assert 'speciali' in message.lower() or 'special' in message.lower()
    
    # Password senza maiuscole
    valid, message = is_valid_password('password123!')
    assert valid is False
    assert 'maiuscol' in message.lower() or 'uppercase' in message.lower()
    
    # Password senza minuscole
    valid, message = is_valid_password('PASSWORD123!')
    assert valid is False
    assert 'minuscol' in message.lower() or 'lowercase' in message.lower()
