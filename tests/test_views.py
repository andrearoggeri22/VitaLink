import pytest
from flask import url_for
import json
from datetime import datetime, timedelta
import re

def test_index_redirect(client):
    """Verifica che la pagina principale reindirizza correttamente."""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    # Se non autenticato, dovrebbe reindirizzare al login
    assert b'login' in response.data.lower()

def test_dashboard_access(authenticated_client):
    """Verifica l'accesso alla dashboard da utente autenticato."""
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data or b'Pannello di controllo' in response.data

def test_dashboard_content(authenticated_client, test_doctor, test_patient, test_note, test_vital_observation):
    """Verifica che la dashboard mostri i contenuti corretti."""
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
    
    # Verifica che il conteggio dei pazienti sia corretto
    assert str(test_doctor.patients.count()).encode() in response.data
    
    # Verifica che ci siano sezioni per pazienti recenti e osservazioni recenti
    assert b'recenti' in response.data.lower() or b'recent' in response.data.lower()
    
    # Il nome del paziente dovrebbe apparire nella pagina
    assert test_patient.first_name.encode() in response.data

def test_patients_page(authenticated_client, random_patients):
    """Verifica che la pagina dei pazienti mostri tutti i pazienti."""
    response = authenticated_client.get('/patients')
    assert response.status_code == 200
    
    # Verifica che ci siano tutti i pazienti
    for patient in random_patients:
        assert patient.first_name.encode() in response.data
        assert patient.last_name.encode() in response.data

def test_patient_detail_page(authenticated_client, test_patient, test_note):
    """Verifica che la pagina di dettaglio del paziente mostri le informazioni corrette."""
    response = authenticated_client.get(f'/patients/{test_patient.uuid}')
    assert response.status_code == 200
    
    # Verifica che ci siano i dettagli del paziente
    assert test_patient.first_name.encode() in response.data
    assert test_patient.last_name.encode() in response.data
    
    # Dovrebbe esserci il contenuto della nota
    assert test_note.content.encode() in response.data

def test_add_patient(authenticated_client):
    """Verifica l'aggiunta di un nuovo paziente tramite form."""
    # Dati del paziente di test
    new_patient = {
        'first_name': 'NewPatient',
        'last_name': 'FromForm',
        'date_of_birth': '1995-05-15',
        'gender': 'Female',
        'contact_number': '+3456789012',
        'address': '789 Form Street, Formville'
    }
    
    response = authenticated_client.post(
        '/patients/add',
        data=new_patient,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il paziente sia stato aggiunto con successo
    assert b'success' in response.data.lower() or b'success' in response.data.lower()
    assert new_patient['first_name'].encode() in response.data
    
    # Verifica nel database
    from app.models import Patient
    patient = Patient.query.filter_by(first_name=new_patient['first_name']).first()
    assert patient is not None
    assert patient.last_name == new_patient['last_name']

def test_edit_patient(authenticated_client, test_patient):
    """Verifica la modifica di un paziente esistente."""
    # Dati aggiornati
    updated_data = {
        'first_name': test_patient.first_name,
        'last_name': test_patient.last_name,
        'date_of_birth': test_patient.date_of_birth.strftime('%Y-%m-%d'),
        'gender': test_patient.gender,
        'contact_number': '+9999999999',  # Numero aggiornato
        'address': 'Indirizzo aggiornato, Nuova Città'  # Indirizzo aggiornato
    }
    
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/edit',
        data=updated_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il paziente sia stato aggiornato con successo
    assert b'aggiornato' in response.data.lower() or b'updated' in response.data.lower() or b'success' in response.data.lower()
    
    # Verifica nel database
    from app.models import Patient
    patient = Patient.query.get(test_patient.id)
    assert patient.contact_number == '+9999999999'
    assert patient.address == 'Indirizzo aggiornato, Nuova Città'

def test_add_note(authenticated_client, test_patient):
    """Verifica l'aggiunta di una nota a un paziente."""
    note_data = {
        'content': 'Questa è una nota aggiunta tramite form web.'
    }
    
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/notes/add',
        data=note_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che la nota sia stata aggiunta
    assert b'success' in response.data.lower() or b'aggiunta' in response.data.lower() or b'added' in response.data.lower()
    
    # Verifica nel database
    from app.models import Note
    notes = Note.query.filter_by(
        patient_id=test_patient.id,
        content='Questa è una nota aggiunta tramite form web.'
    ).all()
    assert len(notes) > 0

def test_add_vital_observation(authenticated_client, test_patient):
    """Verifica l'aggiunta di un'osservazione vitale a un paziente."""
    start_date = datetime.utcnow() - timedelta(days=1)
    end_date = datetime.utcnow()
    
    observation_data = {
        'vital_type': 'heart_rate',
        'content': json.dumps([{"value": 78, "timestamp": datetime.now().isoformat()}]),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }
    
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/vitals/add',
        data=observation_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che l'osservazione sia stata aggiunta
    success_terms = [b'success', b'aggiunta', b'added']
    assert any(term in response.data.lower() for term in success_terms)
    
    # Verifica nel database
    from app.models import VitalObservation, VitalSignType
    observations = VitalObservation.query.filter_by(
        patient_id=test_patient.id,
        vital_type=VitalSignType.HEART_RATE
    ).all()
    assert len(observations) > 0

def test_import_patient(authenticated_client, random_patients):
    """Verifica l'importazione di un paziente tramite UUID."""
    # Prendi un paziente qualsiasi
    other_patient = random_patients[0]
    
    # Simula la rimozione del paziente dall'elenco del dottore per poi reimportarlo
    from app.app import db
    from app.models import DoctorPatient, Doctor
    doctor = Doctor.query.filter_by(email='doctor@example.com').first()
    doctor.remove_patient(other_patient)
    db.session.commit()
    
    # Verifica che il paziente non sia più nella lista
    assert other_patient not in doctor.get_patients()
    
    # Importa il paziente
    response = authenticated_client.post(
        '/patients/import',
        json={'patient_uuid': other_patient.uuid},
        content_type='application/json'
    )
    assert response.status_code == 200
    
    # Verifica che il paziente sia stato importato
    doctor = Doctor.query.filter_by(email='doctor@example.com').first()
    assert other_patient in doctor.get_patients()

def test_profile_page(authenticated_client, test_doctor):
    """Verifica che la pagina del profilo mostri le informazioni corrette."""
    response = authenticated_client.get('/profile')
    assert response.status_code == 200
    
    # Verifica che ci siano i dettagli del dottore
    assert test_doctor.email.encode() in response.data
    assert test_doctor.first_name.encode() in response.data
    assert test_doctor.last_name.encode() in response.data
    
    # Se c'è una specialità, dovrebbe essere mostrata
    if test_doctor.specialty:
        assert test_doctor.specialty.encode() in response.data

def test_update_profile(authenticated_client, test_doctor):
    """Verifica l'aggiornamento del profilo del dottore."""
    # Dati aggiornati
    updated_data = {
        'first_name': 'UpdatedFirstName',
        'last_name': test_doctor.last_name,
        'specialty': 'Cardiology Specialist'
    }
    
    response = authenticated_client.post(
        '/profile/update',
        data=updated_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il profilo sia stato aggiornato
    assert b'success' in response.data.lower() or b'aggiornato' in response.data.lower() or b'updated' in response.data.lower()
    
    # Verifica nel database
    from app.models import Doctor
    doctor = Doctor.query.get(test_doctor.id)
    assert doctor.first_name == 'UpdatedFirstName'
    assert doctor.specialty == 'Cardiology Specialist'

def test_change_password(authenticated_client, test_doctor):
    """Verifica il cambio password del dottore."""
    # Prima esegui il logout per evitare problemi di sessione
    authenticated_client.get('/logout')
    
    # Effettua il login con le credenziali originali
    authenticated_client.post(
        '/login',
        data={'email': 'doctor@example.com', 'password': 'Password123!'},
        follow_redirects=True
    )
    
    # Dati cambio password
    password_data = {
        'current_password': 'Password123!',
        'new_password': 'NewPassword456!',
        'confirm_new_password': 'NewPassword456!'
    }
    
    response = authenticated_client.post(
        '/profile/change-password',
        data=password_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che la password sia stata cambiata
    assert b'success' in response.data.lower() or b'cambiata' in response.data.lower() or b'changed' in response.data.lower()
    
    # Tenta il login con la nuova password
    authenticated_client.get('/logout')
    login_response = authenticated_client.post(
        '/login',
        data={'email': 'doctor@example.com', 'password': 'NewPassword456!'},
        follow_redirects=True
    )
    assert login_response.status_code == 200
    assert b'Dashboard' in login_response.data or b'Pannello di controllo' in login_response.data

def test_audit_logs_page(authenticated_client):
    """Verifica che la pagina dei log di audit sia accessibile e mostri i log."""
    response = authenticated_client.get('/audit-logs')
    assert response.status_code == 200
    
    # Verifica che ci sia la tabella dei log
    assert b'<table' in response.data.lower() and b'</table>' in response.data.lower()

def test_change_language(authenticated_client):
    """Verifica il cambio della lingua dell'interfaccia."""
    # Cambia la lingua in italiano
    response = authenticated_client.get('/set-language/it', follow_redirects=True)
    assert response.status_code == 200
    
    # Verifica che qualche testo sia in italiano
    dashboard_response = authenticated_client.get('/dashboard')
    assert b'Pannello' in dashboard_response.data or b'pazienti' in dashboard_response.data.lower()
    
    # Cambia la lingua in inglese
    response = authenticated_client.get('/set-language/en', follow_redirects=True)
    assert response.status_code == 200
    
    # Verifica che qualche testo sia in inglese
    dashboard_response = authenticated_client.get('/dashboard')
    assert b'Dashboard' in dashboard_response.data or b'patients' in dashboard_response.data.lower()
