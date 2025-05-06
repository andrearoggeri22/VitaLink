"""
Test configuration file for VitaLink application.

This module provides fixtures and setup for testing the VitaLink application.
It configures the test environment, initializes the test database,
and provides utility fixtures for the tests.
"""
import os
import sys
import pytest
import json
from datetime import datetime, date, timedelta
import random
import string

# Add the parent directory to the path so we can import the app package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load test environment variables first
if os.path.exists('.env.tests'):
    from dotenv import load_dotenv
    load_dotenv('.env.tests')

# Import app related modules after env vars are loaded
from app import app, db
# Import models directly from app.models
from app.models import (
    Doctor, Patient, VitalSignType, Note, DoctorPatient,
    VitalObservation
)

# Configure the app for testing
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory SQLite for tests
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF protection in tests

@pytest.fixture(scope='session')
def app_context():
    """Create an application context for the tests.
    
    This fixture creates a Flask application context with an in-memory SQLite database
    that persists for the entire test session. It creates all database tables at the start
    of testing and drops them at the end.
    
    Returns:
        Flask application context that yields control back to the tests.
    """
    with app.app_context():
        # Create tables at the session level
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_context):
    """Create a test client for the app.
    
    This fixture provides a Flask test client that can be used to send requests to the application.
    It ensures each test starts with a clean session and logs out any authenticated users
    both before and after the test.
    
    Args:
        app_context: The Flask application context fixture.
        
    Returns:
        Flask test client for making requests to the application.
    """
    with app.test_client() as client:
        # Tables are created in the app_context fixture
        # Ensure the session is clean at the start of each test
        db.session.begin_nested()
        
        # Logout before each test to ensure a clean state
        client.get('/logout', follow_redirects=True)
        
        yield client
        
        # Logout after each test to ensure the session is clean
        client.get('/logout', follow_redirects=True)
        
        # Rollback any changes made during the test
        db.session.rollback()
        # Clear the session cache
        db.session.expire_all()
        # Keep an active session
        db.session.begin()


@pytest.fixture
def doctor_factory(app_context):
    """Factory to create test doctors with random data.
    
    This fixture returns a function that can create Doctor instances with random or
    specified data. It handles creating the doctor, setting a password, and committing
    to the database.
    
    Args:
        app_context: The Flask application context fixture.
        
    Returns:
        Function that creates and returns Doctor instances.
    """
    def _create_doctor(email=None, password="Password123!", first_name=None, last_name=None, specialty=None):
        """Create a test doctor with the given or random data.
        
        Args:
            email: Optional email address for the doctor.
            password: Password for the doctor account (defaults to "Password123!").
            first_name: Optional first name for the doctor.
            last_name: Optional last name for the doctor.
            specialty: Optional medical specialty for the doctor.
            
        Returns:
            Doctor: A new Doctor instance saved to the database.
        """
        # Generate random data if not provided
        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        if not email:
            email = f"doctor_{random_str}@example.com"
        if not first_name:
            first_name = f"Doctor_{random_str}"
        if not last_name:
            last_name = f"Test_{random_str}"
        if not specialty:
            specialty = "General Medicine"
        
        # Create doctor
        doctor = Doctor(
            email=email,
            first_name=first_name,
            last_name=last_name,
            specialty=specialty
        )
        doctor.set_password(password)
        
        # Save to database
        db.session.add(doctor)
        db.session.commit()
        
        return doctor
    
    return _create_doctor


@pytest.fixture
def patient_factory(app_context):
    """Factory to create test patients with random data.
    
    This fixture returns a function that can create Patient instances with random or
    specified data. It handles creating the patient and committing to the database.
    
    Args:
        app_context: The Flask application context fixture.
        
    Returns:
        Function that creates and returns Patient instances.
    """
    def _create_patient(first_name=None, last_name=None, email=None, date_of_birth=None, gender=None,
                        contact_number=None, address=None):
        """Create a test patient with the given or random data.
        
        Args:
            first_name: Optional first name for the patient.
            last_name: Optional last name for the patient.
            email: Optional email address for the patient.
            date_of_birth: Optional date of birth (defaults to 1980-01-01).
            gender: Optional gender (randomly chosen if not provided).
            contact_number: Optional contact number for the patient.
            address: Optional address for the patient.
            
        Returns:
            Patient: A new Patient instance saved to the database.
        """
        # Generate random data if not provided
        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        if not first_name:
            first_name = f"Patient_{random_str}"
        if not last_name:
            last_name = f"Test_{random_str}"
        if not email:
            email = f"patient_{random_str}@example.com"
        if not date_of_birth:
            date_of_birth = date(1980, 1, 1)
        if not gender:
            gender = random.choice(["Male", "Female", "Non-binary"])
        if not contact_number:
            contact_number = f"+39{random.randint(300000000, 399999999)}"
        if not address:
            address = f"{random.randint(1, 100)} Test Street, Test City"
        
        # Create patient
        patient = Patient(
            first_name=first_name,
            last_name=last_name,
            email=email,
            date_of_birth=date_of_birth,
            gender=gender,
            contact_number=contact_number,
            address=address
        )
        
        # Save to database
        db.session.add(patient)
        db.session.commit()
        
        return patient
    
    return _create_patient


@pytest.fixture
def authenticated_doctor(client, doctor_factory):
    """Create a doctor and authenticate as that doctor.
    
    This fixture creates a doctor, performs a login with their credentials, and returns
    the authenticated doctor instance. It verifies the authentication was successful
    by checking access to the dashboard.
    
    Args:
        client: Flask test client fixture.
        doctor_factory: Factory fixture to create doctor instances.
        
    Returns:
        Doctor: An authenticated doctor instance.
    """
    # Cleanup: ensure no active sessions
    client.get('/logout', follow_redirects=True)
    
    doctor = doctor_factory()
    # Commit to ensure the doctor is saved in the database
    db.session.flush()
    db.session.commit()
    
    doctor_id = doctor.id  # Save the ID before closing the session
    
    # Most reliable way to authenticate: perform an actual login via form
    response = client.post('/login', data={
        'email': doctor.email,
        'password': 'Password123!'  # Standard password used in doctor_factory
    }, follow_redirects=True)
    
    # Verify authentication was successful
    assert response.status_code == 200, "Login failed"
    assert b'Dashboard' in response.data, "Login didn't redirect to dashboard"
    
    # Reload the doctor instance from the database to ensure it's connected to the session
    # Use db.session.get to ensure we have the most recent instance
    doctor = db.session.get(Doctor, doctor_id)
    assert doctor is not None, "Could not retrieve doctor from database"
    
    # Verify authentication works by trying to access the dashboard
    dashboard_response = client.get('/dashboard')
    assert dashboard_response.status_code == 200, "Authentication is not persistent"
    
    # Ensure the object is connected to the session
    doctor = db.session.merge(doctor)
    
    return doctor


@pytest.fixture
def doctor_with_patient(client, doctor_factory, patient_factory):
    """Create a doctor with an associated patient.
    
    This fixture creates a doctor and patient, associates them, and authenticates
    as the doctor. It returns both objects in a dictionary.
    
    Args:
        client: Flask test client fixture.
        doctor_factory: Factory fixture to create doctor instances.
        patient_factory: Factory fixture to create patient instances.
        
    Returns:
        dict: Dictionary containing the authenticated doctor and associated patient.
    """
    # Cleanup: ensure no active sessions
    client.get('/logout', follow_redirects=True)
    
    doctor = doctor_factory()
    db.session.flush()  # Ensure doctor has an ID
    
    patient = patient_factory()
    db.session.flush()  # Ensure patient has an ID
    
    # Reload entities from database to ensure they are attached
    doctor = db.session.get(Doctor, doctor.id)
    patient = db.session.get(Patient, patient.id)
    
    # Create a new association between doctor and patient
    # Instead of using the model method, create the association directly
    association = DoctorPatient(doctor_id=doctor.id, patient_id=patient.id)
    db.session.add(association)
    db.session.commit()
    
    # Most reliable way to authenticate: perform an actual login via form
    response = client.post('/login', data={
        'email': doctor.email,
        'password': 'Password123!'  # Standard password used in doctor_factory
    }, follow_redirects=True)
    
    # Verify authentication was successful
    assert response.status_code == 200, "Login failed"
    assert b'Dashboard' in response.data, "Login didn't redirect to dashboard"
    
    # Reattach objects to current database session to avoid detached instance errors
    doctor = db.session.merge(doctor)
    patient = db.session.merge(patient)
    
    # Verify the association was made correctly
    assert patient in doctor.patients.all(), "Problem with doctor-patient association"
    
    return {'doctor': doctor, 'patient': patient}


@pytest.fixture
def api_auth_headers(client, doctor_factory):
    """Get authentication headers with JWT token for API requests.
    
    This fixture creates a doctor, obtains a JWT token by making an API login request,
    and returns the authentication headers along with doctor and token information.
    
    Args:
        client: Flask test client fixture.
        doctor_factory: Factory fixture to create doctor instances.
        
    Returns:
        dict: Dictionary containing authorization headers, doctor instance, and tokens.
    """
    doctor = doctor_factory()
    
    # Set a known password
    doctor.set_password("Password123!")
    db.session.commit()
    
    # The simplest way: get the token via a direct request
    response = client.post('/api/login', json={
        'email': doctor.email,
        'password': "Password123!"
    })
    
    # Make sure doctor is attached to the session
    doctor = db.session.merge(doctor)
    
    # Parse the response
    data = json.loads(response.data)
    
    assert response.status_code == 200, f"Login API failed with response: {response.data.decode()}"
    assert 'access_token' in data, "Access token not found in response"
    
    headers = {
        'Authorization': f"Bearer {data['access_token']}"
    }
    
    return {'headers': headers, 'doctor': doctor, 'access_token': data['access_token'], 'refresh_token': data['refresh_token']}


@pytest.fixture
def note_factory(app_context):
    """Factory to create test notes.
    
    This fixture returns a function that can create Note instances for a doctor and patient.
    
    Args:
        app_context: Flask application context fixture.
    
    Returns:
        Function that creates and returns Note instances.
    """
    def _create_note(doctor, patient, content=None):
        """Create a test note with the given or random data.
        
        Args:
            doctor: Doctor who creates the note.
            patient: Patient the note is about.
            content: Optional note content (random if not provided).
            
        Returns:
            Note: A new Note instance saved to the database.
        """
        # Ensure doctor and patient are attached to the session
        doctor = db.session.merge(doctor)
        patient = db.session.merge(patient)
        
        if not content:
            content = f"Test note created at {datetime.utcnow().isoformat()}"
        
        # Create note
        note = Note(
            doctor_id=doctor.id,
            patient_id=patient.id,
            content=content
        )
        
        # Save to database
        db.session.add(note)
        db.session.commit()
        
        # Ensure note is attached to the session
        note = db.session.merge(note)
        
        return note
    
    return _create_note


@pytest.fixture
def observation_factory(app_context):
    """Factory to create test vital sign observations.
    
    This fixture returns a function that can create VitalObservation instances
    for a doctor and patient.
    
    Args:
        app_context: Flask application context fixture.
        
    Returns:
        Function that creates and returns VitalObservation instances.
    """
    def _create_observation(doctor, patient, vital_type=None, content=None, 
                           start_date=None, end_date=None):
        """Create a test observation with the given or random data.
        
        Args:
            doctor: Doctor who creates the observation.
            patient: Patient the observation is about.
            vital_type: Type of vital sign (defaults to HEART_RATE).
            content: Optional observation content.
            start_date: Start date for the observation period.
            end_date: End date for the observation period.
            
        Returns:
            VitalObservation: A new VitalObservation instance saved to the database.
        """
        # Ensure doctor and patient are attached to the session
        doctor = db.session.merge(doctor)
        patient = db.session.merge(patient)
        
        if not vital_type:
            vital_type = VitalSignType.HEART_RATE
        if not content:
            content = f"Test observation for {vital_type.value} created at {datetime.utcnow().isoformat()}"
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Create observation
        observation = VitalObservation(
            doctor_id=doctor.id,
            patient_id=patient.id,
            vital_type=vital_type,
            content=content,
            start_date=start_date,
            end_date=end_date
        )
        
        # Save to database
        db.session.add(observation)
        db.session.commit()
        
        # Ensure the observation is attached to the session
        observation = db.session.merge(observation)
        
        return observation
    
    return _create_observation


def reattach_objects(objects):
    """
    Reattach SQLAlchemy objects to the current session.
    
    Takes a single object or a list of objects and reattaches them
    to the current database session using db.session.merge().
    
    Args:
        objects: A single SQLAlchemy object or a list of objects.
        
    Returns:
        The object or list of objects reattached to the session.
        
    Raises:
        Exception: If the object cannot be reattached and has no ID.
    """
    try:
        if isinstance(objects, list):
            return [db.session.merge(obj) if obj is not None else None for obj in objects]
        else:
            return db.session.merge(objects) if objects is not None else None
    except Exception as e:
        # In case of error, try to reload the object using its ID
        if hasattr(objects, 'id') and objects.id is not None:
            obj_class = type(objects)
            return db.session.get(obj_class, objects.id)
        else:
            # If reattachment is not possible, raise the original exception
            raise e


@pytest.fixture
def attach_to_session():
    """Fixture that provides the reattach_objects function to tests.
    
    This fixture makes the reattach_objects function available to tests
    so they can ensure their SQLAlchemy objects are properly attached to
    the current database session.
    
    Returns:
        Function: The reattach_objects function.
    """
    return reattach_objects
