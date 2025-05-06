/**
 * Observations JavaScript
 * 
 * Manages the display and modification of vital parameter observations
 * 
 * Features:
 * - Loading observations for the current period
 * - Adding, editing and deleting observations
 * - Displaying observations in the UI
 */
/**
 * Global variables used throughout the observations management system.
 */
/**
 * Array containing all loaded observations for the current patient.
 * This cache is updated whenever observations are loaded, added, or deleted.
 * @type {Array}
 */
let currentObservations = [];
/**
 * Reference to the Bootstrap modal instance for observation management.
 * Used for adding new observations or confirming deletion of existing ones.
 * @type {bootstrap.Modal|null}
 */
let observationModal = null;
// We use the currentVitalType variable defined in vitals_charts.js
/**
 * Initialize observations management functionality.
 * 
 * Sets up event listeners for UI elements, initializes the observation modal,
 * and handles interactions for adding, editing, and deleting observations.
 * This function is called when the DOM is fully loaded, after charts are initialized.
 */
function initObservations() {
    console.log(translateText('Initializing observations management'));
    // Initialize observation modal
    observationModal = new bootstrap.Modal(document.getElementById('observationModal'));
    // Add event listener to add observation button
    const addObservationBtn = document.getElementById('addObservationBtn');
    if (addObservationBtn) {
        addObservationBtn.addEventListener('click', function() {
            openObservationModal();
        });
    }    // Handle form submission for adding
    const observationForm = document.getElementById('observationForm');
    if (observationForm) {
        observationForm.addEventListener('submit', function(event) {
            event.preventDefault();
            // Check which action to perform (add or delete)
            const action = document.getElementById('formAction').value;
            if (action === 'add') {
                submitAddObservation(this);
            }
        });
    }
    // Add event listener to delete button
    const deleteObservationBtn = document.getElementById('deleteObservationBtn');
    if (deleteObservationBtn) {
        deleteObservationBtn.addEventListener('click', function() {
            deleteObservation();
        });
    }
    // Add event listener to period change
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Observations will be reloaded when charts are reloaded
            setTimeout(loadObservations, 500);
        });
    });
    // Load initial observations
    loadObservations();
}
/**
 * Load all observations for the current patient.
 * 
 * Fetches all observations from the server API without applying period filters.
 * Displays loading indicators during the fetch operation and updates the UI
 * with the retrieved observations upon completion.
 * 
 * Note: This function loads ALL observations regardless of the selected time period,
 * and filtering by vital type is handled in the updateObservationsUI function.
 */
function loadObservations() {
    // Verify that currentVitalType variable is available (defined in vitals_charts.js)
    if (typeof currentVitalType === 'undefined') {
        console.error('The currentVitalType variable is not available');
        // We don't block execution, as loading should work anyway
    }
    const patientId = getPatientIdFromUrl();
    if (!patientId) {
        console.error('Unable to determine patient ID');
        updateObservationsUI([]);
        return;
    }
    // Show loading
    document.getElementById('observationsLoading').classList.remove('d-none');
    document.getElementById('noObservations').classList.add('d-none');
    document.getElementById('observationsList').classList.add('d-none');
    // Build API URL without date parameters
    // to retrieve ALL observations for the patient
    const apiUrl = `/web/observations/${patientId}`;
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(translateText('Error loading observations'));
            }
            return response.json();
        })
        .then(data => {
            console.log(translateText('Observations loaded:'), data);
            currentObservations = data;
            updateObservationsUI(data);
        })
        .catch(error => {
            console.error(translateText('Error loading observations') + ':', error);
            updateObservationsUI([]);
        });
}
/**
 * Update the interface with loaded observations.
 * 
 * Filters observations based on the currently selected vital parameter type,
 * groups them by type, and creates UI elements to display them. Handles empty
 * states and shows appropriate messages when no observations are available.
 * 
 * @param {Array} observations Array of observations to display
 */
function updateObservationsUI(observations) {
    // Hide loading
    document.getElementById('observationsLoading').classList.add('d-none');
    // Ensure observations is an array
    if (!Array.isArray(observations)) {
        console.error(translateText('updateObservationsUI: observations is not an array'), observations);
        observations = [];
    }
    // Container for observations list
    const observationsList = document.getElementById('observationsList');
    // Filter observations based on currently selected vital parameter type
    let filteredObservations = observations;
    try {
        if (typeof currentVitalType !== 'undefined' && currentVitalType !== null) {
            console.log(translateText("Current type:"), currentVitalType, typeof currentVitalType);
            // Extract vital parameter type ID (handle both string and object)
            let vitalTypeId;
            if (typeof currentVitalType === 'string') {
                vitalTypeId = currentVitalType.toLowerCase();
            } else if (typeof currentVitalType === 'object' && currentVitalType !== null) {
                vitalTypeId = currentVitalType.id ? currentVitalType.id.toLowerCase() : '';
            } else {
                vitalTypeId = '';
            }
            if (vitalTypeId) {
                filteredObservations = observations.filter(obs => obs.vital_type === vitalTypeId);
                console.log(translateText(`Showing only observations for type: ${vitalTypeId}`));
            }
        }
    } catch (error) {
        console.error('Error filtering observations:', error);
        // In case of error, show all observations
        filteredObservations = observations;
    }
    if (filteredObservations.length === 0) {
        // Show no observations message
        document.getElementById('noObservations').classList.remove('d-none');
        observationsList.classList.add('d-none');
        return;
    }
    // Show observations list
    document.getElementById('noObservations').classList.add('d-none');
    observationsList.classList.remove('d-none');
    // Empty the list
    observationsList.innerHTML = '';
    // Group observations by type
    const groupedObservations = {};
    filteredObservations.forEach(obs => {
        if (!groupedObservations[obs.vital_type]) {
            groupedObservations[obs.vital_type] = [];
        }
        groupedObservations[obs.vital_type].push(obs);
    });
    // Create UI elements for each observation group
    for (const type in groupedObservations) {
        const typeObservations = groupedObservations[type];
        // Find the information about the type
        let typeName = type.replace('_', ' ');
        let typeColor = '#007bff'; // Default blue
        // Search in the definitions of supported types
        for (const platform in SUPPORTED_DATA_TYPES) {
            const supportedTypes = SUPPORTED_DATA_TYPES[platform];
            const typeInfo = supportedTypes.find(t => t.id === type);
            if (typeInfo) {
                typeName = typeInfo.name;
                typeColor = typeInfo.color;
                break;
            }
        }
        // Create the observations group
        const observationGroup = document.createElement('div');
        observationGroup.className = 'card mb-3';
        observationGroup.innerHTML = `
            <div class="card-header" style="background-color: ${typeColor}20;">
                <h6 class="mb-0" style="color: ${typeColor};">
                    <i class="fas fa-clipboard-list me-2"></i> ${typeName}
                </h6>
            </div>
            <div class="card-body p-0">
                <ul class="list-group list-group-flush observation-list" data-type="${type}"></ul>
            </div>
        `;            // Add the individual observations to the list
        const observationList = observationGroup.querySelector('.observation-list');        typeObservations.forEach(obs => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.setAttribute('data-id', obs.id);
            // Format the dates
            const startDate = new Date(obs.start_date);
            const endDate = new Date(obs.end_date);
            const dateStr = `${formatDateForDisplay(startDate)} - ${formatDateForDisplay(endDate)}`;            // Check if the observation belongs to the current doctor
            let isCurrentDoctorObservation = false;
              try {
                // Get the current doctor ID from the meta tag
                const currentDoctorIdElement = document.querySelector('meta[name="current-doctor-id"]');
                const currentDoctorId = currentDoctorIdElement ? parseInt(currentDoctorIdElement.getAttribute('content')) : null;
                console.log('Checking property:', obs.id, '- Current doctor:', currentDoctorId, '- Observation doctor:', obs.doctor_id);
                // Convert both IDs to integers to make a consistent comparison
                // If both IDs are available, compare them
                if (currentDoctorId && obs.doctor_id) {
                    const doctorIdFromObs = parseInt(obs.doctor_id);
                    isCurrentDoctorObservation = doctorIdFromObs === currentDoctorId;
                    console.log('ID comparison:', doctorIdFromObs, '===', currentDoctorId, '=', isCurrentDoctorObservation);
                } else {                    // If the IDs are missing, we always show the button to maintain existing functionality
                    // This is a fallback that ensures basic functionality is not blocked
                    isCurrentDoctorObservation = true;
                    console.log('Missing IDs, showing button for safety');
                }
            } catch (error) {
                // In case of error, we show the button to maintain functionality
                isCurrentDoctorObservation = true;
                console.error('Error checking observation owner:', error);
            }              // HTML with doctor name and delete button only if they are the owner
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="mb-1">${obs.content}</p>
                        <div class="d-flex align-items-center text-muted small">
                            <span class="me-3">
                                <i class="fas fa-calendar-alt me-1"></i> ${dateStr}
                            </span>
                            <span>
                                <i class="fas fa-user-md me-1"></i> ${obs.doctor_name || translateText('Unknown Doctor')}
                            </span>
                        </div>
                    </div>
                    ${isCurrentDoctorObservation ? 
                      `<button class="btn btn-sm btn-outline-danger delete-observation-btn">
                         <i class="fas fa-trash-alt"></i>
                       </button>` : ''}
                </div>
            `;
            // Add event listener to the delete button only if it exists
            const deleteBtn = item.querySelector('.delete-observation-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', function() {
                    openObservationModal(obs);
                });
            }
            observationList.appendChild(item);
        });
        observationsList.appendChild(observationGroup);
    }
}
/**
 * Opens modal to add a new observation or delete an existing one.
 * 
 * Configures the modal based on the context - either for creating a new observation
 * or confirming deletion of an existing one. Sets up form fields, populates type options,
 * and configures default dates based on the current period.
 * 
 * @param {Object|null} observation - Existing observation for deletion, or null for adding new
 */
function openObservationModal(observation = null) {
    // UI elements
    const modalTitle = document.getElementById('observationModalLabel');
    const addContent = document.getElementById('addObservationContent');
    const deleteContent = document.getElementById('deleteObservationContent');
    const form = document.getElementById('observationForm');
    const formAction = document.getElementById('formAction');
    const addObs = document.getElementById('modal-footer-add');
    const delObs = document.getElementById('modal-footer-delete');
    const observationIdInput = document.getElementById('observationId');
    if (observation) {
        // If it's an existing observation, show deletion confirmation
        modalTitle.textContent = translateText('Delete observation');
        // Setup for deletion
        formAction.value = 'delete';
        addObs.classList.add('d-none');
        delObs.classList.remove('d-none');
        // Show deletion content and hide add form
        addContent.classList.add('d-none');
        deleteContent.classList.remove('d-none');
        // Prepare deletion content
        if (deleteContent) {
            // Ensure container is visible
            deleteContent.classList.remove('d-none');
            // Clear previous content and insert new message
            deleteContent.innerHTML = `
                <div>
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>${translateText('Warning')}</strong>: ${translateText('Are you sure you want to delete this observation?')}
                </div>
            `;
        }
        // Save observation ID
        if (observationIdInput) {
            observationIdInput.value = observation.id;
        }
    } else {
        // If it's a new observation
        modalTitle.textContent = translateText('Add observation');
        // Setup for addition
        formAction.value = 'add';
        delObs.classList.add('d-none');
        addObs.classList.remove('d-none');
        // Show add form and hide deletion content
        addContent.classList.remove('d-none');
        deleteContent.classList.add('d-none');
        // Reset form
        if (form) {
            form.reset();
        }
        // Populate options for available vital types
        populateVitalTypeOptions();
        // Default dates based on current period
        const startDateInput = document.getElementById('observationStartDate');
        const endDateInput = document.getElementById('observationEndDate');
        if (startDateInput && endDateInput) {
            const endDate = new Date();
            const startDate = new Date();
            // Use current period if available, otherwise use 7 days as default
            const period = (typeof currentPeriod !== 'undefined' && currentPeriod) ? currentPeriod : 7;
            startDate.setDate(startDate.getDate() - period);
            startDateInput.value = formatDateForInput(startDate);
            endDateInput.value = formatDateForInput(endDate);
        }// Automatically select the current vital parameter type
        try {
            if (typeof currentVitalType !== 'undefined' && currentVitalType !== null) {
                const typeSelect = document.getElementById('observationType');
                if (typeSelect) {
                    // Extract vital type ID (handle both string and object)
                    let vitalTypeId;
                    if (typeof currentVitalType === 'string') {
                        vitalTypeId = currentVitalType.toLowerCase();
                    } else if (typeof currentVitalType === 'object' && currentVitalType !== null) {
                        vitalTypeId = currentVitalType.id ? currentVitalType.id.toLowerCase() : '';
                    } else {
                        vitalTypeId = '';
                    }
                    if (vitalTypeId) {
                        typeSelect.value = vitalTypeId;
                    }
                }
            }
        } catch (error) {
            console.error(translateText('Error selecting vital type') + ':', error);
            // In case of error, don't set any default value
        }
    }
    // Show the modal
    observationModal.show();
}
/**
 * Populate options for available vital types in the observation form.
 * 
 * Dynamically populates the vital type dropdown select with options based on 
 * the currently selected health platform (from vitals_charts.js). Handles errors
 * gracefully if platform information is not available.
 */
function populateVitalTypeOptions() {
    const typeSelect = document.getElementById('observationType');
    if (!typeSelect) return;
    // Clear existing options, except the first one (empty selection)
    while (typeSelect.options.length > 1) {
        typeSelect.remove(1);
    }
    try {
        // Add options for types supported by the current platform
        // Check that currentPlatform is defined (it might be defined in vitals_charts.js)
        if (typeof currentPlatform !== 'undefined' && currentPlatform && typeof SUPPORTED_DATA_TYPES !== 'undefined' && SUPPORTED_DATA_TYPES[currentPlatform.toUpperCase()]) {
            const types = SUPPORTED_DATA_TYPES[currentPlatform.toUpperCase()];
            types.forEach(type => {
                const option = document.createElement('option');
                option.value = type.id;
                option.textContent = type.name;
                typeSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error(translateText('Error populating options') + ':', error);
    }
}
/**
 * Submit the form to add a new observation.
 * 
 * Validates the form data, including custom validation for date ranges,
 * prepares the observation data object, and submits it to the server API.
 * Handles success and error states, showing appropriate feedback to the user.
 * 
 * @param {HTMLFormElement} form - The form element containing observation data
 */
function submitAddObservation(form) {
    if (!form) return;
    const errorDiv = document.getElementById('observationError');
    // Hide any previous error messages in the error div
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
      // Get values from the form
    const formData = new FormData(form);
    const vitalType = formData.get('vital_type');
    const content = formData.get('content');
    const startDate = formData.get('start_date');
    const endDate = formData.get('end_date');
    // Reset any previous custom validation messages
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.setCustomValidity('');
    });
      // Basic validation - we use HTML5 validation for these fields
    if (!vitalType || !content || !startDate || !endDate) {
        return;
    }// Verify that the start date is before the end date
    if (new Date(startDate) > new Date(endDate)) {
        // Get references to date fields
        const startDateInput = document.getElementById('observationStartDate');
        // Set custom validity on end date field
    startDateInput.setCustomValidity(translateText("Start date must be before end date"));
        // Force display of error message
        startDateInput.reportValidity();
        // Add listener to clear error when value changes
        startDateInput.addEventListener('input', function() {
            this.setCustomValidity('');
            const today = new Date();
            const isoToday = today.toISOString().split('T')[0];
            observationStartDate.max = isoToday;
            observationEndDate.max = isoToday;
        }, { once: true });
        return;
    }
    // Add patient ID to the data
    const patientId = PATIENT_ID || getPatientIdFromUrl();
    const observationData = {
        patient_id: patientId,
        vital_type: vitalType.toLowerCase(),
        content: content,
        start_date: startDate,
        end_date: endDate
    };
    // URL for the API request
    const apiUrl = `/web/observations`;
    console.log(translateText('Sending observation:'), observationData);
    // API call
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(observationData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(translateText('Error saving observation. Please try again later.'));
        }
        return response.json();
    })
    .then(data => {
        console.log(translateText('Observation saved:'), data);
        // Close the modal
        observationModal.hide();
        // Show success message
        showAlert(translateText('Observation added successfully'), 'success');
        // Reload observations
        loadObservations();
    })
    .catch(error => {
        console.error('Error saving observation:', error);
        // Show the API error as a custom message visible at the top of the form
        const errorMessage = error.message || translateText("Error saving observation. Please try again later.");
        // Show the error at the top of the form
        if (errorDiv) {
            errorDiv.textContent = errorMessage;
            errorDiv.style.display = 'block';
            errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
            console.log(translateText('Showing API error:'), errorDiv.textContent);
        }
    });
}
/**
 * Delete an observation from the system.
 * 
 * Retrieves the observation ID from the form, sends a DELETE request to the server API,
 * and handles the server response. Updates the UI by removing the deleted observation
 * element upon successful deletion, or shows an error message if deletion fails.
 */
function deleteObservation() {
    // Get observation ID
    const id = document.getElementById('observationId').value;
    if (!id) return;
    // API URL (browser confirmation not needed anymore, we already have confirmation in the modal)
    const apiUrl = `/web/observations/${id}`;
    const errorDiv = document.getElementById('observationError');
    // Hide any previous error messages
    if (errorDiv) {
        errorDiv.textContent = '';
        errorDiv.style.display = 'none';
    }
    console.log(translateText('Deleting observation with ID:'), id);
    // API call
    fetch(apiUrl, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(translateText('Error deleting observation. Please try again later.'));
        }
        return response.json();
    })
    .then(data => {
        console.log(translateText('Observation deleted:'), data);
        // Close the modal
        observationModal.hide();
        // Show success message
        showAlert(translateText('Observation deleted successfully'), 'success');
        // Reload observations
        loadObservations();
    })
    .catch(error => {
        console.error('Error deleting observation:', error);
        if (errorDiv) {            errorDiv.textContent = error.message || translateText("Error deleting observation. Please try again later.");
            errorDiv.style.display = 'block';
            errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            showAlert(translateText('Error deleting observation. Please try again later.'), 'danger');
        }
    });
}
/**
 * Shows an alert message in the interface.
 * 
 * Creates a Bootstrap alert component with the specified message and styling.
 * The alert is inserted at the beginning of the main container or nearest container
 * and includes a close button. Similar to the showToast function but uses alerts 
 * instead of toasts for more prominent feedback.
 * 
 * @param {string} message - Message to display in the alert
 * @param {string} type - Alert type that determines styling (success, danger, warning, info)
 */
function showAlert(message, type = 'info') {
    // Create the alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    // Insert the alert in the same position as Flask flash messages (at the beginning of the main container)
    const mainContainer = document.querySelector('main.container');
    if (mainContainer) {
        // If an alert already exists, insert before it,
        // otherwise insert before the first element in the main container
        const existingAlert = mainContainer.querySelector('.alert');
        if (existingAlert) {
            mainContainer.insertBefore(alertDiv, existingAlert);
        } else {
            mainContainer.insertBefore(alertDiv, mainContainer.firstChild);
        }
    } else {
        // Fallback: use the standard container if main.container does not exist
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }
    }
    // Automatically remove after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}
/**
 * Formats a date for a date input
 * @param {Date} date Date to format
 * @returns {string} Formatted date YYYY-MM-DD
 */
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}
/**
 * Format a date object for API requests.
 * 
 * Converts a JavaScript Date object to a string in the ISO YYYY-MM-DD format
 * that the server API expects for date values. Currently uses formatDateForInput
 * since both formats are the same.
 * 
 * @param {Date} date - Date object to format
 * @returns {string} Date formatted as ISO YYYY-MM-DD string
 */
function formatDateForAPI(date) {
    return formatDateForInput(date);
}
/**
 * Format a date object for user-friendly display.
 * 
 * Converts a JavaScript Date object to a localized string in DD/MM/YYYY format,
 * which is more human-readable for display in the UI. This format is used in
 * observation lists and other UI elements.
 * 
 * @param {Date} date - Date object to format
 * @returns {string} Formatted date string in DD/MM/YYYY format
 */
function formatDateForDisplay(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
}
/**
 * Initialize observations functionality when the document is fully loaded.
 * 
 * Note: This event handler doesn't directly call initObservations() because
 * the initialization depends on charts being loaded first. The actual
 * initialization is called from vitals_charts.js after chart initialization.
 * 
 * @listens DOMContentLoaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialization will be called after charts are loaded
    // See vitals_charts.js
});