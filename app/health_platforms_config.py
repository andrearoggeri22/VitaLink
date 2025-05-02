"""
Health Platforms Configuration Module.

This module contains configuration settings for integrations with external health platforms
like Fitbit, Google Fit, Apple Health, etc. It defines:

1. API endpoints, credentials and authentication settings
2. Data mapping from external platforms to internal data models
3. Configuration for data retrieval, processing, and visualization
4. Rate limiting and caching parameters

Environment variables are used for sensitive information like client IDs and secrets.
"""

import os

# Fitbit API configuration
FITBIT_CONFIG = {
    'client_id':
    os.environ["FITBIT_CLIENT_ID"],
    'client_secret':
    os.environ["FITBIT_CLIENT_SECRET"],
    'redirect_uri': 
        os.environ.get(
            "FITBIT_REDIRECT_URI",
            "http://localhost:5000/health/oauth_callback",
        ),
    'authorize_url':
    'https://www.fitbit.com/oauth2/authorize',
    'token_url':
    'https://api.fitbit.com/oauth2/token',
    'scope':
    'activity heartrate sleep weight profile electrocardiogram cardio_fitness irregular_rhythm_notifications location nutrition oxygen_saturation respiratory_rate temperature',
    'api_base_url':
    'https://api.fitbit.com'
}

# Mapping of Fitbit endpoints to VitalSignType
FITBIT_ENDPOINTS = {    
    'heart_rate': {
        'endpoint': '/1/user/-/activities/heart/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/heart/date',
        'daily_endpoint': '/1/user/-/activities/heart/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/heart/date/{start}/{end}.json',
        'max_range_days': 30,  # Limiti imposti da Fitbit
        'response_key': 'activities-heart',
        'value_key': 'value.restingHeartRate',
        'timestamp_key': 'dateTime',
        'unit': 'bpm',
        'oauth_scope': 'heartrate',
        'value_transform': lambda x: x,
        'chart_color': '#FF5252'
    },    
    'steps': {
        'endpoint': '/1/user/-/activities/steps/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/steps/date',
        'daily_endpoint': '/1/user/-/activities/steps/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/steps/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-steps',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'steps',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#2196F3'
    },    
    'calories': {
        'endpoint': '/1/user/-/activities/calories/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/calories/date',
        'daily_endpoint': '/1/user/-/activities/calories/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/calories/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-calories',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'kcal',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#FF9800'
    },    
    'distance': {
        'endpoint': '/1/user/-/activities/distance/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/distance/date',
        'daily_endpoint': '/1/user/-/activities/distance/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/distance/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-distance',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'km',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#4CAF50'
    },
    'active_minutes': {
        'endpoint': '/1/user/-/activities/minutesVeryActive/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/minutesVeryActive/date',
        'daily_endpoint': '/1/user/-/activities/minutesVeryActive/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/minutesVeryActive/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-minutesVeryActive',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'min',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#9C27B0'
    },
    'sleep_duration': {
        'endpoint': '/1.2/user/-/sleep/date/today.json',
        'base_endpoint': '/1.2/user/-/sleep/date',
        'daily_endpoint': '/1.2/user/-/sleep/date/{date}.json',
        'range_endpoint': '/1.2/user/-/sleep/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'sleep',
        'value_key': 'minutesAsleep',
        'timestamp_key': 'startTime',
        'unit': 'min',
        'oauth_scope': 'sleep',
        'value_transform': lambda x: x / 60,  # convert minutes to hours
        'chart_color': '#3F51B5'
    },    
    'floors_climbed': {
        'endpoint': '/1/user/-/activities/floors/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/floors/date',
        'daily_endpoint': '/1/user/-/activities/floors/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/floors/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-floors',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'floors',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#795548'
    },    
    'elevation': {
        'endpoint': '/1/user/-/activities/elevation/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/elevation/date',
        'daily_endpoint': '/1/user/-/activities/elevation/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/elevation/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-elevation',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'm',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#795548'
    },
    'weight': {
        'endpoint': '/1/user/-/body/log/weight/date/today/1w.json',
        'base_endpoint': '/1/user/-/body/log/weight/date',
        'daily_endpoint': '/1/user/-/body/log/weight/date/{date}.json',
        'range_endpoint': '/1/user/-/body/log/weight/date/{start}/{end}.json',
        'max_range_days': 31,
        'response_key': 'weight',
        'value_key': 'weight',
        'timestamp_key': 'date',
        'unit': 'kg',
        'oauth_scope': 'weight',
        'value_transform': lambda x: x,
        'chart_color': '#607D8B'
    },
    'activity_calories': {
        'endpoint': '/1/user/-/activities/activityCalories/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/activityCalories/date',
        'daily_endpoint': '/1/user/-/activities/activityCalories/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/activityCalories/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-activityCalories',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'kcal',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#FF5722'
    },
    'calories_bmr': {
        'endpoint': '/1/user/-/activities/caloriesBMR/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/caloriesBMR/date',
        'daily_endpoint': '/1/user/-/activities/caloriesBMR/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/caloriesBMR/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-caloriesBMR',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'kcal',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#FF5722'
    },
    'minutes_sedentary': {
        'endpoint': '/1/user/-/activities/minutesSedentary/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/minutesSedentary/date',
        'daily_endpoint': '/1/user/-/activities/minutesSedentary/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/minutesSedentary/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-minutesSedentary',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'min',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#9E9E9E'
    },
    'minutes_lightly_active': {
        'endpoint': '/1/user/-/activities/minutesLightlyActive/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/minutesLightlyActive/date',
        'daily_endpoint': '/1/user/-/activities/minutesLightlyActive/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/minutesLightlyActive/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-minutesLightlyActive',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'min',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#8BC34A'
    },
    'minutes_fairly_active': {
        'endpoint': '/1/user/-/activities/minutesFairlyActive/date/today/1w.json',
        'base_endpoint': '/1/user/-/activities/minutesFairlyActive/date',
        'daily_endpoint': '/1/user/-/activities/minutesFairlyActive/date/{date}/1d.json',
        'range_endpoint': '/1/user/-/activities/minutesFairlyActive/date/{start}/{end}.json',
        'max_range_days': 100,
        'response_key': 'activities-minutesFairlyActive',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'min',
        'oauth_scope': 'activity',
        'value_transform': lambda x: x,
        'chart_color': '#FFC107'
    },
    'calories_in': {
        'endpoint': '/1/user/-/foods/log/caloriesIn/date/today/1w.json',
        'base_endpoint': '/1/user/-/foods/log/caloriesIn/date',
        'daily_endpoint': '/1/user/-/foods/log/caloriesIn/date/{date}.json',
        'range_endpoint': '/1/user/-/foods/log/caloriesIn/date/{start}/{end}.json',
        'max_range_days': 365,
        'response_key': 'foods-log-caloriesIn',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'kcal',
        'oauth_scope': 'nutrition',
        'value_transform': lambda x: x,
        'chart_color': '#F44336'
    },
    'water': {
        'endpoint': '/1/user/-/foods/log/water/date/today/1w.json',
        'base_endpoint': '/1/user/-/foods/log/water/date',
        'daily_endpoint': '/1/user/-/foods/log/water/date/{date}.json',
        'range_endpoint': '/1/user/-/foods/log/water/date/{start}/{end}.json',
        'max_range_days': 365,
        'response_key': 'foods-log-water',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': 'ml',
        'oauth_scope': 'nutrition',
        'value_transform': lambda x: x,
        'chart_color': '#03A9F4'
    },
    'breathing_rate': {
        'endpoint': '/1/user/-/br/date/today/1w.json',
        'base_endpoint': '/1/user/-/br/date',
        'daily_endpoint': '/1/user/-/br/date/{date}.json',
        'range_endpoint': '/1/user/-/br/date/{start}/{end}.json',
        'max_range_days': 30,
        'response_key': 'br',
        'value_key': 'value.breathingRate',
        'timestamp_key': 'dateTime',
        'unit': 'resp/min',
        'oauth_scope': 'respiratory_rate',
        'value_transform': lambda x: x,
        'chart_color': '#00BCD4'
    },
    'oxygen_saturation': {
        'endpoint': '/1/user/-/spo2/date/today/1w.json',
        'base_endpoint': '/1/user/-/spo2/date',
        'daily_endpoint': '/1/user/-/spo2/date/{date}.json',
        'range_endpoint': '/1/user/-/spo2/date/{start}/{end}.json',
        'max_range_days': 30,
        'response_key': 'spo2',
        'value_key': 'value.avg',
        'timestamp_key': 'dateTime',
        'unit': '%',
        'oauth_scope': 'oxygen_saturation',
        'value_transform': lambda x: x,
        'chart_color': '#3F51B5'
    },
    'temperature_core': {
        'endpoint': '/1/user/-/temp/core/date/today/1w.json',
        'base_endpoint': '/1/user/-/temp/core/date',
        'daily_endpoint': '/1/user/-/temp/core/date/{date}.json',
        'range_endpoint': '/1/user/-/temp/core/date/{start}/{end}.json',
        'max_range_days': 30,
        'response_key': 'tempCore',
        'value_key': 'value',
        'timestamp_key': 'dateTime',
        'unit': '°C',
        'oauth_scope': 'temperature',
        'value_transform': lambda x: x,
        'chart_color': '#3F51B5'
    },
    'temperature_skin': {
        'endpoint': '/1/user/-/temp/skin/date/today/1w.json',
        'base_endpoint': '/1/user/-/temp/skin/date',
        'daily_endpoint': '/1/user/-/temp/skin/date/{date}.json',
        'range_endpoint': '/1/user/-/temp/skin/date/{start}/{end}.json',
        'max_range_days': 30,
        'response_key': 'tempSkin',
        'value_key': 'value.nightlyRelative',
        'timestamp_key': 'dateTime',
        'unit': '°C',
        'oauth_scope': 'temperature',
        'value_transform': lambda x: x,
        'chart_color': '#3F51B5'
    }
}
