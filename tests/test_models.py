import pytest
import uuid
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash

from app import app, db
from models import Doctor, Patient, VitalSign, Note, VitalSignType, DataOrigin, DoctorPatient

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_doctor_model(client):
    """Test the Doctor model functionality."""
    with app.app_context():
        # Create a doctor
        doctor = Doctor(
            email="doctor@example.com",
            first_name="John",
            last_name="Doe",
            specialty="Cardiology"
        )
        doctor.set_password("securepassword")
        
        # Add to database
        db.session.add(doctor)
        db.session.commit()
        
        # Retrieve and verify
        saved_doctor = Doctor.query.filter_by(email="doctor@example.com").first()
        assert saved_doctor is not None
        assert saved_doctor.first_name == "John"
        assert saved_doctor.last_name == "Doe"
        assert saved_doctor.specialty == "Cardiology"
        assert check_password_hash(saved_doctor.password_hash, "securepassword")
        assert saved_doctor.check_password("securepassword")
        assert not saved_doctor.check_password("wrongpassword")
        
        # Test to_dict method
        doctor_dict = saved_doctor.to_dict()
        assert doctor_dict['email'] == "doctor@example.com"
        assert doctor_dict['first_name'] == "John"
        assert doctor_dict['last_name'] == "Doe"
        assert doctor_dict['specialty'] == "Cardiology"

def test_patient_model(client):
    """Test the Patient model functionality."""
    with app.app_context():
        # Create a patient
        patient = Patient(
            first_name="Jane",
            last_name="Smith",
            date_of_birth=datetime(1990, 5, 15).date(),
            gender="Female",
            contact_number="123-456-7890",
            address="123 Main St, Anytown, USA"
        )
        
        # Add to database
        db.session.add(patient)
        db.session.commit()
        
        # Retrieve and verify
        saved_patient = Patient.query.filter_by(first_name="Jane").first()
        assert saved_patient is not None
        assert saved_patient.last_name == "Smith"
        assert saved_patient.date_of_birth == datetime(1990, 5, 15).date()
        assert saved_patient.gender == "Female"
        assert saved_patient.contact_number == "123-456-7890"
        assert saved_patient.address == "123 Main St, Anytown, USA"
        assert saved_patient.uuid is not None
        
        # Test to_dict method
        patient_dict = saved_patient.to_dict()
        assert patient_dict['first_name'] == "Jane"
        assert patient_dict['last_name'] == "Smith"
        assert patient_dict['gender'] == "Female"

def test_vital_sign_model(client):
    """Test the VitalSign model functionality."""
    with app.app_context():
        # Create a patient
        patient = Patient(
            first_name="Vital",
            last_name="Test",
            date_of_birth=datetime(1985, 3, 10).date()
        )
        db.session.add(patient)
        db.session.flush()
        
        # Create vital signs
        heart_rate = VitalSign(
            patient_id=patient.id,
            type=VitalSignType.HEART_RATE,
            value=75.0,
            unit="bpm",
            recorded_at=datetime.utcnow(),
            origin=DataOrigin.MANUAL
        )
        
        blood_pressure = VitalSign(
            patient_id=patient.id,
            type=VitalSignType.BLOOD_PRESSURE,
            value=120.0,
            unit="mmHg",
            recorded_at=datetime.utcnow(),
            origin=DataOrigin.AUTOMATIC
        )
        
        db.session.add_all([heart_rate, blood_pressure])
        db.session.commit()
        
        # Retrieve and verify
        saved_vitals = VitalSign.query.filter_by(patient_id=patient.id).all()
        assert len(saved_vitals) == 2
        
        # Test to_dict method
        hr_dict = next(v for v in saved_vitals if v.type == VitalSignType.HEART_RATE).to_dict()
        assert hr_dict['type'] == "heart_rate"
        assert hr_dict['value'] == 75.0
        assert hr_dict['unit'] == "bpm"
        assert hr_dict['origin'] == "manual"
        
        bp_dict = next(v for v in saved_vitals if v.type == VitalSignType.BLOOD_PRESSURE).to_dict()
        assert bp_dict['type'] == "blood_pressure"
        assert bp_dict['value'] == 120.0
        assert bp_dict['unit'] == "mmHg"
        assert bp_dict['origin'] == "automatic"

def test_note_model(client):
    """Test the Note model functionality."""
    with app.app_context():
        # Create a doctor and patient
        doctor = Doctor(
            email="note_test@example.com",
            first_name="Note",
            last_name="Doctor"
        )
        db.session.add(doctor)
        
        patient = Patient(
            first_name="Note",
            last_name="Patient",
            date_of_birth=datetime(1980, 1, 1).date()
        )
        db.session.add(patient)
        db.session.flush()
        
        # Create a note
        note = Note(
            patient_id=patient.id,
            doctor_id=doctor.id,
            content="This is a test note about the patient."
        )
        db.session.add(note)
        db.session.commit()
        
        # Retrieve and verify
        saved_note = Note.query.filter_by(patient_id=patient.id).first()
        assert saved_note is not None
        assert saved_note.content == "This is a test note about the patient."
        assert saved_note.doctor_id == doctor.id
        
        # Test to_dict method
        note_dict = saved_note.to_dict()
        assert note_dict['content'] == "This is a test note about the patient."
        assert note_dict['patient_id'] == patient.id
        assert note_dict['doctor_id'] == doctor.id

def test_doctor_patient_relationship(client):
    """Test the many-to-many relationship between doctors and patients."""
    with app.app_context():
        # Create doctors
        doctor1 = Doctor(email="doctor1@example.com", first_name="Doctor", last_name="One")
        doctor2 = Doctor(email="doctor2@example.com", first_name="Doctor", last_name="Two")
        db.session.add_all([doctor1, doctor2])
        
        # Create patients
        patient1 = Patient(first_name="Patient", last_name="One", date_of_birth=datetime(1990, 1, 1).date())
        patient2 = Patient(first_name="Patient", last_name="Two", date_of_birth=datetime(1990, 1, 2).date())
        patient3 = Patient(first_name="Patient", last_name="Three", date_of_birth=datetime(1990, 1, 3).date())
        db.session.add_all([patient1, patient2, patient3])
        db.session.flush()
        
        # Associate doctors with patients
        doctor1.add_patient(patient1)
        doctor1.add_patient(patient2)
        doctor2.add_patient(patient2)
        doctor2.add_patient(patient3)
        
        # Test associations
        assert len(doctor1.get_patients()) == 2
        assert len(doctor2.get_patients()) == 2
        assert patient1 in doctor1.get_patients()
        assert patient2 in doctor1.get_patients()
        assert patient2 in doctor2.get_patients()
        assert patient3 in doctor2.get_patients()
        
        # Test removing associations
        doctor1.remove_patient(patient1)
        assert len(doctor1.get_patients()) == 1
        assert patient1 not in doctor1.get_patients()
        
        # Check association timestamps
        association = DoctorPatient.query.filter_by(doctor_id=doctor1.id, patient_id=patient2.id).first()
        assert association is not None
        assert association.assigned_date is not None

def test_patient_vital_signs_filtering(client):
    """Test filtering of vital signs by patient."""
    with app.app_context():
        # Create a patient
        patient = Patient(
            first_name="Filter",
            last_name="Test",
            date_of_birth=datetime(1975, 6, 20).date()
        )
        db.session.add(patient)
        db.session.flush()
        
        # Create vital signs at different times
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        vitals = [
            VitalSign(
                patient_id=patient.id,
                type=VitalSignType.HEART_RATE,
                value=70.0,
                unit="bpm",
                recorded_at=week_ago,
                origin=DataOrigin.MANUAL
            ),
            VitalSign(
                patient_id=patient.id,
                type=VitalSignType.BLOOD_PRESSURE,
                value=118.0,
                unit="mmHg",
                recorded_at=yesterday,
                origin=DataOrigin.MANUAL
            ),
            VitalSign(
                patient_id=patient.id,
                type=VitalSignType.HEART_RATE,
                value=72.0,
                unit="bpm",
                recorded_at=now,
                origin=DataOrigin.AUTOMATIC
            )
        ]
        db.session.add_all(vitals)
        db.session.commit()
        
        # Test filtering by type
        heart_rate_vitals = patient.get_vital_signs(type=VitalSignType.HEART_RATE.value)
        assert len(heart_rate_vitals) == 2
        
        # Test filtering by date
        recent_vitals = patient.get_vital_signs(start_date=yesterday)
        assert len(recent_vitals) == 2
        
        old_vitals = patient.get_vital_signs(end_date=yesterday)
        assert len(old_vitals) == 2
        
        # Test combined filtering
        recent_heart_rate = patient.get_vital_signs(
            type=VitalSignType.HEART_RATE.value,
            start_date=yesterday
        )
        assert len(recent_heart_rate) == 1
        assert recent_heart_rate[0].value == 72.0

def test_patient_notes(client):
    """Test patient notes functionality."""
    with app.app_context():
        # Create a doctor and patient
        doctor = Doctor(email="notes_test@example.com", first_name="Notes", last_name="Doctor")
        db.session.add(doctor)
        
        patient = Patient(first_name="Notes", last_name="Patient", date_of_birth=datetime(1980, 1, 1).date())
        db.session.add(patient)
        db.session.flush()
        
        # Create multiple notes
        notes = [
            Note(patient_id=patient.id, doctor_id=doctor.id, content="First note"),
            Note(patient_id=patient.id, doctor_id=doctor.id, content="Second note"),
            Note(patient_id=patient.id, doctor_id=doctor.id, content="Third note")
        ]
        db.session.add_all(notes)
        db.session.commit()
        
        # Test retrieving all notes
        patient_notes = patient.get_notes()
        assert len(patient_notes) == 3
        
        # Verify they're in reverse chronological order (newest first)
        assert patient_notes[0].content == "Third note"
        assert patient_notes[1].content == "Second note"
        assert patient_notes[2].content == "First note"

def test_uuid_generation(client):
    """Test automatic UUID generation for patients."""
    with app.app_context():
        # Create multiple patients
        patients = [
            Patient(first_name="UUID1", last_name="Test", date_of_birth=datetime(1980, 1, 1).date()),
            Patient(first_name="UUID2", last_name="Test", date_of_birth=datetime(1980, 1, 2).date()),
            Patient(first_name="UUID3", last_name="Test", date_of_birth=datetime(1980, 1, 3).date())
        ]
        db.session.add_all(patients)
        db.session.commit()
        
        # Retrieve patients
        saved_patients = Patient.query.filter(Patient.first_name.like("UUID%")).all()
        
        # Verify UUIDs
        for patient in saved_patients:
            assert patient.uuid is not None
            
            # Verify UUID is valid format
            try:
                uuid_obj = uuid.UUID(patient.uuid)
                assert str(uuid_obj) == patient.uuid
            except ValueError:
                pytest.fail(f"Invalid UUID format: {patient.uuid}")
        
        # Verify UUIDs are unique
        uuids = [patient.uuid for patient in saved_patients]
        assert len(uuids) == len(set(uuids))
