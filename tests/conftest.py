"""
Configuration file for pytest, providing fixtures for testing the VitaLink application.
"""
import os
import pytest
import tempfile
import datetime

from flask import Flask
from flask_login import login_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from app import app as flask_app
from app import db as _db
from app.models import Doctor, Patient, Note, VitalObservation, VitalSignType, HealthPlatform, HealthPlatformLink


@pytest.fixture(scope="session")
def app():
    """
    Create a Flask application for testing.
    
    Returns:
        Flask: The Flask application for testing.
    """
    # Configure app for testing
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    
    # Use a temporary SQLite file database for testing
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        flask_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp.name}"
        
        # Push the application context
        with flask_app.app_context():
            # Create the database and tables
            _db.create_all()
            
            # Return the application for testing
            yield flask_app


@pytest.fixture(scope="session")
def db(app):
    """
    Create a database for testing.
    
    Args:
        app (Flask): The Flask application.
        
    Returns:
        SQLAlchemy: The database instance.
    """
    # Return the database instance
    yield _db
    
    # Clean up the database after testing
    with app.app_context():
        _db.session.close()
        _db.drop_all()


@pytest.fixture(scope="function")
def session(db):
    """
    Create a new database session for testing.
    
    Args:
        db (SQLAlchemy): The database instance.
        
    Returns:
        Session: A new database session.
    """
    # Create a new connection to the database
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Create a new session for testing
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    
    # Set the session for the database
    db.session = session
    
    # Return the session for testing
    yield session
    
    # Clean up the session after testing
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def doctor(session):
    """
    Create a test doctor for testing.
    
    Args:
        session (Session): The database session.
        
    Returns:
        Doctor: The test doctor.
    """
    # Create a doctor for testing
    doctor = Doctor(
        email="test_doctor@vitalink.com",
        first_name="Test",
        last_name="Doctor",
        specialty="General Medicine"
    )
    doctor.set_password("password")
    
    # Add the doctor to the database
    session.add(doctor)
    session.commit()
    
    # Return the doctor for testing
    return doctor


@pytest.fixture(scope="function")
def patient(session):
    """
    Create a test patient for testing.
    
    Args:
        session (Session): The database session.
        
    Returns:
        Patient: The test patient.
    """
    # Create a patient for testing
    patient = Patient(
        first_name="Test",
        last_name="Patient",
        date_of_birth=datetime.datetime(1990, 1, 1),
        gender="Other"
    )
    
    # Add the patient to the database
    session.add(patient)
    session.commit()
    
    # Return the patient for testing
    return patient


@pytest.fixture(scope="function")
def doctor_with_patient(session, doctor, patient):
    """
    Create a test doctor with an assigned patient.
    
    Args:
        session (Session): The database session.
        doctor (Doctor): The test doctor.
        patient (Patient): The test patient.
        
    Returns:
        Doctor: The test doctor with an assigned patient.
    """
    # Assign the patient to the doctor
    doctor.add_patient(patient)
    
    # Return the doctor for testing
    return doctor


@pytest.fixture(scope="function")
def note(session, doctor, patient):
    """
    Create a test note for testing.
    
    Args:
        session (Session): The database session.
        doctor (Doctor): The test doctor.
        patient (Patient): The test patient.
        
    Returns:
        Note: The test note.
    """
    # Create a note for testing
    note = Note(
        patient_id=patient.id,
        doctor_id=doctor.id,
        content="Test note content"
    )
    
    # Add the note to the database
    session.add(note)
    session.commit()
    
    # Return the note for testing
    return note


@pytest.fixture(scope="function")
def vital_observation(session, doctor, patient):
    """
    Create a test vital observation for testing.
    
    Args:
        session (Session): The database session.
        doctor (Doctor): The test doctor.
        patient (Patient): The test patient.
        
    Returns:
        VitalObservation: The test vital observation.
    """
    # Create a vital observation for testing
    vital_observation = VitalObservation(
        patient_id=patient.id,
        doctor_id=doctor.id,
        vital_type=VitalSignType.HEART_RATE,
        content="Test vital observation content",
        start_date=datetime.datetime.utcnow() - datetime.timedelta(days=1),
        end_date=datetime.datetime.utcnow()
    )
    
    # Add the vital observation to the database
    session.add(vital_observation)
    session.commit()
    
    # Return the vital observation for testing
    return vital_observation


@pytest.fixture(scope="function")
def client(app):
    """
    Create a test client for testing.
    
    Args:
        app (Flask): The Flask application.
        
    Returns:
        FlaskClient: The test client.
    """
    # Return the test client
    return app.test_client()


@pytest.fixture(scope="function")
def logged_in_client(client, doctor):
    """
    Create a test client with a logged in doctor.
    
    Args:
        client (FlaskClient): The test client.
        doctor (Doctor): The test doctor.
        
    Returns:
        FlaskClient: The test client with a logged in doctor.
    """
    # Log in the doctor
    with client.session_transaction() as session:
        session["_user_id"] = doctor.id
        session["language"] = "en"  # Set language to English for testing
    
    # Return the client for testing
    return client


@pytest.fixture(scope="function")
def health_platform_link(session, doctor, patient):
    """
    Create a test health platform link for testing.
    
    Args:
        session (Session): The database session.
        doctor (Doctor): The test doctor.
        patient (Patient): The test patient.
        
    Returns:
        HealthPlatformLink: The test health platform link.
    """
    # Create a health platform link for testing
    link = HealthPlatformLink(
        patient_id=patient.id,
        doctor_id=doctor.id,
        platform=HealthPlatform.FITBIT
    )
    
    # Add the link to the database
    session.add(link)
    session.commit()
    
    # Return the link for testing
    return link
