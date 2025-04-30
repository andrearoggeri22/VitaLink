import pytest
from datetime import datetime, timedelta
import json
from app.models import Doctor, Patient, Note, VitalObservation, VitalSignType, HealthPlatform, DoctorPatient

def test_doctor_model(client):
    """Verifica la creazione e le funzionalità del modello Doctor."""
    doctor = Doctor(
        email="model_test@example.com",
        first_name="Model",
        last_name="Test",
        specialty="Internal Medicine"
    )
    doctor.set_password("SecurePass123!")
    
    # Verifica la password hash
    assert doctor.password_hash is not None
    assert doctor.check_password("SecurePass123!") is True
    assert doctor.check_password("WrongPassword") is False
    
    # Salva nel database
    from app.app import db
    db.session.add(doctor)
    db.session.commit()
    
    # Verifica che sia stato creato correttamente
    saved_doctor = Doctor.query.filter_by(email="model_test@example.com").first()
    assert saved_doctor is not None
    assert saved_doctor.first_name == "Model"
    assert saved_doctor.last_name == "Test"
    assert saved_doctor.specialty == "Internal Medicine"
    
    # Verifica il metodo to_dict
    doctor_dict = saved_doctor.to_dict()
    assert doctor_dict["email"] == "model_test@example.com"
    assert doctor_dict["first_name"] == "Model"
    assert doctor_dict["last_name"] == "Test"
    assert doctor_dict["specialty"] == "Internal Medicine"

def test_patient_model(client):
    """Verifica la creazione e le funzionalità del modello Patient."""
    # Crea un nuovo paziente
    patient = Patient(
        first_name="Patient",
        last_name="Test",
        date_of_birth=datetime.strptime("1990-01-01", "%Y-%m-%d").date(),
        gender="Male",
        contact_number="+123456789",
        address="123 Test Street, Testville"
    )
    
    # Salva nel database
    from app.app import db
    db.session.add(patient)
    db.session.commit()
    
    # Verifica che sia stato creato correttamente
    saved_patient = Patient.query.filter_by(first_name="Patient").first()
    assert saved_patient is not None
    assert saved_patient.last_name == "Test"
    assert saved_patient.date_of_birth.isoformat() == "1990-01-01"
    assert saved_patient.gender == "Male"
    assert saved_patient.uuid is not None  # UUID dovrebbe essere generato automaticamente
    
    # Verifica il metodo to_dict
    patient_dict = saved_patient.to_dict()
    assert patient_dict["first_name"] == "Patient"
    assert patient_dict["last_name"] == "Test"
    assert "1990-01-01" in patient_dict["date_of_birth"]
    assert patient_dict["gender"] == "Male"

def test_doctor_patient_relationship(client, test_doctor):
    """Verifica la relazione many-to-many tra Doctor e Patient."""
    # Crea tre pazienti
    patients = []
    for i in range(3):
        patient = Patient(
            first_name=f"Patient{i}",
            last_name="Test",
            date_of_birth=datetime.strptime("1990-01-01", "%Y-%m-%d").date(),
            gender="Female",
            contact_number=f"+123456789{i}",
            address=f"123 Test Street #{i}, Testville"
        )
        patients.append(patient)
        from app.app import db
        db.session.add(patient)
    
    db.session.commit()
    
    # Associa i pazienti al dottore
    for patient in patients:
        test_doctor.add_patient(patient)
    
    # Verifica l'associazione
    doctor_patients = test_doctor.get_patients()
    assert len(doctor_patients) == 3
    
    # Verifica che i pazienti siano quelli corretti
    patient_names = [p.first_name for p in doctor_patients]
    for i in range(3):
        assert f"Patient{i}" in patient_names
    
    # Rimuovi un paziente
    test_doctor.remove_patient(patients[0])
    
    # Verifica la rimozione
    doctor_patients = test_doctor.get_patients()
    assert len(doctor_patients) == 2
    patient_names = [p.first_name for p in doctor_patients]
    assert "Patient0" not in patient_names

def test_note_model(client, test_doctor, test_patient):
    """Verifica la creazione e le funzionalità del modello Note."""
    # Crea una nota
    note = Note(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        content="Questo è un test di nota medica."
    )
    
    # Salva nel database
    from app.app import db
    db.session.add(note)
    db.session.commit()
    
    # Verifica che sia stata creata correttamente
    saved_note = Note.query.filter_by(patient_id=test_patient.id).first()
    assert saved_note is not None
    assert saved_note.doctor_id == test_doctor.id
    assert saved_note.content == "Questo è un test di nota medica."
    
    # Verifica il metodo to_dict
    note_dict = saved_note.to_dict()
    assert note_dict["patient_id"] == test_patient.id
    assert note_dict["doctor_id"] == test_doctor.id
    assert note_dict["content"] == "Questo è un test di nota medica."
    assert "created_at" in note_dict
    
    # Verifica le relazioni
    assert saved_note.patient == test_patient
    assert saved_note.doctor == test_doctor
    
    # Verifica che la nota appaia nelle note del paziente
    patient_notes = test_patient.get_notes()
    assert len(patient_notes) == 1
    assert patient_notes[0].content == "Questo è un test di nota medica."
    
    # Verifica che la nota appaia nelle note del dottore
    doctor_notes = test_doctor.notes.all()
    assert len(doctor_notes) == 1
    assert doctor_notes[0].content == "Questo è un test di nota medica."

def test_vital_observation_model(client, test_doctor, test_patient):
    """Verifica la creazione e le funzionalità del modello VitalObservation."""
    # Crea un'osservazione vitale
    start_date = datetime.utcnow() - timedelta(days=1)
    end_date = datetime.utcnow()
    content = json.dumps([{"value": 72, "timestamp": datetime.now().isoformat()}])
    
    observation = VitalObservation(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        vital_type=VitalSignType.HEART_RATE,
        content=content,
        start_date=start_date,
        end_date=end_date
    )
    
    # Salva nel database
    from app.app import db
    db.session.add(observation)
    db.session.commit()
    
    # Verifica che sia stata creata correttamente
    saved_obs = VitalObservation.query.filter_by(patient_id=test_patient.id).first()
    assert saved_obs is not None
    assert saved_obs.doctor_id == test_doctor.id
    assert saved_obs.vital_type == VitalSignType.HEART_RATE
    assert json.loads(saved_obs.content)[0]["value"] == 72
    
    # Verifica il metodo to_dict
    obs_dict = saved_obs.to_dict()
    assert obs_dict["patient_id"] == test_patient.id
    assert obs_dict["doctor_id"] == test_doctor.id
    assert obs_dict["vital_type"] == "heart_rate"
    assert "doctor_name" in obs_dict  # Il metodo to_dict dovrebbe includere il nome del dottore
    
    # Verifica le relazioni
    assert saved_obs.patient == test_patient
    assert saved_obs.doctor == test_doctor
    
    # Verifica che l'osservazione appaia nelle osservazioni vitali del paziente
    patient_obs = test_patient.get_vital_observations()
    assert len(patient_obs) == 1
    assert patient_obs[0].vital_type == VitalSignType.HEART_RATE
    
    # Verifica la funzionalità di filtraggio per tipo
    filtered_obs = test_patient.get_vital_observations(vital_type=VitalSignType.HEART_RATE)
    assert len(filtered_obs) == 1
    
    # Verifica la funzionalità di filtraggio per data
    filtered_by_date = test_patient.get_vital_observations(
        start_date=start_date - timedelta(hours=1),
        end_date=end_date + timedelta(hours=1)
    )
    assert len(filtered_by_date) == 1
    
    # Non dovrebbero esserci osservazioni con date fuori dal range
    no_obs = test_patient.get_vital_observations(
        start_date=start_date + timedelta(days=2),
        end_date=end_date + timedelta(days=3)
    )
    assert len(no_obs) == 0

def test_health_platform_integration(client, test_patient):
    """Verifica l'integrazione con piattaforme di salute."""
    # Configura l'integrazione con Fitbit
    test_patient.connected_platform = HealthPlatform.FITBIT
    test_patient.platform_access_token = "test_access_token"
    test_patient.platform_refresh_token = "test_refresh_token"
    test_patient.platform_token_expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Salva nel database
    from app.app import db
    db.session.commit()
    
    # Recupera il paziente e verifica l'integrazione
    saved_patient = Patient.query.get(test_patient.id)
    assert saved_patient.connected_platform == HealthPlatform.FITBIT
    assert saved_patient.platform_access_token == "test_access_token"
    assert saved_patient.platform_refresh_token == "test_refresh_token"
    assert saved_patient.platform_token_expires_at > datetime.utcnow()
