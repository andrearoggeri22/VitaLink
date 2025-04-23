/**
 * Health Platforms Integration JavaScript
 * 
 * Handles the integration with health platforms (Fitbit, Google Fit, Apple Health)
 * Provides functionality for:
 * - Creating connection links
 * - Loading data from connected platforms
 * - Displaying data in charts and tables
 */

// Cache for API data to avoid redundant calls
const apiDataCache = {
    // Format: { dataType: { data: [...], timestamp: Date } }
};

// Constants
const CACHE_EXPIRY_MS = 5 * 60 * 1000; // 5 minutes
const PLATFORMS = {
    FITBIT: 'fitbit',
    GOOGLE_FIT: 'google_fit',
    APPLE_HEALTH: 'apple_health'
};

// DOM elements references
let syncButton = null;
let connectButton = null;
let disconnectButton = null;
let syncModal = null;
let platformButtons = null;
let connectionStatusElem = null;

/**
 * Initialize the health platforms integration
 */
function initHealthPlatforms() {
    // Initialize DOM references
    syncButton = document.getElementById('syncHealthBtn');
    connectButton = document.getElementById('connectBtn');
    disconnectButton = document.getElementById('disconnectBtn');
    
    console.log('Initializing health platform...');
    console.log('Sync button found:', !!syncButton);
    console.log('Connect button found:', !!connectButton);
    console.log('Disconnect button found:', !!disconnectButton);
    
    // Find connection details section
    const connectionDetails = document.getElementById('connectionDetails');
    if (connectionDetails) {
        console.log('Connection details section found');
        
        // Get patient ID from the URL
        const patientId = getPatientIdFromUrl();
        console.log('Patient ID:', patientId);
        
        if (patientId) {
            // Add click event to the sync button
            if (syncButton) {
                console.log('Adding click event listener to sync button');
                syncButton.addEventListener('click', function() {
                    createHealthPlatformModal(patientId);
                });
            }
            
            // Add click event to the connect button if it exists
            if (connectButton) {
                console.log('Adding click event listener to connect button');
                connectButton.addEventListener('click', function() {
                    createHealthPlatformModal(patientId);
                });
            }
            
            // Add click event to the disconnect button if it exists
            if (disconnectButton) {
                console.log('Adding click event listener to disconnect button');
                disconnectButton.addEventListener('click', function() {
                    const platform = document.getElementById('platformName')?.textContent || 'fitbit';
                    if (confirm(translateText('Sei sicuro di voler disconnettere questa piattaforma? I dati non saranno più disponibili.'))) {
                        disconnectHealthPlatform(patientId, platform);
                    }
                });
            }
            
            // Check connection status
            checkConnectionStatus(patientId);
        }
    }
    
    // Check if we need to load data for charts
    const chartContainers = document.querySelectorAll('.vitals-chart-container');
    if (chartContainers.length > 0) {
        // Attempt to load data for each chart
        const chartTabs = document.querySelectorAll('#vitalsChartTabs .nav-link');
        if (chartTabs.length > 0) {
            // Load data for the active tab first
            const activeTab = document.querySelector('#vitalsChartTabs .nav-link.active');
            if (activeTab) {
                const dataType = activeTab.id.replace('tab-', '');
                loadHealthPlatformData(dataType);
            }
            
            // Set up event listeners for tab clicks
            chartTabs.forEach(tab => {
                tab.addEventListener('shown.bs.tab', function (event) {
                    const dataType = event.target.id.replace('tab-', '');
                    loadHealthPlatformData(dataType);
                });
            });
        }
    }
}

/**
 * Check the connection status for the patient
 * Updates button text based on connection status and populates connection details
 * @param {number} patientId The patient ID
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
 * Update button to show "Disconnetti" text and styling
 * @param {string} platform Platform name
 */
function updateButtonToDisconnect(platform) {
    if (syncButton) {
        syncButton.innerHTML = `<i class="fas fa-unlink me-1"></i> ${translateText('Disconnetti')}`;
        syncButton.classList.remove('btn-info');
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
        syncButton.classList.add('btn-info');
        syncButton.setAttribute('data-connected', 'false');
        syncButton.removeAttribute('data-platform');
    }
}

/**
 * Handle the click on the Sync button
 * This handles both connection and disconnection based on the current state
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
 * Create a custom confirmation dialog
 * @param {string} title The dialog title
 * @param {string} message The confirmation message
 * @param {Function} confirmCallback Function to call if user confirms
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
                            ${translateText('Annulla')}
                        </button>
                        <button type="button" class="btn btn-danger" id="confirmBtn">
                            <i class="fas fa-unlink me-1"></i> ${translateText('Disconnetti')}
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
    document.getElementById('confirmBtn').addEventListener('click', function() {
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
 * Disconnect from a health platform
 * @param {number} patientId The patient ID
 * @param {string} platform The platform name
 */
function disconnectHealthPlatform(patientId, platform) {
    console.log('Disconnecting platform', platform, 'for patient', patientId);
    
    // Show confirmation dialog
    createConfirmDialog(
        translateText('Disconnetti piattaforma'),
        translateText('Sei sicuro di voler disconnettere questa piattaforma? I dati non saranno più disponibili.'),
        function() {
            // Execute disconnection after confirmation
            executeDisconnection(patientId, platform);
        }
    );
}

/**
 * Execute the disconnection from a health platform
 * @param {number} patientId The patient ID
 * @param {string} platform The platform name
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
    
    // Make API request to disconnect
    fetch(`/health/disconnect/${patientId}/${platform.toLowerCase()}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Disconnect response:', data);
        
        if (data.success) {
            // Update connection details UI if present
            const connectionActive = document.getElementById('connectionActive');
            const connectionInactive = document.getElementById('connectionInactive');
            
            if (connectionActive && connectionInactive) {
                connectionActive.classList.add('d-none');
                connectionInactive.classList.remove('d-none');
            }
            
            // Update sync button if present
            if (syncButton) {
                syncButton.innerHTML = `<i class="fas fa-sync me-1"></i> ${translateText('Health Sync')}`;
                syncButton.classList.remove('btn-danger');
                syncButton.classList.add('btn-info');
                syncButton.setAttribute('data-connected', 'false');
                syncButton.removeAttribute('data-platform');
                syncButton.disabled = false;
            }
            
            // Clear any cached data
            apiDataCache = {};
            
            // Refresh charts if present
            const activeTab = document.querySelector('#vitalsChartTabs .nav-link.active');
            if (activeTab) {
                const dataType = activeTab.id.replace('tab-', '');
                loadHealthPlatformData(dataType);
            }
            
            // Show success notification
            showNotification(translateText('Successfully disconnected from health platform'), 'success');
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
 * Extract patient ID from the current URL
 * @returns {number|null} The patient ID or null if not found
 */
function getPatientIdFromUrl() {
    const urlPath = window.location.pathname;
    const matches = urlPath.match(/\/patients\/(\d+)/);
    return matches && matches.length > 1 ? parseInt(matches[1]) : null;
}

/**
 * Create a modal dialog for selecting a health platform
 * @param {number} patientId The patient ID
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
            btn.addEventListener('click', function() {
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
 * Create a health platform connection link
 * @param {number} patientId The patient ID
 * @param {string} platform The platform name (from PLATFORMS enum)
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
            
            // Don't auto-close the modal or auto-open the link
            // Let the user copy the link manually
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
 * Load data from health platform API for a specific data type
 * @param {string} dataType The type of data to load (heart_rate, steps, etc.)
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
 * Populate a chart with data from health platform
 * @param {string} dataType The type of data to display
 * @param {Array} data The data to display
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
document.addEventListener('DOMContentLoaded', initHealthPlatforms);