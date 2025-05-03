"""
Email Utility Module.

Questo modulo fornisce funzionalità per l'invio di email attraverso il servizio Mailjet.
Include funzioni per inviare email con allegati, come i report dei pazienti.
"""
import os
import base64
import logging
from mailjet_rest import Client
from flask_babel import gettext as _
from .models import Doctor, Patient

# Configurazione logger
logger = logging.getLogger(__name__)

# Configurazione Mailjet API
MJ_APIKEY = os.environ["MJ_APIKEY"]
MJ_APIKEY_SECRET = os.environ["MJ_APIKEY_SECRET"]

def send_report_email(doctor, patient, pdf_buffer, filename, language='it'):
    """
    Invia un report PDF al paziente via email tramite Mailjet.
    
    Args:
        doctor (Doctor): oggetto Doctor rappresentante il medico che ha generato il report
        patient (Patient): oggetto Patient del paziente destinatario
        pdf_buffer (BytesIO): buffer contenente il report PDF
        filename (str): nome del file PDF
        language (str, optional): codice lingua per le traduzioni (it/en)
        
    Returns:
        tuple: Tuple contenente (successo, messaggio)
            - successo (bool): True se l'email è stata inviata con successo, altrimenti False
            - messaggio (str): messaggio di successo o errore
    """
    if not patient.email:
        return False, _("Il paziente non ha un indirizzo email")
    
    try:
        # Creo il client Mailjet
        mailjet = Client(auth=(MJ_APIKEY, MJ_APIKEY_SECRET), version='v3.1')
        
        # Converto PDF in base64
        pdf_content = pdf_buffer.getvalue()
        encoded_pdf = base64.b64encode(pdf_content).decode('utf-8')
        
        # Timestamp per il nome del file
        date_str = filename.split('_')[-2]  # Estraggo la data dal nome file
        
        # Preparo il soggetto dell'email
        subject = _("Report medico da {doctor_name} - {date}").format(
            doctor_name=f"Dr. {doctor.first_name} {doctor.last_name}",
            date=date_str
        )
        
        # Preparo il contenuto dell'email
        text_content = _("""
Gentile {patient_name},

In allegato trova il report medico generato da {doctor_name}.

Questo è un messaggio automatico, si prega di non rispondere a questa email.

Cordiali saluti,
Team VitaLink
        """).format(
            patient_name=f"{patient.first_name} {patient.last_name}",
            doctor_name=f"Dr. {doctor.first_name} {doctor.last_name}"
        )
        
        html_content = _("""
<h3>Gentile {patient_name},</h3>

<p>In allegato trova il report medico generato da {doctor_name}.</p>

<p><strong>Informazioni sul report:</strong><br>
Data: {date}<br>
Generato da: {doctor_name}<br>
Specialità: {specialty}</p>

<p>Questo è un messaggio automatico, si prega di non rispondere a questa email.</p>

<p>Cordiali saluti,<br>
Team VitaLink</p>
        """).format(
            patient_name=f"{patient.first_name} {patient.last_name}",
            doctor_name=f"Dr. {doctor.first_name} {doctor.last_name}",
            specialty=doctor.specialty or _("Medicina generale"),
            date=date_str
        )
        
        # Preparo i dati da inviare a Mailjet
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": os.environ["EMAIL_SENDER"],
                        "Name": "VitaLink"
                    },
                    "To": [
                        {
                            "Email": patient.email,
                            "Name": f"{patient.first_name} {patient.last_name}"
                        }
                    ],
                    "Subject": subject,
                    "TextPart": text_content,
                    "HTMLPart": html_content,
                    "Attachments": [
                        {
                            "ContentType": "application/pdf",
                            "Filename": filename,
                            "Base64Content": encoded_pdf
                        }
                    ]
                }
            ]
        }
        
        # Eseguo la richiesta a Mailjet
        result = mailjet.send.create(data=data)
        
        # Verifico il risultato
        if result.status_code == 200:
            response_data = result.json()
            if response_data and 'Messages' in response_data and len(response_data['Messages']) > 0:
                message = response_data['Messages'][0]
                if message.get('Status') == 'success':
                    logger.info(f"Email inviata con successo a {patient.email}")
                    return True, _("Report inviato con successo a {email}").format(email=patient.email)
        
        # Se arrivo qui c'è stato un problema
        logger.error(f"Errore invio email: {result.status_code} - {result.json()}")
        return False, _("Errore nell'invio dell'email: {error}").format(error=result.status_code)
        
    except Exception as e:
        logger.exception(f"Eccezione durante invio email: {str(e)}")
        return False, _("Si è verificato un errore durante l'invio dell'email: {error}").format(error=str(e))
