// main.js - Common JavaScript functions for the application

/**
 * Deletes a patient note with confirmation.
 * 
 * Displays a confirmation dialog before deleting the note, then sends a DELETE request 
 * to the server to remove the note. Updates the UI by removing the note element and
 * displaying a notification upon success.
 * 
 * @param {number} noteId - The ID of the note to delete
 * @param {number} patientId - The ID of the patient associated with the note
 */
function deleteNote(noteId, patientId) {
    let confirmMessage = translateText('Are you sure you want to delete this note? This action cannot be undone.');
    let confirmTitle = translateText('Confirm Deletion');
    let confirmButton = translateText('Delete');
    let cancelButton = translateText('Cancel');

    showConfirmationModal(confirmTitle, confirmMessage, confirmButton, cancelButton, function () {
        // Send DELETE request to delete the note
        fetch(`/notes/${noteId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to delete note');
                }
                return response.json();
            })
            .then(data => {
                // Remove the note from the DOM
                const noteElement = document.querySelector(`#note-${noteId}`);
                if (noteElement) {
                    noteElement.remove();
                }

                // Show success message
                showToast(data.message || 'Note deleted successfully', 'success');

                // If we're on the patient detail page, update the note count
                const noteCountElement = document.querySelector('#note-count');
                if (noteCountElement) {
                    const currentCount = parseInt(noteCountElement.textContent);
                    if (!isNaN(currentCount)) {
                        noteCountElement.textContent = (currentCount - 1).toString();
                    }
                }
            })
            .catch(error => {
                console.error('Error deleting note:', error);
                showToast('Error deleting note. Please try again.', 'danger');
            });
    });
}

/**
 * Initializes common UI components when the DOM is fully loaded.
 * 
 * Sets up Bootstrap components (tooltips, popovers), configures automatic dismissal
 * of alert messages, adds confirmation dialogs to delete buttons, and initializes
 * datetime inputs with the current date and time.
 * 
 * @listens DOMContentLoaded
 */
document.addEventListener('DOMContentLoaded', function () {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Handle alerts dismissal after 5 seconds
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add confirmation to delete buttons
    const deleteButtons = document.querySelectorAll('.delete-confirm');
    deleteButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            let confirmMessage = translateText('Are you sure you want to delete this item? This action cannot be undone.');

            if (!confirm(confirmMessage)) {
                event.preventDefault();
            }
        });
    });

    // Format date-time inputs to local timezone
    const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    datetimeInputs.forEach(function (input) {
        if (!input.value) {
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');

            input.value = `${year}-${month}-${day}T${hours}:${minutes}`;
        }
    });
});

/**
 * Formats a date string for display in the UI.
 * 
 * Converts an ISO date string to a localized date format based on the current
 * application language (English or Italian). Can optionally include time information
 * in the formatted output.
 * 
 * @param {string} dateString - ISO date string to format
 * @param {boolean} includeTime - Whether to include time in the formatted date (default: true)
 * @returns {string} Formatted date string suitable for display in the UI
 */
function formatDate(dateString, includeTime = true) {
    if (!dateString) return '';

    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };

    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }

    // Use the current language from HTML lang attribute, default to 'en-US'
    const language = document.documentElement.lang || 'en';
    const locale = language === 'it' ? 'it-IT' : 'en-US';

    return date.toLocaleDateString(locale, options);
}

/**
 * Generates a random color in HSL format.
 * 
 * Creates visually pleasing colors with random hue but fixed saturation and lightness
 * values, suitable for charts, UI elements, and data visualizations that need 
 * distinct but harmonious colors.
 * 
 * @returns {string} HSL color string in the format "hsl(hue, 70%, 50%)"
 */
function getRandomColor() {
    const hue = Math.floor(Math.random() * 360);
    return `hsl(${hue}, 70%, 50%)`;
}

/**
 * Displays a toast notification to provide feedback to the user.
 * 
 * Creates a Bootstrap toast element with appropriate styling based on the message type.
 * The toast appears in the bottom-right corner of the screen and automatically dismisses
 * after 5 seconds. Dynamically creates the toast container if it doesn't already exist.
 * 
 * @param {string} message - The message to display in the toast
 * @param {string} type - Toast type that determines styling (success, danger, warning, info)
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');

    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    // Set toast content
    const bgColor = type === 'danger' ? 'bg-danger' :
        type === 'success' ? 'bg-success' :
            type === 'warning' ? 'bg-warning' : 'bg-info';

    toast.innerHTML = `
        <div class="toast-header ${bgColor} text-white">
            <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    // Add toast to container
    toastContainer.appendChild(toast);

    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 5000 });
    bsToast.show();

    // Remove toast from DOM after it's hidden
    toast.addEventListener('hidden.bs.toast', function () {
        toast.remove();
    });
}

/**
 * Displays a customizable confirmation modal dialog.
 * 
 * Creates a Bootstrap modal dialog that prompts the user to confirm an action.
 * The dialog includes a title, message, and customizable button text for both
 * the confirm and cancel buttons. When the user confirms, executes the provided
 * callback function.
 * 
 * @param {string} title - The title to display in the modal header
 * @param {string} message - The message to display in the modal body
 * @param {string} confirmButtonText - Text to display on the confirm button
 * @param {string} cancelButtonText - Text to display on the cancel button
 * @param {Function} onConfirm - Callback function to execute when the user confirms
 */
function showConfirmationModal(title, message, confirmButtonText, cancelButtonText, onConfirm) {
    // Check if a modal already exists
    let modal = document.getElementById('confirmModal');

    if (!modal) {
        // Create modal element
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'confirmModal';
        modal.tabIndex = '-1';
        modal.setAttribute('aria-labelledby', 'confirmModalLabel');
        modal.setAttribute('aria-hidden', 'true');

        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="confirmModalLabel">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        ${message}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${cancelButtonText}</button>
                        <button type="button" class="btn btn-danger" id="confirmButton">${confirmButtonText}</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    } else {
        // Update existing modal
        modal.querySelector('.modal-title').textContent = title;
        modal.querySelector('.modal-body').textContent = message;
        modal.querySelector('.modal-footer .btn-secondary').textContent = cancelButtonText;
        modal.querySelector('#confirmButton').textContent = confirmButtonText;
    }

    // Initialize Bootstrap modal
    const modalInstance = new bootstrap.Modal(modal);

    // Set up confirm button action
    const confirmButton = document.getElementById('confirmButton');

    // Remove any existing event listeners
    const newConfirmButton = confirmButton.cloneNode(true);
    confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);

    // Add new event listener
    newConfirmButton.addEventListener('click', function () {
        modalInstance.hide();
        onConfirm();
    });

    // Show the modal
    modalInstance.show();
}

/**
 * Creates a simpler confirmation modal dialog.
 * 
 * A streamlined version of showConfirmationModal with fewer parameters, using
 * default text for buttons. Creates a Bootstrap modal with warning styling,
 * including an exclamation icon. Used for simple confirmation scenarios where
 * customized button text is not required.
 * 
 * @param {string} title - The title to display in the modal header
 * @param {string} message - The message to display in the modal body
 * @param {Function} onConfirm - Callback function to execute when the user confirms
 */
function confirmAction(title, message, onConfirm) {
    // Check if a modal already exists
    let modal = document.getElementById('confirmModal');

    if (!modal) {
        // Create modal element
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'confirmModal';
        modal.tabIndex = '-1';
        modal.setAttribute('aria-labelledby', 'confirmModalLabel');
        modal.setAttribute('aria-hidden', 'true');

        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="confirmModalLabel">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                    <div class="mb-1">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                ${message}
                            </div>
                        
                    </div>
                    <div class="modal-footer">                        
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${translateText('Cancel')}</button>
                        <button type="button" class="btn btn-danger" id="confirmButton">${translateText('Confirm')}</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    } else {
        // Update existing modal
        modal.querySelector('.modal-title').textContent = title;
        modal.querySelector('.modal-body').textContent = message;
    }

    // Initialize Bootstrap modal
    const modalInstance = new bootstrap.Modal(modal);

    // Set up confirm button action
    const confirmButton = document.getElementById('confirmButton');

    // Remove any existing event listeners
    const newConfirmButton = confirmButton.cloneNode(true);
    confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);

    // Add new event listener
    newConfirmButton.addEventListener('click', function () {
        modalInstance.hide();
        onConfirm();
    });

    // Show the modal
    modalInstance.show();
}
