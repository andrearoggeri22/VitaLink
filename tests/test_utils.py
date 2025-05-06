"""
Test module for utility functions.

This module tests the utility functions including:
- Email validation
- Password strength validation
- UUID validation
- Date parsing and formatting
- Data serialization functions
"""
import pytest
from datetime import date
import uuid

from app.utils import (
    validate_email, is_valid_password, validate_uuid,
    parse_date, to_serializable_dict
)


class TestUtilsFunctions:
    """Test class for utility functions.
    
    This class tests the various utility functions provided by the application,
    including validation functions, data parsing, and serialization utilities.
    """
    def test_validate_email(self):
        """Test email validation function.
        
        Verifies that the email validation function correctly identifies
        valid and invalid email formats.
        """
        # Valid emails
        assert validate_email("test@example.com") is True
        assert validate_email("user.name+tag@example.co.uk") is True
        assert validate_email("123.456@domain.it") is True
        
        # Invalid emails
        assert validate_email("invalid_email") is False
        assert validate_email("missing@domain") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@.com") is False
        assert validate_email("") is False
        assert validate_email(None) is False    
    def test_is_valid_password(self):
        """Test password strength validation function.
        
        Verifies that the password strength validation function correctly identifies
        valid and invalid passwords based on length, character types (uppercase,
        lowercase, digits, special characters) and returns appropriate messages.
        """
        # Valid passwords
        valid, message = is_valid_password("Password123!")
        assert valid is True
        assert "strong" in message.lower()
        
        valid, message = is_valid_password("C0mplex!PassWord")
        assert valid is True
        
        # Invalid passwords - too short
        valid, message = is_valid_password("Abc12!")
        assert valid is False
        assert "8 characters" in message
        
        # Invalid passwords - missing uppercase
        valid, message = is_valid_password("password123!")
        assert valid is False
        assert "uppercase" in message.lower()
        
        # Invalid passwords - missing lowercase
        valid, message = is_valid_password("PASSWORD123!")
        assert valid is False
        assert "lowercase" in message.lower()
        
        # Invalid passwords - missing digit
        valid, message = is_valid_password("PasswordABC!")
        assert valid is False
        assert "digit" in message.lower()
        
        # Invalid passwords - missing special character
        valid, message = is_valid_password("Password123")
        assert valid is False
        assert "special character" in message.lower()
        
        # Empty password
        valid, message = is_valid_password("")
        assert valid is False
        
        # None password
        valid, message = is_valid_password(None)
        assert valid is False    
    def test_validate_uuid(self):
        """Test UUID validation function.
        
        Verifies that the UUID validation function correctly identifies
        valid and invalid UUID formats.
        """
        # Valid UUIDs
        valid_uuid = str(uuid.uuid4())
        assert validate_uuid(valid_uuid) is True
        assert validate_uuid("123e4567-e89b-12d3-a456-426614174000") is True
        
        # Invalid UUIDs
        assert validate_uuid("invalid-uuid") is False
        assert validate_uuid("123e4567-e89b-12d3-a456-42661417400") is False  # Too short
        assert validate_uuid("123e4567-e89b-12d3-a456-4266141740000") is False  # Too long
        assert validate_uuid("") is False
        assert validate_uuid(None) is False    
    def test_parse_date(self):
        """Test date parsing function.
        
        Verifies that the date parsing function correctly converts ISO format date 
        strings (YYYY-MM-DD) to Python date objects and properly handles invalid formats
        by raising appropriate exceptions.
        """
        # Valid date strings
        assert parse_date("2023-05-15") == date(2023, 5, 15)
        assert parse_date("2020-01-01") == date(2020, 1, 1)
        assert parse_date("2025-12-31") == date(2025, 12, 31)
        
        # Invalid date strings
        with pytest.raises(ValueError):
            parse_date("15-05-2023")  # Wrong format
        
        with pytest.raises(ValueError):
            parse_date("2023/05/15")  # Wrong separator
        
        with pytest.raises(ValueError):
            parse_date("2023-13-15")  # Invalid month
        
        with pytest.raises(ValueError):
            parse_date("2023-05-32")  # Invalid day
        
        with pytest.raises(ValueError):
            parse_date("")  # Empty string
        
        with pytest.raises(ValueError):
            parse_date(None)  # None value    
    def test_to_serializable_dict(self):
        """Test object serialization function.
        
        Verifies that the object serialization function correctly converts various data types 
        into JSON-serializable formats, handling dates, custom objects with to_dict methods,
        lists of mixed objects, and simple values appropriately.
        """
        # Test with dictionary containing various types
        test_dict = {
            "string": "value",
            "integer": 123,
            "float": 123.45,
            "date": date(2023, 5, 15),
            "list": [1, 2, 3],
            "nested_dict": {"key": "value"},
            "boolean": True,
            "none": None
        }
        
        serialized = to_serializable_dict(test_dict)
        
        assert serialized["string"] == "value"
        assert serialized["integer"] == 123
        assert serialized["float"] == 123.45
        assert serialized["date"] == "2023-05-15"  # Date converted to string
        assert serialized["list"] == [1, 2, 3]
        assert serialized["nested_dict"] == {"key": "value"}
        assert serialized["boolean"] is True
        assert serialized["none"] is None
        
        # Test with object having to_dict method
        class TestObject:
            def to_dict(self):
                return {"id": 1, "name": "Test Object"}
        
        test_obj = TestObject()
        serialized = to_serializable_dict(test_obj)
        assert serialized == {"id": 1, "name": "Test Object"}
        
        # Test with list of mixed objects
        test_list = [
            {"key": "value"},
            date(2023, 5, 15),
            TestObject()
        ]
        
        serialized = to_serializable_dict(test_list)
        assert serialized[0] == {"key": "value"}
        assert serialized[1] == "2023-05-15"
        assert serialized[2] == {"id": 1, "name": "Test Object"}
        
        # Test with simple values
        assert to_serializable_dict("string") == "string"
        assert to_serializable_dict(123) == 123
        assert to_serializable_dict(None) is None
