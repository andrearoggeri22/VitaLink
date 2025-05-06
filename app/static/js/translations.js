/**
 * translations.js - Manages translations for user interface elements in JavaScript
 * 
 * This file provides translation functionality for the VitaLink system, supporting
 * internationalization of the user interface. It includes a main translation function
 * and predefined text strings for various UI elements.
 */
/**
 * @type {string}
 * The current language set in the application.
 * Retrieved from the 'lang' attribute of the HTML root element or set to 'en' (English) as default
 */
var currentLanguage = document.documentElement.lang || 'en';
/**
 * Translates a text from English to the currently set language
 * 
 * @param {string} text - The English text to translate
 * @returns {string} The translated text in the current language or the original text if no translation is available
 * @example
 * // Returns "Salva" in Italian or "Save" in English
 * const buttonLabel = translateText('Save');
 */
function translateText(text) {
    currentLanguage = document.documentElement.lang || 'en';
    // This function allows for future integration with proper translation systems
    // For now, it returns hardcoded translations based on current language
    if (currentLanguage === 'it') {
        // Add Italian translations for common messages here
        const translations = {
            // Form validation messages
            'Please select at least one time period for each selected vital type': 'Seleziona almeno un periodo di tempo per ogni tipo di parametro vitale selezionato',
            // Error messages
            'An error occurred while deleting the note.': 'Si è verificato un errore durante l\'eliminazione della nota.',
            'Error saving observation. Please try again later.': 'Errore nel salvataggio dell\'osservazione. Riprova più tardi.',
            'Error deleting observation. Please try again later.': 'Errore nell\'eliminazione dell\'osservazione. Riprova più tardi.',
            'Error creating link': 'Errore creazione link',
            'An error occurred while importing the patient. Please try again later.': 'Si è verificato un errore durante l\'importazione del paziente. Riprova più tardi.',
            'Start date must be before end date': 'La data di inizio deve essere precedente alla data di fine',
            'Error loading observations': 'Errore nel caricamento delle osservazioni',
            'Error checking connection': 'Errore nel controllo della connessione',
            'Error showing period buttons': 'Errore nel mostrare i pulsanti del periodo',
            'Error loading data. Try again later.': 'Errore nel caricamento dei dati. Riprova più tardi.',
            'Retry': 'Riprova',
            'Error populating options': 'Errore nel popolamento delle opzioni',
            'Error selecting vital type': 'Errore nella selezione del tipo vitale',
            'Error in vital type selection': 'Errore nella selezione del tipo vitale',
            'Connect to a health platform to view vital signs data.': 'Collegati ad una piattaforma di salute per visualizzare i dati dei parametri vitali.',
            'No data available. Connect a health platform.': 'Nessun dato disponibile. Collega una piattaforma di salute.',
            'Observation deleted successfully': 'Osservazione eliminata con successo',
            'Observation added successfully': 'Osservazione aggiunta con successo',
            'Warning': 'Attenzione',
            'Are you sure you want to delete this observation?': 'Sei sicuro di voler eliminare questa osservazione?',
            'Delete observation': 'Elimina osservazione',
            'Add observation': 'Aggiungi osservazione',
            'No data available for': 'Nessun dato disponibile per',
            'Disconnection completed successfully': 'Disconnessione completata con successo',
            'Error during disconnection:': 'Errore durante la disconnessione:',
            'Error during disconnection. Try again later.': 'Errore durante la disconnessione. Riprova più tardi.',
            'Cancel': 'Annulla',
            'Disconnect': 'Disconnetti',
            'Importing...': 'Importazione...',
            'Import Patient': 'Importa Paziente',
            'Unsupported platform:': 'Piattaforma non supportata:',
            'Connect Health Platform': 'Connetti Piattaforma di Salute',
            'Generate a connection link for health data:': 'Genera un link di connessione per i dati di salute:',
            'Generate Link': 'Genera Link',
            'Close': 'Chiudi',
            'Disconnect Platform': 'Disconnetti Piattaforma',
            'Are you sure you want to disconnect this platform? The data will no longer be available.': 'Sei sicuro di voler disconnettere questa piattaforma? I dati non saranno più disponibili.',
            'Disconnecting...': 'Disconnessione in corso...',
            'Successfully disconnected from health platform': 'Disconnessione dalla piattaforma di salute completata con successo',
            'Error disconnecting. Please try again later.': 'Errore durante la disconnessione. Riprova più tardi.',
            'Error disconnecting:': 'Errore durante la disconnessione:',
            'Copy': 'Copia',
            'Provide this link to the patient to connect their data collection service.': 'Fornisci questo link al paziente per connettere il suo servizio di raccolta dati.',
            'Link created successfully!': 'Link creato con successo!',            'Confirm Deletion': 'Conferma Eliminazione',
            'Are you sure you want to delete this note? This action cannot be undone.': 'Sei sicuro di voler eliminare questa nota? Questa azione non può essere annullata.',
            'Delete': 'Elimina',
            'Are you sure you want to delete this item? This action cannot be undone.': 'Sei sicuro di voler eliminare questo elemento? Questa azione non può essere annullata.',
            'Delete Patient': 'Elimina paziente',
            'Are you sure you want to delete the patient? This action cannot be undone.': 'Sei sicuro di voler eliminare il paziente? L\'azione non può essere cancellata.',
            'Add note': 'Aggiungi nota',
            'Importing...': 'Importazione...',
            'Confirm': 'Conferma',
            'No expiration': 'Nessuna scadenza',
            'Health Sync': 'Sincronizza Salute',
            'Creating connection link...': 'Creazione del link di connessione...',
            'Connection link (valid for 24 hours):': 'Link di connessione (valido per 24 ore):',
            'Copied': 'Copiato',
            'Try Again': 'Riprova',
            'Loading data from health platform...': 'Caricamento dati dalla piattaforma di salute...',
            'Error loading data from health platform': 'Errore nel caricamento dei dati dalla piattaforma di salute',
            'No data available for this parameter': 'Nessun dato disponibile per questo parametro',
            'Date/Time': 'Data/Ora',
            'Generate': 'Genera',
            'Report': 'Report',
            'Unknown Doctor': 'Medico sconosciuto',
            'No notes available': 'Nessuna nota disponibile',
            'Error loading notes': 'Errore nel caricamento delle note',
            'No observations available for this vital type': 'Nessuna osservazione disponibile per questo tipo di parametro vitale',
            'Loading data...': 'Caricamento dati...',
            'Last': 'Ultimi',
            'day': 'giorno',
            'days': 'giorni',
            // Messages for console and debugging
            'Initializing observations management': 'Inizializzazione gestione osservazioni',
            'Observations loaded:': 'Osservazioni caricate:',
            'updateObservationsUI: observations is not an array': 'updateObservationsUI: observations non è un array',
            'Current type:': 'Tipo corrente:',
            'Showing only observations for type:': 'Mostrando solo osservazioni per il tipo:',
            'Sending observation:': 'Invio osservazione:',
            'Observation saved:': 'Osservazione salvata:',
            'Showing API error:': 'Mostrando errore API:',
            'Deleting observation with ID:': 'Eliminazione osservazione con ID:',
            'Observation deleted:': 'Osservazione eliminata:',
            // Tecnical error messages
            'Network response was not ok': 'Risposta di rete non valida',
            'Tab container not found': 'Container delle schede non trovato',
            'Canvas not found for chart': 'Canvas non trovato per il grafico',
            'Data table body not found': 'Corpo della tabella dati non trovato',
            'Unsupported data type:': 'Tipo di dati non supportato:',
            'Error creating link. Please try again.': 'Errore nella creazione del link. Riprova.',
            'Unable to determine patient ID': 'Impossibile determinare l\'ID del paziente',
            'Unable to determine patient ID or data type': 'Impossibile determinare l\'ID del paziente o il tipo di dati',
            'Error loading data for': 'Errore nel caricamento dei dati per',
            'Period hidden: no active connection': 'Periodo nascosto: nessuna connessione attiva',
            'Period shown: active connection with': 'Periodo mostrato: connessione attiva con',
            'Error hiding period buttons:': 'Errore nel nascondere i pulsanti del periodo:',
            // Other messages
            'Initializing vital parameters charts': 'Inizializzazione grafici dei parametri vitali',
            'Loading...': 'Caricamento...',
            'Heart Rate': 'Frequenza cardiaca',
            'Oxygen Saturation': 'Saturazione di ossigeno',
            'Weight': 'Peso',
            'Breathing Rate': 'Frequenza respiratoria',
            'Core Temperature': 'Temperatura corporea',
            'Skin Temperature': 'Temperatura cutanea',
            'Steps': 'Passi',
            'Distance': 'Distanza',
            'Calories Burned': 'Calorie bruciate',
            'Active Minutes': 'Minuti attivi',
            'Sleep Duration': 'Durata del sonno',
            'Floors Climbed': 'Piani saliti',
            'Elevation': 'Elevazione',
            'Activity Calories': 'Calorie da attività',
            'Basal Metabolism': 'Metabolismo basale',
            'Sedentary Time': 'Tempo sedentario',
            'Light Activity': 'Attività leggera',
            'Moderate Activity': 'Attività moderata',
            'Calories Intake': 'Calorie consumate',
            'Water Consumption': 'Consumo di acqua',
            'Initial vital type set to:': 'Tipo vitale iniziale impostato a:',
            'Current vital type set to:': 'Tipo vitale corrente impostato a:',
            'Reloading observations with filter on current vital type': 'Ricaricamento osservazioni con filtro sul tipo vitale corrente',
            'Date': 'Data',
            'Please select a vital sign type first.': 'Seleziona prima un tipo di parametro vitale.',
            'Initializing global variables...': 'Inizializzazione variabili globali...',
            'Starting initVitalsCharts...': 'Avvio initVitalsCharts...',
            'Status after initVitalsCharts:': 'Stato dopo initVitalsCharts:',
            'Starting initObservations...': 'Avvio initObservations...',
            'Status after initObservations:': 'Stato dopo initObservations:',
            'Error fetching vital signs data:': 'Errore nel recupero dei dati vitali:',
            'Note deleted successfully': 'Nota eliminata con successo',
            'Data': 'Dati',
            'hours': 'ore',
        };
        return translations[text] || text;
    }
    return text;
}
/**
 * Preconfigured translation strings based on language
 * These variables are used throughout the project for UI elements that require
 * consistent translations across the application
 */
/** @type {string} Title for the patient deletion dialog */
let deletePatientTitle;
/** @type {string} Confirmation message for patient deletion */
let deletePatientMessage;
/** @type {string} Generic confirmation message for item deletion */
let deleteItemMessage;
/** @type {string} Text for add note button */
let addNoteForText;
/** @type {string} Text for the confirm button */
let confirmButtonText;
/** @type {string} Text for the cancel button */
let cancelButtonText;
/** @type {string} Label for date fields */
let dateText;
/** @type {string} Text for normal vital values */
let normalText;
/** @type {string} Text for high vital values */
let highText;
/** @type {string} Text for low vital values */
let lowText;
/** @type {string} Text for the save button */
let saveText;
/** @type {string} Connected device message */
let deviceConnectedText;
/** @type {string} No device connected message */
let deviceNotConnectedText;
/** @type {string} No data available message */
let noDataText;
/** @type {string} Loading data in progress text */
let loadingText;
/** @type {string} Generic error message */
let errorText;
/** @type {string} Generic success message */
let successText;
/** @type {string} Title for vital parameters charts */
let vitalsChartTitleText;
// Set variable values based on the current language
if (currentLanguage === 'it') {
    // Italian translations
    deletePatientTitle = 'Elimina Paziente';
    deletePatientMessage = 'Sei sicuro di voler eliminare il paziente? Questa azione non può essere annullata.';
    deleteItemMessage = 'Sei sicuro di voler eliminare questo elemento? Questa azione non può essere annullata.';
    addNoteForText = 'Aggiungi nota';
    confirmButtonText = 'Conferma';
    cancelButtonText = 'Annulla';
    // Data and vital values
    dateText = 'Data';
    normalText = 'Normale';
    highText = 'Alto';
    lowText = 'Basso';
    saveText = 'Salva';
    // Devices messages
    deviceConnectedText = 'Dispositivo connesso';
    deviceNotConnectedText = 'Nessun dispositivo connesso';
    // General messages
    noDataText = 'Nessun dato disponibile';
    loadingText = 'Caricamento in corso...';
    errorText = 'Si è verificato un errore';
    successText = 'Operazione completata con successo';
    // Graphs
    vitalsChartTitleText = 'Andamento dei parametri vitali';
} else {
    // Default English translations
    deletePatientTitle = 'Delete Patient';
    deletePatientMessage = 'Are you sure you want to delete the patient? This action cannot be undone.';
    deleteItemMessage = 'Are you sure you want to delete this item? This action cannot be undone.';
    addNoteForText = 'Add Note';
    confirmButtonText = 'Confirm';
    cancelButtonText = 'Cancel';
    // Date and vital values
    dateText = 'Date';
    normalText = 'Normal';
    highText = 'High';
    lowText = 'Low';
    saveText = 'Save';
    // Device messages
    deviceConnectedText = 'Device connected';
    deviceNotConnectedText = 'No device connected';
    // General messages
    noDataText = 'No data available';
    loadingText = 'Loading...';
    errorText = 'An error occurred';
    successText = 'Operation completed successfully';
    // Charts
    vitalsChartTitleText = 'Vital Signs Trend';
}