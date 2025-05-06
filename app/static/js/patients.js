// patients.js - JavaScript for patient-related functionality
/**
 * Initialize all patient management functionality when the document is loaded.
 * 
 * Sets up all patient-related features including form validation, search functionality,
 * delete confirmation dialogs, and patient import capabilities. This is the main entry 
 * point for the patient management JavaScript functionality.
 * 
 * @listens DOMContentLoaded
 */
document.addEventListener('DOMContentLoaded', function () {
    // Initialize the new patient form or edit patient form
    initPatientForm();
    // Set up search functionality
    initPatientSearch();
    // Set up delete patient confirmation
    initDeleteConfirmation();
    // Set up import patient functionality
    initImportPatient();
});
/**
 * Initialize patient form functionality.
 * 
 * Sets up form validation for patient data entry forms and configures
 * the date of birth field to have the current date as the maximum allowed value
 * to prevent invalid birthdates in the future. Adds client-side validation
 * to ensure data integrity before submission.
 */
function initPatientForm() {
    const patientForm = document.getElementById('patientForm');
    if (patientForm) {
        // Set today's date as max for date of birth
        const dobInput = document.getElementById('date_of_birth');
        if (dobInput) {
            const today = new Date().toISOString().split('T')[0];
            dobInput.setAttribute('max', today);
        }
        // Form validation
        patientForm.addEventListener('submit', function (event) {
            if (!patientForm.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            patientForm.classList.add('was-validated');
        });
    }
}
/**
 * Initialize patient search functionality.
 * 
 * Sets up real-time filtering of the patient list as the user types in the search box.
 * Searches through patient names and IDs, hiding non-matching entries instantly.
 * Also manages the visibility of a "no results" message when no patients match the search criteria.
 */
function initPatientSearch() {
    const searchInput = document.getElementById('patientSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const searchTerm = this.value.toLowerCase();
            const patientRows = document.querySelectorAll('.patient-row');
            patientRows.forEach(function (row) {
                const patientName = row.getAttribute('data-name').toLowerCase();
                const patientId = row.getAttribute('data-id').toLowerCase();
                if (patientName.includes(searchTerm) || patientId.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
            // Show/hide "no results" message
            const noResults = document.getElementById('noResults');
            if (noResults) {
                let visible = false;
                patientRows.forEach(function (row) {
                    if (row.style.display !== 'none') {
                        visible = true;
                    }
                });
                noResults.style.display = visible ? 'none' : '';
            }
        });
    }
}
/**
 * Initialize delete confirmation functionality.
 * 
 * Sets up event listeners on all patient delete buttons to show a confirmation dialog
 * before proceeding with deletion. This prevents accidental deletion of patient records
 * by requiring explicit user confirmation of the delete action.
 */
function initDeleteConfirmation() {
    const deleteButtons = document.querySelectorAll('.delete-patient');
    deleteButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            const patientId = this.getAttribute('data-id');
            const patientName = this.getAttribute('data-name');
            confirmAction(
                translateText('Delete Patient'),
                translateText('Are you sure you want to delete the patient? This action cannot be undone.'),
                function () {
                    // Submit the delete form
                    const form = document.getElementById(`deleteForm${patientId}`);
                    if (form) {
                        form.submit();
                    }
                }
            );
        });
    });
}
/**
 * Open the add note modal for a patient.
 * 
 * Configures and displays a Bootstrap modal dialog for adding a new clinical note
 * to a specific patient's record. Sets the appropriate form action URL, patient ID,
 * and modal title based on the patient being edited.
 * 
 * @param {number} patientId - The ID of the patient to add a note for
 * @param {string} patientName - The name of the patient (for display purposes)
 */
function openAddNoteModal(patientId, patientName) {
    const modal = document.getElementById('addNoteModal');
    if (modal) {
        const modalTitle = modal.querySelector('.modal-title');
        const patientIdField = document.getElementById('notePatientId');
        const form = document.getElementById('addNoteForm');
        modalTitle.textContent = translateText('Add note');
        if (patientIdField) {
            patientIdField.value = patientId;
        }
        if (form) {
            form.setAttribute('action', `/patients/${patientId}/notes`);
        }
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}
/**
 * Initialize the patient import functionality.
 * 
 * Sets up the UI and event handlers for importing existing patients using their UUID.
 * Configures the import modal, form submission process, and handles success/error states.
 * Allows doctors to import patients that were previously registered in the system
 * by another doctor by providing the patient's unique identifier.
 */
function initImportPatient() {
    const importBtn = document.getElementById('importPatientBtn');
    const importModal = document.getElementById('importPatientModal');
    const submitBtn = document.getElementById('importPatientSubmit');
    if (importBtn && importModal) {
        // Show the modal when the import button is clicked
        importBtn.addEventListener('click', function () {
            const modal = new bootstrap.Modal(importModal);
            modal.show();
        });
        // Handle form submission
        if (submitBtn) {
            submitBtn.addEventListener('click', function () {
                const uuidInput = document.getElementById('patientUUID');
                const errorDiv = document.getElementById('importPatientError');
                if (uuidInput.value.trim() === '') {
                    return;
                }
                // Clear previous errors
                if (errorDiv) {
                    errorDiv.style.display = 'none';
                }
                // Disable the submit button and show loading state
                submitBtn.disabled = true; submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>' +
                    translateText("Importing...");
                // Make the request to import the patient
                console.log("Sending import request", uuidInput.value.trim());
                fetch('/patients/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    credentials: 'same-origin',  // Include cookies
                    body: JSON.stringify({ patient_uuid: uuidInput.value.trim() })
                })
                    .then(response => {
                        if (!response.ok) {
                            return response.json().then(err => {
                                throw new Error(err.error || 'Errore durante l\'importazione del paziente');
                            });
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Reload the page on success to show the newly imported patient
                        window.location.reload();
                    })
                    .catch(error => {
                        console.error('Error importing patient:', error);
                        // Show error message
                        if (errorDiv) {
                            errorDiv.textContent = error.message || translateText("An error occurred while importing the patient. Please try again later.");
                            errorDiv.style.display = 'block';
                        }
                        // Reset button state
                        submitBtn.disabled = false; submitBtn.innerHTML = '<i class="fas fa-file-import me-1"></i>' +
                            translateText("Import Patient");
                    });
            });
        }
    }
}
