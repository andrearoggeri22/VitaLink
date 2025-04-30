#!/usr/bin/env python
import os
import sys
import pytest
from datetime import datetime

# Aggiungi la directory corrente al path di sistema
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def setup_test_account():
    """Crea un account di test nel database se non esiste già."""
    try:
        from app.app import app, db
        from app.models import Doctor
        
        with app.app_context():
            # Verifica se esiste già l'account di test
            test_doctor = Doctor.query.filter_by(email="test@vitalink.com").first()
            
            if test_doctor is None:
                print("Creazione dell'account di test...")
                
                # Crea un nuovo dottore di test
                doctor = Doctor(
                    email="test@vitalink.com",
                    first_name="Test",
                    last_name="Doctor",
                    specialty="General Medicine"
                )
                doctor.set_password("TestVitaLink123!")
                
                db.session.add(doctor)
                db.session.commit()
                
                print(f"Account di test creato con successo: test@vitalink.com / TestVitaLink123!")
            else:
                print("L'account di test esiste già.")
    
    except Exception as e:
        print(f"Errore durante la creazione dell'account di test: {str(e)}")

def run_tests():
    """Esegue tutti i test del progetto."""
    # Prima crea l'account di test
    setup_test_account()
    
    # Poi esegui i test
    print("\nAvvio dei test...")
    
    # Parametri pytest
    pytest_args = [
        "-v",                  # Modalità verbose
        "--color=yes",         # Output colorato
        "--durations=5",       # Mostra i 5 test più lenti
        "tests/"               # Cartella dei test
    ]
    
    # Aggiungi copertura del codice se il modulo è disponibile
    try:
        import pytest_cov
        pytest_args.extend([
            "--cov=app",
            "--cov-report=term",
            "--cov-report=html:tests/coverage_html"
        ])
        print("Generazione report di copertura attivata.")
    except ImportError:
        print("pytest-cov non trovato. Il report di copertura non sarà generato.")
    
    # Esegui pytest con gli argomenti specificati
    return pytest.main(pytest_args)

if __name__ == "__main__":
    # Salva l'ora di inizio
    start_time = datetime.now()
    
    # Esegui i test
    exit_code = run_tests()
    
    # Calcola il tempo impiegato
    duration = datetime.now() - start_time
    
    print(f"\nTest completati in {duration}.")
    
    # Esci con il codice restituito da pytest
    sys.exit(exit_code)
