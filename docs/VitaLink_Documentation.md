# VitaLink - Documentazione Tecnica

## Panoramica del Sistema

VitaLink è una piattaforma sanitaria completa progettata per il monitoraggio dei pazienti e il tracciamento dei segni vitali, con solide funzionalità backend e capacità flessibili di gestione dei dati. Il sistema è stato sviluppato per aiutare i medici nel monitoraggio efficiente della salute dei pazienti, con particolare attenzione alla gestione dei dati vitali.

### Stack Tecnologico
- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Autenticazione**: Flask-Login (web) e JWT (API)
- **Containerizzazione**: Docker
- **Internazionalizzazione**: Flask-Babel
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Reportistica**: ReportLab (PDF)
- **Integrazione Dispositivi**: Fitbit
- **Notifiche**: ClickSend (SMS)

## Architettura del Sistema

L'architettura di VitaLink segue un pattern Model-View-Controller (MVC) con i seguenti componenti principali:

### Componenti Core
1. **Autenticazione** (`auth.py`) - Gestione utenti e accessi
2. **API** (`api.py`) - Endpoints RESTful per l'accesso programmatico 
3. **Visualizzazione Web** (`views.py`) - Interfaccia utente per browser
4. **Modelli Dati** (`models.py`) - Definizione delle entità
5. **Integrazione Dispositivi** (`fitbit_integration.py`) - Connessione con dispositivi esterni
6. **Audit e Logging** (`audit.py`) - Tracciamento delle attività
7. **Notifiche** (`notifications.py`) - Sistema di avvisi via SMS
8. **Reportistica** (`reports.py`) - Generazione report PDF 
9. **Strumenti** (`utils.py`) - Funzioni di utilità generale

## Modelli di Dati

### Modelli Principali

#### Doctor
```python
class Doctor(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship con pazienti (tramite tabella di associazione)
    patients = db.relationship('Patient', 
                              secondary='doctor_patient',
                              backref=db.backref('doctors', lazy='dynamic'),
                              lazy='dynamic')
    
    # Note create dal medico
    notes = db.relationship('Note', backref='doctor', lazy='dynamic')
```

#### Patient
```python
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20))
    contact_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship con segni vitali e note
    vital_signs = db.relationship('VitalSign', backref='patient', lazy='dynamic')
    notes = db.relationship('Note', backref='patient', lazy='dynamic')
```

#### VitalSign
```python
class VitalSign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    type = db.Column(db.Enum(VitalSignType), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    origin = db.Column(db.Enum(DataOrigin), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Note
```python
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### AuditLog
```python
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    action_type = db.Column(db.Enum(ActionType), nullable=False)
    entity_type = db.Column(db.Enum(EntityType), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    details = db.Column(db.Text)  # JSON string con dettagli azione
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    ip_address = db.Column(db.String(50))
```

### Enumerazioni

```python
class DataOrigin(Enum):
    MANUAL = "manual"      # Dati inseriti manualmente
    AUTOMATIC = "automatic"  # Dati caricati automaticamente

class VitalSignType(Enum):
    HEART_RATE = "heart_rate"           # Frequenza cardiaca
    BLOOD_PRESSURE = "blood_pressure"   # Pressione sanguigna
    OXYGEN_SATURATION = "oxygen_saturation"  # Saturazione ossigeno
    TEMPERATURE = "temperature"         # Temperatura
    RESPIRATORY_RATE = "respiratory_rate"  # Frequenza respiratoria
    GLUCOSE = "glucose"                 # Glucosio
    WEIGHT = "weight"                   # Peso
    STEPS = "steps"                     # Passi
    CALORIES = "calories"               # Calorie
    DISTANCE = "distance"               # Distanza
    ACTIVE_MINUTES = "active_minutes"   # Minuti di attività
    SLEEP_DURATION = "sleep_duration"   # Durata del sonno
    FLOORS_CLIMBED = "floors_climbed"   # Piani saliti

class ActionType(Enum):
    CREATE = "create"  # Creazione entità
    UPDATE = "update"  # Aggiornamento entità
    DELETE = "delete"  # Eliminazione entità
    VIEW = "view"      # Visualizzazione entità
    EXPORT = "export"  # Esportazione dati

class EntityType(Enum):
    PATIENT = "patient"       # Entità paziente
    VITAL_SIGN = "vital_sign"  # Entità segno vitale
    NOTE = "note"             # Entità nota
    REPORT = "report"         # Entità report
```

## API Endpoints

VitaLink offre una serie di API RESTful per l'integrazione con sistemi esterni, app mobili o interfacce personalizzate.

### Autenticazione API

#### Login API
- **Endpoint**: `/api/login`
- **Metodo**: POST
- **Descrizione**: Ottiene i token JWT per l'autenticazione API
- **Parametri**:
  - `email`: Email del medico
  - `password`: Password del medico
- **Risposta**: 
  ```json
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
    "message": "Login successful"
  }
  ```

#### Refresh Token
- **Endpoint**: `/api/refresh`
- **Metodo**: POST
- **Descrizione**: Aggiorna un token JWT scaduto
- **Richiede**: Header `Authorization: Bearer <refresh_token>`
- **Risposta**: Nuovo access token

### API Pazienti

#### Ottieni Tutti i Pazienti
- **Endpoint**: `/api/patients`
- **Metodo**: GET
- **Descrizione**: Ottiene la lista di tutti i pazienti associati al medico autenticato
- **Richiede**: Autenticazione JWT
- **Risposta**:
  ```json
  {
    "patients": [
      {
        "id": 1,
        "uuid": "a1b2c3d4-...",
        "first_name": "Mario",
        "last_name": "Rossi",
        "date_of_birth": "1985-06-15",
        "gender": "Male",
        "contact_number": "3331234567",
        "address": "Via Roma 123, Milano"
      },
      ...
    ]
  }
  ```

#### Ottieni Dettagli Paziente
- **Endpoint**: `/api/patients/<patient_uuid>`
- **Metodo**: GET
- **Descrizione**: Ottiene i dettagli di uno specifico paziente
- **Richiede**: Autenticazione JWT
- **Risposta**:
  ```json
  {
    "patient": {
      "id": 1,
      "uuid": "a1b2c3d4-...",
      "first_name": "Mario",
      "last_name": "Rossi",
      "date_of_birth": "1985-06-15",
      "gender": "Male",
      "contact_number": "3331234567",
      "address": "Via Roma 123, Milano"
    }
  }
  ```

#### Ottieni Segni Vitali Paziente
- **Endpoint**: `/api/patients/<patient_uuid>/vitals`
- **Metodo**: GET
- **Descrizione**: Ottiene i segni vitali di uno specifico paziente
- **Richiede**: Autenticazione JWT
- **Parametri Query (opzionali)**:
  - `type`: Tipo di segno vitale (es. heart_rate, blood_pressure)
  - `start_date`: Data inizio (YYYY-MM-DD)
  - `end_date`: Data fine (YYYY-MM-DD)
- **Risposta**:
  ```json
  {
    "vitals": [
      {
        "id": 1,
        "type": "heart_rate",
        "value": 75,
        "unit": "bpm",
        "recorded_at": "2025-04-21T10:15:30",
        "origin": "manual"
      },
      ...
    ]
  }
  ```

#### Aggiungi Segno Vitale
- **Endpoint**: `/api/patients/<patient_uuid>/vitals`
- **Metodo**: POST
- **Descrizione**: Aggiunge un nuovo segno vitale per un paziente
- **Richiede**: Autenticazione JWT
- **Parametri**:
  - `type`: Tipo di segno vitale (enum VitalSignType)
  - `value`: Valore numerico
  - `unit`: Unità di misura (opzionale)
  - `recorded_at`: Data e ora registrazione (ISO format, opzionale)
- **Risposta**:
  ```json
  {
    "message": "Vital sign added successfully",
    "vital": {
      "id": 15,
      "type": "heart_rate",
      "value": 75,
      "unit": "bpm",
      "recorded_at": "2025-04-21T10:15:30",
      "origin": "manual"
    }
  }
  ```

#### Ottieni Note Paziente
- **Endpoint**: `/api/patients/<patient_uuid>/notes`
- **Metodo**: GET
- **Descrizione**: Ottiene le note mediche per uno specifico paziente
- **Richiede**: Autenticazione JWT
- **Risposta**:
  ```json
  {
    "notes": [
      {
        "id": 1,
        "content": "Il paziente riferisce mal di testa...",
        "created_at": "2025-04-20T15:30:45",
        "doctor": {
          "id": 2,
          "name": "Dr. Luigi Bianchi"
        }
      },
      ...
    ]
  }
  ```

#### Aggiungi Nota
- **Endpoint**: `/api/patients/<patient_uuid>/notes`
- **Metodo**: POST
- **Descrizione**: Aggiunge una nuova nota per un paziente
- **Richiede**: Autenticazione JWT
- **Parametri**:
  - `content`: Testo della nota
- **Risposta**:
  ```json
  {
    "message": "Note added successfully",
    "note": {
      "id": 12,
      "content": "Il paziente riferisce mal di testa...",
      "created_at": "2025-04-21T10:15:30"
    }
  }
  ```

### API Fitbit e Integrazione Dispositivi

#### Verifica Paziente (App Mobile)
- **Endpoint**: `/api/mobile/patient/verify`
- **Metodo**: POST
- **Descrizione**: Verifica l'ID paziente dall'app mobile
- **Parametri**:
  - `patient_uuid`: UUID del paziente
- **Risposta**:
  ```json
  {
    "patient_id": 5,
    "name": "Mario Rossi",
    "success": true
  }
  ```

#### Upload Dati (App Mobile)
- **Endpoint**: `/api/mobile/data/upload`
- **Metodo**: POST
- **Descrizione**: Carica dati Fitbit dall'app mobile
- **Parametri**:
  - `patient_id`: ID del paziente
  - `fitbit_data`: Dati Fitbit (JSON)
- **Risposta**:
  ```json
  {
    "success": true,
    "vitals_saved": 5,
    "message": "Data uploaded successfully"
  }
  ```

#### Verifica Stato Dispositivo
- **Endpoint**: `/api/patients/<patient_id>/device_status`
- **Metodo**: GET
- **Descrizione**: Verifica se un dispositivo Fitbit è connesso
- **Richiede**: Autenticazione JWT/Login
- **Risposta**:
  ```json
  {
    "connected": true,
    "timestamp": "2025-04-21T20:06:41"
  }
  ```

## Sistema di Notifiche

VitaLink utilizza ClickSend per inviare notifiche SMS per eventi critici, come valori vitali anomali.

### Notifica Valori Anomali

```python
def notify_abnormal_vital(patient, vital_type, value, unit, status):
    """
    Invia notifica per segno vitale anomalo
    
    Args:
        patient: Oggetto paziente
        vital_type (str): Tipo di segno vitale
        value (float/str): Valore registrato
        unit (str): Unità di misura
        status (str): 'high' o 'low'
    
    Returns:
        bool: True se successo, False altrimenti
    """
```

### Promemoria Appuntamenti

```python
def send_appointment_reminder(patient, doctor, appointment_date, appointment_time):
    """
    Invia promemoria appuntamento al paziente
    
    Args:
        patient: Oggetto paziente
        doctor: Oggetto medico
        appointment_date: Data appuntamento
        appointment_time: Ora appuntamento
        
    Returns:
        bool: True se successo, False altrimenti
    """
```

## Sistema di Audit

VitaLink include un robusto sistema di audit che traccia tutte le azioni eseguite nel sistema. Questo è importante per la conformità normativa e la sicurezza.

### Funzioni di Audit Principali

```python
def log_action(doctor_id, action_type, entity_type, entity_id, details=None, patient_id=None):
    """
    Crea una nuova voce nel log di audit.
    
    Args:
        doctor_id (int): ID del medico che ha eseguito l'azione
        action_type (ActionType): Tipo di azione eseguita
        entity_type (EntityType): Tipo di entità interessata
        entity_id (int): ID dell'entità interessata
        details (dict, optional): Dettagli aggiuntivi sull'azione
        patient_id (int, optional): ID del paziente relativo all'azione
    
    Returns:
        AuditLog: Voce di log creata o None se si verifica un errore
    """
```

### Funzioni di Audit Specializzate

- `log_patient_creation(doctor_id, patient)`
- `log_patient_update(doctor_id, patient, old_data)`
- `log_patient_delete(doctor_id, patient)`
- `log_vital_creation(doctor_id, vital)`
- `log_note_creation(doctor_id, note)`
- `log_report_generation(doctor_id, patient_id, report_type, params=None)`
- `log_patient_view(doctor_id, patient_id)`

## Integrazione con Dispositivi Fitbit

VitaLink supporta l'integrazione con dispositivi Fitbit per il monitoraggio automatico dei segni vitali.

### Funzioni Principali

```python
def check_device_connected():
    """
    Verifica se un dispositivo Fitbit è connesso via USB.
    
    Returns:
        bool: True se il dispositivo è connesso, False altrimenti
    """

def extract_fitbit_data(patient_id):
    """
    Estrae dati dal dispositivo Fitbit connesso via USB.
    
    Args:
        patient_id (int): ID del paziente da associare ai dati
    
    Returns:
        dict: Dati estratti dal dispositivo
    
    Raises:
        DeviceConnectionError: Se il dispositivo non è connesso o ci sono problemi
    """

def save_fitbit_data(patient_id, data):
    """
    Salva i dati estratti dal dispositivo Fitbit nel database.
    
    Args:
        patient_id (int): ID del paziente da associare ai dati
        data (dict): Dati estratti dal dispositivo
        
    Returns:
        tuple: (success, vitals_saved, errors)
            success (bool): True se i dati sono stati salvati con successo
            vitals_saved (int): Numero di parametri vitali salvati
            errors (list): Lista degli errori verificatisi durante il salvataggio
    """
```

## Reportistica

VitaLink offre funzionalità avanzate di reportistica per generare documenti PDF dettagliati sui dati dei pazienti.

### Funzioni di Reportistica

```python
def generate_patient_report(patient, doctor, vitals, notes, start_date=None, end_date=None, language=None):
    """
    Genera un report PDF per i segni vitali e le note di un paziente
    
    Args:
        patient: Oggetto paziente
        doctor: Oggetto medico
        vitals: Lista di oggetti VitalSign
        notes: Lista di oggetti Note
        start_date: Data inizio filtro (opzionale)
        end_date: Data fine filtro (opzionale)
        language: Codice lingua (it/en)
        
    Returns:
        BytesIO: File PDF come stream binario
    """

def generate_vital_trends_report(patient, vital_type, vitals, period_desc, language=None):
    """
    Genera un report PDF che mostra trend per uno specifico segno vitale
    
    Args:
        patient: Oggetto paziente
        vital_type: Tipo di segno vitale (stringa)
        vitals: Lista di oggetti VitalSign
        period_desc: Descrizione del periodo temporale
        language: Codice lingua (it/en)
        
    Returns:
        BytesIO: File PDF come stream binario
    """
```

## Internazionalizzazione (i18n)

VitaLink supporta completamente la localizzazione in inglese e italiano.

### Gestione Lingua

```python
@app.route('/change_language/<lang_code>')
def change_language(lang_code):
    """
    Cambia la lingua dell'applicazione
    
    Args:
        lang_code: Codice lingua (es. 'en', 'it')
    """
    session['language'] = lang_code
    return redirect(request.referrer or url_for('views.index'))
```

### Rilevamento Automatico Lingua

```python
def get_locale():
    # Prima, controlla se l'utente ha impostato esplicitamente la lingua nella sessione
    if 'language' in session:
        return session['language']
    # Altrimenti, prova a rilevare dalle impostazioni del browser
    best_match = request.accept_languages.best_match(app.config['LANGUAGES'].keys())
    return best_match
```

## Sicurezza

### Protezione CSRF

La protezione CSRF è implementata tramite Flask-WTF:
- Tutti i form ereditano da `FlaskForm` che include protezione CSRF
- I template HTML includono `{{ form.hidden_tag() }}` per il token CSRF
- I form di autenticazione e altre form sensibili utilizzano il campo `csrf_token`

### Hashing Password

```python
def set_password(self, password):
    self.password_hash = generate_password_hash(password)

def check_password(self, password):
    return check_password_hash(self.password_hash, password)
```

### Decoratori di Autenticazione

```python
def api_doctor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Controlla autenticazione JWT per API
        try:
            doctor_id = get_jwt_identity()
            doctor = Doctor.query.get(doctor_id)
            if not doctor:
                return jsonify({"error": "Unauthorized"}), 401
            return f(doctor, *args, **kwargs)
        except Exception as e:
            logger.error(f"API auth error: {str(e)}")
            return jsonify({"error": "Unauthorized"}), 401
    return decorated

def doctor_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        # Controlla autenticazione Web
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated
```

## Considerazioni per Sviluppi Futuri

1. **Notifiche SMS ai Medici**: Implementazione di notifiche per avvisare i medici di valori anomali (Tempo stimato: 45-60 minuti)
2. **Condivisione Pazienti tra Medici**: Funzionalità per consentire a più medici di collaborare sui dati di un paziente (Tempo stimato: 2-3 ore)
3. **Ricerca Globale dei Pazienti**: Implementazione di una funzionalità di ricerca avanzata (Tempo stimato: 3-4 ore)
4. **Sistema di Monitoraggio**: Integrazione di Flask-Monitoring-Dashboard per il monitoraggio delle prestazioni (Tempo stimato: 30-45 minuti)
5. **Backup Automatico Database**: Implementazione di backup programmati del database (Tempo stimato: 30-40 minuti)