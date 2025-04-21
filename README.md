# VitaLink - Sistema di Monitoraggio Sanitario

VitaLink è una piattaforma completa per il monitoraggio dei pazienti, sviluppata come parte di una tesi di laurea triennale in ingegneria informatica.

## Caratteristiche

- 👩‍⚕️ Dashboard per medici con visualizzazione dei pazienti e parametri vitali
- 📊 Monitoraggio dei parametri vitali con avvisi per valori anomali
- 📱 Integrazione con dispositivi Fitbit per importazione automatica dei dati
- 📄 Generazione di report PDF dettagliati
- 📨 Notifiche SMS per eventi critici
- 🔄 Tracciamento completo delle attività e audit log
- 🌍 Interfaccia completamente multilingue (Italiano e Inglese)

## Requisiti

- Docker e Docker Compose
- Account Twilio per notifiche SMS (opzionale)
- Account SendGrid per notifiche email (opzionale)

## Deployment con Docker

### 1. Configurazione delle variabili d'ambiente

Copia il file `.env-example` in un nuovo file `.env` e configura le variabili d'ambiente:

```bash
cp .env-example .env
```

Modifica il file `.env` con i tuoi valori, in particolare per:
- Credenziali database
- Chiavi API Twilio e SendGrid
- Chiave segreta di sessione

### 2. Costruzione e avvio dei container

```bash
docker-compose up -d
```

Questo comando costruirà l'immagine Docker per l'applicazione e avvierà sia il container dell'applicazione che quello del database PostgreSQL.

### 3. Verifica del deployment

L'applicazione sarà disponibile su `http://localhost:5000`

Per visualizzare i log dell'applicazione:
```bash
docker-compose logs -f web
```

### 4. Arresto dei container

```bash
docker-compose down
```

Per arrestare i container e eliminare i volumi (cancellando tutti i dati):
```bash
docker-compose down -v
```

## Sviluppo locale

### Requisiti
- Python 3.11+
- PostgreSQL 13+

### Installazione
1. Clona il repository
2. Installa le dipendenze: `pip install -e .`
3. Configura le variabili d'ambiente
4. Avvia l'applicazione: `gunicorn --bind 0.0.0.0:5000 main:app`

## Licenza
Questo progetto è stato sviluppato come parte di una tesi di laurea.