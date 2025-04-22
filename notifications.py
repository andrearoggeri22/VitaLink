import os
import logging
from datetime import datetime
import clicksend_client
from clicksend_client.rest import ApiException
from flask import session, request, current_app

# Setup logger
logger = logging.getLogger(__name__)

# Get ClickSend credentials from environment
CLICKSEND_USERNAME = os.environ.get("CLICKSEND_USERNAME")
CLICKSEND_API_KEY = os.environ.get("CLICKSEND_API_KEY")
CLICKSEND_FROM_NUMBER = os.environ.get("CLICKSEND_FROM_NUMBER")


def get_sms_translations():
    """
    Get translations for SMS messages based on the selected language.
    
    Returns:
        dict: Dictionary of translated strings
    """
    # Get current language from session or from browser preferred language
    current_language = session.get('language')
    if not current_language:
        # Determine language from browser accept-languages header
        current_language = request.accept_languages.best_match(current_app.config['LANGUAGES'].keys()) or 'en'
        
    logger.debug(f"SMS language: {current_language}")
    
    if current_language == 'it':
        return {
            # Abnormal vital sign notification
            'alert_prefix': 'AVVISO VitaLink',
            'vital_high': 'sopra la norma',
            'vital_low': 'sotto la norma',
            'vital_message': '{prefix}: {name}, il tuo {vital_type} con valore {value} {unit} è {status}. Contatta il tuo medico se non ti senti bene.',
            
            # Appointment reminder
            'reminder_prefix': 'Promemoria',
            'appointment_message': '{prefix}: Hai un appuntamento con Dr. {doctor} il {date} alle {time}. Presentati 15 minuti prima per completare eventuali documenti.'
        }
    else:
        return {
            # Abnormal vital sign notification
            'alert_prefix': 'VitaLink ALERT',
            'vital_high': 'above normal',
            'vital_low': 'below normal',
            'vital_message': '{prefix}: {name}, your {vital_type} reading of {value} {unit} is {status}. Please contact your healthcare provider if you feel unwell.',
            
            # Appointment reminder
            'reminder_prefix': 'Reminder',
            'appointment_message': '{prefix}: You have an appointment with Dr. {doctor} on {date} at {time}. Please arrive 15 minutes early to complete any paperwork.'
        }


def send_sms(to_number, message):
    """
    Send an SMS notification using ClickSend
    
    Args:
        to_number (str): The recipient's phone number in E.164 format (+123456789)
        message (str): The message content to send
        
    Returns:
        bool: True if successful, False otherwise
        str: Status message
    """
    # Validate phone number format (basic check)
    if not to_number.startswith('+'):
        to_number = '+' + to_number

    # Check if ClickSend is configured
    if not all([CLICKSEND_USERNAME, CLICKSEND_API_KEY, CLICKSEND_FROM_NUMBER]):
        logger.error("ClickSend credentials not configured")
        return False, "SMS notification service not configured"

    try:
        # Configure the ClickSend client
        configuration = clicksend_client.Configuration()
        configuration.username = CLICKSEND_USERNAME
        configuration.password = CLICKSEND_API_KEY

        # Create an instance of the API class
        api_instance = clicksend_client.SMSApi(
            clicksend_client.ApiClient(configuration))

        # Create the SMS message
        # Note: In clicksend_client.SmsMessage 'from' is handled by '_from' parameter
        sms_message = clicksend_client.SmsMessage(_from=CLICKSEND_FROM_NUMBER,
                                                  body=message,
                                                  to=to_number,
                                                  source="sdk")

        # Create a message collection (list of messages)
        sms_messages = clicksend_client.SmsMessageCollection(
            messages=[sms_message])

        # Send the message
        api_response = api_instance.sms_send_post(sms_messages)

        logger.info(f"SMS sent successfully to {to_number}: {api_response}")
        return True, f"SMS sent successfully"

    except ApiException as e:
        logger.error(f"ClickSend API error: {str(e)}")
        # Return a more user-friendly error message
        return False, f"SMS notification not sent. Please check patient phone number format."
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        return False, f"SMS notification service temporarily unavailable."


def notify_abnormal_vital(patient, vital_type, value, unit, status):
    """
    Send notification about abnormal vital sign
    
    Args:
        patient: Patient object
        vital_type (str): Type of vital sign
        value (float/str): The recorded value
        unit (str): Unit of measurement
        status (str): 'high' or 'low'
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not patient.contact_number:
        logger.warning(
            f"Cannot send alert: Patient {patient.id} has no contact number")
        return False, "Patient has no contact number"

    # Get translations
    t = get_sms_translations()
    
    # Format the message
    status_text = t['vital_high'] if status == "high" else t['vital_low']
    vital_type_formatted = vital_type.replace('_', ' ')
    
    message = t['vital_message'].format(
        prefix=t['alert_prefix'],
        name=patient.first_name,
        vital_type=vital_type_formatted,
        value=value,
        unit=unit,
        status=status_text
    )

    # Send the SMS
    return send_sms(patient.contact_number, message)


def send_appointment_reminder(patient, doctor, appointment_date,
                              appointment_time):
    """
    Send appointment reminder to patient
    
    Args:
        patient: Patient object
        doctor: Doctor object
        appointment_date: Date of appointment
        appointment_time: Time of appointment
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not patient.contact_number:
        return False, "Patient has no contact number"

    # Get translations
    t = get_sms_translations()
    
    # Format the message
    message = t['appointment_message'].format(
        prefix=t['reminder_prefix'],
        doctor=doctor.last_name,
        date=appointment_date,
        time=appointment_time
    )

    # Send the SMS
    return send_sms(patient.contact_number, message)
