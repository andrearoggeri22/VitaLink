import logging
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from app import db
from models import Patient, Doctor, VitalSign, VitalSignType, DataOrigin, Note, DoctorPatient
from utils import parse_date

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
    
    # Get recent vital signs for this doctor's patients
    recent_vitals = VitalSign.query.join(
        DoctorPatient, VitalSign.patient_id == DoctorPatient.patient_id
    ).filter(
        DoctorPatient.doctor_id == current_user.id
    ).order_by(
        VitalSign.recorded_at.desc()
    ).limit(10).all()
    
    return render_template('dashboard.html', 
                          patient_count=patient_count,
                          recent_patients=recent_patients,
                          recent_vitals=recent_vitals,
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
            flash('First name, last name, and date of birth are required fields', 'danger')
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
            
            flash(f'Patient {first_name} {last_name} created successfully with ID {patient.uuid}', 'success')
            logger.info(f"Doctor {current_user.id} created patient {patient.id}")
            
            return redirect(url_for('views.patient_detail', patient_id=patient.id))
            
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating patient: {str(e)}")
            flash('An error occurred while creating the patient', 'danger')
    
    return render_template('patients.html', mode='new', now=datetime.now())

@views_bp.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    # Get the patient
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash('You are not authorized to view this patient', 'danger')
        return redirect(url_for('views.patients'))
    
    # Get recent vital signs
    recent_vitals = patient.vital_signs.order_by(VitalSign.recorded_at.desc()).limit(10).all()
    
    # Get notes
    notes = patient.notes.order_by(Note.created_at.desc()).all()
    
    return render_template('patient_detail.html', 
                          patient=patient,
                          recent_vitals=recent_vitals,
                          notes=notes,
                          now=datetime.now())

@views_bp.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash('You are not authorized to edit this patient', 'danger')
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
            flash('First name, last name, and date of birth are required fields', 'danger')
            return redirect(url_for('views.edit_patient', patient_id=patient_id))
        
        try:
            # Parse date
            dob = parse_date(date_of_birth)
            
            # Update patient information
            patient.first_name = first_name
            patient.last_name = last_name
            patient.date_of_birth = dob
            patient.gender = gender
            patient.contact_number = contact_number
            patient.address = address
            patient.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('Patient information updated successfully', 'success')
            logger.info(f"Doctor {current_user.id} updated patient {patient.id}")
            
            return redirect(url_for('views.patient_detail', patient_id=patient_id))
            
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating patient: {str(e)}")
            flash('An error occurred while updating the patient', 'danger')
    
    return render_template('patients.html', mode='edit', patient=patient, now=datetime.now())

@views_bp.route('/patients/<int:patient_id>/delete', methods=['POST'])
@login_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash('You are not authorized to delete this patient', 'danger')
        return redirect(url_for('views.patients'))
    
    try:
        # Remove the association between doctor and patient
        current_user.remove_patient(patient)
        
        # If the patient has no other doctors, delete the patient (optional)
        if patient.doctors.count() == 0:
            # Delete all vital signs and notes for the patient
            for vital in patient.vital_signs.all():
                db.session.delete(vital)
            
            for note in patient.notes.all():
                db.session.delete(note)
            
            db.session.delete(patient)
        
        db.session.commit()
        
        flash('Patient removed successfully', 'success')
        logger.info(f"Doctor {current_user.id} removed patient {patient_id}")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error deleting patient: {str(e)}")
        flash('An error occurred while removing the patient', 'danger')
    
    return redirect(url_for('views.patients'))

@views_bp.route('/patients/<int:patient_id>/vitals', methods=['GET', 'POST'])
@login_required
def patient_vitals(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash('You are not authorized to view this patient', 'danger')
        return redirect(url_for('views.patients'))
    
    if request.method == 'POST':
        vital_type = request.form.get('type')
        value = request.form.get('value')
        unit = request.form.get('unit')
        recorded_at = request.form.get('recorded_at')
        
        # Validate required fields
        if not vital_type or not value:
            flash('Vital sign type and value are required fields', 'danger')
            return redirect(url_for('views.patient_vitals', patient_id=patient_id))
        
        try:
            # Convert vital type to enum
            vital_type_enum = VitalSignType(vital_type)
            
            # Parse value
            value_float = float(value)
            
            # Parse date/time or use current time
            if recorded_at:
                try:
                    recorded_datetime = datetime.strptime(recorded_at, '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash('Invalid date/time format. Please use YYYY-MM-DDTHH:MM', 'danger')
                    return redirect(url_for('views.patient_vitals', patient_id=patient_id))
            else:
                recorded_datetime = datetime.utcnow()
            
            # Create new vital sign
            vital = VitalSign(
                patient_id=patient_id,
                type=vital_type_enum,
                value=value_float,
                unit=unit,
                recorded_at=recorded_datetime,
                origin=DataOrigin.MANUAL
            )
            
            db.session.add(vital)
            db.session.commit()
            
            flash('Vital sign recorded successfully', 'success')
            logger.info(f"Doctor {current_user.id} added vital sign for patient {patient_id}")
            
        except ValueError:
            flash('Invalid value format', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error adding vital sign: {str(e)}")
            flash('An error occurred while recording the vital sign', 'danger')
    
    # Get vital signs
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    vital_type = request.args.get('type')
    
    query = patient.vital_signs
    
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(VitalSign.recorded_at >= start_datetime)
        except ValueError:
            flash('Invalid start date format. Please use YYYY-MM-DD', 'warning')
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Add a day to include all records from the end date
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            query = query.filter(VitalSign.recorded_at <= end_datetime)
        except ValueError:
            flash('Invalid end date format. Please use YYYY-MM-DD', 'warning')
    
    if vital_type:
        try:
            vital_type_enum = VitalSignType(vital_type)
            query = query.filter(VitalSign.type == vital_type_enum)
        except ValueError:
            flash('Invalid vital sign type', 'warning')
    
    vitals = query.order_by(VitalSign.recorded_at.desc()).all()
    
    # Organize vitals by type for plotting
    vitals_by_type = {}
    for vital in patient.vital_signs.order_by(VitalSign.recorded_at).all():
        type_name = vital.type.value
        if type_name not in vitals_by_type:
            vitals_by_type[type_name] = []
        
        vitals_by_type[type_name].append({
            'value': vital.value,
            'recorded_at': vital.recorded_at.isoformat(),
            'unit': vital.unit
        })
    
    return render_template('vitals.html', 
                          patient=patient,
                          vitals=vitals,
                          vitals_by_type=vitals_by_type,
                          vital_types=[type.value for type in VitalSignType],
                          now=datetime.now())

@views_bp.route('/patients/<int:patient_id>/notes', methods=['POST'])
@login_required
def add_note(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash('You are not authorized to add notes for this patient', 'danger')
        return redirect(url_for('views.patients'))
    
    content = request.form.get('content')
    
    if not content:
        flash('Note content cannot be empty', 'danger')
        return redirect(url_for('views.patient_detail', patient_id=patient_id))
    
    try:
        note = Note(
            patient_id=patient_id,
            doctor_id=current_user.id,
            content=content
        )
        
        db.session.add(note)
        db.session.commit()
        
        flash('Note added successfully', 'success')
        logger.info(f"Doctor {current_user.id} added note for patient {patient_id}")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error adding note: {str(e)}")
        flash('An error occurred while adding the note', 'danger')
    
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
            flash('Profile updated successfully', 'success')
        
        # Update password
        if current_password and new_password and confirm_password:
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'danger')
            else:
                current_user.set_password(new_password)
                current_user.updated_at = datetime.utcnow()
                
                db.session.commit()
                flash('Password updated successfully', 'success')
    
    return render_template('profile.html', doctor=current_user, now=datetime.now())
