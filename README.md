# VitaLink

VitaLink è una piattaforma per il monitoraggio dei parametri vitali e per l'analisi e la valutazione delle terapie nel contesto sanitario. Questa applicazione permette a medici e personale sanitario di monitorare i parametri vitali dei pazienti, registrare note mediche e generare report personalizzati.

## Panoramica del progetto

VitaLink è una piattaforma web sviluppata con Flask che fornisce le seguenti funzionalità:

- **Gestione dei pazienti**: Registrazione, aggiornamento e monitoraggio dei dati dei pazienti
- **Monitoraggio dei parametri vitali**: Visualizzazione dei parametri vitali come pressione sanguigna, frequenza cardiaca, ecc.
- **Note mediche**: Creazione e gestione di note mediche associate ai pazienti
- **Generazione di report**: Creazione di report personalizzati sui dati dei pazienti
- **Audit logging**: Registrazione completa di tutte le azioni eseguite nel sistema per conformità e sicurezza
- **Integrazione con piattaforme sanitarie**: Connessione a dispositivi e servizi esterni (come Fitbit) per raccogliere dati sanitari

L'applicazione è progettata con un'architettura modulare con una separazione tra:
- Modelli di dati (models.py)
- Viste web (views.py)
- API REST (api.py)
- Autenticazione (auth.py)
- Osservazioni sui parametri vitali (observations.py)
- Logica di audit (audit.py)

## Tecnologie utilizzate

- **Backend**: Python 3.11+ con Flask 3.1+
- **ORM Database**: SQLAlchemy 2.0+ con Flask-SQLAlchemy
- **Database**: PostgreSQL (in produzione/sviluppo), SQLite (per test in memoria)
- **Autenticazione**: JWT (Flask-JWT-Extended) per API, Flask-Login per interfaccia web
- **Gestione migrazioni DB**: Flask-Migrate con Alembic
- **Internazionalizzazione**: Flask-Babel per supporto multilingue
- **Generazione Report**: ReportLab
- **Validazione dati**: WTForms con Flask-WTF
- **Testing**: pytest
- **Containerizzazione**: Docker e docker-compose
- **Documentazione**: MkDocs con Material theme e mkdocstrings

## Modalità di esecuzione

### Prerequisiti

Prima di eseguire VitaLink, è necessario configurare l'ambiente creando un file `.env` nella radice del progetto. È possibile utilizzare `.env.example` come modello:

```bash
cp .env.example .env
```

Quindi, modificare il file `.env` con i valori appropriati per il proprio ambiente.

### Installazione delle dipendenze

Per installare le dipendenze necessarie per lo sviluppo locale:

```powershell
pip install .
```

Per installare le dipendenze di sviluppo (test, linting, ecc.):

```powershell
pip install ".[dev]"
```

### Modalità di esecuzione

#### 1. Test con database in memoria

Questa modalità è ideale per eseguire test rapidi senza la necessità di un database esterno:

```powershell
# Eseguire i test
pytest
```

File `.env` completo per test con database in memoria:
```bash
# Configurazione database per test in memoria
DATABASE_URL=sqlite:///:memory:
CLOUD_RUN_ENVIRONMENT=false

# Configurazione Flask
FLASK_APP=app:app
SESSION_SECRET=secret_key_for_testing
PORT=5000
HOST=0.0.0.0
DEBUG=true

# Configurazione JWT
JWT_SECRET_KEY=jwt_secret_key_for_testing

# API di terze parti (possono essere dummy per testing)
FITBIT_CLIENT_ID=dummy_id
FITBIT_CLIENT_SECRET=dummy_secret
FITBIT_REDIRECT_URI=http://localhost:5000/callback

MJ_APIKEY=dummy_api_key
MJ_APIKEY_SECRET=dummy_api_secret

LOG_LEVEL=DEBUG

EMAIL_SENDER=test@example.com
```

#### 2. Sviluppo locale con Flask e database PostgreSQL

Per lo sviluppo con Flask e un database PostgreSQL locale:

1. Creare manualmente il database PostgreSQL:
   - Impostare il nome del database, utente, password e porta
   - Creare le tabelle necessarie
   - Configurare un utente con password appropriata

2. Configurare il `.env` completo con i dettagli del database:
   ```bash
   # Configurazione database PostgreSQL locale
   DATABASE_URL=postgresql://<utente>:<password>@localhost:<porta>/vitalink
   PGHOST=localhost
   PGPORT=<porta>
   PGUSER=<utente>
   PGPASSWORD=<password>
   PGDATABASE=vitalink
   CLOUD_RUN_ENVIRONMENT=false

   # Configurazione Flask
   FLASK_APP=app:app
   SESSION_SECRET=<una_chiave_segreta_sicura>
   PORT=5000
   HOST=0.0.0.0
   DEBUG=true

   # Configurazione JWT
   JWT_SECRET_KEY=<una_chiave_jwt_sicura>

   # API di terze parti 
   FITBIT_CLIENT_ID=<id_client_fitbit>
   FITBIT_CLIENT_SECRET=<secret_client_fitbit>
   FITBIT_REDIRECT_URI=http://localhost:5000/oauth/callback

   MJ_APIKEY=<chiave_api_mailjet>
   MJ_APIKEY_SECRET=<chiave_segreta_mailjet>

   LOG_LEVEL=INFO

   EMAIL_SENDER=<email_mittente>
   ```

3. Inizializzare il database con le migrazioni:
   ```powershell
   flask db upgrade
   ```

4. Eseguire l'applicazione in locale con Flask:
   ```powershell
   # Esecuzione attraverso Flask direttamente
   flask run
   ```

#### 3. Sviluppo locale con Docker

Per eseguire l'applicazione in un ambiente containerizzato:

```powershell
docker-compose up --build
```

Questo avvierà sia l'applicazione web che il database PostgreSQL in container separati.

File `.env` completo per sviluppo con Docker:
```bash
# Configurazione database (con Docker)
DATABASE_URL=postgresql://postgres:postgres@db:5432/vitalink
PGHOST=db
PGPORT=5432
PGUSER=postgres
PGPASSWORD=postgres
PGDATABASE=vitalink
CLOUD_RUN_ENVIRONMENT=false

# Configurazione Flask
FLASK_APP=app:app
SESSION_SECRET=<una_chiave_segreta_sicura>
PORT=5000
HOST=0.0.0.0
DEBUG=true

# Configurazione JWT
JWT_SECRET_KEY=<una_chiave_jwt_sicura>

# API di terze parti
FITBIT_CLIENT_ID=<id_client_fitbit>
FITBIT_CLIENT_SECRET=<secret_client_fitbit>
FITBIT_REDIRECT_URI=http://localhost:5000/oauth/callback

MJ_APIKEY=<chiave_api_mailjet>
MJ_APIKEY_SECRET=<chiave_segreta_mailjet>

LOG_LEVEL=INFO

EMAIL_SENDER=<email_mittente>
```

#### 4. Deployment in ambiente remoto

##### 4.1 Con database interno al container (sconsigliato per ambienti di produzione)

```powershell
# Avviare l'applicazione con database interno
docker-compose up --build
```

Nota: Questa opzione è sconsigliata per ambienti di produzione poiché i dati andranno persi quando il container viene rimosso.

File `.env` completo per database interno al container:
```bash
# Configurazione database interno
DATABASE_URL=postgresql://postgres:postgres@db:5432/vitalink
PGHOST=db
PGPORT=5432
PGUSER=postgres
PGPASSWORD=postgres
PGDATABASE=vitalink
CLOUD_RUN_ENVIRONMENT=false

# Configurazione Flask
FLASK_APP=app:app
SESSION_SECRET=<una_chiave_segreta_sicura>
PORT=5000
HOST=0.0.0.0
DEBUG=false

# Configurazione JWT
JWT_SECRET_KEY=<una_chiave_jwt_sicura>

# API di terze parti
FITBIT_CLIENT_ID=<id_client_fitbit>
FITBIT_CLIENT_SECRET=<secret_client_fitbit>
FITBIT_REDIRECT_URI=<fitbit_callback_uri_produzione>

MJ_APIKEY=<chiave_api_mailjet>
MJ_APIKEY_SECRET=<chiave_segreta_mailjet>

LOG_LEVEL=INFO

EMAIL_SENDER=<email_mittente_produzione>
```

##### 4.2 Con Koyeb (consigliato per produzione)

Il progetto è già configurato per connettersi a un'istanza Koyeb.

File `.env` completo per connessione a Koyeb:
```bash
# Configurazione Koyeb
DB_USER=<user_cloud_sql>
DB_PASS=<password_cloud_sql>
DB_NAME=<db_name_cloud_sql>
CLOUD_RUN_ENVIRONMENT=true
INSTANCE_UNIX_SOCKET=<host_name>

# Configurazione Flask
FLASK_APP=app:app
SESSION_SECRET=<una_chiave_segreta_sicura_produzione>
HOST=0.0.0.0
DEBUG=false

# Configurazione JWT
JWT_SECRET_KEY=<una_chiave_jwt_sicura_produzione>

# API di terze parti
FITBIT_CLIENT_ID=<id_client_fitbit>
FITBIT_CLIENT_SECRET=<secret_client_fitbit>
FITBIT_REDIRECT_URI=<uri_callback_produzione>

MJ_APIKEY=<chiave_api_mailjet>
MJ_APIKEY_SECRET=<chiave_segreta_mailjet>

LOG_LEVEL=INFO

EMAIL_SENDER=<email_mittente_produzione>
```

## Documentazione

### Generazione della documentazione

Per generare la documentazione del codice e dei test:

```powershell
cd docs/code
mkdocs build

cd ../tests
mkdocs build
```

### Documentazione disponibile

VitaLink include una documentazione completa:

- [API Endpoints](docs/api_endpoints.md): Descrizione di tutti gli endpoint API REST
- [Project Plan](docs/project_plan.md): Project Plan per la soluzione
- [Design Pattern/Tecnologie/Standard](docs/design_patterns_technologies_standards.md): File riepilogativo che descrive i Design Pattern, le tecnologie e gli standard
- [Requisiti](docs/requirements.md): Requisiti funzionali e non funzionali del sistema
- [Guida per l'uso](docs/use_guide.md): Descrizione dei flussi di operazioni per le principali attività

### Diagrammi UML

Il progetto include vari diagrammi UML per descrivere l'architettura e il design:

- [Diagrammi ER](docs/UML/ER/): Struttura del database
- [Diagrammi delle classi](docs/UML/Class/): Relazioni tra le classi
- [Diagrammi di sequenza](docs/UML/Sequence/): Flussi di interazione
- [Diagrammi di stato](docs/UML/State/): Stati del sistema
- [Diagrammi dei casi d'uso](docs/UML/Use%20Case/): Funzionalità del sistema
- [Diagrammi di componenti](docs/UML/Component/): Componenti del sistema
- [Diagrammi di deployment](docs/UML/Deployment/): Struttura di deployment
- [Diagrammi di oggetti](docs/UML/Object/): Istanze di oggetti
- [Diagrammi di attività](docs/UML/Activity/): Flussi di lavoro
- [Diagrammi di comunicazione](docs/UML/Communication/): Comunicazione tra oggetti
- [Diagrammi di timing](docs/UML/Timing/): Visualizzazione temporale
- [Diagrammi di pacchetto](docs/UML/Package/): Organizzazione dei pacchetti

## Localizzazione

VitaLink supporta la localizzazione tramite Flask-Babel. Per gestire le traduzioni:

### Estrazione dei messaggi

Per estrarre le stringhe da tradurre:

```powershell
# Per Windows
pybabel extract -F app\translations\babel.cfg -o app\translations\messages.pot .

# Per Linux/MacOS
pybabel extract -F app/translations/babel.cfg -o app/translations/messages.pot .
```

### Aggiornamento delle traduzioni

Per aggiornare i file di traduzione esistenti:

```powershell
# Per Windows
pybabel update -i app\translations\messages.pot -d app\translations

# Per Linux/MacOS
pybabel update -i app/translations/messages.pot -d app/translations
```

### Compilazione delle traduzioni

Le traduzioni vengono compilate automaticamente all'avvio dell'applicazione, ma è possibile compilarle manualmente:

```powershell
# Per Windows
python -m app.compile_translations

# Per Linux/MacOS
python -m app.compile_translations
```

### Workflow completo per le traduzioni

1. Estrai i messaggi dal codice
2. Aggiorna i file di traduzione 
3. Modifica manualmente i file `.po` nella cartella `app/translations/<locale>/LC_MESSAGES/`
4. Compila le traduzioni (o riavvia l'applicazione che le compilerà automaticamente)

## Testing

### Configurazione per il testing

#### Testing con database in memoria (consigliato per CI/CD e test rapidi)

1. Configurare il file `.env` per il testing con database in memoria:
   ```bash
   # Configurazione essenziale per testing
   DATABASE_URL=sqlite:///:memory:
   CLOUD_RUN_ENVIRONMENT=false
   
   FLASK_APP=app:app
   SESSION_SECRET=test_secret_key
   JWT_SECRET_KEY=test_jwt_secret_key
   
   # Valori fittizi per servizi esterni
   FITBIT_CLIENT_ID=dummy_id
   FITBIT_CLIENT_SECRET=dummy_secret
   FITBIT_REDIRECT_URI=http://localhost:5000/callback
   MJ_APIKEY=dummy_key
   MJ_APIKEY_SECRET=dummy_secret
   EMAIL_SENDER=test@example.com
   ```

2. Eseguire i test:
   ```powershell
   # Esecuzione di tutti i test
   pytest
   
   # Esecuzione di test specifici
   pytest tests/test_models.py
   
   # Esecuzione con maggior dettaglio
   pytest -v
   ```

#### Testing con database PostgreSQL locale

1. Configurare manualmente il database PostgreSQL:
   - Creare un database per fini di test
   - Impostare utente e password
   - Assicurarsi che l'utente abbia permessi completi sul database

2. Configurare il file `.env` per il testing con PostgreSQL:
   ```bash
   # Configurazione database per test
   DATABASE_URL=postgresql://<utente_test>:<password_test>@localhost:<porta>/vitalink_test
   PGHOST=localhost
   PGPORT=<porta>
   PGUSER=<utente_test>
   PGPASSWORD=<password_test>
   PGDATABASE=vitalink_test
   CLOUD_RUN_ENVIRONMENT=false
   
   FLASK_APP=app:app
   SESSION_SECRET=test_secret_key
   JWT_SECRET_KEY=test_jwt_secret_key
   
   # Valori per test (possono essere non reali)
   FITBIT_CLIENT_ID=test_id
   FITBIT_CLIENT_SECRET=test_secret
   FITBIT_REDIRECT_URI=http://localhost:5000/callback
   MJ_APIKEY=test_key
   MJ_APIKEY_SECRET=test_secret
   EMAIL_SENDER=test@example.com
   ```

3. Eseguire i test:
   ```powershell
   pytest
   ```

## Licenza

Questo progetto è distribuito sotto la licenza Apache License, come indicato nel file `LICENSE`.
