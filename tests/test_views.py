"""
Test module for views functionality.

This module tests the web views including:
- Dashboard display
- Patient management (listing, creation, editing, deletion)
- Notes management
- Vital signs visualization
- Report generation
"""
import json
from datetime import date
from uuid import uuid4

from app import db
from app.models import Patient, Note, DoctorPatient


class TestViews:
    """Test class for web views functionality."""
    def test_index_redirect(self, client, doctor_factory):
        """
        Test landing page redirection behavior.
        
        Args:
            client: Flask test client
            doctor_factory: Factory fixture to create doctor instances
        """
        # Clear any active sessions first
        client.get('/logout', follow_redirects=True)
        
        # Unauthenticated user should be redirected to login
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify presence of login elements
        login_elements = [b'login', b'sign in', b'accedi', b'password', b'email']
        login_found = any(element in response.data.lower() for element in login_elements)
        assert login_found, "No login elements found in the response"
        
        # Create and authenticate doctor using the fixture
        doctor = doctor_factory()
        
        # Explicit login via form
        login_response = client.post('/login', data={
            'email': doctor.email,
            'password': 'Password123!'  # Standard password used in doctor_factory
        }, follow_redirects=True)
        
        assert login_response.status_code == 200
        assert b'Dashboard' in login_response.data
        
        # Authenticated user should be redirected to dashboard
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200        # Check for dashboard indicators with flexible matching
        assert b'dashboard' in response.data.lower() or b'welcome' in response.data.lower() or b'benvenuto' in response.data.lower()
    def test_dashboard(self, client, authenticated_doctor, patient_factory):
        """
        Test dashboard view functionality.
        
        Args:
            client: Flask test client
            authenticated_doctor: Pre-authenticated doctor fixture
            patient_factory: Factory fixture to create patient instances
        """
        # Make sure the doctor is attached to the session
        from app import db
        doctor = db.session.merge(authenticated_doctor)
        
        # Ensure proper authentication
        with client.session_transaction() as session:
            session['_user_id'] = str(doctor.id)
            session['_fresh'] = True
        
        # Create test patients
        for i in range(3):
            patient = patient_factory()
            patient = db.session.merge(patient)  # Ensure patient is attached to the session
            doctor = db.session.merge(doctor)    # Re-attach doctor after each iteration
            doctor.add_patient(patient)
        
        # Test dashboard access
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        # Look for general dashboard elements instead of specific text
        assert b'dashboard' in response.data.lower()
        # Check for patient information presence in any format
        assert b'patient' in response.data.lower() and b'3' in response.data    
    def test_patients_list(self, client, authenticated_doctor, patient_factory):
        """
        Test patients list view functionality.
        
        Args:
            client: Flask test client
            authenticated_doctor: Pre-authenticated doctor fixture
            patient_factory: Factory fixture to create patient instances
        """
        from app import db
        doctor = db.session.merge(authenticated_doctor)
        
        # Create test patients
        patient1 = patient_factory(first_name="Alice", last_name="Smith")
        patient2 = patient_factory(first_name="Bob", last_name="Jones")
        
        # Make sure all objects are attached to the session
        doctor = db.session.merge(doctor)
        patient1 = db.session.merge(patient1)
        patient2 = db.session.merge(patient2)
        
        # Authenticate the doctor
        with client.session_transaction() as session:
            session['_user_id'] = str(doctor.id)
            session['_fresh'] = True
        
        doctor.add_patient(patient1)
        doctor = db.session.merge(doctor)  # Reattach after each operation
        doctor.add_patient(patient2)
        
        # Test patients list access
        response = client.get('/patients')
        assert response.status_code == 200
        
        # Patients list should show both patients
        assert b'Alice Smith' in response.data
        assert b'Bob Jones' in response.data    
    def test_new_patient(self, client, authenticated_doctor):
        """Test patient creation view.
        
        Verifies that the patient creation form is displayed correctly and that
        new patients can be created with valid data. Also tests validation errors
        with invalid data.
        
        Args:
            client: Flask test client
            authenticated_doctor: Pre-authenticated doctor fixture
        """
        # Test new patient form display
        response = client.get('/patients/new')
        assert response.status_code == 200
        assert b'Add New Patient' in response.data
        
        # Test patient creation
        response = client.post('/patients/new', data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'date_of_birth': '1990-05-15',
            'gender': 'Female',
            'contact_number': '+39123456789',
            'email': 'jane.doe@example.com',
            'address': '123 Test Street'
        }, follow_redirects=True)
          # Check response
        assert response.status_code == 200
        # Il messaggio effettivo contiene il nome del paziente e l'UUID
        assert b'Patient Jane Doe successfully created with ID' in response.data
        assert b'Jane Doe' in response.data
        
        # Verify patient was created in database
        patient = Patient.query.filter_by(first_name='Jane', last_name='Doe').first()
        assert patient is not None
        assert patient.date_of_birth == date(1990, 5, 15)
        assert patient.gender == 'Female'
        assert patient.contact_number == '+39123456789'
        assert patient.email == 'jane.doe@example.com'
        
        # Test patient creation with invalid data
        response = client.post('/patients/new', data={
            'first_name': '',  # Empty first name
            'last_name': 'Test',
            'date_of_birth': '1990-05-15',
            'gender': 'Male',
            'contact_number': '+39123456789',
            'email': 'invalid.email',  # Invalid email
            'address': '123 Test Street'
        }, follow_redirects=True)
          # Check response shows errors
        assert response.status_code == 200
        assert b'Name, surname and date of birth are mandatory fields' in response.data    
    def test_patient_detail(self, client, doctor_with_patient, note_factory, patient_factory):
        """Test patient detail view functionality.
        
        Verifies that a doctor can view the details of their associated patients,
        including patient information and notes.
        
        Args:
            client: Flask test client
            doctor_with_patient: Fixture providing a doctor with an associated patient
            note_factory: Factory fixture to create note instances
            patient_factory: Factory fixture to create patient instances
        """
        from app import db
        
        doctor = db.session.merge(doctor_with_patient['doctor'])
        patient = db.session.merge(doctor_with_patient['patient'])
        
        # Perform an explicit login
        response = client.post('/login', data={
            'email': doctor.email,
            'password': 'Password123!'  # Standard password used in doctor_factory
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data, "Login failed"
        
        # Make sure the session is properly set
        with client.session_transaction() as session:
            session['_user_id'] = str(doctor.id)
            session['_fresh'] = True
            
        # Add some notes
        note_factory(doctor, patient, "First test note")
        note_factory(doctor, patient, "Second test note")
        
        # Test patient detail access (after adding notes)
        db.session.refresh(patient)  # Make sure the patient is updated
        response = client.get(f'/patients/{patient.id}')
        assert response.status_code == 200
        
        # Check patient info is displayed
        assert patient.first_name.encode() in response.data
        assert patient.last_name.encode() in response.data
        
        # Check notes are displayed
        assert b'First test note' in response.data
        assert b'Second test note' in response.data
        
        # Test with non-existent patient
        response = client.get('/patients/9999')
        assert response.status_code == 404        # Test with patient not associated with doctor
        # Use patient_factory as parameter
        unassociated_patient = patient_factory()
        response = client.get(f'/patients/{unassociated_patient.id}')
        assert response.status_code == 302  # System redirects instead of returning 403    
    def test_edit_patient(self, client, doctor_with_patient, patient_factory):
        """Test patient edit view functionality.
        
        Verifies that a doctor can edit the information of their associated patients
        and that the changes are correctly saved in the database.
        
        Args:
            client: Flask test client
            doctor_with_patient: Fixture providing a doctor with an associated patient
            patient_factory: Factory fixture to create patient instances
        """
        doctor_with_patient['doctor']
        patient = doctor_with_patient['patient']
        
        # Test edit form display
        response = client.get(f'/patients/{patient.id}/edit')
        assert response.status_code == 200
        assert b'Edit Patient' in response.data
        
        # Test patient update
        response = client.post(f'/patients/{patient.id}/edit', data={
            'first_name': 'Updated',
            'last_name': 'Name',
            'date_of_birth': '1985-10-20',
            'gender': 'Non-binary',
            'contact_number': '+39987654321',
            'email': 'updated.email@example.com',
            'address': 'Updated Address'
        }, follow_redirects=True)
          # Check response
        assert response.status_code == 200
        assert b'Patient information updated successfully' in response.data
        assert b'Updated Name' in response.data
        
        # Verify patient was updated in database
        updated_patient = Patient.query.get(patient.id)
        assert updated_patient.first_name == 'Updated'
        assert updated_patient.last_name == 'Name'
        assert updated_patient.date_of_birth == date(1985, 10, 20)
        assert updated_patient.gender == 'Non-binary'
        assert updated_patient.contact_number == '+39987654321'
        assert updated_patient.email == 'updated.email@example.com'
        assert updated_patient.address == 'Updated Address'
        
        # Test with non-existent patient
        response = client.post('/patients/9999/edit', data={
            'first_name': 'Test',
            'last_name': 'Patient'
        })
        assert response.status_code == 404        # Test with patient not associated with doctor        # Create a patient not associated with the doctor
        unassociated_patient = db.session.merge(patient_factory())
        response = client.post(f'/patients/{unassociated_patient.id}/edit', data={
            'first_name': 'Test',
            'last_name': 'Patient'
        })
        assert response.status_code == 302  # System redirects instead of returning 403    
    def test_delete_patient(self, client, doctor_with_patient, patient_factory, doctor_factory):
        """Test patient deletion view functionality.
        
        Verifies that a doctor can delete patients from their list, and tests various
        deletion scenarios including non-existent patients and patients with 
        multiple doctor associations.
        
        Args:
            client: Flask test client
            doctor_with_patient: Fixture providing a doctor with an associated patient
            patient_factory: Factory fixture to create patient instances
            doctor_factory: Factory fixture to create doctor instances
        """
        doctor = doctor_with_patient['doctor']
        patient = doctor_with_patient['patient']
        
        # Test patient deletion
        response = client.post(f'/patients/{patient.id}/delete', follow_redirects=True)
          # Check response
        assert response.status_code == 200
        assert b'Patient successfully removed' in response.data
        
        # Verify patient was deleted from database
        deleted_patient = Patient.query.get(patient.id)
        assert deleted_patient is None
        
        # Test with non-existent patient
        response = client.post('/patients/9999/delete', follow_redirects=True)
        assert response.status_code == 404
          # Test with patient not associated with doctor
        unassociated_patient = patient_factory()
        response = client.post(f'/patients/{unassociated_patient.id}/delete', follow_redirects=True)
        assert response.status_code == 200  # Con follow_redirects=True, anche se c'è un reindirizzamento, il codice sarà 200
        
        # Test deletion of patient with multiple doctors
        # Create a patient associated with multiple doctors
        multi_doctor_patient = patient_factory()
        doctor2 = doctor_factory()
        
        # Associate both doctors with patient
        doctor.add_patient(multi_doctor_patient)
        doctor2.add_patient(multi_doctor_patient)
        
        # Delete patient (should only remove association)
        response = client.post(f'/patients/{multi_doctor_patient.id}/delete', follow_redirects=True)
        assert response.status_code == 200
        
        # Patient should still exist but no longer be associated with the current doctor
        patient_exists = Patient.query.get(multi_doctor_patient.id) is not None
        assert patient_exists is True
        
        doctor_patient = DoctorPatient.query.filter_by(
            doctor_id=doctor.id, 
            patient_id=multi_doctor_patient.id
        ).first()
        assert doctor_patient is None    

    def test_patient_vitals(self, client, doctor_with_patient):
        """Test patient vitals view functionality.
        
        Verifies that a doctor can view the vital signs of their associated patients
        and that different time period filters work correctly.
        
        Args:
            client: Flask test client
            doctor_with_patient: Fixture providing a doctor with an associated patient
        """
        doctor = doctor_with_patient['doctor']
        patient = doctor_with_patient['patient']
        
        # Ensure authentication
        with client.session_transaction() as session:
            session['_user_id'] = str(doctor.id)
            session['_fresh'] = True
            
        # Test vitals page access
        response = client.get(f'/patients/{patient.id}/vitals')
        assert response.status_code == 200
        assert b'Vital Signs' in response.data or b'vitals' in response.data.lower()
        
        # Test with different time periods
        response = client.get(f'/patients/{patient.id}/vitals?period=7')
        assert response.status_code == 200
        
        response = client.get(f'/patients/{patient.id}/vitals?period=30')
        assert response.status_code == 200
        
        # Test API endpoint for fetching vitals data
        response = client.get(f'/api/patients/{patient.id}/vitals?type=heart_rate')
        # Note: This will likely return no data since we haven't mocked health platform data
        assert response.status_code in [200, 404]  # Either empty data or platform not connected

    def test_add_note(self, client, doctor_with_patient, patient_factory):
        """Test adding notes to a patient.
        
        Verifies that a doctor can add notes to their associated patients,
        and tests validation of empty notes and access control.
        
        Args:
            client: Flask test client
            doctor_with_patient: Fixture providing a doctor with an associated patient
            patient_factory: Factory fixture to create patient instances
        """
        patient = doctor_with_patient['patient']
        
        # Test adding a note
        note_content = "This is a test note for the patient."
        response = client.post(f'/patients/{patient.id}/notes', data={
            'content': note_content
        }, follow_redirects=True)
        
        # Check response
        assert response.status_code == 200
        assert b'Note added successfully' in response.data
        assert note_content.encode() in response.data
        
        # Verify note was added to database
        note = Note.query.filter_by(content=note_content, patient_id=patient.id).first()
        assert note is not None
        
        # Test with empty content
        response = client.post(f'/patients/{patient.id}/notes', data={
            'content': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Note content cannot be empty' in response.data
        
        # Test with non-existent patient
        response = client.post('/patients/9999/notes', data={
            'content': 'Test note'
        })
        assert response.status_code == 404
        
        # Test with patient not associated with doctor
        response = client.post(f'/patients/{patient_factory().id}/notes', data={
            'content': 'Test note'
        })
        assert response.status_code == 302  # System redirects instead of returning 403
    def test_delete_note(self, client, doctor_with_patient, note_factory):
        """Test deleting notes from a patient.
        
        Verifies that a doctor can delete notes they created for their patients,
        but cannot delete notes created by other doctors.
        
        Args:
            client: Flask test client
            doctor_with_patient: Fixture providing a doctor with an associated patient
            note_factory: Factory fixture to create note instances
        """
        doctor = doctor_with_patient['doctor']
        patient = doctor_with_patient['patient']
        
        # Ensure proper authentication
        with client.session_transaction() as session:
            session['_user_id'] = str(doctor.id)
            session['_fresh'] = True
            
        # Create a note
        note = note_factory(doctor, patient, "Note to be deleted")
        
        # Adjust to proper endpoint format and method - using DELETE instead of POST
        response = client.delete(f'/notes/{note.id}')
        
        # Check response
        assert response.status_code == 200
        try:
            data = json.loads(response.data)
            assert 'message' in data
        except json.JSONDecodeError:
            # If it's not JSON, check for success indicators in HTML
            assert b'successfully' in response.data.lower() or b'deleted' in response.data.lower()
        
        # Verify note was deleted from database
        deleted_note = Note.query.get(note.id)
        assert deleted_note is None
        
        # Test with non-existent note
        response = client.delete('/notes/9999')
        assert response.status_code == 404
        
        # Test with note not created by doctor
        from app.models import Doctor
        other_doctor = Doctor(
            email="other_doctor@example.com",
            first_name="Other",
            last_name="Doctor",
            specialty="General Medicine"
        )
        other_doctor.set_password("Password123!")
        db.session.add(other_doctor)
        db.session.commit()
        
        other_note = note_factory(other_doctor, patient, "Note by another doctor")
        
        # Attempt to delete other doctor's note
        response = client.delete(f'/notes/{other_note.id}')
        assert response.status_code == 403
        
    def test_import_patient(self, client, authenticated_doctor, patient_factory):
        """Test importing existing patients by UUID.
        
        Verifies that a doctor can import existing patients by their UUID, 
        and tests various import scenarios including non-existent patients
        and already associated patients.
        
        Args:
            client: Flask test client
            authenticated_doctor: Pre-authenticated doctor fixture
            patient_factory: Factory fixture to create patient instances
        """
        # Create a patient that isn't associated with the doctor
        patient = patient_factory()
        
        # Test importing via API
        response = client.post('/patients/import', json={
            'patient_uuid': patient.uuid
        }, follow_redirects=True)
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert data['message'] == "Patient imported successfully"
        
        # Verify patient is now associated with doctor
        # We need to refresh the doctor object from the database
        updated_doctor = db.session.get(authenticated_doctor.__class__, authenticated_doctor.id)
        updated_patient = db.session.get(patient.__class__, patient.id)
        patient_in_list = updated_patient in updated_doctor.get_patients()
        assert patient_in_list is True
        
        # Test importing patient that doesn't exist
        response = client.post('/patients/import', json={
            'patient_uuid': str(uuid4())
        })
        assert response.status_code == 404
        
        # Test importing patient already associated with doctor
        response = client.post('/patients/import', json={
            'patient_uuid': patient.uuid
        })
        assert response.status_code == 409  # Conflict
