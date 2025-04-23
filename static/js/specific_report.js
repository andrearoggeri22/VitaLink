/**
 * Specific Report Form JavaScript
 * Handles the UI interactions for the specific report form.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Show/hide charts selection when vital type is checked/unchecked
    const vitalTypeCheckboxes = document.querySelectorAll('.vital-type-checkbox');
    if (vitalTypeCheckboxes) {
        vitalTypeCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const card = this.closest('.vital-type-card');
                const chartsSelection = card.querySelector('.charts-selection');
                
                if (this.checked) {
                    chartsSelection.classList.remove('d-none');
                } else {
                    chartsSelection.classList.add('d-none');
                    // Deselect all period checkboxes when vital type is deselected
                    card.querySelectorAll('.period-checkbox').forEach(periodCheckbox => {
                        periodCheckbox.checked = false;
                    });
                }
            });
        });
    }
    
    // Select/deselect all notes
    const selectAllNotesBtn = document.getElementById('selectAllNotes');
    if (selectAllNotesBtn) {
        selectAllNotesBtn.addEventListener('click', function() {
            document.querySelectorAll('.note-checkbox').forEach(checkbox => {
                checkbox.checked = true;
            });
        });
    }
    
    const deselectAllNotesBtn = document.getElementById('deselectAllNotes');
    if (deselectAllNotesBtn) {
        deselectAllNotesBtn.addEventListener('click', function() {
            document.querySelectorAll('.note-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
        });
    }
    
    // Select/deselect all observations
    const selectAllObservationsBtn = document.getElementById('selectAllObservations');
    if (selectAllObservationsBtn) {
        selectAllObservationsBtn.addEventListener('click', function() {
            document.querySelectorAll('.observation-checkbox').forEach(checkbox => {
                checkbox.checked = true;
            });
        });
    }
    
    const deselectAllObservationsBtn = document.getElementById('deselectAllObservations');
    if (deselectAllObservationsBtn) {
        deselectAllObservationsBtn.addEventListener('click', function() {
            document.querySelectorAll('.observation-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
        });
    }
    
    // Select/deselect all vital types
    const selectAllVitalTypesBtn = document.getElementById('selectAllVitalTypes');
    if (selectAllVitalTypesBtn) {
        selectAllVitalTypesBtn.addEventListener('click', function() {
            document.querySelectorAll('.vital-type-checkbox').forEach(checkbox => {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change'));
            });
        });
    }
    
    const deselectAllVitalTypesBtn = document.getElementById('deselectAllVitalTypes');
    if (deselectAllVitalTypesBtn) {
        deselectAllVitalTypesBtn.addEventListener('click', function() {
            document.querySelectorAll('.vital-type-checkbox').forEach(checkbox => {
                checkbox.checked = false;
                checkbox.dispatchEvent(new Event('change'));
            });
        });
    }
    
    // Select/deselect all time periods for a specific vital type
    const selectAllPeriodsButtons = document.querySelectorAll('.select-all-periods');
    if (selectAllPeriodsButtons) {
        selectAllPeriodsButtons.forEach(button => {
            button.addEventListener('click', function() {
                const vitalType = this.getAttribute('data-vital-type');
                document.querySelectorAll(`.period-checkbox[data-vital-type="${vitalType}"]`).forEach(checkbox => {
                    checkbox.checked = true;
                });
                // Hide error message if it was shown
                const periodError = this.closest('.charts-selection').querySelector('.period-error');
                if (periodError) {
                    periodError.classList.add('d-none');
                }
            });
        });
    }
    
    const deselectAllPeriodsButtons = document.querySelectorAll('.deselect-all-periods');
    if (deselectAllPeriodsButtons) {
        deselectAllPeriodsButtons.forEach(button => {
            button.addEventListener('click', function() {
                const vitalType = this.getAttribute('data-vital-type');
                document.querySelectorAll(`.period-checkbox[data-vital-type="${vitalType}"]`).forEach(checkbox => {
                    checkbox.checked = false;
                });
            });
        });
    }
    
    // Form validation before submission
    const specificReportForm = document.getElementById('specificReportForm');
    if (specificReportForm) {
        specificReportForm.addEventListener('submit', function(event) {
            let isValid = true;
            
            // Check that selected vital types have at least one time period selected
            document.querySelectorAll('.vital-type-checkbox:checked').forEach(checkbox => {
                const vitalType = checkbox.value;
                const periodCheckboxes = document.querySelectorAll(`.period-checkbox[data-vital-type="${vitalType}"]:checked`);
                
                if (periodCheckboxes.length === 0) {
                    // Show error message
                    const periodError = checkbox.closest('.vital-type-card').querySelector('.period-error');
                    if (periodError) {
                        periodError.classList.remove('d-none');
                    }
                    isValid = false;
                    
                    // Add red border to the card
                    checkbox.closest('.vital-type-card').classList.add('border-danger');
                } else {
                    // Hide error message if it was shown
                    const periodError = checkbox.closest('.vital-type-card').querySelector('.period-error');
                    if (periodError) {
                        periodError.classList.add('d-none');
                    }
                    
                    // Remove red border
                    checkbox.closest('.vital-type-card').classList.remove('border-danger');
                }
            });
            
            // Prevent form submission if validation fails
            if (!isValid) {
                event.preventDefault();
                // Get language from html lang attribute
                const lang = document.documentElement.lang || 'en';
                const message = lang === 'it' 
                    ? 'Seleziona almeno un periodo di tempo per ogni tipo di parametro vitale selezionato' 
                    : 'Please select at least one time period for each selected vital type';
                alert(message);
                window.scrollTo(0, 0);
            }
        });
    }
});