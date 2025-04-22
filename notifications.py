import os
import logging
from datetime import datetime
import clicksend_client
from clicksend_client.rest import ApiException

# Setup logger
logger = logging.getLogger(__name__)

# Get ClickSend credentials from environment
CLICKSEND_USERNAME = os.environ.get("CLICKSEND_USERNAME")
CLICKSEND_API_KEY = os.environ.get("CLICKSEND_API_KEY")
CLICKSEND_FROM_NUMBER = os.environ.get("CLICKSEND_FROM_NUMBER")


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
        api_instance = clicksend_client.SMSApi(clicksend_client.ApiClient(configuration))
        
        # Create the SMS message
        # Note: 'from' is a reserved keyword in Python, so we use named parameters
        sms_message = clicksend_client.SmsMessage()
        sms_message.source = "sdk"
        sms_message.body = message
        sms_message.to = to_number
        sms_message._from = CLICKSEND_FROM_NUMBER  # Use _from instead of from_
        
        # Create a message collection (list of messages)
        sms_messages = clicksend_client.SmsMessageCollection(messages=[sms_message])
        
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
        logger.warning(f"Cannot send alert: Patient {patient.id} has no contact number")
        return False, "Patient has no contact number"
    
    # Format the message
    status_text = "above normal" if status == "high" else "below normal"
    message = (f"HEALTH ALERT: {patient.first_name}, your {vital_type.replace('_', ' ')} "
              f"reading of {value} {unit} is {status_text}. "
              f"Please contact your healthcare provider if you feel unwell.")
    
    # Send the SMS
    return send_sms(patient.contact_number, message)


def send_appointment_reminder(patient, doctor, appointment_date, appointment_time):
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
    
    # Format the message
    message = (f"Reminder: You have an appointment with "
              f"Dr. {doctor.last_name} on {appointment_date} at {appointment_time}. "
              f"Please arrive 15 minutes early to complete any paperwork.")
    
    # Send the SMS
    return send_sms(patient.contact_number, message)