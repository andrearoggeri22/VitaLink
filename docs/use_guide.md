# Guida all'uso di VitaLink per Medici

**Ultima revisione**: 06/05/2025
**Versione**: 1.0
**Autore**: Roggeri Andrea

## Introduzione

Guida all'uso di VitaLink. Questo documento guiderà attraverso gli scenari più comuni che in cui si puà incorrere nell'utilizzo quotidiano del sistema.

## Indice

1. [Accesso e autenticazione](#accesso-e-autenticazione)
2. [Gestione dei pazienti](#gestione-dei-pazienti)
3. [Monitoraggio parametri vitali](#monitoraggio-parametri-vitali)
4. [Gestione osservazioni cliniche](#gestione-osservazioni-cliniche)
5. [Note mediche](#note-mediche)
6. [Generazione report](#generazione-report)
7. [Integrazione con dispositivi Fitbit](#integrazione-con-dispositivi-fitbit)
8. [Importazione pazienti](#importazione-pazienti)
9. [Tracciamento audit](#tracciamento-audit)
10. [Preferenze e impostazioni](#preferenze-e-impostazioni)

---

## Accesso e autenticazione

### Scenario 1: Primo accesso al sistema

1. Aprite il browser e navigate all'indirizzo di VitaLink
2. Cliccate su "Registrazione" nella pagina di login
3. Compilate il modulo con i vostri dati:
   - Email (sarà usata per il login)
   - Nome e cognome
   - Specializzazione medica
   - Password (rispettare i requisiti di sicurezza)
4. Cliccate su "Registrati"
5. Accedete al sistema con le credenziali appena create

### Scenario 2: Login giornaliero

1. Navigate alla pagina di login
2. Inserite la vostra email e password
3. Cliccate su "Accedi"
4. Verrete reindirizzati alla dashboard principale

---

## Gestione dei pazienti

### Scenario 3: Registrazione di un nuovo paziente

1. Dalla dashboard, cliccate su "Pazienti" nel menu laterale
2. Cliccate sul pulsante "+ Nuovo paziente"
3. Compilate il modulo con i dati del paziente:
   - Nome e cognome
   - Data di nascita
   - Genere
   - Informazioni di contatto (telefono, email)
   - Indirizzo (opzionale)
4. Cliccate su "Salva"
5. Verrà generato un UUID univoco per il paziente che potrete comunicare ad altri medici per l'importazione

### Scenario 4: Visualizzazione dettagli paziente

1. Dalla lista pazienti, cliccate sul nome del paziente
2. Nella pagina di dettaglio troverete:
   - Informazioni anagrafiche
   - Collegamento alla pagina dei parametri vitali (se collegato a dispositivi)
   - Collegamento alla pagina di modifica dei dati del paziente
   - Note mediche

### Scenario 5: Modifica dati paziente

1. Nella pagina di dettaglio del paziente, cliccate su "Modifica"
2. Aggiornate i campi necessari
3. Cliccate su "Salva modifiche"
4. Un messaggio confermerà l'aggiornamento dei dati

> **Nota**: Tutte le modifiche vengono registrate nel sistema di audit per garantire la tracciabilità.

---

## Monitoraggio parametri vitali

### Scenario 6: Visualizzazione parametri vitali

1. Dalla pagina di dettaglio del paziente, selezionate la scheda "Parametri vitali"
2. Scegliete il tipo di parametro da visualizzare dal menu a tendina:
   - Frequenza cardiaca
   - Saturazione ossigeno
   - Passi giornalieri
   - Peso
   - Sonno
   - Attività fisica
3. Selezionate il periodo di interesse:
   - Ultime 24 ore
   - Ultima settimana
   - Ultimo mese
   - Ultimi 3 mesi
4. I dati verranno visualizzati sotto forma di grafico interattivo e in forma tabellare

> **Importante**: I dati vengono recuperati in tempo reale dai dispositivi collegati. Se il paziente non ha un dispositivo collegato, vedrete un messaggio di avviso.

## Gestione osservazioni cliniche

### Scenario 7: Aggiunta di un'osservazione sui parametri vitali

1. Mentre visualizzate un grafico dei parametri vitali, cliccate su "Aggiungi osservazione"
2. Compilate il modulo:
   - Selezionate il tipo di parametro vitale a cui si riferisce l'osservazione
   - Specificate la data di inizio e fine del periodo di osservazione
   - Inserite il contenuto dell'osservazione (es. "Frequenza cardiaca elevata durante il riposo")
3. Cliccate su "Salva osservazione"
4. L'osservazione apparirà sotto il grafico corrispondente

### Scenario 8: Eliminazione di un'osservazione

1. Individuate l'osservazione da eliminare
2. Cliccate sull'icona di eliminazione
3. Confermate l'eliminazione nella finestra di dialogo
4. L'osservazione verrà rimossa immediatamente

---

## Note mediche

### Scenario 9: Aggiunta di una nota medica

1. Dalla pagina di dettaglio del paziente, selezionate la scheda "Note mediche"
2. Cliccate su "Nuova nota"
3. Inserite il contenuto della nota nel campo di testo
4. Cliccate su "Salva nota"
5. La nota verrà aggiunta alla lista, con data e ora di creazione

### Scenario 10: Visualizzazione delle note

1. Accedete alla scheda "Note mediche" del paziente
2. Le note sono ordinate cronologicamente, con la più recente in cima
3. Ogni nota mostra:
   - Data e ora di creazione
   - Nome del medico che l'ha scritta
   - Contenuto della nota

### Scenario 11: Eliminazione di una nota

1. Individuate la nota da eliminare
2. Cliccate sull'icona di eliminazione
3. Confermate l'eliminazione
4. La nota verrà rimossa dalla lista

---

## Generazione report

### Scenario 12: Generazione di un report completo

1. Dalla pagina di dettaglio del paziente, cliccate su "Report completo"
2. Selezionate i componenti da includere:
   - Invio per email
   - Parametri vitali specifici (selezionate quali)
   - Note mediche
   - Osservazioni specifiche (selezionate quali)
   - Grafici dei trend (selezionate quali)
3. Aggiungete un sommario personalizzato nel campo apposito
4. Cliccate su "Genera report"
5. Scaricate il PDF generato

### Scenario 13: Generazione di un report parametro specifico

1. Cliccate su "Report parametro specifico"
2. Selezionate i componenti da includere:
   - Invio per email
   - Parametri vitali specifici (selezionate quali)
   - Note mediche
   - Osservazioni specifiche (selezionate quali)
   - Grafici dei trend (selezionate quali)
3. Aggiungete un sommario personalizzato nel campo apposito
4. Cliccate su "Genera report"
5. Scaricate il PDF generato

### Scenario 14: Invio del report via email

1. Dopo aver compilato un report, selezionare "Invia via email"
4. Cliccate su "Genera report"
5. Il sistema invierà un'email con il report allegato

---

## Integrazione con dispositivi Fitbit

### Scenario 15: Collegamento di un dispositivo Fitbit

1. Dalla pagina di dettaglio del paziente, selezionate "Connetti dispositivo"
2. Scegliete "Fitbit" dalla lista delle piattaforme disponibili
3. Cliccate su "Genera link di collegamento"
4. Inviate il link generato al paziente (via email o altro metodo)
5. Il paziente dovrà:
   - Aprire il link
   - Accedere al proprio account Fitbit
   - Autorizzare l'accesso a VitaLink
6. Una volta completata l'autorizzazione, vedrete una conferma nella pagina del paziente

### Scenario 16: Sincronizzazione dati Fitbit

1. Dopo il collegamento del dispositivo, i dati verranno sincronizzati automaticamente
2. Per forzare una sincronizzazione manuale:
   - Accedete alla scheda "Parametri vitali"
   - Cliccate su "Sincronizza dati"
   - Attendete il completamento della sincronizzazione
3. La data e ora dell'ultima sincronizzazione è visibile nella pagina dei parametri vitali

### Scenario 17: Gestione problemi di connessione

1. Se il sistema mostra un avviso di errore di connessione:
   - Verificate che il token di accesso sia ancora valido
   - Cliccate su "Aggiorna collegamento" per tentare un refresh automatico
   - Se il problema persiste, generate un nuovo link di collegamento
2. Se il paziente ha revocato l'accesso da Fitbit:
   - Vedrete un avviso nella pagina del paziente
   - Sarà necessario generare un nuovo link di collegamento
   - Il paziente dovrà autorizzare nuovamente l'accesso

### Scenario 18: Connessione di un dispositivo wearable

1. Cliccate sul pulsante "Health Sync"
   - Apparirà un QR Code e un link per la condivisione
   - Scegliere un metodo di condivisione da fornire al paziente
   - Una volta che il paziente avrà effettuato la connessione, vedrete i suoi dati aggiornati

---

## Importazione pazienti

### Scenario 19: Importazione di un paziente esistente

1. Dalla pagina dei pazienti, cliccate su "Importa paziente"
2. Inserite l'UUID del paziente (che vi deve essere stato comunicato dal paziente o da un altro medico)
3. Cliccate su "Importa"
4. Se l'UUID è valido, il paziente verrà aggiunto alla vostra lista
5. Potrete accedere a tutti i dati del paziente, incluse le connessioni alle piattaforme sanitarie

> **Nota**: L'importazione di un paziente non rimuove l'accesso ad altri medici che già seguono il paziente.

---

## Tracciamento audit

### Scenario 20: Visualizzazione log di audit

1. Dal menu principale, selezionate "Log di audit"
2. Utilizzate i filtri per restringere la visualizzazione:
   - Periodo di tempo
   - Tipo di azione (creazione, modifica, eliminazione)
   - Tipo di entità (paziente, nota, osservazione)
   - Paziente
3. I log mostrano:
   - Data e ora dell'azione
   - Medico che ha eseguito l'azione
   - Tipo di azione
   - Entità coinvolta
   - Dettagli specifici
   - Paziente coinvolto

---

## Preferenze e impostazioni

### Scenario 21: Cambio lingua dell'interfaccia

1. Cliccate sul vostro nome utente nell'angolo in alto a destra
2. Nel menu a tendina "Lingua", scegliete tra:
   - Italiano
   - English (Inglese)
3. L'interfaccia verrà immediatamente aggiornata nella lingua selezionata

### Scenario 22: Modifica password

1. Accedete a "Profilo" dal menu utente cliccando sul menù in alto a destra
2. Andare alla sezione "Cambio password"
3. Inserite la password attuale
4. Inserite e confermate la nuova password
5. Cliccate su "Aggiorna password"
6. Un messaggio confermerà l'aggiornamento della password
