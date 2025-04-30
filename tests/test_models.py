"""
Test module for VitaLink database models.
"""
import datetime
import pytest

from app.models import Doctor, Patient, Note, VitalObservation, VitalSignType, ActionType, EntityType


class TestDoctorModel:
    """Test cases for the Doctor model."""
    
    def test_create_doctor(self, session):
        """Test creating a doctor."""
        # Create a doctor
        doctor = Doctor(
            email="doctor@example.com",
            first_name="John",
            last_name="Doe",
            specialty="Cardiology"
        )
        doctor.set_password("password")
        
        # Add the doctor to the database
        session.add(doctor)
        session.commit()
        
        # Retrieve the doctor from the database
        saved_doctor = session.query(Doctor).filter_by(email="doctor@example.com").first()
        
        # Check the doctor's attributes
        assert saved_doctor is not None
        assert saved_doctor.email == "doctor@example.com"
        assert saved_doctor.first_name == "John"
        assert saved_doctor.last_name == "Doe"
        assert saved_doctor.specialty == "Cardiology"
        assert saved_doctor.check_password("password")
        
    def test_to_dict(self, doctor):
        """Test the to_dict method."""
        # Convert the doctor to a dictionary
        doctor_dict = doctor.to_dict()
        
        # Check the dictionary keys
        assert "id" in doctor_dict
        assert "email" in doctor_dict
        assert "first_name" in doctor_dict
        assert "last_name" in doctor_dict
        assert "specialty" in doctor_dict
        assert "created_at" in doctor_dict
        assert "updated_at" in doctor_dict
        
        # Check the dictionary values
        assert doctor_dict["email"] == doctor.email
        assert doctor_dict["first_name"] == doctor.first_name
        assert doctor_dict["last_name"] == doctor.last_name
        assert doctor_dict["specialty"] == doctor.specialty
    
    def test_check_password(self, doctor):
        """Test the check_password method."""
        # Check correct password
        assert doctor.check_password("password")
        
        # Check incorrect password
        assert not doctor.check_password("wrong_password")
    
    def test_add_patient(self, session, doctor, patient):
        """Test adding a patient to a doctor."""
        # Add the patient to the doctor
        doctor.add_patient(patient)
        
        # Check if the patient was added to the doctor
        assert patient in doctor.patients.all()
        
        # Try adding the same patient again (should not duplicate the association)
        doctor.add_patient(patient)
        assert len(doctor.patients.all()) == 1
    
    def test_remove_patient(self, session, doctor, patient):
        """Test removing a patient from a doctor."""
        # Add the patient to the doctor first
        doctor.add_patient(patient)
        assert patient in doctor.patients.all()
        
        # Remove the patient from the doctor
        doctor.remove_patient(patient)
        
        # Check if the patient was removed from the doctor
        assert patient not in doctor.patients.all()


class TestPatientModel:
    """Test cases for the Patient model."""
    
    def test_create_patient(self, session):
        """Test creating a patient."""
        # Create a patient
        patient = Patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime.date(1990, 1, 1),
            gender="Female",
            contact_number="123-456-7890",
            address="123 Main St"
        )
        
        # Add the patient to the database
        session.add(patient)
        session.commit()
        
        # Retrieve the patient from the database
        saved_patient = session.query(Patient).filter_by(first_name="Jane").first()
        
        # Check the patient's attributes
        assert saved_patient is not None
        assert saved_patient.first_name == "Jane"
        assert saved_patient.last_name == "Doe"
        assert saved_patient.date_of_birth == datetime.date(1990, 1, 1)
        assert saved_patient.gender == "Female"
        assert saved_patient.contact_number == "123-456-7890"
        assert saved_patient.address == "123 Main St"
        assert saved_patient.uuid is not None  # UUID should be generated automatically
    
    def test_to_dict(self, patient):
        """Test the to_dict method."""
        # Convert the patient to a dictionary
        patient_dict = patient.to_dict()
        
        # Check the dictionary keys
        assert "id" in patient_dict
        assert "uuid" in patient_dict
        assert "first_name" in patient_dict
        assert "last_name" in patient_dict
        assert "date_of_birth" in patient_dict
        assert "gender" in patient_dict
        assert "contact_number" in patient_dict
        assert "address" in patient_dict
        assert "created_at" in patient_dict
        assert "updated_at" in patient_dict
        
        # Check the dictionary values
        assert patient_dict["first_name"] == patient.first_name
        assert patient_dict["last_name"] == patient.last_name
        assert patient_dict["gender"] == patient.gender
    
    def test_get_vital_observations(self, session, patient, doctor):
        """Test retrieving vital observations for a patient."""
        # Create vital observations
        observation1 = VitalObservation(
            patient_id=patient.id,
            doctor_id=doctor.id,
            vital_type=VitalSignType.HEART_RATE,
            content="Heart rate observation",
            start_date=datetime.datetime.utcnow() - datetime.timedelta(days=2),
            end_date=datetime.datetime.utcnow() - datetime.timedelta(days=1)
        )
        
        observation2 = VitalObservation(
            patient_id=patient.id,
            doctor_id=doctor.id,
            vital_type=VitalSignType.OXYGEN_SATURATION,
            content="Oxygen saturation observation",
            start_date=datetime.datetime.utcnow() - datetime.timedelta(days=1),
            end_date=datetime.datetime.utcnow()
        )
        
        # Add the observations to the database
        session.add(observation1)
        session.add(observation2)
        session.commit()
        
        # Test getting all observations
        observations = patient.get_vital_observations()
        assert len(observations) == 2
        
        # Test filtering by vital type
        observations = patient.get_vital_observations(vital_type=VitalSignType.HEART_RATE)
        assert len(observations) == 1
        assert observations[0].content == "Heart rate observation"
        
        # Test filtering by date range
        observations = patient.get_vital_observations(
            start_date=datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=1),
            end_date=datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        )
        assert len(observations) == 1
        assert observations[0].content == "Oxygen saturation observation"


class TestNoteModel:
    """Test cases for the Note model."""
    
    def test_create_note(self, session, doctor, patient):
        """Test creating a note."""
        # Create a note
        note = Note(
            patient_id=patient.id,
            doctor_id=doctor.id,
            content="Test note content"
        )
        
        # Add the note to the database
        session.add(note)
        session.commit()
        
        # Retrieve the note from the database
        saved_note = session.query(Note).first()
        
        # Check the note's attributes
        assert saved_note is not None
        assert saved_note.patient_id == patient.id
        assert saved_note.doctor_id == doctor.id
        assert saved_note.content == "Test note content"
        assert saved_note.created_at is not None
        assert saved_note.updated_at is not None
    
    def test_to_dict(self, note):
        """Test the to_dict method."""
        # Convert the note to a dictionary
        note_dict = note.to_dict()
        
        # Check the dictionary keys
        assert "id" in note_dict
        assert "patient_id" in note_dict
        assert "doctor_id" in note_dict
        assert "content" in note_dict
        assert "created_at" in note_dict
        assert "updated_at" in note_dict
        
        # Check the dictionary values
        assert note_dict["content"] == note.content
        assert note_dict["patient_id"] == note.patient_id
        assert note_dict["doctor_id"] == note.doctor_id


class TestVitalObservationModel:
    """Test cases for the VitalObservation model."""
    
    def test_create_vital_observation(self, session, doctor, patient):
        """Test creating a vital observation."""
        # Create a vital observation
        observation = VitalObservation(
            patient_id=patient.id,
            doctor_id=doctor.id,
            vital_type=VitalSignType.HEART_RATE,
            content="Heart rate observation content",
            start_date=datetime.datetime.utcnow() - datetime.timedelta(days=1),
            end_date=datetime.datetime.utcnow()
        )
        
        # Add the observation to the database
        session.add(observation)
        session.commit()
        
        # Retrieve the observation from the database
        saved_observation = session.query(VitalObservation).first()
        
        # Check the observation's attributes
        assert saved_observation is not None
        assert saved_observation.patient_id == patient.id
        assert saved_observation.doctor_id == doctor.id
        assert saved_observation.vital_type == VitalSignType.HEART_RATE
        assert saved_observation.content == "Heart rate observation content"
        assert saved_observation.start_date is not None
        assert saved_observation.end_date is not None
        assert saved_observation.created_at is not None
        assert saved_observation.updated_at is not None
    
    def test_to_dict(self, vital_observation, session):
        """Test the to_dict method."""
        # Convert the vital observation to a dictionary
        observation_dict = vital_observation.to_dict()
        
        # Check the dictionary keys
        assert "id" in observation_dict
        assert "patient_id" in observation_dict
        assert "doctor_id" in observation_dict
        assert "doctor_name" in observation_dict
        assert "vital_type" in observation_dict
        assert "content" in observation_dict
        assert "start_date" in observation_dict
        assert "end_date" in observation_dict
        assert "created_at" in observation_dict
        assert "updated_at" in observation_dict
        
        # Check the dictionary values
        assert observation_dict["content"] == vital_observation.content
        assert observation_dict["patient_id"] == vital_observation.patient_id
        assert observation_dict["doctor_id"] == vital_observation.doctor_id
        assert observation_dict["vital_type"] == vital_observation.vital_type.value


class TestEnums:
    """Test cases for the various Enum classes."""
    
    def test_vital_sign_type_enum(self):
        """Test the VitalSignType enum."""
        # Check if the enum has the expected values
        assert VitalSignType.HEART_RATE.value == "heart_rate"
        assert VitalSignType.OXYGEN_SATURATION.value == "oxygen_saturation"
        assert VitalSignType.BREATHING_RATE.value == "breathing_rate"
        assert VitalSignType.STEPS.value == "steps"
        
    def test_action_type_enum(self):
        """Test the ActionType enum."""
        # Check if the enum has the expected values
        assert ActionType.CREATE.value == "CREATE"
        assert ActionType.UPDATE.value == "UPDATE"
        assert ActionType.DELETE.value == "DELETE"
        assert ActionType.VIEW.value == "VIEW"
    
    def test_entity_type_enum(self):
        """Test the EntityType enum."""
        # Check if the enum has the expected values
        assert EntityType.PATIENT.value == "patient"
        assert EntityType.VITAL_SIGN.value == "vital_sign"
        assert EntityType.NOTE.value == "note"
        assert EntityType.REPORT.value == "report"
