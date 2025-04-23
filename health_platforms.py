"""
Health platforms integration module
Provides functionality to connect to and retrieve data from various health platforms
"""

import os
import json
import base64
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask import url_for, session, Blueprint, redirect, request, render_template, flash, jsonify
from flask_login import login_required, current_user
from flask_babel import gettext as _
from sqlalchemy.exc import SQLAlchemyError

from app import app, db
from models import Patient, HealthPlatform, HealthPlatformLink, VitalSignType, ActionType, EntityType
from audit import log_action, log_health_link_creation, log_platform_connection, log_platform_disconnection, log_data_sync
from health_platforms_config import FITBIT_CONFIG, FITBIT_ENDPOINTS

# Create the blueprint
health_bp = Blueprint('health', __name__, url_prefix='/health')

logger = logging.getLogger(__name__)

# -------- Link generation for health platform connection --------

def generate_platform_link(patient, doctor, platform):
    """
    Generate a temporary link for a patient to connect to a health platform
    
    Args:
        patient (Patient): Patient object
        doctor (Doctor): Doctor object
        platform (HealthPlatform): Platform to connect to
        
    Returns:
        HealthPlatformLink: Created link object
    """
    try:
        # First, invalidate any existing links for this patient and platform
        existing_links = HealthPlatformLink.query.filter_by(
            patient_id=patient.id,
            platform=platform,
            used=False
        ).all()
        
        for link in existing_links:
            link.used = True
        
        # Create a new link
        new_link = HealthPlatformLink(
            patient_id=patient.id,
            doctor_id=doctor.id,
            platform=platform
        )
        
        db.session.add(new_link)
        db.session.commit()
        
        # Log the action
        try:
            log_health_link_creation(doctor.id, new_link)
        except Exception as log_error:
            logger.error(f"Error logging platform link creation: {str(log_error)}")
        
        return new_link
    except Exception as e:
        logger.error(f"Error generating platform link: {str(e)}")
        db.session.rollback()
        return None

def get_link_by_uuid(uuid):
    """
    Get a health platform link by its UUID
    
    Args:
        uuid (str): UUID of the link
        
    Returns:
        HealthPlatformLink: Found link or None
    """
    return HealthPlatformLink.query.filter_by(uuid=uuid).first()

# -------- Fitbit OAuth flow --------

def get_fitbit_authorization_url(link_uuid):
    """
    Get the Fitbit authorization URL for the OAuth flow
    
    Args:
        link_uuid (str): UUID of the health platform link
        
    Returns:
        str: Authorization URL to redirect the user to
    """
    params = {
        'client_id': FITBIT_CONFIG['client_id'],
        'response_type': 'code',
        'scope': FITBIT_CONFIG['scope'],
        'redirect_uri': FITBIT_CONFIG['redirect_uri'],
        'state': link_uuid,
        'expires_in': 31536000  # 365 days (1 year) - massimo consentito da Fitbit
    }
    
    auth_url = f"{FITBIT_CONFIG['authorize_url']}?{urlencode(params)}"
    return auth_url

def exchange_fitbit_code_for_token(authorization_code):
    """
    Exchange an authorization code for an access token
    
    Args:
        authorization_code (str): Authorization code from Fitbit
        
    Returns:
        dict: Token response with access_token, refresh_token, etc. or None if error
    """
    try:
        # Create the Authorization header (Basic auth with client_id:client_secret)
        auth_header = base64.b64encode(
            f"{FITBIT_CONFIG['client_id']}:{FITBIT_CONFIG['client_secret']}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': FITBIT_CONFIG['client_id'],
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': FITBIT_CONFIG['redirect_uri']
        }
        
        response = requests.post(
            FITBIT_CONFIG['token_url'],
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting Fitbit token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception during token exchange: {str(e)}")
        return None

def refresh_fitbit_token(refresh_token):
    """
    Refresh an expired Fitbit access token
    
    Args:
        refresh_token (str): Refresh token from previous authorization
        
    Returns:
        dict: New token response or None if error
    """
    try:
        # Create the Authorization header (Basic auth with client_id:client_secret)
        auth_header = base64.b64encode(
            f"{FITBIT_CONFIG['client_id']}:{FITBIT_CONFIG['client_secret']}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(
            FITBIT_CONFIG['token_url'],
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error refreshing Fitbit token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception during token refresh: {str(e)}")
        return None

def save_fitbit_tokens(patient, token_response):
    """
    Save Fitbit tokens to the patient record
    
    Args:
        patient (Patient): Patient object
        token_response (dict): Token response from Fitbit
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract token data
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        # Default to 1 year if not provided - il massimo possibile per Fitbit
        expires_in = token_response.get('expires_in', 31536000)
        
        # Calculate expiry date
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Update patient record
        patient.connected_platform = HealthPlatform.FITBIT
        patient.platform_access_token = access_token
        patient.platform_refresh_token = refresh_token
        patient.platform_token_expires_at = expires_at
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving Fitbit tokens: {str(e)}")
        db.session.rollback()
        return False

def ensure_fresh_token(patient):
    """
    Ensure the patient has a valid (not expired) Fitbit token
    If token is expired, try to refresh it
    
    Args:
        patient (Patient): Patient object
        
    Returns:
        str: Valid access token or None if unable to get one
    """
    if not patient.connected_platform == HealthPlatform.FITBIT:
        logger.error("Patient is not connected to Fitbit")
        return None
    
    if not patient.platform_token_expires_at or not patient.platform_access_token:
        logger.error("Patient has no Fitbit token data")
        return None
    
    # Check if token is still valid (with a 5 minute buffer)
    if patient.platform_token_expires_at > datetime.utcnow() + timedelta(minutes=5):
        return patient.platform_access_token
    
    # Token is expired or expiring soon, try to refresh
    if not patient.platform_refresh_token:
        logger.error("No refresh token available")
        return None
    
    # Refresh the token
    token_response = refresh_fitbit_token(patient.platform_refresh_token)
    if token_response:
        if save_fitbit_tokens(patient, token_response):
            return token_response.get('access_token')
    
    return None

# -------- Data retrieval from Fitbit API --------

def get_fitbit_data(patient, data_type, start_date=None, end_date=None):
    """
    Get data from Fitbit API for the specified data type
    
    Args:
        patient (Patient): Patient object
        data_type (str): Type of data to retrieve (heart_rate, steps, etc.)
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        
    Returns:
        dict: Data from Fitbit API or None if error
    """
    if data_type not in FITBIT_ENDPOINTS:
        logger.error(f"Unsupported Fitbit data type: {data_type}")
        return None
    
    access_token = ensure_fresh_token(patient)
    if not access_token:
        logger.error("No valid access token available")
        return None
    
    endpoint_config = FITBIT_ENDPOINTS[data_type]
    
    # Costruisci l'endpoint con le date fornite o usa l'endpoint predefinito
    if start_date and end_date:
        # Sostituisci la parte della data nell'endpoint
        base_endpoint = endpoint_config.get('base_endpoint', endpoint_config['endpoint'])
        period = endpoint_config.get('period', '1d')  # periodo predefinito di 1 giorno
        detail_level = endpoint_config.get('detail_level', '')  # livello di dettaglio
        
        # Diversi tipi di dati hanno diverse strutture di endpoint
        if data_type == 'heart_rate':
            endpoint = f"/1/user/-/activities/heart/date/{start_date}/{end_date}/{detail_level or '1min'}.json"
        elif data_type == 'sleep_duration':
            # Per sonno, usiamo un endpoint diverso che accetta un intervallo di date
            endpoint = f"/1.2/user/-/sleep/date/{start_date}/{end_date}.json"
        else:
            # Per altri tipi di dati (passi, calorie, ecc.)
            endpoint = f"/1/user/-/activities/{data_type.replace('_', '')}/date/{start_date}/{end_date}.json"
    else:
        endpoint = endpoint_config['endpoint']
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.get(
            f"{FITBIT_CONFIG['api_base_url']}{endpoint}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            logger.error(f"Error retrieving Fitbit data: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception during Fitbit data retrieval: {str(e)}")
        return None

def process_fitbit_data(data, data_type):
    """
    Process raw Fitbit API data into a standardized format
    
    Args:
        data (dict): Raw data from Fitbit API
        data_type (str): Type of data being processed
        
    Returns:
        list: Processed data in format [{'timestamp': ISO8601, 'value': 123, 'unit': 'xyz'}, ...]
    """
    if not data or data_type not in FITBIT_ENDPOINTS:
        return []
    
    endpoint_config = FITBIT_ENDPOINTS[data_type]
    response_key = endpoint_config['response_key']
    value_key = endpoint_config['value_key']
    timestamp_key = endpoint_config['timestamp_key']
    unit = endpoint_config.get('unit', '')
    transform = endpoint_config.get('transform', lambda x: x)  # Identity function if no transform
    
    # Extract the data using the response key
    data_path = response_key.split('.')
    current_data = data
    
    for key in data_path:
        if key in current_data:
            current_data = current_data[key]
        else:
            logger.error(f"Key {key} not found in Fitbit response for {data_type}")
            return []
    
    # Special case handling for different data structures
    results = []
    
    if isinstance(current_data, list):
        # Handle list data format (most Fitbit endpoints)
        for item in current_data:
            if value_key in item and timestamp_key in item:
                try:
                    value = float(item[value_key])
                    timestamp = item[timestamp_key]
                    
                    # For heart rate and similar high-frequency data, append the date
                    if 'time' in endpoint_config and 'timestamp_format' in endpoint_config:
                        timestamp_format = endpoint_config['timestamp_format']
                        # Assume today's date for intraday data
                        today = datetime.today().strftime('%Y-%m-%d')
                        timestamp = f"{today} {timestamp}"
                    
                    # Apply any transform function
                    value = transform(value)
                    
                    results.append({
                        'timestamp': timestamp,
                        'value': value,
                        'unit': unit
                    })
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing Fitbit value: {str(e)}")
                    continue
    elif isinstance(current_data, dict):
        # Handle single object format (sleep, weight, etc.)
        if value_key in current_data and timestamp_key in current_data:
            try:
                value = float(current_data[value_key])
                timestamp = current_data[timestamp_key]
                
                # Apply any transform function
                value = transform(value)
                
                results.append({
                    'timestamp': timestamp,
                    'value': value,
                    'unit': unit
                })
            except (ValueError, TypeError) as e:
                logger.error(f"Error processing Fitbit value: {str(e)}")
    
    return results

def get_processed_fitbit_data(patient, data_type, start_date=None, end_date=None):
    """
    Get and process data from Fitbit API for the specified data type
    
    Args:
        patient (Patient): Patient object
        data_type (str): Type of data to retrieve (heart_rate, steps, etc.)
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        
    Returns:
        list: Processed data in format [{'timestamp': ISO8601, 'value': 123, 'unit': 'xyz'}, ...]
    """
    # Convert data_type to lowercase if it's coming from JavaScript/frontend
    # JavaScript uses uppercase like 'HEART_RATE' while Python backend expects lowercase like 'heart_rate'
    normalized_data_type = data_type.lower() if isinstance(data_type, str) else data_type
    
    # Common conversions to handle different naming formats
    if normalized_data_type == 'heart_rate':
        api_data_type = 'heart_rate'
    elif normalized_data_type in ['steps', 'step', 'steps_count']:
        api_data_type = 'steps'
    elif normalized_data_type in ['distance', 'distance_km']:
        api_data_type = 'distance'
    elif normalized_data_type in ['calories', 'calorie', 'energy']:
        api_data_type = 'calories'
    elif normalized_data_type in ['active_minutes', 'active_time', 'activity']:
        api_data_type = 'active_minutes'
    elif normalized_data_type in ['sleep_duration', 'sleep', 'sleep_time']:
        api_data_type = 'sleep_duration'
    elif normalized_data_type in ['floors_climbed', 'floors', 'elevation']:
        api_data_type = 'floors_climbed'
    elif normalized_data_type in ['weight', 'weight_kg', 'body_weight']:
        api_data_type = 'weight'
    else:
        # Default to the original value if no match found
        api_data_type = normalized_data_type
    
    raw_data = get_fitbit_data(patient, api_data_type, start_date, end_date)
    if raw_data:
        return process_fitbit_data(raw_data, api_data_type)
    
    logger.warning(f"No data returned from Fitbit API for {api_data_type}, patient {patient.id}")
    return []

# -------- Blueprint routes --------

@health_bp.route('/create_link/<int:patient_id>/<string:platform_name>', methods=['POST'])
@login_required
def create_link(patient_id, platform_name):
    """
    Create a link for a patient to connect to a health platform
    
    Args:
        patient_id (int): ID of the patient
        platform_name (str): Name of the platform to connect to
        
    Returns:
        Response: JSON with link details or error
    """
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        # Ensure the doctor is associated with this patient
        if patient not in current_user.patients.all():
            return jsonify({
                'success': False,
                'message': _('You are not authorized to manage this patient')
            }), 403
        
        # Convert platform name to enum
        try:
            platform = HealthPlatform(platform_name)
        except ValueError:
            return jsonify({
                'success': False,
                'message': _('Invalid platform name')
            }), 400
        
        # Generate link
        link = generate_platform_link(patient, current_user, platform)
        
        if link:
            # Return link details
            return jsonify({
                'success': True,
                'link_uuid': link.uuid,
                'expires_at': link.expires_at.isoformat(),
                'platform': platform.value,
                'connect_url': url_for('health.connect_platform', link_uuid=link.uuid, _external=True)
            })
        else:
            return jsonify({
                'success': False,
                'message': _('Error generating platform link')
            }), 500
    except Exception as e:
        logger.error(f"Error creating health platform link: {str(e)}")
        return jsonify({
            'success': False,
            'message': _('An error occurred')
        }), 500

@health_bp.route('/connect/<string:link_uuid>')
def connect_platform(link_uuid):
    """
    Handle the connection to a health platform
    Shows a page with available platforms and initiates OAuth flow
    
    Args:
        link_uuid (str): UUID of the health platform link
        
    Returns:
        Response: HTML page or redirect
    """
    # Get the link
    link = get_link_by_uuid(link_uuid)
    
    if not link:
        flash(_('Invalid or expired link'), 'danger')
        return render_template('error.html', 
                              message=_('The link you are trying to use is invalid or has expired'))
    
    # Check if link is expired
    if link.is_expired():
        flash(_('This link has expired'), 'danger')
        return render_template('error.html', 
                              message=_('The link you are trying to use has expired'))
    
    # Check if link was already used
    if link.used:
        flash(_('This link has already been used'), 'danger')
        return render_template('error.html', 
                              message=_('The link you are trying to use has already been used'))
    
    # Store link UUID in session for the callback
    session['link_uuid'] = link_uuid
    session['platform'] = link.platform.value
    
    # Get the patient
    patient = Patient.query.get(link.patient_id)
    
    # Show the connect page
    return render_template('health_connect.html',
                          link=link,
                          patient=patient,
                          platform=link.platform.value)

@health_bp.route('/start_auth/<string:platform_name>')
def start_auth(platform_name):
    """
    Start the OAuth flow for the specified platform
    
    Args:
        platform_name (str): Name of the platform
        
    Returns:
        Response: Redirect to OAuth provider
    """
    # Check if we have a link UUID in the session
    link_uuid = session.get('link_uuid')
    if not link_uuid:
        flash(_('Invalid session'), 'danger')
        return render_template('error.html', 
                              message=_('Your session is invalid or has expired'))
    
    # Get the link
    link = get_link_by_uuid(link_uuid)
    
    if not link or link.is_expired() or link.used:
        flash(_('Invalid or expired link'), 'danger')
        return render_template('error.html', 
                              message=_('The link you are trying to use is invalid or has expired'))
    
    # Generate the authorization URL based on the platform
    if platform_name == 'fitbit':
        auth_url = get_fitbit_authorization_url(link_uuid)
        return redirect(auth_url)
    else:
        flash(_('Unsupported platform'), 'danger')
        return render_template('error.html', 
                              message=_('The platform you selected is not supported'))

@health_bp.route('/oauth_callback')
def oauth_callback():
    """
    Handle the callback from OAuth provider
    
    Returns:
        Response: HTML page with success or error message
    """
    # Check for error parameter
    error = request.args.get('error')
    if error:
        flash(_('Authentication failed: %(error)s', error=error), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The health platform authentication failed'))
    
    # Get the authorization code
    code = request.args.get('code')
    if not code:
        flash(_('No authorization code received'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('No authorization code was received from the health platform'))
    
    # Get the state (link UUID)
    state = request.args.get('state')
    if not state:
        flash(_('Invalid state parameter'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The state parameter is missing from the callback'))
    
    # Get the link
    link = get_link_by_uuid(state)
    
    if not link:
        flash(_('Invalid link'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The link is invalid'))
    
    # Check if link is expired
    if link.is_expired():
        flash(_('This link has expired'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The link has expired'))
    
    # Check if link was already used
    if link.used:
        flash(_('This link has already been used'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The link has already been used'))
    
    # Get the patient
    patient = Patient.query.get(link.patient_id)
    
    # Exchange the code for a token based on the platform
    if link.platform == HealthPlatform.FITBIT:
        token_response = exchange_fitbit_code_for_token(code)
        
        if not token_response:
            flash(_('Failed to exchange authorization code for token'), 'danger')
            return render_template('health_connect_result.html',
                                  success=False,
                                  message=_('Failed to exchange the authorization code for a token'))
        
        # Save the tokens to the patient record
        if save_fitbit_tokens(patient, token_response):
            # Mark the link as used
            link.used = True
            db.session.commit()
            
            # Log the connection
            try:
                log_platform_connection(link.doctor_id, patient, HealthPlatform.FITBIT.value)
            except Exception as log_error:
                logger.error(f"Error logging platform connection: {str(log_error)}")
            
            flash(_('Successfully connected to Fitbit'), 'success')
            return render_template('health_connect_result.html',
                                  success=True,
                                  message=_('Your Fitbit account has been successfully connected'))
        else:
            flash(_('Failed to save token data'), 'danger')
            return render_template('health_connect_result.html',
                                  success=False,
                                  message=_('Failed to save the token data'))
    else:
        flash(_('Unsupported platform'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The platform is not supported'))

@health_bp.route('/check_connection/<int:patient_id>')
@login_required
def check_connection(patient_id):
    """
    API endpoint to check if a patient is connected to a health platform
    
    Args:
        patient_id (int): ID of the patient
        
    Returns:
        Response: JSON with connection status
    """
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        # Ensure the doctor is associated with this patient
        if patient not in current_user.patients.all():
            return jsonify({
                'connected': False,
                'message': _('You are not authorized to view this patient\'s data')
            }), 403
        
        # Check if patient has a connected platform
        if patient.connected_platform:
            # Verify token is still valid
            if patient.platform_token_expires_at and patient.platform_access_token:
                # Check if the token is still valid with the service
                is_valid = False
                
                # Platform-specific validity check
                if patient.connected_platform == HealthPlatform.FITBIT:
                    # Try to make a simple API call to check if the token is still valid
                    try:
                        headers = {
                            'Authorization': f'Bearer {patient.platform_access_token}'
                        }
                        response = requests.get(
                            f"{FITBIT_CONFIG['api_base_url']}/1/user/-/profile.json",
                            headers=headers
                        )
                        is_valid = response.status_code == 200
                    except Exception as e:
                        logger.error(f"Error checking Fitbit token validity: {str(e)}")
                        is_valid = False
                
                if is_valid:
                    return jsonify({
                        'connected': True,
                        'platform': patient.connected_platform.value,
                        'connected_since': patient.platform_token_expires_at.isoformat() if patient.platform_token_expires_at else None,
                        'token_expires_at': patient.platform_token_expires_at.isoformat() if patient.platform_token_expires_at else None
                    })
                else:
                    # Token is invalid, clear connection data
                    patient.connected_platform = None
                    patient.platform_access_token = None
                    patient.platform_refresh_token = None
                    patient.platform_token_expires_at = None
                    db.session.commit()
                    
                    # Log the disconnection due to invalid token
                    try:
                        log_platform_disconnection(current_user.id, patient, patient.connected_platform.value)
                    except Exception as log_error:
                        logger.error(f"Error logging platform disconnection: {str(log_error)}")
                    
                    return jsonify({
                        'connected': False,
                        'message': _('Token has expired or been revoked')
                    })
            else:
                return jsonify({
                    'connected': False,
                    'message': _('Incomplete token data')
                })
        else:
            return jsonify({
                'connected': False,
                'message': _('Not connected to any health platform')
            })
    except Exception as e:
        logger.error(f"Error checking connection status: {str(e)}")
        return jsonify({
            'connected': False,
            'message': _('Error checking connection status')
        }), 500

@health_bp.route('/disconnect/<int:patient_id>/<string:platform>', methods=['POST'])
@login_required
def disconnect_platform(patient_id, platform):
    """
    API endpoint to disconnect a patient from a health platform
    
    Args:
        patient_id (int): ID of the patient
        platform (str): Name of the platform to disconnect
        
    Returns:
        Response: JSON confirmation of disconnection
    """
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        # Ensure the doctor is associated with this patient
        if patient not in current_user.patients.all():
            return jsonify({
                'success': False,
                'message': _('You are not authorized to manage this patient\'s connections')
            }), 403
        
        # Convert platform string to enum value
        try:
            platform_enum = HealthPlatform(platform)
        except ValueError:
            return jsonify({
                'success': False,
                'message': _('Invalid platform specified')
            }), 400
        
        # Check if patient is actually connected to this platform
        if patient.connected_platform != platform_enum:
            return jsonify({
                'success': False,
                'message': _('Patient is not connected to the specified platform')
            }), 400
        
        # Clear connection data
        patient.connected_platform = None
        patient.platform_access_token = None
        patient.platform_refresh_token = None
        patient.platform_token_expires_at = None
        db.session.commit()
        
        # Log the disconnection
        try:
            log_platform_disconnection(current_user.id, patient, platform)
        except Exception as log_error:
            logger.error(f"Error logging platform disconnection: {str(log_error)}")
        
        return jsonify({
            'success': True,
            'message': _('Successfully disconnected from health platform')
        })
    except Exception as e:
        logger.error(f"Error disconnecting from health platform: {str(e)}")
        return jsonify({
            'success': False,
            'message': _('Error disconnecting from health platform')
        }), 500

@health_bp.route('/data/<string:data_type>/<int:patient_id>')
@login_required
def get_data(data_type, patient_id):
    """
    API endpoint to get data from a health platform
    Used for AJAX requests from the vitals page
    
    Args:
        data_type (str): Type of data to retrieve
        patient_id (int): ID of the patient
        
    Query Parameters:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        
    Returns:
        Response: JSON with the requested data
    """
    try:
        # Get start_date and end_date from query params if provided
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        patient = Patient.query.get_or_404(patient_id)
        
        # Ensure the doctor is associated with this patient
        if patient not in current_user.patients.all():
            return jsonify({
                'success': False,
                'message': _('You are not authorized to view this patient\'s data')
            }), 403
        
        # Check if patient is connected to a platform
        if not patient.connected_platform:
            return jsonify({
                'success': False,
                'message': _('Patient is not connected to any health platform'),
                'connect_url': url_for('views.patient_vitals', patient_id=patient_id)
            }), 404
        
        # Get data based on the platform
        if patient.connected_platform == HealthPlatform.FITBIT:
            data = get_processed_fitbit_data(patient, data_type, start_date, end_date)
            
            # Log the data sync
            try:
                result_summary = {
                    'data_points': len(data) if data else 0,
                    'start_date': start_date,
                    'end_date': end_date
                }
                log_data_sync(current_user.id, patient, patient.connected_platform.value, data_type, result_summary)
            except Exception as log_error:
                logger.error(f"Error logging data sync: {str(log_error)}")
            
            if data:
                return jsonify(data)
            else:
                return jsonify([])
        else:
            return jsonify({
                'success': False,
                'message': _('Unsupported platform'),
                'platform': patient.connected_platform.value
            }), 400
    except Exception as e:
        logger.error(f"Error retrieving health platform data: {str(e)}")
        return jsonify({
            'success': False,
            'message': _('An error occurred')
        }), 500