# VitaLink Mobile - App Android per la sincronizzazione automatica dei dati Fitbit

## Panoramica
VitaLink Mobile è un'applicazione Android che permette ai pazienti di sincronizzare automaticamente i loro dati di salute dai dispositivi Fitbit al sistema VitaLink. Una volta configurata, l'app funziona in background, senza richiedere ulteriori azioni da parte dell'utente.

## Caratteristiche principali

- **Autenticazione semplice**: Il paziente deve inserire solo il suo UUID fornito dal medico
- **Rilevamento dispositivi Fitbit**: Rilevamento automatico dei dispositivi Fitbit collegati tramite Bluetooth 
- **Sincronizzazione dati in background**: Raccolta e invio automatico dei dati vitali al server VitaLink
- **Risparmio energetico**: Progettata per un impatto minimo sulla batteria dello smartphone
- **Notifiche**: Invia notifiche per confermare il successo della sincronizzazione o per avvisare di eventuali problemi
- **Interfaccia utente semplice**: Facile da usare e configurare anche per pazienti anziani o non esperti di tecnologia

## Tecnologie utilizzate

- Linguaggio Kotlin
- Android Jetpack (ViewModel, LiveData, Room, WorkManager)
- Retrofit per le API REST 
- Bluetooth LE per la connessione ai dispositivi
- Fitbit SDK per l'accesso ai dati
- Servizi in background per la sincronizzazione automatica

## Struttura del progetto

- `app/src/main/java/com/vitalink/mobile/`
  - `ui/`: Interfaccia utente dell'applicazione
  - `network/`: Chiamate API e gestione della connessione
  - `data/`: Gestione dei dati e persistenza locale
  - `fitbit/`: Integrazione con i dispositivi Fitbit
  - `service/`: Servizi in background per la sincronizzazione
  - `util/`: Utilità condivise

## Dettagli di implementazione

L'applicazione è strutturata secondo il pattern MVVM (Model-View-ViewModel) e utilizza i componenti di Android Architecture per garantire un'applicazione robusta e facile da mantenere.

### Flusso di funzionamento

1. L'utente inserisce l'UUID fornito dal medico
2. L'app verifica l'UUID con il server e ottiene l'ID del paziente
3. La configurazione iniziale consente all'utente di associare un dispositivo Fitbit
4. Un servizio in background raccoglie periodicamente i dati dal dispositivo Fitbit
5. I dati vengono inviati al server VitaLink tramite le API REST
6. L'utente riceve notifiche relative allo stato della sincronizzazione

### Sicurezza

L'app implementa misure di sicurezza per proteggere i dati sensibili del paziente:
- I dati sono criptati quando memorizzati localmente
- Le comunicazioni con il server avvengono tramite HTTPS
- Non vengono memorizzate informazioni personali oltre all'UUID del paziente