"""
Test module for authentication functionality.

This module tests authentication functionalities including:
- User registration 
- Login and logout
- JWT token authentication
- Password validation
- Protected route access
"""
import json

from app.models import Doctor


class TestAuthentication:
    """Test class for authentication functionality.
    
    This class tests various authentication features including user registration,
    login/logout functionality, API JWT token authentication, token refresh, and
    protected route access.
    """
    def test_registration(self, client):
        """Test user registration process.
        
        Verifies that a new doctor can successfully register with valid credentials,
        and that duplicate email registration is properly rejected.
        
        Args:
            client: Flask test client
        """
        email = 'new.doctor@example.com'
        
        # Check that the doctor does not already exist
        from app import db
        existing = Doctor.query.filter_by(email=email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        
        # Test successful registration
        response = client.post('/register', data={
            'email': email,
            'first_name': 'New',
            'last_name': 'Doctor',
            'specialty': 'Cardiology',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=True)
          # Check response - look for success text
        assert response.status_code == 200
        # Check for registration success message in English or Italian
        assert b'Registration completed' in response.data or b'Registrazione completata' in response.data
        
        # Explicit database verification after registration
        # Make a new query instead of closing the session
        from sqlalchemy import text
        result = db.session.execute(text(f"SELECT * FROM doctor WHERE email = '{email}'")).fetchone()
        assert result is not None, "Doctor was not created in database"
          # Verify doctor details using a separate query
        doctor = db.session.execute(db.select(Doctor).filter_by(email=email)).scalar_one_or_none()
        assert doctor is not None, "Could not retrieve doctor from database"
        assert doctor.first_name == 'New'
        assert doctor.last_name == 'Doctor'
        assert doctor.specialty == 'Cardiology'
        
        # Test duplicate email registration
        response = client.post('/register', data={
            'email': 'new.doctor@example.com',
            'first_name': 'Another',
            'last_name': 'Doctor',
            'specialty': 'Neurology',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=True)
        
        # Check response for duplicate email
        assert response.status_code == 200
        assert b'An account with this Email already exists' in response.data

    def test_login_logout(self, client, doctor_factory):
        """Test login and logout functionality.
        
        Verifies that a doctor can successfully log in with valid credentials
        and log out. Also tests login failures with incorrect password and
        non-existent account.
        
        Args:
            client: Flask test client
            doctor_factory: Factory to create test doctor instances
        """
        from app import db
        
        # Create a doctor for login testing
        doctor = doctor_factory(email='login.test@example.com')
        
        # Make sure the doctor is properly saved
        db.session.flush()
        db.session.refresh(doctor)
        
        # Test login with correct credentials
        response = client.post('/login', data={
            'email': 'login.test@example.com',
            'password': 'Password123!'
        }, follow_redirects=True)
        
        # Check successful login
        assert response.status_code == 200
        assert b'Dashboard' in response.data  # Successfully logged in users see the dashboard
          # Test logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        # Check for logout confirmation in English or Italian
        assert b'You have been disconnected' in response.data or b'disconnesso' in response.data
        
        # Test login with incorrect password
        response = client.post('/login', data={
            'email': 'login.test@example.com',
            'password': 'WrongPassword!'
        }, follow_redirects=True)
        
        # Check failed login
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
        
        # Test login with non-existent account
        response = client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'Password123!'
        }, follow_redirects=True)
        
        # Check failed login
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_api_login(self, client, doctor_factory):
        """Test API login endpoint and JWT token generation.
        
        Verifies that the API login endpoint correctly generates JWT tokens
        for valid credentials and returns appropriate errors for invalid credentials.
        
        Args:
            client: Flask test client
            doctor_factory: Factory to create test doctor instances
        """
        # Create a doctor for API login testing
        doctor = doctor_factory(email='api.login@example.com')
        
        # Test successful API login
        response = client.post('/api/login', json={
            'email': 'api.login@example.com',
            'password': 'Password123!'
        })
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'doctor' in data
        assert data['doctor']['email'] == 'api.login@example.com'
        
        # Test API login with incorrect credentials
        response = client.post('/api/login', json={
            'email': 'api.login@example.com',
            'password': 'WrongPassword!'
        })
        
        # Check response
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid email or password' in data['error']

    def test_token_refresh(self, client, doctor_factory):
        """Test JWT token refresh endpoint.
        
        Verifies that a valid refresh token can be used to obtain a new access token
        and that invalid refresh tokens are properly rejected.
        
        Args:
            client: Flask test client
            doctor_factory: Factory to create test doctor instances
        """
        # Create a doctor for API login testing
        doctor = doctor_factory(email='refresh.test@example.com')
        
        # Get initial tokens
        response = client.post('/api/login', json={
            'email': 'refresh.test@example.com',
            'password': 'Password123!'
        })
        
        data = json.loads(response.data)
        refresh_token = data['refresh_token']
        
        # Use refresh token to get new access token
        response = client.post('/api/refresh-token', headers={
            'Authorization': f'Bearer {refresh_token}'
        })
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        
        # Test with invalid refresh token
        response = client.post('/api/refresh-token', headers={
            'Authorization': 'Bearer invalid_token'
        })
        
        # Check response
        assert response.status_code == 422  # JWT extended returns 422 for invalid tokens

    def test_protected_routes(self, client, doctor_factory):
        """Test access to protected routes with and without authentication.
        
        Verifies that unauthenticated users are redirected to the login page when
        trying to access protected routes, and that authenticated users can access
        protected routes successfully.
        
        Args:
            client: Flask test client
            doctor_factory: Factory to create test doctor instances
        """
        from app import db
        
        # Try accessing protected route without login
        response = client.get('/dashboard', follow_redirects=True)
          # Should redirect to login page
        assert response.status_code == 200
        # Check for login form in English or Italian
        assert b'login' in response.data.lower() or b'accedi' in response.data.lower()
        
        # Login
        doctor = doctor_factory(email='protected.test@example.com')
        
        # Make sure the doctor is properly saved
        db.session.flush()
        db.session.refresh(doctor)
        
        # Actual login with follow_redirects to reach the dashboard
        login_response = client.post('/login', data={
            'email': 'protected.test@example.com',
            'password': 'Password123!'
        }, follow_redirects=True)
        
        # Verify that login was successful
        assert login_response.status_code == 200
        assert b'Dashboard' in login_response.data
        
        # Try accessing protected route with login
        response = client.get('/dashboard')
        
        # Should allow access
        assert response.status_code == 200
        assert b'Dashboard' in response.data

    def test_api_protected_routes(self, client, doctor_factory):
        """Test access to protected API routes with and without JWT tokens.
        
        Verifies that unauthorized requests to protected API endpoints are rejected
        with a 401 status code, and that requests with valid JWT tokens are accepted.
        
        Args:
            client: Flask test client
            doctor_factory: Factory to create test doctor instances
        """
        # Try accessing protected API route without token
        response = client.get('/api/patients')
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        
        # Login to get token
        doctor = doctor_factory(email='api.protected@example.com')
        auth_response = client.post('/api/login', json={
            'email': 'api.protected@example.com',
            'password': 'Password123!'
        })
        
        data = json.loads(auth_response.data)
        access_token = data['access_token']
        
        # Access protected API route with token
        response = client.get('/api/patients', headers={
            'Authorization': f'Bearer {access_token}'
        })
        
        # Should allow access
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'patients' in data
