# Project Plan per Tesi - VitaLink

**Ultima revisione**: 06/05/2025
**Versione**: 1.0
**Autore**: Roggeri Andrea

## 1. Introduzione

### Background del Progetto
VitaLink è un progetto di tesi che propone una piattaforma sanitaria innovativa per modernizzare il monitoraggio dei parametri vitali dei pazienti. Il progetto nasce dall'osservazione della crescente diffusione di dispositivi indossabili per il monitoraggio della salute e dalla necessità di integrare questi dati nei sistemi sanitari.

L'architettura del sistema si basa sull'utilizzo di OAuth per connettersi a piattaforme sanitarie esterne (come Fitbit) per ottenere dati in tempo reale, rispettando la privacy e il controllo dei dati da parte degli utenti.

### Obiettivi del Progetto
- Sviluppare un'applicazione per il monitoraggio dei parametri vitali dei pazienti in tempo reale
- Implementare l'integrazione con Fitbit tramite protocollo OAuth
- Creare un sistema di osservazioni mediche su periodi specifici dei dati vitali
- Implementare una funzionalità di reportistica per la documentazione clinica
- Permettere l'importazione di pazienti esistenti tramite UUID

### Risultati Attesi
- Un prototipo funzionante dell'applicazione web
- Integrazione OAuth completata con Fitbit
- Un'interfaccia utente per la visualizzazione dei dati sanitari
- Documentazione tecnica completa per supportare la tesi

### Responsabile del Progetto
- **Sviluppatore Full-Stack**: Responsabile dell'intera implementazione, dall'architettura all'interfaccia utente, passando per backend, database, sicurezza e test

### Sintesi del Progetto
VitaLink è un progetto di tesi che mira a sviluppare un prototipo di piattaforma sanitaria per il monitoraggio remoto dei pazienti. Il sistema utilizza OAuth per ottenere dati in tempo reale da Fitbit, permettendo ai medici di visualizzare parametri vitali, registrare osservazioni cliniche e generare report. Si tratta di un progetto accademico sviluppato interamente da Andrea Roggeri per dimostrare l'applicazione di tecnologie web nell'ambito sanitario, con un focus particolare sull'integrazione di servizi esterni e sulla privacy dei dati.

## 2. Modello di Processo

Per lo sviluppo di VitaLink è stato adottato un modello di processo pragmatico e orientato alla consegna rapida, adatto a un progetto sviluppato da una singola persona in un breve periodo di tempo.

### Approccio di Sviluppo
L'approccio utilizzato si ispira ai seguenti principi:

- **Sviluppo Monolitico Progressivo**: Implementazione di tutte le componenti principali del sistema in sequenza logica
- **Priorità alla Funzionalità**: Focus iniziale sulla realizzazione delle funzionalità core, seguita da revisioni e miglioramenti
- **Documentazione Incorporata**: Documentazione del codice e dell'architettura integrata nel processo di sviluppo

### Fasi Principali del Processo

1. **Pianificazione e Progettazione**
   - Definizione dei requisiti funzionali e non funzionali
   - Creazione dei diagrammi UML per l'architettura
   - Progettazione dell'architettura e del modello dati
   - Definizione delle interfacce utente e dei flussi di interazione

2. **Implementazione**
   - Sviluppo dell'infrastruttura di base (database, autenticazione)
   - Implementazione dei moduli funzionali (integrazione OAuth, visualizzazione parametri vitali)
   - Sviluppo dell'interfaccia utente e dei componenti visivi

3. **Verifica e Collaudo**
   - Scrittura di test per verificare il funzionamento delle componenti
   - Verifica dell'integrazione tra i vari moduli
   - Validazione dei requisiti e analisi delle prestazioni

4. **Documentazione e Completamento**
   - Finalizzazione della documentazione tecnica
   - Aggiornamento dei diagrammi UML per l'architettura
   - Preparazione per il rilascio

### Milestone del Progetto

1. **Implementazione dei Modelli Dati e Autenticazione**
   - Definizione del modello dati (Doctor, Patient, etc.)
   - Implementazione del sistema di autenticazione
   - Creazione delle relazioni tra le entità

2. **Integrazione OAuth con Piattaforme Sanitarie**
   - Implementazione del flusso OAuth per Fitbit
   - Sviluppo del sistema di gestione token
   - Implementazione delle API per il recupero dati

3. **Sistema di Visualizzazione e Osservazioni**
   - Sviluppo dei componenti per la visualizzazione dei parametri vitali
   - Implementazione del sistema di osservazioni mediche
   - Creazione dell'interfaccia utente per l'analisi dei dati

4. **Reportistica e Funzionalità Avanzate**
   - Sistema di generazione report personalizzati
   - Funzionalità di importazione pazienti tramite UUID
   - Implementazione del sistema di audit completo

## 3. Organizzazione del Progetto

### Contesto Tecnologico

#### Utilizzatori Potenziali
- **Medici**: Il sistema è progettato per essere utilizzato principalmente da professionisti sanitari
- **Pazienti**: Utenti che autorizzano l'accesso ai propri dati tramite le piattaforme di health tracking

#### Piattaforme Integrate
- **Fitbit**: Principale provider di dati sanitari tramite API OAuth per questo progetto
- **Altri servizi**: Il sistema è progettato per supportare in futuro altre piattaforme come Google Health e Apple Health

### Validazione del Prototipo

Trattandosi di un progetto di tesi, la validazione avverrà attraverso:
- **Test di funzionalità**: Verifica delle principali funzionalità implementate
- **Simulazione d'uso**: Test pratici con account di sviluppo Fitbit
- **Confronto con i requisiti**: Valutazione del soddisfacimento degli obiettivi iniziali

### Struttura del Progetto

#### Ruoli e Responsabilità

- **Sviluppatore Full-Stack**
  - Pianificazione e esecuzione del progetto
  - Progettazione dell'architettura del sistema
  - Implementazione del backend con Flask e SQLAlchemy
  - Sviluppo del frontend e dell'interfaccia utente
  - Integrazione con piattaforme sanitarie tramite OAuth
  - Testing e debugging
  - Documentazione tecnica e UML

Date le dimensioni ridotte del progetto e il tempo limitato (2-3 settimane), tutte le responsabilità sono state assunte da un'unica persona che ha gestito l'intero ciclo di sviluppo, dalla progettazione al collaudo finale.

### Preparazione e Competenze

Per realizzare efficacemente il progetto, sono state necessarie le seguenti competenze:

- **Sviluppo Backend**: Python, Flask, SQLAlchemy, RESTful API
- **Integrazione OAuth**: Implementazione del protocollo OAuth 2.0
- **Piattaforme Sanitarie**: Conoscenza delle API Fitbit
- **Sviluppo Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: Progettazione schema, PostgreSQL
- **Sicurezza**: Autenticazione, gestione dei token, protezione dei dati sensibili
- **Testing**: Unit testing, integration testing

### Organizzazione del Lavoro

Il lavoro è stato organizzato in moduli funzionali per mantenere una struttura chiara nonostante lo sviluppo individuale:

- **Core**: Funzionalità base dell'applicazione e modelli di dati
- **Authentication**: Sistema di autenticazione e gestione sessioni
- **Health Integration**: Moduli per l'integrazione con piattaforme sanitarie
- **Visualization**: Componenti per la visualizzazione dei parametri vitali
- **Reporting**: Funzionalità di generazione report
- **Patient Management**: Gestione pazienti e importazione

## 4. Standard, Linee Guida e Procedure

### Standard di Codifica

- **Python**: Aderenza al PEP 8 (Style Guide for Python Code)
- **JavaScript**: Utilizzo dello standard ES6+
- **HTML/CSS**: Conformità agli standard W3C e utilizzo di Bootstrap per l'UI
- **SQL**: Convenzioni standardizzate per query e gestione del database

### Linee Guida per il Controllo del Codice

- **Auto-revisione**: Revisione personale del codice prima di ogni commit
- **Controllo di Versione**: Uso di Git per tracciare le modifiche del codice
- **Testing**: Test manuali durante lo sviluppo, seguiti da unit test a fine implementazione

### Procedure di Documentazione

- **Documentazione del Codice**: Tutti i moduli, classi e metodi devono includere docstring
- **UML Diagrams**: Mantenimento di diagrammi UML aggiornati per l'architettura del sistema
- **User Guides**: Documentazione dettagliata per l'utilizzo del sistema

### Controllo di Versione e Gestione della Configurazione

- **Git**: Utilizzo di Git per il controllo di versione
- **Branching semplice**: Utilizzo di branch principale e branch di feature quando necessario
- **Environment Configuration**: Gestione delle variabili d'ambiente per configurazioni

### Procedure di Test

- **Test Manuali**: Verifica delle funzionalità durante lo sviluppo
- **Unit Testing**: Test di funzioni e componenti principali con pytest
- **Integration Testing**: Test delle interazioni tra i diversi moduli
- **Verifica Funzionale**: Test completo delle user story principali

### Documentazione Tecnica

La documentazione viene gestita con i seguenti criteri:

- **Tempistiche**: Aggiornamento della documentazione contestualmente al codice
- **Revisione**: Revisione della documentazione come parte del processo di code review
- **Automazione**: Generazione automatica della documentazione API da annotazioni nel codice

### Standard di Sicurezza

- **Encryption**: Standard per la crittografia dei dati sensibili in transito e a riposo

## 5. Attività di Gestione

### Obiettivi e Priorità

#### Obiettivi Primari
1. Garantire la stabilità e l'affidabilità del sistema
2. Rispettare i tempi di consegna delle milestone
3. Mantenere alti standard di qualità del codice e della documentazione
4. Assicurare la sicurezza dei dati e la conformità alle normative

#### Priorità
1. **Funzionalità critiche**: Integrazione OAuth, visualizzazione dei dati vitali
2. **Sicurezza**: Gestione sicura dei token e dei dati sensibili
3. **Usabilità**: Esperienza utente fluida e intuitiva
4. **Performance**: Tempi di risposta rapidi e efficienza del sistema

### Monitoraggio del Progresso

#### Tracking Semplificato
- **Commit Git**: Registrazione dei progressi tramite commit frequenti con messaggi descrittivi
- **To-Do List**: Utilizzo di semplici checklist per monitorare il completamento delle attività
- **Diario di Sviluppo**: Documentazione giornaliera dei problemi incontrati e delle soluzioni adottate

#### Verifica della Qualità
- **Test Manuali**: Esecuzione regolare di test delle funzionalità implementate
- **Revisione del Codice**: Auto-revisione periodica del codice scritto

### Gestione delle Priorità

#### Focalizzazione sugli Obiettivi Core
- **MVP First**: Implementazione iniziale delle funzionalità essenziali
- **Funzionalità Opzionali**: Identificazione chiara di feature secondarie da implementare solo se c'è tempo
- **Timeboxing**: Allocazione di tempo limitato per ciascuna componente principale

## 6. Rischi

### Principali Rischi del Progetto

| ID | Rischio | Probabilità | Impatto | Strategia |
|----|---------|------------|---------|-------------|
| R1 | Difficoltà nell'ottenimento credenziali OAuth Fitbit | Alta | Medio | Uso account developer e sandbox |
| R2 | Problemi tecnici con l'integrazione OAuth | Media | Alto | Seguire documentazione ufficiale e test approfonditi |
| R3 | Limiti di tempo per il completamento | Alta | Medio | Focalizzazione sulle funzionalità core |
| R4 | Problemi con il caching temporaneo dei dati | Media | Medio | Testing approfondito e meccanismi fallback |
| R5 | Limitazioni di rate nelle API Fitbit | Alta | Basso | Ottimizzare le chiamate API |

### Strategie di Mitigazione

#### R1: Ottenimento Credenziali OAuth
- Iniziare la registrazione dell'app Fitbit all'inizio del progetto
- Utilizzare dati di esempio durante l'attesa delle credenziali
- Prepararsi per eventuali richieste di documentazione aggiuntiva

#### R2: Integrazione OAuth
- Studiare approfonditamente la documentazione Fitbit
- Implementare in modo modulare per facilitare il debug
- Testare diversi scenari (autenticazione, rinnovo token, revoca)

#### R3: Limiti di Tempo
- Definire chiaramente le funzionalità essenziali vs opzionali
- Implementare prima il core funzionale, poi le feature aggiuntive
- Allocare buffer di tempo per imprevisti

#### R4: Caching dei Dati
- Progettare un sistema di cache semplice ma robusto
- Implementare meccanismi di fallback in caso di errori
- Testare scenari di disconnessione e recupero

#### R5: Rate Limiting
- Implementare la memorizzazione dei dati frequentemente richiesti
- Ottimizzare le query per richiedere solo i dati necessari
- Aggiungere gestione degli errori per limitazioni di quota

## 7. Risorse

### Risorse per lo Sviluppo

#### Risorse Umane
- **Sviluppatore Full-Stack**: Una sola persona responsabile dell'intero progetto in tutte le fasi

#### Fasi di Sviluppo
| Fase | Durata Approssimativa | Attività Principali |
|------|----------------------|---------------------|
| Pianificazione | 2-3 giorni | Analisi requisiti, progettazione architettura |
| Sviluppo Backend | 5-7 giorni | Implementazione modelli, API, OAuth |
| Sviluppo Frontend | 3-5 giorni | Implementazione UI, visualizzazioni |
| Integrazioni | 3-4 giorni | OAuth con Fitbit, caching |
| Testing | 2-3 giorni | Test unità, integrazione, funzionali |
| Documentazione | 1-2 giorni | UML, documentazione API, manuali |

### Competenze Utilizzate

#### Competenze Tecniche
- **Backend**: Python, Flask, SQLAlchemy, PostgreSQL, RESTful API, OAuth 2.0
- **Frontend**: JavaScript, HTML5, CSS3, Bootstrap, Chart.js
- **Database**: PostgreSQL, progettazione schema relazionale
- **Security**: Autenticazione, gestione token OAuth, protezione dei dati
- **Testing**: Pytest, test manuali

#### Competenze Trasversali
- **Project Management**: Auto-gestione, pianificazione e monitoraggio
- **Architettura Software**: Progettazione MVC, pattern di integrazione
- **Problem Solving**: Troubleshooting, soluzioni per vincoli temporali

### Risorse di Apprendimento

| Argomento | Tipo di Risorsa | Scopo |
|-----------|----------------|-------|
| OAuth 2.0 | Documentazione ufficiale | Implementazione del flusso di autenticazione |
| API Fitbit | Developer Documentation | Comprensione endpoint e formati dati |
| Flask | Tutorial e documentazione | Sviluppo del backend |
| Chart.js | Guide ed esempi | Visualizzazione dei dati vitali |

## 8. Metodi e Tecniche

### Approccio ai Requisiti

- **Raccolta**: Revisione della letteratura, analisi di applicazioni simili
- **Analisi**: Modellazione UML, casi d'uso principali
- **Documentazione**: Requisiti funzionali e non funzionali in forma semplificata MoSCoW
- **Verifica**: Controllo di fattibilità e coerenza con gli obiettivi della tesi

### Progettazione

- **Architettura**: Pattern MVC con Flask per una struttura ben organizzata
- **Design Pattern**: Repository pattern per l'accesso ai dati, Adapter per le integrazioni OAuth
- **UX/UI Design**: Interfaccia semplice e funzionale basata su Bootstrap
- **Database Design**: Schema ER essenziale focalizzato sui requisiti principali

### Implementazione

- **Stack Tecnologico**:
  - Backend: Python 3.9+, Flask, SQLAlchemy, PostgreSQL
  - Frontend: HTML5, CSS3, JavaScript, Bootstrap, Chart.js
  - Tooling: Git, Docker

- **Pratiche di Codifica**:
  - Sviluppo incrementale per componenti funzionali
  - Commenti e documentazione inline
  - Test manuali durante lo sviluppo

### Testing

#### Ambiente di Test
- **Locale**: Ambiente di sviluppo per test rapidi

#### Tipi di Test
- **Test Manuali**: Verifica del comportamento atteso
- **Unit Test**: Test di funzioni e componenti isolati con pytest
- **Test Funzionali**: Verifica delle funzionalità end-to-end

#### Approccio ai Test
- Test manuali durante lo sviluppo per feedback rapido
- Test unità scritti dopo l'implementazione delle funzionalità
- Verifica dei casi d'uso principali prima della consegna

#### Procedure di Validazione
- Confronto con i requisiti funzionali
- Test dei casi limite e gestione errori
- Verifica compatibilità browser

### Controllo Versione e Sviluppo

- **Git** per il controllo del codice sorgente
- **Branch singolo** con commit frequenti
- **Environment Variables**: Dotenv per gestire configurazioni
- **Backup**: Copie regolari del repository locale

### Documentazione Tecnica

- **Docstrings**: Documentazione inline nelle funzioni e classi
- **README**: Istruzioni di base per l'installazione e l'utilizzo
- **UML Diagrams**: Diagrammi UML per visualizzare l'architettura del sistema
- **API Documentation**: Commenti nei controller per documentare gli endpoint

## 9. Garanzia di Qualità

### Approccio alla Qualità

- **Auto-verifica**: Lo sviluppatore verifica personalmente la qualità del codice e delle funzionalità
- **Testing Progressivo**: Test manuali durante lo sviluppo, seguiti da test automatizzati a fine implementazione
- **Focus sulle Funzionalità Critiche**: Maggiore attenzione alla qualità di componenti cruciali (OAuth, sicurezza)

### Metriche di Qualità

- **Funzionalità**: Completezza delle funzionalità rispetto ai requisiti
- **Usabilità**: Facilità d'uso dell'interfaccia e chiarezza del flusso utente

### Strumenti per la Qualità

- **Lint e Formattazione**: Pylint per Python, ESLint per JavaScript
- **Verifiche di Sicurezza**: Analisi manuale del codice per componenti critici
- **Testing Automatico**: Pytest per componenti principali

### Revisione del Codice

- **Self-review**: Revisione personale del codice prima del commit
- **Test-case Validation**: Verifica manuale dei casi d'uso principali
- **Documentazione**: Aggiunta di commenti e docstrings per chiarire la logica del codice

### Gestione dei Difetti

- **Tracciamento**: Utilizzo di TODO nel codice per i problemi minori
- **Prioritizzazione**: Focus sulla risoluzione dei problemi critici prima del rilascio
- **Verifiche Post-Fix**: Test approfondito dopo la correzione dei difetti

## 10. Moduli di Lavoro

### Struttura del Progetto

1. **Setup e Configurazione**
   1.1. Analisi dei requisiti
   1.2. Configurazione dell'ambiente di sviluppo
   1.3. Inizializzazione del repository Git
   1.4. Schema del database e modelli di dati

2. **Funzionalità Core**
   2.1. Modelli di database (Doctor, Patient)
   2.2. Sistema di autenticazione
   2.3. API REST di base
   2.4. Integrazione OAuth con Fitbit
   2.5. Sistema di caching temporaneo

3. **Interfaccia Utente**
   3.1. Layout di base e template
   3.2. Pagina di gestione pazienti
   3.3. Dashboard dati sanitari
   3.4. Visualizzazione parametri vitali (grafici)
   3.5. Gestione osservazioni mediche
   3.6. Generazione report

4. **Testing**
   4.1. Test unitari per componenti critici
   4.3. Test manuali dell'interfaccia

5. **Documentazione**
   5.1. Diagrammi UML (classi, ER, sequenza)
   5.2. README e guida all'installazione
   5.3. Documentazione delle API
   5.4. Documentazione per la tesi

### Pianificazione del Lavoro

| Task ID | Descrizione | Giorno | Dipendenze |
|-------|-------------|--------|------------|
| 1.1 | Analisi dei requisiti | 1 | - |
| 1.2 | Setup ambiente di sviluppo | 1 | - |
| 1.3 | Inizializzazione Git | 1 | - |
| 1.4 | Progettazione DB e architettura | 1-2 | 1.1 |
| 2.1 | Implementazione modelli DB | 2-3 | 1.4 |
| 2.2 | Sistema di autenticazione | 3-4 | 2.1 |
| 2.3 | API endpoint base | 4-5 | 2.1 |
| 2.4 | Integrazione OAuth Fitbit | 6-8 | 2.2, 2.3 |
| 2.5 | Sistema di caching | 7-8 | 2.3 |
| 3.1 | Templates base | 5-6 | 1.4 |
| 3.2 | Dashboard e visualizzazione | 9-11 | 3.1, 2.4 |
| 3.3 | Gestione osservazioni e report | 10-12 | 3.2 |
| 4.1 | Test funzionali | 13 | 3.3 |
| 5.1 | UML e documentazione | 14-15 | Tutti |

## 11. Risorse

### Risorse Necessarie

#### Ambiente di Sviluppo
- **Computer**: Computer personale con sufficiente capacità di calcolo
- **Ambiente di Test**: Locale, con possibilità di utilizzare Docker

### Strumenti Software

#### Tecnologie Core
- **Backend**: Python 3.9+, Flask, SQLAlchemy
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Gestione Dati**: Caching temporaneo in memoria

#### Strumenti di Sviluppo
- **IDE**: Visual Studio Code Insider(gratuito)
- **Version Control**: Git, GitHub
- **Testing**: Pytest per unit test basilari
- **Containerizzazione**: Docker per ambiente isolato

#### Strumenti di Collaborazione
- **Documentazione**: Markdown, direttamente nel repository
- **Diagramming**: Strumento PlantUML
- **Tracciamento**: File TODO.txt nell'ambiente di sviluppo

### Distribuzione Temporale dello Sviluppo

| Fase | Giorni | Attività principali |
|------|--------|--------------------------|
| Settimana 1 | 1-5 | Configurazione ambiente, progettazione architettura, modelli dati, implementazione base |
| Settimana 2 | 6-10 | Integrazione OAuth con Fitbit, sviluppo sistema di caching, implementazione UI base |
| Settimana 3 | 11-15 | Dashboard, visualizzazione dati, test, documentazione |

## 12. Budget e Programma

### Risorse e Tempistiche

#### Requisiti per lo Sviluppo

- **Ambiente**: Computer personale con ambiente di sviluppo Python
- **Account**: Account sviluppatore Fitbit per ottenere credenziali OAuth e Koyeb per eventuale deployment
- **Conoscenze Tecniche**: Python, Flask, OAuth 2.0, frontend web

#### Piano di Sviluppo Dettagliato

```
Giorno 1-2:  Configurazione e architettura
Giorno 3-5:  Modelli dati e API base
Giorno 6-8:  Integrazione OAuth Fitbit
Giorno 9-11: Frontend e visualizzazioni
Giorno 12-13: Test e debug
Giorno 14-15: Documentazione e UML
```

#### Milestone

| # | Milestone | Giorno | Deliverable |
|---|-----------|-------|-------------|
| M1 | Configurazione | 1 | Ambiente di sviluppo pronto |
| M2 | Architettura | 2 | Diagrammi UML e struttura del progetto |
| M3 | Database | 3-4 | Modelli dati implementati |
| M4 | API Core | 5-7 | Endpoint REST funzionanti |
| M5 | OAuth Fitbit | 8-10 | Integrazione completata |
| M6 | Frontend | 11-13 | UI funzionante con visualizzazioni |
| M7 | Test | 14 | Tutti i test completati |
| M8 | Documentazione | 15 | UML e documentazione finali |

### Monitoraggio del Progresso

- **Commit Giornalieri**: Tracciamento del progresso tramite Git
- **Testing Continuo**: Verifica manuale delle funzionalità durante lo sviluppo
- **Controllo Requisiti**: Verifica della completezza rispetto ai requisiti iniziali

## 13. Cambiamenti

### Gestione delle Modifiche

#### Approccio Semplificato
1. **Identificazione**: Annotare nuovi requisiti o cambiamenti necessari
2. **Valutazione**: Analizzare l'impatto sul piano di sviluppo (tempo e fattibilità)
3. **Prioritizzazione**: Decidere se implementare subito o rimandare a future iterazioni
4. **Implementazione**: Integrare i cambiamenti nel workflow di sviluppo

### Controllo del Codice

- **Version Control**: Utilizzo di Git per tracciare tutte le modifiche
- **Branch Strategy**: Sviluppo feature di grandi dimensioni su branch, merge nella branch principale
- **Commit Frequenti**: Piccoli commit con messaggi chiari e descrittivi

### Documentazione dei Cambiamenti

I cambiamenti significativi vengono documentati in un semplice messaggio nel commit

## 14. Consegna e Documentazione Finale

### Artefatti da Consegnare

1. **Codice Sorgente**: Completo e commentato nel repository Git
2. **Diagrammi UML**: Aggiornati e coerenti con l'implementazione finale
3. **Documentazione API**: Endpoint REST documentati con parametri
4. **Guida all'Installazione**: Istruzioni per configurare l'ambiente

### Testing Finale

- **Test Funzionali**: Verifica di tutte le features implementate
- **Test Manuali**: Verifica dell'usabilità e dell'interfaccia utente

### Documentazione Utente

- **Manuale Utente**: Guida all'utilizzo per i medici
- **Documentazione endpoints**: Guida sui vari endpoint del sistema
- **File dei requisiti**: Descrizione dei requisiti(funzionali e non funzionali) estesa tramite metodologia MoSCoW
- **README**: Documentazione introduttiva al progetto
- **Commenti nel Codice**: Documentazione inline per sviluppatori futuri

### Note di Sviluppo Futuro

- **Estensioni Possibili**: Integrazione con altre piattaforme health (Apple Health, Google Fit)
- **Ottimizzazioni**: Aree identificate per miglioramento delle performance
- **Funzionalità Future**: Nuove feature prioritizzate per sviluppi successivi