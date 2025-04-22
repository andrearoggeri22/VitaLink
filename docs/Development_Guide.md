# VitaLink - Guida per lo Sviluppo

## Introduzione

Questa guida fornisce informazioni dettagliate per sviluppatori che lavorano sul progetto VitaLink. Troverai istruzioni su come configurare l'ambiente di sviluppo, comprendere l'architettura del sistema, seguire le best practices e contribuire efficacemente al codice.

## Configurazione Ambiente di Sviluppo

### Requisiti di Sistema

- Python 3.9+
- PostgreSQL 13+
- Docker e Docker Compose (opzionale, ma consigliato)
- Git

### Setup con Docker (Consigliato)

1. Clona il repository:
   ```
   git clone https://github.com/username/vitalink.git
   cd vitalink
   ```

2. Crea un file `.env` basato sul template `.env-example`:
   ```
   cp .env-example .env
   ```

3. Modifica il file `.env` con le tue impostazioni:
   ```
   # Database
   DATABASE_URL=postgresql://postgres:postgres@db:5432/vitalink
   PGUSER=postgres
   PGPASSWORD=postgres
   PGDATABASE=vitalink
   PGHOST=db
   PGPORT=5432
   
   # JWT
   JWT_SECRET_KEY=change_me_with_a_strong_secret
   
   # ClickSend (SMS)
   CLICKSEND_USERNAME=your_username
   CLICKSEND_API_KEY=your_api_key
   CLICKSEND_FROM_NUMBER=your_sender_number
   
   # Flask
   FLASK_APP=main.py
   FLASK_ENV=development
   SESSION_SECRET=another_strong_secret_key
   ```

4. Avvia i container Docker:
   ```
   docker-compose up -d
   ```

5. Accedi all'applicazione su `http://localhost:5000`

### Setup Manuale

1. Clona il repository:
   ```
   git clone https://github.com/username/vitalink.git
   cd vitalink
   ```

2. Crea un ambiente virtuale Python:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Installa le dipendenze:
   ```
   pip install -r requirements.txt
   ```

4. Configura il database PostgreSQL e crea un file `.env` con le variabili appropriate

5. Inizializza il database:
   ```
   flask db upgrade
   ```

6. Avvia l'applicazione:
   ```
   flask run
   ```

## Architettura del Progetto

VitaLink segue un'architettura Model-View-Controller (MVC) con la seguente struttura:

```
vitalink/
├── app.py                # Configurazione Flask principale
├── main.py               # Punto di ingresso dell'applicazione
├── models.py             # Modelli dati (SQLAlchemy)
├── api.py                # Endpoints API RESTful
├── views.py              # Route per l'interfaccia web
├── auth.py               # Autenticazione e gestione utenti
├── audit.py              # Sistema di audit trail
├── fitbit_integration.py # Integrazione con dispositivi
├── notifications.py      # Sistema di notifiche SMS
├── reports.py            # Generazione report PDF
├── utils.py              # Funzioni di utilità
├── language.py           # Gestione linguaggio
├── static/               # Asset statici (CSS, JS, immagini)
├── templates/            # Template HTML Jinja2
├── translations/         # File di traduzione
├── uploads/              # Directory per upload temporanei
├── tests/                # Test unitari e di integrazione
├── migrations/           # Migrazioni database
└── docs/                 # Documentazione
```

## Flusso di Sviluppo

### Creazione di una Nuova Funzionalità

1. **Definisci il Modello**: Se necessario, aggiungi o modifica modelli in `models.py`
2. **Crea/Aggiorna le Route**: Implementa le route in `views.py` (web) o `api.py` (API)
3. **Implementa la Logica**: Aggiungi la logica di business nelle funzioni appropriate
4. **Crea Template**: Per funzionalità web, crea o modifica i template in `templates/`
5. **Aggiungi Traduzioni**: Aggiorna i file di traduzione per il supporto multilingua
6. **Test**: Scrivi test unitari e di integrazione in `tests/`
7. **Documentazione**: Aggiorna la documentazione secondo necessità

### Convenzioni di Codice

- Segui PEP 8 per lo stile Python
- Usa docstring in formato Google per documentare funzioni e classi
- Mantieni le funzioni piccole e con responsabilità singola
- Scrivi nomi di variabili e funzioni descrittivi in inglese
- Usa commenti per spiegare complessità o logica non ovvia

## Sistema di Database

### Modelli Principali

- **Doctor**: Medici che utilizzano il sistema
- **Patient**: Pazienti monitorati
- **VitalSign**: Segni vitali registrati
- **Note**: Note mediche
- **AuditLog**: Log delle azioni eseguite

### Migrazioni

VitaLink utilizza Alembic (tramite Flask-Migrate) per gestire le migrazioni del database:

1. Generare una nuova migrazione dopo modifiche ai modelli:
   ```
   flask db migrate -m "Descrizione delle modifiche"
   ```

2. Applicare le migrazioni:
   ```
   flask db upgrade
   ```

3. Rollback all'ultima migrazione:
   ```
   flask db downgrade
   ```

## Internazionalizzazione (i18n)

VitaLink supporta completamente inglese e italiano. Per aggiungere o modificare traduzioni:

1. Estrai i messaggi da tradurre:
   ```
   pybabel extract -F babel.cfg -o messages.pot .
   ```

2. Aggiorna i file di traduzione:
   ```
   pybabel update -i messages.pot -d translations
   ```

3. Modifica i file `translations/[language]/LC_MESSAGES/messages.po`

4. Compila le traduzioni:
   ```
   pybabel compile -d translations
   ```

## Testing

VitaLink utilizza pytest per i test. Esegui i test con:

```
python -m pytest
```

### Struttura dei Test

- `tests/test_models.py`: Test per i modelli dati
- `tests/test_api.py`: Test per gli endpoint API
- `tests/test_auth.py`: Test per l'autenticazione
- `tests/test_views.py`: Test per le route web

### Best Practices per i Test

- Ogni funzione dovrebbe avere almeno un test
- Usa fixture per configurare ambienti di test riutilizzabili
- Test ogni caso limite e comportamento di errore
- Isola i test e non dipendere dallo stato di altri test

## Sistema di Audit

VitaLink include un robusto sistema di audit per tracciare tutte le azioni. Quando implementi nuove funzionalità, usa le funzioni di audit appropriate:

```python
from audit import log_action, ActionType, EntityType

# Registra una nuova azione
log_action(
    doctor_id=current_user.id,
    action_type=ActionType.CREATE,
    entity_type=EntityType.PATIENT,
    entity_id=patient.id,
    details={"description": "Created new patient record"},
    patient_id=patient.id
)
```

## Gestione Notifiche

Per inviare SMS tramite ClickSend:

```python
from notifications import send_sms

success, message = send_sms(
    to_number="+391234567890", 
    message="Messaggio di test"
)

if not success:
    # Gestione errore
    print(f"Errore invio SMS: {message}")
```

## Integrazione con Dispositivi Fitbit

L'integrazione con Fitbit è gestita in `fitbit_integration.py`. Il sistema supporta:

1. Caricamento dati da dispositivi connessi via USB
2. Upload dati tramite API per app mobili
3. Verifica dello stato di connessione del dispositivo

### Tipi di Dati Supportati

- Frequenza cardiaca (heart_rate)
- Passi (steps)
- Calorie (calories)
- Distanza (distance)
- Minuti di attività (active_minutes)
- Durata del sonno (sleep_duration)
- Piani saliti (floors_climbed)

## Generazione Report PDF

Il sistema genera report PDF utilizzando ReportLab. Per creare un nuovo tipo di report:

1. Definisci una nuova funzione in `reports.py`
2. Aggiungi le traduzioni necessarie in `get_report_translations()`
3. Implementa la logica per generare il PDF
4. Aggiungi una route in `views.py` per permettere agli utenti di accedere al report

Esempio:
```python
def generate_custom_report(patient, data, language=None):
    """
    Genera un report PDF personalizzato
    
    Args:
        patient: Oggetto paziente
        data: Dati da includere nel report
        language: Codice lingua (it/en)
        
    Returns:
        BytesIO: File PDF come stream binario
    """
    # Implementa la generazione del report
    # ...
```

## Sicurezza

### Best Practices di Sicurezza

1. **Autenticazione**:
   - Non memorizzare mai password in chiaro
   - Utilizza sempre `generate_password_hash` e `check_password_hash`
   - I token JWT dovrebbero avere una durata limitata

2. **Protezione CSRF**:
   - Tutti i form dovrebbero includere `{{ form.hidden_tag() }}`
   - Verifica che ogni form sia protetto

3. **Validazione Input**:
   - Convalida sempre tutti gli input utente
   - Usa i validatori WTForms per i form web
   - Controlla i tipi di dati e i formati nelle API

4. **Protezione Dati Sensibili**:
   - Usa HTTPS in produzione
   - Limita l'accesso ai dati solo agli utenti autorizzati
   - Implementa la politica del privilegio minimo

## Deployment

### Docker (Consigliato)

1. Assicurati che `Dockerfile` e `docker-compose.yml` siano configurati correttamente
2. Imposta le variabili di ambiente per la produzione
3. Esegui: `docker-compose -f docker-compose.yml up -d`

### Server Standard

1. Configura un server web (Nginx, Apache) come proxy reverse per Gunicorn
2. Imposta Gunicorn come server WSGI:
   ```
   gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
   ```
3. Configura un servizio systemd per gestire l'avvio automatico

## Contribuire al Progetto

1. Crea un fork del repository
2. Crea un branch per la tua funzionalità: `git checkout -b feature/nome-funzionalita`
3. Commit delle modifiche: `git commit -am 'Aggiungi nuova funzionalità'`
4. Push al branch: `git push origin feature/nome-funzionalita`
5. Crea una Pull Request

### Processo di Code Review

Tutte le Pull Request devono:
- Passare tutti i test
- Seguire le convenzioni di codice
- Includere test per le nuove funzionalità
- Aggiornare la documentazione secondo necessità

## Risoluzione Problemi

### Database

- **Problemi di connessione**: Verifica che le credenziali nel file `.env` siano corrette
- **Errori di migrazione**: Controlla i log di Alembic per dettagli specifici
- **Conflitti di dati**: Usa `db.session.rollback()` se necessario e verifica i vincoli di integrità

### Integrazione Fitbit

- **Dispositivo non rilevato**: Verifica che il dispositivo sia correttamente connesso via USB
- **Errori di estrazione dati**: Controlla i log per errori specifici di comunicazione

### SMS (ClickSend)

- **SMS non inviati**: Verifica le credenziali ClickSend e il saldo disponibile
- **Errori API**: Controlla la risposta dettagliata dall'API ClickSend

## Roadmap di Sviluppo

Funzionalità future pianificate:

1. **Notifiche SMS ai Medici**: Implementazione di notifiche per avvisare i medici di valori anomali (Tempo stimato: 45-60 minuti)
2. **Condivisione Pazienti tra Medici**: Funzionalità per consentire a più medici di collaborare sui dati di un paziente (Tempo stimato: 2-3 ore)
3. **Ricerca Globale dei Pazienti**: Implementazione di una funzionalità di ricerca avanzata (Tempo stimato: 3-4 ore)
4. **Sistema di Monitoraggio**: Integrazione di Flask-Monitoring-Dashboard per il monitoraggio delle prestazioni (Tempo stimato: 30-45 minuti)
5. **Backup Automatico Database**: Implementazione di backup programmati del database (Tempo stimato: 30-40 minuti)

## Risorse Aggiuntive

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [Flask-JWT-Extended Documentation](https://flask-jwt-extended.readthedocs.io/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [ClickSend API Documentation](https://developers.clicksend.com/)