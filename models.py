import uuid
import json
from datetime import datetime
from enum import Enum, auto
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

# Models for the VitaLink application
# Defines the main data entities and their relationships

class DataOrigin(Enum):
    # Origin of the vital signs data
    # MANUAL: Data entered manually by the doctor
    # AUTOMATIC: Data collected automatically from devices
    MANUAL = "manual"
    AUTOMATIC = "automatic"

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
    
    # Notes created by this doctor
    notes = db.relationship('Note', backref='doctor', lazy='dynamic')

    def set_password(self, password):
        """
        Imposta l'hash della password del medico.
        
        Args:
            password: La password in chiaro da hashare
            
        Returns:
            None
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifica se la password fornita corrisponde all'hash memorizzato.
        
        Args:
            password: La password in chiaro da verificare
            
        Returns:
            bool: True se la password è corretta, False altrimenti
        """
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """
        Converte l'oggetto in un dizionario serializzabile.
        
        Returns:
            dict: Rappresentazione dell'oggetto come dizionario
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
        Ottiene tutti i pazienti associati a questo medico.
        
        Returns:
            list: Lista di oggetti Patient associati al medico
        """
        return self.patients.all()
    
    def add_patient(self, patient):
        """
        Aggiunge un paziente alla lista dei pazienti di questo medico.
        
        Args:
            patient: Oggetto Patient da aggiungere
            
        Returns:
            None
        """
        if patient not in self.patients.all():
            association = DoctorPatient(doctor_id=self.id, patient_id=patient.id)
            db.session.add(association)
            db.session.commit()
    
    def remove_patient(self, patient):
        """
        Rimuove un paziente dalla lista dei pazienti di questo medico.
        
        Args:
            patient: Oggetto Patient da rimuovere
            
        Returns:
            None
        """
        association = DoctorPatient.query.filter_by(doctor_id=self.id, patient_id=patient.id).first()
        if association:
            db.session.delete(association)
            db.session.commit()

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
    #   vital_signs: Relationship with patient's vital signs
    #   notes: Relationship with patient's medical notes
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
    
    # Relationships
    vital_signs = db.relationship('VitalSign', backref='patient', lazy='dynamic')
    notes = db.relationship('Note', backref='patient', lazy='dynamic')
    
    def to_dict(self):
        """
        Converte l'oggetto in un dizionario serializzabile.
        
        Returns:
            dict: Rappresentazione dell'oggetto come dizionario
        """
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
    
    def get_vital_signs(self, type=None, start_date=None, end_date=None):
        """
        Ottiene i parametri vitali per questo paziente con possibile filtraggio.
        
        Args:
            type (VitalSignType, optional): Tipo di parametro vitale da filtrare
            start_date (datetime, optional): Data di inizio per il filtraggio
            end_date (datetime, optional): Data di fine per il filtraggio
            
        Returns:
            list: Lista di oggetti VitalSign che soddisfano i criteri di filtraggio
        """
        query = self.vital_signs
        
        if type:
            query = query.filter_by(type=type)
        
        if start_date:
            query = query.filter(VitalSign.recorded_at >= start_date)
        
        if end_date:
            query = query.filter(VitalSign.recorded_at <= end_date)
        
        return query.order_by(VitalSign.recorded_at.desc()).all()
    
    def get_notes(self):
        """
        Ottiene tutte le note mediche associate a questo paziente.
        
        Returns:
            list: Lista di oggetti Note ordinati per data di creazione (più recenti prima)
        """
        return self.notes.order_by(Note.created_at.desc()).all()

class VitalSign(db.Model):
    # Model representing a vital sign of a patient
    #
    # Attributes:
    #   id: Unique identifier of the vital sign
    #   patient_id: ID of the patient to whom the parameter belongs
    #   type: Type of vital sign (from VitalSignType enum)
    #   value: Numeric value of the parameter
    #   unit: Unit of measurement of the value
    #   recorded_at: Date and time when the parameter was recorded
    #   origin: Origin of the data (manual or automatic)
    #   created_at: Record creation date
    __tablename__ = 'vital_sign'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    type = db.Column(db.Enum(VitalSignType), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    origin = db.Column(db.Enum(DataOrigin), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """
        Converte l'oggetto in un dizionario serializzabile.
        
        Returns:
            dict: Rappresentazione dell'oggetto come dizionario
        """
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'type': self.type.value,
            'value': self.value,
            'unit': self.unit,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'origin': self.origin.value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

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
        """
        Converte l'oggetto in un dizionario serializzabile.
        
        Returns:
            dict: Rappresentazione dell'oggetto come dizionario
        """
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'content': self.content,
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
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"

class EntityType(Enum):
    # Enumeration defining the types of entities that can be tracked in the audit log system
    #
    # Attributes:
    #   PATIENT: Patient entity
    #   VITAL_SIGN: Vital sign entity
    #   NOTE: Medical note entity
    #   REPORT: Report/document entity
    PATIENT = "patient"
    VITAL_SIGN = "vital_sign"
    NOTE = "note"
    REPORT = "report"

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
        """
        Converte l'oggetto in un dizionario serializzabile.
        
        Returns:
            dict: Rappresentazione dell'oggetto come dizionario
        """
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'doctor_name': f"{self.doctor.first_name} {self.doctor.last_name}" if self.doctor else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'action_type': self.action_type.value,
            'entity_type': self.entity_type.value,
            'entity_id': self.entity_id,
            'details': self.get_details(),
            'patient_id': self.patient_id,
            'patient_name': f"{self.patient.first_name} {self.patient.last_name}" if self.patient else None,
            'ip_address': self.ip_address
        }
