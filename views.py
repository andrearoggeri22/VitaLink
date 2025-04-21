import logging
import json
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from flask_babel import gettext as _
import copy

from app import db
from models import Patient, Doctor, VitalSign, VitalSignType, DataOrigin, Note, DoctorPatient, ActionType, EntityType
from utils import parse_date, is_vital_in_range, get_vital_sign_unit, to_serializable_dict
from notifications import notify_abnormal_vital
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
            flash(_('Nome, cognome e data di nascita sono campi obbligatori'), 'danger')
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
            
            flash(_(f'Paziente {first_name} {last_name} creato con successo con ID {patient.uuid}'), 'success')
            logger.info(f"Doctor {current_user.id} created patient {patient.id}")
            
            return redirect(url_for('views.patient_detail', patient_id=patient.id))
            
        except ValueError:
            flash(_('Formato data non valido. Utilizzare AAAA-MM-GG'), 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating patient: {str(e)}")
            flash(_('Si è verificato un errore durante la creazione del paziente'), 'danger')
    
    return render_template('patients.html', mode='new', now=datetime.now())

@views_bp.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    # Get the patient
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('Non sei autorizzato a visualizzare questo paziente'), 'danger')
        return redirect(url_for('views.patients'))
    
    # Get recent vital signs
    recent_vitals = patient.vital_signs.order_by(VitalSign.recorded_at.desc()).limit(10).all()
    
    # Get notes
    notes = patient.notes.order_by(Note.created_at.desc()).all()
    
    # Log patient view in the audit trail
    log_patient_view(current_user.id, patient.id)
    
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
        flash(_('Non sei autorizzato a modificare questo paziente'), 'danger')
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
            flash(_('Nome, cognome e data di nascita sono campi obbligatori'), 'danger')
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
            
            flash(_('Informazioni del paziente aggiornate con successo'), 'success')
            logger.info(f"Doctor {current_user.id} updated patient {patient.id}")
            
            return redirect(url_for('views.patient_detail', patient_id=patient_id))
            
        except ValueError:
            flash(_('Formato data non valido. Utilizzare AAAA-MM-GG'), 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating patient: {str(e)}")
            flash(_('Si è verificato un errore durante l\'aggiornamento del paziente'), 'danger')
    
    return render_template('patients.html', mode='edit', patient=patient, now=datetime.now())

@views_bp.route('/patients/<int:patient_id>/delete', methods=['POST'])
@login_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('Non sei autorizzato a eliminare questo paziente'), 'danger')
        return redirect(url_for('views.patients'))
    
    try:
        # Store patient data for audit log before deletion
        patient_data = patient.to_dict()
        
        # Remove the association between doctor and patient
        current_user.remove_patient(patient)
        
        # If the patient has no other doctors, delete the patient (optional)
        if patient.doctors.count() == 0:
            # Delete all vital signs and notes for the patient
            for vital in patient.vital_signs.all():
                db.session.delete(vital)
            
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
        
        flash(_('Paziente rimosso con successo'), 'success')
        logger.info(f"Doctor {current_user.id} removed patient {patient_id}")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error deleting patient: {str(e)}")
        flash(_('Si è verificato un errore durante la rimozione del paziente'), 'danger')
    
    return redirect(url_for('views.patients'))

@views_bp.route('/patients/<int:patient_id>/vitals', methods=['GET', 'POST'])
@login_required
def patient_vitals(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('Non sei autorizzato a visualizzare questo paziente'), 'danger')
        return redirect(url_for('views.patients'))
    
    if request.method == 'POST':
        vital_type = request.form.get('type')
        value = request.form.get('value')
        unit = request.form.get('unit')
        recorded_at = request.form.get('recorded_at')
        
        # Validate required fields
        if not vital_type or not value:
            flash(_('Il tipo di parametro vitale e il valore sono campi obbligatori'), 'danger')
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
                    flash(_('Formato data/ora non valido. Utilizzare AAAA-MM-GGTHH:MM'), 'danger')
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
            
            # Log the vital sign creation in the audit trail
            log_vital_creation(current_user.id, vital)
            
            # Check if the vital sign is outside normal range
            vital_value = str(value_float) if vital_type != 'blood_pressure' else value
            is_normal, status = is_vital_in_range(vital_type, vital_value)
            
            # If value is abnormal and patient has contact number, send notification
            notification_status = ""
            if not is_normal and patient.contact_number:
                if not unit:
                    unit = get_vital_sign_unit(vital_type)
                    
                # Send SMS notification
                success, message = notify_abnormal_vital(
                    patient=patient,
                    vital_type=vital_type,
                    value=vital_value,
                    unit=unit,
                    status=status
                )
                
                if success:
                    notification_status = f" {_('Abnormal value detected')}. {_('Patient notification sent')}."
                    logger.info(f"Abnormal vital notification sent to patient {patient.id}")
                else:
                    notification_status = f" {_('Abnormal value detected')}. {_('Failed to send notification')}: {_(message)}"
                    logger.warning(f"Failed to send vital notification to patient {patient.id}: {message}")
            elif not is_normal:
                notification_status = f" {_('Abnormal value detected')} ({_('patient has no contact number for notifications')})."
            
            flash(f'{_("Vital sign recorded successfully")}.{notification_status}', 'success')
            logger.info(f"Doctor {current_user.id} added vital sign for patient {patient_id}")
            
        except ValueError:
            flash(_('Formato valore non valido'), 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error adding vital sign: {str(e)}")
            flash(_('Si è verificato un errore durante la registrazione del parametro vitale'), 'danger')
    
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
            flash(_('Formato data di inizio non valido. Utilizzare AAAA-MM-GG'), 'warning')
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Add a day to include all records from the end date
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            query = query.filter(VitalSign.recorded_at <= end_datetime)
        except ValueError:
            flash(_('Formato data di fine non valido. Utilizzare AAAA-MM-GG'), 'warning')
    
    if vital_type:
        try:
            vital_type_enum = VitalSignType(vital_type)
            query = query.filter(VitalSign.type == vital_type_enum)
        except ValueError:
            flash(_('Tipo di parametro vitale non valido'), 'warning')
    
    vitals = query.order_by(VitalSign.recorded_at.desc()).all()
    
    # Get all vital sign types for tabs
    vitals_by_type = {}
    for vital in patient.vital_signs.all():
        type_name = vital.type.value
        if type_name not in vitals_by_type:
            vitals_by_type[type_name] = True
    
    return render_template('vitals.html', 
                          patient=patient,
                          vitals=vitals,
                          vitals_by_type=vitals_by_type,
                          vital_types=[type.value for type in VitalSignType],
                          now=datetime.now())
                          
@views_bp.route('/api/patients/<int:patient_id>/vitals')
@login_required
def api_patient_vitals(patient_id):
    """API endpoint to get vital signs data in JSON format"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        return jsonify({'error': 'Not authorized'}), 403
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    vital_type = request.args.get('type')
    
    query = patient.vital_signs
    
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(VitalSign.recorded_at >= start_datetime)
        except ValueError:
            return jsonify({'error': 'Invalid start date format'}), 400
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            query = query.filter(VitalSign.recorded_at <= end_datetime)
        except ValueError:
            return jsonify({'error': 'Invalid end date format'}), 400
    
    if vital_type:
        try:
            vital_type_enum = VitalSignType(vital_type)
            query = query.filter(VitalSign.type == vital_type_enum)
        except ValueError:
            return jsonify({'error': 'Invalid vital sign type'}), 400
    
    # Organize vitals by type for plotting
    vitals_by_type = {}
    for vital in query.order_by(VitalSign.recorded_at).all():
        type_name = vital.type.value
        if type_name not in vitals_by_type:
            vitals_by_type[type_name] = []
        
        vitals_by_type[type_name].append({
            'value': float(vital.value),
            'recorded_at': vital.recorded_at.isoformat(),
            'unit': vital.unit or get_vital_sign_unit(type_name)
        })
    
    return jsonify(vitals_by_type)

@views_bp.route('/patients/<int:patient_id>/notes', methods=['POST'])
@login_required
def add_note(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('Non sei autorizzato ad aggiungere note per questo paziente'), 'danger')
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
        
        # Log the note creation in the audit trail
        log_note_creation(current_user.id, note)
        
        flash(_('Nota aggiunta con successo'), 'success')
        logger.info(f"Doctor {current_user.id} added note for patient {patient_id}")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error adding note: {str(e)}")
        flash(_('Si è verificato un errore durante l\'aggiunta della nota'), 'danger')
    
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
            flash(_('Profilo aggiornato con successo'), 'success')
        
        # Update password
        if current_password and new_password and confirm_password:
            if not current_user.check_password(current_password):
                flash(_('La password attuale non è corretta'), 'danger')
            elif new_password != confirm_password:
                flash(_('Le nuove password non corrispondono'), 'danger')
            else:
                current_user.set_password(new_password)
                current_user.updated_at = datetime.utcnow()
                
                db.session.commit()
                flash(_('Password aggiornata con successo'), 'success')
    
    return render_template('profile.html', doctor=current_user, now=datetime.now())

@views_bp.route('/patients/<int:patient_id>/report')
@login_required
def generate_report(patient_id):
    """Generate a comprehensive patient report in PDF format."""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('Non sei autorizzato a generare report per questo paziente'), 'danger')
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
            flash(_('Formato data di inizio non valido. Utilizzare AAAA-MM-GG'), 'warning')
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Add a day to include all records from the end date
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
        except ValueError:
            flash(_('Formato data di fine non valido. Utilizzare AAAA-MM-GG'), 'warning')
    
    # Query vitals with filter
    vitals_query = patient.vital_signs
    
    if start_datetime:
        vitals_query = vitals_query.filter(VitalSign.recorded_at >= start_datetime)
    
    if end_datetime:
        vitals_query = vitals_query.filter(VitalSign.recorded_at <= end_datetime)
    
    vitals = vitals_query.order_by(VitalSign.recorded_at.desc()).all()
    
    # Query notes with filter
    notes_query = patient.notes
    
    if start_datetime:
        notes_query = notes_query.filter(Note.created_at >= start_datetime)
    
    if end_datetime:
        notes_query = notes_query.filter(Note.created_at <= end_datetime)
    
    notes = notes_query.order_by(Note.created_at.desc()).all()
    
    # Generate the PDF report
    try:
        pdf_buffer = generate_patient_report(
            patient=patient,
            doctor=current_user,
            vitals=vitals,
            notes=notes,
            start_date=start_datetime,
            end_date=end_datetime
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
        flash(_('Si è verificato un errore durante la generazione del report'), 'danger')
        return redirect(url_for('views.patient_detail', patient_id=patient_id))

@views_bp.route('/patients/<int:patient_id>/vital_report/<string:vital_type>')
@login_required
def generate_vital_report(patient_id, vital_type):
    """Generate a trend analysis report for a specific vital sign."""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if the current doctor is associated with this patient
    if patient not in current_user.patients.all():
        flash(_('Non sei autorizzato a generare report per questo paziente'), 'danger')
        return redirect(url_for('views.patients'))
    
    # Validate vital type
    try:
        vital_type_enum = VitalSignType(vital_type)
    except ValueError:
        flash(_('Tipo di parametro vitale non valido'), 'danger')
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
            period_desc = f"From {start_date}"
        except ValueError:
            flash(_('Formato data di inizio non valido. Utilizzare AAAA-MM-GG'), 'warning')
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Add a day to include all records from the end date
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            if start_date:
                period_desc = f"{period_desc} to {end_date}"
            else:
                period_desc = f"Until {end_date}"
        except ValueError:
            flash(_('Formato data di fine non valido. Utilizzare AAAA-MM-GG'), 'warning')
    
    # Query vitals with filter
    vitals_query = patient.vital_signs.filter(VitalSign.type == vital_type_enum)
    
    if start_datetime:
        vitals_query = vitals_query.filter(VitalSign.recorded_at >= start_datetime)
    
    if end_datetime:
        vitals_query = vitals_query.filter(VitalSign.recorded_at <= end_datetime)
    
    vitals = vitals_query.order_by(VitalSign.recorded_at).all()
    
    if not vitals:
        flash(_('Nessun dato disponibile per il parametro vitale e il periodo di tempo selezionati'), 'warning')
        return redirect(url_for('views.patient_vitals', patient_id=patient_id))
    
    # Generate the PDF report
    try:
        pdf_buffer = generate_vital_trends_report(
            patient=patient,
            vital_type=vital_type,
            vitals=vitals,
            period_desc=period_desc
        )
        
        # Generate a filename for the report
        vital_name = vital_type.replace('_', ' ').title()
        filename = f"{vital_name}_report_{patient.last_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Log this action in audit trail
        log_report_generation(
            doctor_id=current_user.id,
            patient_id=patient_id,
            report_type=f"vital_{vital_type}",
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
        flash(_('Si è verificato un errore durante la generazione del report'), 'danger')
        return redirect(url_for('views.patient_vitals', patient_id=patient_id))
