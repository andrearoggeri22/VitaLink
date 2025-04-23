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
let syncModal = null;
let platformButtons = null;
let connectionStatusElem = null;

/**
 * Initialize the health platforms integration
 */
function initHealthPlatforms() {
    // Initialize DOM references
    syncButton = document.getElementById('syncHealthBtn');
    
    if (syncButton) {
        syncButton.addEventListener('click', handleSyncButtonClick);
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
 * Handle the click on the Sync button
 */
function handleSyncButtonClick() {
    // Get the patient ID from the URL
    const patientId = getPatientIdFromUrl();
    if (!patientId) {
        console.error('Could not determine patient ID');
        return;
    }
    
    // Show platform selection modal or directly create a link
    createHealthPlatformModal(patientId);
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
                `;
            }
            
            // Open the link in a new window/tab
            setTimeout(() => {
                window.open(data.connect_url, '_blank');
                
                // Close the modal
                if (syncModal) {
                    syncModal.hide();
                }
            }, 1000);
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