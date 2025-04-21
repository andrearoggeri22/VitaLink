import pytest
import json
import uuid
from datetime import datetime, timedelta

from app import app, db
from models import Doctor, Patient, VitalSign, VitalSignType, DataOrigin, Note

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create a test doctor
            doctor = Doctor(
                email="api@example.com",
                first_name="API",
                last_name="Doctor",
                specialty="Testing"
            )
            doctor.set_password("testpassword")
            db.session.add(doctor)
            
            # Create test patients
            patient1 = Patient(
                first_name="Test",
                last_name="Patient",
                date_of_birth=datetime(1990, 5, 15).date(),
                gender="Male"
            )
            patient2 = Patient(
                first_name="Another",
                last_name="Patient",
                date_of_birth=datetime(1985, 3, 20).date(),
                gender="Female"
            )
            db.session.add_all([patient1, patient2])
            db.session.flush()
            
            # Associate doctor with patients
            doctor.add_patient(patient1)
            doctor.add_patient(patient2)
            
            # Add some vital signs
            vitals = [
                VitalSign(
                    patient_id=patient1.id,
                    type=VitalSignType.HEART_RATE,
                    value=75.0,
                    unit="bpm",
                    recorded_at=datetime.utcnow(),
                    origin=DataOrigin.MANUAL
                ),
                VitalSign(
                    patient_id=patient1.id,
                    type=VitalSignType.BLOOD_PRESSURE,
                    value=120.0,
                    unit="mmHg",
                    recorded_at=datetime.utcnow() - timedelta(days=1),
                    origin=DataOrigin.AUTOMATIC
                )
            ]
            db.session.add_all(vitals)
            
            # Add a note
            note = Note(
                patient_id=patient1.id,
                doctor_id=doctor.id,
                content="Initial test note"
            )
            db.session.add(note)
            
            db.session.commit()
            
            yield client
            
            db.session.remove()
            db.drop_all()

@pytest.fixture
def auth_headers(client):
    # Login via API
    response = client.post(
        '/api/login',
        json={'email': 'api@example.com', 'password': 'testpassword'},
        content_type='application/json'
    )
    data = json.loads(response.data)
    token = data['access_token']
    
    return {'Authorization': f'Bearer {token}'}

def test_get_patients(client, auth_headers):
    """Test getting all patients for a doctor."""
    response = client.get('/api/patients', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'patients' in data
    assert len(data['patients']) == 2
    
    # Verify patient data
    patient_names = [p['first_name'] for p in data['patients']]
    assert 'Test' in patient_names
    assert 'Another' in patient_names

def test_get_patient(client, auth_headers):
    """Test getting a specific patient by UUID."""
    # First get all patients to find a UUID
    response = client.get('/api/patients', headers=auth_headers)
    data = json.loads(response.data)
    patient_uuid = data['patients'][0]['uuid']
    
    # Now get the specific patient
    response = client.get(f'/api/patients/{patient_uuid}', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'patient' in data
    assert data['patient']['uuid'] == patient_uuid

def test_get_patient_invalid_uuid(client, auth_headers):
    """Test error handling for invalid UUID format."""
    response = client.get('/api/patients/not-a-valid-uuid', headers=auth_headers)
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid UUID format' in data['error']

def test_get_patient_not_found(client, auth_headers):
    """Test error handling for patient not found."""
    # Generate a random valid UUID that shouldn't exist in the database
    random_uuid = str(uuid.uuid4())
    
    response = client.get(f'/api/patients/{random_uuid}', headers=auth_headers)
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Patient not found' in data['error']

def test_get_vitals(client, auth_headers):
    """Test getting vital signs for a patient."""
    # First get all patients to find a UUID
    response = client.get('/api/patients', headers=auth_headers)
    data = json.loads(response.data)
    patient_uuid = data['patients'][0]['uuid']
    
    # Get vital signs for the patient
    response = client.get(f'/api/patients/{patient_uuid}/vitals', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'vitals' in data
    assert len(data['vitals']) == 2
    
    # Verify vital sign types
    vital_types = [v['type'] for v in data['vitals']]
    assert 'heart_rate' in vital_types
    assert 'blood_pressure' in vital_types

def test_get_vitals_with_filters(client, auth_headers):
    """Test filtering vital signs by type and date."""
    # First get all patients to find a UUID
    response = client.get('/api/patients', headers=auth_headers)
    data = json.loads(response.data)
    patient_uuid = data['patients'][0]['uuid']
    
    # Get heart rate vitals only
    response = client.get(
        f'/api/patients/{patient_uuid}/vitals?type=heart_rate', 
        headers=auth_headers
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data['vitals']) == 1
    assert data['vitals'][0]['type'] == 'heart_rate'

def test_add_vital(client, auth_headers):
    """Test adding a new vital sign."""
    # First get all patients to find a UUID
    response = client.get('/api/patients', headers=auth_headers)
    data = json.loads(response.data)
    patient_uuid = data['patients'][0]['uuid']
    
    # Add a new vital sign
    vital_data = {
        'type': 'temperature',
        'value': 37.5,
        'unit': '°C'
    }
    
    response = client.post(
        f'/api/patients/{patient_uuid}/vitals',
        json=vital_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert 'vital' in data
    assert data['vital']['type'] == 'temperature'
    assert data['vital']['value'] == 37.5
    assert data['vital']['unit'] == '°C'
    
    # Verify it was added by getting all vitals
    response = client.get(f'/api/patients/{patient_uuid}/vitals', headers=auth_headers)
    data = json.loads(response.data)
    assert len(data['vitals']) == 3

def test_add_vital_validation(client, auth_headers):
    """Test validation when adding vital signs."""
    # First get all patients to find a UUID
    response = client.get('/api/patients', headers=auth_headers)
    data = json.loads(response.data)
    patient_uuid = data['patients'][0]['uuid']
    
    # Missing type
    vital_data = {
        'value': 37.5
    }
    
    response = client.post(
        f'/api/patients/{patient_uuid}/vitals',
        json=vital_data,
        headers=auth_headers
    )
    assert response.status_code == 400
    
    # Invalid type
    vital_data = {
        'type': 'not_a_vital_type',
        'value': 37.5
    }
    
    response = client.post(
        f'/api/patients/{patient_uuid}/vitals',
        json=vital_data,
        headers=auth_headers
    )
    assert response.status_code == 400
    
    # Invalid value
    vital_data = {
        'type': 'temperature',
        'value': 'not a number'
    }
    
    response = client.post(
        f'/api/patients/{patient_uuid}/vitals',
        json=vital_data,
        headers=auth_headers
    )
    assert response.status_code == 400

def test_get_notes(client, auth_headers):
    """Test getting notes for a patient."""
    # First get all patients to find a UUID
    response = client.get('/api/patients', headers=auth_headers)
    data = json.loads(response.data)
    patient_uuid = data['patients'][0]['uuid']
    
    # Get notes for the patient
    response = client.get(f'/api/patients/{patient_uuid}/notes', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'notes' in data
    assert len(data['notes']) == 1
    assert 'Initial test note' in data['notes'][0]['content']

def test_add_note(client, auth_headers):
    """Test adding a new note."""
    # First get all patients to find a UUID
    response = client.get('/api/patients', headers=auth_headers)
    data = json.loads(response.data)
    patient_uuid = data['patients'][0]['uuid']
    
    # Add a new note
    note_data = {
        'content': 'This is a new test note added via API'
    }
    
    response = client.post(
        f'/api/patients/{patient_uuid}/notes',
        json=note_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert 'note' in data
    assert data['note']['content'] == 'This is a new test note added via API'
    
    # Verify it was added by getting all notes
    response = client.get(f'/api/patients/{patient_uuid}/notes', headers=auth_headers)
    data = json.loads(response.data)
    assert len(data['notes']) == 2

def test_add_note_validation(client, auth_headers):
    """Test validation when adding notes."""
    # First get all patients to find a UUID
    response = client.get('/api/patients', headers=auth_headers)
    data = json.loads(response.data)
    patient_uuid = data['patients'][0]['uuid']
    
    # Empty content
    note_data = {
        'content': ''
    }
    
    response = client.post(
        f'/api/patients/{patient_uuid}/notes',
        json=note_data,
        headers=auth_headers
    )
    assert response.status_code == 400
    
    # Missing content
    note_data = {}
    
    response = client.post(
        f'/api/patients/{patient_uuid}/notes',
        json=note_data,
        headers=auth_headers
    )
    assert response.status_code == 400

def test_unauthorized_access(client):
    """Test API access without authentication."""
    response = client.get('/api/patients')
    assert response.status_code == 401

def test_invalid_token(client):
    """Test API access with invalid token."""
    headers = {'Authorization': 'Bearer invalid-token'}
    response = client.get('/api/patients', headers=headers)
    assert response.status_code == 422
