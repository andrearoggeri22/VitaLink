"""
Configuration file for health platform integrations
Contains API keys, credentials, and other settings needed for integrating with external health platforms
"""

import os

# Fitbit API configuration
FITBIT_CONFIG = {
    'client_id': os.environ.get('FITBIT_CLIENT_ID', '23Q88S'),
    'client_secret': os.environ.get('FITBIT_CLIENT_SECRET', '255d300e5671fe7667ade5d12a83ee85'),
    'redirect_uri': os.environ.get('FITBIT_REDIRECT_URI', 'http://localhost:5000/health/oauth_callback'),
    'authorize_url': 'https://www.fitbit.com/oauth2/authorize',
    'token_url': 'https://api.fitbit.com/oauth2/token',
    'scope': 'activity heartrate sleep weight profile',
    'api_base_url': 'https://api.fitbit.com'
}

# Mapping of Fitbit endpoints to VitalSignType
FITBIT_ENDPOINTS = {
    'heart_rate': {
        'endpoint': '/1/user/-/activities/heart/date/today/1d/1min.json',
        'response_key': 'activities-heart-intraday.dataset',
        'value_key': 'value',
        'timestamp_key': 'time',
        'timestamp_format': '%H:%M:%S',
        'unit': 'bpm'
    },
    'steps': {
        'endpoint': '/1/user/-/activities/steps/date/today/1w.json',
        'response_key': 'activities-steps',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'steps'
    },
    'calories': {
        'endpoint': '/1/user/-/activities/calories/date/today/1w.json',
        'response_key': 'activities-calories',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'kcal'
    },
    'distance': {
        'endpoint': '/1/user/-/activities/distance/date/today/1w.json',
        'response_key': 'activities-distance',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'km'
    },
    'active_minutes': {
        'endpoint': '/1/user/-/activities/minutesActive/date/today/1w.json',
        'response_key': 'activities-minutesActive',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'min'
    },
    'sleep_duration': {
        'endpoint': '/1.2/user/-/sleep/date/today.json',
        'response_key': 'sleep',
        'value_key': 'minutesAsleep',
        'timestamp_key': 'startTime',
        'unit': 'min',
        'transform': lambda x: x / 60  # convert minutes to hours
    },
    'floors_climbed': {
        'endpoint': '/1/user/-/activities/floors/date/today/1w.json',
        'response_key': 'activities-floors',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'floors'
    },
    'weight': {
        'endpoint': '/1/user/-/body/log/weight/date/today/1m.json',
        'response_key': 'weight',
        'value_key': 'weight',
        'timestamp_key': 'date',
        'unit': 'kg'
    }
}