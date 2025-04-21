import os
import json
import glob
import logging
import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from models import Patient, VitalSign, VitalSignType, DataOrigin, db
from audit import log_vital_creation
from utils import get_vital_sign_unit
from notifications import notify_abnormal_vital
from utils import is_vital_in_range

fitbit_bp = Blueprint('fitbit', __name__)

# Directory temporanea per il caricamento dei file
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Tipi di dati che possono essere importati da Fitbit
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
    """Eccezione sollevata quando il dispositivo non può essere connesso"""
    pass

def check_device_connected():
    """
    Verifica se un dispositivo Fitbit è connesso via USB.
    Simula la verifica del dispositivo cercando in determinate directory del sistema.
    
    Ritorna:
        bool: True se il dispositivo è connesso, False altrimenti
    """
    try:
        # Qui dovrebbe essere implementato il codice per verificare se un dispositivo Fitbit è connesso
        # Per ora simula che nessun dispositivo sia connesso
        return False
    except Exception as e:
        logging.error(f"Errore durante la verifica del dispositivo: {str(e)}")
        return False

def extract_fitbit_data(patient_id):
    """
    Estrae i dati dal dispositivo Fitbit collegato via USB.
    
    Args:
        patient_id (int): ID del paziente a cui associare i dati
        
    Returns:
        dict: Dati estratti dal dispositivo nel formato:
              {
                'heart_rate': [{'timestamp': '2025-04-21T12:30:00', 'value': 75}],
                'steps': [{'timestamp': '2025-04-21', 'value': 8500}],
                'calories': [{'timestamp': '2025-04-21', 'value': 2100}],
                ...
              }
              
    Raises:
        DeviceConnectionError: Se il dispositivo non è connesso o ci sono problemi di connessione
    """
    if not check_device_connected():
        raise DeviceConnectionError("Nessun dispositivo Fitbit connesso")
    
    try:
        # Qui dovrebbe essere implementato il codice per estrarre i dati dal dispositivo
        # Per ora simula l'estrazione dei dati
        
        # Data corrente per simulazione
        current_date = datetime.datetime.now()
        
        # Simula un dataset di esempio con timestamp attuali
        sample_data = {
            'heart_rate': [
                {'timestamp': current_date.strftime('%Y-%m-%dT%H:%M:%S'), 'value': 72}
            ],
            'steps': [
                {'timestamp': current_date.strftime('%Y-%m-%d'), 'value': 8450}
            ],
            'calories': [
                {'timestamp': current_date.strftime('%Y-%m-%d'), 'value': 2050}
            ],
            'distance': [
                {'timestamp': current_date.strftime('%Y-%m-%d'), 'value': 5.2}
            ],
            'active_minutes': [
                {'timestamp': current_date.strftime('%Y-%m-%d'), 'value': 45}
            ],
            'sleep_duration': [
                {'timestamp': current_date.strftime('%Y-%m-%d'), 'value': 7.5}
            ],
            'floors_climbed': [
                {'timestamp': current_date.strftime('%Y-%m-%d'), 'value': 12}
            ]
        }
        
        return sample_data
    except Exception as e:
        logging.error(f"Errore durante l'estrazione dei dati dal dispositivo: {str(e)}")
        raise DeviceConnectionError(f"Errore durante l'estrazione dei dati: {str(e)}")

def save_fitbit_data(patient_id, data):
    """
    Salva i dati estratti dal dispositivo Fitbit nel database.
    
    Args:
        patient_id (int): ID del paziente a cui associare i dati
        data (dict): Dati estratti dal dispositivo nel formato descritto in extract_fitbit_data
        
    Returns:
        tuple: (success, vitals_saved, errors)
            success (bool): True se i dati sono stati salvati con successo
            vitals_saved (int): Numero di parametri vitali salvati
            errors (list): Lista di errori occorsi durante il salvataggio
    """
    vitals_saved = 0
    errors = []
    
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return False, 0, ["Paziente non trovato"]
        
        for data_type, measurements in data.items():
            if data_type not in FITBIT_DATA_TYPES:
                errors.append(f"Tipo di dato non supportato: {data_type}")
                continue
            
            vital_type = FITBIT_DATA_TYPES[data_type]
            
            for measurement in measurements:
                try:
                    # Converte il timestamp in datetime
                    if 'T' in measurement['timestamp']:
                        recorded_at = datetime.datetime.strptime(measurement['timestamp'], '%Y-%m-%dT%H:%M:%S')
                    else:
                        recorded_at = datetime.datetime.strptime(measurement['timestamp'], '%Y-%m-%d')
                    
                    # Crea il nuovo parametro vitale
                    vital = VitalSign(
                        patient_id=patient_id,
                        type=vital_type,
                        value=measurement['value'],
                        unit=get_vital_sign_unit(data_type),
                        recorded_at=recorded_at,
                        origin=DataOrigin.AUTOMATIC
                    )
                    
                    db.session.add(vital)
                    vitals_saved += 1
                    
                    # Verifica se il valore è fuori range e invia notifica
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
                    errors.append(f"Errore nel salvataggio del parametro {data_type}: {str(e)}")
        
        db.session.commit()
        return True, vitals_saved, errors
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, 0, [f"Errore database: {str(e)}"]
    except Exception as e:
        db.session.rollback()
        return False, 0, [f"Errore generico: {str(e)}"]

@fitbit_bp.route('/patients/<int:patient_id>/upload_fitbit', methods=['GET', 'POST'])
@login_required
def upload_fitbit_data(patient_id):
    """
    Route per caricare dati da un dispositivo Fitbit connesso via USB.
    """
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        try:
            # Verifica se il dispositivo è connesso
            if not check_device_connected():
                flash("Nessun dispositivo Fitbit connesso. Collega il dispositivo via USB e riprova.", "error")
                return redirect(url_for('fitbit.upload_fitbit_data', patient_id=patient_id))
            
            # Estrae i dati dal dispositivo
            try:
                data = extract_fitbit_data(patient_id)
            except DeviceConnectionError as e:
                flash(f"Errore durante l'estrazione dei dati: {str(e)}", "error")
                return redirect(url_for('fitbit.upload_fitbit_data', patient_id=patient_id))
            
            # Salva i dati nel database
            success, vitals_saved, errors = save_fitbit_data(patient_id, data)
            
            if success:
                flash(f"Dati Fitbit caricati con successo. {vitals_saved} parametri vitali salvati.", "success")
                if errors:
                    for error in errors:
                        flash(f"Avviso: {error}", "warning")
            else:
                flash("Errore durante il salvataggio dei dati Fitbit.", "error")
                for error in errors:
                    flash(error, "error")
            
            return redirect(url_for('views.patient_vitals', patient_id=patient_id))
        
        except Exception as e:
            flash(f"Errore durante il processo di caricamento: {str(e)}", "error")
            return redirect(url_for('fitbit.upload_fitbit_data', patient_id=patient_id))
    
    # GET request - mostra la pagina per il caricamento
    return render_template('fitbit_upload.html', patient=patient)