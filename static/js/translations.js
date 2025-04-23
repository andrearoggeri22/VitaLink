// translations.js - Translations for user interface elements in JavaScript

// Check the current language
const currentLanguage = document.documentElement.lang || 'en';

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