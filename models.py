import uuid
import json
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from zoneinfo import ZoneInfo
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

# Models for the VitaLink application
# Defines the main data entities and their relationships

class VitalSignType(Enum):
    # Types of vital signs supported in the system
    # HEART_RATE: Heart rate
    # BLOOD_PRESSURE: Blood pressure
    # OXYGEN_SATURATION: Oxygen saturation
    # TEMPERATURE: Body temperature
    # RESPIRATORY_RATE: Respiratory rate
    # GLUCOSE: Glucose level
    # WEIGHT: Body weight
    # STEPS: Step count (fitness devices)
    # CALORIES: Calories burned (fitness devices)
    # DISTANCE: Distance traveled (fitness devices)
    # ACTIVE_MINUTES: Active minutes (fitness devices)
    # SLEEP_DURATION: Sleep duration (fitness devices)
    # FLOORS_CLIMBED: Floors climbed (fitness devices)
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE = "blood_pressure"
    OXYGEN_SATURATION = "oxygen_saturation"
    TEMPERATURE = "temperature"
    RESPIRATORY_RATE = "respiratory_rate"
    GLUCOSE = "glucose"
    WEIGHT = "weight"
    STEPS = "steps"
    CALORIES = "calories"
    DISTANCE = "distance"
    ACTIVE_MINUTES = "active_minutes"
    SLEEP_DURATION = "sleep_duration"
    FLOORS_CLIMBED = "floors_climbed"

class DoctorPatient(db.Model):
    # Association table for the many-to-many relationship between doctors and patients
    # 
    # Attributes:
    #   doctor_id: ID of the doctor in the relationship
    #   patient_id: ID of the patient in the relationship
    #   assigned_date: Date when the patient was assigned to the doctor
    __tablename__ = 'doctor_patient'
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), primary_key=True)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)

class Doctor(UserMixin, db.Model):
    # Model representing a doctor in the system
    # 
    # Extends UserMixin to support Flask-Login authentication
    # 
    # Attributes:
    #   id: Unique identifier of the doctor
    #   email: Unique email address of the doctor, used for authentication
    #   password_hash: Hash of the doctor's password
    #   first_name: First name of the doctor
    #   last_name: Last name of the doctor
    #   specialty: Medical specialty of the doctor
    #   created_at: Record creation date
    #   updated_at: Record last update date
    #   patients: Relationship with patients assigned to the doctor
    #   notes: Relationship with notes created by the doctor
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
        # Set the doctor's password hash
        #
        # Args:
        #   password: The plain text password to hash
        #            
        # Returns:
        #   None
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Check if the provided password matches the stored hash
        #
        # Args:
        #   password: The plain text password to verify
        #            
        # Returns:
        #   bool: True if the password is correct, False otherwise
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        # Convert the object to a serializable dictionary
        #
        # Returns:
        #   dict: Dictionary representation of the object
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
        # Get all patients associated with this doctor
        #
        # Returns:
        #   list: List of Patient objects associated with the doctor
        return self.patients.all()
    
    def add_patient(self, patient):
        # Add a patient to this doctor's patient list
        #
        # Args:
        #   patient: Patient object to add
        # 
        # Returns:
        #   None
        if patient not in self.patients.all():
            association = DoctorPatient(doctor_id=self.id, patient_id=patient.id)
            db.session.add(association)
            db.session.commit()
    
    def remove_patient(self, patient):
        # Remove a patient from this doctor's patient list
        #
        # Args:
        #   patient: Patient object to remove
        # 
        # Returns:
        #   None
        association = DoctorPatient.query.filter_by(doctor_id=self.id, patient_id=patient.id).first()
        if association:
            db.session.delete(association)
            db.session.commit()

class HealthPlatform(Enum):
    # Types of health platforms that can be integrated
    FITBIT = "fitbit"
    GOOGLE_HEALTH_CONNECT = "google_health_connect"
    APPLE_HEALTH = "apple_health"

class Patient(db.Model):
    # Model representing a patient in the system
    #
    # Attributes:
    #   id: Unique identifier of the patient
    #   uuid: Unique UUID of the patient, used in URLs and APIs
    #   first_name: First name of the patient
    #   last_name: Last name of the patient
    #   date_of_birth: Date of birth of the patient
    #   gender: Gender of the patient
    #   contact_number: Contact number of the patient
    #   address: Address of the patient
    #   created_at: Record creation date
    #   updated_at: Record last update date
    #   notes: Relationship with patient's medical notes
    #   vital_observations: Relationship with patient's vital sign observations
    #   connected_platform: Health platform connected to this patient (Fitbit, Google Fit, etc.)
    #   platform_access_token: OAuth access token for the connected health platform
    #   platform_refresh_token: OAuth refresh token for the connected health platform
    #   platform_token_expires_at: Expiration date of the current access token
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20))
    contact_number = db.Column(db.String(20))
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
        # Convert the object to a serializable dictionary
        #
        # Returns:
        #   dict: Dictionary representation of the object
        return {
            'id': self.id,
            'uuid': self.uuid,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'contact_number': self.contact_number,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_vital_observations(self, vital_type=None, start_date=None, end_date=None):
        # Get vital observations for this patient with optional filtering
        #
        # Args:
        #   vital_type (VitalSignType, optional): Type of vital sign to filter by
        #   start_date (datetime, optional): Start date for filtering
        #   end_date (datetime, optional): End date for filtering
        #            
        # Returns:
        #   list: List of VitalObservation objects that meet the filtering criteria
        query = self.vital_observations
        
        if vital_type:
            query = query.filter_by(vital_type=vital_type)
        
        if start_date:
            query = query.filter(VitalObservation.start_date >= start_date)
        
        if end_date:
            query = query.filter(VitalObservation.end_date <= end_date)
        
        return query.order_by(VitalObservation.created_at.desc()).all()
    
    def get_notes(self):
        # Get all medical notes associated with this patient
        #
        # Returns:
        #   list: List of Note objects ordered by creation date (most recent first)
        return self.notes.order_by(Note.created_at.desc()).all()


class Note(db.Model):
    # Model representing a medical note for a patient
    #
    # Attributes:
    #   id: Unique identifier of the note
    #   patient_id: ID of the patient to whom the note belongs
    #   doctor_id: ID of the doctor who created the note
    #   content: Textual content of the note
    #   created_at: Note creation date
    #   updated_at: Note last update date
    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        # Convert the object to a serializable dictionary
        #
        # Returns:
        #   dict: Dictionary representation of the object
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
class VitalObservation(db.Model):
    # Model representing observations for vital sign data over specific time periods
    #
    # Attributes:
    #   id: Unique identifier of the observation
    #   patient_id: ID of the patient to whom the observation belongs
    #   doctor_id: ID of the doctor who created the observation
    #   vital_type: Type of vital sign (heart_rate, steps, etc.)
    #   content: Textual content of the observation
    #   start_date: Start date of the observation period
    #   end_date: End date of the observation period
    #   created_at: Observation creation date
    #   updated_at: Observation last update date
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
        # Carica il dottore per ottenere i dettagli
        from app import db
        from sqlalchemy.orm import joinedload
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
    # Enumeration defining the types of actions for the audit log system
    #
    # Attributes:
    #   CREATE: Action of creating a new entity
    #   UPDATE: Action of updating an existing entity
    #   DELETE: Action of deleting an entity
    #   VIEW: Action of viewing an entity
    #   EXPORT: Action of exporting an entity (e.g., report generation)
    #   GENERATE_LINK: Action of generating a link for health platform integration
    #   CONNECT: Action of connecting a health platform
    #   DISCONNECT: Action of disconnecting a health platform
    #   SYNC: Action of synchronizing data from a health platform
    #   IMPORT: Action of importing an existing entity
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VIEW = "VIEW"
    EXPORT = "EXPORT"
    GENERATE_LINK = "GENERATE_LINK"
    CONNECT = "CONNECT"
    DISCONNECT = "DISCONNECT"
    SYNC = "SYNC" # Nota: questo è in minuscolo perché è così nel database
    IMPORT = "IMPORT"

class EntityType(Enum):
    # Enumeration defining the types of entities that can be tracked in the audit log system
    #
    # Attributes:
    #   PATIENT: Patient entity
    #   VITAL_SIGN: Vital sign entity
    #   NOTE: Medical note entity
    #   REPORT: Report/document entity
    #   HEALTH_PLATFORM: Health platform entity
    #   HEALTH_LINK: Health platform link entity
    #   OBSERVATION: Vital observation entity
    PATIENT = "patient"
    VITAL_SIGN = "vital_sign"
    NOTE = "note"
    REPORT = "report"
    HEALTH_PLATFORM = "health_platform"
    HEALTH_LINK = "health_link"
    OBSERVATION = "observation" # Manteniamo minuscole per essere consistenti
    
class HealthPlatformLink(db.Model):
    # Model for storing temporary links for health platform integration
    # These links expire after 24 hours and are used for patients to connect their health devices
    #
    # Attributes:
    #   id: Unique identifier of the link
    #   uuid: Unique UUID for the link, used in URLs
    #   patient_id: ID of the patient this link is for
    #   doctor_id: ID of the doctor who created the link
    #   created_at: Link creation date/time
    #   expires_at: Link expiration date/time (24 hours after creation)
    #   used: Whether the link has been used
    #   platform: The health platform this link is for (Fitbit, Google Fit, etc.)
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
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
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
    # Model for storing audit logs of all actions performed in the system
    # Used to track who did what and when, for compliance and security purposes
    #
    # Attributes:
    #   id: Unique identifier of the audit record
    #   doctor_id: ID of the doctor who performed the action
    #   doctor: Relationship with the doctor who performed the action
    #   timestamp: Date and time when the action was performed
    #   action_type: Type of action performed (from ActionType enum)
    #   entity_type: Type of entity affected by the action (from EntityType enum)
    #   entity_id: ID of the entity affected by the action
    #   details: Additional details about the action (stored as JSON)
    #   patient_id: Optional ID of the patient related to the action
    #   patient: Relationship with the patient related to the action
    #   ip_address: IP address from which the action was performed
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
        # Initialize a new audit log record
        #
        # Args:
        #   doctor_id (int): ID of the doctor who performed the action
        #   action_type (ActionType): Type of action performed
        #   entity_type (EntityType): Type of entity affected by the action
        #   entity_id (int): ID of the entity affected by the action
        #   details (dict, optional): Additional details about the action
        #   patient_id (int, optional): ID of the patient related to the action
        #   ip_address (str, optional): IP address from which the action was performed
        self.doctor_id = doctor_id
        self.action_type = action_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.details = json.dumps(details) if details else None
        self.patient_id = patient_id
        self.ip_address = ip_address
        
    def get_details(self):
        # Convert the JSON string of details to a Python dictionary
        #
        # Returns:
        #   dict: The action details as a dictionary
        if self.details:
            return json.loads(self.details)
        return {}
    
    def to_dict(self):
        # Convert the object to a serializable dictionary
        #
        # Returns:
        #   dict: Dictionary representation of the object
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
