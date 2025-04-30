"""
Test module for VitaLink health platforms integration functionality.
"""
import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.models import HealthPlatform, HealthPlatformLink, Patient


class TestHealthPlatformLinks:
    """Test cases for health platform links functionality."""
    
    def test_create_health_platform_link(self, doctor, patient, session):
        """Test creating a health platform link."""
        # Create a health platform link
        link = HealthPlatformLink(
            patient_id=patient.id,
            doctor_id=doctor.id,
            platform=HealthPlatform.FITBIT
        )
        
        # Add the link to the database
        session.add(link)
        session.commit()
        
        # Retrieve the link from the database
        saved_link = session.query(HealthPlatformLink).first()
        
        # Check the link's attributes
        assert saved_link is not None
        assert saved_link.patient_id == patient.id
        assert saved_link.doctor_id == doctor.id
        assert saved_link.platform == HealthPlatform.FITBIT
        assert saved_link.uuid is not None
        assert not saved_link.used
        
        # The link should not be expired
        assert not saved_link.is_expired()
        
        # Convert the link to a dictionary
        link_dict = saved_link.to_dict()
        
        # Check the dictionary
        assert link_dict["patient_id"] == patient.id
        assert link_dict["doctor_id"] == doctor.id
        assert link_dict["platform"] == HealthPlatform.FITBIT.value
        assert not link_dict["used"]
    
    def test_link_expiration(self, doctor, patient, session):
        """Test health platform link expiration."""
        # Create a health platform link that is already expired
        link = HealthPlatformLink(
            patient_id=patient.id,
            doctor_id=doctor.id,
            platform=HealthPlatform.FITBIT,
            created_at=datetime.utcnow() - timedelta(days=2),
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        
        # Add the link to the database
        session.add(link)
        session.commit()
        
        # Check if the link is expired
        assert link.is_expired()


class TestHealthPlatformViews:
    """Test cases for health platform views."""
    
    def test_health_connect_page(self, logged_in_client, doctor_with_patient, patient):
        """Test health connect page."""
        # Create a health platform link
        with logged_in_client.application.app_context():
            link = HealthPlatformLink(
                patient_id=patient.id,
                doctor_id=doctor_with_patient.id,
                platform=HealthPlatform.FITBIT
            )
            logged_in_client.application.extensions['sqlalchemy'].db.session.add(link)
            logged_in_client.application.extensions['sqlalchemy'].db.session.commit()
        
        # Access the health connect page using the link's UUID
        response = logged_in_client.get(f"/health/connect/{link.uuid}")
        
        # Check if the page loaded successfully
        assert response.status_code == 200
        assert b"VitaLink" in response.data
        assert b"health platform" in response.data.lower()
        assert bytes(patient.first_name, 'utf-8') in response.data
    
    @patch('app.health_platforms.requests.get')
    def test_check_connection_api(self, mock_get, logged_in_client, doctor_with_patient, patient, session):
        """Test checking health platform connection status."""
        # Mock the response from the health platform API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Setup a patient with a connected health platform
        patient.connected_platform = HealthPlatform.FITBIT
        patient.platform_access_token = "fake-access-token"
        patient.platform_refresh_token = "fake-refresh-token"
        patient.platform_token_expires_at = datetime.utcnow() + timedelta(days=1)
        session.commit()
        
        # Send a GET request to check connection status
        response = logged_in_client.get(f"/health/check_connection/{patient.id}")
        
        # Check if the request was successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check the connection status
        assert data["connected"]
        assert data["platform"] == HealthPlatform.FITBIT.value
        
    @patch('app.health_platforms.requests.post')
    @patch('app.health_platforms.requests.get')
    def test_generate_platform_link(self, mock_get, mock_post, logged_in_client, doctor_with_patient, patient):
        """Test generating a health platform link."""
        # Send a POST request to generate a link
        response = logged_in_client.post(
            "/health/generate_link",
            data={
                "patient_id": patient.id,
                "platform": "fitbit"
            },
            follow_redirects=True
        )
        
        # Check if the request was successful
        assert response.status_code == 200
        assert b"Link generated successfully" in response.data
        
        # Verify that the link was created in the database
        with logged_in_client.application.app_context():
            link = logged_in_client.application.extensions['sqlalchemy'].db.session.query(HealthPlatformLink).filter_by(patient_id=patient.id).first()
            assert link is not None
            assert link.platform == HealthPlatform.FITBIT


class TestHealthPlatformIntegration:
    """Test cases for health platform integration."""
    
    @patch('app.health_platforms.requests.get')
    def test_disconnect_platform(self, mock_get, logged_in_client, doctor_with_patient, patient, session):
        """Test disconnecting a health platform."""
        # Setup a patient with a connected health platform
        patient.connected_platform = HealthPlatform.FITBIT
        patient.platform_access_token = "fake-access-token"
        patient.platform_refresh_token = "fake-refresh-token"
        patient.platform_token_expires_at = datetime.utcnow() + timedelta(days=1)
        session.commit()
        
        # Mock the response from the health platform API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Send a POST request to disconnect the platform
        response = logged_in_client.post(
            f"/health/disconnect/{patient.id}",
            follow_redirects=True
        )
        
        # Check if the request was successful
        assert response.status_code == 200
        assert b"disconnected" in response.data.lower()
        
        # Verify that the platform was disconnected in the database
        session.refresh(patient)
        assert patient.connected_platform is None
        assert patient.platform_access_token is None
        assert patient.platform_refresh_token is None
        assert patient.platform_token_expires_at is None
    
    @patch('app.health_platforms_config.FITBIT_CONFIG', {
        'auth_base_url': 'https://www.fitbit.com/oauth2/authorize',
        'token_url': 'https://api.fitbit.com/oauth2/token',
        'api_base_url': 'https://api.fitbit.com',
        'scope': ['activity', 'heartrate', 'sleep', 'weight', 'nutrition', 'respiratory_rate', 'temperature'],
        'client_id': 'test-client-id',
        'client_secret': 'test-client-secret',
        'redirect_uri': 'https://example.com/callback'
    })
    def test_fitbit_oauth_redirect(self, logged_in_client, health_platform_link):
        """Test Fitbit OAuth redirect."""
        # Access the Fitbit OAuth redirect endpoint
        response = logged_in_client.get(f"/health/authorize/fitbit/{health_platform_link.uuid}")
        
        # Check if we get redirected to the Fitbit authorization page
        assert response.status_code == 302  # HTTP 302 Found (redirect)
        assert "fitbit.com/oauth2/authorize" in response.location
        assert "client_id=test-client-id" in response.location
        assert "scope=" in response.location
        assert "redirect_uri=" in response.location
