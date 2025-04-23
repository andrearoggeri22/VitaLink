import logging
import json
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file, session
from app import app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from flask_babel import gettext as _
import copy

from app import db
from models import Patient, Doctor, VitalSignType, DataOrigin, Note, DoctorPatient, ActionType, EntityType, VitalObservation
from utils import parse_date, to_serializable_dict
from reports import generate_patient_report, generate_vital_trends_report
from audit import (
    log_patient_creation, log_patient_update, log_patient_delete,
    log_vital_creation, log_note_creation, log_report_generation, log_patient_view,
    log_action
)

views_bp = Blueprint('views', __name__)
logger = logging.getLogger(__name__)

@views_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    return redirect(url_for('auth.login'))

@views_bp.route('/dashboard')
@login_required
def dashboard():
    # Get counts for dashboard
    patient_count = current_user.patients.count()
    
    # Get recent patients
    recent_patients = current_user.patients.order_by(Patient.created_at.desc()).limit(5).all()
    
    # Get recent audit logs
    from models import AuditLog
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
    # Get all patients for the current doctor
    all_patients = current_user.patients.all()
    return render_template('patients.html', patients=all_patients, now=datetime.now())

@views_bp.route('/patients/new', methods=['GET', 'POST'])
@login_required
def new_patient():
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
            
            flash(_(f'Patient {first_name} {last_name} successfully created with ID {patient.uuid}'), 'success')
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
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('You are not authorized to view this patient'), 'danger')
        return redirect(url_for('views.patients'))
    
    # Get observations
    observations = VitalObservation.query.filter_by(patient_id=patient_id).order_by(VitalObservation.created_at.desc()).all()
    
    return render_template('vitals.html', 
                          patient=patient,
                          observations=observations,
                          vital_types=[type.value for type in VitalSignType],
                          now=datetime.now())
                          
@views_bp.route('/api/patients/<int:patient_id>/vitals')
@login_required
def api_patient_vitals(patient_id):
    """API endpoint to get health platform data in JSON format"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        return jsonify({'error': 'Not authorized'}), 403
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    vital_type = request.args.get('type')
    
    # Check if patient has health platform connection
    if not patient.fitbit_access_token:
        return jsonify({'error': 'No health platform connection', 'vital_type': vital_type}), 404
    
    # Import health platform functionality
    from health_platforms import get_processed_fitbit_data
    
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
        return jsonify({'error': 'Failed to retrieve health platform data', 'message': str(e)}), 500

@views_bp.route('/patients/<int:patient_id>/notes', methods=['POST'])
@login_required
def add_note(patient_id):
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

@views_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
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

@views_bp.route('/patients/<int:patient_id>/report')
@login_required
def generate_report(patient_id):
    """Generate a comprehensive patient report in PDF format."""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('You are not authorized to generate reports for this patient'), 'danger')
        return redirect(url_for('views.patients'))
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Process date filters
    start_datetime = None
    end_datetime = None
    
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            flash(_('Invalid start date format. Use YYYY-MM-DD'), 'warning')
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Add a day to include all records from the end date
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
        except ValueError:
            flash(_('Invalid end date format. Use YYYY-MM-DD'), 'warning')
    
    # Get health platform connection status
    has_health_connection = patient.fitbit_access_token is not None
    
    # Query notes with filter
    notes_query = patient.notes
    
    if start_datetime:
        notes_query = notes_query.filter(Note.created_at >= start_datetime)
    
    if end_datetime:
        notes_query = notes_query.filter(Note.created_at <= end_datetime)
    
    notes = notes_query.order_by(Note.created_at.desc()).all()
    
    # Generate the PDF report
    try:
        # Get current language from session or from browser preferred language
        current_language = session.get('language')
        if not current_language:
            # Determine language from browser accept-languages header
            current_language = request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'en'
            
        logger.debug(f"Generating report with language: {current_language}")
        
        pdf_buffer = generate_patient_report(
            patient=patient,
            doctor=current_user,
            notes=notes,
            has_health_connection=has_health_connection,
            start_date=start_datetime,
            end_date=end_datetime,
            language=current_language
        )
        
        # Generate a filename for the report
        filename = f"patient_report_{patient.last_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Log this action in audit trail
        log_report_generation(
            doctor_id=current_user.id,
            patient_id=patient_id,
            report_type="complete",
            params={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        # Log this action in application logs
        logger.info(f"Doctor {current_user.id} generated report for patient {patient_id}")
        
        # Return the PDF as a downloadable file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        flash(_('An error occurred while generating the report'), 'danger')
        return redirect(url_for('views.patient_detail', patient_id=patient_id))

@views_bp.route('/patients/<int:patient_id>/specific_report')
@login_required
def generate_specific_report(patient_id):
    """Generate a specific vital parameter report in PDF format using health platform data."""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('You are not authorized to generate reports for this patient'), 'danger')
        return redirect(url_for('views.patients'))
    
    # Get vital type parameter
    vital_type = request.args.get('vital_type')
    if not vital_type:
        flash(_('No vital parameter type specified'), 'danger')
        return redirect(url_for('views.patient_vitals', patient_id=patient_id))
    
    # Get period parameter (in days)
    period = request.args.get('period', '7')  # Default to 7 days
    try:
        period_days = int(period)
    except ValueError:
        period_days = 7
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    
    # Period description for the report
    period_desc = f"{_('Last')} {period_days} {_('days')}"
    
    # Log the report generation attempt
    log_report_generation(current_user.id, patient.id, 'specific_vital', {
        'vital_type': vital_type,
        'period': period_days
    })
    
    try:
        # Attempt to get data from the health platform
        from health_platforms import get_processed_fitbit_data
        
        # Check if patient has Fitbit connection
        if not patient.fitbit_access_token:
            flash(_('This patient does not have an active health platform connection'), 'warning')
            return redirect(url_for('views.patient_vitals', patient_id=patient_id))
        
        # Fetch data from Fitbit
        vitals = get_processed_fitbit_data(
            patient, 
            vital_type, 
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not vitals:
            flash(_('No data available for the selected vital parameter and time period'), 'warning')
            return redirect(url_for('views.patient_vitals', patient_id=patient_id))
        
        # Get current language from session
        current_language = session.get('language', 'en')
            
        logger.debug(f"Generating specific vital report with language: {current_language}")
        
        # Generate the PDF report
        from reports import generate_vital_trends_report
        
        # Try to convert vital_type to enum if possible
        try:
            vital_type_enum = VitalSignType[vital_type.upper()]
        except (KeyError, AttributeError):
            vital_type_enum = None
        
        pdf_buffer = generate_vital_trends_report(
            patient=patient,
            vital_type=vital_type_enum or vital_type,  # Use enum if possible, otherwise string ID
            vitals=vitals,
            period_desc=period_desc,
            language=current_language
        )
        
        # Generate a filename for the report
        vital_name = vital_type.replace('_', ' ').title()
        filename = f"{vital_name}_report_{patient.last_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
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


@views_bp.route('/patients/<int:patient_id>/vital_report/<string:vital_type>')
@login_required
def generate_vital_report(patient_id, vital_type):
    """Generate a trend analysis report for a specific vital sign."""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('You are not authorized to generate reports for this patient.'), 'danger')
        return redirect(url_for('views.patients'))
    
    # Validate vital type
    try:
        vital_type_enum = VitalSignType(vital_type)
    except ValueError:
        flash(_('Invalid vital sign type'), 'danger')
        return redirect(url_for('views.patient_vitals', patient_id=patient_id))
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Process date filters
    start_datetime = None
    end_datetime = None
    period_desc = "All Records"
    
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            period_desc = _("From %(start_date)s") % {"start_date": start_date}
        except ValueError:
            flash(_('Invalid start date format. Use YYYY-MM-DD'), 'warning')
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Add a day to include all records from the end date
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            if start_date:
                period_desc = _("%(period_desc)s to %(end_date)s") % {
                    "period_desc": period_desc,
                    "end_date": end_date
                }
            else:
                period_desc = _("Until %(end_date)s") % {
                    "end_date": end_date
            }
        except ValueError:
            flash(_('Invalid end date format. Use YYYY-MM-DD'), 'warning')
    
    # Get health platform data using Fitbit API
    from health_platforms import get_processed_fitbit_data
    
    try:
        # If patient doesn't have a health platform connection, redirect
        if not patient.fitbit_access_token:
            flash(_('Patient does not have a health platform connection. Please connect first.'), 'warning')
            return redirect(url_for('views.patient_vitals', patient_id=patient_id))
            
        # Get data from Fitbit
        vitals = get_processed_fitbit_data(
            patient,
            vital_type_enum.value,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error retrieving data from health platform: {str(e)}")
        flash(_('Error retrieving data from health platform'), 'danger')
        return redirect(url_for('views.patient_vitals', patient_id=patient_id))
    
    if not vitals:
        flash(_('No data available for the selected vital parameter and time period'), 'warning')
        return redirect(url_for('views.patient_vitals', patient_id=patient_id))
    
    # Generate the PDF report
    try:
        # Get current language from session or from browser preferred language
        current_language = session.get('language')
        if not current_language:
            # Determine language from browser accept-languages header
            current_language = request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'en'
            
        logger.debug(f"Generating vital report with language: {current_language}")
        
        pdf_buffer = generate_vital_trends_report(
            patient=patient,
            vital_type=vital_type,
            vitals=vitals,
            period_desc=period_desc,
            language=current_language
        )
        
        # Generate a filename for the report
        vital_name = vital_type.replace('_', ' ').title()
        filename = f"{vital_name}_report_{patient.last_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Log this action in audit trail
        log_report_generation(
            doctor_id=current_user.id,
            patient_id=patient_id,
            report_type = _("vital_%(vital_type)s") % {
                "vital_type": vital_type
            },
            params={
                "start_date": start_date,
                "end_date": end_date,
                "vital_type": vital_type,
                "period_desc": period_desc
            }
        )
        
        # Log this action in application logs
        logger.info(f"Doctor {current_user.id} generated {vital_type} report for patient {patient_id}")
        
        # Return the PDF as a downloadable file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error generating vital report: {str(e)}")
        flash(_('An error occurred while generating the report'), 'danger')
        return redirect(url_for('views.patient_vitals', patient_id=patient_id))
