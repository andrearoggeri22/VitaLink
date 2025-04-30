import pytest
import os
import sys
import uuid
from datetime import datetime, date, timedelta
import random
from faker import Faker
import json

# Aggiungi la directory principale al path per importare i moduli
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.app import app, db
    from app.models import Doctor, Patient, Note, VitalObservation, VitalSignType, HealthPlatform
except ImportError:
    # Gestione degli errori di importazione per i test
    print("Errore di importazione dei moduli dell'applicazione")
    # Crea stub delle classi necessarie per evitare errori di importazione nei test
    class Doctor: pass
    class Patient: pass
    class Note: pass
    class VitalObservation: pass
    class VitalSignType: pass
    class HealthPlatform: pass
    db = None
    app = None

fake = Faker()

# Non importare ora i fixture aggiuntivi per evitare problemi di importazione circolare
# Li importeremo in fase di esecuzione
admin_doctor = None
multiple_doctors = None
patient_with_history = None
connected_patient = None
api_client = None

@pytest.fixture(scope='function')
def client():
    """Fixture per creare un client di test e un database in memoria."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture(scope='function')
def test_doctor(client):
    """Fixture per creare un dottore di test."""
    doctor = Doctor(
        email="doctor@example.com",
        first_name="Test",
        last_name="Doctor",
        specialty="General Medicine"
    )
    doctor.set_password("Password123!")
    db.session.add(doctor)
    db.session.commit()
    return doctor

@pytest.fixture(scope='function')
def test_patient(client, test_doctor):
    """Fixture per creare un paziente di test."""
    patient = Patient(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
        gender=random.choice(["Male", "Female", "Other"]),
        contact_number=fake.phone_number(),
        address=fake.address()
    )
    db.session.add(patient)
    db.session.commit()
    
    # Associate patient with doctor
    test_doctor.add_patient(patient)
    
    return patient

@pytest.fixture(scope='function')
def authenticated_client(client, test_doctor):
    """Fixture per un client con login già effettuato."""
    client.post(
        '/login',
        data={'email': 'doctor@example.com', 'password': 'Password123!'},
        follow_redirects=True
    )
    return client

@pytest.fixture(scope='function')
def test_note(client, test_doctor, test_patient):
    """Fixture per creare una nota medica di test."""
    note = Note(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        content=fake.paragraph(nb_sentences=3)
    )
    db.session.add(note)
    db.session.commit()
    return note

@pytest.fixture(scope='function')
def test_vital_observation(client, test_doctor, test_patient):
    """Fixture per creare un'osservazione vitale di test."""
    # Scegli un tipo casuale di segno vitale
    vital_type = random.choice(list(VitalSignType))
    
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
    
    # Genera contenuto appropriato in base al tipo di segno vitale
    if vital_type == VitalSignType.HEART_RATE:
        content = json.dumps([{"value": random.randint(60, 100), "timestamp": datetime.now().isoformat()} for _ in range(5)])
    elif vital_type == VitalSignType.STEPS:
        content = json.dumps([{"value": random.randint(1000, 15000), "timestamp": datetime.now().isoformat()}])
    else:
        content = json.dumps([{"value": random.random() * 100, "timestamp": datetime.now().isoformat()} for _ in range(3)])
    
    observation = VitalObservation(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        vital_type=vital_type,
        content=content,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(observation)
    db.session.commit()
    return observation

@pytest.fixture(scope='function')
def random_patients(client, test_doctor, num_patients=5):
    """Fixture per creare più pazienti casuali."""
    patients = []
    for _ in range(num_patients):
        patient = Patient(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
            gender=random.choice(["Male", "Female", "Other"]),
            contact_number=fake.phone_number(),
            address=fake.address()
        )
        db.session.add(patient)
        patients.append(patient)
    
    db.session.commit()
    
    # Associate patients with the doctor
    for patient in patients:
        test_doctor.add_patient(patient)
    
    return patients
