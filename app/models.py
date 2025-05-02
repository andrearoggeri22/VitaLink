"""
Data Models Module.

This module defines the database models and their relationships for the VitaLink application.
It includes models for doctors, patients, medical notes, vital sign observations,
audit logs, and health platform integrations.

The models use SQLAlchemy ORM for database interactions and follow a relational
database design with appropriate foreign key relationships. Each model includes
methods for serialization, password handling (where applicable), and other utility
functions related to their specific domain.

Key models include:
- Doctor: Medical professionals using the system
- Patient: Individuals receiving care and being monitored
- Note: Medical notes created by doctors about patients
- VitalObservation: Medical interpretations of vital sign data
- AuditLog: Tracking of all system actions for compliance
- HealthPlatformLink: Integration with external health data sources

Enums in this module define standardized types for vital signs, health platforms,
and audit-related classifications.
"""

import uuid
import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .app import db

# Models for the VitaLink application
# Defines the main data entities and their relationships

class VitalSignType(Enum):
    """
    Enumeration of all supported vital sign and health metric types.
    
    This enum defines standardized identifiers for various health metrics and vital signs
    that can be tracked in the system. Each enum value corresponds to a specific type of
    health data that can be imported from health platforms, manually recorded, or analyzed.
    
    The enum is grouped into categories:
    1. Main vital parameters: Core physiological measurements
    2. Physical activity: Movement and exercise metrics
    3. Metabolism and detailed activity: Energy expenditure and activity breakdown
    4. Nutrition and hydration: Food and fluid intake
    
    Each enum value stores a string identifier used in APIs and database storage.
    """
    # Main vital parameters
    HEART_RATE = "heart_rate"
    OXYGEN_SATURATION = "oxygen_saturation"
    BREATHING_RATE = "breathing_rate"
    WEIGHT = "weight"
    TEMPERATURE_CORE = "temperature_core"
    TEMPERATURE_SKIN = "temperature_skin"
    
    # Physical activity parameters
    STEPS = "steps"
    CALORIES = "calories"
    DISTANCE = "distance"
    ACTIVE_MINUTES = "active_minutes"
    SLEEP_DURATION = "sleep_duration"
    FLOORS_CLIMBED = "floors_climbed"
    ELEVATION = "elevation"
    
    # Metabolism and detailed activity
    ACTIVITY_CALORIES = "activity_calories"
    CALORIES_BMR = "calories_bmr"
    MINUTES_SEDENTARY = "minutes_sedentary"
    MINUTES_LIGHTLY_ACTIVE = "minutes_lightly_active"
    MINUTES_FAIRLY_ACTIVE = "minutes_fairly_active"
    
    # Nutrition and hydration
    CALORIES_IN = "calories_in"
    WATER = "water"

class DoctorPatient(db.Model):
    """
    Association model between doctors and patients.
    
    This model implements the many-to-many relationship between doctors and patients,
    allowing each doctor to be associated with multiple patients and each patient
    to be associated with multiple doctors. This supports collaborative care scenarios
    where multiple healthcare providers may treat the same patient.
    
    The model includes a timestamp of when the association was created, allowing
    the system to track when a doctor began caring for a specific patient.
    
    Attributes:
        doctor_id (int): Foreign key to the doctor table, part of composite primary key
        patient_id (int): Foreign key to the patient table, part of composite primary key
        assigned_date (datetime): When this association was created
    """
    __tablename__ = 'doctor_patient'
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), primary_key=True)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)

class Doctor(UserMixin, db.Model):
    """
    Model representing a medical professional in the system.
    
    This model stores information about doctors who use the VitaLink system.
    It extends Flask-Login's UserMixin to provide user authentication functionality.
    Doctors can be associated with multiple patients, create medical notes,
    and record vital sign observations.
    
    Attributes:
        id (int): Primary key and unique identifier
        email (str): Email address used for login, must be unique
        password_hash (str): Securely hashed password, never stored in plaintext
        first_name (str): Doctor's first name
        last_name (str): Doctor's last name
        specialty (str): Medical specialty or area of practice
        created_at (datetime): When the doctor account was created
        updated_at (datetime): When the doctor account was last updated
        patients (relationship): Many-to-many relationship with Patient model
        notes (relationship): One-to-many relationship with Note model
        vital_observations (relationship): One-to-many relationship with VitalObservation model
    """
    __tablename__ = 'doctor'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with patients (many-to-many)
    patients = db.relationship('Patient', 
                              secondary='doctor_patient',
                              backref=db.backref('doctors', lazy='dynamic'),
                              lazy='dynamic')
    
    # Notes and observations created by this doctor
    notes = db.relationship('Note', backref='doctor', lazy='dynamic')
    vital_observations = db.relationship('VitalObservation', backref='doctor', lazy='dynamic')

    def set_password(self, password):
        """
        Set the doctor's password hash.
        
        This method securely hashes the provided password using Werkzeug's
        generate_password_hash function and stores the hash in the database.
        The original password is never stored in plaintext.
        
        Args:
            password (str): The plain text password to hash
                    
        Returns:
            None
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Check if the provided password matches the stored hash.
        
        This method verifies the provided password against the stored hash
        using Werkzeug's check_password_hash function, which is resistant
        to timing attacks.
        
        Args:
            password (str): The plain text password to verify
                    
        Returns:
            bool: True if the password is correct, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    def to_dict(self):
        """
        Convert the doctor object to a serializable dictionary.
        
        This method creates a dictionary representation of the Doctor object
        suitable for JSON serialization in API responses. It formats datetime
        objects as ISO 8601 strings and includes all relevant doctor attributes
        except for the password hash.
        
        Returns:
            dict: Dictionary containing the doctor's attributes
                  with datetimes converted to ISO format strings
        """
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'specialty': self.specialty,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    def get_patients(self):
        """
        Get all patients associated with this doctor.
        
        This method retrieves all Patient objects that have been linked to this doctor
        through the DoctorPatient association table. This represents the doctor's
        current patient roster.
        
        Returns:
            list: List of Patient objects associated with the doctor
        """
        return self.patients.all()
    def add_patient(self, patient):
        """
        Add a patient to this doctor's patient list.
        
        This method establishes a doctor-patient relationship by creating a new
        entry in the DoctorPatient association table. If the relationship already
        exists, no action is taken. The method handles the database session
        and commits the change.
        
        Args:
            patient (Patient): Patient object to add to this doctor's care
        
        Returns:
            None
        """
        if patient not in self.patients.all():
            association = DoctorPatient(doctor_id=self.id, patient_id=patient.id)
            db.session.add(association)
            db.session.commit()
    def remove_patient(self, patient):
        """
        Remove a patient from this doctor's patient list.
        
        This method ends a doctor-patient relationship by removing the corresponding
        entry from the DoctorPatient association table. If no such relationship
        exists, no action is taken. The method handles the database session
        and commits the change.
        
        Args:
            patient (Patient): Patient object to remove from this doctor's care
        
        Returns:
            None
        """
        association = DoctorPatient.query.filter_by(doctor_id=self.id, patient_id=patient.id).first()
        if association:
            db.session.delete(association)
            db.session.commit()

class HealthPlatform(Enum):
    """
    Enumeration of health platforms that can be integrated with the system.
    
    This enum defines the health platforms and wearable device ecosystems
    that are supported for data integration. Each platform requires specific
    OAuth2 authentication flows and API endpoints for retrieving health data.
    
    Attributes:
        FITBIT: Integration with Fitbit devices and platform
        GOOGLE_HEALTH_CONNECT: Integration with Google Health Connect
        APPLE_HEALTH: Integration with Apple Health
    """
    FITBIT = "fitbit"
    GOOGLE_HEALTH_CONNECT = "google_health_connect"
    APPLE_HEALTH = "apple_health"

class Patient(db.Model):
    """
    Model representing a patient in the system.
    
    This model stores comprehensive information about patients, including
    their personal details, contact information, and health platform integration.
    The model uses a UUID for secure identification in URLs and APIs, while
    maintaining a standard integer primary key for database relationships.
    
    Patients can be associated with multiple doctors for collaborative care,
    have medical notes, vital sign observations, and connect to external
    health platforms (like Fitbit) to provide real-time health data.
    
    Attributes:
        id (int): Primary key and unique identifier
        uuid (str): Unique UUID used in URLs and APIs
        first_name (str): Patient's first name
        last_name (str): Patient's last name
        date_of_birth (date): Patient's date of birth
        gender (str): Patient's gender
        contact_number (str): Patient's contact phone number
        email (str): Email address used for sending notifications, must be unique
        address (str): Patient's physical address
        created_at (datetime): When the patient record was created
        updated_at (datetime): When the patient record was last updated
        connected_platform (HealthPlatform): Health platform connected to this patient
        platform_access_token (str): OAuth access token for the connected platform
        platform_refresh_token (str): OAuth refresh token for the connected platform
        platform_token_expires_at (datetime): Expiration date of the access token
        notes (relationship): One-to-many relationship with Note model
        vital_observations (relationship): One-to-many relationship with VitalObservation model
    """
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20))
    contact_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Health platform integration
    connected_platform = db.Column(db.Enum(HealthPlatform), nullable=True)
    platform_access_token = db.Column(db.String(1024), nullable=True)
    platform_refresh_token = db.Column(db.String(1024), nullable=True)
    platform_token_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    notes = db.relationship('Note', backref='patient', lazy='dynamic')
    vital_observations = db.relationship('VitalObservation', backref='patient', lazy='dynamic')
    
    def to_dict(self):
        """
        Convert the patient object to a serializable dictionary.
        
        This method creates a dictionary representation of the Patient object
        suitable for JSON serialization in API responses. It formats date and
        datetime objects as ISO 8601 strings.
        
        Returns:
            dict: Dictionary containing all the patient's attributes
                  with dates and datetimes converted to ISO format strings
        """
        return {
            'id': self.id,
            'uuid': self.uuid,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'contact_number': self.contact_number,
            'email': self.email,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_vital_observations(self, vital_type=None, start_date=None, end_date=None):
        """
        Get vital observations for this patient with optional filtering.
        
        This method retrieves vital sign observations associated with the patient,
        with optional filtering by vital sign type and date range. Results are
        ordered by creation date, with the most recent observations first.
        
        Args:
            vital_type (VitalSignType, optional): Type of vital sign to filter by
            start_date (datetime, optional): Start date for filtering
            end_date (datetime, optional): End date for filtering
                    
        Returns:
            list: List of VitalObservation objects that meet the filtering criteria
        """
        query = self.vital_observations
        
        if vital_type:
            query = query.filter_by(vital_type=vital_type)
        
        if start_date:
            query = query.filter(VitalObservation.start_date >= start_date)
        
        if end_date:
            query = query.filter(VitalObservation.end_date <= end_date)
        
        return query.order_by(VitalObservation.created_at.desc()).all()
    
    def get_notes(self):
        """
        Get all medical notes associated with this patient.
        
        This method retrieves all notes created for this patient,
        ordered by creation date with the most recent notes first.
        
        Returns:
            list: List of Note objects ordered by creation date (most recent first)
        """
        return self.notes.order_by(Note.created_at.desc()).all()


class Note(db.Model):
    """
    Model representing a medical note for a patient.
    
    This model stores textual notes created by doctors about patients.
    Notes can include observations, treatment plans, reminders,
    or any other relevant medical information. Each note is associated
    with both a patient and the doctor who created it.
    
    Attributes:
        id (int): Primary key and unique identifier
        patient_id (int): Foreign key to the patient this note is about
        doctor_id (int): Foreign key to the doctor who created this note
        content (str): The text content of the medical note
        created_at (datetime): When the note was created
        updated_at (datetime): When the note was last updated
    """
    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """
        Convert the note object to a serializable dictionary.
        
        This method creates a dictionary representation of the Note object
        suitable for JSON serialization in API responses. It formats datetime
        objects as ISO 8601 strings.
        
        Returns:
            dict: Dictionary containing all the note's attributes
                  with datetimes converted to ISO format strings
        """
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
class VitalObservation(db.Model):
    """
    Model representing medical observations about vital sign data.
    
    This model stores doctors' interpretations and analyses of vital sign data
    over specific time periods. Unlike raw vital sign data points, observations
    represent medical insights, trends, or concerns identified by healthcare 
    professionals after reviewing the data.
    
    Observations have a time range (start to end date) that they cover,
    and include a text commentary from the doctor about what they observed
    in the vital sign data during that period.
    
    Attributes:
        id (int): Primary key and unique identifier
        patient_id (int): Foreign key to the patient this observation is about
        doctor_id (int): Foreign key to the doctor who created this observation
        vital_type (VitalSignType): Type of vital sign being observed
        content (str): Doctor's notes and interpretation of the vital sign data
        start_date (datetime): Beginning of the observation period
        end_date (datetime): End of the observation period
        created_at (datetime): When the observation was created
        updated_at (datetime): When the observation was last updated
    """
    __tablename__ = 'vital_observation'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    vital_type = db.Column(db.Enum(VitalSignType), nullable=False)
    content = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def to_dict(self):
        # Convert the object to a serializable dictionary
        #
        # Returns:
        #   dict: Dictionary representation of the object
        # Load the Doctor model to get the doctor's name
        from .app import db
        doctor = db.session.query(Doctor).get(self.doctor_id)
        
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'doctor_name': f"{doctor.first_name} {doctor.last_name}" if doctor else "Unknown Doctor",
            'vital_type': self.vital_type.value,
            'content': self.content,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ActionType(Enum):
    """
    Enumeration defining the types of actions for the audit log system.
    
    This enum defines all possible action types that can be recorded in the audit log,
    providing standardized identifiers for different types of operations performed 
    in the system. These values help categorize and filter audit logs for 
    reporting and compliance purposes.
    
    Attributes:
        CREATE: Action of creating a new entity
        UPDATE: Action of updating an existing entity
        DELETE: Action of deleting an entity
        VIEW: Action of viewing an entity
        EXPORT: Action of exporting an entity (e.g., report generation)
        GENERATE_LINK: Action of generating a link for health platform integration
        CONNECT: Action of connecting a health platform
        DISCONNECT: Action of disconnecting a health platform
        SYNC: Action of synchronizing data from a health platform
        IMPORT: Action of importing an existing entity
    """
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VIEW = "VIEW"
    EXPORT = "EXPORT"
    GENERATE_LINK = "GENERATE_LINK"
    CONNECT = "CONNECT"
    DISCONNECT = "DISCONNECT"
    SYNC = "SYNC"
    IMPORT = "IMPORT"

class EntityType(Enum):
    """
    Enumeration defining the types of entities that can be tracked in the audit log system.
    
    This enum defines all the different entities for which actions can be recorded
    in the audit log. By categorizing entities, the system can provide more
    targeted filtering and reporting capabilities for audit investigations.
    
    Attributes:
        PATIENT: Patient entity
        VITAL_SIGN: Vital sign entity
        NOTE: Medical note entity
        REPORT: Report/document entity
        HEALTH_PLATFORM: Health platform entity
        HEALTH_LINK: Health platform link entity
        OBSERVATION: Vital observation entity
    """
    PATIENT = "patient"
    VITAL_SIGN = "vital_sign"
    NOTE = "note"
    REPORT = "report"
    HEALTH_PLATFORM = "health_platform"
    HEALTH_LINK = "health_link"
    OBSERVATION = "observation"
    
class HealthPlatformLink(db.Model):
    """
    Model for storing temporary links for health platform integration.
    
    This model manages the temporary connection links that doctors can generate
    for patients to connect their health platforms (like Fitbit, Google Fit).
    These links have a limited validity period (24 hours) and can only be used once.
    
    The system creates a unique URL based on the UUID that patients can use to
    authorize the application to access their health platform data without
    needing to share their health platform credentials directly.
    
    Attributes:
        id (int): Primary key and unique identifier
        uuid (str): Unique UUID for the link, used in URLs
        patient_id (int): Foreign key to the patient this link is for
        doctor_id (int): Foreign key to the doctor who created the link
        created_at (datetime): Link creation date/time
        expires_at (datetime): Link expiration date/time (24 hours after creation)
        used (bool): Whether the link has been used
        platform (HealthPlatform): The health platform this link is for
        patient (relationship): Relationship to the Patient model
        doctor (relationship): Relationship to the Doctor model
    """
    __tablename__ = 'health_platform_link'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    used = db.Column(db.Boolean, default=False)
    platform = db.Column(db.Enum(HealthPlatform), nullable=False)
    
    # Relationships
    patient = db.relationship('Patient', backref=db.backref('health_platform_links', lazy='dynamic'))
    doctor = db.relationship('Doctor', backref=db.backref('health_platform_links', lazy='dynamic'))
    
    def is_expired(self):
        """
        Check if the link has expired.
        
        A link expires 24 hours after creation or if it has already been used.
        This method compares the current time with the expiration timestamp.
        
        Returns:
            bool: True if the link has expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        """
        Convert the link object to a serializable dictionary.
        
        This method creates a dictionary representation of the HealthPlatformLink object
        suitable for JSON serialization in API responses. It formats datetime
        objects as ISO 8601 strings.
        
        Returns:
            dict: Dictionary containing all the link's attributes
                  with datetimes converted to ISO format strings
        """
        return {
            'id': self.id,
            'uuid': self.uuid,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used,
            'platform': self.platform.value if self.platform else None,
        }

class AuditLog(db.Model):
    """
    Model for storing audit logs of all actions performed in the system.
    
    This model is used to track who did what and when, for compliance, security,
    and accountability purposes. Each entry records details about an action
    performed by a specific doctor, including the affected entity, timestamp,
    and additional contextual information.
    
    The audit log is a critical component for healthcare applications where
    maintaining an immutable record of all system activities is essential for
    regulatory compliance (e.g., HIPAA, GDPR) and security incident investigation.
    
    Attributes:
        id (int): Primary key and unique identifier
        doctor_id (int): Foreign key to the doctor who performed the action
        doctor (relationship): Relationship with the doctor who performed the action
        timestamp (datetime): Date and time when the action was performed
        action_type (ActionType): Type of action performed (enum)
        entity_type (EntityType): Type of entity affected by the action (enum)
        entity_id (int): ID of the entity affected by the action
        details (str): Additional details about the action (stored as JSON)
        patient_id (int): Optional foreign key to the patient related to the action
        patient (relationship): Relationship with the patient related to the action
        ip_address (str): IP address from which the action was performed
    """
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    
    # Who performed the action
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    doctor = db.relationship('Doctor')
    
    # When the action was performed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # What type of action was performed
    action_type = db.Column(db.Enum(ActionType), nullable=False)
    
    # Which entity was affected
    entity_type = db.Column(db.Enum(EntityType), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)  # ID of the affected entity
    
    # Additional details about the action (stored as JSON)
    details = db.Column(db.Text)  # JSON string with action details
    
    # Optional patient ID to facilitate queries
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    patient = db.relationship('Patient')
    
    # IP address of the user who performed the action
    ip_address = db.Column(db.String(50))
    
    def __init__(self, doctor_id, action_type, entity_type, entity_id, details=None, patient_id=None, ip_address=None):
        """
        Initialize a new audit log record.
        
        This constructor sets up a new audit log entry with the provided information.
        The timestamp is automatically set to the current UTC time.
        Any JSON-serializable details can be stored to provide additional context
        about the action being logged.
        
        Args:
            doctor_id (int): ID of the doctor who performed the action
            action_type (ActionType): Type of action performed
            entity_type (EntityType): Type of entity affected by the action
            entity_id (int): ID of the entity affected by the action
            details (dict, optional): Additional details about the action
            patient_id (int, optional): ID of the patient related to the action
            ip_address (str, optional): IP address from which the action was performed
        """
        self.doctor_id = doctor_id
        self.action_type = action_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.details = json.dumps(details) if details else None
        self.patient_id = patient_id
        self.ip_address = ip_address
        
    def get_details(self):
        """
        Convert the JSON string of details to a Python dictionary.
        
        This method retrieves the additional details stored as a JSON string
        and deserializes them into a Python dictionary for easier access.
        If no details are stored, an empty dictionary is returned.
        
        Returns:
            dict: The action details as a dictionary
        """
        if self.details:
            return json.loads(self.details)
        return {}
    
    def to_dict(self):
        """
        Convert the audit log object to a serializable dictionary.
        
        This method creates a dictionary representation of the AuditLog object
        suitable for JSON serialization in API responses and for displaying
        in the user interface. It formats the timestamp to UTC+2 timezone
        and includes related entities' display names.
        
        Returns:
            dict: Dictionary containing all the audit log's attributes
                  with properly formatted timestamp and related entity names
        """
        utc_plus_2 = timezone(timedelta(hours=2))
        timestamp = self.timestamp
        if timestamp:
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            timestamp = timestamp.astimezone(utc_plus_2)
            timestamp = timestamp.replace(microsecond=0)
            timestamp_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S')
            timestamp_str = timestamp_str.replace('T', ' ')  # Convert to UTC format
        else:
            timestamp_str = None
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'doctor_name': f"{self.doctor.first_name} {self.doctor.last_name}" if self.doctor else None,
            'timestamp': timestamp_str,
            'action_type': self.action_type.value,
            'entity_type': self.entity_type.value,
            'entity_id': self.entity_id,
            'details': self.get_details(),
            'patient_id': self.patient_id,
            'patient_name': f"{self.patient.first_name} {self.patient.last_name}" if self.patient else None,
            'ip_address': self.ip_address
        }
