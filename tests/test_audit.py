import pytest
from datetime import datetime, timedelta
import json
from app.models import ActionType, EntityType, AuditLog

def test_audit_log_creation(client, test_doctor, test_patient):
    """Verifica la creazione di log di audit."""
    from app.audit import log_action
    
    # Crea un log di audit per la visualizzazione di un paziente
    log_action(
        doctor_id=test_doctor.id,
        action_type=ActionType.VIEW,
        entity_type=EntityType.PATIENT,
        entity_id=test_patient.id,
        patient_id=test_patient.id,
        description=f"Visualizzazione dei dettagli del paziente {test_patient.first_name} {test_patient.last_name}"
    )
    
    # Verifica che il log sia stato creato
    audit = AuditLog.query.filter_by(
        doctor_id=test_doctor.id,
        action_type=ActionType.VIEW,
        entity_type=EntityType.PATIENT,
        entity_id=test_patient.id
    ).first()
    
    assert audit is not None
    assert audit.patient_id == test_patient.id
    assert audit.timestamp is not None
    assert f"Visualizzazione dei dettagli del paziente {test_patient.first_name}" in audit.description

def test_patient_creation_audit(authenticated_client, test_doctor):
    """Verifica che venga registrato un log quando viene creato un paziente."""
    # Crea un nuovo paziente
    patient_data = {
        'first_name': 'AuditTest',
        'last_name': 'Patient',
        'date_of_birth': '1990-05-15',
        'gender': 'Male',
        'contact_number': '+12345678901',
        'address': '123 Audit Test Street, Testville'
    }
    
    response = authenticated_client.post(
        '/patients/add',
        data=patient_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Trova il paziente appena creato
    from app.models import Patient
    patient = Patient.query.filter_by(first_name='AuditTest').first()
    assert patient is not None
    
    # Verifica che sia stato creato un log di audit
    audit = AuditLog.query.filter_by(
        doctor_id=test_doctor.id,
        action_type=ActionType.CREATE,
        entity_type=EntityType.PATIENT,
        entity_id=patient.id
    ).first()
    
    assert audit is not None
    assert audit.patient_id == patient.id

def test_patient_update_audit(authenticated_client, test_doctor, test_patient):
    """Verifica che venga registrato un log quando viene aggiornato un paziente."""
    # Aggiorna un paziente esistente
    update_data = {
        'first_name': test_patient.first_name,
        'last_name': test_patient.last_name,
        'date_of_birth': test_patient.date_of_birth.strftime('%Y-%m-%d'),
        'gender': test_patient.gender,
        'contact_number': '+98765432100',  # Numero aggiornato
        'address': 'Nuovo indirizzo per il test di audit'  # Indirizzo aggiornato
    }
    
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/edit',
        data=update_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che sia stato creato un log di audit
    audit = AuditLog.query.filter_by(
        doctor_id=test_doctor.id,
        action_type=ActionType.UPDATE,
        entity_type=EntityType.PATIENT,
        entity_id=test_patient.id
    ).first()
    
    assert audit is not None
    assert audit.patient_id == test_patient.id

def test_note_creation_audit(authenticated_client, test_doctor, test_patient):
    """Verifica che venga registrato un log quando viene creata una nota."""
    # Crea una nuova nota
    note_data = {
        'content': 'Questa è una nota di test per verificare l\'audit.'
    }
    
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/notes/add',
        data=note_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Trova la nota appena creata
    from app.models import Note
    note = Note.query.filter_by(
        patient_id=test_patient.id,
        content='Questa è una nota di test per verificare l\'audit.'
    ).first()
    assert note is not None
    
    # Verifica che sia stato creato un log di audit
    audit = AuditLog.query.filter_by(
        doctor_id=test_doctor.id,
        action_type=ActionType.CREATE,
        entity_type=EntityType.NOTE,
        entity_id=note.id
    ).first()
    
    assert audit is not None
    assert audit.patient_id == test_patient.id

def test_vital_observation_creation_audit(authenticated_client, test_doctor, test_patient):
    """Verifica che venga registrato un log quando viene creata un'osservazione vitale."""
    # Crea una nuova osservazione vitale
    start_date = datetime.utcnow() - timedelta(days=1)
    end_date = datetime.utcnow()
    
    observation_data = {
        'vital_type': 'heart_rate',
        'content': json.dumps([{"value": 80, "timestamp": datetime.now().isoformat()}]),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }
    
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/vitals/add',
        data=observation_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Trova l'osservazione appena creata
    from app.models import VitalObservation, VitalSignType
    observation = VitalObservation.query.filter_by(
        patient_id=test_patient.id,
        vital_type=VitalSignType.HEART_RATE
    ).order_by(VitalObservation.created_at.desc()).first()
    assert observation is not None
    
    # Verifica che sia stato creato un log di audit
    audit = AuditLog.query.filter_by(
        doctor_id=test_doctor.id,
        action_type=ActionType.CREATE,
        entity_type=EntityType.OBSERVATION,
        entity_id=observation.id
    ).first()
    
    assert audit is not None
    assert audit.patient_id == test_patient.id

def test_report_generation_audit(authenticated_client, test_doctor, test_patient, test_vital_observation):
    """Verifica che venga registrato un log quando viene generato un report."""
    # Ottieni il tipo di parametro vitale dall'osservazione di test
    vital_type = test_vital_observation.vital_type.value
    
    # Richiedi la generazione di un report
    from_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    to_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/reports/generate',
        data={
            'report_type': 'vital',
            'vital_type': vital_type,
            'from_date': from_date,
            'to_date': to_date
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che sia stato creato un log di audit
    audit = AuditLog.query.filter_by(
        doctor_id=test_doctor.id,
        action_type=ActionType.EXPORT,
        entity_type=EntityType.REPORT,
        patient_id=test_patient.id
    ).order_by(AuditLog.timestamp.desc()).first()
    
    assert audit is not None

def test_health_platform_link_generation_audit(authenticated_client, test_doctor, test_patient):
    """Verifica che venga registrato un log quando viene generato un link per l'integrazione con piattaforme sanitarie."""
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/health-platforms/generate-link',
        data={'platform': 'fitbit'},
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che sia stato creato un log di audit
    audit = AuditLog.query.filter_by(
        doctor_id=test_doctor.id,
        action_type=ActionType.GENERATE_LINK,
        entity_type=EntityType.HEALTH_LINK,
        patient_id=test_patient.id
    ).order_by(AuditLog.timestamp.desc()).first()
    
    assert audit is not None

def test_patient_import_audit(authenticated_client, test_doctor):
    """Verifica che venga registrato un log quando viene importato un paziente."""
    # Crea un paziente non associato al dottore corrente
    from app.app import db
    from app.models import Patient
    
    new_patient = Patient(
        first_name='ImportTest',
        last_name='Patient',
        date_of_birth=datetime.strptime('1992-07-20', '%Y-%m-%d').date(),
        gender='Female',
        contact_number='+45678901234',
        address='456 Import Test Road, Importville'
    )
    db.session.add(new_patient)
    db.session.commit()
    
    # Importa il paziente
    response = authenticated_client.post(
        '/patients/import',
        json={'patient_uuid': new_patient.uuid},
        content_type='application/json'
    )
    assert response.status_code == 200
    
    # Verifica che sia stato creato un log di audit
    audit = AuditLog.query.filter_by(
        doctor_id=test_doctor.id,
        action_type=ActionType.IMPORT,
        entity_type=EntityType.PATIENT,
        entity_id=new_patient.id
    ).first()
    
    assert audit is not None
    assert audit.patient_id == new_patient.id
