# VitaLink - Documentazione API

## Panoramica API

VitaLink offre una serie di API RESTful che consentono l'integrazione con sistemi esterni, applicazioni mobili o interfacce personalizzate. Questa documentazione fornisce dettagli su tutti gli endpoint API disponibili, i loro parametri, le risposte attese e gli esempi di utilizzo.

## Autenticazione

Tutte le API VitaLink (ad eccezione degli endpoint mobile) richiedono autenticazione tramite JSON Web Token (JWT). Per ottenere un token, è necessario effettuare una richiesta di login con le credenziali valide di un medico.

### Ottenere Token di Accesso

**Endpoint**: `/api/login`  
**Metodo**: POST  
**Content-Type**: `application/json`

**Richiesta**:
```json
{
  "email": "medico@example.com",
  "password": "password_sicura"
}
```

**Risposta di Successo** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "message": "Login successful"
}
```

**Risposta di Errore** (401 Unauthorized):
```json
{
  "error": "Invalid credentials"
}
```

### Utilizzare il Token

Per tutte le successive richieste API, includi il token di accesso nell'header HTTP:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Aggiornare il Token

Quando il token di accesso scade (dopo 1 ora), utilizzare il refresh token per ottenerne uno nuovo:

**Endpoint**: `/api/refresh`  
**Metodo**: POST  
**Header**: `Authorization: Bearer <refresh_token>`

**Risposta di Successo** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "message": "Token refreshed successfully"
}
```

## API Pazienti

### Elenco Pazienti

Restituisce tutti i pazienti associati al medico autenticato.

**Endpoint**: `/api/patients`  
**Metodo**: GET  
**Richiede**: Autenticazione JWT

**Risposta di Successo** (200 OK):
```json
{
  "patients": [
    {
      "id": 1,
      "uuid": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
      "first_name": "Mario",
      "last_name": "Rossi",
      "date_of_birth": "1985-06-15",
      "gender": "Male",
      "contact_number": "3331234567",
      "address": "Via Roma 123, Milano",
      "created_at": "2024-12-01T10:30:45Z",
      "updated_at": "2025-03-15T14:22:10Z"
    },
    {
      "id": 2,
      "uuid": "q1w2e3r4-t5y6-u7i8-o9p0-a1s2d3f4g5h6",
      "first_name": "Anna",
      "last_name": "Bianchi",
      "date_of_birth": "1990-09-22",
      "gender": "Female",
      "contact_number": "3497654321",
      "address": "Via Dante 45, Torino",
      "created_at": "2025-01-15T09:45:30Z",
      "updated_at": "2025-04-10T11:20:15Z"
    }
  ]
}
```

### Dettagli Paziente

Restituisce i dettagli di uno specifico paziente identificato dal suo UUID.

**Endpoint**: `/api/patients/<patient_uuid>`  
**Metodo**: GET  
**Richiede**: Autenticazione JWT

**Risposta di Successo** (200 OK):
```json
{
  "patient": {
    "id": 1,
    "uuid": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "first_name": "Mario",
    "last_name": "Rossi",
    "date_of_birth": "1985-06-15",
    "gender": "Male",
    "contact_number": "3331234567",
    "address": "Via Roma 123, Milano",
    "created_at": "2024-12-01T10:30:45Z",
    "updated_at": "2025-03-15T14:22:10Z"
  }
}
```

**Risposte di Errore**:
- 400 Bad Request: UUID non valido
- 404 Not Found: Paziente non trovato
- 403 Forbidden: Medico non autorizzato ad accedere a questo paziente

### Segni Vitali del Paziente

Ottiene i segni vitali di un paziente specifico, con opzioni di filtro.

**Endpoint**: `/api/patients/<patient_uuid>/vitals`  
**Metodo**: GET  
**Richiede**: Autenticazione JWT

**Parametri Query (opzionali)**:
- `type`: Filtra per tipo di segno vitale (heart_rate, blood_pressure, ecc.)
- `start_date`: Filtra per data inizio (formato YYYY-MM-DD)
- `end_date`: Filtra per data fine (formato YYYY-MM-DD)

**Risposta di Successo** (200 OK):
```json
{
  "vitals": [
    {
      "id": 1,
      "type": "heart_rate",
      "value": 75,
      "unit": "bpm",
      "recorded_at": "2025-04-20T10:15:30Z",
      "origin": "manual",
      "created_at": "2025-04-20T10:15:30Z"
    },
    {
      "id": 2,
      "type": "blood_pressure",
      "value": 120.80,
      "unit": "mmHg",
      "recorded_at": "2025-04-20T10:16:45Z",
      "origin": "manual",
      "created_at": "2025-04-20T10:16:45Z"
    },
    {
      "id": 3,
      "type": "temperature",
      "value": 36.5,
      "unit": "°C",
      "recorded_at": "2025-04-20T10:18:20Z",
      "origin": "manual",
      "created_at": "2025-04-20T10:18:20Z"
    }
  ]
}
```

### Aggiungere un Segno Vitale

Registra un nuovo segno vitale per un paziente specifico.

**Endpoint**: `/api/patients/<patient_uuid>/vitals`  
**Metodo**: POST  
**Richiede**: Autenticazione JWT  
**Content-Type**: `application/json`

**Richiesta**:
```json
{
  "type": "heart_rate",
  "value": 78,
  "unit": "bpm",
  "recorded_at": "2025-04-21T11:30:00Z"
}
```

**Risposta di Successo** (201 Created):
```json
{
  "message": "Vital sign added successfully",
  "vital": {
    "id": 15,
    "type": "heart_rate",
    "value": 78,
    "unit": "bpm",
    "recorded_at": "2025-04-21T11:30:00Z",
    "origin": "manual",
    "created_at": "2025-04-21T15:45:22Z"
  }
}
```

**Risposte di Errore**:
- 400 Bad Request: Dati non validi o incompleti
- 404 Not Found: Paziente non trovato
- 403 Forbidden: Medico non autorizzato ad accedere a questo paziente

### Note del Paziente

Ottiene le note mediche per un paziente specifico.

**Endpoint**: `/api/patients/<patient_uuid>/notes`  
**Metodo**: GET  
**Richiede**: Autenticazione JWT

**Risposta di Successo** (200 OK):
```json
{
  "notes": [
    {
      "id": 1,
      "content": "Il paziente riferisce mal di testa persistente da tre giorni. Consigliato riposo e paracetamolo al bisogno.",
      "created_at": "2025-04-15T15:30:45Z",
      "updated_at": "2025-04-15T15:30:45Z",
      "doctor": {
        "id": 2,
        "name": "Dr. Luigi Bianchi"
      }
    },
    {
      "id": 2,
      "content": "Follow-up: il mal di testa è migliorato ma persiste sensazione di stanchezza. Prescritti esami del sangue di routine.",
      "created_at": "2025-04-18T09:15:20Z",
      "updated_at": "2025-04-18T09:18:35Z",
      "doctor": {
        "id": 2,
        "name": "Dr. Luigi Bianchi"
      }
    }
  ]
}
```

### Aggiungere una Nota

Registra una nuova nota medica per un paziente specifico.

**Endpoint**: `/api/patients/<patient_uuid>/notes`  
**Metodo**: POST  
**Richiede**: Autenticazione JWT  
**Content-Type**: `application/json`

**Richiesta**:
```json
{
  "content": "Visita di controllo: il paziente presenta miglioramento significativo. Pressione sanguigna tornata nella norma. Consigliato di mantenere la terapia attuale."
}
```

**Risposta di Successo** (201 Created):
```json
{
  "message": "Note added successfully",
  "note": {
    "id": 12,
    "content": "Visita di controllo: il paziente presenta miglioramento significativo. Pressione sanguigna tornata nella norma. Consigliato di mantenere la terapia attuale.",
    "created_at": "2025-04-21T10:15:30Z",
    "updated_at": "2025-04-21T10:15:30Z",
    "doctor_id": 2
  }
}
```

**Risposte di Errore**:
- 400 Bad Request: Dati non validi o incompleti
- 404 Not Found: Paziente non trovato
- 403 Forbidden: Medico non autorizzato ad accedere a questo paziente

## API Integrazione Fitbit

### Verifica Stato Dispositivo

Verifica se un dispositivo Fitbit è attualmente connesso al sistema.

**Endpoint**: `/api/patients/<patient_id>/device_status`  
**Metodo**: GET  
**Richiede**: Autenticazione JWT

**Risposta di Successo** (200 OK):
```json
{
  "connected": true,
  "timestamp": "2025-04-21T20:06:41Z"
}
```

### Verifica Paziente (App Mobile)

Verifica l'esistenza di un paziente tramite il suo UUID, utilizzato dall'app mobile.

**Endpoint**: `/api/mobile/patient/verify`  
**Metodo**: POST  
**Content-Type**: `application/json`

**Richiesta**:
```json
{
  "patient_uuid": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
}
```

**Risposta di Successo** (200 OK):
```json
{
  "patient_id": 5,
  "name": "Mario Rossi",
  "success": true
}
```

**Risposte di Errore**:
- 400 Bad Request: UUID mancante o non valido
- 404 Not Found: Paziente non trovato

### Upload Dati (App Mobile)

Carica i dati raccolti da un dispositivo Fitbit tramite l'app mobile.

**Endpoint**: `/api/mobile/data/upload`  
**Metodo**: POST  
**Content-Type**: `application/json`

**Richiesta**:
```json
{
  "patient_id": 5,
  "fitbit_data": {
    "heart_rate": [
      {"timestamp": "2025-04-21T12:30:00Z", "value": 75},
      {"timestamp": "2025-04-21T13:00:00Z", "value": 78},
      {"timestamp": "2025-04-21T13:30:00Z", "value": 80}
    ],
    "steps": [
      {"timestamp": "2025-04-21", "value": 8500}
    ],
    "calories": [
      {"timestamp": "2025-04-21", "value": 2100}
    ],
    "sleep_duration": [
      {"timestamp": "2025-04-20", "value": 7.5}
    ]
  }
}
```

**Risposta di Successo** (200 OK):
```json
{
  "success": true,
  "vitals_saved": 6,
  "message": "Data uploaded successfully",
  "errors": []
}
```

**Risposte di Errore**:
- 400 Bad Request: Dati mancanti o non validi
- 404 Not Found: Paziente non trovato
- 500 Internal Server Error: Errore durante il salvataggio dei dati

## Gestione degli Errori

Tutte le API di VitaLink utilizzano codici di stato HTTP standard e restituiscono messaggi di errore consistenti:

### Formato Errore Generale

```json
{
  "error": "Descrizione dell'errore",
  "code": "CODICE_ERRORE",  // opzionale
  "details": {  // opzionale, dettagli aggiuntivi
    ...
  }
}
```

### Codici di Stato Comuni

- **200 OK**: Richiesta completata con successo
- **201 Created**: Risorsa creata con successo
- **400 Bad Request**: Parametri della richiesta non validi o incompleti
- **401 Unauthorized**: Autenticazione richiesta o fallita
- **403 Forbidden**: Autenticazione riuscita ma accesso negato
- **404 Not Found**: Risorsa non trovata
- **422 Unprocessable Entity**: Dati inviati validi ma non elaborabili
- **500 Internal Server Error**: Errore interno del server

## Note sull'Utilizzo

1. **Rate Limiting**: Per prevenire abusi, VitaLink implementa limitazioni al numero di richieste API. Le richieste eccedenti riceveranno un codice di stato 429 (Too Many Requests).

2. **Formato Date**: Tutte le date devono essere fornite in formato ISO 8601 (YYYY-MM-DDTHH:MM:SSZ).

3. **Sicurezza**: Non trasmettere mai informazioni sensibili dei pazienti in parametri URL. Utilizzare sempre il corpo della richiesta JSON per dati sensibili.

4. **Token JWT**: I token di accesso hanno una validità di 1 ora, mentre i refresh token scadono dopo 24 ore.

5. **Controllo Versione**: Questa documentazione si riferisce alla versione 1.0 delle API VitaLink.