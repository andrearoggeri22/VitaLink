"""
Fitbit API Service Module
Servizio ottimizzato per la gestione delle richieste alle API Fitbit
Implementa un sistema di cache e gestione rate limit avanzato
"""

import uuid
import json
import time
import logging
from datetime import datetime, timedelta
import requests

from app import db
from models import Patient, VitalSignType
from health_platforms_config import FITBIT_CONFIG, FITBIT_ENDPOINTS

# Configurazione logging avanzato per monitoraggio API
api_logger = logging.getLogger('fitbit_api')
api_logger.setLevel(logging.DEBUG)

# Gestione file di log separato
try:
    api_handler = logging.FileHandler('logs/fitbit_api.log')
    api_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(request_id)s] %(message)s')
    api_handler.setFormatter(formatter)
    api_logger.addHandler(api_handler)
except Exception as e:
    # Fallback su logging standard
    api_logger = logging.getLogger('app')
    api_logger.error(f"Impossibile creare log dedicato per API Fitbit: {str(e)}")

# Cache per le richieste API
# Struttura: {
#   'key': {
#     'data': [...], 
#     'timestamp': datetime,
#     'ttl': seconds,
#     'source': 'cache/api'
#   }
# }
api_cache = {}

# Configurazione del rate limiter
rate_limit = {
    'hourly_limit': 150,  # Limite orario API Fitbit
    'calls_this_hour': 0,
    'last_reset': datetime.now(),
    'retry_after': None
}

# Tempo di vita predefinito per la cache (secondi)
DEFAULT_CACHE_TTL = 300  # 5 minuti

class FitbitAPIService:
    """
    Servizio per la gestione ottimizzata delle richieste alle API Fitbit
    Implementa caching, rate limiting e gestione degli errori
    """
    
    @staticmethod
    def make_request(endpoint, access_token, params=None, method='GET'):
        """
        Esegue una richiesta alle API Fitbit con gestione rate limit e cache
        
        Args:
            endpoint (str): Endpoint API relativo (senza URL base)
            access_token (str): Token di accesso OAuth
            params (dict, optional): Parametri della richiesta
            method (str, optional): Metodo HTTP (GET, POST, ecc.)
            
        Returns:
            dict: Risposta JSON dall'API o None in caso di errore
        """
        # Genera ID univoco per questa richiesta (per tracciamento nei log)
        request_id = str(uuid.uuid4())[:8]
        
        # Controlla se abbiamo raggiunto il rate limit
        if not FitbitAPIService._check_rate_limit():
            extra = {'request_id': request_id}
            api_logger.warning(f"Rate limit attivo, richiesta bloccata: {endpoint}", extra=extra)
            return None
        
        # Prepara l'URL e gli headers
        url = f"{FITBIT_CONFIG['api_base_url']}{endpoint}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept-Language': 'it_IT'  # Localizzazione italiana
        }
        
        extra = {'request_id': request_id}
        api_logger.info(f"Richiesta API: {method} {endpoint}", extra=extra)
        
        try:
            # Esegui la richiesta
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=params)
            else:
                api_logger.error(f"Metodo non supportato: {method}", extra=extra)
                return None
            
            # Incrementa il contatore delle richieste
            FitbitAPIService._increment_request_counter()
            
            # Gestisci la risposta
            if response.status_code == 200:
                data = response.json()
                api_logger.debug(f"Risposta valida: {len(str(data))} bytes", extra=extra)
                return data
            elif response.status_code == 429:
                # Rate limit raggiunto
                FitbitAPIService._handle_rate_limit(response)
                api_logger.warning(f"Rate limit raggiunto: {response.headers.get('Retry-After', '3600')}s", extra=extra)
                return None
            else:
                api_logger.error(f"Errore API: {response.status_code} - {response.text}", extra=extra)
                return None
                
        except Exception as e:
            api_logger.error(f"Eccezione durante richiesta API: {str(e)}", extra=extra)
            return None
    
    @staticmethod
    def get_cached_data(cache_key, ttl=DEFAULT_CACHE_TTL):
        """
        Ottieni dati dalla cache se disponibili e non scaduti
        
        Args:
            cache_key (str): Chiave di cache univoca
            ttl (int): Tempo di vita massimo in secondi
            
        Returns:
            tuple: (data, is_from_cache)
        """
        if cache_key in api_cache:
            cache_entry = api_cache[cache_key]
            cache_age = (datetime.now() - cache_entry.get('timestamp', datetime.min)).total_seconds()
            
            # Verifica se la cache è ancora valida
            if cache_age < cache_entry.get('ttl', ttl):
                return cache_entry.get('data', None), True
        
        return None, False
    
    @staticmethod
    def set_cached_data(cache_key, data, ttl=DEFAULT_CACHE_TTL):
        """
        Salva dati in cache con TTL specificato
        
        Args:
            cache_key (str): Chiave di cache univoca
            data: Dati da memorizzare
            ttl (int): Tempo di vita in secondi
        """
        api_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now(),
            'ttl': ttl,
            'source': 'api'
        }
    
    @staticmethod
    def get_vital_data(patient, data_type, start_date=None, end_date=None, use_intraday=True):
        """
        Ottiene dati vitali per un paziente con gestione cache ottimizzata
        
        Args:
            patient (Patient): Oggetto paziente
            data_type (str): Tipo di dati vitali
            start_date (str, optional): Data inizio formato YYYY-MM-DD
            end_date (str, optional): Data fine formato YYYY-MM-DD
            use_intraday (bool, optional): Se usare dati intraday quando disponibili
            
        Returns:
            list: Dati vitali nel formato standardizzato
        """
        # Imposta date predefinite se non specificate
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            start_dt = end_dt - timedelta(days=7) # Default: 7 giorni
            start_date = start_dt.strftime('%Y-%m-%d')
        
        # Genera ID univoco per questa richiesta
        request_id = str(uuid.uuid4())[:8]
        extra = {'request_id': request_id}
        
        # Generiamo la chiave di cache
        cache_key = f"{patient.id}_{data_type.lower()}_{start_date}_{end_date}_{use_intraday}"
        
        # Configurazione TTL basata sul tipo di dati e periodo
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days_diff = (end_dt - start_dt).days + 1
            
            # Imposta TTL in base al periodo: dati storici possono essere cachati più a lungo
            if days_diff > 30:  # Dati di lungo periodo (>1 mese)
                cache_ttl = 60 * 60 * 12  # 12 ore
            elif days_diff > 7:  # Dati settimanali (7-30 giorni)
                cache_ttl = 60 * 60  # 1 ora
            else:  # Dati recenti (<7 giorni)
                cache_ttl = 300  # 5 minuti
                
            # Per i dati odierni, riduce ulteriormente il TTL
            today = datetime.now().date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            if end_date_obj >= today and days_diff <= 2:
                # Per oggi/ieri, i dati cambiano frequentemente
                cache_ttl = 120  # 2 minuti
        except:
            # Fallback su TTL predefinito
            cache_ttl = DEFAULT_CACHE_TTL
        
        # Verifica se i dati sono in cache
        cached_data, from_cache = FitbitAPIService.get_cached_data(cache_key, cache_ttl)
        if from_cache and cached_data is not None:
            api_logger.info(f"Dati recuperati da cache per {data_type}, periodo {start_date} - {end_date}", extra=extra)
            return cached_data
        
        api_logger.info(f"Dati non in cache o scaduti per {data_type}, recupero da API", extra=extra)
        
        # I dati non sono in cache, dobbiamo richiederli alle API
        # Implementazione dipendente dal tipo di dati richiesti
        # ... 
        # Qui andrebbe il codice specifico per chiamare le API Fitbit
        # con gestione di token, rate limit, ecc.
        # ...
        
        # Placeholder per l'implementazione completa
        return []

    @staticmethod
    def _check_rate_limit():
        """Verifica se abbiamo raggiunto il rate limit"""
        now = datetime.now()
        
        # Se c'è un retry_after attivo, verifica se è passato
        if rate_limit['retry_after'] and now < rate_limit['retry_after']:
            return False
        
        # Resetta il contatore se è passata un'ora
        if (now - rate_limit['last_reset']).total_seconds() >= 3600:
            rate_limit['calls_this_hour'] = 0
            rate_limit['last_reset'] = now
        
        # Verifica se abbiamo superato il limite
        return rate_limit['calls_this_hour'] < rate_limit['hourly_limit']
    
    @staticmethod
    def _increment_request_counter():
        """Incrementa il contatore delle richieste API"""
        rate_limit['calls_this_hour'] += 1
        
        # Log del contatore ogni 10 richieste
        if rate_limit['calls_this_hour'] % 10 == 0:
            remaining = rate_limit['hourly_limit'] - rate_limit['calls_this_hour']
            api_logger.info(f"Rate limit: {rate_limit['calls_this_hour']}/{rate_limit['hourly_limit']} usato, {remaining} rimanenti")
    
    @staticmethod
    def _handle_rate_limit(response):
        """Gestisce la risposta di rate limit dalle API"""
        retry_after = response.headers.get('Retry-After')
        
        if retry_after:
            try:
                seconds = int(retry_after)
                rate_limit['retry_after'] = datetime.now() + timedelta(seconds=seconds)
            except:
                # Se Retry-After non è un intero, assume 3600 secondi (1 ora)
                rate_limit['retry_after'] = datetime.now() + timedelta(seconds=3600)
        else:
            # Se non c'è Retry-After, assumiamo 1 ora
            rate_limit['retry_after'] = datetime.now() + timedelta(seconds=3600)
