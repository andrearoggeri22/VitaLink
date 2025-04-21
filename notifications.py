import os
import logging
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Setup logger
logger = logging.getLogger(__name__)

# Get Twilio credentials from environment
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")


def send_sms(to_number, message):
    """
    Send an SMS notification using Twilio
    
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
        
    # Check if Twilio is configured
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        logger.error("Twilio credentials not configured")
        return False, "SMS notification service not configured"
    
    try:
        # Initialize the Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send the message
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        
        logger.info(f"SMS sent successfully to {to_number}, SID: {message.sid}")
        return True, f"SMS sent successfully"
        
    except TwilioRestException as e:
        logger.error(f"Twilio error: {str(e)}")
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