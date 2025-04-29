/**
 * Specific Report Form JavaScript
 * Gestisce le interazioni UI per il form di generazione dei report specifici per pazienti.
 */
document.addEventListener('DOMContentLoaded', function () {
    // Controlla se ci sono parametri nell'URL che indicano un tipo vitale specifico
    const urlParams = new URLSearchParams(window.location.search);
    const vitalTypeParam = urlParams.get('vital_type');
    const periodParam = urlParams.get('period');
    const selectAllParam = urlParams.get('select_all');

    // Se è presente il parametro select_all, seleziona tutti i dati
    if (selectAllParam === 'true') {
        console.log('Selezione automatica di tutti i dati attivata');

        // Seleziona tutte le note
        document.querySelectorAll('.note-checkbox').forEach(checkbox => {
            checkbox.checked = true;
            checkbox.closest('.form-check').classList.add('selected-item');
        });

        // Seleziona tutte le osservazioni
        document.querySelectorAll('.observation-checkbox').forEach(checkbox => {
            checkbox.checked = true;
            checkbox.closest('.form-check').classList.add('selected-item');
        });

        // Seleziona tutti i tipi vitali e periodi
        document.querySelectorAll('.vital-type-checkbox').forEach(checkbox => {
            checkbox.checked = true;

            // Evidenzia la card del tipo vitale
            const card = checkbox.closest('.vital-type-card');
            card.classList.add('selected');

            // Mostra le opzioni per i periodi
            const chartsSelection = card.querySelector('.charts-selection');
            if (chartsSelection) {
                chartsSelection.classList.remove('d-none');
            }

            // Seleziona tutti i periodi per questo tipo vitale
            const vitalType = checkbox.value;
            document.querySelectorAll(`.period-checkbox[data-vital-type="${vitalType}"]`).forEach(periodCheckbox => {
                // Se è specificato un periodo, seleziona solo quello, altrimenti seleziona tutti
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
                            periodValue = '7d'; // Default a 7 giorni
                    }

                    if (periodCheckbox.value === periodValue) {
                        periodCheckbox.checked = true;
                    }
                } else {
                    // Se non è specificato un periodo, seleziona tutti
                    periodCheckbox.checked = true;
                }
            });
        });
    }

    // Show/hide charts selection when vital type is checked/unchecked
    const vitalTypeCheckboxes = document.querySelectorAll('.vital-type-checkbox');
    if (vitalTypeCheckboxes) {
        vitalTypeCheckboxes.forEach(checkbox => {
            // Controllo se questo tipo vitale corrisponde a quello nell'URL
            // Solo se non è presente select_all=true
            if (!selectAllParam && vitalTypeParam && checkbox.value.toUpperCase() === vitalTypeParam.toUpperCase()) {
                checkbox.checked = true;
                // Evidenzia la card del tipo vitale
                const card = checkbox.closest('.vital-type-card');
                card.classList.add('selected');

                // Mostra le opzioni per i periodi
                const chartsSelection = card.querySelector('.charts-selection');
                if (chartsSelection) {
                    chartsSelection.classList.remove('d-none');
                }

                // Se è specificato anche un parametro di periodo, seleziona quello
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
                            periodValue = '7d'; // Default a 7 giorni
                    }

                    // Cerca e seleziona il checkbox del periodo corrispondente
                    const periodCheckboxes = card.querySelectorAll(`.period-checkbox`);
                    periodCheckboxes.forEach(periodCheckbox => {
                        if (periodCheckbox.value === periodValue) {
                            periodCheckbox.checked = true;
                        }
                    });
                }

                // Scorri automaticamente a questa sezione
                setTimeout(() => {
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 500);
            }

            // Aggiungi event listener per mostrare/nascondere le opzioni dei periodi
            checkbox.addEventListener('change', function () {
                const card = this.closest('.vital-type-card');
                const chartsSelection = card.querySelector('.charts-selection');

                if (this.checked) {
                    chartsSelection.classList.remove('d-none');
                    card.classList.add('selected');
                } else {
                    chartsSelection.classList.add('d-none');
                    card.classList.remove('selected');
                    // Deseleziona tutti i periodi quando si deseleziona il tipo vitale
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
                // Get language from html lang attribute
                const lang = document.documentElement.lang || 'en';
                const message = lang === 'it'
                    ? 'Seleziona almeno un periodo di tempo per ogni tipo di parametro vitale selezionato'
                    : 'Please select at least one time period for each selected vital type';

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