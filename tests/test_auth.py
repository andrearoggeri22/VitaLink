import pytest
import json
from flask import url_for
from app import app, db
from models import Doctor

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create a test doctor
            doctor = Doctor(
                email="test@example.com",
                first_name="Test",
                last_name="Doctor",
                specialty="General"
            )
            doctor.set_password("password123")
            db.session.add(doctor)
            db.session.commit()
            
            yield client
            
            db.session.remove()
            db.drop_all()

def test_login_page(client):
    """Test that the login page loads correctly."""
    response = client.get(url_for('auth.login'))
    assert response.status_code == 200
    assert b'Please login to access the platform' in response.data

def test_login_success(client):
    """Test successful login."""
    response = client.post(
        url_for('auth.login'),
        data={'email': 'test@example.com', 'password': 'password123'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        url_for('auth.login'),
        data={'email': 'test@example.com', 'password': 'wrongpassword'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data

def test_logout(client):
    """Test logout functionality."""
    # Login first
    client.post(
        url_for('auth.login'),
        data={'email': 'test@example.com', 'password': 'password123'},
        follow_redirects=True
    )
    
    # Then logout
    response = client.get(url_for('auth.logout'), follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out successfully' in response.data

def test_api_login_success(client):
    """Test successful API login."""
    response = client.post(
        url_for('auth.api_login'),
        json={'email': 'test@example.com', 'password': 'password123'},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert data['message'] == 'Login successful'

def test_api_login_invalid(client):
    """Test API login with invalid credentials."""
    response = client.post(
        url_for('auth.api_login'),
        json={'email': 'test@example.com', 'password': 'wrongpassword'},
        content_type='application/json'
    )
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data

def test_api_login_missing_fields(client):
    """Test API login with missing fields."""
    response = client.post(
        url_for('auth.api_login'),
        json={'email': 'test@example.com'},
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
