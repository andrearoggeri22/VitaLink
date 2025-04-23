/**
 * Health platform connection management for patient detail page
 */

// Global variables
let syncButton = null;
let syncModal = null;
let platformButtons = null;
let connectionStatusElem = null;

// Constants
const PLATFORMS = {
    FITBIT: 'fitbit',
    GOOGLE_FIT: 'google_fit',
    APPLE_HEALTH: 'apple_health'
};

// Cache for API data
let apiDataCache = {};
const CACHE_EXPIRY_MS = 10 * 60 * 1000; // 10 minutes

/**
 * Initialize the health platforms integration on patient detail page
 */
function initializeHealthPlatform() {
    console.log('Initializing health platform...');
    
    // Initialize DOM references
    syncButton = document.getElementById('syncHealthBtn');
    console.log('Sync button found:', syncButton !== null);
    
    // Initialize connection details section
    const connectionDetails = document.getElementById('connectionDetails');
    if (connectionDetails) {
        console.log('Connection details section found');
        // Get the patient ID from the URL
        const patientId = getPatientIdFromUrl();
        if (patientId) {
            console.log('Patient ID:', patientId);
            loadConnectionDetails(patientId);
        } else {
            console.error('Could not determine patient ID from URL');
            showConnectionError();
        }
    } else {
        console.log('Connection details section not found');
    }
    
    // Add event listener to sync button if it exists
    if (syncButton) {
        console.log('Adding click event listener to sync button');
        // Rimuovi prima eventuali listener precedenti per evitare duplicazioni
        syncButton.removeEventListener('click', handleSyncButtonClick);
        syncButton.addEventListener('click', handleSyncButtonClick);
        
        // Aggiunge anche un handler diretto per assicurarci che funzioni
        syncButton.onclick = function() {
            console.log('Direct click handler triggered');
            handleSyncButtonClick();
        };
    } else {
        console.error('Sync button not found, cannot add event listener');
    }
}

/**
 * Load connection details for the patient
 * @param {number} patientId The patient ID
 */
function loadConnectionDetails(patientId) {
    // Show loading state
    document.getElementById('connectionLoading').classList.remove('d-none');
    document.getElementById('connectionActive').classList.add('d-none');
    document.getElementById('connectionInactive').classList.add('d-none');
    
    // Make API request to check connection status
    fetch(`/health/check_connection/${patientId}`)
    .then(response => response.json())
    .then(data => {
        // Hide loading state
        document.getElementById('connectionLoading').classList.add('d-none');
        
        if (data.connected) {
            // Show active connection section
            document.getElementById('connectionActive').classList.remove('d-none');
            
            // Update UI with connection details
            updateConnectionDetails(data);
            
            // Update button state
            updateButtonToDisconnect(data.platform);
        } else {
            // Show inactive connection section
            document.getElementById('connectionInactive').classList.remove('d-none');
            
            // Update button state
            updateButtonToConnect();
        }
    })
    .catch(error => {
        console.error('Error loading connection details:', error);
        showConnectionError();
    });
}

/**
 * Update connection details in the UI
 * @param {Object} data Connection data from API
 */
function updateConnectionDetails(data) {
    // Format the platform name
    const platformName = document.getElementById('platformName');
    if (platformName) {
        let formattedName = data.platform || '';
        
        // Format special platform names
        if (formattedName === 'fitbit') {
            formattedName = 'Fitbit';
        } else if (formattedName === 'google_fit') {
            formattedName = 'Google Fit';
        } else if (formattedName === 'apple_health') {
            formattedName = 'Apple Health';
        } else {
            // Capitalize first letter of other platforms
            formattedName = formattedName.charAt(0).toUpperCase() + formattedName.slice(1);
        }
        
        platformName.textContent = formattedName;
    }
    
    // Format connection date
    const connectionDate = document.getElementById('connectionDate');
    if (connectionDate && data.connected_since) {
        const date = new Date(data.connected_since);
        connectionDate.textContent = formatDateTime(date);
    }
    
    // Format expiration date
    const expirationDate = document.getElementById('expirationDate');
    if (expirationDate && data.token_expires_at) {
        const date = new Date(data.token_expires_at);
        expirationDate.textContent = formatDateTime(date);
    }
}

/**
 * Show connection error in the UI
 */
function showConnectionError() {
    // Hide loading state
    document.getElementById('connectionLoading').classList.add('d-none');
    
    // Show inactive connection with error
    document.getElementById('connectionInactive').classList.remove('d-none');
    
    // Update button state
    updateButtonToConnect();
}

/**
 * Handle the click on the Sync button
 * This handles both connection and disconnection based on the current state
 */
function handleSyncButtonClick() {
    console.log('Health Sync button clicked');
    // Get the patient ID from the URL
    const patientId = getPatientIdFromUrl();
    if (!patientId) {
        console.error('Could not determine patient ID');
        return;
    }
    
    console.log('Patient ID from URL:', patientId);
    
    // Check if we're connected or not
    const isConnected = syncButton.getAttribute('data-connected') === 'true';
    console.log('Is connected:', isConnected);
    
    if (isConnected) {
        // Handle disconnection
        const platform = syncButton.getAttribute('data-platform');
        console.log('Disconnecting from platform:', platform);
        disconnectHealthPlatform(patientId, platform);
    } else {
        // Handle connection - show platform selection modal
        console.log('Creating health platform modal');
        createHealthPlatformModal(patientId);
    }
}

/**
 * Update button to show "Disconnetti" text and styling
 * @param {string} platform Platform name
 */
function updateButtonToDisconnect(platform) {
    if (syncButton) {
        syncButton.innerHTML = `<i class="fas fa-unlink me-1"></i> ${translateText('Disconnect')}`;
        syncButton.classList.remove('btn-info', 'btn-lg');
        syncButton.classList.add('btn-danger');
        syncButton.setAttribute('data-connected', 'true');
        syncButton.setAttribute('data-platform', platform);
    }
}

/**
 * Update button to show "Health Sync" text and styling
 */
function updateButtonToConnect() {
    if (syncButton) {
        syncButton.innerHTML = `<i class="fas fa-sync me-1"></i> ${translateText('Health Sync')}`;
        syncButton.classList.remove('btn-danger');
        syncButton.classList.add('btn-info', 'btn-lg');
        syncButton.setAttribute('data-connected', 'false');
        syncButton.removeAttribute('data-platform');
    }
}

/**
 * Create a modal dialog for selecting a health platform
 * @param {number} patientId The patient ID
 */
function createHealthPlatformModal(patientId) {
    console.log('Creating health platform modal, patient ID:', patientId);
    
    // Prima verifichiamo se jQuery è disponibile
    if (typeof $ === 'undefined') {
        console.error('jQuery non è disponibile. Impossibile creare il modal.');
        alert('Errore: jQuery non disponibile. Impossibile visualizzare il popup.');
        return;
    }
    
    console.log('jQuery is available, creating jQuery modal');
    
    // Rimuovi il modal esistente se presente
    $('#healthPlatformModal').remove();
    
    // Crea l'HTML del modal e aggiungilo alla pagina
    const modalHtml = `
        <div class="modal" id="healthPlatformModal" tabindex="-1" role="dialog">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-link me-2"></i> ${translateText('Connect Health Platform')}
                        </h5>
                        <button type="button" class="btn-close" data-dismiss="modal" aria-label="${translateText('Close')}"></button>
                    </div>
                    <div class="modal-body">
                        <p>${translateText('Choose a health platform to connect:')}</p>
                        <div id="platformOptions" class="d-grid gap-2">
                            <button class="btn btn-outline-primary platform-btn" data-platform="${PLATFORMS.FITBIT}">
                                <i class="fas fa-heartbeat me-2"></i> Fitbit
                            </button>
                        </div>
                        <div id="connectionStatus" class="alert mt-3 d-none"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">
                            ${translateText('Cancel')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Aggiungi il modal al DOM
    $('body').append(modalHtml);
    
    // Salva il riferimento all'elemento del modal
    const $modal = $('#healthPlatformModal');
    
    // Aggiungi event listener ai pulsanti delle piattaforme
    $('.platform-btn').on('click', function() {
        const platform = $(this).data('platform');
        console.log('Platform button clicked:', platform);
        createHealthPlatformLink(patientId, platform);
    });
    
    // Salva il riferimento all'elemento dello stato della connessione
    connectionStatusElem = document.getElementById('connectionStatus');
    
    // Gestisci la chiusura del modal con il pulsante Close
    $('.btn-close, button[data-dismiss="modal"]').on('click', function() {
        $modal.hide();
    });
    
    // Visualizza il modal
    console.log('Showing modal');
    $modal.css({
        'display': 'block',
        'background-color': 'rgba(0,0,0,0.5)',
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'width': '100%',
        'height': '100%',
        'z-index': 1050
    });
    
    // Posiziona il dialogo al centro
    $('.modal-dialog').css({
        'margin': '10% auto',
        'max-width': '500px'
    });
    
    // Storica i riferimenti
    platformButtons = $('.platform-btn');
}

/**
 * Create a health platform connection link
 * @param {number} patientId The patient ID
 * @param {string} platform The platform name (from PLATFORMS enum)
 */
function createHealthPlatformLink(patientId, platform) {
    // Disable platform buttons
    if (platformButtons) {
        if (platformButtons.jquery) {
            // jQuery collection
            platformButtons.prop('disabled', true);
        } else {
            // DOM collection
            platformButtons.forEach(btn => btn.disabled = true);
        }
    }
    
    // Show loading status
    if (connectionStatusElem) {
        connectionStatusElem.classList.remove('d-none', 'alert-success', 'alert-danger');
        connectionStatusElem.classList.add('alert-info');
        connectionStatusElem.innerHTML = `
            <i class="fas fa-spinner fa-spin me-2"></i>
            ${translateText('Creating connection link...')}
        `;
    }
    
    // Make API request to create link
    fetch(`/health/create_link/${patientId}/${platform}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        // Re-enable platform buttons
        if (platformButtons) {
            if (platformButtons.jquery) {
                // jQuery collection
                platformButtons.prop('disabled', false);
            } else {
                // DOM collection
                platformButtons.forEach(btn => btn.disabled = false);
            }
        }
        
        if (data.success) {
            // Show success message with the link to copy
            if (connectionStatusElem) {
                connectionStatusElem.classList.remove('alert-info', 'alert-danger');
                connectionStatusElem.classList.add('alert-success');
                connectionStatusElem.innerHTML = `
                    <i class="fas fa-check-circle me-2"></i>
                    ${translateText('Link created successfully!')}
                    <div class="mt-3">
                        <p class="mb-1">${translateText('Link per la connessione (valido per 24 ore):')}</p>
                        <div class="input-group mb-3">
                            <input type="text" class="form-control" id="linkCopyInput" value="${data.connect_url}" readonly>
                            <button class="btn btn-outline-primary" type="button" id="copyLinkBtn">
                                <i class="fas fa-copy"></i> ${translateText('Copia')}
                            </button>
                        </div>
                        <small class="text-muted">${translateText('Fornisci questo link al paziente per connettere il suo account Fitbit.')}</small>
                    </div>
                `;
                
                // Add event listener for the copy button
                const copyBtn = document.getElementById('copyLinkBtn');
                const linkInput = document.getElementById('linkCopyInput');
                
                if (copyBtn && linkInput) {
                    copyBtn.addEventListener('click', () => {
                        linkInput.select();
                        document.execCommand('copy');
                        copyBtn.innerHTML = `<i class="fas fa-check"></i> ${translateText('Copiato')}`;
                        setTimeout(() => {
                            copyBtn.innerHTML = `<i class="fas fa-copy"></i> ${translateText('Copia')}`;
                        }, 2000);
                    });
                }
            }
        } else {
            // Show error message
            if (connectionStatusElem) {
                connectionStatusElem.classList.remove('alert-info', 'alert-success');
                connectionStatusElem.classList.add('alert-danger');
                connectionStatusElem.innerHTML = `
                    <i class="fas fa-exclamation-circle me-2"></i>
                    ${translateText('Error creating link')}: ${data.message}
                `;
            }
        }
    })
    .catch(error => {
        console.error('Error creating health platform link:', error);
        
        // Re-enable platform buttons
        if (platformButtons) {
            if (platformButtons.jquery) {
                // jQuery collection
                platformButtons.prop('disabled', false);
            } else {
                // DOM collection
                platformButtons.forEach(btn => btn.disabled = false);
            }
        }
        
        // Show error message
        if (connectionStatusElem) {
            connectionStatusElem.classList.remove('alert-info', 'alert-success');
            connectionStatusElem.classList.add('alert-danger');
            connectionStatusElem.innerHTML = `
                <i class="fas fa-exclamation-circle me-2"></i>
                ${translateText('Error creating link. Please try again.')}
            `;
        }
    });
}

/**
 * Disconnect from a health platform
 * @param {number} patientId The patient ID
 * @param {string} platform The platform name
 */
function disconnectHealthPlatform(patientId, platform) {
    // Confirm before disconnecting
    if (!confirm(translateText('Sei sicuro di voler disconnettere questa piattaforma? I dati non saranno più disponibili.'))) {
        return;
    }
    
    // Disable button during the request
    if (syncButton) {
        syncButton.disabled = true;
        syncButton.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i> ${translateText('Disconnessione...')}`;
    }
    
    // Make API request to disconnect
    fetch(`/health/disconnect/${patientId}/${platform}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success notification
            showNotification(translateText('Disconnessione completata con successo'), 'success');
            
            // Reload connection details
            loadConnectionDetails(patientId);
        } else {
            // Show error notification
            showNotification(translateText('Errore durante la disconnessione: ') + data.message, 'danger');
            
            // Re-enable button
            if (syncButton) {
                syncButton.disabled = false;
            }
        }
    })
    .catch(error => {
        console.error('Error disconnecting health platform:', error);
        
        // Show error notification
        showNotification(translateText('Errore durante la disconnessione. Riprova più tardi.'), 'danger');
        
        // Re-enable button
        if (syncButton) {
            syncButton.disabled = false;
        }
    });
}

/**
 * Extract patient ID from the current URL
 * @returns {number|null} The patient ID or null if not found
 */
function getPatientIdFromUrl() {
    const urlPath = window.location.pathname;
    const matches = urlPath.match(/\/patients\/(\d+)/);
    return matches && matches.length > 1 ? parseInt(matches[1]) : null;
}

/**
 * Format a date object to a readable date-time string
 * @param {Date} date The date to format
 * @returns {string} Formatted date string
 */
function formatDateTime(date) {
    if (!(date instanceof Date) || isNaN(date)) {
        return '-';
    }
    
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return date.toLocaleDateString(undefined, options);
}

/**
 * Show a temporary notification
 * @param {string} message The message to display
 * @param {string} type The type of notification (success, danger, etc.)
 */
function showNotification(message, type) {
    // Create notification element if it doesn't exist
    let notificationContainer = document.getElementById('notificationContainer');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notificationContainer';
        notificationContainer.style.position = 'fixed';
        notificationContainer.style.top = '20px';
        notificationContainer.style.right = '20px';
        notificationContainer.style.zIndex = '9999';
        document.body.appendChild(notificationContainer);
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    notificationContainer.appendChild(notification);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 150);
    }, 5000);
}

/**
 * Helper function to get CSRF token from cookies
 * @returns {string} CSRF token
 */
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='));
    
    return cookieValue ? cookieValue.split('=')[1] : '';
}

/**
 * Helper function for text translation
 * Just returns the input text for now
 * Can be expanded later to use actual translations
 * @param {string} text Text to translate
 * @returns {string} Translated text
 */
function translateText(text) {
    return text;
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', initializeHealthPlatform);