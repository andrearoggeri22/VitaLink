import logging
from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from app import db
from models import Patient, VitalSign, VitalSignType, DataOrigin, Note
from auth import doctor_required
from utils import validate_uuid

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
        return jsonify({"error": "Invalid UUID format"}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": "You are not authorized to access this patient"}), 403
    
    return jsonify({
        "patient": patient.to_dict()
    }), 200

@api_bp.route('/patients/<string:patient_uuid>/vitals', methods=['GET'])
@doctor_required
def get_vitals(doctor, patient_uuid):
    """Get vital signs for a specific patient."""
    # Validate UUID format
    if not validate_uuid(patient_uuid):
        return jsonify({"error": "Invalid UUID format"}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": "You are not authorized to access this patient"}), 403
    
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
        return jsonify({"error": "Invalid UUID format"}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": "You are not authorized to access this patient"}), 403
    
    # Validate request data
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    
    required_fields = ['type', 'value']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Validate vital sign type
    try:
        vital_type = VitalSignType(data['type'])
    except ValueError:
        return jsonify({
            "error": f"Invalid vital sign type. Must be one of: {[t.value for t in VitalSignType]}"
        }), 400
    
    # Validate value
    try:
        value = float(data['value'])
    except ValueError:
        return jsonify({"error": "Value must be a number"}), 400
    
    # Get optional fields
    unit = data.get('unit')
    
    # Get recorded_at or use current time
    recorded_at = data.get('recorded_at')
    if recorded_at:
        try:
            recorded_datetime = datetime.fromisoformat(recorded_at.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
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
        
        return jsonify({
            "message": "Vital sign recorded successfully",
            "vital": vital.to_dict()
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error adding vital sign: {str(e)}")
        return jsonify({"error": "An error occurred while recording the vital sign"}), 500

@api_bp.route('/patients/<string:patient_uuid>/notes', methods=['GET'])
@doctor_required
def get_notes(doctor, patient_uuid):
    """Get notes for a specific patient."""
    # Validate UUID format
    if not validate_uuid(patient_uuid):
        return jsonify({"error": "Invalid UUID format"}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": "You are not authorized to access this patient"}), 403
    
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
        return jsonify({"error": "Invalid UUID format"}), 400
    
    # Find the patient
    patient = Patient.query.filter_by(uuid=patient_uuid).first()
    
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": "You are not authorized to access this patient"}), 403
    
    # Validate request data
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    
    if 'content' not in data or not data['content']:
        return jsonify({"error": "Note content cannot be empty"}), 400
    
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
            "message": "Note added successfully",
            "note": note.to_dict()
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error adding note: {str(e)}")
        return jsonify({"error": "An error occurred while adding the note"}), 500
