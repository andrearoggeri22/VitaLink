"""
Test module for VitaLink authentication functionality.
"""
import pytest
from flask import url_for

from app.models import Doctor


class TestAuthRoutes:
    """Test cases for authentication routes."""
    
    def test_login_page(self, client):
        """Test login page loads correctly."""
        # Access the login page
        response = client.get("/login")
        
        # Check if the page loaded successfully
        assert response.status_code == 200
        assert b"VitaLink" in response.data
        assert b"Email" in response.data
        assert b"Password" in response.data
        assert b"Login" in response.data
    
    def test_successful_login(self, client, doctor):
        """Test successful login with valid credentials."""
        # Send a POST request to the login route
        response = client.post(
            "/login",
            data={
                "email": doctor.email,
                "password": "password",
                "remember": False
            },
            follow_redirects=True
        )
        
        # Check if the login was successful and we were redirected to the dashboard
        assert response.status_code == 200
        assert b"Dashboard" in response.data
    
    def test_login_with_invalid_credentials(self, client, doctor):
        """Test login with invalid credentials."""
        # Send a POST request to the login route with incorrect password
        response = client.post(
            "/login",
            data={
                "email": doctor.email,
                "password": "wrong_password",
                "remember": False
            },
            follow_redirects=True
        )
        
        # Check if login failed and we are still on the login page
        assert response.status_code == 200
        assert b"Invalid email or password" in response.data
        assert b"Login" in response.data
    
    def test_login_with_nonexistent_user(self, client):
        """Test login with a nonexistent user."""
        # Send a POST request to the login route with a nonexistent email
        response = client.post(
            "/login",
            data={
                "email": "nonexistent@example.com",
                "password": "password",
                "remember": False
            },
            follow_redirects=True
        )
        
        # Check if login failed and we are still on the login page
        assert response.status_code == 200
        assert b"Invalid email or password" in response.data
        assert b"Login" in response.data
    
    def test_logout(self, logged_in_client):
        """Test logging out."""
        # Send a GET request to the logout route
        response = logged_in_client.get(
            "/logout",
            follow_redirects=True
        )
        
        # Check if logout was successful and we are redirected to the login page
        assert response.status_code == 200
        assert b"Login" in response.data
        assert b"You have been logged out" in response.data
    
    def test_access_protected_page_when_not_logged_in(self, client):
        """Test accessing a protected page when not logged in."""
        # Try to access the dashboard
        response = client.get(
            "/",
            follow_redirects=True
        )
        
        # Check if we were redirected to the login page
        assert response.status_code == 200
        assert b"Login" in response.data
        assert b"Please log in to access this page" in response.data
    
    def test_remember_me_functionality(self, client, doctor, app):
        """Test the 'remember me' functionality."""
        with app.test_client() as test_client:
            # Login with 'remember me' checked
            response = test_client.post(
                "/login",
                data={
                    "email": doctor.email,
                    "password": "password",
                    "remember": True
                },
                follow_redirects=True
            )
            
            # Check if the login was successful
            assert response.status_code == 200
            assert b"Dashboard" in response.data
            
            # Check if the remember cookie was set
            cookies = {cookie.name: cookie.value for cookie in test_client.cookie_jar}
            assert any('remember_token' in cookie_name for cookie_name in cookies)


class TestPasswordManagement:
    """Test cases for password management functionality."""
    
    def test_password_hashing(self, session):
        """Test that passwords are properly hashed."""
        # Create a doctor with a password
        doctor = Doctor(
            email="doctor@example.com",
            first_name="Test",
            last_name="Doctor"
        )
        doctor.set_password("password")
        
        # Check that the password is hashed
        assert doctor.password_hash != "password"
        assert doctor.check_password("password")
        assert not doctor.check_password("wrong_password")
        
        # Add the doctor to the database
        session.add(doctor)
        session.commit()
        
        # Retrieve the doctor from the database
        saved_doctor = session.query(Doctor).filter_by(email="doctor@example.com").first()
        
        # Check that the password hash was saved correctly
        assert saved_doctor.password_hash == doctor.password_hash
        assert saved_doctor.check_password("password")


class TestAccessControl:
    """Test cases for access control functionality."""
    
    def test_access_to_protected_routes(self, logged_in_client):
        """Test access to protected routes when logged in."""
        # Access dashboard
        response = logged_in_client.get("/")
        assert response.status_code == 200
        assert b"Dashboard" in response.data
        
        # Access patients page
        response = logged_in_client.get("/patients")
        assert response.status_code == 200
        assert b"Patients" in response.data
        
        # Access audit logs page
        response = logged_in_client.get("/audit/logs")
        assert response.status_code == 200
        assert b"Audit" in response.data
        
    def test_redirect_after_login(self, client, doctor):
        """Test redirection after login."""
        # Try to access a protected page
        client.get("/patients", follow_redirects=False)
        
        # Login and check if we're redirected to the page we tried to access
        response = client.post(
            "/login",
            data={
                "email": doctor.email,
                "password": "password",
                "remember": False
            },
            follow_redirects=True
        )
        
        # Check if we were redirected to the page we tried to access
        assert response.status_code == 200
        assert b"Patients" in response.data
