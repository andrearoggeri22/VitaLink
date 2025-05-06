"""
Test module for data models.

This module tests the database models and their relationships:
- Doctor model and authentication functions
- Patient model and relationships
- Notes and observations models
- Audit log functionality
- Health platform integration models
"""
from datetime import datetime, date, timedelta
from uuid import UUID

from app.models import (
    VitalSignType, Note, VitalObservation, HealthPlatform, ActionType,
    EntityType, HealthPlatformLink, AuditLog
)
from app.app import db


class TestModels:
    """Test class for database models.
    
    This class contains test cases for all database models in the application,
    including their relationships, methods, and validations.
    """

    def test_doctor_model(self, doctor_factory):
        """Test Doctor model creation and methods.
        
        Verifies that a Doctor instance can be created with the correct attributes,
        that passwords are properly hashed and can be verified, and that the to_dict
        method returns the expected representation.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
        """
        # Test creation
        doctor = doctor_factory(
            email="test.doctor@example.com",
            first_name="Test",
            last_name="Doctor",
            specialty="General Medicine"
        )
        
        # Verify doctor was created correctly
        assert doctor.id is not None
        assert doctor.email == "test.doctor@example.com"
        assert doctor.first_name == "Test"
        assert doctor.last_name == "Doctor"
        assert doctor.specialty == "General Medicine"
        
        # Test password hash
        assert doctor.password_hash is not None
        assert doctor.password_hash != "Password123!"  # Password should be hashed
        assert doctor.check_password("Password123!") is True
        assert doctor.check_password("WrongPassword") is False
        
        # Test to_dict method
        doctor_dict = doctor.to_dict()
        assert doctor_dict['id'] == doctor.id
        assert doctor_dict['email'] == doctor.email
        assert doctor_dict['first_name'] == doctor.first_name
        assert doctor_dict['last_name'] == doctor.last_name
        assert doctor_dict['specialty'] == doctor.specialty
        assert 'password_hash' not in doctor_dict  # Password hash should not be exposed in serialized data
        
        # Test timestamps
        assert isinstance(doctor.created_at, datetime)
        assert isinstance(doctor.updated_at, datetime)

    def test_patient_model(self, patient_factory):
        """Test Patient model creation and methods.
        
        Verifies that a Patient instance can be created with the correct attributes,
        that the UUID is properly generated, and that the to_dict method returns
        the expected representation. Also checks that health platform fields are
        initialized as null.
        
        Args:
            patient_factory: Factory fixture to create Patient instances
        """
        # Test creation
        dob = date(1985, 5, 15)
        patient = patient_factory(
            first_name="Test",
            last_name="Patient",
            date_of_birth=dob,
            gender="Male",
            contact_number="+391234567890",
            email="test.patient@example.com",
            address="123 Test Street"
        )
        
        # Verify patient was created correctly
        assert patient.id is not None
        assert isinstance(UUID(patient.uuid), UUID)  # Verify UUID is in valid format
        assert patient.first_name == "Test"
        assert patient.last_name == "Patient"
        assert patient.date_of_birth == dob
        assert patient.gender == "Male"
        assert patient.contact_number == "+391234567890"
        assert patient.email == "test.patient@example.com"
        assert patient.address == "123 Test Street"
        
        # Test to_dict method
        patient_dict = patient.to_dict()
        assert patient_dict['id'] == patient.id
        assert patient_dict['uuid'] == patient.uuid
        assert patient_dict['first_name'] == patient.first_name
        assert patient_dict['last_name'] == patient.last_name
        assert patient_dict['date_of_birth'] == dob.isoformat()
        assert patient_dict['gender'] == patient.gender
        
        # Test health platform fields
        assert patient.connected_platform is None
        assert patient.platform_access_token is None
        assert patient.platform_refresh_token is None
        assert patient.platform_token_expires_at is None

    def test_doctor_patient_relationship(self, doctor_factory, patient_factory):
        """Test the many-to-many relationship between doctors and patients.
        
        Verifies that doctors can be associated with multiple patients and
        vice versa. Tests both sides of the relationship and confirms that 
        the relationship is properly established in the database.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        # Create doctors and patients
        doctor1 = doctor_factory()
        doctor2 = doctor_factory()
        patient1 = patient_factory()
        patient2 = patient_factory()
        
        # Associate doctors with patients
        doctor1.add_patient(patient1)
        doctor1.add_patient(patient2)
        doctor2.add_patient(patient1)
        
        # Check relationships
        assert patient1 in doctor1.get_patients()
        assert patient2 in doctor1.get_patients()
        assert patient1 in doctor2.get_patients()
        assert patient2 not in doctor2.get_patients()
        
        # Check reverse relationships through query
        patient1_doctors = list(patient1.doctors)
        patient2_doctors = list(patient2.doctors)
        
        assert doctor1 in patient1_doctors
        assert doctor2 in patient1_doctors
        assert doctor1 in patient2_doctors
        assert doctor2 not in patient2_doctors
          # Test removing patients
        doctor1.remove_patient(patient1)
        assert patient1 not in doctor1.get_patients()
        assert patient1 in doctor2.get_patients()  # Verify patient1 remains associated with doctor2

    def test_note_model(self, doctor_factory, patient_factory):
        """Test Note model creation and relationships.
        
        Verifies that a Note instance can be created with the correct attributes,
        that it's properly associated with a doctor and patient, and that
        timestamps are correctly set.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        
        # Create a note
        note = Note(
            doctor_id=doctor.id,
            patient_id=patient.id,
            content="Test note content"
        )
        db.session.add(note)
        db.session.commit()
        
        # Verify note was created correctly
        assert note.id is not None
        assert note.doctor_id == doctor.id
        assert note.patient_id == patient.id
        assert note.content == "Test note content"
        
        # Test relationships
        assert note.doctor.id == doctor.id
        assert note.patient.id == patient.id
        
        # Test timestamps
        assert isinstance(note.created_at, datetime)
        assert note.created_at is not None
        
        # Test to_dict method
        note_dict = note.to_dict()
        assert note_dict['id'] == note.id
        assert note_dict['content'] == note.content
        assert isinstance(note_dict['created_at'], str)  # DateTime should be converted to string in serialized data
        assert note_dict['doctor_id'] == doctor.id
        assert note_dict['patient_id'] == patient.id

    def test_vital_observation_model(self, doctor_factory, patient_factory):
        """Test VitalObservation model creation and relationships.
        
        Verifies that a VitalObservation instance can be created with the correct attributes,
        that it's properly associated with a doctor and patient, and that
        vital signs can be filtered by type and date range.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # Create observation
        observation = VitalObservation(
            doctor_id=doctor.id,
            patient_id=patient.id,
            vital_type=VitalSignType.HEART_RATE,
            content="Heart rate has been stable",
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(observation)
        db.session.commit()
        
        # Verify observation was created correctly
        assert observation.id is not None
        assert observation.doctor_id == doctor.id
        assert observation.patient_id == patient.id
        assert observation.vital_type == VitalSignType.HEART_RATE
        assert observation.content == "Heart rate has been stable"
        assert observation.start_date == start_date
        assert observation.end_date == end_date
        
        # Test relationships
        assert observation in doctor.vital_observations.all()
        assert observation in patient.vital_observations.all()
        
        # Test filtering observations by vital type
        filtered_observations = patient.get_vital_observations(
            vital_type=VitalSignType.HEART_RATE
        )
        assert observation in filtered_observations
        
        # Test filtering observations by date range
        filtered_observations = patient.get_vital_observations(
            start_date=start_date - timedelta(days=1),
            end_date=end_date + timedelta(days=1)
        )
        assert observation in filtered_observations
        
        # Test to_dict method
        observation_dict = observation.to_dict()
        assert observation_dict['id'] == observation.id
        assert observation_dict['vital_type'] == observation.vital_type.value
        assert observation_dict['content'] == observation.content
        assert observation_dict['doctor_id'] == doctor.id
        assert observation_dict['patient_id'] == patient.id

    def test_health_platform_link_model(self, doctor_factory, patient_factory):
        """Test HealthPlatformLink model creation and methods.
        
        Verifies that a HealthPlatformLink instance can be created with the correct attributes,
        that UUIDs are properly generated, and that expiration functionality works correctly.
        Also tests the relationships with doctors and patients.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        
        # Create health platform link
        link = HealthPlatformLink(
            patient_id=patient.id,
            doctor_id=doctor.id,
            platform=HealthPlatform.FITBIT
        )
        db.session.add(link)
        db.session.commit()
        
        # Verify link was created correctly
        assert link.id is not None
        assert isinstance(UUID(link.uuid), UUID)  # Verify UUID is in valid format
        assert link.patient_id == patient.id
        assert link.doctor_id == doctor.id
        assert link.platform == HealthPlatform.FITBIT
        assert link.used is False
        assert link.created_at is not None
        assert link.expires_at > datetime.utcnow()
        
        # Test relationships
        assert link in patient.health_platform_links.all()
        assert link in doctor.health_platform_links.all()
        
        # Test expiration method
        assert link.is_expired() is False
          # Simulate expired link
        link.expires_at = datetime.utcnow() - timedelta(minutes=5)
        db.session.add(link)
        db.session.commit()
        assert link.is_expired() is True
        
        # Test updating the used flag directly
        link.used = True
        db.session.add(link)
        db.session.commit()
        assert link.used is True

    def test_audit_log_model(self, doctor_factory, patient_factory):
        """Test AuditLog model creation and methods.
        
        Verifies that an AuditLog instance can be created with the correct attributes,
        that JSON details are properly stored and retrieved, and that the to_dict
        method returns the expected representation.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        
        # Create audit log entry
        details = {"action": "test", "value": 123}
        audit_log = AuditLog(
            doctor_id=doctor.id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.PATIENT,
            entity_id=patient.id,
            details=details,
            patient_id=patient.id,
            ip_address="127.0.0.1"
        )
        db.session.add(audit_log)
        db.session.commit()
        
        # Verify audit log was created correctly
        assert audit_log.id is not None
        assert audit_log.doctor_id == doctor.id
        assert audit_log.action_type == ActionType.CREATE
        assert audit_log.entity_type == EntityType.PATIENT
        assert audit_log.entity_id == patient.id
        assert audit_log.patient_id == patient.id
        assert audit_log.ip_address == "127.0.0.1"
        assert audit_log.timestamp is not None
        
        # Test get_details method
        log_details = audit_log.get_details()
        assert log_details['action'] == "test"
        assert log_details['value'] == 123
        
        # Test to_dict method
        audit_dict = audit_log.to_dict()
        assert audit_dict['id'] == audit_log.id
        assert audit_dict['action_type'] == ActionType.CREATE.value
        assert audit_dict['entity_type'] == EntityType.PATIENT.value
        assert audit_dict['entity_id'] == patient.id
        assert 'timestamp' in audit_dict
        assert 'doctor_id' in audit_dict
        assert 'patient_id' in audit_dict

    def test_vital_sign_type_enum(self):
        """Test VitalSignType enum values.
        
        Verifies that the VitalSignType enum contains the correct string values
        for each vital sign type category (vital parameters, physical activity metrics,
        and other health metrics).
        """
        # Test main vital parameters
        assert VitalSignType.HEART_RATE.value == 'heart_rate'
        assert VitalSignType.OXYGEN_SATURATION.value == 'oxygen_saturation'
        assert VitalSignType.BREATHING_RATE.value == 'breathing_rate'
        assert VitalSignType.WEIGHT.value == 'weight'
        assert VitalSignType.TEMPERATURE_CORE.value == 'temperature_core'
        
        # Test physical activity metrics
        assert VitalSignType.STEPS.value == 'steps'
        assert VitalSignType.CALORIES.value == 'calories'
        assert VitalSignType.DISTANCE.value == 'distance'
        assert VitalSignType.ACTIVE_MINUTES.value == 'active_minutes'
        
        # Test other metrics
        assert VitalSignType.SLEEP_DURATION.value == 'sleep_duration'
        assert VitalSignType.WATER.value == 'water'

    def test_action_type_enum(self):
        """Test ActionType enum values.
        
        Verifies that the ActionType enum contains the correct string values
        for all supported action types in the audit logging system.
        """
        assert ActionType.CREATE.value == 'CREATE'
        assert ActionType.UPDATE.value == 'UPDATE'
        assert ActionType.DELETE.value == 'DELETE'
        assert ActionType.VIEW.value == 'VIEW'
        assert ActionType.EXPORT.value == 'EXPORT'
        assert ActionType.GENERATE_LINK.value == 'GENERATE_LINK'
        assert ActionType.CONNECT.value == 'CONNECT'
        assert ActionType.DISCONNECT.value == 'DISCONNECT'
        assert ActionType.SYNC.value == 'SYNC'
        assert ActionType.IMPORT.value == 'IMPORT'

    def test_entity_type_enum(self):
        """Test EntityType enum values.
        
        Verifies that the EntityType enum contains the correct string values
        for all supported entity types in the system that can be audited.
        """
        assert EntityType.PATIENT.value == 'patient'
        assert EntityType.VITAL_SIGN.value == 'vital_sign'
        assert EntityType.NOTE.value == 'note'
        assert EntityType.REPORT.value == 'report'
        assert EntityType.HEALTH_PLATFORM.value == 'health_platform'
        assert EntityType.HEALTH_LINK.value == 'health_link'
        assert EntityType.OBSERVATION.value == 'observation'

    def test_health_platform_enum(self):
        """Test HealthPlatform enum values.
        
        Verifies that the HealthPlatform enum contains the correct string values
        for all supported external health platforms that can be integrated with the system.
        """
        assert HealthPlatform.FITBIT.value == 'fitbit'
        assert HealthPlatform.GOOGLE_HEALTH_CONNECT.value == 'google_health_connect'
        assert HealthPlatform.APPLE_HEALTH.value == 'apple_health'
