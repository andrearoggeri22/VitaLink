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
    """
    Modello che rappresenta un paziente nel sistema.
    
    Attributi:
        id: Identificatore unico del paziente
        uuid: UUID univoco del paziente, usato in URL e API
        first_name: Nome del paziente
        last_name: Cognome del paziente
        date_of_birth: Data di nascita del paziente
        gender: Genere del paziente
        contact_number: Numero di contatto del paziente
        address: Indirizzo del paziente
        created_at: Data di creazione del record
        updated_at: Data di ultimo aggiornamento del record
        vital_signs: Relazione con i parametri vitali del paziente
        notes: Relazione con le note mediche del paziente
    """
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
    """
    Modello che rappresenta un parametro vitale di un paziente.
    
    Attributi:
        id: Identificatore unico del parametro vitale
        patient_id: ID del paziente a cui appartiene il parametro
        type: Tipo di parametro vitale (dall'enum VitalSignType)
        value: Valore numerico del parametro
        unit: Unità di misura del valore
        recorded_at: Data e ora in cui è stato rilevato il parametro
        origin: Origine del dato (manuale o automatica)
        created_at: Data di creazione del record
    """
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
    """
    Modello che rappresenta una nota medica per un paziente.
    
    Attributi:
        id: Identificatore unico della nota
        patient_id: ID del paziente a cui appartiene la nota
        doctor_id: ID del medico che ha creato la nota
        content: Contenuto testuale della nota
        created_at: Data di creazione della nota
        updated_at: Data di ultimo aggiornamento della nota
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
    """
    Enumerazione che definisce i tipi di azioni per il sistema di audit log.
    
    Attributi:
        CREATE: Azione di creazione di una nuova entità
        UPDATE: Azione di aggiornamento di un'entità esistente
        DELETE: Azione di eliminazione di un'entità
        VIEW: Azione di visualizzazione di un'entità
        EXPORT: Azione di esportazione di un'entità (es. generazione di report)
    """
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"

class EntityType(Enum):
    """
    Enumerazione che definisce i tipi di entità tracciabili nel sistema di audit log.
    
    Attributi:
        PATIENT: Entità paziente
        VITAL_SIGN: Entità parametro vitale
        NOTE: Entità nota medica
        REPORT: Entità report/documento
    """
    PATIENT = "patient"
    VITAL_SIGN = "vital_sign"
    NOTE = "note"
    REPORT = "report"

class AuditLog(db.Model):
    """
    Modello per memorizzare i log di audit di tutte le azioni eseguite nel sistema.
    Utilizzato per tracciare chi ha fatto cosa e quando, per scopi di conformità e sicurezza.
    
    Attributi:
        id: Identificatore unico del record di audit
        doctor_id: ID del medico che ha eseguito l'azione
        doctor: Relazione con il medico che ha eseguito l'azione
        timestamp: Data e ora in cui è stata eseguita l'azione
        action_type: Tipo di azione eseguita (dall'enum ActionType)
        entity_type: Tipo di entità interessata dall'azione (dall'enum EntityType)
        entity_id: ID dell'entità interessata dall'azione
        details: Dettagli aggiuntivi sull'azione (memorizzati come JSON)
        patient_id: ID opzionale del paziente correlato all'azione
        patient: Relazione con il paziente correlato all'azione
        ip_address: Indirizzo IP da cui è stata eseguita l'azione
    """
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    
    # Chi ha eseguito l'azione
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    doctor = db.relationship('Doctor')
    
    # Quando l'azione è stata eseguita
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Che tipo di azione è stata eseguita
    action_type = db.Column(db.Enum(ActionType), nullable=False)
    
    # Quale entità è stata interessata
    entity_type = db.Column(db.Enum(EntityType), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)  # ID dell'entità interessata
    
    # Dettagli aggiuntivi sull'azione (memorizzati come JSON)
    details = db.Column(db.Text)  # Stringa JSON con dettagli sull'azione
    
    # ID opzionale del paziente per facilitare le query
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    patient = db.relationship('Patient')
    
    # Indirizzo IP dell'utente che ha eseguito l'azione
    ip_address = db.Column(db.String(50))
    
    def __init__(self, doctor_id, action_type, entity_type, entity_id, details=None, patient_id=None, ip_address=None):
        """
        Inizializza un nuovo record di audit log.
        
        Args:
            doctor_id (int): ID del medico che ha eseguito l'azione
            action_type (ActionType): Tipo di azione eseguita
            entity_type (EntityType): Tipo di entità interessata dall'azione
            entity_id (int): ID dell'entità interessata dall'azione
            details (dict, optional): Dettagli aggiuntivi sull'azione
            patient_id (int, optional): ID del paziente correlato all'azione
            ip_address (str, optional): Indirizzo IP da cui è stata eseguita l'azione
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
        Converte la stringa JSON dei dettagli in un dizionario Python.
        
        Returns:
            dict: I dettagli dell'azione come dizionario
        """
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
