import uuid
from datetime import datetime
from enum import Enum, auto
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

class DataOrigin(Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"

class VitalSignType(Enum):
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE = "blood_pressure"
    OXYGEN_SATURATION = "oxygen_saturation"
    TEMPERATURE = "temperature"
    RESPIRATORY_RATE = "respiratory_rate"
    GLUCOSE = "glucose"
    WEIGHT = "weight"

# Association table for the many-to-many relationship between doctors and patients
class DoctorPatient(db.Model):
    __tablename__ = 'doctor_patient'
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), primary_key=True)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)

class Doctor(UserMixin, db.Model):
    __tablename__ = 'doctor'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with patients
    patients = db.relationship('Patient', 
                              secondary='doctor_patient',
                              backref=db.backref('doctors', lazy='dynamic'),
                              lazy='dynamic')
    
    # Notes created by this doctor
    notes = db.relationship('Note', backref='doctor', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
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
        """Get all patients associated with this doctor."""
        return self.patients.all()
    
    def add_patient(self, patient):
        """Add a patient to this doctor's list."""
        if patient not in self.patients.all():
            association = DoctorPatient(doctor_id=self.id, patient_id=patient.id)
            db.session.add(association)
            db.session.commit()
    
    def remove_patient(self, patient):
        """Remove a patient from this doctor's list."""
        association = DoctorPatient.query.filter_by(doctor_id=self.id, patient_id=patient.id).first()
        if association:
            db.session.delete(association)
            db.session.commit()

class Patient(db.Model):
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
        """Get vital signs for this patient with optional filtering."""
        query = self.vital_signs
        
        if type:
            query = query.filter_by(type=type)
        
        if start_date:
            query = query.filter(VitalSign.recorded_at >= start_date)
        
        if end_date:
            query = query.filter(VitalSign.recorded_at <= end_date)
        
        return query.order_by(VitalSign.recorded_at.desc()).all()
    
    def get_notes(self):
        """Get all notes for this patient."""
        return self.notes.order_by(Note.created_at.desc()).all()

class VitalSign(db.Model):
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
    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
