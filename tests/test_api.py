"""
Test module for VitaLink API endpoints.
"""
import pytest
import json
from datetime import datetime, timedelta

from app.models import VitalSignType, Patient, VitalObservation


class TestPatientAPI:
    """Test cases for patient API endpoints."""
    
    def test_get_patients_api(self, logged_in_client, doctor_with_patient, patient):
        """Test retrieving patients via API."""
        # Send a GET request to the patients API
        response = logged_in_client.get("/api/patients")
        
        # Check if the request was successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check if the response contains the patient
        assert "patients" in data
        assert len(data["patients"]) >= 1
        
        # Find our test patient in the response
        patient_found = False
        for p in data["patients"]:
            if p["id"] == patient.id:
                patient_found = True
                assert p["first_name"] == patient.first_name
                assert p["last_name"] == patient.last_name
                break
        
        assert patient_found, "Test patient not found in API response"
    
    def test_get_patient_detail_api(self, logged_in_client, doctor_with_patient, patient):
        """Test retrieving patient detail via API."""
        # Send a GET request to the patient detail API
        response = logged_in_client.get(f"/api/patient/{patient.id}")
        
        # Check if the request was successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check if the response contains the patient details
        assert "patient" in data
        assert data["patient"]["id"] == patient.id
        assert data["patient"]["first_name"] == patient.first_name
        assert data["patient"]["last_name"] == patient.last_name
    
    def test_patient_not_found_api(self, logged_in_client):
        """Test retrieving a nonexistent patient."""
        # Send a GET request for a patient that doesn't exist
        response = logged_in_client.get("/api/patient/9999")
        
        # Check if the request failed correctly
        assert response.status_code == 404
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check if the response contains an error message
        assert "error" in data
        assert data["error"] == "Patient not found"


class TestVitalsAPI:
    """Test cases for vitals API endpoints."""
    
    def test_get_vital_data_api(self, logged_in_client, doctor_with_patient, patient, session):
        """Test retrieving vital data via API."""
        # Create some vital data
        current_time = datetime.utcnow()
        
        # Heart rate data
        hr_data = VitalObservation(
            patient_id=patient.id,
            doctor_id=doctor_with_patient.id,
            vital_type=VitalSignType.HEART_RATE,
            content="Normal heart rate",
            start_date=current_time - timedelta(days=7),
            end_date=current_time
        )
        
        # Steps data
        steps_data = VitalObservation(
            patient_id=patient.id,
            doctor_id=doctor_with_patient.id,
            vital_type=VitalSignType.STEPS,
            content="Daily steps count",
            start_date=current_time - timedelta(days=7),
            end_date=current_time
        )
        
        # Add the vital data to the database
        session.add(hr_data)
        session.add(steps_data)
        session.commit()
        
        # Send a GET request to get heart rate data
        response = logged_in_client.get(f"/api/patient/{patient.id}/vitals/heart_rate?period=7")
        
        # Check if the request was successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check if the response contains the vital data
        assert "observations" in data
        assert len(data["observations"]) >= 1
        
        # Check the heart rate observation
        hr_obs_found = False
        for obs in data["observations"]:
            if obs["content"] == "Normal heart rate":
                hr_obs_found = True
                assert obs["vital_type"] == "heart_rate"
                break
        
        assert hr_obs_found, "Heart rate observation not found in API response"
        
        # Send a GET request to get steps data
        response = logged_in_client.get(f"/api/patient/{patient.id}/vitals/steps?period=7")
        
        # Check if the request was successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check if the response contains the vital data
        assert "observations" in data
        assert len(data["observations"]) >= 1
        
        # Check the steps observation
        steps_obs_found = False
        for obs in data["observations"]:
            if obs["content"] == "Daily steps count":
                steps_obs_found = True
                assert obs["vital_type"] == "steps"
                break
        
        assert steps_obs_found, "Steps observation not found in API response"
    
    def test_add_vital_observation_api(self, logged_in_client, doctor_with_patient, patient):
        """Test adding a vital observation via API."""
        # Prepare the observation data
        observation_data = {
            "patient_id": patient.id,
            "vital_type": "heart_rate",
            "content": "Test heart rate observation",
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
        
        # Send a POST request to the observation API
        response = logged_in_client.post(
            "/observations/add",
            json=observation_data,
            content_type="application/json"
        )
        
        # Check if the request was successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check if the observation was added successfully
        assert data["status"] == "success"
        assert "observation" in data
        assert data["observation"]["content"] == "Test heart rate observation"
        assert data["observation"]["vital_type"] == "heart_rate"
    
    def test_delete_vital_observation_api(self, logged_in_client, vital_observation):
        """Test deleting a vital observation via API."""
        # Send a DELETE request to the observation API
        response = logged_in_client.delete(f"/observations/{vital_observation.id}")
        
        # Check if the request was successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check if the observation was deleted successfully
        assert data["status"] == "success"
        assert data["message"] == "Observation deleted successfully"


class TestReportsAPI:
    """Test cases for reports API endpoints."""
    
    def test_generate_report_data(self, logged_in_client, doctor_with_patient, patient, note, vital_observation):
        """Test generating report data via API."""
        # Prepare the report request data
        report_data = {
            "patient_id": patient.id,
            "report_title": "Test Report",
            "include_personal_info": True,
            "include_notes": True,
            "selected_notes": [note.id],
            "include_vital_types": True,
            "selected_vital_types": ["heart_rate"],
            "charts_heart_rate": ["7d"],
            "selected_observations": [vital_observation.id]
        }
        
        # Send a POST request to the report generation API
        response = logged_in_client.post(
            "/api/generate_report",
            json=report_data,
            content_type="application/json"
        )
        
        # Check if the request was successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check if the report data was generated successfully
        assert "report_data" in data
        assert data["report_data"]["patient"]["id"] == patient.id
        assert data["report_data"]["title"] == "Test Report"
        assert "notes" in data["report_data"]
        assert len(data["report_data"]["notes"]) >= 1
        assert "vital_types" in data["report_data"]
        assert "heart_rate" in [vt["id"] for vt in data["report_data"]["vital_types"]]
