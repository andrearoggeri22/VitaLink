"""
Test module for VitaLink views functionality.
"""
import pytest
from flask import url_for

from app.models import Patient, Note


class TestDashboardViews:
    """Test cases for dashboard views."""
    
    def test_dashboard_access(self, logged_in_client):
        """Test dashboard access when logged in."""
        # Access the dashboard
        response = logged_in_client.get("/")
        
        # Check if the dashboard loaded successfully
        assert response.status_code == 200
        assert b"Dashboard" in response.data
    
    def test_dashboard_statistics(self, logged_in_client, doctor_with_patient):
        """Test dashboard statistics display correctly."""
        # Access the dashboard
        response = logged_in_client.get("/")
        
        # Check if the dashboard shows patient statistics
        assert response.status_code == 200
        assert b"Patients" in response.data
        # We should have at least 1 patient
        assert b"1" in response.data


class TestPatientViews:
    """Test cases for patient views."""
    
    def test_patients_list(self, logged_in_client, doctor_with_patient, patient):
        """Test patients list view."""
        # Access the patients list
        response = logged_in_client.get("/patients")
        
        # Check if the patients list loaded successfully
        assert response.status_code == 200
        assert b"Patients" in response.data
        assert bytes(patient.first_name, 'utf-8') in response.data
        assert bytes(patient.last_name, 'utf-8') in response.data
    
    def test_patient_detail(self, logged_in_client, doctor_with_patient, patient):
        """Test patient detail view."""
        # Access the patient detail page
        response = logged_in_client.get(f"/patient/{patient.id}")
        
        # Check if the patient detail page loaded successfully
        assert response.status_code == 200
        assert bytes(patient.first_name, 'utf-8') in response.data
        assert bytes(patient.last_name, 'utf-8') in response.data
    
    def test_add_patient_form(self, logged_in_client):
        """Test add patient form view."""
        # Access the add patient form
        response = logged_in_client.get("/patients/add")
        
        # Check if the add patient form loaded successfully
        assert response.status_code == 200
        assert b"Add New Patient" in response.data
        assert b"First Name" in response.data
        assert b"Last Name" in response.data
        assert b"Date of Birth" in response.data
        assert b"Gender" in response.data
        assert b"Contact Number" in response.data
        assert b"Address" in response.data
        assert b"Save" in response.data
    
    def test_add_patient(self, logged_in_client):
        """Test adding a new patient."""
        # Send a POST request to add a new patient
        response = logged_in_client.post(
            "/patients/add",
            data={
                "first_name": "New",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "gender": "Female",
                "contact_number": "123-456-7890",
                "address": "123 Main St"
            },
            follow_redirects=True
        )
        
        # Check if the patient was added successfully
        assert response.status_code == 200
        assert b"Patient added successfully" in response.data
        assert b"New" in response.data
        assert b"Patient" in response.data
    
    def test_edit_patient_form(self, logged_in_client, doctor_with_patient, patient):
        """Test edit patient form view."""
        # Access the edit patient form
        response = logged_in_client.get(f"/patient/{patient.id}/edit")
        
        # Check if the edit patient form loaded successfully
        assert response.status_code == 200
        assert b"Edit Patient" in response.data
        assert bytes(patient.first_name, 'utf-8') in response.data
        assert bytes(patient.last_name, 'utf-8') in response.data
        assert b"Save" in response.data
    
    def test_edit_patient(self, logged_in_client, doctor_with_patient, patient):
        """Test editing a patient."""
        # Send a POST request to edit the patient
        response = logged_in_client.post(
            f"/patient/{patient.id}/edit",
            data={
                "first_name": "Updated",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "gender": "Female",
                "contact_number": "123-456-7890",
                "address": "123 Main St"
            },
            follow_redirects=True
        )
        
        # Check if the patient was updated successfully
        assert response.status_code == 200
        assert b"Patient updated successfully" in response.data
        assert b"Updated" in response.data
        assert b"Patient" in response.data
    
    def test_delete_patient(self, logged_in_client, doctor_with_patient, patient):
        """Test deleting a patient."""
        # Send a POST request to delete the patient
        response = logged_in_client.post(
            f"/patient/{patient.id}/delete",
            follow_redirects=True
        )
        
        # Check if the patient was deleted successfully
        assert response.status_code == 200
        assert b"Patient deleted successfully" in response.data


class TestNoteViews:
    """Test cases for note views."""
    
    def test_add_note(self, logged_in_client, doctor_with_patient, patient):
        """Test adding a new note."""
        # Send a POST request to add a new note
        response = logged_in_client.post(
            f"/patient/{patient.id}/notes/add",
            data={
                "content": "Test note content"
            },
            follow_redirects=True
        )
        
        # Check if the note was added successfully
        assert response.status_code == 200
        assert b"Note added successfully" in response.data
        assert b"Test note content" in response.data
    
    def test_delete_note(self, logged_in_client, note):
        """Test deleting a note."""
        # Send a POST request to delete the note
        response = logged_in_client.post(
            f"/note/{note.id}/delete",
            follow_redirects=True
        )
        
        # Check if the note was deleted successfully
        assert response.status_code == 200
        assert b"Note deleted successfully" in response.data


class TestVitalViews:
    """Test cases for vital sign views."""
    
    def test_vitals_page(self, logged_in_client, doctor_with_patient, patient):
        """Test vital signs page."""
        # Access the vital signs page
        response = logged_in_client.get(f"/patient/{patient.id}/vitals")
        
        # Check if the vital signs page loaded successfully
        assert response.status_code == 200
        assert b"Vital Signs" in response.data
        assert bytes(patient.first_name, 'utf-8') in response.data
        assert bytes(patient.last_name, 'utf-8') in response.data
    
    def test_add_vital_observation(self, logged_in_client, doctor_with_patient, patient):
        """Test adding a new vital observation."""
        # Send a POST request to the observation API
        response = logged_in_client.post(
            f"/observations/add",
            json={
                "patient_id": patient.id,
                "vital_type": "heart_rate",
                "content": "Test heart rate observation",
                "start_date": "2023-01-01T00:00:00",
                "end_date": "2023-01-02T00:00:00"
            },
            follow_redirects=True
        )
        
        # Check if the observation was added successfully
        assert response.status_code == 200
        assert b"success" in response.data
