"""
Audit Logging Module.

This module provides functionality for tracking and logging user actions in the system.
It includes routes for viewing audit logs and utility functions for recording various
types of actions (patient creation, updates, deletions, report generation, etc.).

The audit system helps maintain a complete history of all changes made in the application,
which is essential for healthcare applications that require high levels of data integrity
and traceability.
"""

from datetime import datetime, timedelta
import logging
from flask import request, jsonify, Blueprint, render_template
from flask_login import current_user, login_required
from flask_babel import _

from .models import (AuditLog, ActionType, EntityType, Doctor, Patient, DoctorPatient)
from .app import db
from .auth import doctor_required

# Initialize logger
logger = logging.getLogger(__name__)
"""
Logger instance for the audit module.

This logger is used throughout the audit module to record application-level
logs related to audit operations, particularly focusing on error conditions
during audit logging operations.
"""

audit_bp = Blueprint('audit', __name__)
"""
Flask Blueprint for audit-related routes.

This Blueprint defines routes for viewing and accessing audit logs,
providing functionality for tracking and monitoring user actions
within the VitaLink application.
"""

@audit_bp.route('/audit-logs')
@login_required
@doctor_required
def view_logs():
    """
    View all audit logs for the current doctor.
    
    This route handler renders a page displaying all audit logs associated with the currently
    logged-in doctor, ordered by timestamp (most recent first). The audit logs provide
    a comprehensive history of all actions performed by the doctor within the system.
    
    Decorators:
        login_required: Ensures that only authenticated users can access this route
        doctor_required: Ensures that only users with doctor role can access this route
    
    Returns:
        Response: Rendered HTML page containing all audit logs for the current doctor
    """
    # Get all audit logs for the current doctor, ordered by timestamp (most recent first)
    logs = AuditLog.query.filter_by(doctor_id=current_user.id).order_by(
        AuditLog.timestamp.desc()
    ).all()
    
    return render_template('audit_logs.html', logs=logs)

def log_action(doctor_id, action_type, entity_type, entity_id, details=None, patient_id=None):
    """
    Create a new audit log entry in the system.
    
    This is the core function of the audit system that records all actions performed
    within the VitaLink application. It captures who performed an action (doctor),
    what action was performed, which entity was affected, when it happened, and 
    additional contextual information.
    
    Args:
        doctor_id (int): ID of the doctor who performed the action
        action_type (ActionType): Type of action performed (CREATE, UPDATE, DELETE, VIEW, etc.)
        entity_type (EntityType): Type of entity affected (PATIENT, NOTE, REPORT, etc.)
        entity_id (int): ID of the entity affected by the action
        details (dict, optional): Additional details about the action in dictionary format,
                                 useful for storing contextual information
        patient_id (int, optional): ID of the patient related to the action (for easier querying)
                                   and for organizing logs by patient
    
    Returns:
        AuditLog: The created audit log entry object or None if an error occurs during creation
    
    Note:
        - The function automatically captures the IP address of the request if available
        - If entity_id is None, it will use a temporary default value (0)
        - Any exceptions during log creation are caught to prevent disruption to the main application flow
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
    
    This endpoint retrieves audit logs based on provided filter criteria and returns
    them either as HTML or JSON depending on the requested format. It provides a 
    comprehensive search and filtering system for audit trails.
    
    Supports filtering by:
        - Date range (start_date, end_date)
        - Doctor (doctor_id)
        - Patient (patient_id)
        - Action type (create, update, delete, etc.)
        - Entity type (patient, note, report, etc.)
    
    Args (from request.args):
        start_date (str, optional): Start date for filtering logs (format: YYYY-MM-DD)
        end_date (str, optional): End date for filtering logs (format: YYYY-MM-DD)
        doctor_id (str, optional): ID of doctor whose actions should be included
        patient_id (str, optional): ID of patient whose records were affected
        action_type (str, optional): Type of action to filter by
        entity_type (str, optional): Type of entity to filter by
        format (str, optional): Response format, either 'html' (default) or 'json'
    
    Returns:
        Response: Either a rendered HTML template with filtered logs or a JSON response
                 containing the filtered logs, depending on the format parameter
    
    Decorators:
        login_required: Ensures that only authenticated users can access this endpoint
        doctor_required: Ensures that only users with doctor role can access this endpoint
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
                message=_("Error during action filtering: %(error)s") % {"error": str(e)}
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
            # In case of error, return an empty set
            return render_template(
                'audit_logs.html',
                logs=[],
                patients=patients,
                doctors=doctors,
                request=request,
                current_user=current_user,
                now=datetime.now(),
                message=_("Error during entity filtering: %(error)s") % {"error": str(e)}
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
    Get comprehensive statistics derived from audit logs.
    
    This endpoint analyzes audit log data and generates various statistical insights
    that can be used for monitoring system usage, identifying patterns, and ensuring
    compliance with usage policies.
    
    Statistics generated include:
        - Total number of actions by type (create, update, delete, etc.)
        - Actions by entity type (patient, note, report, etc.)
        - Top doctors by activity level
        - Most accessed patients
        - Activity timeline showing actions per day
    
    Args (from request.args):
        days (int, optional): Number of days to include in the statistics (default: 30)
    
    Returns:
        Response: JSON response containing the various statistics categories
        
    Decorators:
        login_required: Ensures that only authenticated users can access this endpoint
        doctor_required: Ensures that only users with doctor role can access this endpoint
    
    Note:
        The timeline is limited to a maximum of 30 days regardless of the days parameter
        to ensure reasonable response size and performance.
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
    """
    Log the creation of a new patient record.
    
    This convenience function creates an audit log entry when a doctor creates
    a new patient record in the system.
    
    Args:
        doctor_id (int): ID of the doctor who created the patient
        patient (Patient): The Patient object that was created
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
    
    Note:
        This function uses log_action internally, setting appropriate action_type
        and entity_type values for patient creation events.
    """
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.CREATE,
        entity_type=EntityType.PATIENT,
        entity_id=patient.id,
        details=patient.to_dict(),
        patient_id=patient.id
    )

def log_patient_update(doctor_id, patient, old_data):
    """
    Log the update of an existing patient record.
    
    This convenience function creates an audit log entry when a doctor updates
    information in a patient record, storing both the previous and new states.
    
    Args:
        doctor_id (int): ID of the doctor who updated the patient record
        patient (Patient): The Patient object with updated information
        old_data (dict): Dictionary containing the patient's data before the update
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        The details field of the audit log contains both 'old' and 'new' states
        for comparison and historical tracking purposes.
    """
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
    """
    Log the deletion of a patient record.
    
    This convenience function creates an audit log entry when a doctor deletes
    a patient record from the system, preserving the patient information for
    audit purposes even after deletion.
    
    Args:
        doctor_id (int): ID of the doctor who deleted the patient record
        patient (Patient): The Patient object being deleted
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        The complete patient data is stored in the details field to maintain
        a record of the deleted information for compliance and audit purposes.
    """
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.DELETE,
        entity_type=EntityType.PATIENT,
        entity_id=patient.id,
        details=patient.to_dict(),
        patient_id=patient.id
    )

def log_vital_creation(doctor_id, vital):
    """
    Log the creation of a vital sign record.
    
    This convenience function creates an audit log entry when a doctor or system
    adds a new vital sign measurement to a patient's record.
    
    Args:
        doctor_id (int): ID of the doctor who created the vital sign record
        vital (VitalSign): The VitalSign object that was created
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        The patient_id is automatically extracted from the vital sign object
        to enable filtering audit logs by patient.
    """
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.CREATE,
        entity_type=EntityType.VITAL_SIGN,
        entity_id=vital.id,
        details=vital.to_dict(),
        patient_id=vital.patient_id
    )

def log_note_creation(doctor_id, note):
    """
    Log the creation of a clinical note.
    
    This convenience function creates an audit log entry when a doctor adds
    a new clinical note to a patient's medical record.
    
    Args:
        doctor_id (int): ID of the doctor who created the note
        note (Note): The Note object that was created
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        Clinical notes are important medical record entries that may contain
        observations, assessments, and treatment plans. Their creation is
        tracked for medical and legal compliance purposes.
    """
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.CREATE,
        entity_type=EntityType.NOTE,
        entity_id=note.id,
        details=note.to_dict(),
        patient_id=note.patient_id
    )

def log_report_generation(doctor_id, patient_id, report_type, params=None):
    """
    Log the generation of a medical report.
    
    This convenience function creates an audit log entry when a doctor generates
    a report from patient data, such as a vital signs summary, progress report,
    or other clinical document.
    
    Args:
        doctor_id (int): ID of the doctor who generated the report
        patient_id (int): ID of the patient the report is about
        report_type (str): Type or name of the report being generated
        params (dict, optional): Parameters used for report generation such as
                               date ranges, included data types, etc.
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        Since reports don't have persistent IDs in the database, a placeholder
        value of 0 is used for the entity_id.
    """
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
    """
    Log when a doctor views a patient's record.
    
    This convenience function creates an audit log entry when a doctor accesses
    or views a patient's medical record. This is important for privacy compliance
    and access tracking in healthcare systems.
    
    Args:
        doctor_id (int): ID of the doctor who viewed the patient record
        patient_id (int): ID of the patient whose record was viewed
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        Patient record viewing is tracked separately from other operations as
        it's a common compliance requirement in healthcare systems to monitor
        who has accessed patient information.
    """
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.VIEW,
        entity_type=EntityType.PATIENT,
        entity_id=patient_id,
        patient_id=patient_id
    )

def log_health_link_creation(doctor_id, link):
    """
    Log the creation of a health platform connection link.
    
    This convenience function creates an audit log entry when a doctor generates
    a link that allows a patient to connect their external health platform 
    (like Fitbit, Apple Health, etc.) to the VitaLink system.
    
    Args:
        doctor_id (int): ID of the doctor who generated the link
        link (HealthPlatformLink): The HealthPlatformLink object that was created
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        The details field includes information about the platform type and
        link expiration date for tracking purposes.
    """    # Gestione sia di enum HealthPlatform che di stringhe
    if hasattr(link.platform, 'value'):
        platform_value = link.platform.value
    else:
        platform_value = link.platform
        
    return log_action(
        doctor_id=doctor_id,
        action_type=ActionType.GENERATE_LINK,
        entity_type=EntityType.HEALTH_LINK,
        entity_id=link.id,
        details={
            'platform': platform_value,
            'expires_at': link.expires_at.isoformat() if link.expires_at else None
        },
        patient_id=link.patient_id
    )

def log_platform_connection(doctor_id, patient, platform_name):
    """
    Log when a patient connects an external health platform to VitaLink.
    
    This convenience function creates an audit log entry when a patient successfully
    connects their external health platform account (like Fitbit, Google Fit, etc.)
    to the VitaLink system, enabling data sharing.
    
    Args:
        doctor_id (int): ID of the doctor who initiated or supervised the connection
        patient (Patient): The Patient object whose account is being connected
        platform_name (str): Name of the external health platform being connected
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        Since platforms don't have distinct IDs in the system, a placeholder
        value of 0 is used for the entity_id.
    """
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
    """
    Log when a patient disconnects an external health platform from VitaLink.
    
    This convenience function creates an audit log entry when a patient or doctor
    disconnects an external health platform account from the VitaLink system,
    stopping the data sharing between systems.
    
    Args:
        doctor_id (int): ID of the doctor who initiated or supervised the disconnection
        patient (Patient): The Patient object whose account is being disconnected
        platform_name (str): Name of the external health platform being disconnected
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        The disconnection timestamp is stored in the details field for future reference.
    """
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
    """
    Log the synchronization of data from an external health platform.
    
    This convenience function creates an audit log entry when data is synchronized
    from an external health platform (like Fitbit, Apple Health, etc.) into the 
    VitaLink system. The log includes details about what was synchronized and the result.
    
    Args:
        doctor_id (int): ID of the doctor who initiated the data synchronization
        patient (Patient): The Patient object whose data is being synchronized
        platform_name (str): Name of the external health platform being synchronized with
        data_type (str): Type of data being synchronized (e.g., 'heart_rate', 'steps', etc.)
        result_summary (dict): Summary of the synchronization results (e.g., number of records, success status)
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        This function includes specific error handling to prevent sync failures
        from disrupting the application flow, as data synchronization is an
        auxiliary function to the core medical record system.
    """
    try:
        # Use ActionType.SYNC directly instead of trying to convert a string
        return log_action(
            doctor_id=doctor_id,
            action_type=ActionType.SYNC,
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
    """
    Log the creation of a clinical observation.
    
    This convenience function creates an audit log entry when a doctor adds
    a new clinical observation to a patient's record. Observations are structured
    medical assessments related to specific vital signs or health metrics.
    
    Args:
        doctor_id (int): ID of the doctor who created the observation
        observation (Observation): The Observation object that was created
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        The details field includes a truncated version of the observation content
        if it's lengthy, as well as the vital sign type and relevant dates.
    """
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
    """
    Log the update of an existing clinical observation.
    
    This convenience function creates an audit log entry when a doctor modifies
    an existing clinical observation in a patient's record. This tracks changes
    made to clinical assessments over time.
    
    Args:
        doctor_id (int): ID of the doctor who updated the observation
        observation (Observation): The updated Observation object
        old_data (dict, optional): The previous state of the observation before updates
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        If old_data is provided, it is included in the details for comparison,
        allowing for tracking of specific changes made to the observation.
    """
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
    """
    Log the deletion of a clinical observation.
    
    This convenience function creates an audit log entry when a doctor deletes
    a clinical observation from a patient's record. This ensures that even deleted
    observations leave an audit trail for compliance purposes.
    
    Args:
        doctor_id (int): ID of the doctor who deleted the observation
        observation (Observation): The Observation object being deleted
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        Key information about the deleted observation is preserved in the
        audit log details, including a truncated version of the content, 
        the vital type, and the time period it covered.
    """
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
    """
    Log the deletion of a clinical note.
    
    This convenience function creates an audit log entry when a doctor deletes
    a clinical note from a patient's record. This preserves a record of the
    deletion action for compliance and audit purposes.
    
    Args:
        doctor_id (int): ID of the doctor who deleted the note
        note (Note): The Note object being deleted
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        A truncated version of the note content is preserved in the audit log
        details to maintain context about what was deleted, while the exact
        deletion time is also recorded.
    """
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
    """
    Log the import of a patient record from an external source.
    
    This convenience function creates an audit log entry when a doctor imports
    a patient record from another system or data source into VitaLink.
    
    Args:
        doctor_id (int): ID of the doctor who performed the import
        patient (Patient): The Patient object that was imported
    
    Returns:
        AuditLog: The created audit log entry or None if an error occurs
        
    Note:
        The details field captures key identifiers including the patient's UUID,
        which is particularly important for tracking imported records that
        originated from external systems.
    """
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