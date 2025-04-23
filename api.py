import logging
from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from flask_babel import gettext as _
from app import db
from models import Patient, VitalSign, VitalSignType, DataOrigin, Note, VitalObservation
from auth import api_doctor_required as doctor_required
from utils import validate_uuid, is_vital_in_range, get_vital_sign_unit
from notifications import notify_abnormal_vital

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.route('/patients', methods=['GET'])
@doctor_required
def get_patients(doctor):
    """Get all patients for the authenticated doctor."""
    patients = doctor.patients.all()
    return jsonify({
        "patients": [patient.to_dict() for patient in patients]
    }), 200

@api_bp.route('/patients/<string:patient_uuid>', methods=['GET'])
@doctor_required
def get_patient(doctor, patient_uuid):
    """Get a specific patient by UUID."""
    # Validate UUID format
    if not validate_uuid(patient_uuid):
        return jsonify({"error": _("Invalid UUID format")}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error": _("Patient not found")}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": _("You are not authorized to access this patient")}), 403
    
    return jsonify({
        "patient": patient.to_dict()
    }), 200

@api_bp.route('/patients/<string:patient_uuid>/vitals', methods=['GET'])
@doctor_required
def get_vitals(doctor, patient_uuid):
    """Get vital signs for a specific patient."""
    # Validate UUID format
    if not validate_uuid(patient_uuid):
        return jsonify({"error": _("Invalid UUID format")}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error": _("Patient not found")}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": _("You are not authorized to access this patient")}), 403
    
    # Get query parameters for filtering
    type_param = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Get vital signs
    vitals = patient.get_vital_signs(
        type=type_param,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify({
        "vitals": [vital.to_dict() for vital in vitals]
    }), 200

@api_bp.route('/patients/<string:patient_uuid>/vitals', methods=['POST'])
@doctor_required
def add_vital(doctor, patient_uuid):
    """Add a new vital sign for a patient."""
    # Validate UUID format
    if not validate_uuid(patient_uuid):
        return jsonify({"error": _("Invalid UUID format")}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error": _("Patient not found")}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": _("You are not authorized to access this patient")}), 403
    
    # Validate request data
    if not request.is_json:
        return jsonify({"error": _("Missing JSON in request")}), 400
    
    data = request.json
    
    required_fields = ['type', 'value']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": _("Missing required field: {field}") % {"field": field}}), 400
    
    # Validate vital sign type
    try:
        vital_type = VitalSignType(data['type'])
    except ValueError:
        return jsonify({
            "error": _("Invalid vital sign type. Must be one of: %(types)s") % {
                "types": ", ".join(t.value for t in VitalSignType)
            }
        }), 400
    
    # Validate value
    try:
        value = float(data['value'])
    except ValueError:
        return jsonify({"error": _("Value must be a number")}), 400
    
    # Get optional fields
    unit = data.get('unit')
    
    # Get recorded_at or use current time
    recorded_at = data.get('recorded_at')
    if recorded_at:
        try:
            recorded_datetime = datetime.fromisoformat(recorded_at.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": _("Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")}), 400
    else:
        recorded_datetime = datetime.utcnow()
    
    # Create new vital sign
    try:
        vital = VitalSign(
            patient_id=patient.id,
            type=vital_type,
            value=value,
            unit=unit,
            recorded_at=recorded_datetime,
            origin=DataOrigin.AUTOMATIC
        )
        
        db.session.add(vital)
        db.session.commit()
        
        logger.info(f"Vital sign added for patient {patient_uuid} via API")
        
        # Check if the vital sign is outside normal range and send notification if needed
        vital_value = str(value) if vital_type.value != 'blood_pressure' else value
        is_normal, status = is_vital_in_range(vital_type.value, vital_value)
        
        # If value is abnormal, send notification
        if not is_normal and patient.contact_number:
            if not unit:
                unit = get_vital_sign_unit(vital_type.value)
                
            # Send SMS notification for abnormal vital sign
            success, message = notify_abnormal_vital(
                patient=patient,
                vital_type=vital_type.value,
                value=vital_value,
                unit=unit,
                status=status
            )
            
            if success:
                logger.info(f"Abnormal vital notification sent to patient {patient_uuid}")
            else:
                logger.warning(f"Failed to send vital notification to patient {patient_uuid}: {message}")
        
        # Return response with notification status
        response = {
            "message": _("Vital sign recorded successfully"),
            "vital": vital.to_dict(),
            "is_normal": is_normal
        }
        
        if not is_normal:
            response["status"] = status
            if patient.contact_number:
                response["notification_sent"] = True
            else:
                response["notification_sent"] = False
                response["notification_message"] = _("Patient has no contact number for notifications")
        
        return jsonify(response), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error adding vital sign: {str(e)}")
        return jsonify({"error": _("An error occurred while recording the vital sign")}), 500

@api_bp.route('/patients/<string:patient_uuid>/notes', methods=['GET'])
@doctor_required
def get_notes(doctor, patient_uuid):
    """Get notes for a specific patient."""
    # Validate UUID format
    if not validate_uuid(patient_uuid):
        return jsonify({"error": _("Invalid UUID format")}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error":_("Patient not found")}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": _("You are not authorized to access this patient")}), 403
    
    # Get notes
    notes = patient.get_notes()
    
    return jsonify({
        "notes": [note.to_dict() for note in notes]
    }), 200

@api_bp.route('/patients/<string:patient_uuid>/notes', methods=['POST'])
@doctor_required
def add_note(doctor, patient_uuid):
    """Add a new note for a patient."""
    # Validate UUID format
    if not validate_uuid(patient_uuid):
        return jsonify({"error": _("Invalid UUID format")}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error": _("Patient not found")}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": _("You are not authorized to access this patient")}), 403
    
    # Validate request data
    if not request.is_json:
        return jsonify({"error": _("Missing JSON in request")}), 400
    
    data = request.json
    
    if 'content' not in data or not data['content']:
        return jsonify({"error": _("Note content cannot be empty")}), 400
    
    content = data['content']
    
    # Create new note
    try:
        note = Note(
            patient_id=patient.id,
            doctor_id=doctor.id,
            content=content
        )
        
        db.session.add(note)
        db.session.commit()
        
        logger.info(f"Note added for patient {patient_uuid} via API")
        
        return jsonify({
            "message": _("Note added successfully"),
            "note": note.to_dict()
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error adding note: {str(e)}")
        return jsonify({"error": _("An error occurred while adding the note")}), 500

@api_bp.route('/observations/<int:patient_id>', methods=['GET'])
@doctor_required
def get_observations(doctor, patient_id):
    """Get observations for the specified patient and time period."""
    # Find the patient
    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({"error": _("Patient not found")}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": _("You are not authorized to access this patient")}), 403
    
    # Get query parameters for filtering
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    vital_type = request.args.get('vital_type')
    
    # Create query
    query = VitalObservation.query.filter_by(patient_id=patient_id)
    
    # Apply filters
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            query = query.filter(VitalObservation.start_date >= start_date)
        except ValueError:
            return jsonify({"error": _("Invalid start_date format. Use ISO format (YYYY-MM-DD)")}), 400
    
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            query = query.filter(VitalObservation.end_date <= end_date)
        except ValueError:
            return jsonify({"error": _("Invalid end_date format. Use ISO format (YYYY-MM-DD)")}), 400
    
    if vital_type:
        try:
            vital_type_enum = VitalSignType(vital_type)
            query = query.filter_by(vital_type=vital_type_enum)
        except ValueError:
            return jsonify({
                "error": _("Invalid vital sign type. Must be one of: %(types)s") % {
                    "types": ", ".join(t.value for t in VitalSignType)
                }
            }), 400
    
    # Execute query
    observations = query.order_by(VitalObservation.created_at.desc()).all()
    
    return jsonify([obs.to_dict() for obs in observations]), 200

@api_bp.route('/observations', methods=['POST'])
@doctor_required
def add_observation(doctor):
    """Add a new observation."""
    # Validate request data
    if not request.is_json:
        return jsonify({"error": _("Missing JSON in request")}), 400
    
    data = request.json
    
    # Validate required fields
    required_fields = ['patient_id', 'vital_type', 'content', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": _("Missing required field: {field}") % {"field": field}}), 400
    
    # Find the patient
    patient_id = data['patient_id']
    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({"error": _("Patient not found")}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": _("You are not authorized to access this patient")}), 403
    
    # Validate vital type
    try:
        logger.debug(f"Input vital_type: {data['vital_type']}")
        logger.debug(f"Available VitalSignTypes: {[t.value for t in VitalSignType]}")
        vital_type = VitalSignType(data['vital_type'])
    except ValueError as e:
        logger.error(f"Invalid vital sign type: {data['vital_type']}, error: {str(e)}")
        return jsonify({
            "error": _("Invalid vital sign type. Must be one of: %(types)s") % {
                "types": ", ".join(t.value for t in VitalSignType)
            }
        }), 400
    
    # Parse dates
    try:
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": _("Invalid start_date format. Use ISO format (YYYY-MM-DD)")}), 400
    
    try:
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": _("Invalid end_date format. Use ISO format (YYYY-MM-DD)")}), 400
    
    # Validate that start date is before end date
    if start_date >= end_date:
        return jsonify({"error": _("Start date must be before end date")}), 400
    
    # Create the observation
    try:
        observation = VitalObservation(
            patient_id=patient_id,
            doctor_id=doctor.id,
            vital_type=vital_type,
            content=data['content'],
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(observation)
        db.session.commit()
        
        logger.info(f"Observation added for patient {patient_id} by doctor {doctor.id}")
        
        return jsonify({
            "message": _("Observation added successfully"),
            "observation": observation.to_dict()
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error adding observation: {str(e)}")
        return jsonify({"error": _("An error occurred while adding the observation")}), 500

@api_bp.route('/observations/<int:observation_id>', methods=['PUT'])
@doctor_required
def update_observation(doctor, observation_id):
    """Update an existing observation."""
    # Find the observation
    observation = VitalObservation.query.get(observation_id)
    
    if not observation:
        return jsonify({"error": _("Observation not found")}), 404
    
    # Check if the doctor is the creator of the observation
    if observation.doctor_id != doctor.id:
        return jsonify({"error": _("You are not authorized to modify this observation")}), 403
    
    # Validate request data
    if not request.is_json:
        return jsonify({"error": _("Missing JSON in request")}), 400
    
    data = request.json
    
    # Update vital type if provided
    if 'vital_type' in data:
        try:
            observation.vital_type = VitalSignType(data['vital_type'])
        except ValueError:
            return jsonify({
                "error": _("Invalid vital sign type. Must be one of: %(types)s") % {
                    "types": ", ".join(t.value for t in VitalSignType)
                }
            }), 400
    
    # Update content if provided
    if 'content' in data:
        observation.content = data['content']
    
    # Update start date if provided
    if 'start_date' in data:
        try:
            observation.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": _("Invalid start_date format. Use ISO format (YYYY-MM-DD)")}), 400
    
    # Update end date if provided
    if 'end_date' in data:
        try:
            observation.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": _("Invalid end_date format. Use ISO format (YYYY-MM-DD)")}), 400
    
    # Validate that start date is before end date
    if observation.start_date >= observation.end_date:
        return jsonify({"error": _("Start date must be before end date")}), 400
    
    # Save changes
    try:
        observation.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Observation {observation_id} updated by doctor {doctor.id}")
        
        return jsonify({
            "message": _("Observation updated successfully"),
            "observation": observation.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error updating observation: {str(e)}")
        return jsonify({"error": _("An error occurred while updating the observation")}), 500

@api_bp.route('/observations/<int:observation_id>', methods=['DELETE'])
@doctor_required
def delete_observation(doctor, observation_id):
    """Delete an observation."""
    # Find the observation
    observation = VitalObservation.query.get(observation_id)
    
    if not observation:
        return jsonify({"error": _("Observation not found")}), 404
    
    # Check if the doctor is the creator of the observation
    if observation.doctor_id != doctor.id:
        return jsonify({"error": _("You are not authorized to delete this observation")}), 403
    
    # Delete the observation
    try:
        db.session.delete(observation)
        db.session.commit()
        
        logger.info(f"Observation {observation_id} deleted by doctor {doctor.id}")
        
        return jsonify({
            "message": _("Observation deleted successfully")
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error deleting observation: {str(e)}")
        return jsonify({"error": _("An error occurred while deleting the observation")}), 500
