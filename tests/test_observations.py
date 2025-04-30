"""
Test module for VitaLink observations functionality.
"""
import pytest
import json
from datetime import datetime, timedelta

from app.models import VitalObservation, VitalSignType


class TestObservations:
    """Test cases for observations functionality."""
    
    def test_add_vital_observation(self, logged_in_client, doctor_with_patient, patient):
        """Test adding a vital observation."""
        # Prepare observation data
        observation_data = {
            "patient_id": patient.id,
            "vital_type": "heart_rate",
            "content": "Heart rate is within normal range (60-80 bpm)",
            "start_date": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        # Send a POST request to add the observation
        response = logged_in_client.post(
            "/observations/add",
            json=observation_data,
            content_type="application/json"
        )
        
        # Check if the observation was added successfully
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["observation"]["content"] == observation_data["content"]
        assert data["observation"]["vital_type"] == observation_data["vital_type"]
    
    def test_add_vital_observation_validation(self, logged_in_client, doctor_with_patient, patient):
        """Test validation when adding a vital observation."""
        # Prepare observation data with missing fields
        observation_data = {
            "patient_id": patient.id,
            "vital_type": "heart_rate",
            # Missing content
            "start_date": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S"),
            # Missing end_date
        }
        
        # Send a POST request to add the observation
        response = logged_in_client.post(
            "/observations/add",
            json=observation_data,
            content_type="application/json"
        )
        
        # Check if the validation caught the missing fields
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "content" in data["message"].lower()
        
        # Test with invalid vital type
        observation_data = {
            "patient_id": patient.id,
            "vital_type": "invalid_type",
            "content": "Test content",
            "start_date": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        response = logged_in_client.post(
            "/observations/add",
            json=observation_data,
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "vital_type" in data["message"].lower()
    
    def test_delete_vital_observation(self, logged_in_client, doctor_with_patient, patient, session):
        """Test deleting a vital observation."""
        # Create a vital observation
        observation = VitalObservation(
            patient_id=patient.id,
            doctor_id=doctor_with_patient.id,
            vital_type=VitalSignType.HEART_RATE,
            content="Test observation to delete",
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        session.add(observation)
        session.commit()
        
        # Send a DELETE request to delete the observation
        response = logged_in_client.delete(
            f"/observations/{observation.id}"
        )
        
        # Check if the observation was deleted successfully
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["message"] == "Observation deleted successfully"
        
        # Check if the observation was actually deleted from the database
        deleted_obs = session.query(VitalObservation).filter_by(id=observation.id).first()
        assert deleted_obs is None
    
    def test_delete_nonexistent_observation(self, logged_in_client):
        """Test deleting a nonexistent observation."""
        # Send a DELETE request for a nonexistent observation
        response = logged_in_client.delete("/observations/9999")
        
        # Check if the request was handled correctly
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert data["message"] == "Observation not found"
    
    def test_get_observations_for_patient(self, logged_in_client, doctor_with_patient, patient, session):
        """Test retrieving observations for a patient."""
        # Create some observations
        heart_rate_obs = VitalObservation(
            patient_id=patient.id,
            doctor_id=doctor_with_patient.id,
            vital_type=VitalSignType.HEART_RATE,
            content="Heart rate observations",
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        steps_obs = VitalObservation(
            patient_id=patient.id,
            doctor_id=doctor_with_patient.id,
            vital_type=VitalSignType.STEPS,
            content="Steps observations",
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        session.add(heart_rate_obs)
        session.add(steps_obs)
        session.commit()
        
        # Send a GET request to get heart rate observations
        response = logged_in_client.get(
            f"/observations/{patient.id}/heart_rate"
        )
        
        # Check if the request was successful
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert len(data["observations"]) >= 1
        
        # Verify the heart rate observation is in the response
        heart_rate_found = False
        for obs in data["observations"]:
            if obs["content"] == "Heart rate observations":
                heart_rate_found = True
                assert obs["vital_type"] == "heart_rate"
                break
        
        assert heart_rate_found, "Heart rate observation not found in response"
        
        # Send a GET request to get steps observations
        response = logged_in_client.get(
            f"/observations/{patient.id}/steps"
        )
        
        # Check if the request was successful
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert len(data["observations"]) >= 1
        
        # Verify the steps observation is in the response
        steps_found = False
        for obs in data["observations"]:
            if obs["content"] == "Steps observations":
                steps_found = True
                assert obs["vital_type"] == "steps"
                break
        
        assert steps_found, "Steps observation not found in response"
    
    def test_observations_page(self, logged_in_client, doctor_with_patient, patient):
        """Test the observations page."""
        # Access the observations page
        response = logged_in_client.get(f"/patient/{patient.id}/observations")
        
        # Check if the page loaded successfully
        assert response.status_code == 200
        assert b"Observations" in response.data
        assert bytes(patient.first_name, 'utf-8') in response.data
        assert bytes(patient.last_name, 'utf-8') in response.data
