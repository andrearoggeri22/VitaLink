// patients.js - JavaScript for patient-related functionality

document.addEventListener('DOMContentLoaded', function() {
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
 * Initialize patient form functionality
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
        patientForm.addEventListener('submit', function(event) {
            if (!patientForm.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            patientForm.classList.add('was-validated');
        });
    }
}

/**
 * Initialize patient search functionality
 */
function initPatientSearch() {
    const searchInput = document.getElementById('patientSearch');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const patientRows = document.querySelectorAll('.patient-row');
            
            patientRows.forEach(function(row) {
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
                patientRows.forEach(function(row) {
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
 * Initialize delete confirmation functionality
 */
function initDeleteConfirmation() {
    const deleteButtons = document.querySelectorAll('.delete-patient');
    
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            const patientId = this.getAttribute('data-id');
            const patientName = this.getAttribute('data-name');
            
            confirmAction(
                document.documentElement.lang === "it" ? "Elimina paziente" : 'Delete Patient',
                document.documentElement.lang === "it" ? "Sei sicuro di voler eliminare il paziente? L'azione non può essere cancellata." : 'Are you sure you want to delete the patient? This action cannot be undone.',
                function() {
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
 * Open the add note modal for a patient
 * @param {number} patientId - The ID of the patient
 * @param {string} patientName - The name of the patient
 */
function openAddNoteModal(patientId, patientName) {
    const modal = document.getElementById('addNoteModal');
    
    if (modal) {
        const modalTitle = modal.querySelector('.modal-title');
        const patientIdField = document.getElementById('notePatientId');
        const form = document.getElementById('addNoteForm');
        
        modalTitle.textContent = document.documentElement.lang === "it" ? "Aggiungi nota" : 'Add note';
        
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
 * Initialize the import patient functionality
 */
function initImportPatient() {
    const importBtn = document.getElementById('importPatientBtn');
    const importModal = document.getElementById('importPatientModal');
    const submitBtn = document.getElementById('importPatientSubmit');
    
    if (importBtn && importModal) {
        // Show the modal when the import button is clicked
        importBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(importModal);
            modal.show();
        });
        
        // Handle form submission
        if (submitBtn) {
            submitBtn.addEventListener('click', function() {
                const uuidInput = document.getElementById('patientUUID');
                const errorDiv = document.getElementById('importPatientError');
                
                if (uuidInput.value.trim() === '') {
                    // Show error if the UUID is empty
                    if (errorDiv) {
                        errorDiv.textContent = document.documentElement.lang === "it" 
                            ? "Inserisci un UUID valido" 
                            : "Please enter a valid UUID";
                        errorDiv.style.display = 'block';
                    }
                    return;
                }
                
                // Clear previous errors
                if (errorDiv) {
                    errorDiv.style.display = 'none';
                }
                
                // Disable the submit button and show loading state
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>' + 
                                      (document.documentElement.lang === "it" ? "Importazione..." : "Importing...");
                
                // Make the request to import the patient
                fetch('/api/import_patient', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ uuid: uuidInput.value.trim() })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Reload the page on success to show the newly imported patient
                        window.location.reload();
                    } else {
                        // Show error message
                        if (errorDiv) {
                            errorDiv.textContent = data.message;
                            errorDiv.style.display = 'block';
                        }
                        
                        // Reset button state
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="fas fa-file-import me-1"></i>' + 
                                             (document.documentElement.lang === "it" ? "Importa Paziente" : "Import Patient");
                    }
                })
                .catch(error => {
                    console.error('Error importing patient:', error);
                    
                    // Show generic error message
                    if (errorDiv) {
                        errorDiv.textContent = document.documentElement.lang === "it"
                            ? "Si è verificato un errore durante l'importazione del paziente. Riprova più tardi."
                            : "An error occurred while importing the patient. Please try again later.";
                        errorDiv.style.display = 'block';
                    }
                    
                    // Reset button state
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-file-import me-1"></i>' + 
                                         (document.documentElement.lang === "it" ? "Importa Paziente" : "Import Patient");
                });
            });
        }
    }
}
