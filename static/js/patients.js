// patients.js - JavaScript for patient-related functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the new patient form or edit patient form
    initPatientForm();
    
    // Set up search functionality
    initPatientSearch();
    
    // Set up delete patient confirmation
    initDeleteConfirmation();
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
                window.deletePatientTitle || 'Delete Patient',
                window.deletePatientMessage ? window.deletePatientMessage.replace('{name}', patientName) : `Are you sure you want to delete the patient ${patientName}? This action cannot be undone.`,
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
        
        modalTitle.textContent = window.addNoteForText ? window.addNoteForText.replace('{name}', patientName) : `Add Note for ${patientName}`;
        
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
