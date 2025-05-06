"""
Health Platforms Integration Module.

This module provides comprehensive functionality to connect to, authenticate with,
and retrieve data from various health and fitness platforms. It currently supports
Fitbit with extensibility for other platforms like Google Health Connect and Apple Health.

Key features:
1. OAuth2 authentication flows for connecting user accounts to health platforms
2. API clients for retrieving different types of health data (heart rate, steps, etc.)
3. Data processing and normalization to standardize data across platforms
4. Intelligent caching to minimize API calls and respect rate limits
5. Error handling for API failures, token expiration, and invalid requests

The module implements a Blueprint with routes for connecting/disconnecting platforms
and background functionality for data synchronization. It includes proper audit logging
for all operations to maintain a record of data access.
"""

import uuid
import base64
import logging
import requests
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask import url_for, session, Blueprint, redirect, request, render_template, flash, jsonify
from flask_login import login_required, current_user
from flask_babel import gettext as _

from .app import db
from .models import (Patient, HealthPlatform, HealthPlatformLink)
from .audit import (log_health_link_creation, log_platform_connection, log_platform_disconnection, log_data_sync)
from .health_platforms_config import (FITBIT_CONFIG, FITBIT_ENDPOINTS)

# Create the blueprint
health_bp = Blueprint('health', __name__, url_prefix='/health')
"""
Health Platforms Blueprint.

This blueprint manages all routes related to health platform integrations,
including OAuth flows, connection management, and data retrieval.
It provides both web interface endpoints and API endpoints for interacting
with third-party health data sources.
"""

logger = logging.getLogger(__name__)
"""
Health platforms module logger.

Logger for tracking events related to health platform integrations,
including connection attempts, OAuth flows, API calls, and data synchronization.
"""

"""
Cache for vital sign data to minimize API calls and improve performance.

This dictionary stores previously fetched data from health platforms to avoid
redundant API calls when the same data is requested multiple times within a
short timeframe. This helps respect API rate limits and improves application
responsiveness.

Structure:
    {
        'cache_key': {
            'data': [...],                # Actual vital sign data points
            'cache_time': datetime,       # When data was cached
            'request_params': {...},      # Request parameters (for debugging)
            'api_calls': 0                # API call count for this cache key
        }
    }

Cache keys are generated based on patient ID, vital type, and date range.
Data is considered stale after a configurable period (default: 5 minutes).
"""
vitals_cache = {}

"""
Rate limit management for health platform API calls.

This dictionary tracks API usage to ensure the application respects
the rate limits imposed by health platforms (particularly Fitbit).
It implements a sliding window approach to track call frequency and
automatically backs off when approaching limits.

Structure:
    {
        'last_reset': datetime,      # Last time the counter was reset
        'calls': 0,                  # Call counter within current window
        'hourly_limit': 150,         # Hourly call limit (Fitbit rate limit)
        'retry_after': None          # Time when we can resume calls after hitting limit
    }

When the rate limit is reached, subsequent calls are blocked until
the retry_after time, preventing HTTP 429 errors from the API.
"""
api_rate_limit = {
    'last_reset': datetime.utcnow(),
    'calls': 0,
    'hourly_limit': 150,
    'retry_after': None
}

# Logging configuration
logger = logging.getLogger(__name__)

# Add a specific handler for Fitbit API
api_logger = logging.getLogger('fitbit_api')
"""
Specialized logger for Fitbit API interactions.

This dedicated logger captures detailed information about all Fitbit API calls,
responses, errors, and rate limit information. It writes to a separate log file
for easier debugging and monitoring of API-specific issues.
"""
api_logger.setLevel(logging.DEBUG)

# Create a file handler for detailed logging
try:
    api_file_handler = logging.FileHandler('fitbit_api.log')
    """
    File handler for Fitbit API logs.

    Writes detailed Fitbit API interaction logs to a dedicated file, separate
    from the main application logs for easier troubleshooting of API issues.
    """
    api_file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    """
    Log formatter for Fitbit API logs.

    Defines the format for API log entries, including timestamp, log level,
    and the actual message content.
    """
    api_file_handler.setFormatter(formatter)
    api_logger.addHandler(api_file_handler)
except Exception as e:
    """
    Exception object from log file creation attempt.

    Captured when the application fails to create or write to the Fitbit API log file,
    typically due to permission issues or disk space constraints.
    """
    logger.error(f"Unable to create log file for Fitbit API: {str(e)}")

# -------- Link generation for health platform connection --------

def generate_platform_link(patient, doctor, platform):
    """
    Generate a temporary link for a patient to connect to a health platform.

    This function creates a unique, time-limited link that can be shared with a patient
    to authorize connection to a health platform (e.g., Fitbit). The link contains
    a secure token that expires after a set period and can only be used once.

    The link is recorded in the database and associated with both the patient and
    the doctor who initiated the connection. Old/expired links for the same patient
    and platform are invalidated to maintain security.

    Args:
        patient (Patient): The patient object to connect to the platform
        doctor (Doctor): The doctor who is initiating the connection
        platform (HealthPlatform): Which health platform to connect to (e.g., FITBIT)

    Returns:
        HealthPlatformLink: The created link object containing the token and URL

    Raises:
        SQLAlchemyError: If there's a database issue when creating the link
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
    Retrieve a health platform link by its UUID.

    This function looks up an existing health platform connection link
    using its unique identifier. These links are created when a doctor
    initiates a connection process for a patient.

    Args:
        uuid (str): The unique identifier of the platform link

    Returns:
        HealthPlatformLink: The found link object, or None if not found

    Example:
        link = get_link_by_uuid("123e4567-e89b-12d3-a456-426614174000")
        if link and not link.used:
            # Process valid link
    """
    return HealthPlatformLink.query.filter_by(uuid=uuid).first()

# -------- Fitbit OAuth flow --------

def get_fitbit_authorization_url(link_uuid):
    """
    Generate the Fitbit authorization URL for initiating the OAuth2 flow.

    This function builds the URL to Fitbit's authorization endpoint with all
    necessary OAuth2 parameters. When a user visits this URL, they will be
    prompted to log in to their Fitbit account and authorize the VitaLink
    application to access their health data according to the requested scopes.

    The function includes:
    - Client ID from Fitbit Developer configuration
    - Required response_type for authorization code flow
    - All needed data scopes (activity, heartrate, etc.)
    - Redirect URI for OAuth callback
    - State parameter for security (using the link UUID)
    - Expiration setting requesting maximum token lifetime

    Args:
        link_uuid (str): UUID of the health platform link, used as the state
                        parameter to prevent CSRF attacks

    Returns:
        str: Complete authorization URL to redirect the user to
             This URL points to Fitbit's authorization server
    """
    params = {
        'client_id': FITBIT_CONFIG['client_id'],
        'response_type': 'code',
        'scope': FITBIT_CONFIG['scope'],
        'redirect_uri': FITBIT_CONFIG['redirect_uri'],
        'state': link_uuid,
        'expires_in': 31536000  # 365 days (1 year) - maximum allowed by Fitbit
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
    Save OAuth2 tokens from Fitbit to the patient record.

    This function processes the token response received after a successful OAuth2
    authentication with Fitbit and stores the relevant token information in the
    patient's record. It handles both initial authorization and token refresh flows.

    The function stores:
    - Access token (for API calls)
    - Refresh token (for renewing access when it expires)
    - Expiration time (calculated based on expires_in value)

    Args:
        patient (Patient): The patient object to update with token information
        token_response (dict): The OAuth2 token response from Fitbit API

    Returns:
        bool: True if tokens were saved successfully, False if an error occurred

    Raises:
        Exception: Logs database errors but doesn't propagate them
    """
    try:
        # Extract token data
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        # Default to 1 year if not provided - the maximum possible for Fitbit
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
    Ensure the patient has a valid (not expired) Fitbit token.

    This function checks if the patient's Fitbit access token is still valid
    and attempts to refresh it if expired. It handles all aspects of token
    management including checking expiration time, using the refresh token
    to obtain a new access token, and updating the patient record with new
    token information.

    A small buffer time (5 minutes) is applied to the expiration to prevent
    using tokens that are about to expire during an operation.

    Args:
        patient (Patient): Patient object with stored token information

    Returns:
        str: Valid access token ready for API use, or None if unable to get one
              (due to disconnected platform, missing tokens, or refresh failure)

    Side effects:
        Updates the patient's token information in the database if refreshed
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

def check_rate_limit():
    """
    Check if we have reached the Fitbit API rate limit.

    This function implements the rate limiting logic to prevent exceeding
    Fitbit's API call limits, which could result in temporary service blocks.
    It tracks call frequency in a sliding window approach and enforces
    waiting periods when limits are reached.

    The function checks:
    1. If we're in a forced wait period after hitting the rate limit
    2. If the hourly window has elapsed, resetting the counter when needed
    3. If we've exceeded the hourly call limit

    Returns:
        bool: True if we can make API requests, False if we should wait
              When False is returned, the application should avoid making
              new API calls until the rate limit window resets
    """
    global api_rate_limit

    now = datetime.utcnow()

    # If there's a retry_after set and it hasn't passed yet, block requests
    if api_rate_limit['retry_after'] and now < api_rate_limit['retry_after']:
        wait_seconds = (api_rate_limit['retry_after'] - now).total_seconds()
        api_logger.warning(f"Rate limit active, wait {wait_seconds:.1f} seconds.")
        return False

    # If an hour has passed since the last reset, reset the counter
    if (now - api_rate_limit['last_reset']).total_seconds() >= 3600:
        api_rate_limit['last_reset'] = now
        api_rate_limit['calls'] = 0
        api_logger.info("Rate limit counter reset after 1 hour.")

    # Check if we've exceeded the hourly limit
    if api_rate_limit['calls'] >= api_rate_limit['hourly_limit']:
        api_rate_limit['retry_after'] = api_rate_limit['last_reset'] + timedelta(hours=1)
        api_logger.warning(f"Rate limit reached ({api_rate_limit['calls']} calls). "
                           f"Try again after {api_rate_limit['retry_after'].strftime('%H:%M:%S')}")
        return False

    return True

def increment_api_call_counter(response=None):
    """
    Increment the API call counter and handle any rate limits.

    This function updates the API call tracking system after each API request
    and processes any rate limit information returned from the Fitbit API.
    It is essential for maintaining compliance with Fitbit's API usage policies
    and preventing API lockout due to excessive calls.

    The function handles various rate limiting scenarios:
    1. Incrementing the call counter for normal tracking
    2. Detecting 429 (Too Many Requests) responses
    3. Processing the Retry-After header value to establish waiting periods

    Args:
        response (Response, optional): The API response object to check for
            rate limit headers. If None, only increments the counter without
            checking for rate limiting headers.

    Side effects:
        Updates the global api_rate_limit dictionary with new counts and
        potentially sets the retry_after timestamp when rate limits are hit.
    """
    global api_rate_limit

    api_rate_limit['calls'] += 1

    # If the response contains rate limit headers, update our limits
    if response and response.status_code == 429:
        # Get the Retry-After value if present
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                seconds = int(retry_after)
                api_rate_limit['retry_after'] = datetime.utcnow() + timedelta(seconds=seconds)
                api_logger.warning(f"Rate limit reached. Retry-After: {seconds} seconds.")
            except ValueError:
                # If it's not an integer, assume it's an RFC1123 date
                api_rate_limit['retry_after'] = datetime.utcnow() + timedelta(hours=1)
                api_logger.warning("Rate limit reached. Wait for 1 hour.")
        else:
            # If there's no Retry-After, wait 1 hour for safety
            api_rate_limit['retry_after'] = datetime.utcnow() + timedelta(hours=1)
            api_logger.warning("Rate limit reached. Wait for 1 hour.")

def get_fitbit_data(patient, data_type, start_date=None, end_date=None):
    """
    Retrieve raw data from Fitbit API for the specified data type.

    This function handles all aspects of communicating with Fitbit's API
    to retrieve health data, including token management, rate limit checking,
    proper URL formatting, and error handling. It supports various Fitbit
    data types as defined in FITBIT_ENDPOINTS.

    This is a lower-level function that returns the raw API response. For
    processed and formatted data suitable for the application, use 
    get_processed_fitbit_data() instead.

    Args:
        patient (Patient): Patient object with Fitbit connection information
        data_type (str): Type of data to retrieve (heart_rate, steps, sleep, etc.)
                         Must be one of the keys in FITBIT_ENDPOINTS
        start_date (str, optional): Start date in YYYY-MM-DD format
                                   Defaults to current date if not provided
        end_date (str, optional): End date in YYYY-MM-DD format
                                 Defaults to current date if not provided

    Returns:
        dict: Raw data from Fitbit API or None if any error occurs
              (authentication failure, rate limit, invalid data type, etc.)

    Note:
        This function respects Fitbit's rate limits and may refuse to make
        a request if the rate limit has been reached. In such cases, None
        is returned and the caller should wait before retrying.
    """
    # Check if we have reached the rate limit
    if not check_rate_limit():
        api_logger.warning(f"Rate limit active, request blocked: {data_type} for patient {patient.id}")
        return None

    if data_type not in FITBIT_ENDPOINTS:
        api_logger.error(f"Unsupported Fitbit data type: {data_type}")
        return None

    access_token = ensure_fresh_token(patient)
    if not access_token:
        api_logger.error(f"Access token not available for patient {patient.id}")
        return None

    endpoint_config = FITBIT_ENDPOINTS[data_type]

    # Generate a unique log request ID to track this specific request
    request_id = str(uuid.uuid4())[:8]

    # Build the appropriate endpoint based on dates and data type
    if start_date and end_date:
        # Calculate the difference in days between the dates to check if it's within Fitbit's limits
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days_diff = (end_dt - start_dt).days + 1

            # Check if the range exceeds the maximum number of days for this data type
            max_range = endpoint_config.get('max_range_days', 31)

            if days_diff > max_range:
                api_logger.warning(f"[{request_id}] Range of {days_diff} days exceeds the limit of {max_range} for {data_type}. "
                                 f"Limiting to {max_range} days from {end_date}.")
                # Limit the range to the maximum allowed, starting from the end date
                start_date = (end_dt - timedelta(days=max_range-1)).strftime('%Y-%m-%d')
                api_logger.info(f"[{request_id}] Modified range: {start_date} - {end_date}")
        except ValueError as e:
            api_logger.error(f"[{request_id}] Error in date format: {str(e)}")
            return None

        # Use the specific range endpoint for this data type
        if 'range_endpoint' in endpoint_config:
            endpoint = endpoint_config['range_endpoint'].format(start=start_date, end=end_date)
            api_logger.info(f"[{request_id}] Using range endpoint for {data_type}: {endpoint}")
        else:
            # Fallback to the generic format if no range_endpoint is specified
            base = endpoint_config.get('base_endpoint', '')
            endpoint = f"{base}/{start_date}/{end_date}.json"
            api_logger.info(f"[{request_id}] Using generic endpoint for {data_type}: {endpoint}")
    else:
        # If no dates are provided, use the default endpoint
        endpoint = endpoint_config['endpoint']
        api_logger.info(f"[{request_id}] Using default endpoint for {data_type}: {endpoint}")

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept-Language': 'it_IT'  # Request data in Italian format
    }

    api_logger.debug(f"[{request_id}] Fitbit API call: {endpoint}")

    try:
        # Make the API call
        response = requests.get(
            f"{FITBIT_CONFIG['api_base_url']}{endpoint}",
            headers=headers
        )
          # Increment API call counter
        increment_api_call_counter(response)

        if response.status_code == 200:
            data = response.json()
            api_logger.info(f"[{request_id}] Data successfully received for {data_type}")

            # Detailed log for debugging (only in debug mode)
            if api_logger.isEnabledFor(logging.DEBUG):
                truncated_data = str(data)[:1000] + "..." if len(str(data)) > 1000 else str(data)
                api_logger.debug(f"[{request_id}] Response: {truncated_data}")

            return data
        elif response.status_code == 429:
            # Rate limit reached
            retry_after = response.headers.get('Retry-After', '3600')
            api_logger.warning(f"[{request_id}] Rate limit reached. Retry-After: {retry_after}")
            return None
        else:
            api_logger.error(f"[{request_id}] Error retrieving data: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        api_logger.error(f"[{request_id}] Exception during data retrieval: {str(e)}")
        return None

def process_fitbit_data(data, data_type):
    """
    Process raw Fitbit API data into a standardized format for the application.

    This function transforms the varied response formats from different Fitbit API
    endpoints into a consistent structure that can be used throughout the application.
    It handles the intricacies of each data type according to configurations in
    FITBIT_ENDPOINTS, including proper key extraction, value transformation,
    and unit standardization.

    Data processing includes:
    - Navigating the nested JSON structure of Fitbit responses
    - Extracting timestamps and converting to ISO 8601 format
    - Applying value transformations (e.g., unit conversions)
    - Adding appropriate measurement units

    Args:
        data (dict): Raw data from Fitbit API as returned by get_fitbit_data()
        data_type (str): Type of data being processed (must match a key in FITBIT_ENDPOINTS)

    Returns:
        list: Processed data in standardized format:
              [{'timestamp': ISO8601, 'value': 123, 'unit': 'xyz'}, ...]
              Returns empty list if data is None, empty, or data_type is unsupported

    Note:
        Each data point includes:
        - timestamp: ISO 8601 formatted time when the measurement was taken
        - value: The numerical value of the measurement (may be transformed from raw value)
        - unit: The unit of measurement (e.g., 'bpm' for heart rate)
    """
    request_id = str(uuid.uuid4())[:8]  # ID for log tracking

    if not data or data_type not in FITBIT_ENDPOINTS:
        api_logger.warning(f"[{request_id}] No data for processing or unsupported data type: {data_type}")
        return []

    endpoint_config = FITBIT_ENDPOINTS[data_type]
    response_key = endpoint_config['response_key']
    value_key = endpoint_config['value_key']
    timestamp_key = endpoint_config['timestamp_key']
    unit = endpoint_config.get('unit', '')
    transform = endpoint_config.get('value_transform', lambda x: x)  # Default identity function

    api_logger.info(f"[{request_id}] Processing data {data_type}, response with key {response_key}")

    # Special handling for heart rate
    if data_type == 'heart_rate' and 'activities-heart' in data:
        # Special processing for heart rate responses
        heart_results = []

        for heart_data in data['activities-heart']:
            if 'dateTime' in heart_data and 'value' in heart_data and isinstance(heart_data['value'], dict):
                timestamp = heart_data['dateTime']
                heart_value = None
                value_type = None

                # First check if there's a resting heart rate value
                if 'restingHeartRate' in heart_data['value']:
                    heart_value = heart_data['value']['restingHeartRate']
                    value_type = 'resting'
                    api_logger.info(f"[{request_id}] Found resting heart rate value: {heart_value} for {timestamp}")
                # If not, calculate an average from heart rate zones
                elif 'heartRateZones' in heart_data['value'] and heart_data['value']['heartRateZones']:
                    zones = heart_data['value']['heartRateZones']
                    zone_values = []

                    for zone in zones:
                        if 'min' in zone and 'max' in zone:
                            # Calculate the average of each zone
                            zone_avg = (float(zone['min']) + float(zone['max'])) / 2
                            zone_values.append(zone_avg)

                    if zone_values:
                        heart_value = sum(zone_values) / len(zone_values)
                        value_type = 'zone_avg'
                        api_logger.info(f"[{request_id}] Calculated average value from zones: {heart_value} for {timestamp}")

                if heart_value is not None:
                    heart_results.append({
                        'timestamp': timestamp,
                        'recorded_at': timestamp,
                        'value': float(heart_value),
                        'unit': unit,
                        'type': value_type
                    })

        if heart_results:
            api_logger.info(f"[{request_id}] Processed {len(heart_results)} heart rate values")
            return heart_results

    # Standard processing
    # Extract data from response based on response key
    if response_key in data:
        current_data = data[response_key]
    else:
        api_logger.error(f"[{request_id}] Response key {response_key} not found in data")
        return []

    # Handling of different data structures
    results = []

    # Helper function to extract nested values
    def extract_nested_value(obj, path):
        """Extract a nested value from an object based on a path."""
        if not path or not isinstance(obj, dict):
            return None

        key = path[0]
        if key not in obj:
            return None

        if len(path) == 1:
            return obj[key]

        return extract_nested_value(obj[key], path[1:])

    # Handling of nested values (e.g., value.restingHeartRate, value.avg)
    if '.' in value_key:
        value_path = value_key.split('.')

        if isinstance(current_data, list):
            # Process data in list format
            for item in current_data:
                if timestamp_key in item:
                    try:
                        nested_value = extract_nested_value(item, value_path)
                        if nested_value is not None:
                            value = float(nested_value)
                            timestamp = item[timestamp_key]

                            # Apply transformations
                            value = transform(value)

                            results.append({
                                'timestamp': timestamp,
                                'recorded_at': timestamp,
                                'value': value,
                                'unit': unit
                            })
                    except (ValueError, TypeError) as e:
                        api_logger.error(f"[{request_id}] Error during value processing: {str(e)}")

        elif isinstance(current_data, dict):
            # Process data in dict format
            if timestamp_key in current_data:
                try:
                    nested_value = extract_nested_value(current_data, value_path)
                    if nested_value is not None:
                        value = float(nested_value)
                        timestamp = current_data[timestamp_key]

                        # Apply transformations
                        value = transform(value)

                        results.append({
                            'timestamp': timestamp,
                            'recorded_at': timestamp,
                            'value': value,
                            'unit': unit
                        })
                except (ValueError, TypeError) as e:
                    api_logger.error(f"[{request_id}] Error during value processing: {str(e)}")
    else:
        # Standard key-value processing
        if isinstance(current_data, list):
            # Process list format
            for item in current_data:
                if value_key in item and timestamp_key in item:
                    try:
                        value = float(item[value_key])
                        timestamp = item[timestamp_key]

                        # Apply transformations
                        value = transform(value)

                        results.append({
                            'timestamp': timestamp,
                            'recorded_at': timestamp,
                            'value': value,
                            'unit': unit
                        })
                    except (ValueError, TypeError) as e:
                        api_logger.error(f"[{request_id}] Error in value processing: {str(e)}")

        elif isinstance(current_data, dict):
            # Process single dict format
            if value_key in current_data and timestamp_key in current_data:
                try:
                    value = float(current_data[value_key])
                    timestamp = current_data[timestamp_key]

                    # Apply transformations
                    value = transform(value)

                    results.append({
                        'timestamp': timestamp,
                        'recorded_at': timestamp,
                        'value': value,
                        'unit': unit
                    })
                except (ValueError, TypeError) as e:
                    api_logger.error(f"[{request_id}] Error in value processing: {str(e)}")

    api_logger.info(f"[{request_id}] Processed {len(results)} results for {data_type}")
    return results

def get_vitals_data(patient, data_type, start_date=None, end_date=None, cache_duration=300):
    """
    Get vital sign data for a patient from their connected health platform.

    This is the main high-level function used throughout the application to retrieve 
    patient health data from connected platforms. It handles platform selection,
    caching to minimize API calls, error recovery, and returns data in a consistent
    format regardless of the source platform.

    Features:
    - Intelligent caching with configurable duration
    - Automatic platform selection based on patient's connected services
    - Consistent data format across all vital sign types and platforms
    - Proper error handling and logging

    Args:
        patient (Patient): Patient object with connection information
        data_type (str): Type of data to retrieve (heart_rate, steps, etc.)
                        Can be either a string or VitalSignType enum value
        start_date (str, optional): Start date in YYYY-MM-DD format
                                   Defaults to current date if not provided
        end_date (str, optional): End date in YYYY-MM-DD format
                                 Defaults to current date if not provided
        cache_duration (int, optional): How long to keep data in cache (seconds)
                                       Defaults to 300 seconds (5 minutes)

    Returns:
        list: Processed data in standardized format:
              [{'timestamp': ISO8601, 'value': 123, 'unit': 'xyz'}, ...]
              Returns empty list if data retrieval fails or no data available

    Note:
        This function is the preferred way to access health data throughout
        the application, as it abstracts away the complexities of different
        health platforms and provides consistent caching.
    """
    # Generate a unique ID for this request
    request_id = str(uuid.uuid4())[:8]

    # Normalize the data type (convert to lowercase if it's a string)
    if isinstance(data_type, str):
        normalized_data_type = data_type.lower()
    else:
        normalized_data_type = data_type

    # Set default dates if not provided
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        api_logger.debug(f"[{request_id}] End date not provided, using today: {end_date}")

    if not start_date:
        # Default: 7 days before end date
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=7)
        start_date = start_dt.strftime('%Y-%m-%d')
        api_logger.debug(f"[{request_id}] Start date not provided, using 7 days before: {start_date}")

    # Check if we have cached data for this request
    cache_key = f"{patient.id}_{normalized_data_type}_{start_date}_{end_date}"
    if cache_key in vitals_cache:
        # Check if the cache is still valid
        cache_entry = vitals_cache[cache_key]
        cache_time = cache_entry.get('cache_time')
        if cache_time:
            cache_age = (datetime.utcnow() - cache_time).total_seconds()
            # If the cache is still valid, use the stored data
            if cache_age < cache_duration:
                api_logger.info(f"[{request_id}] Using data from cache for {normalized_data_type}, age: {cache_age:.1f}s")
                return cache_entry.get('data', [])
            else:
                api_logger.info(f"[{request_id}] Cache expired for {normalized_data_type}, age: {cache_age:.1f}s")

    # No valid cache, need to get data from the platform
    data = []

    # Check which platform the patient is connected to
    if not patient.connected_platform:
        api_logger.warning(f"[{request_id}] Patient {patient.id} not connected to any platform")
        return []

    start_time = time.time()  # To measure execution time
    try:
        if patient.connected_platform == HealthPlatform.FITBIT:
            api_logger.info(f"[{request_id}] Requesting Fitbit data: {normalized_data_type} from {start_date} to {end_date}")
            data = get_processed_fitbit_data(patient, normalized_data_type, start_date, end_date)
        elif patient.connected_platform == HealthPlatform.GOOGLE_HEALTH_CONNECT:
            # Placeholder for Google Fit implementation
            api_logger.warning(f"[{request_id}] Google Fit integration not yet implemented")
            data = []
        elif patient.connected_platform == HealthPlatform.APPLE_HEALTH:
            # Placeholder for Apple Health implementation
            api_logger.warning(f"[{request_id}] Apple Health integration not yet implemented")
            data = []
        else:
            api_logger.warning(f"[{request_id}] Unsupported platform: {patient.connected_platform}")
            data = []

        # Calculate statistics on the data
        stats = {
            "count": len(data),
            "execution_time": round(time.time() - start_time, 3)
        }

        if data and len(data) > 0:
            # Calculate min, max, avg only if we have data
            try:
                values = [item.get('value') for item in data if item.get('value') is not None]
                if values:
                    stats["min"] = min(values)
                    stats["max"] = max(values)
                    stats["avg"] = sum(values) / len(values)

                    # Get the unit of measure from the first element
                    stats["unit"] = data[0].get('unit', '')
            except Exception as stats_error:
                api_logger.error(f"[{request_id}] Error calculating statistics: {str(stats_error)}")

        # Cache the data with statistics
        vitals_cache[cache_key] = {
            'data': data,
            'cache_time': datetime.utcnow(),
            'statistics': stats,
            'source': patient.connected_platform.value
        }

        api_logger.info(f"[{request_id}] Retrieved {len(data)} data points for {normalized_data_type} in {stats['execution_time']}s")
        return data
    except Exception as e:
        api_logger.error(f"[{request_id}] Error retrieving data for patient {patient.id}, type {normalized_data_type}: {str(e)}")
        return []

def get_processed_fitbit_data(patient, data_type, start_date=None, end_date=None):
    """
    Retrieve and process Fitbit data in one consolidated function.

    This function combines the steps of retrieving raw data from Fitbit's API
    and processing it into the application's standardized format. It provides
    a convenient wrapper around get_fitbit_data() and process_fitbit_data()
    with smart defaults for date ranges and proper error handling.

    The function handles:
    - Defaulting to a 7-day range when dates are not specified
    - Converting date formats as needed
    - Retrieving the raw data from Fitbit
    - Processing the data into a standardized format
    - Error handling at each step

    Args:
        patient (Patient): Patient object with Fitbit connection information
        data_type (str): Type of data to retrieve (must match a key in FITBIT_ENDPOINTS)
        start_date (str, optional): Start date in YYYY-MM-DD format
                                   Defaults to 7 days before end_date if not provided
        end_date (str, optional): End date in YYYY-MM-DD format
                                 Defaults to current date if not provided

    Returns:
        list: Processed data in standardized format:
              [{'timestamp': ISO8601, 'value': 123, 'unit': 'xyz'}, ...]
              Returns empty list if data retrieval fails or no data available
    """
    # If dates are not specified, use default values
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    if not start_date:
        # Default: 7 days before end date
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=7)
        start_date = start_dt.strftime('%Y-%m-%d')

    # Generate a unique ID for this data request (for log tracking)
    request_id = str(uuid.uuid4())[:8]
    api_logger.info(f"[{request_id}] Data request: {data_type} for patient {patient.id} from {start_date} to {end_date}")

    # Convert data_type to lowercase if it's coming from JavaScript/frontend
    # JavaScript uses uppercase like 'HEART_RATE' while Python backend expects lowercase like 'heart_rate'
    normalized_data_type = data_type.lower() if isinstance(data_type, str) else data_type

    # Detailed mapping for all supported data types
    mapping = {
    'heart_rate': 'heart_rate',
    'steps': 'steps',
    'calories': 'calories',
    'distance': 'distance',
    'active_minutes': 'active_minutes',
    'sleep_duration': 'sleep_duration',
    'floors_climbed': 'floors_climbed',
    'elevation': 'elevation',
    'weight': 'weight',
    'activity_calories': 'activity_calories',
    'calories_bmr': 'calories_bmr',
    'minutes_sedentary': 'minutes_sedentary',
    'minutes_lightly_active': 'minutes_lightly_active',
    'minutes_fairly_active': 'minutes_fairly_active',
    'calories_in': 'calories_in',
    'water': 'water',
    'breathing_rate': 'breathing_rate',
    'oxygen_saturation': 'oxygen_saturation',
    'temperature_core': 'temperature_core',
    'temperature_skin': 'temperature_skin'
    }


    # Determine the correct API data type
    api_data_type = mapping.get(normalized_data_type, normalized_data_type)
    api_logger.debug(f"[{request_id}] Normalized data type: {normalized_data_type} -> {api_data_type}")

    # Check if the data type is supported by Fitbit
    if api_data_type not in FITBIT_ENDPOINTS:
        api_logger.error(f"[{request_id}] Data type not supported by Fitbit: {api_data_type}")
        return []

    # Multiple data retrieval strategies for greater resilience
    results = []
    error_count = 0

    # First attempt: range data with full period
    api_logger.info(f"[{request_id}] Attempt 1: Requesting range data for {api_data_type}")

    try:
        raw_data = get_fitbit_data(patient, api_data_type, start_date, end_date)
        if raw_data:
            # Process normal range data
            range_results = process_fitbit_data(raw_data, api_data_type)
            if range_results:
                results = range_results
                api_logger.info(f"[{request_id}] Retrieved {len(range_results)} range data points")
            else:
                api_logger.warning(f"[{request_id}] No range data available for the period")
        else:
            api_logger.warning(f"[{request_id}] No data received for {api_data_type}")
            error_count += 1
    except Exception as e:
        api_logger.error(f"[{request_id}] Error retrieving or processing range data: {str(e)}")
        error_count += 1

    if results:
        try:
            # Some timestamps may not have the expected format, so handle exceptions
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception as sort_error:
            api_logger.warning(f"[{request_id}] Unable to sort results: {str(sort_error)}")

    # Apply any additional transformations (e.g., unit of measure)
    try:
        endpoint_config = FITBIT_ENDPOINTS[api_data_type]
        transform_function = endpoint_config.get('value_transform', lambda x: x)
        unit = endpoint_config.get('unit', '')

        for item in results:
            # Make sure each item has the correct unit
            if 'unit' not in item:
                item['unit'] = unit

            # Add the recorded_at field if it doesn't already exist
            if 'recorded_at' not in item and 'timestamp' in item:
                item['recorded_at'] = item['timestamp']
    except Exception as transform_error:
        api_logger.error(f"[{request_id}] Error in final data transformation: {str(transform_error)}")

    api_logger.info(f"[{request_id}] Processing completed, returning {len(results)} data points for {api_data_type}")
    return results

# -------- Blueprint routes --------

@health_bp.route('/create_link/<int:patient_id>/<string:platform_name>', methods=['POST'])
@login_required
def create_link(patient_id, platform_name):
    """
    Create a connection link for a patient to connect to a health platform.

    This API endpoint generates a unique, time-limited URL that can be shared
    with a patient to authorize connection to their health platform account
    (like Fitbit). The link includes a secure UUID and platform information.
    Once created, the link can be sent to the patient via email or other means.

    The function performs several validations:
    - Verifies the patient exists
    - Ensures the requesting doctor has permission to manage this patient
    - Validates that the platform name is supported
    - Checks if the patient already has a connection to this platform

    Args:
        patient_id (int): ID of the patient in the database
        platform_name (str): Name of the platform to connect to (must match HealthPlatform enum)

    Returns:
        Response: JSON object with:
            success (bool): Whether the operation succeeded
            message (str): Description message
            link (dict): Details of the created link (if successful)
                - uuid: Unique identifier for this link
                - url: Full URL that the patient should visit
                - expires_at: ISO 8601 timestamp when the link will expire

    Status Codes:
        201: Link created successfully
        400: Invalid platform name
        403: Not authorized to manage this patient
        404: Patient not found
        409: Patient already connected to this platform
        500: Server error

    Route: /health/link
    Method: POST
    Auth: Required (Doctor)
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
    Handle the patient-facing connection flow to a health platform.

    This web endpoint presents the connection interface to patients who have
    received a link from their doctor. It displays a page explaining the
    health platform connection process and provides buttons to initiate the
    OAuth flow for the specific platform (Fitbit, Google Health Connect, etc.).

    The function:
    - Validates the provided UUID corresponds to an active, non-expired link
    - Retrieves the associated patient and platform information
    - Renders a user-friendly interface explaining what data will be shared
    - Provides platform-specific connection buttons that initiate OAuth

    Args:
        link_uuid (str): UUID of the health platform link as generated by create_link()

    Returns:
        Response: HTML page with platform connection UI or error message
                 Will redirect to OAuth provider if the user initiates connection

    Template:
        health_connect.html - Success case with connection UI
        health_connect_result.html - Error cases with appropriate message

    Route: /health/connect/<uuid>
    Method: GET
    Auth: Not required (patient-facing public URL)
    """
    # Get the link
    link = get_link_by_uuid(link_uuid)
    if not link:
        flash(_('Invalid or expired link'), 'danger')
        return render_template('health_connect_result.html', 
                              success=False,
                              message=_('The link you are trying to use is invalid or has expired'),
                              now=datetime.now())
      # Check if link is expired
    if link.is_expired():
        flash(_('This link has expired'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The link you are trying to use has expired'),
                              now=datetime.now())

    # Check if link was already used
    if link.used:
        flash(_('This link has already been used'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The link you are trying to use has already been used'),
                              now=datetime.now())

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
    Start the OAuth2 authorization flow for the specified health platform.

    This endpoint initiates the OAuth2 authorization flow when a patient clicks
    on a platform connection button. It validates the session, retrieves the
    appropriate authorization URL for the selected platform, and redirects the
    user to the platform's authorization page.

    The function handles:
    - Session validation to ensure the connection link is valid
    - Link validation to prevent expired or misused links
    - Platform-specific OAuth2 flow initiation
    - Security state parameter setup to prevent CSRF attacks

    Currently supported platforms:
    - Fitbit
    - Google Health Connect (planned)
    - Apple Health (planned)

    Args:
        platform_name (str): Name of the platform to connect to (must match HealthPlatform enum)

    Returns:
        Response: Redirect to the OAuth provider's authorization page or error page
                 if validation fails

    Route: /health/start-auth/<platform_name>
    Method: GET
    Auth: Not required (patient-facing, protected by session and link validation)
    """# Check if we have a link UUID in the session
    link_uuid = session.get('link_uuid')
    if not link_uuid:
        flash(_('Invalid session'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('Your session is invalid or has expired'),
                              now=datetime.now())

    # Get the link
    link = get_link_by_uuid(link_uuid)

    if not link or link.is_expired() or link.used:
        flash(_('Invalid or expired link'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The link you are trying to use is invalid or has expired'),
                              now=datetime.now())
      # Generate the authorization URL based on the platform
    if platform_name == 'fitbit':
        auth_url = get_fitbit_authorization_url(link_uuid)
        return redirect(auth_url)
    else:
        flash(_('Unsupported platform'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The platform you selected is not supported'),
                              now=datetime.now())

@health_bp.route('/oauth_callback')
def oauth_callback():
    """
    Handle the callback from OAuth2 providers after patient authorization.

    This endpoint processes the response from health platforms after a patient
    has authorized or denied access to their data. It handles both successful
    authorizations (receiving an authorization code) and errors/rejections.

    The complete OAuth2 flow involves:
    1. Getting the authorization code from the redirect
    2. Exchanging the code for access and refresh tokens
    3. Storing the tokens securely in the patient record
    4. Marking the connection as active in the system
    5. Recording the connection event in the audit log

    Error handling covers:
    - User rejections of authorization
    - Missing or invalid state parameters
    - Failed token exchanges
    - Database errors during token storage

    Args:
        None - Parameters are received via query string
               - code: Authorization code from OAuth provider
               - state: Link UUID for verification
               - error/error_description: Details if auth failed

    Returns:
        Response: HTML page with success or error message to display to the patient

    Route: /health/oauth-callback
    Method: GET
    Auth: Not required (patient-facing callback)
    """
    # Check for error parameter
    error = request.args.get('error')
    if error:
        flash(_('Authentication failed: %(error)s', error=error), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The health platform authentication failed'),
                              now=datetime.now())

    # Get the authorization code
    code = request.args.get('code')
    if not code:
        flash(_('No authorization code received'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('No authorization code was received from the health platform'),
                              now=datetime.now())
      # Get the state (link UUID)
    state = request.args.get('state')
    if not state:
        flash(_('Invalid state parameter'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The state parameter is missing from the callback'),
                              now=datetime.now())

    # Get the link
    link = get_link_by_uuid(state)

    if not link:
        flash(_('Invalid link'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The link is invalid'),
                              now=datetime.now())
      # Check if link is expired
    if link.is_expired():
        flash(_('This link has expired'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The link has expired'),
                              now=datetime.now())

    # Check if link was already used
    if link.used:
        flash(_('This link has already been used'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The link has already been used'),
                              now=datetime.now())

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
                                  message=_('Your Fitbit account has been successfully connected'),
                                  now=datetime.now())
        else:
            flash(_('Failed to save token data'), 'danger')
            return render_template('health_connect_result.html',
                                  success=False,
                                  message=_('Failed to save the token data'),
                                  now=datetime.now())
    else:
        flash(_('Unsupported platform'), 'danger')
        return render_template('health_connect_result.html',
                              success=False,
                              message=_('The platform is not supported'),
                              now=datetime.now())

@health_bp.route('/check_connection/<int:patient_id>')
@login_required
def check_connection(patient_id):
    """
    API endpoint to check if a patient is connected to a health platform.

    This endpoint allows doctors to verify if a patient has an active connection
    to any health platform and retrieve the connection details. It's commonly
    used by the frontend to determine if health data can be fetched and when
    displaying connection status indicators.

    The response includes:
    - Connection status (true/false)
    - Platform name if connected
    - Connection timestamp
    - Token expiration information

    For disconnected patients, it provides information on why no connection
    exists (never connected, expired tokens, manually disconnected).

    Args:
        patient_id (int): ID of the patient to check

    Returns:
        Response: JSON object with:
            connected (bool): Whether the patient is connected
            platform (str, optional): Name of the connected platform if any
            connected_since (str, optional): ISO timestamp of when connection was established
            expires_at (str, optional): ISO timestamp of when the token expires
            message (str): Descriptive message about the connection status

    Status Codes:
        200: Request processed successfully
        403: Not authorized to view this patient's data
        404: Patient not found
        500: Server error

    Route: /health/connection/<patient_id>
    Method: GET
    Auth: Required (Doctor)
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
    API endpoint to disconnect a patient from a health platform.

    This endpoint allows doctors to remove a patient's connection to a health
    platform. It revokes the OAuth tokens and clears connection data from the
    patient record. This is useful when:
    - A patient requests disconnection
    - The patient changes accounts
    - Privacy concerns require removing access
    - Repeated token refresh failures indicate an invalid connection

    The function:
    - Validates doctor authorization for the patient
    - Verifies the platform is valid
    - Checks if the patient is actually connected to the specified platform
    - Clears all token and connection data
    - Adds an audit log entry for the disconnection

    Args:
        patient_id (int): ID of the patient to disconnect
        platform (str): Name of the platform to disconnect (must match HealthPlatform enum)

    Returns:
        Response: JSON object with:
            success (bool): Whether the disconnection was successful
            message (str): Description message about the result

    Status Codes:
        200: Disconnection successful
        400: Invalid platform name
        403: Not authorized to manage this patient's connections
        404: Patient not found or not connected to specified platform
        500: Server error

    Route: /health/disconnect/<patient_id>/<platform>
    Method: POST
    Auth: Required (Doctor)
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
    API endpoint to retrieve health data from connected platforms.

    This endpoint provides a unified interface for the frontend to request health
    data of various types for a patient. It's primarily used for AJAX requests from
    the vitals monitoring page to populate charts and data tables. The function
    handles platform selection, permission checking, and returns data in a consistent
    format regardless of the source platform.

    The endpoint supports date range filtering and leverages the caching system
    to minimize API calls to health platforms. All data is returned in a standardized
    format suitable for direct use in frontend visualizations.

    Args:
        data_type (str): Type of data to retrieve (must be a valid VitalSignType value)
        patient_id (int): ID of the patient to get data for

    Query Parameters:
        start_date (str, optional): Start date in YYYY-MM-DD format
                                   Defaults to 7 days before end_date
        end_date (str, optional): End date in YYYY-MM-DD format
                                 Defaults to current date

    Returns:
        Response: JSON object with:
            success (bool): Whether the data retrieval was successful
            data (list): Array of data points in format:
                  [{'timestamp': ISO8601, 'value': numeric, 'unit': string}, ...]
            message (str, optional): Error description if success is false

    Status Codes:
        200: Data retrieved successfully
        403: Not authorized to access this patient's data
        404: Patient not found
        500: Server error or health platform error

    Route: /health/data/<data_type>/<patient_id>
    Method: GET
    Auth: Required (Doctor)
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