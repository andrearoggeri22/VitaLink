# Requisiti del Sistema VitaLink

Questo documento descrive i requisiti funzionali e non funzionali del sistema VitaLink, utilizzando la metodologia MoSCoW per la prioritizzazione. Il documento è stato creato nella fase di pianificazione del progetto e serve come riferimento per lo sviluppo e la valutazione del sistema.

**Ultima revisione**: 06/05/2025 
**Versione**: 1.0
**Autore**: Roggeri Andrea

## Indice
1. [Panoramica del Sistema](#panoramica-del-sistema)
2. [Requisiti Funzionali](#requisiti-funzionali)
3. [Requisiti Non Funzionali](#requisiti-non-funzionali)
4. [Considerazioni Aggiuntive](#considerazioni-aggiuntive)

## Panoramica del Sistema

VitaLink è un sistema di consultazione di parametri vitali ottenuti da dispositivi wearable progettato per medici e operatori sanitari. Il sistema consente la gestione completa dei dati dei pazienti, il monitoraggio dei parametri vitali tramite integrazione con dispositivi e piattaforme sanitarie di terze parti, e la collaborazione tra professionisti sanitari.

Questo documento utilizza la metodologia di prioritizzazione MoSCoW:
- **Must have (M)**: Requisiti essenziali e non negoziabili per il lancio del prodotto
- **Should have (S)**: Requisiti importanti ma non critici per la prima release
- **Could have (C)**: Funzionalità desiderabili ma che potrebbero essere rimandate a versioni future
- **Won't have (W)**: Funzionalità esplicitamente escluse da questa versione del prodotto

## Requisiti Funzionali

### Must Have (M)
*Requisiti essenziali e non negoziabili per il lancio del prodotto*

1. **Autenticazione e Sicurezza**
   - Il sistema deve fornire un meccanismo sicuro di registrazione per i medici
   - Gli utenti devono potersi autenticare tramite email e password
   - Il sistema deve supportare l'autenticazione API tramite token JWT
   - Le password devono essere memorizzate con crittografia sicura (werkzeug)

2. **Gestione Pazienti**
   - I medici devono poter creare nuovi record paziente con informazioni anagrafiche di base
   - I medici devono poter visualizzare la lista di tutti i loro pazienti
   - I medici devono poter visualizzare i dettagli completi di un paziente
   - I medici devono poter modificare le informazioni dei loro pazienti
   - I medici devono poter aggiungere note mediche ai record dei pazienti

3. **Interfaccia Utente**
   - Il sistema deve fornire una dashboard per i medici che mostri statistiche rilevanti
   - L'interfaccia deve essere accessibile tramite browser web standard
   - L'interfaccia utente deve essere responsiva per supportare diversi dispositivi
   - La navigazione deve essere intuitiva e coerente in tutta l'applicazione

4. **API Base**
   - Il sistema deve fornire API RESTful per le operazioni CRUD sui pazienti
   - Le API devono supportare la ricerca e il filtraggio dei pazienti
   - Le API devono essere protette tramite autenticazione JWT
   - Le risposte API devono seguire standard coerenti e gestire gli errori in modo appropriato

### Should Have (S)
*Requisiti importanti ma non critici per la prima release*

1. **Integrazione con Piattaforme Sanitarie**
   - Il sistema dovrebbe integrarsi con Fitbit per recuperare dati sui parametri vitali
   - I medici dovrebbero poter visualizzare i parametri vitali del paziente in formato grafico
   - Il sistema dovrebbe supportare l'autenticazione OAuth con le piattaforme sanitarie
   - I dati dovrebbero essere sincronizzati periodicamente dalle piattaforme connesse

2. **Osservazioni sui Parametri Vitali**
   - I medici dovrebbero poter creare osservazioni sui parametri vitali dei pazienti
   - I medici dovrebbero poter modificare e eliminare le loro osservazioni
   - Il sistema dovrebbe supportare diversi tipi di parametri vitali (frequenza cardiaca, pressione sanguigna, ecc.)
   - Le osservazioni dovrebbero essere visualizzabili in modo cronologico

3. **Internazionalizzazione**
   - L'interfaccia utente dovrebbe essere disponibile in italiano e inglese
   - Il sistema dovrebbe consentire agli utenti di cambiare facilmente lingua
   - Date e numeri dovrebbero essere formattati in base alle convenzioni locali
   - I messaggi di errore dovrebbero essere localizzati

4. **Reportistica**
   - Il sistema dovrebbe generare report base sui dati dei pazienti
   - I report dovrebbero essere esportabili in formati standard (PDF)
   - I report dovrebbero essere inviabili al paziente tramite email
   - I medici dovrebbero poter personalizzare alcuni parametri dei report
   - I report generati dovrebbero essere archiviati per consultazioni future

### Could Have (C)
*Funzionalità desiderabili ma che potrebbero essere rimandate a versioni future*

1. **Integrazione con Ulteriori Piattaforme Sanitarie**
   - Il sistema potrebbe integrarsi con Apple Health
   - Il sistema potrebbe integrarsi con Google Fit
   - Il sistema potrebbe integrarsi con Garmin Connect
   - Il sistema potrebbe supportare dispositivi medici Bluetooth LE

2. **Collaborazione tra Medici**
   - I medici potrebbero condividere l'accesso ai pazienti con altri medici
   - Il sistema potrebbe supportare commenti collaborativi sulle note mediche
   - I medici potrebbero ricevere notifiche quando ci sono aggiornamenti sui pazienti condivisi
   - Il sistema potrebbe tenere traccia di chi ha effettuato modifiche ai record

3. **Autenticazione a Due Fattori**
   - Il sistema potrebbe supportare l'autenticazione a due fattori via SMS
   - Il sistema potrebbe supportare l'autenticazione a due fattori via app mobile
   - L'utente potrebbe configurare le preferenze di sicurezza del proprio account
   - Il sistema potrebbe richiedere 2FA per operazioni sensibili

4. **Analisi Avanzata dei Dati**
   - Il sistema potrebbe implementare algoritmi di rilevamento anomalie nei parametri vitali
   - Il sistema potrebbe offrire suggerimenti basati sui trend dei dati
   - Il sistema potrebbe generare report comparativi tra pazienti anonimi
   - Il sistema potrebbe supportare la visualizzazione di correlazioni tra diversi parametri

### Won't Have (W)
*Funzionalità esplicitamente escluse da questa versione del prodotto*

1. **Prescrizione Elettronica**
   - Il sistema non supporterà la generazione di prescrizioni elettroniche
   - Non ci sarà integrazione con farmacie o sistemi di prescrizione nazionali
   - Non sarà possibile tracciare l'aderenza ai farmaci prescritti
   - Non ci sarà un modulo di gestione inventario farmaci

2. **Cartella Clinica Elettronica Completa**
   - Il sistema non sostituirà una cartella clinica elettronica completa
   - Non ci saranno moduli per la gestione di esami di laboratorio
   - Non ci sarà integrazione con sistemi ospedalieri (HIS)
   - Non ci sarà supporto per la gestione di immagini diagnostiche

3. **Telemedicina**
   - Il sistema non includerà funzionalità di videoconferenza
   - Non ci sarà supporto per consultazioni remote in tempo reale
   - Non ci saranno strumenti per la pianificazione di visite virtuali
   - Non ci sarà integrazione con sistemi di pagamento per visite telematiche

4. **App Mobile Dedicata**
   - Non verrà sviluppata un'app mobile dedicata nella prima fase
   - I pazienti non avranno accesso diretto al sistema
   - Non ci sarà supporto per notifiche push su dispositivi mobili
   - Non ci sarà funzionalità offline per l'app mobile

## Requisiti Non Funzionali

### Must Have (M)

1. **Sicurezza e Privacy**
   - Tutti i dati personali dei pazienti devono essere crittografati a riposo
   - Deve essere implementato un sistema completo di log per gli audit di sicurezza

2. **Performance**
   - Il tempo di risposta per le operazioni di base deve essere inferiore a 2 secondi
   - Il sistema deve supportare almeno 1000 utenti concorrenti
   - Il caricamento della dashboard non deve richiedere più di 3 secondi
   - Il sistema deve supportare la gestione di almeno 100.000 record paziente

3. **Disponibilità**
   - Il sistema deve avere un uptime del 99,9% durante le ore lavorative
   - I backup del database devono essere eseguiti quotidianamente

4. **Usabilità**
   - L'interfaccia utente deve essere utilizzabile senza formazione specifica
   - I flussi di lavoro principali non devono richiedere più di 3 clic
   - I messaggi di errore devono essere chiari e fornire indicazioni per la risoluzione

### Should Have (S)

1. **Scalabilità**
   - L'architettura dovrebbe supportare lo scaling orizzontale
   - Il database dovrebbe gestire efficacemente l'aumento di volume dei dati
   - Le prestazioni non dovrebbero degradarsi significativamente con l'aumentare degli utenti
   - Il sistema dovrebbe implementare tecniche di caching per migliorare la reattività

2. **Manutenibilità**
   - Il codice dovrebbe seguire standard di codifica e best practice
   - La documentazione del codice dovrebbe essere completa e aggiornata
   - L'architettura dovrebbe essere modulare per facilitare gli aggiornamenti
   - Il sistema dovrebbe supportare aggiornamenti con tempi di inattività minimi

3. **Portabilità**
   - Il sistema dovrebbe funzionare sui principali browser web (Chrome, Firefox, Edge, Safari)
   - L'interfaccia utente dovrebbe adattarsi a diverse risoluzioni dello schermo
   - Il sistema dovrebbe essere containerizzato per facilitare il deployment
   - Il backend dovrebbe funzionare su diversi sistemi operativi server

4. **Interoperabilità**
   - Le API dovrebbero seguire standard RESTful
   - Il sistema dovrebbe supportare almeno il formato JSON per lo scambio di dati
   - Il sistema dovrebbe utilizzare formati standard per date, orari e dati medici

### Could Have (C)

1. **Prestazioni Avanzate**
   - Il sistema potrebbe implementare tecniche di precaricamento dei dati
   - L'interfaccia utente potrebbe utilizzare rendering lato server per il caricamento iniziale
   - Il sistema potrebbe implementare la compressione delle risposte API
   - Il database potrebbe essere ottimizzato con indici avanzati e strategie di partizionamento

2. **Monitoraggio e Analytics**
   - Il sistema potrebbe implementare dashboard di monitoraggio in tempo reale
   - Le metriche di prestazione potrebbero essere raccolte e analizzate
   - Il sistema potrebbe implementare alerting automatico per problemi prestazionali
   - Gli errori utente potrebbero essere tracciati per identificare problemi di usabilità

3. **Supporto Offline**
   - L'interfaccia utente potrebbe implementare funzionalità progressive web app
   - I dati critici potrebbero essere memorizzati nella cache del browser
   - Il sistema potrebbe supportare la sincronizzazione dei dati dopo la riconnessione
   - Le modifiche potrebbero essere accodate quando offline

4. **Testing Automatizzato**
   - Il sistema potrebbe avere una copertura di test unitari superiore all'85%
   - I test di integrazione potrebbero essere eseguiti automaticamente
   - Il sistema potrebbe implementare test di carico programmati
   - Il processo di CI/CD potrebbe includere test di sicurezza automatizzati

### Won't Have (W)

1. **Supporto Legacy**
   - Non ci sarà compatibilità con sistemi operativi obsoleti
   - Non verranno fornite versioni desktop standalone

2. **Alta Disponibilità Geografica**
   - Il sistema non implementerà il deployment multi-regione nella prima fase
   - Non ci sarà failover automatico tra diversi data center
   - Non ci sarà ottimizzazione per utenti in regioni geografiche specifiche
   - Non ci sarà un sistema di content delivery network globale

3. **Integrazione Enterprise Completa**
   - Non ci sarà supporto per Single Sign-On aziendale completo
   - Non ci sarà integrazione con sistemi ERP legacy
   - Non ci saranno connettori personalizzati per ogni sistema clinico

4. **Conformità Internazionale Completa**
   - Il sistema non sarà inizialmente certificato per standard internazionali come HIPAA
   - Non ci sarà supporto completo per tutti i requisiti normativi regionali
   - Non ci saranno localizzazioni complete per tutti i paesi
   - Non ci sarà certificazione FDA come dispositivo medico

## Considerazioni Aggiuntive

### Rischi Identificati
- Normativa: frequenti cambiamenti nelle leggi sulla privacy sanitaria
- Integrazione: dipendenza dalle API di terze parti e compatibilità
- Adozione: resistenza al cambiamento da parte dei medici
- Performance: gestione efficiente di grandi volumi di dati sanitari