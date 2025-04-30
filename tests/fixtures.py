import pytest
import random
import json
from datetime import datetime, timedelta
from faker import Faker
from app.models import Doctor, Patient, Note, VitalObservation, VitalSignType, HealthPlatform

fake = Faker()

@pytest.fixture(scope='function')
def admin_doctor(client):
    """Fixture per creare un dottore admin con privilegi speciali."""
    doctor = Doctor(
        email="admin@vitalink.com",
        first_name="Admin",
        last_name="Doctor",
        specialty="System Administrator",
        # In un sistema reale potrebbe esserci un campo is_admin
    )
    doctor.set_password("AdminPass123!")
    from app.app import db
    db.session.add(doctor)
    db.session.commit()
    return doctor

@pytest.fixture(scope='function')
def multiple_doctors(client, num_doctors=3):
    """Fixture per creare più dottori per testare scenari multi-utente."""
    doctors = []
    for i in range(num_doctors):
        doctor = Doctor(
            email=f"doctor{i}@example.com",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            specialty=random.choice(["Cardiology", "Neurology", "Pediatrics", "Internal Medicine"])
        )
        doctor.set_password(f"DocPassword{i}!")
        from app.app import db
        db.session.add(doctor)
        doctors.append(doctor)
    
    db.session.commit()
    return doctors

@pytest.fixture(scope='function')
def patient_with_history(client, test_doctor):
    """Fixture per creare un paziente con storia clinica completa."""
    # Crea il paziente
    patient = Patient(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        date_of_birth=fake.date_of_birth(minimum_age=40, maximum_age=70),
        gender="Male",
        contact_number=fake.phone_number(),
        address=fake.address()
    )
    from app.app import db
    db.session.add(patient)
    db.session.commit()
    
    # Associa il paziente al dottore
    test_doctor.add_patient(patient)
    
    # Aggiungi note mediche
    for _ in range(5):
        note_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))
        note = Note(
            patient_id=patient.id,
            doctor_id=test_doctor.id,
            content=fake.paragraph(nb_sentences=4),
            created_at=note_date,
            updated_at=note_date
        )
        db.session.add(note)
    
    # Aggiungi osservazioni vitali
    # - Frequenza cardiaca
    for _ in range(10):
        observation_date = datetime.utcnow() - timedelta(days=random.randint(1, 90))
        heart_rates = [random.randint(60, 100) for _ in range(5)]
        content = json.dumps([
            {"value": hr, "timestamp": (observation_date + timedelta(hours=i)).isoformat()} 
            for i, hr in enumerate(heart_rates)
        ])
        
        observation = VitalObservation(
            patient_id=patient.id,
            doctor_id=test_doctor.id,
            vital_type=VitalSignType.HEART_RATE,
            content=content,
            start_date=observation_date,
            end_date=observation_date + timedelta(hours=len(heart_rates) - 1),
            created_at=observation_date,
            updated_at=observation_date
        )
        db.session.add(observation)
    
    # - Passi
    for _ in range(30):
        observation_date = datetime.utcnow() - timedelta(days=random.randint(1, 90))
        steps = random.randint(3000, 15000)
        content = json.dumps([{"value": steps, "timestamp": observation_date.isoformat()}])
        
        observation = VitalObservation(
            patient_id=patient.id,
            doctor_id=test_doctor.id,
            vital_type=VitalSignType.STEPS,
            content=content,
            start_date=observation_date,
            end_date=observation_date + timedelta(days=1),
            created_at=observation_date,
            updated_at=observation_date
        )
        db.session.add(observation)
    
    # - Temperatura
    for _ in range(5):
        observation_date = datetime.utcnow() - timedelta(days=random.randint(1, 90))
        temperature = round(random.uniform(36.2, 37.8), 1)
        content = json.dumps([{"value": temperature, "timestamp": observation_date.isoformat()}])
        
        observation = VitalObservation(
            patient_id=patient.id,
            doctor_id=test_doctor.id,
            vital_type=VitalSignType.TEMPERATURE_CORE,
            content=content,
            start_date=observation_date,
            end_date=observation_date,
            created_at=observation_date,
            updated_at=observation_date
        )
        db.session.add(observation)
    
    db.session.commit()
    return patient

@pytest.fixture(scope='function')
def connected_patient(client, test_doctor):
    """Fixture per creare un paziente già connesso a una piattaforma sanitaria."""
    patient = Patient(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=50),
        gender="Female",
        contact_number=fake.phone_number(),
        address=fake.address(),
        connected_platform=HealthPlatform.FITBIT,
        platform_access_token="mock_access_token",
        platform_refresh_token="mock_refresh_token",
        platform_token_expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    from app.app import db
    db.session.add(patient)
    db.session.commit()
    
    # Associa il paziente al dottore
    test_doctor.add_patient(patient)
    
    return patient

@pytest.fixture(scope='function')
def api_client(client, test_doctor):
    """Fixture per un client che utilizza l'API con token JWT."""
    # Prima otteniamo un token di accesso
    response = client.post(
        '/api/login',
        json={
            'email': 'doctor@example.com',
            'password': 'Password123!'
        }
    )
    token = json.loads(response.data)['access_token']
    
    # Crea una classe semplice per racchiudere il client e il token
    class ApiClient:
        def __init__(self, client, token):
            self.client = client
            self.token = token
            self.headers = {'Authorization': f'Bearer {token}'}
        
        def get(self, url):
            return self.client.get(url, headers=self.headers)
        
        def post(self, url, json=None):
            return self.client.post(url, json=json, headers=self.headers)
        
        def put(self, url, json=None):
            return self.client.put(url, json=json, headers=self.headers)
        
        def delete(self, url):
            return self.client.delete(url, headers=self.headers)
    
    return ApiClient(client, token)
