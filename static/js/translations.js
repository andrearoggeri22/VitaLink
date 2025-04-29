// translations.js - Translations for user interface elements in JavaScript

// Check the current language
const currentLanguage = document.documentElement.lang || 'en';

// Translation function for dynamic texts
function translateText(text) {
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
            'Unsupported platform:': 'Piattaforma non supportata:',            'Connect Health Platform': 'Connetti Piattaforma di Salute',
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
            'Confirm': 'Conferma'
        };
        
        return translations[text] || text;
    }
    
    return text;
}

// Translation strings based on language
let deletePatientTitle, deletePatientMessage, deleteItemMessage, addNoteForText, confirmButtonText, cancelButtonText;
let dateText, normalText, highText, lowText, saveText, deviceConnectedText, deviceNotConnectedText;
let noDataText, loadingText, errorText, successText, vitalsChartTitleText;

if (currentLanguage === 'it') {
    // Italian translations
    deletePatientTitle = 'Elimina Paziente';
    deletePatientMessage = 'Sei sicuro di voler eliminare il paziente? Questa azione non può essere annullata.';
    deleteItemMessage = 'Sei sicuro di voler eliminare questo elemento? Questa azione non può essere annullata.';
    addNoteForText = 'Aggiungi nota';
    confirmButtonText = 'Conferma';
    cancelButtonText = 'Annulla';
    
    // Data e valori vitali
    dateText = 'Data';
    normalText = 'Normale';
    highText = 'Alto';
    lowText = 'Basso';
    saveText = 'Salva';
    
    // Messaggi dispositivo
    deviceConnectedText = 'Dispositivo connesso';
    deviceNotConnectedText = 'Nessun dispositivo connesso';
    
    // Messaggi generali
    noDataText = 'Nessun dato disponibile';
    loadingText = 'Caricamento in corso...';
    errorText = 'Si è verificato un errore';
    successText = 'Operazione completata con successo';
    
    // Grafici
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