/**
 * Specific Report Form JavaScript
 * Handles UI interactions for patient-specific report generation form.
 */

/**
 * Initialize the specific report generator interface when the DOM is loaded.
 * 
 * This function handles all aspects of the patient-specific report form including:
 * - Processing URL parameters for pre-selecting vital types and periods
 * - Implementing "select all" functionality for notes, observations, and vital types
 * - Managing visual feedback for selected items with highlighting
 * - Setting up event listeners for select/deselect buttons
 * - Implementing client-side validation to ensure proper form submission
 * - Providing error notifications and visual cues for invalid selections
 * - Handling automatic scrolling to relevant sections
 * 
 * The form allows users to generate comprehensive reports that include:
 * 1. Selected clinical notes
 * 2. Clinical observations for specific vital parameters
 * 3. Charts and data visualizations for selected vital parameters and time periods
 * 
 * @listens DOMContentLoaded
 */
document.addEventListener('DOMContentLoaded', function () {
    // Check if there are URL parameters indicating a specific vital type
    const urlParams = new URLSearchParams(window.location.search);
    const vitalTypeParam = urlParams.get('vital_type');
    const periodParam = urlParams.get('period');
    const selectAllParam = urlParams.get('select_all');

    // If select_all parameter is present, select all data
    if (selectAllParam === 'true') {
        console.log('Automatic selection of all data activated');

        // Select all notes
        document.querySelectorAll('.note-checkbox').forEach(checkbox => {
            checkbox.checked = true;
            checkbox.closest('.form-check').classList.add('selected-item');
        });

        // Select all observations
        document.querySelectorAll('.observation-checkbox').forEach(checkbox => {
            checkbox.checked = true;
            checkbox.closest('.form-check').classList.add('selected-item');
        });

        // Select all vital types and periods
        document.querySelectorAll('.vital-type-checkbox').forEach(checkbox => {
            checkbox.checked = true;

            // Highlight vital type card
            const card = checkbox.closest('.vital-type-card');
            card.classList.add('selected');

            // Show options for periods
            const chartsSelection = card.querySelector('.charts-selection');
            if (chartsSelection) {
                chartsSelection.classList.remove('d-none');
            }

            // Select all periods for this vital type
            const vitalType = checkbox.value;
            document.querySelectorAll(`.period-checkbox[data-vital-type="${vitalType}"]`).forEach(periodCheckbox => {
                // If a period is specified, select only that one, otherwise select all
                if (periodParam) {
                    let periodValue;
                    switch (periodParam) {
                        case '1':
                            periodValue = '1d';
                            break;
                        case '7':
                            periodValue = '7d';
                            break;
                        case '30':
                            periodValue = '1m';
                            break;
                        case '90':
                            periodValue = '3m';
                            break;
                        default:
                            periodValue = '7d'; // Default to 7 days
                    }

                    if (periodCheckbox.value === periodValue) {
                        periodCheckbox.checked = true;
                    }
                } else {
                    // If no period is specified, select all
                    periodCheckbox.checked = true;
                }
            });
        });
    }

    // Show/hide charts selection when vital type is checked/unchecked
    const vitalTypeCheckboxes = document.querySelectorAll('.vital-type-checkbox');
    if (vitalTypeCheckboxes) {
        vitalTypeCheckboxes.forEach(checkbox => {
            // Check if this vital type matches the one in the URL
            // Only if select_all=true is not present
            if (!selectAllParam && vitalTypeParam && checkbox.value.toUpperCase() === vitalTypeParam.toUpperCase()) {
                checkbox.checked = true;
                // Highlight vital type card
                const card = checkbox.closest('.vital-type-card');
                card.classList.add('selected');

                // Show options for periods
                const chartsSelection = card.querySelector('.charts-selection');
                if (chartsSelection) {
                    chartsSelection.classList.remove('d-none');
                }

                // If a period parameter is also specified, select that one
                if (periodParam) {
                    let periodValue;
                    switch (periodParam) {
                        case '1':
                            periodValue = '1d';
                            break;
                        case '7':
                            periodValue = '7d';
                            break;
                        case '30':
                            periodValue = '1m';
                            break;
                        case '90':
                            periodValue = '3m';
                            break;
                        default:
                            periodValue = '7d'; // Default to 7 days
                    }

                    // Find and select the corresponding period checkbox
                    const periodCheckboxes = card.querySelectorAll(`.period-checkbox`);
                    periodCheckboxes.forEach(periodCheckbox => {
                        if (periodCheckbox.value === periodValue) {
                            periodCheckbox.checked = true;
                        }
                    });
                }

                // Auto-scroll to this section
                setTimeout(() => {
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 500);
            }

            // Add event listener to show/hide period options
            checkbox.addEventListener('change', function () {
                const card = this.closest('.vital-type-card');
                const chartsSelection = card.querySelector('.charts-selection');

                if (this.checked) {
                    chartsSelection.classList.remove('d-none');
                    card.classList.add('selected');
                } else {
                    chartsSelection.classList.add('d-none');
                    card.classList.remove('selected');
                    // Deselect all periods when the vital type is unchecked
                    card.querySelectorAll('.period-checkbox').forEach(periodCheckbox => {
                        periodCheckbox.checked = false;
                    });
                }
            });
        });
    }

    // Select/deselect all notes with visual feedback
    const selectAllNotesBtn = document.getElementById('selectAllNotes');
    if (selectAllNotesBtn) {
        selectAllNotesBtn.addEventListener('click', function () {
            document.querySelectorAll('.note-checkbox').forEach(checkbox => {
                checkbox.checked = true;
                checkbox.closest('.form-check').classList.add('selected-item');
            });
        });
    }

    const deselectAllNotesBtn = document.getElementById('deselectAllNotes');
    if (deselectAllNotesBtn) {
        deselectAllNotesBtn.addEventListener('click', function () {
            document.querySelectorAll('.note-checkbox').forEach(checkbox => {
                checkbox.checked = false;
                checkbox.closest('.form-check').classList.remove('selected-item');
            });
        });
    }

    // Add selection style to note checkboxes
    document.querySelectorAll('.note-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            if (this.checked) {
                this.closest('.form-check').classList.add('selected-item');
            } else {
                this.closest('.form-check').classList.remove('selected-item');
            }
        });
    });

    // Select/deselect all observations with visual feedback
    const selectAllObservationsBtn = document.getElementById('selectAllObservations');
    if (selectAllObservationsBtn) {
        selectAllObservationsBtn.addEventListener('click', function () {
            document.querySelectorAll('.observation-checkbox').forEach(checkbox => {
                checkbox.checked = true;
                checkbox.closest('.form-check').classList.add('selected-item');
            });
        });
    }

    const deselectAllObservationsBtn = document.getElementById('deselectAllObservations');
    if (deselectAllObservationsBtn) {
        deselectAllObservationsBtn.addEventListener('click', function () {
            document.querySelectorAll('.observation-checkbox').forEach(checkbox => {
                checkbox.checked = false;
                checkbox.closest('.form-check').classList.remove('selected-item');
            });
        });
    }

    // Add selection style to observation checkboxes
    document.querySelectorAll('.observation-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            if (this.checked) {
                this.closest('.form-check').classList.add('selected-item');
            } else {
                this.closest('.form-check').classList.remove('selected-item');
            }
        });
    });

    // Select/deselect all vital types
    const selectAllVitalTypesBtn = document.getElementById('selectAllVitalTypes');
    if (selectAllVitalTypesBtn) {
        selectAllVitalTypesBtn.addEventListener('click', function () {
            document.querySelectorAll('.vital-type-checkbox').forEach(checkbox => {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change'));
            });
        });
    }

    const deselectAllVitalTypesBtn = document.getElementById('deselectAllVitalTypes');
    if (deselectAllVitalTypesBtn) {
        deselectAllVitalTypesBtn.addEventListener('click', function () {
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
            button.addEventListener('click', function () {
                const vitalType = this.getAttribute('data-vital-type');
                document.querySelectorAll(`.period-checkbox[data-vital-type="${vitalType}"]`).forEach(checkbox => {
                    checkbox.checked = true;
                });
                // Hide error message if it was shown
                const periodError = this.closest('.charts-selection').querySelector('.period-error');
                if (periodError) {
                    periodError.classList.add('d-none');
                }
                // Remove red border if it was added
                const card = this.closest('.vital-type-card');
                if (card) {
                    card.classList.remove('border-danger');
                }
            });
        });
    }

    const deselectAllPeriodsButtons = document.querySelectorAll('.deselect-all-periods');
    if (deselectAllPeriodsButtons) {
        deselectAllPeriodsButtons.forEach(button => {
            button.addEventListener('click', function () {
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
        specificReportForm.addEventListener('submit', function (event) {
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
                const message = translateText('Please select at least one time period for each selected vital type');

                // Create a toast notification instead of alert
                const toastHtml = `
                        <div class="toast align-items-center bg-danger text-white border-0 fade show" role="alert" aria-live="assertive" aria-atomic="true">
                            <div class="d-flex">
                                <div class="toast-body">
                                    <i class="fas fa-exclamation-circle me-2"></i> ${message}
                                </div>
                                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                            </div>
                        </div>
                    `;

                // Create toast container if it doesn't exist
                let toastContainer = document.querySelector('.toast-container');
                if (!toastContainer) {
                    toastContainer = document.createElement('div');
                    toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
                    document.body.appendChild(toastContainer);
                }

                // Add toast to container
                toastContainer.innerHTML = toastHtml;

                // Initialize BS toast
                const toastEl = toastContainer.querySelector('.toast');
                const toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 5000 });
                toast.show();

                // Scroll to first error
                const firstErrorCard = document.querySelector('.vital-type-card.border-danger');
                if (firstErrorCard) {
                    firstErrorCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }
});