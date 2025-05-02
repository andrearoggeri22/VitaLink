"""
API Blueprint Module.

This module defines the REST API endpoints for the VitaLink application.
It provides routes for accessing and managing patient data, vital signs,
notes, and observations through authenticated HTTP requests.

The API is designed to be used by:
1. Frontend applications that need to fetch or update data
2. Mobile applications that interface with the VitaLink backend
3. External systems that need to integrate with VitaLink

All endpoints require authentication using JWT tokens, which can be obtained
via the auth module. Every request is validated to ensure the requesting doctor
has proper permissions for the requested resources.

The API follows RESTful principles with consistent error handling and status codes:
- 200: Successful GET, PUT or DELETE
- 201: Successful POST (resource created)
- 400: Bad request (invalid data or parameters)
- 401: Unauthorized (missing or invalid authentication)
- 403: Forbidden (authenticated but lacking permission)
- 404: Resource not found
- 500: Server error

API routes are organized by resource type (patients, notes, observations, etc.)
and include proper audit logging for compliance and traceability.
"""

import logging
from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from flask_babel import gettext as _
from .app import db 
from .models import (Patient, VitalSignType, Note, VitalObservation, DoctorPatient)
from .auth import api_doctor_required as doctor_required
from .utils import validate_uuid
from .audit import log_patient_import

# Blueprint for API routes with a base prefix of /api
api_bp = Blueprint('api', __name__)
# Configure logger for this module
logger = logging.getLogger(__name__)

@api_bp.route('/patients', methods=['GET'])
@doctor_required
def get_patients(doctor):
    """
    Get all patients for the authenticated doctor.
    
    This endpoint returns a list of all patients associated with the
    authenticated doctor, providing basic patient information in a
    serialized format.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        
    Returns:
        JSON response with an array of patient objects
        
    Response format:
        {
            "patients": [
                {
                    "id": 1,
                    "uuid": "123e4567-e89b-12d3-a456-426614174000",
                    "first_name": "John",
                    "last_name": "Doe",
                    ...
                },
                ...
            ]
        }
    """
    patients = doctor.patients.all()
    return jsonify({
        "patients": [patient.to_dict() for patient in patients]
    }), 200

@api_bp.route('/patients/<string:patient_uuid>', methods=['GET'])
@doctor_required
def get_patient(doctor, patient_uuid):
    """
    Get a specific patient by UUID.
    
    This endpoint returns detailed information for a specific patient identified by UUID.
    It includes validation to ensure the doctor has access to the requested patient.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        patient_uuid (str): UUID of the patient to retrieve
        
    Returns:
        JSON response with patient details or error message
        
    Status codes:
        200: Patient found and returned successfully
        400: Invalid UUID format
        403: Doctor not authorized to access this patient
        404: Patient not found
        
    Response format (success):
        {
            "patient": {
                "id": 1,
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "first_name": "John",
                "last_name": "Doe",
                ...
            }
        }
    """
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
    """
    Get vital signs for a specific patient from health platform.
    
    This endpoint retrieves vital sign data from the connected health platform
    (e.g., Fitbit) for a specific patient. It supports filtering by vital sign type
    and date range. The patient must have an active connection to a health platform.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        patient_uuid (str): UUID of the patient
        
    Query parameters:
        type (str): Type of vital sign to retrieve (e.g., 'heart_rate', 'steps')
        start_date (str, optional): Start date for data range in ISO format (YYYY-MM-DD)
        end_date (str, optional): End date for data range in ISO format (YYYY-MM-DD)
        
    Returns:
        JSON response with vital sign data or error message
        
    Status codes:
        200: Data retrieved successfully
        400: Invalid UUID format
        403: Doctor not authorized to access this patient
        404: Patient not found or no health platform connection
        500: Error retrieving data from health platform
        
    Response format (success):
        {
            "heart_rate": [
                {
                    "timestamp": "2023-05-01T14:30:00Z",
                    "value": 72,
                    "unit": "bpm"
                },
                ...
            ]
        }
    """
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
      # Check if patient has health platform connection
    if not patient.platform_access_token:
        return jsonify({"error": _("Patient does not have a health platform connection")}), 404
    
    # Get query parameters for filtering
    type_param = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Import health platform functionality
    from .health_platforms import get_processed_fitbit_data
    
    try:
        # Get data from Fitbit
        data = get_processed_fitbit_data(
            patient,
            type_param,
            start_date=start_date,
            end_date=end_date
        )
        
        if not data:
            return jsonify({type_param: []}), 200
        
        # Return data for the specific vital type
        return jsonify({type_param: data}), 200
    except Exception as e:
        logger.error(f"Error getting data from health platform: {str(e)}")
        return jsonify({'error': _('Failed to retrieve health platform data'), 'message': str(e)}), 500

@api_bp.route('/patients/<string:patient_uuid>/notes', methods=['GET'])
@doctor_required
def get_notes(doctor, patient_uuid):
    """
    Get medical notes for a specific patient.
    
    This endpoint retrieves all medical notes associated with a specific patient.
    Notes are ordered by creation date (most recent first) and include information
    about the doctor who created them.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        patient_uuid (str): UUID of the patient whose notes should be retrieved
        
    Returns:
        JSON response with an array of note objects or error message
        
    Status codes:
        200: Notes retrieved successfully
        400: Invalid UUID format
        403: Doctor not authorized to access this patient
        404: Patient not found
        
    Response format:
        {
            "notes": [
                {
                    "id": 1,
                    "content": "Patient reported improvement in symptoms",
                    "doctor_id": 2,
                    "doctor_name": "Dr. Jane Smith",
                    "created_at": "2023-05-01T14:30:00Z"
                },
                ...
            ]
        }
    """
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
    """
    Add a new medical note for a patient.
    
    This endpoint allows doctors to create a new medical note for a specific patient.
    The note is associated with both the patient and the doctor who created it,
    and includes a timestamp of when it was created.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        patient_uuid (str): UUID of the patient to add a note for
        
    Request body:
        content (str): Text content of the note
        
    Returns:
        JSON response with the created note details or error message
        
    Status codes:
        201: Note created successfully
        400: Invalid UUID format, missing JSON request, or empty content
        403: Doctor not authorized to access this patient
        404: Patient not found
        500: Database error
        
    Response format (success):
        {
            "message": "Note added successfully",
            "note": {
                "id": 123,
                "content": "Patient reported feeling better",
                "doctor_id": 45,
                "patient_id": 67,
                "created_at": "2023-05-01T15:30:00Z"
            }
        }
    """
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
        
        # Log the note creation
        from .audit import log_note_creation
        log_note_creation(doctor.id, note)
        
        logger.info(f"Note added for patient {patient_uuid} via API")
        
        return jsonify({
            "message": _("Note added successfully"),
            "note": note.to_dict()
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error adding note: {str(e)}")
        return jsonify({"error": _("An error occurred while adding the note")}), 500

@api_bp.route('/notes/<int:note_id>', methods=['DELETE'])
@doctor_required
def delete_note(doctor, note_id):
    """
    Delete a medical note by ID.
    
    This endpoint allows doctors to delete a medical note they have previously created.
    Multiple security checks are performed to ensure that only the doctor who created
    the note can delete it, and only for patients they are authorized to access.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        note_id (int): ID of the note to delete
        
    Returns:
        JSON response with success message or error message
        
    Status codes:
        200: Note deleted successfully
        403: Not authorized to delete this note/access this patient
        404: Note or patient not found
        500: Database error
        
    Response format (success):
        {
            "message": "Note deleted successfully",
            "note": {
                "id": 123,
                "content": "Patient reported feeling better",
                "doctor_id": 45,
                "patient_id": 67,
                "created_at": "2023-05-01T15:30:00Z"
            }
        }
    """
    # Find the note
    note = Note.query.get(note_id)
    
    if not note:
        return jsonify({"error": _("Note not found")}), 404
    
    # Find the patient
    patient = Patient.query.get(note.patient_id)
    
    if not patient:
        return jsonify({"error": _("Patient not found")}), 404
    
    # Check if the doctor is associated with this patient
    if patient not in doctor.patients.all():
        return jsonify({"error": _("You are not authorized to access this patient")}), 403
    
    # Check if the doctor is the author of the note
    if note.doctor_id != doctor.id:
        return jsonify({"error": _("You can only delete notes you have created")}), 403
    
    # Delete the note
    try:
        # Log the note deletion
        from .audit import log_note_delete
        log_note_delete(doctor.id, note)
        
        # Store note details for response
        note_dict = note.to_dict()
        patient_uuid = patient.uuid
        
        db.session.delete(note)
        db.session.commit()
        
        logger.info(f"Note {note_id} deleted for patient {patient_uuid} via API")
        
        return jsonify({
            "message": _("Note deleted successfully"),
            "note": note_dict
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error deleting note: {str(e)}")
        return jsonify({"error": _("An error occurred while deleting the note")}), 500

@api_bp.route('/observations/<int:patient_id>', methods=['GET'])
@doctor_required
def get_observations(doctor, patient_id):
    """
    Get vital sign observations for the specified patient.
    
    This endpoint retrieves doctor-created observations about a patient's vital signs
    for a specific time period. Observations can be filtered by date range and vital
    sign type.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        patient_id (int): ID of the patient to get observations for
        
    Query parameters:
        start_date (str, optional): ISO formatted start date to filter observations
        end_date (str, optional): ISO formatted end date to filter observations
        vital_type (str, optional): Type of vital sign to filter by (e.g. 'heart_rate')
        
    Returns:
        JSON response with an array of observation objects or error message
        
    Status codes:
        200: Observations retrieved successfully
        400: Invalid date format or vital sign type
        403: Doctor not authorized to access this patient
        404: Patient not found
        
    Response format:
        [
            {
                "id": 1,
                "patient_id": 42,
                "doctor_id": 5,
                "vital_type": "heart_rate",
                "content": "Heart rate has stabilized after medication change",
                "start_date": "2023-05-01T00:00:00Z",
                "end_date": "2023-05-07T23:59:59Z",
                "created_at": "2023-05-08T10:15:30Z"
            },
            ...
        ]
    """
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
    """
    Add a new vital sign observation for a patient.
    
    This endpoint allows doctors to create a new observation about a patient's vital signs
    for a specific time period. Observations include interpretations and medical notes
    about trends in vital sign data.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        
    Request body:
        patient_id (int): ID of the patient the observation is for
        vital_type (str): Type of vital sign from VitalSignType enum (e.g., 'heart_rate')
        content (str): Doctor's notes and interpretation of the vital sign data
        start_date (str): ISO formatted start date of the observation period
        end_date (str): ISO formatted end date of the observation period
        
    Returns:
        JSON response with the created observation or error message
        
    Status codes:
        201: Observation created successfully
        400: Invalid request data (missing fields, invalid vital type, invalid dates)
        403: Not authorized to create observation for this patient
        404: Patient not found
        500: Database error
        
    Response format (success):
        {
            "message": "Observation added successfully",
            "observation": {
                "id": 123,
                "patient_id": 42,
                "doctor_id": 5,
                "vital_type": "heart_rate",
                "content": "Heart rate has stabilized after medication change",
                "start_date": "2023-05-01T00:00:00Z",
                "end_date": "2023-05-07T23:59:59Z",
                "created_at": "2023-05-08T10:15:30Z"
            }
        }
    """
    # Validate request data
    if not request.is_json:
        return jsonify({"error": _("Missing JSON in request")}), 400
    
    data = request.json
    
    # Validate required fields
    required_fields = ['patient_id', 'vital_type', 'content', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": _("Missing required field: %(field)s") % {"field": field}}), 400
    
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
    """
    Update an existing vital sign observation.
    
    This endpoint allows doctors to modify their previously created observations.
    Only the doctor who created the observation can update it. Any fields provided
    in the request will be updated; omitted fields remain unchanged.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        observation_id (int): ID of the observation to update
        
    Request body:
        vital_type (str, optional): New vital sign type
        content (str, optional): Updated notes or interpretation
        start_date (str, optional): New ISO formatted start date
        end_date (str, optional): New ISO formatted end date
        
    Returns:
        JSON response with the updated observation or error message
        
    Status codes:
        200: Observation updated successfully
        400: Invalid request data (invalid vital type, invalid dates)
        403: Not authorized to modify this observation
        404: Observation not found
        500: Database error
        
    Response format (success):
        {
            "message": "Observation updated successfully",
            "observation": {
                "id": 123,
                "patient_id": 42,
                "doctor_id": 5,
                "vital_type": "heart_rate",
                "content": "Updated interpretation of heart rate trends",
                "start_date": "2023-05-01T00:00:00Z",
                "end_date": "2023-05-07T23:59:59Z",
                "created_at": "2023-05-08T10:15:30Z",
                "updated_at": "2023-05-09T08:20:15Z"
            }
        }
    """
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
    """
    Delete a vital sign observation.
    
    This endpoint allows doctors to delete their previously created observations.
    Only the doctor who created the observation can delete it.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        observation_id (int): ID of the observation to delete
        
    Returns:
        JSON response with success message or error message
        
    Status codes:
        200: Observation deleted successfully
        403: Not authorized to delete this observation
        404: Observation not found
        500: Database error
        
    Response format (success):
        {
            "message": "Observation deleted successfully"
        }
    """
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
        
@api_bp.route('/patients/import', methods=['POST'])
@doctor_required
def import_patient(doctor):
    """
    Import an existing patient by UUID.
    
    This endpoint allows doctors to associate themselves with existing patients
    in the system by providing the patient's UUID. This is useful for collaborative
    care where multiple doctors need access to the same patient's data.
    
    Args:
        doctor: Doctor object automatically provided by the doctor_required decorator
        
    Request body:
        patient_uuid (str): UUID of the patient to import
        
    Returns:
        JSON response with success message and patient details or error message
        
    Status codes:
        200: Patient imported successfully
        400: Invalid UUID format or missing UUID
        404: Patient not found
        409: Patient already associated with this doctor
        500: Database or server error
        
    Response format (success):
        {
            "message": "Patient imported successfully",
            "patient": {
                "id": 42,
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "first_name": "John",
                "last_name": "Doe",
                ...
            }
        }
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
    if patient in doctor.patients.all():
        return jsonify({"error": _("Patient is already associated with your account")}), 409
    
    try:
        # Add patient to doctor's patients
        doctor_patient = DoctorPatient(doctor_id=doctor.id, patient_id=patient.id)
        db.session.add(doctor_patient)
        db.session.commit()
        
        # Log the import action
        log_patient_import(doctor.id, patient)
        
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
