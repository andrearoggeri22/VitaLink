# VitaLink - Design Pattern, Tecnologie e Standard

Questo documento fornisce una panoramica dettagliata dei design pattern, delle tecnologie e degli standard utilizzati nel progetto VitaLink.

**Ultima revisione**: 06/05/2025
**Versione**: 1.0
**Autore**: Roggeri Andrea

## 1. Design Pattern

Il progetto VitaLink utilizza diversi design pattern architetturali e di progettazione per garantire una struttura modulare, manutenibile e scalabile. I principali pattern implementati sono:

### 1.1 Pattern Architetturali

#### Model-View-Controller (MVC)
L'architettura principale del sistema segue il pattern MVC, separando chiaramente le responsabilità tra:
- **Model**: Le classi nel file `models.py` che rappresentano le entità di dominio e la logica di business
- **View**: I template e le interfacce utente implementate nelle route di Flask
- **Controller**: I blueprint Flask che gestiscono le richieste HTTP e orchestrano l'interazione tra modelli e viste

**Riferimenti nel codice**:
- `app/models.py`: Definizione dei modelli di dominio
- `app/views.py`: Gestione delle viste web
- `app/api.py`: Endpoints API RESTful

#### Repository Pattern
Utilizzato per l'accesso ai dati e la separazione della logica di business dalla persistenza dei dati:
- Incapsula la logica di accesso al database
- Fornisce metodi coerenti per le operazioni CRUD
- Facilita i test e la manutenzione

**Riferimenti nel codice**:
- Le classi con metodi come `find_by_id`, `save`, `delete` implementano questo pattern

#### Modular Function Organization Pattern
Implementato per incapsulare la logica di business complessa in moduli funzionali, invece che in classi di servizio:
- Modulo `health_platforms.py`: Gestisce l'integrazione con le piattaforme sanitarie tramite funzioni specializzate
- Modulo `observations.py`: Gestisce le operazioni sulle osservazioni mediche tramite funzioni dedicate
- Modulo `reports.py`: Gestisce la generazione di report tramite funzioni specifiche

**Riferimenti nel codice**:
- `app/health_platforms.py`: Funzioni per l'integrazione con piattaforme sanitarie (es. `get_processed_fitbit_data`, `process_fitbit_data`)
- `app/reports.py`: Funzioni per la generazione di report (es. `generate_specific_report`, `create_vital_chart`)
- `app/observations.py`: Funzioni per la gestione delle osservazioni


### 1.2 Pattern di Progettazione

#### Factory Pattern
Implementato implicitamente nella creazione di link di autorizzazione per diverse piattaforme sanitarie:
- Funzione `generate_platform_link`: Crea link di autorizzazione specifici per piattaforma

**Riferimenti nel codice**:
- `app/health_platforms.py`: Implementazione del meccanismo di generazione link

#### Singleton Pattern
Utilizzato per componenti che devono essere istanziati una sola volta nell'applicazione:
- Istanza dell'applicazione Flask
- Connessione al database
- Cache per i dati vitali

**Riferimenti nel codice**:
- `app/app.py`: Istanza singleton dell'applicazione Flask
- `app/health_platforms.py`: Sistema di cache per i dati vitali

#### Strategy Pattern
Implementato per la gestione di diverse strategie di elaborazione dei dati in base al tipo di parametro vitale:
- Funzioni come `process_standard_list`, `process_nested_value_list`, ecc.: Diverse strategie di elaborazione

**Riferimenti nel codice**:
- `app/health_platforms.py`: Diverse strategie di elaborazione dati

#### Observer Pattern
Implementato nel sistema di audit per registrare le azioni degli utenti:
- Sistema di audit che "osserva" e registra tutte le azioni significative nel sistema

**Riferimenti nel codice**:
- `app/audit.py`: Sistema di logging delle azioni

#### Decorator Pattern
Utilizzato per aggiungere funzionalità a route Flask e per la protezione delle API:
- Decoratori come `doctor_required`, `login_required`: Aggiungono verifica dell'autenticazione

**Riferimenti nel codice**:
- Decoratori per la protezione delle route e per il logging

## 2. Tecnologie Utilizzate

### 2.1 Backend

#### Python
Linguaggio di programmazione principale per lo sviluppo backend:
- Versione: Python 3.9+
- Benefici: Leggibilità, vasta libreria standard, supporto per pattern orientati agli oggetti

#### Flask
Framework web leggero per la costruzione di applicazioni web in Python:
- Funzionalità: Routing, gestione delle richieste, template rendering
- Estensioni: Flask-SQLAlchemy, Flask-Login, Flask-Babel

#### SQLAlchemy
ORM (Object-Relational Mapping) per interagire con il database in modo orientato agli oggetti:
- Funzionalità: Mappatura oggetti-database, gestione delle query, migrazioni

#### PostgreSQL
Sistema di gestione di database relazionale:
- Versione: PostgreSQL 13+
- Funzionalità: Transazioni ACID, supporto JSON, indicizzazione avanzata

#### Flask-Migrate
Estensione Flask basata su Alembic per la gestione delle migrazioni del database:
- Funzionalità: Creazione di script di migrazione, applicazione di modifiche al database, rollback
- Vantaggi: Gestione delle versioni dello schema del database, evoluzioni incrementali

**Riferimenti nel codice**:
- `app/migrate.py`: Configurazione e funzioni per la migrazione del database

#### ReportLab
Libreria per la generazione di documenti PDF:
- Utilizzo: Creazione di report medici con grafici e dati formattati

**Riferimenti nel codice**:
- `app/reports.py`: Utilizzo di ReportLab per generare report PDF

### 2.2 Frontend

#### HTML5, CSS3, JavaScript
Linguaggi standard per lo sviluppo frontend:
- Utilizzo: Struttura, stile e interattività dell'interfaccia utente

#### Bootstrap
Framework CSS per lo sviluppo di interfacce responsive e moderne:
- Versione: Bootstrap 5
- Componenti: Griglie, forme, modali, navigazione

#### Chart.js
Libreria JavaScript per la creazione di grafici interattivi:
- Utilizzo: Visualizzazione dei dati vitali dei pazienti
- Tipi di grafici: Lineari, a barre, a torta per diversi parametri vitali

**Riferimenti nel codice**:
- Template per la visualizzazione di grafici e tendenze

### 2.3 Integrazione e API

#### OAuth 2.0
Protocollo di autorizzazione per l'accesso sicuro alle API di terze parti:
- Flussi: Authorization Code Flow
- Implementazione: Gestione completa del ciclo di vita dei token

**Riferimenti nel codice**:
- `app/health_platforms.py`: Implementazione del flusso OAuth 2.0

#### Fitbit API
API REST per accedere ai dati di salute e fitness degli utenti Fitbit:
- Endpoint: Heart rate, sleep, activity, weight, etc.
- Rate Limiting: Gestione delle limitazioni di chiamate (150/ora)

**Riferimenti nel codice**:
- `app/health_platforms_config.py`: Configurazione degli endpoint Fitbit
- `app/health_platforms.py`: Interazione con l'API Fitbit

#### Mailjet API
API per l'invio di email transazionali e marketing:
- Funzionalità: Invio di email con allegati (report PDF)
- Autenticazione: API key e API secret key

**Riferimenti nel codice**:
- `app/email_utils.py`: Implementazione dell'invio di email con reportistica

#### Flask-Babel
Estensione Flask per l'internazionalizzazione e la localizzazione:
- Lingue supportate: Italiano, Inglese
- Funzionalità: Traduzioni, formattazione di date e numeri
- Sistema di compilazione: Da file `.po` a file binari `.mo`

**Riferimenti nel codice**:
- `app/language.py`: Configurazione di Flask-Babel
- `app/compile_translations.py`: Compilazione dei file di traduzione

### 2.4 Sicurezza

#### Werkzeug
Libreria per la gestione sicura delle password e l'autenticazione:
- Funzionalità: Hash sicuro delle password, verifica

#### JWT (JSON Web Tokens)
Standard per la creazione di token di accesso basati su JSON:
- Utilizzo: Autenticazione API e gestione delle sessioni

**Riferimenti nel codice**:
- `app/auth.py`: Implementazione dell'autenticazione

### 2.5 Testing

#### Pytest
Framework di testing per Python:
- Funzionalità: Test unitari, test di integrazione, fixtures

## 3. Standard Utilizzati

### 3.1 Standard di Codifica

#### PEP 8
Guida di stile per il codice Python:
- Convenzioni: Indentazione, lunghezza delle linee, convenzioni di denominazione
- Strumenti: Linter per verificare la conformità

#### Docstrings
Documentazione inline nel codice secondo lo standard PEP 257:
- Formato: Descrizione, argomenti, valori di ritorno, eccezioni
- Strumenti: Sphinx per la generazione di documentazione

**Riferimenti nel codice**:
- Commenti e docstrings in `app/models.py`, `app/health_platforms.py`, etc.

#### JavaScript ES6+
Utilizzo di caratteristiche moderne di JavaScript:
- Funzionalità: Arrow functions, template literals, destructuring

### 3.2 Standard di Architettura e Sicurezza

#### REST
Architettura per le API web:
- Principi: Stateless, risorse identificate da URI, rappresentazioni
- Metodi HTTP: GET, POST, PUT, DELETE

**Riferimenti nel codice**:
- `app/api.py`: Implementazione delle API RESTful

### 3.3 Standard di Documentazione

#### UML
Linguaggio di modellazione unificato per la documentazione dell'architettura:
- Diagrammi: Classi, sequenza, casi d'uso, componenti, ER
- Strumenti: PlantUML per la generazione dei diagrammi

**Riferimenti**:
- Diagrammi UML in `docs/UML/`

## 4. Principi di Design

### 4.1 SOLID

#### Single Responsibility
Ogni modulo e funzione ha una sola responsabilità:
- Esempio: Classe `Doctor` gestisce solo i dati del medico, modulo `health_platforms.py` contiene funzioni specializzate per l'integrazione

#### Open/Closed
Classi aperte all'estensione ma chiuse alla modifica:
- Esempio: Utilizzo di enum e costanti per tipi di dati vitali, facilitando l'aggiunta di nuovi tipi

### 4.3 Separation of Concerns
Separazione delle responsabilità in componenti distinti:
- Esempio: Moduli separati per autenticazione, gestione pazienti, integrazioni

### 4.4 Modularità e Organizzazione del Codice

Il progetto è organizzato in moduli funzionali chiaramente definiti, ciascuno con responsabilità specifiche:

- **Core**: Modelli di dati e funzionalità base (`models.py`, `app.py`)
- **Authentication**: Sistema di autenticazione e gestione sessioni (`auth.py`)
- **Health Integration**: Integrazione con piattaforme sanitarie (`health_platforms.py`, `health_platforms_config.py`)
- **Visualization**: Componenti per la visualizzazione dei parametri vitali (frontend)
- **Reporting**: Funzionalità di generazione report (`reports.py`)
- **Patient Management**: Gestione pazienti e importazione (API)
- **Localization**: Internazionalizzazione e supporto multilingua (`language.py`, `compile_translations.py`)
- **Communication**: Servizi di comunicazione email (`email_utils.py`)
- **Database Migration**: Gestione delle migrazioni del database (`migrate.py`)

Questa organizzazione modulare facilita la manutenzione, il testing e le future estensioni del sistema.