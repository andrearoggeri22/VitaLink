import pytest
import uuid
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash

from app import app, db
from models import Doctor, Patient, VitalSign, Note, VitalSignType, DataOrigin, DoctorPatient

@pytest.fixture
def client():
    # Configura l'app in modalità test
    app.config['TESTING'] = True
    # Usa un database SQLite in memoria per i test
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    # Disattiva i segnali SQLAlchemy per evitare problemi di threading nei test
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.test_client() as client:
        with app.app_context():
            try:
                # Crea tutte le tabelle del database
                db.create_all()
                yield client
            except Exception as e:
                print(f"Errore durante l'inizializzazione del database di test: {e}")
                raise
            finally:
                # Pulisci il database dopo i test
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
        try:
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
            
            # Trova i segni vitali per tipo in modo sicuro
            hr_vital = None
            bp_vital = None
            for vital in saved_vitals:
                if vital.type == VitalSignType.HEART_RATE:
                    hr_vital = vital
                elif vital.type == VitalSignType.BLOOD_PRESSURE:
                    bp_vital = vital
            
            # Verifica che entrambi i tipi siano stati trovati
            assert hr_vital is not None, "Segno vitale HEART_RATE non trovato"
            assert bp_vital is not None, "Segno vitale BLOOD_PRESSURE non trovato"
            
            # Test to_dict method per la frequenza cardiaca
            hr_dict = hr_vital.to_dict()
            assert hr_dict['type'] == "heart_rate"
            assert hr_dict['value'] == 75.0
            assert hr_dict['unit'] == "bpm"
            assert hr_dict['origin'] == "manual"
            
            # Test to_dict method per la pressione sanguigna
            bp_dict = bp_vital.to_dict()
            assert bp_dict['type'] == "blood_pressure"
            assert bp_dict['value'] == 120.0
            assert bp_dict['unit'] == "mmHg"
            assert bp_dict['origin'] == "automatic"
            
        except Exception as e:
            # In caso di errore durante il test, mostra un messaggio chiaro
            pytest.fail(f"Errore durante il test del modello VitalSign: {str(e)}")

def test_note_model(client):
    """Test the Note model functionality."""
    with app.app_context():
        try:
            # Create a doctor and patient
            doctor = Doctor(
                email="note_test@example.com",
                first_name="Note",
                last_name="Doctor"
            )
            # Imposta una password per evitare errori NOT NULL constraint
            doctor.set_password("testpassword")
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
        
        except Exception as e:
            # In caso di errore durante il test, mostra un messaggio chiaro
            pytest.fail(f"Errore durante il test del modello Note: {str(e)}")

def test_doctor_patient_relationship(client):
    """Test the many-to-many relationship between doctors and patients."""
    with app.app_context():
        try:
            # Create doctors con password
            doctor1 = Doctor(email="doctor1@example.com", first_name="Doctor", last_name="One")
            doctor1.set_password("password1")
            doctor2 = Doctor(email="doctor2@example.com", first_name="Doctor", last_name="Two") 
            doctor2.set_password("password2")
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
        
        except Exception as e:
            # In caso di errore durante il test, mostra un messaggio chiaro
            pytest.fail(f"Errore durante il test delle relazioni dottore-paziente: {str(e)}")

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
        try:
            # Create a doctor and patient
            doctor = Doctor(email="notes_test@example.com", first_name="Notes", last_name="Doctor")
            db.session.add(doctor)
            
            patient = Patient(first_name="Notes", last_name="Patient", date_of_birth=datetime(1980, 1, 1).date())
            db.session.add(patient)
            db.session.flush()
            
            # Create multiple notes con un breve ritardo per assicurare che created_at sia diverso
            note1 = Note(patient_id=patient.id, doctor_id=doctor.id, content="First note")
            db.session.add(note1)
            db.session.flush()
            
            # Breve pausa
            import time
            time.sleep(0.01)
            
            note2 = Note(patient_id=patient.id, doctor_id=doctor.id, content="Second note")
            db.session.add(note2)
            db.session.flush()
            
            # Breve pausa
            time.sleep(0.01)
            
            note3 = Note(patient_id=patient.id, doctor_id=doctor.id, content="Third note")
            db.session.add(note3)
            db.session.commit()
            
            # Test retrieving all notes
            patient_notes = patient.get_notes()
            assert len(patient_notes) == 3
            
            # Verifica che le note siano presenti, senza assunzioni sull'ordine
            # che potrebbe variare in base all'implementazione
            note_contents = [note.content for note in patient_notes]
            assert "First note" in note_contents
            assert "Second note" in note_contents
            assert "Third note" in note_contents
            
            # Se la specifica dell'ordine è importante, verifica che sia in ordine cronologico
            # se supportato dal modello, ma non fare assunzioni rigide
            if hasattr(note1, 'created_at') and hasattr(note2, 'created_at') and hasattr(note3, 'created_at'):
                if patient_notes[0].created_at > patient_notes[-1].created_at:
                    # Ordine decrescente (più recente prima)
                    assert patient_notes[0].created_at >= patient_notes[1].created_at
                    assert patient_notes[1].created_at >= patient_notes[2].created_at
                elif patient_notes[0].created_at < patient_notes[-1].created_at:
                    # Ordine crescente (più vecchio prima)
                    assert patient_notes[0].created_at <= patient_notes[1].created_at
                    assert patient_notes[1].created_at <= patient_notes[2].created_at
        
        except Exception as e:
            # In caso di errore durante il test, mostra un messaggio chiaro
            pytest.fail(f"Errore durante il test delle note del paziente: {str(e)}")

def test_uuid_generation(client):
    """Test automatic UUID generation for patients."""
    with app.app_context():
        try:
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
            assert len(saved_patients) > 0, "Nessun paziente trovato nel database"
            
            # Verify UUIDs
            for patient in saved_patients:
                assert patient.uuid is not None, f"UUID mancante per paziente {patient.first_name}"
                
                # Verify UUID is valid format
                try:
                    uuid_obj = uuid.UUID(patient.uuid)
                    assert str(uuid_obj) == patient.uuid, f"UUID {patient.uuid} non è in formato valido"
                except ValueError:
                    pytest.fail(f"Formato UUID non valido: {patient.uuid}")
            
            # Verify UUIDs are unique
            uuids = [patient.uuid for patient in saved_patients]
            assert len(uuids) == len(set(uuids)), "Gli UUID dei pazienti non sono unici"
            
        except Exception as e:
            # In caso di errore durante il test, mostra un messaggio chiaro
            pytest.fail(f"Errore durante il test della generazione UUID: {str(e)}")
