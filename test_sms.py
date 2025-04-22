#!/usr/bin/env python3
"""
Script di test per verificare l'invio di SMS tramite ClickSend.
Esegui questo script con 'python test_sms.py <numero_telefono>'
dove <numero_telefono> è in formato internazionale (es. +391234567890)
"""

import sys
import os
import logging
from notifications import send_sms

# Configurazione logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Verifica degli argomenti
    if len(sys.argv) < 2:
        print("Uso: python test_sms.py <numero_telefono>")
        print("Il numero deve essere in formato internazionale, es. +391234567890")
        sys.exit(1)
    
    # Prendi il numero di telefono dalla riga di comando
    to_number = sys.argv[1]
    
    # Verifica che siano disponibili le credenziali ClickSend
    clicksend_username = os.environ.get('CLICKSEND_USERNAME')
    clicksend_api_key = os.environ.get('CLICKSEND_API_KEY')
    clicksend_from = os.environ.get('CLICKSEND_FROM_NUMBER')
    
    if not all([clicksend_username, clicksend_api_key, clicksend_from]):
        print("ERRORE: Credenziali ClickSend non configurate. Imposta le variabili d'ambiente:")
        print("- CLICKSEND_USERNAME")
        print("- CLICKSEND_API_KEY")
        print("- CLICKSEND_FROM_NUMBER")
        sys.exit(1)
    
    # Prova a inviare un SMS di test
    print(f"Invio SMS di test al numero {to_number}...")
    success, message = send_sms(
        to_number, 
        "VitaLink: Questo è un SMS di test inviato dal sistema VitaLink."
    )
    
    # Mostra il risultato
    if success:
        print(f"SMS inviato con successo! Messaggio: {message}")
    else:
        print(f"Errore nell'invio dell'SMS: {message}")

if __name__ == "__main__":
    main()