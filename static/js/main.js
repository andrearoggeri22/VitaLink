// main.js - Common JavaScript functions for the application

document.addEventListener('DOMContentLoaded', function() {
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
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add confirmation to delete buttons
    const deleteButtons = document.querySelectorAll('.delete-confirm');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                event.preventDefault();
            }
        });
    });

    // Format date-time inputs to local timezone
    const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    datetimeInputs.forEach(function(input) {
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
 * Format a date for display
 * @param {string} dateString - ISO date string
 * @param {boolean} includeTime - Whether to include time in the formatted date
 * @returns {string} Formatted date string
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
 * Generate a random color in HSL format with fixed saturation and lightness
 * @returns {string} HSL color string
 */
function getRandomColor() {
    const hue = Math.floor(Math.random() * 360);
    return `hsl(${hue}, 70%, 50%)`;
}

/**
 * Create confirmation modal
 * @param {string} title - Modal title
 * @param {string} message - Modal message
 * @param {Function} onConfirm - Callback function on confirmation
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
                        ${message}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${cancelButtonText || 'Cancel'}</button>
                        <button type="button" class="btn btn-danger" id="confirmButton">${confirmButtonText || 'Confirm'}</button>
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
    newConfirmButton.addEventListener('click', function() {
        modalInstance.hide();
        onConfirm();
    });
    
    // Show the modal
    modalInstance.show();
}
