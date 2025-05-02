"""
Observations Module.

This module provides functionality for creating, retrieving, updating, and deleting
vital sign observations for patients. It includes web routes for the application's
user interface as well as utility functions for working with observation data.

Observations represent medical professionals' interpretations of vital sign data
over specific time periods, allowing tracking and analysis of patient health trends.
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from flask_babel import gettext as _
from .app import db
from .models import (Patient, VitalObservation, VitalSignType)
from .audit import (log_observation_creation, log_observation_update, log_observation_delete)

observations_bp = Blueprint('observations', __name__)
"""
Observations Blueprint.

This blueprint manages all routes related to vital sign observations,
including creating, retrieving, updating, and deleting observations.
It provides both web interface endpoints and utility functions for 
handling observation data.
"""

logger = logging.getLogger(__name__)
"""
Observations module logger.

Logger for observation-related events such as creation, updates, 
and deletions of vital sign observations, along with any errors
that occur during these operations.
"""

@observations_bp.route('/web/observations/<int:patient_id>', methods=['GET'])
@login_required
def get_web_observations(patient_id):
    """
    Get observations for a specific patient.
    
    This endpoint retrieves vital sign observations for a specific patient
    with optional filtering by date range and vital sign type.
    
    Args:
        patient_id (int): The ID of the patient to get observations for
        
    Query Parameters:
        start_date (str, optional): ISO formatted date to filter observations after
        end_date (str, optional): ISO formatted date to filter observations before
        vital_type (str, optional): Type of vital sign to filter by
    
    Returns:
        JSON response with filtered observations or error message
    """    # Find the patient
    patient = Patient.query.get_or_404(patient_id)
    
    # Verify that the doctor is associated with this patient
    if patient not in current_user.patients.all():
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
            return jsonify({"error": _("Invalid start date format. Use ISO format (YYYY-MM-DD)")}), 400
    
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            query = query.filter(VitalObservation.end_date <= end_date)
        except ValueError:
            return jsonify({"error": _("Invalid end date format. Use ISO format (YYYY-MM-DD)")}), 400
    
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

@observations_bp.route('/web/observations', methods=['POST'])
@login_required
def add_web_observation():
    """
    Add a new vital sign observation.
    
    This endpoint creates a new observation for a patient's vital signs over a specific
    time period. The observation includes interpretation and notes from the doctor.
    
    Request Body JSON:
        patient_id (int): ID of the patient the observation is for
        vital_type (str): Type of vital sign from VitalSignType enum
        content (str): Doctor's notes and interpretation of the vital sign data
        start_date (str): ISO formatted start date of the observation period
        end_date (str): ISO formatted end date of the observation period
    
    Returns:
        JSON response with the created observation or error message
    
    Status Codes:
        201: Observation created successfully
        400: Invalid request data
        403: Not authorized to create observation for this patient
        404: Patient not found
        500: Database error
    """    # Validate request data
    if not request.is_json:
        return jsonify({"error": _("Missing JSON data in request")}), 400
    
    data = request.json
    logger.debug(f"Data received for new observation: {data}")
    
    # Validate required fields
    required_fields = ['patient_id', 'vital_type', 'content', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": _("Required field missing: %(field)s") % {"field": field}}), 400
    
    # Find the patient
    patient_id = data['patient_id']
    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({"error": _("Patient not found")}), 404
    
    # Verify that the doctor is associated with this patient
    if patient not in current_user.patients.all():
        return jsonify({"error": _("You are not authorized to access this patient")}), 403
      # Validate vital sign type
    try:
        logger.debug(f"Received vital sign type: {data['vital_type']}")
        logger.debug(f"Available vital sign types: {[t.value for t in VitalSignType]}")
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
        return jsonify({"error": _("Invalid start date format. Use ISO format (YYYY-MM-DD)")}), 400
    
    try:
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": _("Invalid end date format. Use ISO format (YYYY-MM-DD)")}), 400
    
    # Verify that start date is before end date
    if start_date >= end_date:
        return jsonify({"error": _("Start date must be before end date")}), 400
      # Create the observation
    try:
        observation = VitalObservation(
            patient_id=patient_id,
            doctor_id=current_user.id,
            vital_type=vital_type,
            content=data['content'],
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(observation)
        db.session.commit()
        
        # Audit logging
        try:
            log_observation_creation(current_user.id, observation)
        except Exception as e:
            logger.error(f"Error during audit logging for observation creation: {str(e)}")
        
        logger.info(f"Observation added for patient {patient_id} by doctor {current_user.id}")
        
        return jsonify({
            "message": _("Observation added successfully"),
            "observation": observation.to_dict()
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error while adding the observation: {str(e)}")
        return jsonify({"error": _("An error occurred while adding the observation")}), 500

@observations_bp.route('/web/observations/<int:observation_id>', methods=['PUT'])
@login_required
def update_web_observation(observation_id):
    """
    Update an existing vital sign observation.
    
    This endpoint allows doctors to modify their own previously created observations.
    Any combination of observation fields may be updated.
    
    Args:
        observation_id (int): ID of the observation to update
        
    Request Body JSON:
        vital_type (str, optional): New type of vital sign
        content (str, optional): Updated notes or interpretation
        start_date (str, optional): New ISO formatted start date
        end_date (str, optional): New ISO formatted end date
        
    Returns:
        JSON response with the updated observation or error message
        
    Status Codes:
        200: Observation updated successfully
        400: Invalid request data
        403: Not authorized to modify this observation
        404: Observation not found
        500: Database error
    """    # Find the observation
    observation = VitalObservation.query.get_or_404(observation_id)
    
    # Verify that the doctor is the creator of the observation
    if observation.doctor_id != current_user.id:
        return jsonify({"error": _("You are not authorized to modify this observation")}), 403
    
    # Validate the request data
    if not request.is_json:
        return jsonify({"error": _("Missing JSON data in request")}), 400
    
    data = request.json
      # Update the vital sign type if provided
    if 'vital_type' in data:
        try:
            observation.vital_type = VitalSignType(data['vital_type'])
        except ValueError:
            return jsonify({
                "error": _("Invalid vital sign type. Must be one of: %(types)s") % {
                    "types": ", ".join(t.value for t in VitalSignType)
                }
            }), 400
    
    # Update the content if provided
    if 'content' in data:
        observation.content = data['content']
    
    # Update the start date if provided
    if 'start_date' in data:
        try:
            observation.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": _("Invalid start date format. Use ISO format (YYYY-MM-DD)")}), 400
    
    # Aggiorna la data di fine se fornita
    if 'end_date' in data:
        try:
            observation.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": _("Invalid end date format. Use ISO format (YYYY-MM-DD)")}), 400
    # Verify that start date is before end date
    if observation.start_date >= observation.end_date:
        return jsonify({"error": _("Start date must be before end date")}), 400
    
    # Save the changes
    try:
        # Save previous data for audit
        old_data = {
            'vital_type': observation.vital_type.value if observation.vital_type else None,
            'content': observation.content,
            'start_date': observation.start_date.isoformat() if observation.start_date else None,
            'end_date': observation.end_date.isoformat() if observation.end_date else None,
        }
        observation.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Audit logging
        try:
            log_observation_update(current_user.id, observation, old_data)
        except Exception as e:
            logger.error(f"Error during audit logging for observation update: {str(e)}")
        
        logger.info(f"Observation {observation_id} updated by doctor {current_user.id}")
        return jsonify({
            "message": _("Observation updated successfully"),
            "observation": observation.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error while updating the observation: {str(e)}")
        return jsonify({"error": _("An error occurred while updating the observation")}), 500

@observations_bp.route('/web/observations/<int:observation_id>', methods=['DELETE'])
@login_required
def delete_web_observation(observation_id):
    """
    Delete an existing vital sign observation.
    
    This endpoint allows doctors to remove their own previously created observations.
    A record of the deletion is maintained in the audit log for compliance purposes.
    
    Args:
        observation_id (int): ID of the observation to delete
        
    Returns:
        JSON response with success message or error details
        
    Status Codes:
        200: Observation deleted successfully
        403: Not authorized to delete this observation
        404: Observation not found
        500: Database error
    """    # Find the observation
    observation = VitalObservation.query.get_or_404(observation_id)
    
    # Verify that the doctor is the creator of the observation
    if observation.doctor_id != current_user.id:
        return jsonify({"error": _("You are not authorized to delete this observation")}), 403
    
    # Delete the observation
    try:
        # Save a copy of the observation data before deletion for audit
        observation_copy = {
            'id': observation.id,
            'patient_id': observation.patient_id,
            'vital_type': observation.vital_type,
            'content': observation.content,
            'start_date': observation.start_date,
            'end_date': observation.end_date
        }        
        db.session.delete(observation)
        db.session.commit()
        
        # Audit logging
        try:
            # Create a temporary object with attributes needed for logging
            class TempObservation:
                def __init__(self, data):
                    self.id = data['id']
                    self.patient_id = data['patient_id']
                    self.vital_type = data['vital_type']
                    self.content = data['content']
                    self.start_date = data['start_date']
                    self.end_date = data['end_date']
            
            temp_obs = TempObservation(observation_copy)
            log_observation_delete(current_user.id, temp_obs)
        except Exception as e:
            logger.error(f"Error during audit logging for observation deletion: {str(e)}")
        
        logger.info(f"Observation {observation_id} deleted by doctor {current_user.id}")
        
        return jsonify({
            "message": _("Observation deleted successfully")
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error while deleting the observation: {str(e)}")
        return jsonify({"error": _("An error occurred while deleting the observation")}), 500