# Documentazione delle API VitaLink

Questo documento fornisce una descrizione dettagliata di tutti gli endpoint API disponibili nell'applicazione VitaLink. Gli endpoint sono organizzati per modulo e includono informazioni sul loro scopo, parametri accettati, formati di risposta e codici di stato.

**Ultima revisione**: 06/05/2025 
**Versione**: 1.0
**Autore**: Roggeri Andrea

## Indice
- [Autenticazione](#autenticazione)
- [Gestione Pazienti](#gestione-pazienti)
- [Note Mediche](#note-mediche)
- [Osservazioni dei Parametri Vitali](#osservazioni-dei-parametri-vitali)
- [Piattaforme Sanitarie](#piattaforme-sanitarie)
- [Gestione Interfaccia Web](#gestione-interfaccia-web)
- [Audit e Statistiche](#audit-e-statistiche)
- [Gestione della Lingua](#gestione-della-lingua)

---

## Autenticazione

### Registrazione Medico
**GET `/register`**
- **Modulo**: `app/auth.py`
- **Descrizione**: Mostra il modulo di registrazione per i nuovi medici.
- **Autenticazione**: Non richiesta
- **Risposta**: Form HTML per la registrazione di un nuovo account medico.

**POST `/register`**
- **Modulo**: `app/auth.py`
- **Descrizione**: Elabora il modulo di registrazione e crea un nuovo account medico.
- **Parametri**:
  - `email`: Indirizzo email del medico (deve essere univoco)
  - `first_name`: Nome del medico
  - `last_name`: Cognome del medico
  - `specialty`: Specializzazione medica
  - `password`: Password (deve soddisfare i requisiti di sicurezza)
  - `confirm_password`: Conferma della password
- **Risposta**: Reindirizzamento alla pagina di login in caso di successo, altrimenti visualizzazione del modulo con messaggi di errore.

### Login Medico
**GET `/login`**
- **Modulo**: `app/auth.py`
- **Descrizione**: Mostra il modulo di login per i medici.
- **Autenticazione**: Non richiesta
- **Risposta**: Form HTML per il login.

**POST `/login`**
- **Modulo**: `app/auth.py`
- **Descrizione**: Autentica un medico e stabilisce una sessione.
- **Parametri**:
  - `email`: Indirizzo email del medico
  - `password`: Password dell'account medico
- **Risposta**: Reindirizzamento alla dashboard in caso di successo, altrimenti visualizzazione del modulo di login con messaggi di errore.

### Logout Medico
**GET `/logout`**
- **Modulo**: `app/auth.py`
- **Descrizione**: Termina la sessione autenticata del medico.
- **Autenticazione**: Richiesta
- **Risposta**: Reindirizzamento alla pagina di login con messaggio di conferma.

### API Login
**POST `/api/login`**
- **Modulo**: `app/auth.py`
- **Descrizione**: Endpoint API per l'autenticazione dei medici. Valida le credenziali e genera token JWT per l'accesso alle API.
- **Tipo di Contenuto**: JSON
- **Parametri**:
  ```json
  {
    "email": "medico@esempio.com",
    "password": "password_sicura"
  }
  ```
- **Risposta di Successo** (200 OK):
  ```json
  {
    "message": "Login effettuato con successo",
    "doctor": {
      "id": 1,
      "first_name": "Mario",
      "last_name": "Rossi",
      "email": "medico@esempio.com",
      "specialty": "Cardiologia"
    },
    "access_token": "eyJhbGciOiJIUz...",
    "refresh_token": "eyJhbGciOiJIUz..."
  }
  ```
- **Possibili Errori**:
  - 400 Bad Request: Richiesta JSON mancante o credenziali incomplete
  - 401 Unauthorized: Credenziali non valide

### Aggiornamento Token
**POST `/api/refresh-token`**
- **Modulo**: `app/auth.py`
- **Descrizione**: Genera un nuovo access token utilizzando un refresh token valido. Questo endpoint consente di mantenere le sessioni API attive senza richiedere un nuovo login.
- **Autenticazione**: Refresh token JWT richiesto nell'header Authorization
- **Risposta di Successo** (200 OK):
  ```json
  {
    "access_token": "eyJhbGciOiJIUz..."
  }
  ```
- **Possibili Errori**:
  - 401 Unauthorized: Token di aggiornamento mancante o non valido

---

## Gestione Pazienti

### Elenco Pazienti
**GET `/api/patients`**
- **Modulo**: `app/api.py`
- **Descrizione**: Recupera l'elenco di tutti i pazienti associati al medico autenticato.
- **Autenticazione**: JWT richiesto
- **Risposta di Successo** (200 OK):
  ```json
  {
    "patients": [
      {
        "id": 1,
        "uuid": "123e4567-e89b-12d3-a456-426614174000",
        "first_name": "Giovanni",
        "last_name": "Bianchi",
        "date_of_birth": "1980-05-15",
        "gender": "male",
        "contact_info": "telefono: +39 123456789",
        "created_at": "2023-05-01T14:30:00Z"
      },
      // altri pazienti...
    ]
  }
  ```

### Dettagli Paziente
**GET `/api/patients/<string:patient_uuid>`**
- **Modulo**: `app/api.py`
- **Descrizione**: Ottiene informazioni dettagliate su un paziente specifico.
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `patient_uuid` - UUID univoco del paziente
- **Risposta di Successo** (200 OK):
  ```json
  {
    "patient": {
      "id": 1,
      "uuid": "123e4567-e89b-12d3-a456-426614174000",
      "first_name": "Giovanni",
      "last_name": "Bianchi",
      "date_of_birth": "1980-05-15",
      "gender": "male",
      "contact_info": "telefono: +39 123456789",
      "medical_history": "Ipertensione, allergia agli arachidi",
      "created_at": "2023-05-01T14:30:00Z"
    }
  }
  ```
- **Possibili Errori**:
  - 400 Bad Request: Formato UUID non valido
  - 403 Forbidden: Medico non autorizzato ad accedere a questo paziente
  - 404 Not Found: Paziente non trovato

### Parametri Vitali del Paziente
**GET `/api/patients/<string:patient_uuid>/vitals`**
- **Modulo**: `app/api.py`
- **Descrizione**: Recupera i parametri vitali di un paziente dalla piattaforma sanitaria collegata (ad es. Fitbit).
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `patient_uuid` - UUID univoco del paziente
- **Parametri Query**:
  - `type` (opzionale): Tipo di segno vitale da recuperare (es. 'heart_rate', 'steps')
  - `start_date` (opzionale): Data di inizio per il range di dati in formato ISO (YYYY-MM-DD)
  - `end_date` (opzionale): Data di fine per il range di dati in formato ISO (YYYY-MM-DD)
- **Risposta di Successo** (200 OK, esempio per type='heart_rate'):
  ```json
  {
    "heart_rate": [
      {
        "timestamp": "2023-05-01T14:30:00Z",
        "value": 72,
        "unit": "bpm"
      },
      // altri dati di frequenza cardiaca...
    ]
  }
  ```
- **Possibili Errori**:
  - 400 Bad Request: Formato UUID non valido
  - 403 Forbidden: Medico non autorizzato ad accedere a questo paziente
  - 404 Not Found: Paziente non trovato o connessione alla piattaforma sanitaria mancante
  - 500 Internal Server Error: Errore nel recupero dei dati dalla piattaforma sanitaria

---

## Note Mediche

### Elenco Note
**GET `/api/patients/<string:patient_uuid>/notes`**
- **Modulo**: `app/api.py`
- **Descrizione**: Recupera tutte le note mediche associate a un paziente specifico.
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `patient_uuid` - UUID univoco del paziente
- **Risposta di Successo** (200 OK):
  ```json
  {
    "notes": [
      {
        "id": 1,
        "content": "Il paziente ha riportato un miglioramento dei sintomi",
        "doctor_id": 2,
        "doctor_name": "Dott.ssa Laura Verdi",
        "created_at": "2023-05-01T14:30:00Z"
      },
      // altre note...
    ]
  }
  ```
- **Possibili Errori**:
  - 400 Bad Request: Formato UUID non valido
  - 403 Forbidden: Medico non autorizzato ad accedere a questo paziente
  - 404 Not Found: Paziente non trovato

### Aggiunta Nota
**POST `/api/patients/<string:patient_uuid>/notes`**
- **Modulo**: `app/api.py`
- **Descrizione**: Aggiunge una nuova nota medica per un paziente specifico.
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `patient_uuid` - UUID univoco del paziente
- **Corpo Richiesta**:
  ```json
  {
    "content": "Il paziente ha riportato un miglioramento dei sintomi dopo il cambio di terapia."
  }
  ```
- **Risposta di Successo** (201 Created):
  ```json
  {
    "message": "Nota aggiunta con successo",
    "note": {
      "id": 2,
      "content": "Il paziente ha riportato un miglioramento dei sintomi dopo il cambio di terapia.",
      "doctor_id": 2,
      "doctor_name": "Dott.ssa Laura Verdi",
      "created_at": "2023-05-10T09:15:00Z"
    }
  }
  ```
- **Possibili Errori**:
  - 400 Bad Request: Formato UUID non valido, JSON mancante o contenuto vuoto
  - 403 Forbidden: Medico non autorizzato ad accedere a questo paziente
  - 404 Not Found: Paziente non trovato
  - 500 Internal Server Error: Errore del database

### Eliminazione Nota
**DELETE `/api/notes/<int:note_id>`**
- **Modulo**: `app/api.py`
- **Descrizione**: Elimina una nota medica specifica.
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `note_id` - ID univoco della nota
- **Risposta di Successo** (200 OK):
  ```json
  {
    "message": "Nota eliminata con successo"
  }
  ```
- **Possibili Errori**:
  - 403 Forbidden: Il medico non è autorizzato a eliminare questa nota (solo il creatore può eliminarla)
  - 404 Not Found: Nota non trovata
  - 500 Internal Server Error: Errore del database

---

## Osservazioni dei Parametri Vitali

### Elenco Osservazioni
**GET `/api/patients/<int:patient_id>/observations`**
- **Modulo**: `app/api.py`
- **Descrizione**: Recupera le osservazioni sui parametri vitali per un paziente specifico.
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `patient_id` - ID del paziente
- **Parametri Query**:
  - `start_date` (opzionale): Data di inizio per filtrare le osservazioni in formato ISO
  - `end_date` (opzionale): Data di fine per filtrare le osservazioni in formato ISO
  - `vital_type` (opzionale): Tipo di segno vitale per filtrare le osservazioni
- **Risposta di Successo** (200 OK):
  ```json
  [
    {
      "id": 1,
      "patient_id": 1,
      "doctor_id": 2,
      "doctor_name": "Dott.ssa Laura Verdi",
      "vital_type": "heart_rate",
      "content": "La frequenza cardiaca si è stabilizzata dopo il cambio di farmaco",
      "start_date": "2023-05-01T00:00:00Z",
      "end_date": "2023-05-07T23:59:59Z",
      "created_at": "2023-05-08T10:15:30Z"
    },
    // altre osservazioni...
  ]
  ```
- **Possibili Errori**:
  - 400 Bad Request: Formato della data non valido o tipo di segno vitale non valido
  - 403 Forbidden: Medico non autorizzato ad accedere a questo paziente
  - 404 Not Found: Paziente non trovato

### Aggiunta Osservazione
**POST `/api/observations`**
- **Modulo**: `app/observations.py`
- **Descrizione**: Crea una nuova osservazione sui parametri vitali di un paziente.
- **Autenticazione**: JWT richiesto
- **Corpo Richiesta**:
  ```json
  {
    "patient_id": 1,
    "vital_type": "heart_rate",
    "content": "La frequenza cardiaca si è stabilizzata dopo il cambio di farmaco",
    "start_date": "2023-05-01T00:00:00Z",
    "end_date": "2023-05-07T23:59:59Z"
  }
  ```
- **Risposta di Successo** (201 Created):
  ```json
  {
    "message": "Osservazione aggiunta con successo",
    "observation": {
      "id": 1,
      "patient_id": 1,
      "doctor_id": 2,
      "vital_type": "heart_rate",
      "content": "La frequenza cardiaca si è stabilizzata dopo il cambio di farmaco",
      "start_date": "2023-05-01T00:00:00Z",
      "end_date": "2023-05-07T23:59:59Z",
      "created_at": "2023-05-08T10:15:30Z"
    }
  }
  ```
- **Possibili Errori**:
  - 400 Bad Request: Dati mancanti o non validi
  - 403 Forbidden: Non autorizzato a creare osservazioni per questo paziente
  - 404 Not Found: Paziente non trovato
  - 500 Internal Server Error: Errore del database

### Modifica Osservazione
**PUT `/api/observations/<int:observation_id>`**
- **Modulo**: `app/observations.py`
- **Descrizione**: Aggiorna una osservazione sui parametri vitali esistente.
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `observation_id` - ID dell'osservazione
- **Corpo Richiesta**:
  ```json
  {
    "vital_type": "heart_rate",
    "content": "La frequenza cardiaca si è normalizzata e rimane stabile dopo due settimane di nuova terapia",
    "start_date": "2023-05-01T00:00:00Z",
    "end_date": "2023-05-15T23:59:59Z"
  }
  ```
- **Risposta di Successo** (200 OK):
  ```json
  {
    "message": "Osservazione aggiornata con successo",
    "observation": {
      "id": 1,
      "patient_id": 1,
      "doctor_id": 2,
      "vital_type": "heart_rate",
      "content": "La frequenza cardiaca si è normalizzata e rimane stabile dopo due settimane di nuova terapia",
      "start_date": "2023-05-01T00:00:00Z",
      "end_date": "2023-05-15T23:59:59Z",
      "updated_at": "2023-05-16T09:30:00Z",
      "created_at": "2023-05-08T10:15:30Z"
    }
  }
  ```
- **Possibili Errori**:
  - 400 Bad Request: Dati mancanti o non validi
  - 403 Forbidden: Non autorizzato a modificare questa osservazione
  - 404 Not Found: Osservazione non trovata
  - 500 Internal Server Error: Errore del database

### Eliminazione Osservazione
**DELETE `/api/observations/<int:observation_id>`**
- **Modulo**: `app/observations.py`
- **Descrizione**: Elimina un'osservazione sui parametri vitali.
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `observation_id` - ID dell'osservazione
- **Risposta di Successo** (200 OK):
  ```json
  {
    "message": "Osservazione eliminata con successo"
  }
  ```
- **Possibili Errori**:
  - 403 Forbidden: Non autorizzato a eliminare questa osservazione
  - 404 Not Found: Osservazione non trovata
  - 500 Internal Server Error: Errore del database

---

## Piattaforme Sanitarie

### Connessione Piattaforma
**POST `/health-platforms/connect/<string:platform_name>`**
- **Modulo**: `app/health_platforms.py`
- **Descrizione**: Connette un paziente a una piattaforma sanitaria esterna (es. Fitbit).
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `platform_name` - Nome della piattaforma sanitaria (es. 'fitbit')
- **Corpo Richiesta**:
  ```json
  {
    "patient_id": 1,
    "access_token": "oauth-access-token",
    "refresh_token": "oauth-refresh-token",
    "expires_at": "2024-05-01T00:00:00Z"
  }
  ```
- **Risposta di Successo** (200 OK):
  ```json
  {
    "message": "Connessione alla piattaforma sanitaria avvenuta con successo",
    "platform": "fitbit",
    "patient_id": 1
  }
  ```

### Elenco Piattaforme
**GET `/health-platforms`**
- **Modulo**: `app/health_platforms.py`
- **Descrizione**: Recupera l'elenco di tutte le piattaforme sanitarie supportate.
- **Autenticazione**: JWT richiesto
- **Risposta di Successo** (200 OK):
  ```json
  {
    "platforms": [
      {
        "name": "fitbit",
        "display_name": "Fitbit",
        "description": "Piattaforma per il monitoraggio dell'attività fisica e dei parametri vitali",
        "auth_type": "oauth2"
      },
      // altre piattaforme...
    ]
  }
  ```

### Dettagli Piattaforma
**GET `/health-platforms/<string:platform_name>`**
- **Modulo**: `app/health_platforms.py`
- **Descrizione**: Ottiene informazioni dettagliate su una piattaforma sanitaria specifica.
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `platform_name` - Nome della piattaforma sanitaria
- **Risposta di Successo** (200 OK):
  ```json
  {
    "name": "fitbit",
    "display_name": "Fitbit",
    "description": "Piattaforma per il monitoraggio dell'attività fisica e dei parametri vitali",
    "auth_type": "oauth2",
    "supported_vitals": ["heart_rate", "steps", "sleep", "activity"]
  }
  ```
  
### Connessioni Piattaforma Paziente
**GET `/health-platforms/patients/<int:patient_id>`**
- **Modulo**: `app/health_platforms.py`
- **Descrizione**: Ottiene informazioni sulle connessioni alle piattaforme sanitarie di un paziente specifico.
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `patient_id` - ID del paziente
- **Risposta di Successo** (200 OK):
  ```json
  {
    "connections": [
      {
        "platform": "fitbit",
        "connected_at": "2023-01-15T10:30:00Z",
        "status": "active"
      }
      // altre connessioni...
    ]
  }
  ```

### Dati Fitbit
**GET `/health-platforms/fitbit/<string:patient_uuid>`**
- **Modulo**: `app/health_platforms.py`
- **Descrizione**: Recupera i dati Fitbit per un paziente specifico.
- **Autenticazione**: JWT richiesto
- **Parametri URL**: `patient_uuid` - UUID del paziente
- **Parametri Query**:
  - `type` (opzionale): Tipo di dati Fitbit da recuperare (es. 'heart_rate', 'sleep')
  - `start_date` (opzionale): Data di inizio in formato ISO
  - `end_date` (opzionale): Data di fine in formato ISO
- **Risposta di Successo** (200 OK):
  ```json
  {
    "data": {
      // Dati Fitbit in formato specifico per il tipo richiesto
    }
  }
  ```

---

## Gestione Interfaccia Web

### Dashboard
**GET `/dashboard`**
- **Modulo**: `app/views.py`
- **Descrizione**: Visualizza la dashboard principale del medico con panoramica dei pazienti, attività recenti e statistiche.
- **Autenticazione**: Login richiesto
- **Risposta**: Pagina HTML della dashboard.

### Elenco Pazienti
**GET `/patients`**
- **Modulo**: `app/views.py`
- **Descrizione**: Mostra l'elenco di tutti i pazienti associati al medico autenticato.
- **Autenticazione**: Login richiesto
- **Risposta**: Pagina HTML con l'elenco dei pazienti.

### Importazione Paziente
**POST `/patients/import`**
- **Modulo**: `app/views.py`
- **Descrizione**: Importa un paziente esistente nel sistema associandolo al medico corrente tramite UUID.
- **Autenticazione**: Login richiesto
- **Corpo Richiesta**:
  ```json
  {
    "patient_uuid": "123e4567-e89b-12d3-a456-426614174000"
  }
  ```
- **Risposta di Successo** (200 OK):
  ```json
  {
    "message": "Paziente importato con successo",
    "patient": {
      // dettagli paziente...
    }
  }
  ```

### Nuovo Paziente
**GET `/patients/new`**
- **Modulo**: `app/views.py`
- **Descrizione**: Mostra il modulo per la creazione di un nuovo paziente.
- **Autenticazione**: Login richiesto
- **Risposta**: Pagina HTML con il form per la creazione del paziente.

**POST `/patients/new`**
- **Modulo**: `app/views.py`
- **Descrizione**: Processa il modulo di creazione paziente e crea un nuovo record paziente.
- **Autenticazione**: Login richiesto
- **Parametri**:
  - `first_name`: Nome del paziente
  - `last_name`: Cognome del paziente
  - `date_of_birth`: Data di nascita
  - `gender`: Genere
  - `contact_info`: Informazioni di contatto
  - `medical_history`: Storia clinica (opzionale)
- **Risposta**: Reindirizzamento alla pagina del paziente in caso di successo, altrimenti ripresentazione del modulo con errori.

### Dettagli Paziente
**GET `/patients/<int:patient_id>`**
- **Modulo**: `app/views.py`
- **Descrizione**: Mostra la pagina con i dettagli di un paziente specifico.
- **Autenticazione**: Login richiesto
- **Parametri URL**: `patient_id` - ID del paziente
- **Risposta**: Pagina HTML con dettagli paziente, parametri vitali e note mediche.

### Modifica Paziente
**GET `/patients/<int:patient_id>/edit`**
- **Modulo**: `app/views.py`
- **Descrizione**: Mostra il modulo per la modifica di un paziente esistente.
- **Autenticazione**: Login richiesto
- **Parametri URL**: `patient_id` - ID del paziente
- **Risposta**: Pagina HTML con il form per la modifica del paziente.

**POST `/patients/<int:patient_id>/edit`**
- **Modulo**: `app/views.py`
- **Descrizione**: Processa il modulo di modifica paziente e aggiorna il record.
- **Autenticazione**: Login richiesto
- **Parametri URL**: `patient_id` - ID del paziente
- **Parametri Form**: Stessi del POST `/patients/new`
- **Risposta**: Reindirizzamento alla pagina del paziente in caso di successo, altrimenti ripresentazione del modulo con errori.

### Eliminazione Paziente
**POST `/patients/<int:patient_id>/delete`**
- **Modulo**: `app/views.py`
- **Descrizione**: Elimina un paziente dal sistema o rimuove l'associazione tra il medico e il paziente.
- **Autenticazione**: Login richiesto
- **Parametri URL**: `patient_id` - ID del paziente
- **Risposta**: Reindirizzamento all'elenco dei pazienti con messaggio di conferma.

### Parametri Vitali Paziente
**GET `/patients/<int:patient_id>/vitals`**
- **Modulo**: `app/views.py`
- **Descrizione**: Mostra la pagina dei parametri vitali di un paziente specifico.
- **Autenticazione**: Login richiesto
- **Parametri URL**: `patient_id` - ID del paziente
- **Risposta**: Pagina HTML con grafici e tabelle dei parametri vitali.

### Note Paziente
**POST `/patients/<int:patient_id>/notes`**
- **Modulo**: `app/views.py`
- **Descrizione**: Aggiunge una nuova nota medica per un paziente specifico attraverso l'interfaccia web.
- **Autenticazione**: Login richiesto
- **Parametri URL**: `patient_id` - ID del paziente
- **Parametri Form**:
  - `content`: Contenuto della nota
- **Risposta**: Reindirizzamento alla pagina del paziente con la nuova nota visibile.

### Eliminazione Nota
**DELETE `/notes/<int:note_id>`**
- **Modulo**: `app/views.py`
- **Descrizione**: Elimina una nota medica specifica attraverso l'interfaccia web.
- **Autenticazione**: Login richiesto
- **Parametri URL**: `note_id` - ID della nota
- **Risposta**: Risposta JSON di conferma o errore.

### Report
**GET `/reports`**
- **Modulo**: `app/views.py`
- **Descrizione**: Mostra la pagina per la generazione di report.
- **Autenticazione**: Login richiesto
- **Risposta**: Pagina HTML con opzioni per la generazione di report.

**POST `/reports`**
- **Modulo**: `app/views.py`
- **Descrizione**: Genera e scarica un report basato sui parametri specificati.
- **Autenticazione**: Login richiesto
- **Parametri Form**:
  - `report_type`: Tipo di report da generare
  - `start_date`: Data di inizio del report
  - `end_date`: Data di fine del report
  - `patient_id` (opzionale): ID del paziente se il report è specifico per un paziente
- **Risposta**: File del report (PDF, CSV, ecc.) scaricabile o messaggio di errore.

### Report Specifico
**GET `/reports/<int:report_id>/specific_report`**
- **Modulo**: `app/views.py`
- **Descrizione**: Visualizza o scarica un report specifico generato in precedenza.
- **Autenticazione**: Login richiesto
- **Parametri URL**: `report_id` - ID del report
- **Risposta**: File del report o pagina di visualizzazione.

**POST `/reports/<int:report_id>/specific_report`**
- **Modulo**: `app/views.py`
- **Descrizione**: Aggiorna o rigenera un report specifico.
- **Autenticazione**: Login richiesto
- **Parametri URL**: `report_id` - ID del report
- **Risposta**: File del report aggiornato o messaggio di errore.

---

## Audit e Statistiche

### Log di Audit
**GET `/audit/logs`**
- **Modulo**: `app/audit.py`
- **Descrizione**: Visualizza i log di audit con possibilità di filtraggio.
- **Autenticazione**: Login richiesto (solo per amministratori)
- **Parametri Query**:
  - `start_date` (opzionale): Data di inizio per il filtraggio
  - `end_date` (opzionale): Data di fine per il filtraggio
  - `doctor_id` (opzionale): ID del medico per filtrare le azioni
  - `action_type` (opzionale): Tipo di azione da filtrare
- **Risposta**: Pagina HTML con i log filtrati.

### Statistiche
**GET `/audit/stats`**
- **Modulo**: `app/audit.py`
- **Descrizione**: Visualizza le statistiche aggregate dell'uso del sistema.
- **Autenticazione**: Login richiesto (solo per amministratori)
- **Risposta**: Pagina HTML con grafici e tabelle statistiche.

---

## Gestione della Lingua

### Cambio Lingua
**GET `/lang/<string:lang_code>`**
- **Modulo**: `app/language.py`
- **Descrizione**: Cambia la lingua dell'interfaccia utente.
- **Autenticazione**: Non richiesta
- **Parametri URL**: `lang_code` - Codice della lingua (es. 'it', 'en')
- **Risposta**: Reindirizzamento alla pagina precedente con la nuova lingua impostata.
