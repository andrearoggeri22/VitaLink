"""
Views Module.

This module provides the main web interface routes for the VitaLink application.
It includes routes for:

1. Dashboard and landing pages
2. Patient management (creation, viewing, editing, deletion)
3. Patient vital signs visualization
4. Medical notes management
5. Reports generation and export
6. Audit log viewing

All routes in this module use templates for rendering HTML responses and
integrate with the Flask-Login system for authentication.
"""

import logging
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file, session
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from flask_babel import gettext as _

from .app import db
from .models import (Patient, VitalSignType, Note, DoctorPatient, ActionType, EntityType, VitalObservation)
from .utils import (parse_date, validate_uuid)
from .audit import (
    log_patient_creation, log_patient_update, log_patient_delete,
    log_note_creation, log_report_generation, log_patient_view, log_action,
    log_patient_import
)

views_bp = Blueprint('views', __name__)
logger = logging.getLogger(__name__)

@views_bp.route('/')
def index():
    """
    Landing page route.
    
    This route serves as the entry point to the application.
    Authenticated users are redirected to the dashboard.
    Unauthenticated users are redirected to the login page.
    
    Returns:
        Response: Redirect to appropriate page based on authentication status
    """
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    return redirect(url_for('auth.login'))

@views_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Doctor dashboard route.
    
    Displays an overview of the doctor's patients, recent activities, and
    system statistics. This is the main landing page after authentication.
    
    Returns:
        Response: Rendered dashboard template with context data
    """
    # Get counts for dashboard
    patient_count = current_user.patients.count()
    
    # Get recent patients
    recent_patients = current_user.patients.order_by(Patient.created_at.desc()).limit(5).all()
    
    # Get recent audit logs
    from .models import AuditLog
    recent_audits = AuditLog.query.filter_by(doctor_id=current_user.id).order_by(
        AuditLog.timestamp.desc()
    ).limit(10).all()
    
    # Get recent observations
    recent_observations = VitalObservation.query.join(
        DoctorPatient, VitalObservation.patient_id == DoctorPatient.patient_id
    ).filter(
        DoctorPatient.doctor_id == current_user.id
    ).order_by(
        VitalObservation.created_at.desc()
    ).limit(10).all()
    
    return render_template('dashboard.html', 
                          patient_count=patient_count,
                          recent_patients=recent_patients,
                          recent_observations=recent_observations,
                          recent_audits=recent_audits,
                          now=datetime.now())

@views_bp.route('/patients')
@login_required
def patients():
    """
    Display list of all patients for the current doctor.
    
    This route retrieves and displays all patients associated with the 
    authenticated doctor. It provides an overview of the doctor's patient list
    and serves as the main patient management interface.
    
    The page includes functionality for:
    - Viewing patient details
    - Adding new patients
    - Importing existing patients by UUID
    - Searching and filtering patients
    
    Returns:
        Response: Rendered template with list of all patients 
                 associated with the current doctor
    """
    # Get all patients for the current doctor
    all_patients = current_user.patients.all()
    return render_template('patients.html', patients=all_patients, now=datetime.now())

@views_bp.route('/patients/import', methods=['POST'])
@login_required
def import_patient():
    """
    Import an existing patient into doctor's patient list by UUID.
    
    This endpoint allows doctors to associate themselves with existing patients
    in the system by providing the patient's UUID. This is useful when multiple
    doctors need to collaborate on patient care.
    
    Request Body JSON:
        patient_uuid (str): UUID of the patient to import
        
    Returns:
        JSON response with success message or error details
        
    Status Codes:
        200: Patient imported successfully
        400: Invalid request data or UUID format
        404: Patient not found
        409: Patient already associated with the doctor
        500: Database or server error
    """
    data = request.json
    
    # Validate request data
    if not data or 'patient_uuid' not in data:
        return jsonify({"error": _("Patient UUID is required")}), 400
    
    patient_uuid = data['patient_uuid']
    
    # Validate UUID format
    if not validate_uuid(patient_uuid):
        return jsonify({"error": _("Invalid UUID format")}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error": _("Patient not found")}), 404
    
    # Check if the doctor is already associated with this patient
    if patient in current_user.patients.all():
        return jsonify({"error": _("Patient is already associated with your account")}), 409
    
    try:
        # Add patient to doctor's patients
        doctor_patient = DoctorPatient(doctor_id=current_user.id, patient_id=patient.id)
        db.session.add(doctor_patient)
        db.session.commit()
        
        # Log the import action
        log_patient_import(current_user.id, patient)
        
        return jsonify({
            "message": _("Patient imported successfully"),
            "patient": patient.to_dict()
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error importing patient: {str(e)}")
        return jsonify({"error": _("A database error occurred while importing the patient")}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing patient: {str(e)}")
        return jsonify({"error": _("An error occurred while importing the patient")}), 500

@views_bp.route('/patients/new', methods=['GET', 'POST'])
@login_required
def new_patient():
    """
    Create a new patient record.
    
    This route handles both displaying the new patient form (GET)
    and processing the form submission (POST).
    
    For GET requests:
        Displays the form to enter patient information
        
    For POST requests:
        Validates and processes form data
        Creates a new patient record
        Associates the patient with the current doctor
        Logs the patient creation in the audit trail
    
    Returns:
        GET: Rendered form template
        POST (success): Redirect to patient's detail page
        POST (failure): Redirect back to form with error message
    """
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        contact_number = request.form.get('contact_number')
        address = request.form.get('address')
        
        # Validate required fields
        if not first_name or not last_name or not date_of_birth:
            flash(_('Name, surname and date of birth are mandatory fields'), 'danger')
            return redirect(url_for('views.new_patient'))
        
        try:
            # Parse date
            dob = parse_date(date_of_birth)
            
            # Create new patient
            patient = Patient(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob,
                gender=gender,
                contact_number=contact_number,
                address=address
            )
            
            db.session.add(patient)
            db.session.flush()  # Flush to get the patient ID
            
            # Associate the patient with the current doctor
            association = DoctorPatient(doctor_id=current_user.id, patient_id=patient.id)
            db.session.add(association)
            
            db.session.commit()
            
            # Log the patient creation in the audit trail
            log_patient_creation(current_user.id, patient)
            
            flash(_('Patient %(first_name)s %(last_name)s successfully created with ID %(uuid)s') % {
                'first_name': first_name,
                'last_name': last_name,
                'uuid': patient.uuid
            }, 'success')
            logger.info(f"Doctor {current_user.id} created patient {patient.id}")
            
            return redirect(url_for('views.patient_detail', patient_id=patient.id))
            
        except ValueError:
            flash(_('Invalid date format. Use YYYY-MM-DD'), 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating patient: {str(e)}")
            flash(_('An error occurred while creating the patient'), 'danger')
    
    return render_template('patients.html', mode='new', now=datetime.now())

@views_bp.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    """
    Display detailed information about a specific patient.
    
    This route shows comprehensive information about a patient,
    including personal details and medical notes. It also logs
    the view action in the audit trail for tracking purposes.
    
    Args:
        patient_id (int): ID of the patient to display
        
    Returns:
        Response: Rendered patient detail template or redirect
                 if unauthorized
    
    Security:
        Verifies that the current doctor is associated with the patient
        before displaying any information
    """
    # Get the patient
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('You are not authorized to view this patient.'), 'danger')
        return redirect(url_for('views.patients'))
    
    # Get notes
    notes = patient.notes.order_by(Note.created_at.desc()).all()
    
    # Log patient view in the audit trail
    log_patient_view(current_user.id, patient.id)
    
    return render_template('patient_detail.html', 
                          patient=patient,
                          notes=notes,
                          now=datetime.now())

@views_bp.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    """
    Edit an existing patient's information.
    
    This route handles both displaying the patient edit form (GET)
    and processing form submissions to update patient data (POST).
    Changes are logged in the audit trail for accountability.
    
    Args:
        patient_id (int): ID of the patient to edit
        
    Request Form Data (POST):
        first_name (str): Patient's updated first name
        last_name (str): Patient's updated last name
        date_of_birth (str): Updated date of birth in YYYY-MM-DD format
        gender (str): Updated gender
        contact_number (str): Updated contact number
        address (str): Updated address
        
    Returns:
        GET: Rendered form template with patient data
        POST (success): Redirect to patient's detail page
        POST (failure): Redirect back to form with error message
        
    Security:
        Verifies that the current doctor is associated with the patient
        before allowing any modifications
    """
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('You are not authorized to modify this patient.'), 'danger')
        return redirect(url_for('views.patients'))
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        contact_number = request.form.get('contact_number')
        address = request.form.get('address')
        
        # Validate required fields
        if not first_name or not last_name or not date_of_birth:
            flash(_('Name, surname and date of birth are mandatory fields'), 'danger')
            return redirect(url_for('views.edit_patient', patient_id=patient_id))
        
        try:
            # Parse date
            dob = parse_date(date_of_birth)
            
            # Save original data for audit log
            old_data = patient.to_dict()
            
            # Update patient information
            patient.first_name = first_name
            patient.last_name = last_name
            patient.date_of_birth = dob
            patient.gender = gender
            patient.contact_number = contact_number
            patient.address = address
            patient.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log the patient update in the audit trail
            log_patient_update(current_user.id, patient, old_data)
            
            flash(_('Patient information updated successfully'), 'success')
            logger.info(f"Doctor {current_user.id} updated patient {patient.id}")
            
            return redirect(url_for('views.patient_detail', patient_id=patient_id))
            
        except ValueError:
            flash(_('Invalid date format. Use YYYY-MM-DD'), 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating patient: {str(e)}")
            flash(_('An error occurred while updating the patient'), 'danger')
    
    return render_template('patients.html', mode='edit', patient=patient, now=datetime.now())

@views_bp.route('/patients/<int:patient_id>/delete', methods=['POST'])
@login_required
def delete_patient(patient_id):
    """
    Delete or disassociate a patient from the current doctor.
    
    This endpoint handles two scenarios:
    1. If the patient is associated with other doctors, only the association
       between the current doctor and patient is removed
    2. If this is the last doctor associated with the patient, all patient data
       (including notes) is completely removed from the system
    
    Args:
        patient_id (int): ID of the patient to delete or disassociate
        
    Returns:
        Response: Redirect to patients list with success or error message
        
    Security:
        Verifies that the current doctor is associated with the patient
        before allowing deletion or disassociation
        
    Notes:
        This operation logs either a patient deletion or disassociation
        in the audit trail for accountability
    """
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('You are not authorized to delete this patient.'), 'danger')
        return redirect(url_for('views.patients'))
    
    try:
        # Store patient data for audit log before deletion
        patient_data = patient.to_dict()
        
        # Remove the association between doctor and patient
        current_user.remove_patient(patient)
        
        # If the patient has no other doctors, delete the patient (optional)
        if patient.doctors.count() == 0:
            # Delete all notes for the patient
            for note in patient.notes.all():
                db.session.delete(note)
            
            # Log complete patient deletion in the audit trail before actually deleting
            log_patient_delete(current_user.id, patient)
            
            # Now delete the patient
            db.session.delete(patient)
        else:
            # Log patient disassociation in the audit trail
            log_action(
                doctor_id=current_user.id,
                action_type=ActionType.UPDATE,
                entity_type=EntityType.PATIENT,
                entity_id=patient.id,
                details={
                    'action': 'disassociate',
                    'patient_data': patient_data
                },
                patient_id=patient.id
            )
        
        db.session.commit()
        
        flash(_('Patient successfully removed'), 'success')
        logger.info(f"Doctor {current_user.id} removed patient {patient_id}")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error deleting patient: {str(e)}")
        flash(_('An error occurred while removing the patient'), 'danger')
    
    return redirect(url_for('views.patients'))

@views_bp.route('/patients/<int:patient_id>/vitals', methods=['GET'])
@login_required
def patient_vitals(patient_id):
    """
    Display vital signs data and observations for a patient.
    
    This route renders the vital signs visualization page for a specific patient.
    It displays charts, observations, and provides options for filtering
    and analyzing the patient's health data.
    
    Args:
        patient_id (int): ID of the patient to display vital signs for
        
    Query Parameters:
        period (int, optional): Time period in days for filtering data, 
                               defaults to 7 if not specified
        
    Returns:
        Response: Rendered vitals template with patient data and observations
                 or redirect if unauthorized
        
    Security:
        Verifies that the current doctor is associated with the patient
        before displaying any information
    """
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('You are not authorized to view this patient'), 'danger')
        return redirect(url_for('views.patients'))
      # Get observations
    observations = VitalObservation.query.filter_by(patient_id=patient_id).order_by(VitalObservation.created_at.desc()).all()
    
    # Get current period from query parameters or default to 7
    current_period = request.args.get('period', 7, type=int)
    
    return render_template('vitals.html', 
                          patient=patient,
                          observations=observations,
                          vital_types=[type.value for type in VitalSignType],
                          currentPeriod=current_period,
                          now=datetime.now())
                          
@views_bp.route('/api/patients/<int:patient_id>/vitals')
@login_required
def api_patient_vitals(patient_id):
    """
    API endpoint to retrieve patient vital sign data from health platforms.
    
    This endpoint fetches data from external health platforms (like Fitbit)
    that are connected to the patient's account. It returns the data in JSON
    format for use in charts, reports, and analysis.
    
    Args:
        patient_id (int): ID of the patient to get vital signs for
        
    Query Parameters:
        start_date (str, optional): ISO formatted start date to filter data
        end_date (str, optional): ISO formatted end date to filter data
        type (str): Type of vital sign to retrieve (heart_rate, steps, etc.)
        
    Returns:
        JSON: Vital sign data organized by type or error message
        
    Status Codes:
        200: Data retrieved successfully (even if empty)
        403: Doctor not authorized to access this patient
        404: Patient has no health platform connection
        500: Error retrieving data from health platform
        
    Security:
        Verifies that the current doctor is associated with the patient
        Validates that the patient has a connected health platform
    """
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        return jsonify({'error': _('Not authorized')}), 403
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    vital_type = request.args.get('type')
    
    # Check if patient has health platform connection
    if not patient.platform_access_token:
        return jsonify({'error': _('No health platform connection'), 'vital_type': vital_type}), 404
    
    # Import health platform functionality
    from .health_platforms import get_processed_fitbit_data
    
    # Get data from Fitbit
    try:
        data = get_processed_fitbit_data(
            patient,
            vital_type,
            start_date=start_date,
            end_date=end_date
        )
        
        if not data:
            return jsonify({vital_type: []}), 200
        
        # Organize data by vital type
        return jsonify({vital_type: data}), 200
    except Exception as e:
        logger.error(f"Error getting data from health platform: {str(e)}")
        return jsonify({'error': _('Failed to retrieve health platform data'), 'message': str(e)}), 500

@views_bp.route('/patients/<int:patient_id>/notes', methods=['POST'])
@login_required
def add_note(patient_id):
    """
    Add a new medical note for a specific patient.
    
    This route handles the creation of a new medical note associated with a patient.
    The note is created by the authenticated doctor and includes a timestamp.
    The action is logged in the audit trail for accountability.
    
    Args:
        patient_id (int): ID of the patient to add a note for
        
    Request Form Data:
        content (str): The text content of the medical note
        
    Returns:
        Response: Redirect to patient detail page with success or error message
        
    Security:
        Verifies that the current doctor is associated with the patient
        before allowing note creation
    """
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('You are not allowed to add notes for this patient'), 'danger')
        return redirect(url_for('views.patients'))
    
    content = request.form.get('content')
    
    if not content:
        flash(_('Note content cannot be empty'), 'danger')
        return redirect(url_for('views.patient_detail', patient_id=patient_id))
    
    try:
        note = Note(
            patient_id=patient_id,
            doctor_id=current_user.id,
            content=content
        )
        
        db.session.add(note)
        db.session.commit()
        
        # Log the note creation in the audit trail
        log_note_creation(current_user.id, note)
        
        flash(_('Note added successfully'), 'success')
        logger.info(f"Doctor {current_user.id} added note for patient {patient_id}")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error adding note: {str(e)}")
        flash(_('An error occurred while adding the note'), 'danger')
    
    return redirect(url_for('views.patient_detail', patient_id=patient_id))

@views_bp.route('/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    """
    Delete a specific medical note.
    
    This API endpoint handles the deletion of medical notes. It implements several
    security checks to ensure that only authorized doctors can delete notes:
    1. The doctor must be associated with the patient
    2. The doctor must be the original author of the note
    
    The deletion is logged in the audit trail for accountability.
    
    Args:
        note_id (int): ID of the note to delete
        
    Returns:
        JSON: Success message and deleted note data or error message
        
    Status Codes:
        200: Note deleted successfully
        403: Not authorized to delete this note
        404: Note or patient not found
        500: Database error occurred
    """
    # Find the note
    note = Note.query.get_or_404(note_id)
    
    # Find the patient
    patient = Patient.query.get(note.patient_id)
    
    if not patient:
        return jsonify({"error": _("Patient not found")}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in current_user.patients.all():
        return jsonify({"error": _("You are not authorized to access this patient")}), 403
    
    # Check if the doctor is the author of the note
    if note.doctor_id != current_user.id:
        return jsonify({"error": _("You can only delete notes you have created")}), 403
    
    # Delete the note
    try:
        # Log the note deletion
        from .audit import log_note_delete
        log_note_delete(current_user.id, note)
        
        # Store note details for response
        note_dict = note.to_dict()
        
        db.session.delete(note)
        db.session.commit()
        
        logger.info(f"Note {note_id} deleted")
        
        return jsonify({
            "message": _("Note deleted successfully"),
            "note": note_dict
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error deleting note: {str(e)}")
        return jsonify({"error": _("An error occurred while deleting the note")}), 500

@views_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Doctor profile management route.
    
    This route handles both displaying and updating the doctor's profile information:
    - For GET requests: Displays the doctor's current profile information and a form to update it
    - For POST requests: Processes form submissions to update the doctor's information
    
    The profile update functionality is divided into two parts:
    1. Updating basic information (name, specialty)
    2. Changing password (requires current password verification)
    
    Returns:
        GET: Rendered profile template with doctor data
        POST: Same template with success or error messages based on update result
        
    Security:
        Uses login_required decorator to ensure only authenticated doctors can access
        Verifies current password before allowing password changes
    """
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        specialty = request.form.get('specialty')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Update basic information
        if first_name and last_name:
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.specialty = specialty
            current_user.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash(_('Profile updated successfully'), 'success')
        
        # Update password
        if current_password and new_password and confirm_password:
            if not current_user.check_password(current_password):
                flash(_('The current password is incorrect'), 'danger')
            elif new_password != confirm_password:
                flash(_('New passwords do not match'), 'danger')
            else:
                current_user.set_password(new_password)
                current_user.updated_at = datetime.utcnow()
                
                db.session.commit()
                flash(_('Password updated successfully'), 'success')
    
    return render_template('profile.html', doctor=current_user, now=datetime.now())

@views_bp.route('/patients/<int:patient_id>/specific_report', methods=['GET', 'POST'])
@login_required
def create_specific_patient_report(patient_id):
    """
    Generate a customized medical report for a specific patient.
    
    This route provides a powerful reporting system that allows doctors to create
    comprehensive, tailored medical reports with selected:
    - Medical notes
    - Vital sign types
    - Data visualization charts with different time periods
    - Clinical observations
    - Custom summary text
    
    The generated report is provided as a downloadable PDF file, and the report
    generation action is logged in the audit trail.
    
    Args:
        patient_id (int): ID of the patient to generate a report for
        
    Query Parameters (for GET):
        vital_type (str, optional): Pre-select specific vital sign type
        period (str, optional): Pre-select specific time period
        select_all (bool, optional): Whether to pre-select all available options
        
    Request Form Data (for POST):
        summary (str, optional): Doctor's summary text for the report
        selected_notes (list): IDs of selected medical notes to include
        selected_vital_types (list): Types of vital signs to include
        charts_* (list): Time periods to include for each vital type's charts 
        selected_observations (list): IDs of observations to include
        
    Returns:
        GET: Rendered report configuration form
        POST: Downloadable PDF report or redirect with error message
        
    Security:
        Verifies that the current doctor is associated with the patient
        before allowing report generation
    """
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('You are not authorized to generate reports for this patient'), 'danger')
        return redirect(url_for('views.patients'))
    
    if request.method == 'POST':
        try:
            # Get summary
            summary = request.form.get('summary')
            
            # Parse selected notes
            selected_note_ids = request.form.getlist('selected_notes')
            selected_notes = []
            if selected_note_ids:
                selected_notes = Note.query.filter(Note.id.in_(selected_note_ids)).all()
            
            # Parse selected vital types
            selected_vital_types_values = request.form.getlist('selected_vital_types')
            selected_vital_types = []
            for value in selected_vital_types_values:
                for enum_member in VitalSignType:
                    if enum_member.value == value:
                        selected_vital_types.append(enum_member)
                        break
                        
            # Parse selected charts
            selected_charts = {}
            for vital_type in selected_vital_types_values:
                charts_key = f"charts_{vital_type}"
                selected_periods = request.form.getlist(charts_key)
                
                # Convert period strings to days numbers
                days_periods = []
                for period in selected_periods:
                    if period == '1d':
                        days_periods.append(1)
                    elif period == '7d':
                        days_periods.append(7)
                    elif period == '1m':
                        days_periods.append(30)
                    elif period == '3m':
                        days_periods.append(90)
                
                selected_charts[vital_type] = days_periods
                
            # Parse selected observations
            selected_observation_ids = request.form.getlist('selected_observations')
            selected_observations = []
            if selected_observation_ids:
                selected_observations = VitalObservation.query.filter(VitalObservation.id.in_(selected_observation_ids)).all()
            
            # Use the current session language if available
            current_language = session.get('language', 'en')
            
            logger.debug(f"Generating specific report with language: {current_language}")
            
            # Generate the PDF report
            from .reports import generate_specific_report
            pdf_buffer = generate_specific_report(
                patient, 
                current_user, 
                selected_notes, 
                selected_vital_types,
                selected_charts,
                selected_observations,
                summary=summary,
                language=current_language
            )
            
            # Generate a filename for the report
            filename = f"specific_report_{patient.last_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            
            # Log the report generation
            log_report_generation(
                current_user.id, 
                patient.id, 
                "specific", 
                {
                    "notes_count": len(selected_notes),
                    "vital_types": [vt.value for vt in selected_vital_types],
                    "charts_count": sum(len(periods) for periods in selected_charts.values()),
                    "observations_count": len(selected_observations),
                    "has_summary": summary is not None
                }
            )
            
            logger.info(f"Doctor {current_user.id} generated specific report for patient {patient_id}")
            
            # Return the PDF as a downloadable file
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
        except Exception as e:
            logger.exception(f"Error generating specific report: {str(e)}")
            flash(_('Error generating specific report: %(error)s', error=str(e)), 'danger')
            return redirect(url_for('views.patient_vitals', patient_id=patient_id))
      # GET request - load data for the form
    notes = patient.notes.order_by(Note.created_at.desc()).all()
    observations = VitalObservation.query.filter_by(patient_id=patient_id).all()
    
    # Group observations by vital type
    observations_by_type = {}
    for obs in observations:
        vital_type = obs.vital_type.value
        if vital_type not in observations_by_type:
            observations_by_type[vital_type] = []
        observations_by_type[vital_type].append(obs)
      # Check for specific vital type in query parameters
    vital_type_param = request.args.get('vital_type')
    period_param = request.args.get('period')
    select_all_param = request.args.get('select_all')
    
    logger.info(f"Loading report form with parameters: vital_type={vital_type_param}, period={period_param}, select_all={select_all_param}")
    return render_template(
        'specific_report_form.html',  # We use the updated template
        patient=patient,
        notes=notes,
        vital_types=list(VitalSignType),
        observations_by_type=observations_by_type,
        vital_type_param=vital_type_param,
        period_param=period_param,
        select_all_param=select_all_param,
        now=datetime.now()
    )