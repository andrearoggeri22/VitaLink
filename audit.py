from datetime import datetime, timedelta
import logging
from flask import request, current_app, jsonify, Blueprint, render_template
from flask_login import current_user, login_required

from models import AuditLog, ActionType, EntityType, Doctor, Patient, Note, DoctorPatient, HealthPlatformLink, HealthPlatform, VitalObservation
from app import db
from auth import doctor_required

# Initialize logger
logger = logging.getLogger(__name__)

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/audit-logs')
@login_required
@doctor_required
def view_logs():
    """
    View all audit logs for the current doctor
    
    Returns:
        Response: HTML page with all audit logs
    """
    # Get all audit logs for the current doctor, ordered by timestamp (most recent first)
    logs = AuditLog.query.filter_by(doctor_id=current_user.id).order_by(
        AuditLog.timestamp.desc()
    ).all()
    
    return render_template('audit_logs.html', logs=logs)

def log_action(doctor_id, action_type, entity_type, entity_id, details=None, patient_id=None):
    """
    Create a new audit log entry.
    
    Args:
        doctor_id (int): ID of the doctor who performed the action
        action_type (ActionType): Type of action performed
        entity_type (EntityType): Type of entity affected
        entity_id (int): ID of the entity affected
        details (dict, optional): Additional details about the action
        patient_id (int, optional): ID of the patient related to the action (for easier querying)
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
    """
    try:
        # Check that entity_id is not None to avoid "not-null constraint" error
        if entity_id is None:
            # If ID is None, use a temporary default value
            # In a production system, we should handle this differently
            entity_id = 0
            print(f"WARNING: entity_id is None for {entity_type}. Using temporary ID 0.")
        
        ip_address = request.remote_addr if request else None
        
        # Log the params for debugging
        print(f"DEBUG: log_action - doctor_id={doctor_id}, action_type={action_type}, entity_type={entity_type}, entity_id={entity_id}")
        
        audit_log = AuditLog(
            doctor_id=doctor_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            patient_id=patient_id,
            ip_address=ip_address
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
        return audit_log
    except Exception as e:
        # In case of error, perform rollback and log the error
        db.session.rollback()
        import traceback
        print(f"Error in log_action: {str(e)}")
        print(f"Parameters: doctor_id={doctor_id}, action_type={action_type}, entity_type={entity_type}, entity_id={entity_id}")
        print(traceback.format_exc())
        # Don't let the entire operation fail if logging fails
        return None

@audit_bp.route('/logs', methods=['GET'])
@login_required
@doctor_required
def get_audit_logs():
    """
    Get audit logs filtered by various parameters.
    Supports filtering by date range, doctor, patient, action type, and entity type.
    """
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    doctor_id = request.args.get('doctor_id')
    patient_id = request.args.get('patient_id')
    action_type = request.args.get('action_type')
    entity_type = request.args.get('entity_type')
    format_type = request.args.get('format', 'html')  # Default to HTML
    
    # Start building the query
    query = AuditLog.query
    
    # Apply filters
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            # Add one day to include the whole end date
            end_date_obj = end_date_obj + timedelta(days=1)
            query = query.filter(AuditLog.timestamp < end_date_obj)
        except ValueError:
            pass
    
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)
    
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    
    # Get list of patients and doctors for filter dropdowns
    patients = Patient.query.join(
        DoctorPatient, Patient.id == DoctorPatient.patient_id
    ).filter(
        DoctorPatient.doctor_id == current_user.id
    ).all()
    
    # For admin users, show all doctors. For regular doctors, only show themselves
    doctors = [current_user]
    
    if action_type:
        # Ottieni i valori delle enum dal database
        try:
            existing_action_types = db.session.query(db.distinct(AuditLog.action_type)).all()
            existing_action_types = [action_type[0].value.upper() for action_type in existing_action_types]
            
            if action_type.upper() in existing_action_types:
                # Mappa diretta dai valori delle stringhe agli enum
                action_map = {
                    'CREATE': ActionType.CREATE,
                    'UPDATE': ActionType.UPDATE,
                    'DELETE': ActionType.DELETE,
                    'VIEW': ActionType.VIEW,
                    'EXPORT': ActionType.EXPORT,
                    'GENERATE_LINK': ActionType.GENERATE_LINK,
                    'CONNECT': ActionType.CONNECT,
                    'DISCONNECT': ActionType.DISCONNECT,
                    'SYNC': ActionType.SYNC
                }
                
                # Filtro solo se esiste nel database
                query = query.filter_by(action_type=action_map[action_type.upper()])
            else:
                # Se il valore non esiste, restituisci un insieme vuoto (nessun risultato)
                # invece di generare un errore
                return render_template(
                    'audit_logs.html',
                    logs=[],
                    patients=patients,
                    doctors=doctors,
                    request=request,
                    current_user=current_user,
                    now=datetime.now()
                )
        except Exception as e:
            # In caso di errore, restituisci un insieme vuoto
            return render_template(
                'audit_logs.html',
                logs=[],
                patients=patients,
                doctors=doctors,
                request=request,
                current_user=current_user,
                now=datetime.now(),
                message=f"Errore durante il filtraggio per azione: {str(e)}"
            )
    
    if entity_type:
        # Ottieni i valori delle enum dal database
        try:
            existing_entity_types = db.session.query(db.distinct(AuditLog.entity_type)).all()
            existing_entity_types = [entity_type[0].value.upper() for entity_type in existing_entity_types]
            
            if entity_type.upper() in existing_entity_types:
                # Mappa diretta dai valori delle stringhe agli enum
                entity_map = {
                    'PATIENT': EntityType.PATIENT,
                    'NOTE': EntityType.NOTE,
                    'REPORT': EntityType.REPORT,
                    'HEALTH_PLATFORM': EntityType.HEALTH_PLATFORM,
                    'HEALTH_LINK': EntityType.HEALTH_LINK,
                    'OBSERVATION': EntityType.OBSERVATION,
                    'VITAL_SIGN': EntityType.VITAL_SIGN
                }
                
                # Filtro solo se esiste nel database
                query = query.filter_by(entity_type=entity_map[entity_type.upper()])
            else:
                # Se il valore non esiste, restituisci un insieme vuoto
                return render_template(
                    'audit_logs.html',
                    logs=[],
                    patients=patients,
                    doctors=doctors,
                    request=request,
                    current_user=current_user,
                    now=datetime.now()
                )
        except Exception as e:
            # In caso di errore, restituisci un insieme vuoto
            return render_template(
                'audit_logs.html',
                logs=[],
                patients=patients,
                doctors=doctors,
                request=request,
                current_user=current_user,
                now=datetime.now(),
                message=f"Errore durante il filtraggio per entità: {str(e)}"
            )
    
    # Get results ordered by timestamp (most recent first)
    logs = query.order_by(AuditLog.timestamp.desc()).all()
    
    # If format is JSON, return JSON response
    if format_type == 'json':
        # Convert to dictionaries for JSON response
        log_list = [log.to_dict() for log in logs]
        
        return jsonify({
            'status': 'success',
            'count': len(log_list),
            'logs': log_list
        })
    
    # Otherwise, render HTML template
    # Get list of patients and doctors for filter dropdowns
    patients = Patient.query.join(
        DoctorPatient, Patient.id == DoctorPatient.patient_id
    ).filter(
        DoctorPatient.doctor_id == current_user.id
    ).all()
    
    # For admin users, show all doctors. For regular doctors, only show themselves
    # Note: this is simplified as we don't have admin roles yet, but preparing for future
    doctors = [current_user]
    
    # In the future, if admin roles are implemented:
    # if current_user.is_admin:
    #     doctors = Doctor.query.all()
    
    # Render the audit logs template
    return render_template(
        'audit_logs.html',
        logs=[log.to_dict() for log in logs],  # log.to_dict() already includes doctor_name and patient_name
        patients=patients,
        doctors=doctors,
        request=request,
        current_user=current_user,
        now=datetime.now()
    )

@audit_bp.route('/logs/stats', methods=['GET'])
@login_required
@doctor_required
def get_audit_stats():
    """
    Get statistics from audit logs, such as:
    - Total number of actions by type
    - Actions per doctor
    - Most accessed patients
    - Activity timeline
    """
    # Time period filter
    days = request.args.get('days', default=30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Base query for the time period
    base_query = AuditLog.query.filter(AuditLog.timestamp >= start_date)
      # Count actions by type
    action_stats = []
    # Get only the action types that exist in the database to avoid InvalidTextRepresentation errors
    existing_action_types = db.session.query(db.distinct(AuditLog.action_type)).all()
    existing_action_types = [action_type[0] for action_type in existing_action_types]
    
    for action_type in existing_action_types:
        count = base_query.filter_by(action_type=action_type).count()
        if count > 0:
            # Se action_type è già una stringa, usarla direttamente
            # altrimenti se è un enum, accedere alla proprietà value
            action_type_value = action_type
            if hasattr(action_type, 'value'):
                action_type_value = action_type.value
                
            action_stats.append({
                'type': action_type_value,
                'count': count
            })
    
    # Count actions by entity type
    entity_stats = []
    # Same approach for entity types
    existing_entity_types = db.session.query(db.distinct(AuditLog.entity_type)).all()
    existing_entity_types = [entity_type[0] for entity_type in existing_entity_types]
    
    for entity_type in existing_entity_types:
        count = base_query.filter_by(entity_type=entity_type).count()
        if count > 0:
            # Se entity_type è già una stringa, usarla direttamente
            # altrimenti se è un enum, accedere alla proprietà value
            entity_type_value = entity_type
            if hasattr(entity_type, 'value'):
                entity_type_value = entity_type.value
                
            entity_stats.append({
                'type': entity_type_value,
                'count': count
            })
    
    # Top doctors by activity
    doctor_stats = db.session.query(
        AuditLog.doctor_id,
        Doctor.first_name,
        Doctor.last_name,
        db.func.count(AuditLog.id).label('action_count')
    ).join(Doctor).filter(
        AuditLog.timestamp >= start_date
    ).group_by(
        AuditLog.doctor_id,
        Doctor.first_name,
        Doctor.last_name
    ).order_by(
        db.desc('action_count')
    ).limit(5).all()
    
    doctor_activity = [{
        'doctor_id': doctor_id,
        'name': f"{first_name} {last_name}",
        'action_count': action_count
    } for doctor_id, first_name, last_name, action_count in doctor_stats]
    
    # Most accessed patients
    patient_stats = db.session.query(
        AuditLog.patient_id,
        Patient.first_name,
        Patient.last_name,
        db.func.count(AuditLog.id).label('access_count')
    ).join(Patient).filter(
        AuditLog.timestamp >= start_date,
        AuditLog.patient_id != None  # Equivalent to "is not None"
    ).group_by(
        AuditLog.patient_id,
        Patient.first_name,
        Patient.last_name
    ).order_by(
        db.desc('access_count')
    ).limit(5).all()
    
    patient_activity = [{
        'patient_id': patient_id,
        'name': f"{first_name} {last_name}",
        'access_count': access_count
    } for patient_id, first_name, last_name, access_count in patient_stats]
    
    # Activity timeline (actions per day)
    timeline_days = min(days, 30)  # Limit to 30 days for timeline
    timeline_start = datetime.utcnow() - timedelta(days=timeline_days)
    
    # Generate date labels for the past N days
    date_labels = [(timeline_start + timedelta(days=i)).strftime('%Y-%m-%d') 
                  for i in range(timeline_days + 1)]
    
    # Initialize counts with zeros
    date_counts = {date: 0 for date in date_labels}
    
    # Query actions grouped by date
    timeline_data = db.session.query(
        db.func.date(AuditLog.timestamp).label('date'),
        db.func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= timeline_start
    ).group_by(
        'date'
    ).all()
      # Fill in the actual counts
    for date_str, count in timeline_data:
        # Se date_str è già una stringa, usarla direttamente
        # altrimenti, se è un oggetto datetime, formattarlo come stringa
        if isinstance(date_str, str):
            date_key = date_str
        else:
            date_key = date_str.strftime('%Y-%m-%d')
            
        if date_key in date_counts:
            date_counts[date_key] = count
    
    # Format for chart display
    timeline = {
        'labels': date_labels,
        'counts': [date_counts[date] for date in date_labels]
    }
    
    return jsonify({
        'status': 'success',
        'period_days': days,
        'action_stats': action_stats,
        'entity_stats': entity_stats,
        'doctor_activity': doctor_activity,
        'patient_activity': patient_activity,
        'timeline': timeline
    })

# Convenience functions to use throughout the application

def log_patient_creation(doctor_id, patient):
    """Log patient creation."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.CREATE,
        entity_type=EntityType.PATIENT,
        entity_id=patient.id,
        details=patient.to_dict(),
        patient_id=patient.id
    )

def log_patient_update(doctor_id, patient, old_data):
    """Log patient update."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.UPDATE,
        entity_type=EntityType.PATIENT,
        entity_id=patient.id,
        details={
            'old': old_data,
            'new': patient.to_dict()
        },
        patient_id=patient.id
    )

def log_patient_delete(doctor_id, patient):
    """Log patient deletion."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.DELETE,
        entity_type=EntityType.PATIENT,
        entity_id=patient.id,
        details=patient.to_dict(),
        patient_id=patient.id
    )

def log_vital_creation(doctor_id, vital):
    """Log vital sign creation."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.CREATE,
        entity_type=EntityType.VITAL_SIGN,
        entity_id=vital.id,
        details=vital.to_dict(),
        patient_id=vital.patient_id
    )

def log_note_creation(doctor_id, note):
    """Log note creation."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.CREATE,
        entity_type=EntityType.NOTE,
        entity_id=note.id,
        details=note.to_dict(),
        patient_id=note.patient_id
    )

def log_report_generation(doctor_id, patient_id, report_type, params=None):
    """Log report generation."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.EXPORT,
        entity_type=EntityType.REPORT,
        entity_id=0,  # Reports don't have IDs, using 0 as placeholder
        details={
            'report_type': report_type,
            'params': params or {}
        },
        patient_id=patient_id
    )

def log_patient_view(doctor_id, patient_id):
    """Log patient view."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.VIEW,
        entity_type=EntityType.PATIENT,
        entity_id=patient_id,
        patient_id=patient_id
    )

def log_health_link_creation(doctor_id, link):
    """Log health platform link creation."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.GENERATE_LINK,
        entity_type=EntityType.HEALTH_LINK,
        entity_id=link.id,
        details={
            'platform': link.platform.value,
            'expires_at': link.expires_at.isoformat() if link.expires_at else None
        },
        patient_id=link.patient_id
    )

def log_platform_connection(doctor_id, patient, platform_name):
    """Log health platform connection."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.CONNECT,
        entity_type=EntityType.HEALTH_PLATFORM,
        entity_id=0,  # Using 0 as placeholder since platform doesn't have an ID
        details={
            'platform': platform_name,
            'connected_at': datetime.utcnow().isoformat()
        },
        patient_id=patient.id
    )

def log_platform_disconnection(doctor_id, patient, platform_name):
    """Log health platform disconnection."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.DISCONNECT,
        entity_type=EntityType.HEALTH_PLATFORM,
        entity_id=0,  # Using 0 as placeholder since platform doesn't have an ID
        details={
            'platform': platform_name,
            'disconnected_at': datetime.utcnow().isoformat()
        },
        patient_id=patient.id
    )

def log_data_sync(doctor_id, patient, platform_name, data_type, result_summary):
    """Log health platform data synchronization."""
    try:
        # Utilizziamo ActionType("sync") per assicurarci di usare il valore minuscolo
        sync_action = ActionType.SYNC
        return log_action(
            doctor_id=doctor_id,
            action_type=sync_action,
            entity_type=EntityType.HEALTH_PLATFORM,
            entity_id=0,  # Using 0 as placeholder since sync doesn't have an ID
            details={
                'platform': platform_name,
                'data_type': data_type,
                'sync_at': datetime.utcnow().isoformat(),
                'result': result_summary
            },
            patient_id=patient.id
        )
    except Exception as e:
        logger.error(f"Error logging data sync: {str(e)}")
        return None
    
def log_observation_creation(doctor_id, observation):
    """Log observation creation."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.CREATE,
        entity_type=EntityType.OBSERVATION,
        entity_id=observation.id,
        details={
            'vital_type': observation.vital_type.value,
            'content': observation.content[:100] + ('...' if len(observation.content) > 100 else ''),
            'period': f"{observation.start_date.isoformat()} to {observation.end_date.isoformat()}",
            'created_at': observation.created_at.isoformat() if observation.created_at else None,
        },
        patient_id=observation.patient_id
    )
    
def log_observation_update(doctor_id, observation, old_data=None):
    """Log observation update."""
    details = {
        'vital_type': observation.vital_type.value,
        'content': observation.content[:100] + ('...' if len(observation.content) > 100 else ''),
        'period': f"{observation.start_date.isoformat()} to {observation.end_date.isoformat()}",
        'updated_at': observation.updated_at.isoformat() if observation.updated_at else None,
    }
    
    # Add previous state information if provided
    if old_data:
        details['previous'] = old_data
        
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.UPDATE,
        entity_type=EntityType.OBSERVATION,
        entity_id=observation.id,
        details=details,
        patient_id=observation.patient_id
    )
    
def log_observation_delete(doctor_id, observation):
    """Log observation deletion."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.DELETE,
        entity_type=EntityType.OBSERVATION,
        entity_id=observation.id,
        details={
            'vital_type': observation.vital_type.value,
            'content': observation.content[:100] + ('...' if len(observation.content) > 100 else ''),
            'period': f"{observation.start_date.isoformat()} to {observation.end_date.isoformat()}",
            'deleted_at': datetime.utcnow().isoformat(),
        },
        patient_id=observation.patient_id
    )
    
def log_note_delete(doctor_id, note):
    """Log note deletion."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.DELETE,
        entity_type=EntityType.NOTE,
        entity_id=note.id,
        details={
            'content': note.content[:100] + ('...' if len(note.content) > 100 else ''),
            'deleted_at': datetime.utcnow().isoformat(),
        },
        patient_id=note.patient_id
    )

def log_patient_import(doctor_id, patient):
    """Log patient import."""
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.IMPORT,
        entity_type=EntityType.PATIENT,
        entity_id=patient.id,
        details={
            'patient_uuid': patient.uuid,
            'patient_name': f"{patient.first_name} {patient.last_name}",
            'patient_dob': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            'imported_at': datetime.utcnow().isoformat(),
        },
        patient_id=patient.id
    )