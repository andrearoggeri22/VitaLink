// translations.js - Translations for user interface elements in JavaScript

// Check the current language
const currentLanguage = document.documentElement.lang || 'en';

// Translation strings based on language
let deletePatientTitle, deletePatientMessage, addNoteForText, confirmButtonText, cancelButtonText;

if (currentLanguage === 'it') {
    // Italian translations
    deletePatientTitle = 'Elimina Paziente';
    deletePatientMessage = 'Sei sicuro di voler eliminare il paziente {name}? Questa azione non può essere annullata.';
    addNoteForText = 'Aggiungi nota per {name}';
    confirmButtonText = 'Conferma';
    cancelButtonText = 'Annulla';
} else {
    // Default English translations
    deletePatientTitle = 'Delete Patient';
    deletePatientMessage = 'Are you sure you want to delete the patient {name}? This action cannot be undone.';
    addNoteForText = 'Add Note for {name}';
    confirmButtonText = 'Confirm';
    cancelButtonText = 'Cancel';
}