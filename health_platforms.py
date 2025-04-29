"""
Health platforms integration module
Provides functionality to connect to and retrieve data from various health platforms
"""

import os
import uuid
import json
import base64
import logging
import requests
import time
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

# Define cache for vitals data to avoid unnecessary API calls
# Struttura: {
#   'cache_key': {
#     'data': [...],                 # Dati effettivi
#     'cache_time': datetime,        # Quando i dati sono stati memorizzati
#     'request_params': {...},       # Parametri usati nella richiesta (per debug)
#     'api_calls': 0                 # Conteggio chiamate all'API per questa cache key
#   }  
# }
vitals_cache = {}

# Cache per la gestione dei rate limit
# Struttura: {
#  'last_reset': datetime,           # Ultima volta che il contatore è stato azzerato
#  'calls': 0,                       # Contatore delle chiamate
#  'hourly_limit': 150,              # Limite di chiamate orarie (rate limit Fitbit)
#  'retry_after': None               # Da quale ora possiamo riprendere le chiamate
# }
api_rate_limit = {
    'last_reset': datetime.utcnow(),
    'calls': 0,
    'hourly_limit': 150,
    'retry_after': None
}

# Configurazione delle opzioni di logging
logger = logging.getLogger(__name__)

# Aggiungi un handler specifico per le API Fitbit
api_logger = logging.getLogger('fitbit_api')
api_logger.setLevel(logging.DEBUG)

# Crea un file handler per il logging dettagliato
try:
    api_file_handler = logging.FileHandler('fitbit_api.log')
    api_file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    api_file_handler.setFormatter(formatter)
    api_logger.addHandler(api_file_handler)
except Exception as e:
    logger.error(f"Impossibile creare il file di log per le API Fitbit: {str(e)}")

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

def check_rate_limit():
    """
    Verifica se abbiamo raggiunto il rate limit dell'API Fitbit
    
    Returns:
        bool: True se possiamo fare richieste, False altrimenti
    """
    global api_rate_limit
    
    now = datetime.utcnow()
    
    # Se c'è un retry_after impostato e non è ancora passato, blocca le richieste
    if api_rate_limit['retry_after'] and now < api_rate_limit['retry_after']:
        wait_seconds = (api_rate_limit['retry_after'] - now).total_seconds()
        api_logger.warning(f"Rate limit attivo, attendere {wait_seconds:.1f} secondi.")
        return False
    
    # Se è passata un'ora dall'ultimo reset, azzera il contatore
    if (now - api_rate_limit['last_reset']).total_seconds() >= 3600:
        api_rate_limit['last_reset'] = now
        api_rate_limit['calls'] = 0
        api_logger.info("Contatore rate limit azzerato dopo 1 ora.")
    
    # Verifica se abbiamo superato il limite orario
    if api_rate_limit['calls'] >= api_rate_limit['hourly_limit']:
        api_rate_limit['retry_after'] = api_rate_limit['last_reset'] + timedelta(hours=1)
        api_logger.warning(f"Rate limit raggiunto ({api_rate_limit['calls']} chiamate). "
                           f"Riprova dopo {api_rate_limit['retry_after'].strftime('%H:%M:%S')}")
        return False
    
    return True

def increment_api_call_counter(response=None):
    """
    Incrementa il contatore delle chiamate API e gestisce eventuali rate limit
    
    Args:
        response: Risposta dell'API per controllare il rate limit
    """
    global api_rate_limit
    
    api_rate_limit['calls'] += 1
    
    # Se la risposta contiene headers relativi al rate limit, aggiorniamo i nostri limiti
    if response and response.status_code == 429:
        # Otteni il valore di Retry-After se presente
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                seconds = int(retry_after)
                api_rate_limit['retry_after'] = datetime.utcnow() + timedelta(seconds=seconds)
                api_logger.warning(f"Rate limit raggiunto. Retry-After: {seconds} secondi.")
            except ValueError:
                # Se non è un intero, assume che sia una data RFC1123
                api_rate_limit['retry_after'] = datetime.utcnow() + timedelta(hours=1)
                api_logger.warning("Rate limit raggiunto. Attesa di 1 ora.")
        else:
            # Se non c'è Retry-After, attendi 1 ora per sicurezza
            api_rate_limit['retry_after'] = datetime.utcnow() + timedelta(hours=1)
            api_logger.warning("Rate limit raggiunto. Attesa di 1 ora.")

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
    # Verifica se abbiamo raggiunto il rate limit
    if not check_rate_limit():
        api_logger.warning(f"Rate limit attivo, richiesta bloccata: {data_type} per il paziente {patient.id}")
        return None
    
    if data_type not in FITBIT_ENDPOINTS:
        api_logger.error(f"Tipo di dati Fitbit non supportato: {data_type}")
        return None
    
    access_token = ensure_fresh_token(patient)
    if not access_token:
        api_logger.error(f"Token di accesso non disponibile per il paziente {patient.id}")
        return None
    
    endpoint_config = FITBIT_ENDPOINTS[data_type]
    
    # Genera il log request ID univoco per tracciare questa specifica richiesta
    request_id = str(uuid.uuid4())[:8]
    
    # Costruisci l'endpoint appropriato in base alle date e al tipo di dati
    if start_date and end_date:
        # Calcola la differenza di giorni tra le date per verificare se è all'interno dei limiti di Fitbit
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days_diff = (end_dt - start_dt).days + 1
            
            # Verifica se l'intervallo supera il numero massimo di giorni per questo tipo di dati
            max_range = endpoint_config.get('max_range_days', 31)
            
            if days_diff > max_range:
                api_logger.warning(f"[{request_id}] Intervallo di {days_diff} giorni supera il limite di {max_range} per {data_type}. "
                                 f"Limitazione a {max_range} giorni a partire da {end_date}.")
                # Limitiamo l'intervallo al massimo consentito, partendo dalla data di fine
                start_date = (end_dt - timedelta(days=max_range-1)).strftime('%Y-%m-%d')
                api_logger.info(f"[{request_id}] Intervallo modificato: {start_date} - {end_date}")
        except ValueError as e:
            api_logger.error(f"[{request_id}] Errore nel formato delle date: {str(e)}")
            return None
        
        # Utilizzo dell'endpoint di range specifico per questo tipo di dati
        if 'range_endpoint' in endpoint_config:
            endpoint = endpoint_config['range_endpoint'].format(start=start_date, end=end_date)
            api_logger.info(f"[{request_id}] Utilizzo endpoint range per {data_type}: {endpoint}")
        else:
            # Fallback al formato generico se non è specificato un range_endpoint
            base = endpoint_config.get('base_endpoint', '')
            endpoint = f"{base}/{start_date}/{end_date}.json"
            api_logger.info(f"[{request_id}] Utilizzo endpoint generico per {data_type}: {endpoint}")
    else:
        # Se non vengono fornite date, usiamo l'endpoint predefinito
        endpoint = endpoint_config['endpoint']
        api_logger.info(f"[{request_id}] Utilizzo endpoint predefinito per {data_type}: {endpoint}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept-Language': 'it_IT'  # Richiedi i dati in formato italiano
    }
    
    api_logger.debug(f"[{request_id}] Chiamata API Fitbit: {endpoint}")
    
    try:
        # Effettua la chiamata API
        response = requests.get(
            f"{FITBIT_CONFIG['api_base_url']}{endpoint}",
            headers=headers
        )
        
        # Incrementa il contatore delle chiamate API
        increment_api_call_counter(response)
        
        if response.status_code == 200:
            data = response.json()
            api_logger.info(f"[{request_id}] Dati ricevuti con successo per {data_type}")
            
            # Log dettagliato per debug (solo in modalità debug)
            if api_logger.isEnabledFor(logging.DEBUG):
                truncated_data = str(data)[:1000] + "..." if len(str(data)) > 1000 else str(data)
                api_logger.debug(f"[{request_id}] Risposta: {truncated_data}")
            
            return data
        elif response.status_code == 429:
            # Rate limit raggiunto
            retry_after = response.headers.get('Retry-After', '3600')
            api_logger.warning(f"[{request_id}] Rate limit raggiunto. Retry-After: {retry_after}")
            return None
        else:
            api_logger.error(f"[{request_id}] Errore recupero dati: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        api_logger.error(f"[{request_id}] Eccezione durante il recupero dati: {str(e)}")
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
    request_id = str(uuid.uuid4())[:8]  # ID per tracciamento nel log
    
    if not data or data_type not in FITBIT_ENDPOINTS:
        api_logger.warning(f"[{request_id}] Nessun dato per l'elaborazione o tipo di dati non supportato: {data_type}")
        return []
    
    endpoint_config = FITBIT_ENDPOINTS[data_type]
    response_key = endpoint_config['response_key']
    value_key = endpoint_config['value_key']
    timestamp_key = endpoint_config['timestamp_key']
    unit = endpoint_config.get('unit', '')
    transform = endpoint_config.get('value_transform', lambda x: x)  # Default identity function
    
    api_logger.info(f"[{request_id}] Elaborazione dati {data_type}, risposta con chiave {response_key}")
    
    # Gestione speciale per la frequenza cardiaca
    if data_type == 'heart_rate' and 'activities-heart' in data:
        # Elaborazione speciale per le risposte della frequenza cardiaca
        heart_results = []
        
        for heart_data in data['activities-heart']:
            if 'dateTime' in heart_data and 'value' in heart_data and isinstance(heart_data['value'], dict):
                timestamp = heart_data['dateTime']
                heart_value = None
                value_type = None
                
                # Prima verifichiamo se c'è il valore di frequenza cardiaca a riposo
                if 'restingHeartRate' in heart_data['value']:
                    heart_value = heart_data['value']['restingHeartRate']
                    value_type = 'resting'
                    api_logger.info(f"[{request_id}] Trovato valore di frequenza cardiaca a riposo: {heart_value} per {timestamp}")
                # Se non c'è, calcoliamo una media dalle zone di frequenza cardiaca
                elif 'heartRateZones' in heart_data['value'] and heart_data['value']['heartRateZones']:
                    zones = heart_data['value']['heartRateZones']
                    zone_values = []
                    
                    for zone in zones:
                        if 'min' in zone and 'max' in zone:
                            # Calcola la media di ogni zona
                            zone_avg = (float(zone['min']) + float(zone['max'])) / 2
                            zone_values.append(zone_avg)
                    
                    if zone_values:
                        heart_value = sum(zone_values) / len(zone_values)
                        value_type = 'zone_avg'
                        api_logger.info(f"[{request_id}] Calcolato valore medio dalle zone: {heart_value} per {timestamp}")
                
                if heart_value is not None:
                    heart_results.append({
                        'timestamp': timestamp,
                        'recorded_at': timestamp,
                        'value': float(heart_value),
                        'unit': unit,
                        'type': value_type
                    })
        
        if heart_results:
            api_logger.info(f"[{request_id}] Elaborati {len(heart_results)} valori di frequenza cardiaca")
            return heart_results
    
    # Elaborazione standard
    # Estrai i dati dalla risposta in base alla chiave di risposta
    if response_key in data:
        current_data = data[response_key]
    else:
        api_logger.error(f"[{request_id}] Chiave di risposta {response_key} non trovata nei dati")
        return []
    
    # Gestione di diverse strutture di dati
    results = []
    
    # Funzione di supporto per estrarre valori nidificati
    def extract_nested_value(obj, path):
        """Estrai un valore nidificato da un oggetto in base a un percorso."""
        if not path or not isinstance(obj, dict):
            return None
        
        key = path[0]
        if key not in obj:
            return None
        
        if len(path) == 1:
            return obj[key]
        
        return extract_nested_value(obj[key], path[1:])
    
    # Gestione dei valori nidificati (es: value.restingHeartRate, value.avg)
    if '.' in value_key:
        value_path = value_key.split('.')
        
        if isinstance(current_data, list):
            # Elabora dati in formato lista
            for item in current_data:
                if timestamp_key in item:
                    try:
                        nested_value = extract_nested_value(item, value_path)
                        if nested_value is not None:
                            value = float(nested_value)
                            timestamp = item[timestamp_key]
                            
                            # Applica trasformazioni
                            value = transform(value)
                            
                            results.append({
                                'timestamp': timestamp,
                                'recorded_at': timestamp,
                                'value': value,
                                'unit': unit
                            })
                    except (ValueError, TypeError) as e:
                        api_logger.error(f"[{request_id}] Errore durante l'elaborazione del valore: {str(e)}")
        
        elif isinstance(current_data, dict):
            # Elabora dati in formato dizionario
            if timestamp_key in current_data:
                try:
                    nested_value = extract_nested_value(current_data, value_path)
                    if nested_value is not None:
                        value = float(nested_value)
                        timestamp = current_data[timestamp_key]
                        
                        # Applica trasformazioni
                        value = transform(value)
                        
                        results.append({
                            'timestamp': timestamp,
                            'recorded_at': timestamp,
                            'value': value,
                            'unit': unit
                        })
                except (ValueError, TypeError) as e:
                    api_logger.error(f"[{request_id}] Errore durante l'elaborazione del valore: {str(e)}")
    else:
        # Gestione standard dei dati (chiave valore semplice)
        if isinstance(current_data, list):
            # Elabora formato lista
            for item in current_data:
                if value_key in item and timestamp_key in item:
                    try:
                        value = float(item[value_key])
                        timestamp = item[timestamp_key]
                        
                        # Applica trasformazioni
                        value = transform(value)
                        
                        results.append({
                            'timestamp': timestamp,
                            'recorded_at': timestamp,
                            'value': value,
                            'unit': unit
                        })
                    except (ValueError, TypeError) as e:
                        api_logger.error(f"[{request_id}] Errore nell'elaborazione del valore: {str(e)}")
        
        elif isinstance(current_data, dict):
            # Elabora formato dizionario singolo
            if value_key in current_data and timestamp_key in current_data:
                try:
                    value = float(current_data[value_key])
                    timestamp = current_data[timestamp_key]
                    
                    # Applica trasformazioni
                    value = transform(value)
                    
                    results.append({
                        'timestamp': timestamp,
                        'recorded_at': timestamp,
                        'value': value,
                        'unit': unit
                    })
                except (ValueError, TypeError) as e:
                    api_logger.error(f"[{request_id}] Errore nell'elaborazione del valore: {str(e)}")
    
    api_logger.info(f"[{request_id}] Elaborati {len(results)} risultati per {data_type}")
    return results

def get_vitals_data(patient, data_type, start_date=None, end_date=None, cache_duration=300):
    """
    Get vital sign data for a patient from their connected health platform
    This is the main function used by reports and charts to get vital sign data
    
    Args:
        patient (Patient): Patient object
        data_type (str): Type of data to retrieve (heart_rate, steps, etc.)
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        cache_duration (int, optional): Duration in seconds to keep data in cache
        
    Returns:
        list: Processed data in format [{'timestamp': ISO8601, 'value': 123, 'unit': 'xyz'}, ...]
    """
    # Genera un ID univoco per questa richiesta
    request_id = str(uuid.uuid4())[:8]
    
    # Normalizza il tipo di dato (converti in minuscolo se è una stringa)
    if isinstance(data_type, str):
        normalized_data_type = data_type.lower()
    else:
        normalized_data_type = data_type
    
    # Imposta date predefinite se non fornite
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        api_logger.debug(f"[{request_id}] Data fine non fornita, usando oggi: {end_date}")
    
    if not start_date:
        # Default: 7 giorni prima della data di fine
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=7)
        start_date = start_dt.strftime('%Y-%m-%d')
        api_logger.debug(f"[{request_id}] Data inizio non fornita, usando 7 giorni prima: {start_date}")
    
    # Check if we have cached data for this request
    cache_key = f"{patient.id}_{normalized_data_type}_{start_date}_{end_date}"
    if cache_key in vitals_cache:
        # Check if the cache is still valid
        cache_entry = vitals_cache[cache_key]
        cache_time = cache_entry.get('cache_time')
        if cache_time:
            cache_age = (datetime.utcnow() - cache_time).total_seconds()
            # Se la cache è ancora valida, usiamo i dati memorizzati
            if cache_age < cache_duration:
                api_logger.info(f"[{request_id}] Usando dati dalla cache per {normalized_data_type}, età: {cache_age:.1f}s")
                return cache_entry.get('data', [])
            else:
                api_logger.info(f"[{request_id}] Cache scaduta per {normalized_data_type}, età: {cache_age:.1f}s")
    
    # No valid cache, need to get data from the platform
    data = []
    
    # Check which platform the patient is connected to
    if not patient.connected_platform:
        api_logger.warning(f"[{request_id}] Paziente {patient.id} non collegato a nessuna piattaforma")
        return []
    
    start_time = time.time()  # Per misurare il tempo di esecuzione
    try:
        if patient.connected_platform == HealthPlatform.FITBIT:
            api_logger.info(f"[{request_id}] Richiesta dati Fitbit: {normalized_data_type} dal {start_date} al {end_date}")
            data = get_processed_fitbit_data(patient, normalized_data_type, start_date, end_date)
        elif patient.connected_platform == HealthPlatform.GOOGLE_HEALTH_CONNECT:
            # Placeholder for Google Fit implementation
            api_logger.warning(f"[{request_id}] Integrazione Google Fit non ancora implementata")
            data = []
        elif patient.connected_platform == HealthPlatform.APPLE_HEALTH:
            # Placeholder for Apple Health implementation
            api_logger.warning(f"[{request_id}] Integrazione Apple Health non ancora implementata")
            data = []
        else:
            api_logger.warning(f"[{request_id}] Piattaforma non supportata: {patient.connected_platform}")
            data = []
        
        # Calcola statistiche sui dati
        stats = {
            "count": len(data),
            "execution_time": round(time.time() - start_time, 3)
        }
        
        if data and len(data) > 0:
            # Calcola min, max, avg solo se abbiamo dati
            try:
                values = [item.get('value') for item in data if item.get('value') is not None]
                if values:
                    stats["min"] = min(values)
                    stats["max"] = max(values)
                    stats["avg"] = sum(values) / len(values)
                    
                    # Ottieni l'unità di misura dal primo elemento
                    stats["unit"] = data[0].get('unit', '')
            except Exception as stats_error:
                api_logger.error(f"[{request_id}] Errore nel calcolo delle statistiche: {str(stats_error)}")
        
        # Cache the data with statistics
        vitals_cache[cache_key] = {
            'data': data,
            'cache_time': datetime.utcnow(),
            'statistics': stats,
            'source': patient.connected_platform.value
        }
        
        api_logger.info(f"[{request_id}] Recuperati {len(data)} punti dati per {normalized_data_type} in {stats['execution_time']}s")
        return data
    except Exception as e:
        api_logger.error(f"[{request_id}] Errore nel recupero dati per paziente {patient.id}, tipo {normalized_data_type}: {str(e)}")
        return []

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
    # Se le date non sono specificate, usa valori predefiniti
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    if not start_date:
        # Default: 7 giorni prima della data di fine
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=7)
        start_date = start_dt.strftime('%Y-%m-%d')
    
    # Genera un ID univoco per questa richiesta di dati (per tracciamento nel log)
    request_id = str(uuid.uuid4())[:8]
    api_logger.info(f"[{request_id}] Richiesta dati: {data_type} per paziente {patient.id} dal {start_date} al {end_date}")
    
    # Convert data_type to lowercase if it's coming from JavaScript/frontend
    # JavaScript uses uppercase like 'HEART_RATE' while Python backend expects lowercase like 'heart_rate'
    normalized_data_type = data_type.lower() if isinstance(data_type, str) else data_type
    
    # Mapping dettagliato per tutti i tipi di dati supportati
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

    
    # Determina il tipo di dato API corretto
    api_data_type = mapping.get(normalized_data_type, normalized_data_type)
    api_logger.debug(f"[{request_id}] Tipo dati normalizzato: {normalized_data_type} -> {api_data_type}")
    
    # Verifica se il tipo di dati è supportato da Fitbit
    if api_data_type not in FITBIT_ENDPOINTS:
        api_logger.error(f"[{request_id}] Tipo di dati non supportato da Fitbit: {api_data_type}")
        return []
    
    # Strategie multiple di recupero dati per maggiore resilienza
    results = []
    error_count = 0
    
    # Primo tentativo: dati di range con periodo completo
    api_logger.info(f"[{request_id}] Tentativo 1: Richiesta dati range per {api_data_type}")
    
    try:
        raw_data = get_fitbit_data(patient, api_data_type, start_date, end_date)
        if raw_data:
            # Processa i dati di range normali
            range_results = process_fitbit_data(raw_data, api_data_type)
            if range_results:
                results = range_results
                api_logger.info(f"[{request_id}] Recuperati {len(range_results)} punti dati range")
            else:
                api_logger.warning(f"[{request_id}] Nessun dato range disponibile per il periodo")
        else:
            api_logger.warning(f"[{request_id}] Nessun dato ricevuto per {api_data_type}")
            error_count += 1
    except Exception as e:
        api_logger.error(f"[{request_id}] Errore nel recupero o processamento dati range: {str(e)}")
        error_count += 1
    if results:
        try:
            # Alcuni timestamp potrebbero non avere il formato previsto, quindi gestiamo le eccezioni
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception as sort_error:
            api_logger.warning(f"[{request_id}] Impossibile ordinare i risultati: {str(sort_error)}")
    
    # Applica eventuali trasformazioni addizionali (ad esempio, unità di misura)
    try:
        endpoint_config = FITBIT_ENDPOINTS[api_data_type]
        transform_function = endpoint_config.get('value_transform', lambda x: x)
        unit = endpoint_config.get('unit', '')
        
        for item in results:
            # Assicurati che ogni elemento abbia l'unità corretta
            if 'unit' not in item:
                item['unit'] = unit
            
            # Aggiungi il campo recorded_at se non esiste già
            if 'recorded_at' not in item and 'timestamp' in item:
                item['recorded_at'] = item['timestamp']
    except Exception as transform_error:
        api_logger.error(f"[{request_id}] Errore nella trasformazione finale dei dati: {str(transform_error)}")
    
    api_logger.info(f"[{request_id}] Elaborazione completata, restituiti {len(results)} punti dati per {api_data_type}")
    return results

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
    Start the OAuth flow for the specified platform
    
    Args:
        platform_name (str): Name of the platform
        
    Returns:
        Response: Redirect to OAuth provider
    """    # Check if we have a link UUID in the session
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