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

### Relazione PDF
-[File PDF](docs/Progetto_Piattaforme_Cloud_e_Mobile_Roggeri_Andrea_1079033_2025_Vitalink.pdf)

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

## Licenza

Questo progetto è distribuito sotto la licenza Apache License, come indicato nel file `LICENSE`.
