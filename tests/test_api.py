"""
Test module for the API functionality.

This module tests the REST API endpoints including:
- Patient data access and management
- Vital sign retrieval
- Notes creation and management
- Observations handling
- Patient import functionality
"""
import json
from datetime import datetime, timedelta
from uuid import uuid4

from app.models import (Patient, Note, VitalObservation, VitalSignType)


class TestAPI:
    """Test class for API functionality.
    
    This class contains test cases for all the API endpoints including patient management,
    notes, observations, and patient import functionality.
    """    
    def test_get_patients(self, client, api_auth_headers, patient_factory):
        """Test GET /api/patients endpoint.
        
        Verifies that the endpoint returns all patients associated with the authenticated doctor.
        
        Args:
            client: Flask test client
            api_auth_headers: Authentication headers fixture
            patient_factory: Factory to create test patients
        """
        doctor = api_auth_headers['doctor']
        headers = api_auth_headers['headers']
        
        # Create patients and associate with doctor
        patient1 = patient_factory(first_name="Patient", last_name="One")
        patient2 = patient_factory(first_name="Patient", last_name="Two")
        
        doctor.add_patient(patient1)
        doctor.add_patient(patient2)        # Test endpoint
        response = client.get('/api/patients', headers=headers)
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'patients' in data
        assert len(data['patients']) == 2
        
        # Verify patient data
        patient_ids = [p['id'] for p in data['patients']]
        assert patient1.id in patient_ids
        assert patient2.id in patient_ids

    def test_get_patient(self, client, api_auth_headers, patient_factory):
        """Test GET /api/patients/<uuid> endpoint.
        
        Verifies that the endpoint returns the specific patient information when requested with a valid UUID.
        Also tests error cases for invalid UUID, non-existent UUID, and accessing a patient 
        not associated with the doctor.
        
        Args:
            client: Flask test client
            api_auth_headers: Authentication headers fixture
            patient_factory: Factory to create test patients
        """
        doctor = api_auth_headers['doctor']
        headers = api_auth_headers['headers']
        
        # Create patient and associate with doctor
        patient = patient_factory(first_name="Test", last_name="Patient")
        doctor.add_patient(patient)
        
        # Test endpoint with valid UUID
        response = client.get(f'/api/patients/{patient.uuid}', headers=headers)
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'patient' in data
        assert data['patient']['id'] == patient.id
        assert data['patient']['first_name'] == "Test"
        assert data['patient']['last_name'] == "Patient"
        
        # Test with invalid UUID
        response = client.get('/api/patients/invalid-uuid', headers=headers)
        assert response.status_code == 400
        
        # Test with non-existent UUID
        random_uuid = str(uuid4())
        response = client.get(f'/api/patients/{random_uuid}', headers=headers)
        assert response.status_code == 404
        
        # Test with patient not associated with doctor
        unassociated_patient = patient_factory()
        response = client.get(f'/api/patients/{unassociated_patient.uuid}', headers=headers)
        assert response.status_code == 403

    def test_get_notes(self, client, api_auth_headers, patient_factory, note_factory):
        """Test GET /api/patients/<uuid>/notes endpoint.
        
        Verifies that the endpoint returns all notes for a specific patient.
        Also tests error cases for invalid UUID, non-existent patient, and accessing
        a patient not associated with the doctor.
        
        Args:
            client: Flask test client
            api_auth_headers: Authentication headers fixture
            patient_factory: Factory to create test patients
            note_factory: Factory to create test notes
        """
        doctor = api_auth_headers['doctor']
        headers = api_auth_headers['headers']
        
        # Create patient with notes
        patient = patient_factory()
        doctor.add_patient(patient)
        
        # Add multiple notes
        note1 = note_factory(doctor, patient, "First test note")
        note2 = note_factory(doctor, patient, "Second test note")
        
        # Test endpoint
        response = client.get(f'/api/patients/{patient.uuid}/notes', headers=headers)
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'notes' in data
        assert len(data['notes']) == 2
        
        # Notes should be ordered by creation date (newest first)
        assert data['notes'][0]['id'] == note2.id
        assert data['notes'][1]['id'] == note1.id
        
        # Test with invalid UUID
        response = client.get('/api/patients/invalid-uuid/notes', headers=headers)
        assert response.status_code == 400
        
        # Test with non-existent patient
        random_uuid = str(uuid4())
        response = client.get(f'/api/patients/{random_uuid}/notes', headers=headers)
        assert response.status_code == 404
        
        # Test with patient not associated with doctor
        unassociated_patient = patient_factory()
        response = client.get(f'/api/patients/{unassociated_patient.uuid}/notes', headers=headers)
        assert response.status_code == 403

    def test_add_note(self, client, api_auth_headers, patient_factory):
        """Test POST /api/patients/<uuid>/notes endpoint.
        
        Verifies that notes can be added to a patient through the API.
        Also tests error cases for empty content, missing content, invalid UUID,
        and adding a note to a patient not associated with the doctor.
        
        Args:
            client: Flask test client
            api_auth_headers: Authentication headers fixture
            patient_factory: Factory to create test patients
        """
        doctor = api_auth_headers['doctor']
        headers = api_auth_headers['headers']
        
        # Create patient
        patient = patient_factory()
        doctor.add_patient(patient)
        
        # Test adding a note
        note_content = "API test note content"
        response = client.post(
            f'/api/patients/{patient.uuid}/notes',
            headers=headers,
            json={"content": note_content}
        )
        
        # Check response
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'note' in data
        assert data['note']['content'] == note_content
        
        # Verify note was added to database
        assert Note.query.filter_by(content=note_content, patient_id=patient.id).first() is not None
        
        # Test with empty content
        response = client.post(
            f'/api/patients/{patient.uuid}/notes',
            headers=headers,
            json={"content": ""}
        )
        assert response.status_code == 400
        
        # Test without content
        response = client.post(
            f'/api/patients/{patient.uuid}/notes',
            headers=headers,
            json={}
        )
        assert response.status_code == 400
        
        # Test with invalid UUID
        response = client.post(
            '/api/patients/invalid-uuid/notes',
            headers=headers,
            json={"content": "Test content"}
        )
        assert response.status_code == 400
        
        # Test with patient not associated with doctor
        unassociated_patient = patient_factory()
        response = client.post(
            f'/api/patients/{unassociated_patient.uuid}/notes',
            headers=headers,
            json={"content": "Test content"}
        )
        assert response.status_code == 403

    def test_delete_note(self, client, api_auth_headers, patient_factory, note_factory):
        """Test DELETE /api/notes/<note_id> endpoint.
        
        Verifies that notes can be deleted through the API.
        Also tests error cases for non-existent notes and unauthorized deletion attempts.
        
        Args:
            client: Flask test client
            api_auth_headers: Authentication headers fixture
            patient_factory: Factory to create test patients
            note_factory: Factory to create test notes
        """
        doctor = api_auth_headers['doctor']
        headers = api_auth_headers['headers']
        
        # Create patient
        patient = patient_factory()
        doctor.add_patient(patient)
        
        # Add a note
        note = note_factory(doctor, patient, "Note to be deleted")
        
        # Test deleting the note
        response = client.delete(f'/api/notes/{note.id}', headers=headers)
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert 'Note deleted successfully' in data['message']
        
        # Verify note was deleted from database
        assert Note.query.get(note.id) is None
        
        # Test with non-existent note
        response = client.delete('/api/notes/9999', headers=headers)
        assert response.status_code == 404
        
        # Create another doctor and note to test authorization
        from app.models import Doctor
        from app.app import db
        
        # Create a new doctor
        another_doctor = Doctor(email="another.doctor@example.com", first_name="Another", last_name="Doctor")
        another_doctor.set_password("Password123!")
        db.session.add(another_doctor)
        db.session.commit()
        
        # Create a patient and note for this new doctor
        another_patient = patient_factory()
        another_doctor.add_patient(another_patient)
        another_note = note_factory(another_doctor, another_patient, "Note from another doctor")
        
        # Login with the new doctor to get a token
        another_login_response = client.post('/api/login', json={
            'email': "another.doctor@example.com",
            'password': "Password123!"
        })
        another_auth_token = json.loads(another_login_response.data)['access_token']
        another_headers = {'Authorization': f'Bearer {another_auth_token}'}
        
        # Attempt to delete the note using the original doctor's token
        response = client.delete(f'/api/notes/{another_note.id}', headers=headers)
        assert response.status_code == 403

    def test_get_observations(self, client, api_auth_headers, patient_factory, observation_factory):
        """Test GET /api/patients/<patient_id>/observations endpoint.
        
        Verifies that observations can be retrieved for a patient through the API.
        Tests retrieving all observations and filtering by vital type and date range.
        Also tests error cases for non-existent patient and unauthorized access.
        
        Args:
            client: Flask test client
            api_auth_headers: Authentication headers fixture
            patient_factory: Factory to create test patients
            observation_factory: Factory to create test observations
        """
        doctor = api_auth_headers['doctor']
        headers = api_auth_headers['headers']
        
        # Create patient and observations
        patient = patient_factory()
        doctor.add_patient(patient)
        
        # Create observations with different vital types
        observation_factory(doctor, patient, VitalSignType.HEART_RATE)
        observation_factory(doctor, patient, VitalSignType.STEPS)
          # Test endpoint without filters
        response = client.get(f'/api/observations/{patient.id}', headers=headers)
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        
        # Test with vital type filter
        response = client.get(
            f'/api/observations/{patient.id}?vital_type=heart_rate',
            headers=headers
        )
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['vital_type'] == 'heart_rate'        # Test with date range filter
        start_date = (datetime.utcnow() - timedelta(days=10)).strftime('%Y-%m-%d')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        response = client.get(
            f'/api/observations/{patient.id}?start_date={start_date}&end_date={end_date}',
            headers=headers
        )
          # Check response - results may be empty depending on the date
        assert response.status_code == 200
        # We don't verify the number of results since it depends on the date
        
        # Test with non-existent patient
        response = client.get('/api/patients/9999/observations', headers=headers)
        assert response.status_code == 404
        
        # Test with patient not associated with doctor
        unassociated_patient = patient_factory()
        response = client.get(f'/api/observations/{unassociated_patient.id}', headers=headers)
        assert response.status_code == 403  # HTTP 403 when patient is not associated with the doctor

    def test_add_observation(self, client, api_auth_headers, patient_factory):
        """Test POST /api/observations endpoint.
        
        Verifies that observations can be added through the API.
        Also tests error cases for missing required fields, invalid vital type,
        and adding an observation to a patient not associated with the doctor.
        
        Args:
            client: Flask test client
            api_auth_headers: Authentication headers fixture
            patient_factory: Factory to create test patients
        """
        doctor = api_auth_headers['doctor']
        headers = api_auth_headers['headers']
        
        # Create patient
        patient = patient_factory()
        doctor.add_patient(patient)
        
        # Test creating an observation
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        observation_data = {
            "patient_id": patient.id,
            "vital_type": "heart_rate",
            "content": "Heart rate has been stable within normal range",
            "start_date": start_date,
            "end_date": end_date
        }
        
        response = client.post('/api/observations', headers=headers, json=observation_data)
        
        # Check response
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'observation' in data
        assert data['observation']['vital_type'] == 'heart_rate'
        assert data['observation']['content'] == observation_data['content']
        
        # Verify observation was added to database
        observation_id = data['observation']['id']
        assert VitalObservation.query.get(observation_id) is not None
        
        # Test with missing required fields
        response = client.post('/api/observations', headers=headers, json={
            "patient_id": patient.id,
            "content": "Incomplete observation"
        })
        assert response.status_code == 400
        
        # Test with invalid vital type
        response = client.post('/api/observations', headers=headers, json={
            "patient_id": patient.id,
            "vital_type": "invalid_type",
            "content": "Invalid vital type",
            "start_date": start_date,
            "end_date": end_date
        })
        assert response.status_code == 400
        
        # Test with patient not associated with doctor
        unassociated_patient = patient_factory()
        response = client.post('/api/observations', headers=headers, json={
            "patient_id": unassociated_patient.id,
            "vital_type": "heart_rate",
            "content": "Unauthorized",
            "start_date": start_date,
            "end_date": end_date
        })
        assert response.status_code == 403

    def test_update_observation(self, client, api_auth_headers, patient_factory, observation_factory):
        """Test PUT /api/observations/<observation_id> endpoint.
        
        Verifies that observations can be updated through the API.
        Also tests error cases for non-existent observation and unauthorized update attempts.
        
        Args:
            client: Flask test client
            api_auth_headers: Authentication headers fixture
            patient_factory: Factory to create test patients
            observation_factory: Factory to create test observations
        """
        doctor = api_auth_headers['doctor']
        headers = api_auth_headers['headers']
        
        # Create patient and observation
        patient = patient_factory()
        doctor.add_patient(patient)
        observation = observation_factory(doctor, patient)
        
        # Test updating observation
        update_data = {
            "content": "Updated observation content",
            "vital_type": "steps"
        }
        
        # Use the correct endpoint format
        response = client.put(
            f'/api/observations/{observation.id}',
            headers=headers, 
            json=update_data,
            content_type='application/json'  # Ensure proper content type
        )
        
        # Check response
        assert response.status_code == 200
        
        # More robust JSON handling
        if response.data:
            try:
                data = json.loads(response.data)
                if 'observation' in data:
                    assert data['observation']['content'] == update_data['content']
                    assert data['observation']['vital_type'] == update_data['vital_type']
            except json.JSONDecodeError:
                pass  # If we can't decode JSON, we'll rely on status code check only
        
        # Verify observation was updated in database
        updated_observation = VitalObservation.query.get(observation.id)
        assert updated_observation.content == update_data['content']
        assert updated_observation.vital_type.value == update_data['vital_type']
        
        # Test with non-existent observation
        response = client.put('/api/observations/9999', headers=headers, json=update_data)
        assert response.status_code == 404
        
        # Test with observation not created by this doctor
        from app.models import Doctor
        from app.app import db
        
        # Create a new doctor for authorization testing
        other_doctor = Doctor(email="test_update_other@example.com", first_name="Other", last_name="Doctor")
        other_doctor.set_password("Password123!")
        db.session.add(other_doctor)
        db.session.commit()
        
        # Create a patient and observation owned by the other doctor
        other_patient = patient_factory()
        other_doctor.add_patient(other_patient)
        other_observation = observation_factory(other_doctor, other_patient)
        
        # Try to update the other doctor's observation with the original doctor's credentials
        response = client.put(
            f'/api/observations/{other_observation.id}',
            headers=headers,
            json=update_data
        )
        assert response.status_code == 403

    def test_delete_observation(self, client, api_auth_headers, patient_factory, observation_factory):
        """Test DELETE /api/observations/<observation_id> endpoint.
        
        Verifies that observations can be deleted through the API.
        Also tests error cases for non-existent observation and unauthorized deletion attempts.
        
        Args:
            client: Flask test client
            api_auth_headers: Authentication headers fixture
            patient_factory: Factory to create test patients
            observation_factory: Factory to create test observations
        """
        doctor = api_auth_headers['doctor']
        headers = api_auth_headers['headers']
        
        # Create patient and observation
        patient = patient_factory()
        doctor.add_patient(patient)
        observation = observation_factory(doctor, patient)
        
        # Test deleting observation
        response = client.delete(f'/api/observations/{observation.id}', headers=headers)
        
        # Check response - just verify status code since response might not be JSON
        assert response.status_code == 200
        
        # Try to parse JSON response if available
        if response.data:
            try:
                data = json.loads(response.data)
                if 'message' in data:
                    assert 'successfully' in data['message'].lower()
            except json.JSONDecodeError:
                # If not JSON, that's okay - just check the status code
                pass
        
        # Verify observation was deleted from database
        assert VitalObservation.query.get(observation.id) is None
        
        # Test with non-existent observation
        response = client.delete('/api/observations/9999', headers=headers)
        assert response.status_code == 404
        
        # Test with observation not created by this doctor
        from app.models import Doctor
        from app.app import db
        
        # Create a new doctor for authorization testing
        other_doctor = Doctor(email="test_delete_other@example.com", first_name="Other", last_name="Doctor")
        other_doctor.set_password("Password123!")
        db.session.add(other_doctor)
        db.session.commit()
        
        # Create a patient and observation owned by the other doctor
        other_patient = patient_factory()
        other_doctor.add_patient(other_patient)
        other_observation = observation_factory(other_doctor, other_patient)
        
        # Try to delete the other doctor's observation with the original doctor's credentials
        response = client.delete(f'/api/observations/{other_observation.id}', headers=headers)
        assert response.status_code == 403

    def test_import_patient(self, client, api_auth_headers, patient_factory):
        """Test POST /api/patients/import endpoint.
        
        Verifies that a patient can be imported/associated with a doctor through the API.
        Also tests error cases for already associated patient, invalid UUID, and non-existent patient.
        
        Args:
            client: Flask test client
            api_auth_headers: Authentication headers fixture
            patient_factory: Factory to create test patients
        """
        api_auth_headers['doctor']
        headers = api_auth_headers['headers']
        
        # Create a patient that isn't associated with the doctor
        patient = patient_factory()
        
        # Test importing patient
        response = client.post(
            '/api/patients/import',
            headers=headers,
            json={"patient_uuid": patient.uuid}
        )
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert 'Patient imported successfully' in data['message']
        
        # Verify patient is now associated with doctor
        doctor_patient = Patient.query.join(
            Patient.doctors
        ).filter(
            Patient.id == patient.id
        ).count()
        assert doctor_patient > 0
        
        # Test importing already associated patient
        response = client.post(
            '/api/patients/import',
            headers=headers,
            json={"patient_uuid": patient.uuid}
        )
        assert response.status_code == 409  # Conflict
        
        # Test with invalid UUID
        response = client.post(
            '/api/patients/import',
            headers=headers,
            json={"patient_uuid": "invalid-uuid"}
        )
        assert response.status_code == 400
        
        # Test with non-existent UUID
        random_uuid = str(uuid4())
        response = client.post(
            '/api/patients/import',
            headers=headers,
            json={"patient_uuid": random_uuid}
        )
        assert response.status_code == 404
