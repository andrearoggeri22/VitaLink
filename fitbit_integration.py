# File: fitbit_integration.py
# Author: VitaLink Team
# Date: April 2025
# Description: Module for integration with Fitbit devices.
#              Manages device connections, data extraction and storage
#              in the VitaLink system.

import os
import json
import glob
import logging
import datetime
import uuid
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from flask_babel import _

from models import Patient, VitalSign, VitalSignType, DataOrigin, db
from audit import log_vital_creation, log_action, ActionType, EntityType
from utils import get_vital_sign_unit
from notifications import notify_abnormal_vital
from utils import is_vital_in_range

fitbit_bp = Blueprint('fitbit', __name__)

# Temporary directory for file uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Mapping between Fitbit data types and system vital sign types
FITBIT_DATA_TYPES = {
    'heart_rate': VitalSignType.HEART_RATE,
    'steps': VitalSignType.STEPS,
    'calories': VitalSignType.CALORIES,
    'distance': VitalSignType.DISTANCE,
    'active_minutes': VitalSignType.ACTIVE_MINUTES,
    'sleep_duration': VitalSignType.SLEEP_DURATION,
    'floors_climbed': VitalSignType.FLOORS_CLIMBED
}

class DeviceConnectionError(Exception):
    # Exception raised when a Fitbit device cannot be connected or is unavailable
    # Used to handle connection errors specifically
    pass

def check_device_connected():
    # Check if a Fitbit device is connected via USB
    # Checks system directories for compatible USB devices
    #
    # Returns:
    #   bool: True if the device is connected, False otherwise
    try:
        # For demonstration and testing purposes, we return False to simulate device absence
        # In a real implementation, we would check the physical device
        from flask_babel import gettext as _
        
        logging.info(_("Fitbit device connection check - simulation mode enabled"))
        return False
        
        # The code below would be used in a real implementation
        """
        import glob
        
        # Search for Fitbit devices in USB directories (wearable device)
        fitbit_patterns = [
            '/dev/bus/usb/*/*',  # Generic USB devices
            '/sys/bus/usb/devices/*/idVendor',  # Check vendor IDs
        ]
        
        for pattern in fitbit_patterns:
            devices = glob.glob(pattern)
            for device in devices:
                # In a real implementation, check vendor and product IDs
                # Fitbit devices have specific USB identifiers
                if len(devices) > 0:
                    return True
        
        # No Fitbit device found
        return False
        """
    except Exception as e:
        logging.error(f"Error during device verification: {str(e)}")
        return False  # Return False in case of error for safety

def extract_fitbit_data(patient_id):
    # Extract data from the connected Fitbit device via USB
    #
    # Args:
    #     patient_id (int): ID of the patient to associate the data with
    #
    # Returns:
    #     dict: Data extracted from the device in the format:
    #           {
    #             'heart_rate': [{'timestamp': '2025-04-21T12:30:00', 'value': 75}],
    #             'steps': [{'timestamp': '2025-04-21', 'value': 8500}],
    #             'calories': [{'timestamp': '2025-04-21', 'value': 2100}],
    #             ...
    #           }
    #
    # Raises:
    #     DeviceConnectionError: If the device is not connected or there are connection problems
    if not check_device_connected():
        raise DeviceConnectionError("No Fitbit device connected")
    
    try:
        # Implementation for real data extraction from Fitbit device
        import os
        import json
        import subprocess
        import tempfile
        
        # 1. Identify the Fitbit device in the system
        # We use lsusb to search for Fitbit devices
        try:
            usb_devices = subprocess.check_output(['lsusb'], universal_newlines=True)
            # In a real system, we would filter Fitbit devices
            # Fitbit vendor ID is 0x2687
            if 'Fitbit' not in usb_devices and '2687' not in usb_devices:
                logging.warning("No Fitbit device found in lsusb")
                # We continue anyway to demonstrate functionality
        except (subprocess.SubprocessError, FileNotFoundError):
            logging.warning("Unable to execute lsusb to find Fitbit devices")
        
        # 2. Mount the device (in a real system)
        # In a complete implementation, we would have commands to mount the device's filesystem
        
        # 3. Read files from the device
        # In a real system, data might be in a proprietary format
        # Here we simulate reading from temporary files or from the mounted device
        
        # Temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        
        # Create temporary files that simulate data files from Fitbit
        current_date = datetime.datetime.now()
        
        # Generate sample data as if it were read from actual files
        result_data = {
            'heart_rate': [],
            'steps': [],
            'calories': [],
            'distance': [],
            'active_minutes': [],
            'sleep_duration': [],
            'floors_climbed': []
        }
        
        # Heart rate extraction - simulate data from the last 24 hours with 1 hour intervals
        for i in range(24, 0, -1):
            timestamp = current_date - datetime.timedelta(hours=i)
            # Vary the values a bit to simulate real measurements
            heart_rate = 70 + (i % 10) - 5
            result_data['heart_rate'].append({
                'timestamp': timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
                'value': heart_rate
            })
        
        # Steps extraction - data from the last 7 days
        for i in range(7, 0, -1):
            timestamp = current_date - datetime.timedelta(days=i)
            # Simulate different step counts per day
            steps = 7500 + (i * 200) + (hash(str(i)) % 1000)
            result_data['steps'].append({
                'timestamp': timestamp.strftime('%Y-%m-%d'),
                'value': steps
            })
        
        # Calories extraction - data from the last 7 days
        for i in range(7, 0, -1):
            timestamp = current_date - datetime.timedelta(days=i)
            # Calories correlated to steps
            calories = 2000 + (result_data['steps'][7-i-1]['value'] / 20)
            result_data['calories'].append({
                'timestamp': timestamp.strftime('%Y-%m-%d'),
                'value': int(calories)
            })
        
        # Distance extraction - data from the last 7 days
        for i in range(7, 0, -1):
            timestamp = current_date - datetime.timedelta(days=i)
            # Distance correlated to steps (approximately)
            distance = result_data['steps'][7-i-1]['value'] / 1300  # ~1300 steps per km
            result_data['distance'].append({
                'timestamp': timestamp.strftime('%Y-%m-%d'),
                'value': round(distance, 2)
            })
        
        # Active minutes data - last 7 days
        for i in range(7, 0, -1):
            timestamp = current_date - datetime.timedelta(days=i)
            # Active minutes correlated to steps
            active_mins = int(result_data['steps'][7-i-1]['value'] / 100)
            result_data['active_minutes'].append({
                'timestamp': timestamp.strftime('%Y-%m-%d'),
                'value': active_mins
            })
        
        # Sleep data - last 7 days
        for i in range(7, 0, -1):
            timestamp = current_date - datetime.timedelta(days=i)
            # Sleep hours with variation
            sleep_hours = 7 + ((hash(str(i*3)) % 20) / 10)
            result_data['sleep_duration'].append({
                'timestamp': timestamp.strftime('%Y-%m-%d'),
                'value': round(sleep_hours, 1)
            })
        
        # Floors climbed data - last 7 days
        for i in range(7, 0, -1):
            timestamp = current_date - datetime.timedelta(days=i)
            # Floors with variation
            floors = 8 + (hash(str(i*7)) % 10)
            result_data['floors_climbed'].append({
                'timestamp': timestamp.strftime('%Y-%m-%d'),
                'value': floors
            })
        
        # 4. Cleanup
        try:
            # In a real system, unmount the device
            # And remove temporary files
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as cleanup_error:
            logging.warning(f"Error during cleanup: {str(cleanup_error)}")
        
        return result_data
    except Exception as e:
        logging.error(f"Error during data extraction from the device: {str(e)}")
        raise DeviceConnectionError(f"Error during data extraction: {str(e)}")

def save_fitbit_data(patient_id, data):
    """
    Save data extracted from the Fitbit device to the database.
    
    Args:
        patient_id (int): Patient ID to associate the data with
        data (dict): Data extracted from the device in the format described in extract_fitbit_data
        
    Returns:
        tuple: (success, vitals_saved, errors)
            success (bool): True if data was successfully saved
            vitals_saved (int): Number of vital parameters saved
            errors (list): List of errors occurred during the saving process
    """
    vitals_saved = 0
    errors = []
    
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return False, 0, ["Patient not found"]
        
        # Debug logging
        logging.info(f"Starting to save Fitbit data for patient ID: {patient_id}")
        
        for data_type, measurements in data.items():
            if data_type not in FITBIT_DATA_TYPES:
                errors.append(f"Unsupported data type: {data_type}")
                continue
            
            vital_type = FITBIT_DATA_TYPES[data_type]
            logging.info(f"Processing data type: {data_type} -> enum type: {vital_type}, value: {vital_type.value}")
            
            for measurement in measurements:
                try:
                    # Convert timestamp to datetime
                    if 'T' in measurement['timestamp']:
                        recorded_at = datetime.datetime.strptime(measurement['timestamp'], '%Y-%m-%dT%H:%M:%S')
                    else:
                        recorded_at = datetime.datetime.strptime(measurement['timestamp'], '%Y-%m-%d')
                    
                    # Log values for debugging
                    logging.info(f"Value to insert: {measurement['value']}, timestamp: {recorded_at}")
                    
                    # Create new vital sign parameter
                    vital = VitalSign(
                        patient_id=patient_id,
                        type=vital_type,  # VitalSignType object from enum
                        value=float(measurement['value']),  # Ensure it's a float
                        unit=get_vital_sign_unit(data_type),
                        recorded_at=recorded_at,
                        origin=DataOrigin.AUTOMATIC
                    )
                    
                    db.session.add(vital)
                    vitals_saved += 1
                    
                    # Check if value is outside normal range and send notification
                    is_normal, status = is_vital_in_range(data_type, measurement['value'])
                    if not is_normal:
                        notify_abnormal_vital(
                            patient=patient,
                            vital_type=vital_type.value,
                            value=measurement['value'],
                            unit=get_vital_sign_unit(data_type),
                            status=status
                        )
                    
                except Exception as e:
                    logging.error(f"Save error: {str(e)}")
                    errors.append(f"Error saving parameter {data_type}: {str(e)}")
        
        db.session.commit()
        logging.info(f"Fitbit data successfully saved: {vitals_saved} parameters")
        return True, vitals_saved, errors
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemy database error: {str(e)}")
        return False, 0, [f"Database error: {str(e)}"]
    except Exception as e:
        db.session.rollback()
        logging.error(f"Generic error: {str(e)}")
        return False, 0, [f"Generic error: {str(e)}"]

@fitbit_bp.route('/patients/<int:patient_id>/check_device', methods=['GET'])
@login_required
def check_device_status(patient_id):
    """
    API endpoint to check if a Fitbit device is connected.
    
    Args:
        patient_id (int): Patient ID (not used directly but required for the route)
        
    Returns:
        JSON: JSON response with connection status in the format:
             {
               'connected': True|False,
               'timestamp': '2025-04-21T20:06:41'
             }
    """
    try:
        # This endpoint is called via AJAX from the client
        is_connected = check_device_connected()
        return jsonify({
            'connected': is_connected,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error during device verification: {str(e)}")
        return jsonify({
            'connected': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

@fitbit_bp.route('/patients/<int:patient_id>/upload_fitbit', methods=['GET', 'POST'])
@login_required
def upload_fitbit_data(patient_id):
    """
    Route to upload data from a Fitbit device connected via USB.
    """
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        try:
            # Check if the device is connected
            if not check_device_connected():
                flash("No Fitbit device connected. Connect the device via USB and try again.", "error")
                return redirect(url_for('fitbit.upload_fitbit_data', patient_id=patient_id))
            
            # Extract data from the device
            try:
                data = extract_fitbit_data(patient_id)
            except DeviceConnectionError as e:
                flash(f"Error during data extraction: {str(e)}", "error")
                return redirect(url_for('fitbit.upload_fitbit_data', patient_id=patient_id))
            
            # Save data to the database
            success, vitals_saved, errors = save_fitbit_data(patient_id, data)
            
            if success:
                flash(f"Fitbit data successfully uploaded. {vitals_saved} vital parameters saved.", "success")
                if errors:
                    for error in errors:
                        flash(f"Warning: {error}", "warning")
            else:
                flash("Error saving Fitbit data.", "error")
                for error in errors:
                    flash(error, "error")
            
            return redirect(url_for('views.patient_vitals', patient_id=patient_id))
        
        except Exception as e:
            flash(f"Error during upload process: {str(e)}", "error")
            return redirect(url_for('fitbit.upload_fitbit_data', patient_id=patient_id))
    
    # GET request - show the upload page
    return render_template('fitbit_upload.html', patient=patient)

# Mobile app APIs
@fitbit_bp.route('/api/mobile/patient/verify', methods=['POST'])
def mobile_verify_patient():
    """
    API endpoint to verify patient ID from the mobile app.
    The patient enters their UUID in the app and this endpoint verifies if it exists.
    
    Returns:
        JSON: Response with patient information if found
    """
    try:
        data = request.get_json()
        
        if not data or 'patient_uuid' not in data:
            return jsonify({'error': 'Patient UUID required'}), 400
            
        patient_uuid = data['patient_uuid']
        
        try:
            # Verify if UUID is in valid format
            uuid_obj = uuid.UUID(patient_uuid)
        except ValueError:
            return jsonify({'error': 'Invalid patient UUID'}), 400
            
        # Search for the patient in the database
        patient = Patient.query.filter_by(uuid=patient_uuid).first()
        
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
            
        # Return basic patient information
        return jsonify({
            'patient_id': patient.id,
            'name': f"{patient.first_name} {patient.last_name}",
            'success': True
        })
        
    except Exception as e:
        logging.error(f"Error during mobile patient verification: {str(e)}")
        return jsonify({'error': 'Server error'}), 500
        
@fitbit_bp.route('/api/mobile/data/upload', methods=['POST'])
def mobile_upload_data():
    """
    API endpoint per caricare dati Fitbit dall'app mobile.
    L'app mobile invia i dati raccolti dal dispositivo Fitbit.
    
    Returns:
        JSON: Risposta di conferma del salvataggio
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dati richiesti'}), 400
            
        # Valida i dati richiesti
        required_fields = ['patient_id', 'fitbit_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} richiesto'}), 400
                
        patient_id = data['patient_id']
        fitbit_data = data['fitbit_data']
        
        # Verifica che il paziente esista
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Paziente non trovato'}), 404
            
        # Salva i dati Fitbit
        success, vitals_saved, errors = save_fitbit_data(patient_id, fitbit_data)
        
        # Log dell'azione di caricamento dati da mobile
        log_action(
            doctor_id=None,  # Nessun medico coinvolto, è un'azione automatica da mobile
            action_type=ActionType.CREATE,
            entity_type=EntityType.VITAL_SIGN,
            entity_id=patient_id,  # Usiamo l'ID del paziente come reference
            details={
                'operation': 'mobile_data_upload',
                'vitals_saved': vitals_saved,
                'errors': errors
            },
            patient_id=patient_id
        )
        
        if not success:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
            
        return jsonify({
            'success': True,
            'vitals_saved': vitals_saved,
            'errors': errors
        })
        
    except Exception as e:
        logging.error(f"Errore durante il caricamento dei dati mobile: {str(e)}")
        return jsonify({'error': 'Errore del server'}), 500