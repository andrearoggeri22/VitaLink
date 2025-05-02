/**
 * Health Platforms Integration JavaScript
 * 
 * Handles the integration with health platforms (Fitbit, Google Fit, Apple Health)
 * Provides functionality for:
 * - Creating connection links
 * - Loading data from connected platforms
 * - Displaying data in charts and tables
 */

/**
 * Cache for API data to avoid redundant calls.
 * Stores data retrieved from health platforms to reduce API requests and improve performance.
 * @type {Object}
 * @format { dataType: { data: Array, timestamp: Date } }
 */
const apiDataCache = {
    // Format: { dataType: { data: [...], timestamp: Date } }
};

// Constants
/**
 * Cache expiration time in milliseconds (5 minutes).
 * Determines how long cached health platform data remains valid before a refresh is needed.
 * @type {number}
 */
const CACHE_EXPIRY_MS = 5 * 60 * 1000; // 5 minutes

/**
 * Supported health data platforms.
 * Defines the available health platforms that can be integrated with the application.
 * @type {Object}
 */
const PLATFORMS = {
    FITBIT: 'fitbit',
    GOOGLE_HEALTH_CONNECT: 'google_health_connect',
    APPLE_HEALTH: 'apple_health'
};

/**
 * DOM element references for health platform integration.
 * These references are initialized in the initHealthPlatforms function.
 */

/**
 * Reference to the sync button element.
 * This button toggles between connecting to a platform and disconnecting from it.
 * @type {HTMLElement|null}
 */
let syncButton = null;

/**
 * Reference to the connect button element (deprecated).
 * Previously used for connecting to health platforms, now replaced by syncButton.
 * @type {HTMLElement|null}
 * @deprecated
 */
let connectButton = null;

/**
 * Reference to the disconnect button element (deprecated).
 * Previously used for disconnecting from health platforms, now replaced by syncButton.
 * @type {HTMLElement|null}
 * @deprecated
 */
let disconnectButton = null;

/**
 * Reference to the modal dialog for health platform selection.
 * Contains UI for selecting and connecting to health platforms.
 * @type {bootstrap.Modal|null}
 */
let syncModal = null;

/**
 * Collection of platform selection buttons in the modal.
 * Each button represents a specific health platform that can be connected.
 * @type {NodeList|null}
 */
let platformButtons = null;

/**
 * Element that displays connection status messages.
 * Shows success/error messages during connection attempts.
 * @type {HTMLElement|null}
 */
let connectionStatusElem = null;

/**
 * Initialize the health platforms integration.
 * 
 * This function sets up the health platform integration by:
 * 1. Initializing DOM references for UI elements
 * 2. Setting up event handlers for user interactions
 * 3. Checking connection status
 * 4. Loading health data for charts if available
 * 
 * It runs when the DOM is fully loaded.
 */
function initHealthPlatforms() {
    // Initialize DOM references
    syncButton = document.getElementById('syncHealthBtn');
    // The connect and disconnect buttons have been removed
    connectButton = null;
    disconnectButton = null;

    console.log('Initializing health platform...');
    console.log('Sync button found:', !!syncButton);    /**
     * Find connection details section in the DOM.
     * This section contains information about the current health platform connection.
     * @type {HTMLElement|null}
     */
    const connectionDetails = document.getElementById('connectionDetails');
    if (connectionDetails) {
        console.log('Connection details section found');

        /**
         * Get patient ID from the URL.
         * The patient ID is extracted from the current URL path.
         * @type {number|null}
         */
        const patientId = getPatientIdFromUrl();
        console.log('Patient ID:', patientId);

        if (patientId) {
            // Add click event to the sync button (now handles both connect and disconnect)
            if (syncButton) {
                console.log('Adding click event listener to sync button');                /**
                 * Event handler for sync button clicks.
                 * Determines whether to show connection or disconnection UI based on current state.
                 * @listens click
                 */
                syncButton.addEventListener('click', function () {
                    /** @type {boolean} Whether a platform is currently connected */
                    const isConnected = this.getAttribute('data-connected') === 'true';
                    /** @type {string|null} The currently connected platform */
                    const platform = this.getAttribute('data-platform');

                    if (isConnected && platform) {
                        // If connected, show disconnect confirmation popup
                        disconnectHealthPlatform(patientId, platform);
                    } else {
                        // If not connected, show connection popup
                        createHealthPlatformModal(patientId);
                    }
                });
            }

            // Check connection status
            checkConnectionStatus(patientId);
        }
    }    /**
     * Check if charts are present on the page and load data for them.
     * If charts are found, it loads data for the currently active chart first,
     * then sets up listeners for tab changes.
     */
    // Check if we need to load data for charts
    /** @type {NodeList} Collection of chart container elements */
    const chartContainers = document.querySelectorAll('.vitals-chart-container');
    if (chartContainers.length > 0) {
        // Attempt to load data for each chart
        /** @type {NodeList} Collection of chart tab navigation links */
        const chartTabs = document.querySelectorAll('#vitalsChartTabs .nav-link');
        if (chartTabs.length > 0) {
            // Load data for the active tab first
            /** @type {HTMLElement|null} Currently active chart tab */
            const activeTab = document.querySelector('#vitalsChartTabs .nav-link.active');
            if (activeTab) {
                /** @type {string} Type of health data to display (heart_rate, steps, etc.) */
                const dataType = activeTab.id.replace('tab-', '');
                loadHealthPlatformData(dataType);
            }            // Set up event listeners for tab clicks
            chartTabs.forEach(tab => {
                /**
                 * Event handler for tab changes to load appropriate health data.
                 * When user switches tabs, loads the relevant health data for the selected tab.
                 * @listens shown.bs.tab
                 */
                tab.addEventListener('shown.bs.tab', function (event) {
                    /** @type {string} Type of health data to display */
                    const dataType = event.target.id.replace('tab-', '');
                    loadHealthPlatformData(dataType);
                });
            });
        }
    }
}

/**
 * Check the connection status for the patient.
 * Makes an API call to determine if the patient has an active health platform 
 * connection, then updates the UI accordingly.
 * 
 * Updates button text based on connection status and populates connection details
 * including platform name, connection date, and expiration date.
 * 
 * @param {number} patientId The patient ID to check connection status for
 */
function checkConnectionStatus(patientId) {
    if (!patientId) {
        console.error('Could not determine patient ID');
        return;
    }

    const connectionLoading = document.getElementById('connectionLoading');
    const connectionActive = document.getElementById('connectionActive');
    const connectionInactive = document.getElementById('connectionInactive');

    console.log('Checking connection status for patient', patientId);

    fetch(`/health/check_connection/${patientId}`)
        .then(response => response.json())
        .then(data => {
            console.log('Connection status data:', data);

            if (connectionLoading) connectionLoading.classList.add('d-none');

            if (data.connected) {
                // Update button to disconnect
                if (syncButton) {
                    syncButton.innerHTML = `<i class="fas fa-unlink me-1"></i> ${translateText('Disconnect')}`;
                    syncButton.classList.remove('btn-info');
                    syncButton.classList.add('btn-danger');
                    syncButton.setAttribute('data-connected', 'true');
                    syncButton.setAttribute('data-platform', data.platform);
                }

                // Update connection details if present
                if (connectionActive && connectionInactive) {
                    connectionActive.classList.remove('d-none');
                    connectionInactive.classList.add('d-none');

                    // Populate platform info
                    if (document.getElementById('platformName')) {
                        document.getElementById('platformName').textContent = data.platform.charAt(0).toUpperCase() + data.platform.slice(1);
                    }

                    // Populate connection date
                    if (document.getElementById('connectionDate')) {
                        document.getElementById('connectionDate').textContent = data.connected_since ?
                            new Date(data.connected_since).toLocaleDateString() :
                            new Date().toLocaleDateString();
                    }

                    // Populate expiration date
                    if (document.getElementById('expirationDate')) {
                        document.getElementById('expirationDate').textContent = data.token_expires_at ?
                            new Date(data.token_expires_at).toLocaleDateString() :
                            translateText('No expiration');
                    }
                }
            } else {
                // Update button to connect
                if (syncButton) {
                    syncButton.innerHTML = `<i class="fas fa-sync me-1"></i> ${translateText('Health Sync')}`;
                    syncButton.classList.remove('btn-danger');
                    syncButton.classList.add('btn-info');
                    syncButton.setAttribute('data-connected', 'false');
                    syncButton.removeAttribute('data-platform');
                }

                // Update connection details if present
                if (connectionActive && connectionInactive) {
                    connectionActive.classList.add('d-none');
                    connectionInactive.classList.remove('d-none');
                }
            }
        })
        .catch(error => {
            console.error('Error checking connection status:', error);

            // Hide loading indicator
            if (connectionLoading) connectionLoading.classList.add('d-none');

            // Show inactive state in case of error
            if (connectionActive && connectionInactive) {
                connectionActive.classList.add('d-none');
                connectionInactive.classList.remove('d-none');
            }

            // Default to Connect button in case of error
            if (syncButton) {
                syncButton.innerHTML = `<i class="fas fa-sync me-1"></i> ${translateText('Health Sync')}`;
                syncButton.classList.remove('btn-danger');
                syncButton.classList.add('btn-info');
                syncButton.setAttribute('data-connected', 'false');
                syncButton.removeAttribute('data-platform');
            }
        });
}

/**
 * Update button to show "Disconnect" text and styling.
 * Changes the sync button appearance and attributes to indicate a connected state,
 * including changing colors, icon, and storing the connected platform name.
 * 
 * @param {string} platform Platform name (e.g., 'fitbit', 'google_health_connect')
 */
function updateButtonToDisconnect(platform) {
    if (syncButton) {
        syncButton.innerHTML = `<i class="fas fa-unlink me-1"></i> ${translateText('Disconnect')}`;
        syncButton.classList.remove('btn-info');
        syncButton.classList.add('btn-danger');
        syncButton.setAttribute('data-connected', 'true');
        syncButton.setAttribute('data-platform', platform);
    }
}

/**
 * Update button to show "Health Sync" text and styling.
 * Changes the sync button appearance and attributes to indicate a disconnected state,
 * including changing button color, icon, and removing the platform data attribute.
 */
function updateButtonToConnect() {
    if (syncButton) {
        syncButton.innerHTML = `<i class="fas fa-sync me-1"></i> ${translateText('Health Sync')}`;
        syncButton.classList.remove('btn-danger');
        syncButton.classList.add('btn-info');
        syncButton.setAttribute('data-connected', 'false');
        syncButton.removeAttribute('data-platform');
    }
}

/**
 * Handle the click on the Sync button.
 * This function determines the current connection state and either initiates
 * a new platform connection or disconnects from the currently connected platform.
 * The behavior changes based on the current connection state.
 */
function handleSyncButtonClick() {
    // Get the patient ID from the URL
    const patientId = getPatientIdFromUrl();
    if (!patientId) {
        console.error('Could not determine patient ID');
        return;
    }

    // Check if we're connected or not
    const isConnected = syncButton.getAttribute('data-connected') === 'true';

    if (isConnected) {
        // Handle disconnection
        const platform = syncButton.getAttribute('data-platform');
        disconnectHealthPlatform(patientId, platform);
    } else {
        // Handle connection - show platform selection modal
        createHealthPlatformModal(patientId);
    }
}

/**
 * Create a custom confirmation dialog.
 * Creates a Bootstrap modal dialog for confirming potentially destructive actions,
 * such as disconnecting from health platforms. The dialog includes a title,
 * message, and buttons for canceling or confirming the action.
 * 
 * @param {string} title The dialog title displayed in the header
 * @param {string} message The confirmation message displayed in the body
 * @param {Function} confirmCallback Function to call if user confirms the action
 */
function createConfirmDialog(title, message, confirmCallback) {
    // Remove any existing confirmation dialogs
    const existingDialog = document.getElementById('confirmationModal');
    if (existingDialog) {
        existingDialog.remove();
    }

    // Create the modal HTML
    const modalHtml = `
        <div class="modal fade" id="confirmationModal" tabindex="-1" aria-labelledby="confirmationModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title" id="confirmationModalLabel">
                            <i class="fas fa-exclamation-triangle me-2"></i> ${title}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            ${translateText('Cancel')}
                        </button>
                        <button type="button" class="btn btn-danger" id="confirmBtn">
                            <i class="fas fa-unlink me-1"></i> ${translateText('Disconnect')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add the modal to the DOM
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer.firstElementChild);

    // Initialize the modal
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));

    // Add event listener for the confirm button
    document.getElementById('confirmBtn').addEventListener('click', function () {
        // Hide the modal
        modal.hide();

        // Call the callback function
        if (confirmCallback && typeof confirmCallback === 'function') {
            confirmCallback();
        }
    });

    // Show the modal
    modal.show();
}

/**
 * Disconnect from a health platform.
 * Shows a confirmation dialog before disconnecting to ensure the user wants
 * to proceed. If confirmed, it calls executeDisconnection to perform the actual
 * disconnection from the health platform.
 * 
 * @param {number} patientId The patient ID associated with the connection
 * @param {string} platform The platform name to disconnect from (e.g., 'fitbit')
 */
function disconnectHealthPlatform(patientId, platform) {
    console.log('Disconnecting platform', platform, 'for patient', patientId);

    // Show confirmation dialog
    createConfirmDialog(
        translateText('Disconnect Platform'),
        translateText('Are you sure you want to disconnect this platform? The data will no longer be available.'),
        function () {
            // Execute disconnection after confirmation
            executeDisconnection(patientId, platform);
        }
    );
}

/**
 * Execute the disconnection from a health platform.
 * Makes the API call to disconnect the specified health platform from the patient's
 * account, updates the UI during the process, and handles success/failure states.
 * This is called after user confirmation from disconnectHealthPlatform.
 * 
 * @param {number} patientId The patient ID associated with the connection
 * @param {string} platform The platform name to disconnect from (e.g., 'fitbit')
 */
function executeDisconnection(patientId, platform) {
    // Disable buttons during the request
    if (syncButton) {
        syncButton.disabled = true;
        syncButton.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i> ${translateText('Disconnecting...')}`;
    }

    if (disconnectButton) {
        disconnectButton.disabled = true;
        disconnectButton.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i> ${translateText('Disconnecting...')}`;
    }

    // Log operation details
    console.log(`Executing disconnection for patient ${patientId} from platform '${platform}'`);

    // Make API request to disconnect
    fetch(`/health/disconnect/${patientId}/fitbit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
        .then(response => response.json())
        .then(data => {
            console.log('Disconnect response:', data);

            if (data.success) {            // Show success notification
                showNotification(translateText('Successfully disconnected from health platform'), 'success');

                // Reload page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                // Re-enable buttons
                if (syncButton) syncButton.disabled = false;
                if (disconnectButton) disconnectButton.disabled = false;

                // Restore original button text
                if (syncButton) {
                    syncButton.innerHTML = `<i class="fas fa-unlink me-1"></i> ${translateText('Disconnect')}`;
                }

                if (disconnectButton) {
                    disconnectButton.innerHTML = `<i class="fas fa-unlink me-1"></i> ${translateText('Disconnect')}`;
                }

                // Show error notification
                showNotification(translateText('Error disconnecting: ') + data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error disconnecting health platform:', error);

            // Re-enable buttons
            if (syncButton) syncButton.disabled = false;
            if (disconnectButton) disconnectButton.disabled = false;

            // Restore original button text
            if (syncButton) {
                syncButton.innerHTML = `<i class="fas fa-unlink me-1"></i> ${translateText('Disconnect')}`;
            }

            if (disconnectButton) {
                disconnectButton.innerHTML = `<i class="fas fa-unlink me-1"></i> ${translateText('Disconnect')}`;
            }

            // Show error notification
            showNotification(translateText('Error disconnecting. Please try again later.'), 'danger');
        });
}

/**
 * Show a temporary notification.
 * Creates and displays a Bootstrap alert component with the specified message
 * and styling. The notification automatically dismisses itself after 5 seconds.
 * It's used to provide feedback after operations like connecting or disconnecting.
 * 
 * @param {string} message The message to display in the notification
 * @param {string} type The type of notification that determines styling (success, danger, warning, info)
 */
function showNotification(message, type) {
    // Instead of creating a custom container, we use the same method as showAlert
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
        // Check if an alert already exists, if so insert before it,
        // otherwise insert before the first element in the main container
        const existingAlert = mainContainer.querySelector('.alert');
        if (existingAlert) {
            mainContainer.insertBefore(alertDiv, existingAlert);
        } else {
            mainContainer.insertBefore(alertDiv, mainContainer.firstChild);
        }
    } else {
        // Fallback: use standard container if main.container doesn't exist
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
 * Extract patient ID from the current URL.
 * Parses the current window URL to extract the patient ID from paths like '/patients/123'.
 * This allows the script to determine which patient is being viewed without additional API calls.
 * 
 * @returns {number|null} The patient ID as a number if found, null otherwise
 */
function getPatientIdFromUrl() {
    const urlPath = window.location.pathname;
    const matches = urlPath.match(/\/patients\/(\d+)/);
    return matches && matches.length > 1 ? parseInt(matches[1]) : null;
}

/**
 * Create a modal dialog for selecting a health platform.
 * Dynamically generates a Bootstrap modal dialog that allows the user to select
 * which health platform they want to connect to. The modal contains buttons for
 * each supported platform and handles the connection process.
 * 
 * @param {number} patientId The patient ID to create the health platform connection for
 */
function createHealthPlatformModal(patientId) {
    // Create modal element if it doesn't exist
    if (!document.getElementById('healthPlatformModal')) {
        const modalHtml = `
            <div class="modal fade" id="healthPlatformModal" tabindex="-1" aria-labelledby="healthPlatformModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="healthPlatformModalLabel">
                                <i class="fas fa-link me-2"></i> ${translateText('Connect Health Platform')}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="${translateText('Close')}"></button>
                        </div>                        <div class="modal-body">
                            <p>${translateText('Generate a connection link for health data:')}</p>
                            <div id="platformOptions" class="d-grid gap-2">
                                <button class="btn btn-outline-primary platform-btn" data-platform="${PLATFORMS.FITBIT}">
                                    <i class="fas fa-link me-2"></i> ${translateText('Generate Link')}
                                </button>
                            </div>
                            <div id="connectionStatus" class="alert mt-3 d-none"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                ${translateText('Cancel')}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to the DOM
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer.firstElementChild);

        // Initialize modal reference
        syncModal = new bootstrap.Modal(document.getElementById('healthPlatformModal'));

        // Initialize platform buttons
        platformButtons = document.querySelectorAll('.platform-btn');
        platformButtons.forEach(btn => {
            btn.addEventListener('click', function () {
                const platform = this.getAttribute('data-platform');
                createHealthPlatformLink(patientId, platform);
            });
        });

        // Initialize connection status element
        connectionStatusElem = document.getElementById('connectionStatus');
    } else {
        syncModal = new bootstrap.Modal(document.getElementById('healthPlatformModal'));
    }

    // Show the modal
    syncModal.show();
}

/**
 * Create a health platform connection link.
 * Makes an API call to generate a unique connection URL that patients can use
 * to connect their health platform accounts (like Fitbit) to the VitaLink system.
 * Displays the generated link in the modal with copy functionality.
 * 
 * @param {number} patientId The patient ID to create the connection for
 * @param {string} platform The platform name (from PLATFORMS enum, e.g., 'fitbit')
 */
function createHealthPlatformLink(patientId, platform) {
    // Disable platform buttons
    if (platformButtons) {
        platformButtons.forEach(btn => btn.disabled = true);
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
                platformButtons.forEach(btn => btn.disabled = false);
            }

            if (data.success) {
                // Show success message
                if (connectionStatusElem) {
                    // Remove existing classes and add success class
                    connectionStatusElem.classList.remove('alert-info', 'alert-danger', 'd-none');
                    connectionStatusElem.classList.add('alert-success');

                    connectionStatusElem.innerHTML = `
                    <i class="fas fa-check-circle me-2"></i>
                    ${translateText('Link created successfully!')}
                `;
                const URL = data.connect_url;
                // Create a new element outside the alert to contain the link
                // This element won't be affected by any automatic alert behavior
                const linkContainer = document.createElement('div');
                linkContainer.id = 'healthPlatformLinkContainer';
                linkContainer.className = 'mt-3 w-100'; // Add w-100 for full width

                linkContainer.innerHTML = `
                    <div class="mb-1 d-flex justify-content-center" id="qrcode"></div>
                    <p class="mb-1">${translateText('Connection link (valid for 24 hours):')}</p>
                    <div class="input-group mb-3">
                        <input type="text" class="form-control" id="linkCopyInput" value="${URL}" readonly>
                        <button class="btn btn-outline-primary" type="button" id="copyLinkBtn">
                            <i class="fas fa-copy"></i> ${translateText('Copy')}
                        </button>
                    </div>
                    <small class="text-muted">${translateText('Provide this link to the patient to connect their data collection service.')}</small>
                `;
                // Insert new container after connectionStatusElem
                connectionStatusElem.parentNode.insertBefore(linkContainer, connectionStatusElem.nextSibling);
                // Generate QR code for the connection link
                if (window.QRCode) {
                    new QRCode(linkContainer.querySelector('#qrcode'), {
                        text: URL,
                        colorDark: '#000',
                        colorLight: '#fff',
                        correctLevel: QRCode.CorrectLevel.H
                    });
                }
                // Insert new container after connectionStatusElem
                connectionStatusElem.parentNode.insertBefore(linkContainer, connectionStatusElem.nextSibling);

                // Add event listener for the copy button
                const copyBtn = document.getElementById('copyLinkBtn');
                const linkInput = document.getElementById('linkCopyInput');

                if (copyBtn && linkInput) {
                    copyBtn.addEventListener('click', () => {
                        linkInput.select();
                        document.execCommand('copy');
                        copyBtn.innerHTML = `<i class="fas fa-check"></i> ${translateText('Copied')}`;
                        setTimeout(() => {
                            copyBtn.innerHTML = `<i class="fas fa-copy"></i> ${translateText('Copy')}`;
                        }, 2000);
                    });
                }

                // Modify the modal footer to make it clear the user needs to close manually
                const modalFooter = document.querySelector('#healthPlatformModal .modal-footer');
                if (modalFooter) {
                    modalFooter.innerHTML = `
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                            ${translateText('Close')}
                        </button>
                    `;
                }
            }

            // Explicitly set that we don't want automatic closures
            // Don't automatically close the modal and don't automatically open the link
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
            platformButtons.forEach(btn => btn.disabled = false);
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
 * Load data from health platform API for a specific data type.
 * Retrieves health data of the specified type from the server, with smart caching
 * to avoid redundant API calls. Displays loading states and handles error conditions.
 * Data is fetched for the current patient and passed to the chart rendering function.
 * 
 * @param {string} dataType The type of health data to load (e.g., 'heart_rate', 'steps', 'sleep')
 */
function loadHealthPlatformData(dataType) {
    // Check if we have cached data that's still valid
    if (apiDataCache[dataType] &&
        (new Date() - apiDataCache[dataType].timestamp) < CACHE_EXPIRY_MS) {
        // Use cached data
        populateChart(dataType, apiDataCache[dataType].data);
        return;
    }

    // Get the patient ID from the URL
    const patientId = getPatientIdFromUrl();
    if (!patientId) {
        console.error('Could not determine patient ID');
        return;
    }

    // Show loading indicator on the chart
    const chartContainer = document.getElementById(`chart-tab-${dataType}`);
    if (chartContainer) {
        chartContainer.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
                <p>${translateText('Loading data from health platform...')}</p>
            </div>
        `;
    }

    // Make API request to get data
    fetch(`/health/data/${dataType}/${patientId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cache the data
                apiDataCache[dataType] = {
                    data: data.data,
                    timestamp: new Date()
                };

                // Populate chart with the data
                populateChart(dataType, data.data);
            } else {
                // Show error message
                if (chartContainer) {
                    chartContainer.innerHTML = `
                    <div class="text-center py-5">
                        <i class="fas fa-exclamation-circle fa-2x text-danger mb-3"></i>
                        <p>${data.message || translateText('Error loading data from health platform')}</p>
                        <button class="btn btn-sm btn-outline-primary mt-2" onclick="loadHealthPlatformData('${dataType}')">
                            <i class="fas fa-sync me-1"></i> ${translateText('Try Again')}
                        </button>
                    </div>
                `;
                }
            }
        })
        .catch(error => {
            console.error(`Error loading health platform data for ${dataType}:`, error);

            // Show error message
            if (chartContainer) {
                chartContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-exclamation-circle fa-2x text-danger mb-3"></i>
                    <p>${translateText('Error loading data from health platform')}</p>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="loadHealthPlatformData('${dataType}')">
                        <i class="fas fa-sync me-1"></i> ${translateText('Try Again')}
                    </button>
                </div>
            `;
            }
        });
}

/**
 * Populate a chart with data from health platform.
 * Creates or updates a Chart.js visualization with the provided health data.
 * Handles empty data sets gracefully with informative messages, and adds
 * a report generation button for exporting chart data as reports.
 * 
 * @param {string} dataType The type of health data to display (e.g., 'heart_rate', 'steps')
 * @param {Array} data Array of data points with timestamp, value, and unit properties
 */
function populateChart(dataType, data) {
    const chartContainer = document.getElementById(`chart-tab-${dataType}`);
    const canvas = document.getElementById(`chart-${dataType}`);

    if (!chartContainer || !canvas) {
        console.error(`Chart container or canvas for ${dataType} not found`);
        return;
    }

    // Prepare chart data
    if (!data || data.length === 0) {
        // No data available
        chartContainer.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-chart-area fa-2x text-muted mb-3"></i>
                <p>${translateText('No data available for this parameter')}</p>
            </div>
        `;
        return;
    }

    // Sort data by timestamp
    data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    // Extract data for chart
    const labels = data.map(item => {
        const date = new Date(item.timestamp);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    });

    const values = data.map(item => item.value);
    const unit = data[0].unit || '';

    // Get or create chart
    let chart = Chart.getChart(canvas);
    if (chart) {
        // Update existing chart
        chart.data.labels = labels;
        chart.data.datasets[0].data = values;
        chart.update();
    } else {
        // Create new chart
        chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `${dataType.replace('_', ' ')} (${unit})`,
                    data: values,
                    borderColor: '#4285f4',
                    backgroundColor: 'rgba(66, 133, 244, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: unit
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: translateText('Date/Time')
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }

    // Add report generation button after chart
    const reportBtnContainer = document.createElement('div');
    reportBtnContainer.className = 'text-end mt-2';
    reportBtnContainer.innerHTML = `
        <a href="/views/patients/${getPatientIdFromUrl()}/vitals/${dataType}/report" 
           class="btn btn-sm btn-outline-info" target="_blank">
            <i class="fas fa-file-pdf me-1"></i> 
            ${translateText('Generate')} ${dataType.replace('_', ' ')} ${translateText('Report')}
        </a>
    `;

    // Replace the chart container content with the canvas and report button
    chartContainer.innerHTML = '';

    const canvasContainer = document.createElement('div');
    canvasContainer.className = 'vitals-chart-container';
    canvasContainer.appendChild(canvas);

    chartContainer.appendChild(canvasContainer);
    chartContainer.appendChild(reportBtnContainer);
}

/**
 * Helper function to get CSRF token from cookies.
 * Extracts the Cross-Site Request Forgery (CSRF) token from browser cookies,
 * which is required for making secure POST requests to the server.
 * 
 * @returns {string} The CSRF token value or an empty string if not found
 */
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='));

    return cookieValue ? cookieValue.split('=')[1] : '';
}

/**
 * Helper function for text translation.
 * A placeholder function for internationalization. Currently returns the input text unchanged,
 * but this can be expanded later to use actual translation services or dictionaries
 * to support multiple languages in the interface.
 * 
 * @param {string} text Text to be translated
 * @returns {string} Translated text (currently returns the same text)
 */
function translateText(text) {
    return text;
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', initHealthPlatforms);