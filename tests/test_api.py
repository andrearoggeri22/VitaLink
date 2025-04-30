import pytest
from flask import url_for
import json
from datetime import datetime, timedelta

def test_api_auth_required(client):
    """Verifica che le API protette richiedano l'autenticazione."""
    # Prova ad accedere a un endpoint API protetto senza token
    response = client.get('/api/patients')
    assert response.status_code == 401  # Unauthorized
    
def test_api_get_patients(authenticated_client, test_doctor, random_patients):
    """Verifica l'API per ottenere la lista dei pazienti."""
    # Prima otteniamo un token di accesso
    login_response = authenticated_client.post(
        '/api/login',
        json={
            'email': 'doctor@example.com',
            'password': 'Password123!'
        }
    )
    token = json.loads(login_response.data)['access_token']
    
    # Usa il token per accedere all'API dei pazienti
    response = authenticated_client.get(
        '/api/patients',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'patients' in data
    assert len(data['patients']) == len(random_patients)

def test_api_get_patient_detail(authenticated_client, test_doctor, test_patient):
    """Verifica l'API per ottenere i dettagli di un singolo paziente."""
    # Prima otteniamo un token di accesso
    login_response = authenticated_client.post(
        '/api/login',
        json={
            'email': 'doctor@example.com',
            'password': 'Password123!'
        }
    )
    token = json.loads(login_response.data)['access_token']
    
    # Usa il token per accedere all'API dei dettagli del paziente
    response = authenticated_client.get(
        f'/api/patients/{test_patient.uuid}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'patient' in data
    assert data['patient']['uuid'] == test_patient.uuid
    assert data['patient']['first_name'] == test_patient.first_name

def test_api_create_patient(authenticated_client, test_doctor):
    """Verifica l'API per creare un nuovo paziente."""
    # Prima otteniamo un token di accesso
    login_response = authenticated_client.post(
        '/api/login',
        json={
            'email': 'doctor@example.com',
            'password': 'Password123!'
        }
    )
    token = json.loads(login_response.data)['access_token']
    
    # Crea un nuovo paziente tramite API
    new_patient_data = {
        'first_name': 'New',
        'last_name': 'Patient',
        'date_of_birth': '1985-03-15',
        'gender': 'Female',
        'contact_number': '+9876543210',
        'address': '456 New Street, Newville'
    }
    
    response = authenticated_client.post(
        '/api/patients',
        json=new_patient_data,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert 'patient' in data
    assert data['patient']['first_name'] == 'New'
    assert data['patient']['last_name'] == 'Patient'
    
    # Verifica che il paziente sia stato creato nel database
    from app.models import Patient
    patient = Patient.query.filter_by(first_name='New', last_name='Patient').first()
    assert patient is not None
    assert patient.gender == 'Female'

def test_api_update_patient(authenticated_client, test_doctor, test_patient):
    """Verifica l'API per aggiornare un paziente esistente."""
    # Prima otteniamo un token di accesso
    login_response = authenticated_client.post(
        '/api/login',
        json={
            'email': 'doctor@example.com',
            'password': 'Password123!'
        }
    )
    token = json.loads(login_response.data)['access_token']
    
    # Aggiorna il paziente tramite API
    update_data = {
        'contact_number': '+111222333',
        'address': 'Updated Address, City'
    }
    
    response = authenticated_client.put(
        f'/api/patients/{test_patient.uuid}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'patient' in data
    assert data['patient']['contact_number'] == '+111222333'
    assert data['patient']['address'] == 'Updated Address, City'
    
    # Verifica che il paziente sia stato aggiornato nel database
    from app.models import Patient
    patient = Patient.query.get(test_patient.id)
    assert patient.contact_number == '+111222333'
    assert patient.address == 'Updated Address, City'

def test_api_add_note(authenticated_client, test_doctor, test_patient):
    """Verifica l'API per aggiungere una nota medica a un paziente."""
    # Prima otteniamo un token di accesso
    login_response = authenticated_client.post(
        '/api/login',
        json={
            'email': 'doctor@example.com',
            'password': 'Password123!'
        }
    )
    token = json.loads(login_response.data)['access_token']
    
    # Aggiungi una nota tramite API
    note_data = {
        'content': 'Questa è una nota di test tramite API.'
    }
    
    response = authenticated_client.post(
        f'/api/patients/{test_patient.uuid}/notes',
        json=note_data,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert 'note' in data
    assert data['note']['content'] == 'Questa è una nota di test tramite API.'
    
    # Verifica che la nota sia stata creata nel database
    from app.models import Note
    note = Note.query.filter_by(patient_id=test_patient.id).first()
    assert note is not None
    assert note.content == 'Questa è una nota di test tramite API.'
    assert note.doctor_id == test_doctor.id

def test_api_get_notes(authenticated_client, test_doctor, test_patient, test_note):
    """Verifica l'API per ottenere le note di un paziente."""
    # Prima otteniamo un token di accesso
    login_response = authenticated_client.post(
        '/api/login',
        json={
            'email': 'doctor@example.com',
            'password': 'Password123!'
        }
    )
    token = json.loads(login_response.data)['access_token']
    
    # Ottieni le note tramite API
    response = authenticated_client.get(
        f'/api/patients/{test_patient.uuid}/notes',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'notes' in data
    assert len(data['notes']) > 0
    assert data['notes'][0]['content'] == test_note.content

def test_api_add_vital_observation(authenticated_client, test_doctor, test_patient):
    """Verifica l'API per aggiungere un'osservazione vitale a un paziente."""
    # Prima otteniamo un token di accesso
    login_response = authenticated_client.post(
        '/api/login',
        json={
            'email': 'doctor@example.com',
            'password': 'Password123!'
        }
    )
    token = json.loads(login_response.data)['access_token']
    
    # Aggiungi un'osservazione vitale tramite API
    start_date = datetime.utcnow() - timedelta(days=1)
    end_date = datetime.utcnow()
    
    observation_data = {
        'vital_type': 'heart_rate',
        'content': json.dumps([{"value": 75, "timestamp": datetime.now().isoformat()}]),
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    }
    
    response = authenticated_client.post(
        f'/api/patients/{test_patient.uuid}/vitals',
        json=observation_data,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert 'observation' in data
    assert data['observation']['vital_type'] == 'heart_rate'
    
    # Verifica che l'osservazione sia stata creata nel database
    from app.models import VitalObservation, VitalSignType
    observation = VitalObservation.query.filter_by(
        patient_id=test_patient.id,
        vital_type=VitalSignType.HEART_RATE
    ).first()
    assert observation is not None
    assert observation.doctor_id == test_doctor.id

def test_api_get_vital_observations(authenticated_client, test_doctor, test_patient, test_vital_observation):
    """Verifica l'API per ottenere le osservazioni vitali di un paziente."""
    # Prima otteniamo un token di accesso
    login_response = authenticated_client.post(
        '/api/login',
        json={
            'email': 'doctor@example.com',
            'password': 'Password123!'
        }
    )
    token = json.loads(login_response.data)['access_token']
    
    # Ottieni le osservazioni vitali tramite API
    response = authenticated_client.get(
        f'/api/patients/{test_patient.uuid}/vitals',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'observations' in data
    assert len(data['observations']) > 0
    
    # Verifica il filtraggio per tipo
    response = authenticated_client.get(
        f'/api/patients/{test_patient.uuid}/vitals?type={test_vital_observation.vital_type.value}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'observations' in data
    assert len(data['observations']) > 0
    assert data['observations'][0]['vital_type'] == test_vital_observation.vital_type.value

def test_api_health_platform_integration(authenticated_client, test_doctor, test_patient):
    """Verifica l'API per l'integrazione con piattaforme sanitarie."""
    # Prima otteniamo un token di accesso
    login_response = authenticated_client.post(
        '/api/login',
        json={
            'email': 'doctor@example.com',
            'password': 'Password123!'
        }
    )
    token = json.loads(login_response.data)['access_token']
    
    # Genera un link di integrazione
    response = authenticated_client.post(
        f'/api/patients/{test_patient.uuid}/health-platforms/generate-link',
        json={'platform': 'fitbit'},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Nota: poiché la generazione del link dipende da configurazioni esterne,
    # verifichiamo solo che la risposta sia valida, non il contenuto specifico
    assert response.status_code in [200, 201]
    
    data = json.loads(response.data)
    if 'link' in data:  # Se l'API è implementata con questa risposta
        assert 'uuid' in data['link']
