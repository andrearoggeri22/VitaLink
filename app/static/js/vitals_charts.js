/**
 * Vitals Charts JavaScript
 * 
 * Manages the visualization of vital signs trend charts
 * and the historical data table obtained from health platforms
 * 
 * Features:
 * - Loading data from platform APIs (Fitbit, etc.)
 * - Displaying charts with customizable periods
 * - Updating the historical data table
 */
// Constants and global variables
const SUPPORTED_DATA_TYPES = {
    FITBIT: [
        // Main vital parameters
        { id: 'HEART_RATE', name: translateText('Heart Rate'), unit: 'bpm', color: '#FF5252', chartType: 'line' },
        { id: 'OXYGEN_SATURATION', name: translateText('Oxygen Saturation'), unit: '%', color: '#3F51B5', chartType: 'line' },
        { id: 'WEIGHT', name: translateText('Weight'), unit: 'kg', color: '#607D8B', chartType: 'line' },
        { id: 'BREATHING_RATE', name: translateText('Breathing Rate'), unit: 'resp/min', color: '#00BCD4', chartType: 'line' },
        { id: 'TEMPERATURE_CORE', name: translateText('Core Temperature'), unit: '°C', color: '#FF9800', chartType: 'line' },
        { id: 'TEMPERATURE_SKIN', name: translateText('Skin Temperature'), unit: '°C', color: '#FF9800', chartType: 'line' },
        // Physical activity parameters
        { id: 'STEPS', name: translateText('Steps'), unit: translateText('steps'), color: '#2196F3', chartType: 'bar' },
        { id: 'DISTANCE', name: translateText('Distance'), unit: 'km', color: '#4CAF50', chartType: 'bar' },
        { id: 'CALORIES', name: translateText('Calories Burned'), unit: 'kcal', color: '#FF9800', chartType: 'bar' },
        { id: 'ACTIVE_MINUTES', name: translateText('Active Minutes'), unit: 'min', color: '#9C27B0', chartType: 'bar' },
        { id: 'SLEEP_DURATION', name: translateText('Sleep Duration'), unit: translateText('hours'), color: '#3F51B5', chartType: 'bar' },
        { id: 'FLOORS_CLIMBED', name: translateText('Floors Climbed'), unit: translateText('floors'), color: '#795548', chartType: 'bar' },
        { id: 'ELEVATION', name: translateText('Elevation'), unit: 'm', color: '#795548', chartType: 'bar' },
        // Metabolism and detailed activity
        { id: 'ACTIVITY_CALORIES', name: translateText('Activity Calories'), unit: 'kcal', color: '#FF5722', chartType: 'bar' },
        { id: 'CALORIES_BMR', name: translateText('Basal Metabolism'), unit: 'kcal', color: '#FF5722', chartType: 'line' },
        { id: 'MINUTES_SEDENTARY', name: translateText('Sedentary Time'), unit: 'min', color: '#9E9E9E', chartType: 'bar' },
        { id: 'MINUTES_LIGHTLY_ACTIVE', name: translateText('Light Activity'), unit: 'min', color: '#8BC34A', chartType: 'bar' },
        { id: 'MINUTES_FAIRLY_ACTIVE', name: translateText('Moderate Activity'), unit: 'min', color: '#FFC107', chartType: 'bar' },
        // Nutrition and hydration
        { id: 'CALORIES_IN', name: translateText('Calories Intake'), unit: 'kcal', color: '#F44336', chartType: 'bar' },
        { id: 'WATER', name: translateText('Water Consumption'), unit: 'ml', color: '#03A9F4', chartType: 'bar' }
    ]
};
let currentPeriod = 7; // Default: 7 days
let activeCharts = {}; // Stores references to active charts
let currentPlatform = null; // Currently connected platform
let currentVitalType = null; // Currently displayed vital parameter type
/**
 * Initializes the charts and related events
 */
function initVitalsCharts() {
    console.log(translateText('Initializing vital parameters charts'));
    // Get period from URL parameters or use default
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('period')) {
        currentPeriod = parseInt(urlParams.get('period')) || 7;
    }
    // Update all report links with the current period at initialization
    updateAllReportLinks();
    // Handle period button clicks
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(btn => {
        const period = parseInt(btn.getAttribute('data-period'));
        // Set the active button based on current period
        if (period === currentPeriod) {
            btn.classList.remove('btn-light');
            btn.classList.add('btn-primary', 'active');
        }
        // Add event listener
        btn.addEventListener('click', function () {
            // Update button styles
            periodButtons.forEach(b => {
                b.classList.remove('btn-primary', 'active');
                b.classList.add('btn-light');
            });
            this.classList.remove('btn-light');
            this.classList.add('btn-primary', 'active');
            // Set the new period
            currentPeriod = period;
            // Update all report links with the new period
            updateAllReportLinks();
            // Reload all charts
            reloadAllCharts();
        });
    });
    // Check connection status to load data
    checkPlatformConnection();
}
/**
 * Check if there's an active connection with a health platform
 * Queries the server to determine if the current patient has a connected health platform
 * and updates the UI accordingly
 * 
 * @returns {Promise<string|null>} A promise that resolves to the connected platform name or null if none
 */
function checkPlatformConnection() {
    const patientId = getPatientIdFromUrl();
    if (!patientId) {
        console.error(translateText('Unable to determine patient ID'));
        updateUIForNoConnection();
        return;
    }
    fetch(`/health/check_connection/${patientId}`)
        .then(response => response.json())
        .then(data => {
            if (data.connected) {
                // Save the connected platform
                currentPlatform = data.platform;
                // Update the interface for the connected platform
                updateUIForConnectedPlatform(data.platform);
                // Load available data types for the platform
                loadAvailableDataTypes(data.platform);
            } else {
                // Update the interface for no connection
                updateUIForNoConnection();
            }
        })
        .catch(error => {
            console.error(translateText('Error checking connection') + ':', error);
            updateUIForNoConnection();
        });
}
/**
 * Update the interface when there's no active connection with a health platform
 * Disables period buttons and displays a message to connect a health platform
 */
function updateUIForNoConnection() {
    // Show no data message
    const noDataMessage = document.getElementById('noDataMessage');
    if (noDataMessage) {
        noDataMessage.classList.remove('d-none');
        noDataMessage.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                ${translateText('Connect to a health platform to view vital signs data.')}
            </div>
        `;
    }
    // Update message in the table
    const vitalsTableMessage = document.getElementById('vitalsTableMessage');
    if (vitalsTableMessage) {
        vitalsTableMessage.textContent = translateText('No data available. Connect a health platform.');
    }
    // Hide period buttons container
    try {
        const periodContainer = document.querySelector('.btn-group[role="group"][aria-label="Time Period"]').closest('.mb-4');
        if (periodContainer) {
            periodContainer.classList.add('d-none');
            console.log(translateText('Period hidden: no active connection'));
        }
    } catch (error) {
        console.error(translateText('Error hiding period buttons:'), error);
    }
    // Disable period buttons (for safety)
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(btn => {
        btn.disabled = true;
    });
}
/**
 * Update the interface when there's an active connection with a health platform
 * Enables period buttons, hides the connection message, and loads available data types
 * 
 * @param {string} platform Name of the connected platform (e.g., "FITBIT", "GOOGLE")
 */
function updateUIForConnectedPlatform(platform) {
    try {
        // Show period buttons container
        const periodContainer = document.querySelector('.btn-group[role="group"][aria-label="Time Period"]').closest('.mb-4');
        if (periodContainer) {
            periodContainer.classList.remove('d-none');
            console.log(translateText('Period shown: active connection with'), platform);
        }
    } catch (error) {
        console.error(translateText('Error showing period buttons:'), error);
    }
    // Enable period buttons
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(btn => {
        btn.disabled = false;
    });
    // Hide no data message
    const noDataMessage = document.getElementById('noDataMessage');
    if (noDataMessage) {
        noDataMessage.classList.add('d-none');
    }
}
/**
 * Load available data types for the specified platform
 * Identifies supported data types for the platform and updates the UI tabs
 * 
 * @param {string} platform Platform name (e.g., "FITBIT", "GOOGLE")
 * @throws {Error} If the platform is not supported
 */
function loadAvailableDataTypes(platform) {
    platform = platform.toUpperCase();
    // Check if platform is supported
    if (!SUPPORTED_DATA_TYPES[platform]) {
        console.error(translateText(`Unsupported platform:`) + ` ${platform}`);
        return;
    }
    // Get supported data types for this platform
    const dataTypes = SUPPORTED_DATA_TYPES[platform];
    // Update chart tabs
    updateChartTabs(dataTypes);
    // Load data for first type
    if (dataTypes.length > 0) {
        // Set initial vital parameter type
        currentVitalType = dataTypes[0].id;
        console.log(translateText(`Initial vital type set to:`) + ` ${currentVitalType}`);
        // Load data for the chart
        loadDataForType(dataTypes[0].id);
        // Reload observations with current type filter
        if (typeof loadObservations === 'function') {
            setTimeout(loadObservations, 500);
        }
    }
}
/**
 * Update chart tabs with available data types
 * Creates tab navigation and content containers for each data type
 * 
 * @param {Array<Object>} dataTypes Array of available data types
 * @param {string} dataTypes[].id - Unique identifier for the data type
 * @param {string} dataTypes[].name - Display name of the data type
 */
function updateChartTabs(dataTypes) {
    const tabsContainer = document.getElementById('vitalsChartTabs');
    const tabContent = document.getElementById('vitalsChartTabContent');
    if (!tabsContainer || !tabContent) {
        console.error(translateText('Tab container not found'));
        return;
    }
    // Clear existing tabs
    tabsContainer.innerHTML = '';
    // Clear existing tab content
    // Keep no data message
    const noDataMessage = document.getElementById('noDataMessage');
    tabContent.innerHTML = '';
    if (noDataMessage) {
        tabContent.appendChild(noDataMessage);
    }
    // Create new tabs
    dataTypes.forEach((type, index) => {
        // Create tab
        const tabItem = document.createElement('li');
        tabItem.className = 'nav-item';
        tabItem.setAttribute('role', 'presentation');
        const tabButton = document.createElement('button');
        tabButton.className = `nav-link ${index === 0 ? 'active' : ''}`;
        tabButton.id = `tab-${type.id}`;
        tabButton.setAttribute('data-bs-toggle', 'tab');
        tabButton.setAttribute('data-bs-target', `#chart-tab-${type.id}`);
        tabButton.setAttribute('type', 'button');
        tabButton.setAttribute('role', 'tab');
        tabButton.setAttribute('aria-controls', `chart-tab-${type.id}`);
        tabButton.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
        tabButton.textContent = type.name;
        tabItem.appendChild(tabButton);
        tabsContainer.appendChild(tabItem);
        // Create tab content
        const tabPane = document.createElement('div');
        tabPane.className = `tab-pane fade ${index === 0 ? 'show active' : ''}`;
        tabPane.id = `chart-tab-${type.id}`;
        tabPane.setAttribute('role', 'tabpanel');
        tabPane.setAttribute('aria-labelledby', `tab-${type.id}`);
        const chartContainer = document.createElement('div');
        chartContainer.className = 'vitals-chart-container';
        chartContainer.style.height = '400px';
        chartContainer.style.position = 'relative';
        const canvas = document.createElement('canvas');
        canvas.id = `chart-${type.id}`;
        chartContainer.appendChild(canvas);
        tabPane.appendChild(chartContainer);
        tabContent.appendChild(tabPane);
    });
    // Add event listeners for tabs
    const tabButtons = tabsContainer.querySelectorAll('.nav-link');
    tabButtons.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            const typeId = event.target.id.replace('tab-', '');
            // Update current vital parameter type
            // Ensure it's always a string
            currentVitalType = typeId;
            console.log(translateText(`Current vital type set to:`) + ` ${currentVitalType}`);
            // Load data for the chart
            loadDataForType(typeId);
            // Reload observations with updated filter (if function exists)
            if (typeof loadObservations === 'function') {
                console.log(translateText('Reloading observations with filter on current vital type'));
                loadObservations();
            }
        });
    });
}
/**
 * Load data for specific type and display on chart
 * Fetches data from the API for the specified type and time period,
 * then updates both the chart and data table
 * 
 * @param {string} typeId Data type ID (e.g., "heart_rate", "steps")
 */
function loadDataForType(typeId) {
    const patientId = getPatientIdFromUrl();
    if (!patientId || !typeId) {
        console.error(translateText('Unable to determine patient ID or data type'));
        return;
    }
    // Show loading indicator
    showChartLoading(typeId);
    // Calculate start and end dates based on current period
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - currentPeriod);
    // Format dates for API
    const startDateStr = formatDateForAPI(startDate);
    const endDateStr = formatDateForAPI(endDate);
    // Build API URL
    const apiUrl = `/health/data/${typeId}/${patientId}?start_date=${startDateStr}&end_date=${endDateStr}`;
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            // Update chart with data
            updateChart(typeId, data);
            // Update data table
            updateDataTable(typeId, data);
        })
        .catch(error => {
            console.error(translateText(`Error loading data for`) + ` ${typeId}:`, error);
            showChartError(typeId);
        });
}
/**
 * Reload all active charts
 * Identifies the currently active tab/chart and reloads its data
 * Also triggers observation reload if that function is available
 */
function reloadAllCharts() {
    // Find the active tab
    const activeTab = document.querySelector('#vitalsChartTabs .nav-link.active');
    if (activeTab) {
        const typeId = activeTab.id.replace('tab-', '');
        // Update current vital parameter type
        // Ensure it's always a string
        currentVitalType = typeId;
        // Load data for the chart
        loadDataForType(typeId);
        // Reload observations with current type filter
        if (typeof loadObservations === 'function') {
            setTimeout(loadObservations, 500);
        }
    }
}
/**
 * Show loading indicator on chart
 * Creates or displays a loading overlay with spinner on the chart container
 * 
 * @param {string} typeId Data type ID to identify which chart to show loading on
 */
function showChartLoading(typeId) {
    const chartContainer = document.querySelector(`#chart-tab-${typeId} .vitals-chart-container`);
    if (!chartContainer) return;
    // Add loading overlay
    let loadingOverlay = chartContainer.querySelector('.chart-loading-overlay');
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'chart-loading-overlay';
        loadingOverlay.style.position = 'absolute';
        loadingOverlay.style.top = '0';
        loadingOverlay.style.left = '0';
        loadingOverlay.style.width = '100%';
        loadingOverlay.style.height = '100%';
        loadingOverlay.style.backgroundColor = 'transparent';
        loadingOverlay.style.display = 'flex';
        loadingOverlay.style.justifyContent = 'center';
        loadingOverlay.style.alignItems = 'center';
        loadingOverlay.style.zIndex = '10';
        loadingOverlay.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary mb-2" role="status">
                    <span class="visually-hidden">${translateText('Loading...')}</span>
                </div>
                <p class="mb-0">${translateText('Loading data...')}</p>
            </div>
        `;
        chartContainer.appendChild(loadingOverlay);
    } else {
        loadingOverlay.style.display = 'flex';
    }
}
/**
 * Show error on chart
 * Removes loading indicator and creates an error overlay with a retry button
 * 
 * @param {string} typeId Data type ID to identify which chart to show error on
 */
function showChartError(typeId) {
    const chartContainer = document.querySelector(`#chart-tab-${typeId} .vitals-chart-container`);
    if (!chartContainer) return;
    // Remove loading overlay
    const loadingOverlay = chartContainer.querySelector('.chart-loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
    // Add error overlay
    let errorOverlay = chartContainer.querySelector('.chart-error-overlay');
    if (!errorOverlay) {
        errorOverlay = document.createElement('div');
        errorOverlay.className = 'chart-error-overlay';
        errorOverlay.style.position = 'absolute';
        errorOverlay.style.top = '0';
        errorOverlay.style.left = '0';
        errorOverlay.style.width = '100%';
        errorOverlay.style.height = '100%';
        errorOverlay.style.backgroundColor = 'transparent';
        errorOverlay.style.display = 'flex';
        errorOverlay.style.justifyContent = 'center';
        errorOverlay.style.alignItems = 'center';
        errorOverlay.style.zIndex = '10';
        errorOverlay.innerHTML = `
            <div class="text-center">
                <i class="fas fa-exclamation-circle text-danger fa-3x mb-3"></i>                <p class="mb-0">${translateText('Error loading data. Try again later.')}</p>
                <button class="btn btn-outline-primary mt-3 retry-btn">
                    <i class="fas fa-sync me-1"></i> ${translateText('Retry')}
                </button>
            </div>
        `;
        chartContainer.appendChild(errorOverlay);
        // Add event listener for the retry button
        const retryBtn = errorOverlay.querySelector('.retry-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', function() {
                loadDataForType(typeId);
            });
        }
    } else {
        errorOverlay.style.display = 'flex';
    }
}
/**
 * Update the chart with received data
 * Finds the data type information, removes loading/error overlays,
 * and creates or updates the chart with the received data
 * 
 * @param {string} typeId ID of the data type
 * @param {Array<Object>} data Data received from the API
 * @param {string} data[].timestamp - Timestamp of the measurement
 * @param {number} data[].value - Value of the measurement
 */
function updateChart(typeId, data) {
    // Find information about the data type
    let typeInfo = null;
    for (const platform in SUPPORTED_DATA_TYPES) {
        const types = SUPPORTED_DATA_TYPES[platform];
        const found = types.find(t => t.id === typeId);
        if (found) {
            typeInfo = found;
            break;
        }
    }
    if (!typeInfo) {
        console.error(translateText(`Unsupported data type:`) + ` ${typeId}`);
        return;
    }
    // Remove loading overlay
    const chartContainer = document.querySelector(`#chart-tab-${typeId} .vitals-chart-container`);
    if (chartContainer) {
        const loadingOverlay = chartContainer.querySelector('.chart-loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
        const errorOverlay = chartContainer.querySelector('.chart-error-overlay');
        if (errorOverlay) {
            errorOverlay.style.display = 'none';
        }
    }
    // Prepare data for the chart
    const chartData = prepareChartData(data, typeInfo);
    // Update or create the chart
    updateOrCreateChart(typeId, chartData, typeInfo);
}
/**
 * Prepare data for the chart
 * Generate an array of dates for the selected period, even if there's no data for all dates.
 * Maps API data to a consistent format for Chart.js with proper handling of missing values.
 * 
 * @param {Array<Object>} data Data received from the API
 * @param {string} data[].timestamp - Timestamp of the measurement
 * @param {number} data[].value - Value of the measurement
 * @param {Object} typeInfo Information about the data type
 * @param {string} typeInfo.name - Display name of the data type
 * @param {string} typeInfo.unit - Unit of measurement
 * @param {string} typeInfo.color - Chart color in hex format
 * @returns {Object} Data formatted for Chart.js
 */
function prepareChartData(data, typeInfo) {
    // Generate array of dates for the selected period
    const today = new Date();
    const startDate = new Date();
    startDate.setDate(today.getDate() - currentPeriod);
    // Create array with all dates in the period
    const allDates = [];
    const allLabels = [];
    const currentDate = new Date(startDate);
    // Add all dates from start period to today
    while (currentDate <= today) {
        allDates.push(new Date(currentDate));
        allLabels.push(formatTimestamp(currentDate));
        currentDate.setDate(currentDate.getDate() + 1);
    }
    // If data is empty, return an empty dataset but with dates for the period
    if (!data || !data.length) {
        // Create array of null values for all dates
        const emptyValues = allDates.map(() => null);
        return {
            labels: allLabels,
            datasets: [{
                label: `${typeInfo.name} (${typeInfo.unit})`,
                data: emptyValues,
                borderColor: typeInfo.color,
                backgroundColor: `${typeInfo.color}33`, // Color with 0.2 opacity
                fill: true,
                tension: 0.4
            }]
        };
    }
    // Sort data by timestamp
    data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    // Create a mapping of data by date
    const dataByDate = {};
    data.forEach(item => {
        const date = new Date(item.timestamp);
        const dateKey = formatDateForAPI(date);
        dataByDate[dateKey] = item.value;
    });
    // Prepare values for all dates in the period
    // Important: if the value is 0, it should be displayed as 0 and not as null
    const values = allDates.map(date => {
        const dateKey = formatDateForAPI(date);
        return dataByDate[dateKey] !== undefined ? dataByDate[dateKey] : null;
    });
    return {
        labels: allLabels,
        datasets: [{
            label: `${typeInfo.name} (${typeInfo.unit})`,
            data: values,
            borderColor: typeInfo.color,
            backgroundColor: `${typeInfo.color}33`, // Color with 0.2 opacity
            fill: true,
            tension: 0.4,
            // Important: allow line display even with null/missing values
            spanGaps: true
        }]
    };
}
/**
 * Update or create a chart
 * Creates a new Chart.js instance or updates an existing one with new data
 * 
 * @param {string} typeId Data type ID
 * @param {Object} chartData Data formatted for Chart.js
 * @param {Array<string>} chartData.labels - Labels for the X axis (dates)
 * @param {Array<Object>} chartData.datasets - Dataset configurations
 * @param {Object} typeInfo Information about the data type
 * @param {string} typeInfo.name - Display name of the data type
 * @param {string} typeInfo.unit - Unit of measurement
 */
function updateOrCreateChart(typeId, chartData, typeInfo) {
    const canvas = document.getElementById(`chart-${typeId}`);
    if (!canvas) {
        console.error(translateText(`Canvas not found for chart ${typeId}`));
        return;
    }
    // Destroy existing chart if present
    if (activeCharts[typeId]) {
        activeCharts[typeId].destroy();
    }
    // Create a new chart
    activeCharts[typeId] = new Chart(canvas, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${typeInfo.name} - ${translateText('Last')} ${currentPeriod} ${translateText(currentPeriod === 1 ? 'day' : 'days')}`,
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: translateText('Date')
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: typeInfo.unit
                    },
                    min: 0
                }
            }
        }
    });
}
/**
 * Update the data table in "Vital Parameters History"
 * Shows only data of currently selected type, to sync with chart.
 * Sorts data by timestamp (newest first) and limits to 50 entries for performance.
 * 
 * @param {string} typeId Data type ID
 * @param {Array<Object>} data Data received from API
 * @param {string} data[].timestamp - Timestamp of the measurement
 * @param {number} data[].value - Value of the measurement
 */
function updateDataTable(typeId, data) {
    const tableBody = document.querySelector('#vitalsDataTable tbody');
    const noDataRow = document.getElementById('noVitalsDataRow');
    if (!tableBody) {
        console.error(translateText('Data table body not found'));
        return;
    }
    // Find information about data type
    let typeInfo = null;
    for (const platform in SUPPORTED_DATA_TYPES) {
        const types = SUPPORTED_DATA_TYPES[platform];
        const found = types.find(t => t.id === typeId);
        if (found) {
            typeInfo = found;
            break;
        }
    }
    if (!typeInfo) {
        console.error(translateText(`Unsupported data type: ${typeId}`));
        return;
    }
    // If data is empty, show a message
    if (!data || !data.length) {
        if (noDataRow) {
            const message = document.getElementById('vitalsTableMessage');
            if (message) {
                message.textContent = translateText(`No data available for`) + ` ${typeInfo.name.toLowerCase()}`;
            }
            noDataRow.style.display = 'table-row';
        }
        // Remove all existing rows
        const existingRows = tableBody.querySelectorAll('tr:not(#noVitalsDataRow)');
        existingRows.forEach(row => row.remove());
        return;
    }
    // Hide no data row
    if (noDataRow) {
        noDataRow.style.display = 'none';
    }
    // Sort data by timestamp (most recent first)
    data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    // Limit to 50 rows to prevent browser slowdown
    const maxRows = 50;
    const limitedData = data.slice(0, maxRows);
    // Create table rows
    const rows = limitedData.map(item => {
        const date = new Date(item.timestamp);
        const formattedDate = date.toLocaleString();
        return `
            <tr>
                <td>
                    <span class="badge bg-info text-dark">
                        ${typeInfo.name}
                    </span>
                </td>
                <td>
                    <strong>${item.value}</strong>
                    <small class="text-muted">${typeInfo.unit}</small>
                </td>
                <td>${formattedDate}</td>
                <td>
                    <span class="badge bg-primary">
                        ${currentPlatform ? currentPlatform.charAt(0).toUpperCase() + currentPlatform.slice(1) : 'Device'}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
    // Remove all existing rows and add new ones
    const existingRows = tableBody.querySelectorAll('tr:not(#noVitalsDataRow)');
    existingRows.forEach(row => row.remove());
    tableBody.insertAdjacentHTML('afterbegin', rows);
}
/**
 * Format a date for API (YYYY-MM-DD)
 * @param {Date} date Date to format
 * @returns {string} Formatted date
 */
function formatDateForAPI(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}
/**
 * Format a timestamp for chart labels
 * @param {string} timestamp Timestamp in ISO format
 * @returns {string} Formatted date
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    // If the period is 1 day, show only the time
    if (currentPeriod === 1) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    // Otherwise show the date
    return date.toLocaleDateString();
}
/**
 * Handle click on the button to generate a specific report
 * Redirects to the URL to generate PDF with current vital type and period
 */
function setupSpecificReportButton() {
    const reportBtn = document.getElementById('generateSpecificReportBtn');
    if (!reportBtn) return;
    reportBtn.addEventListener('click', function (e) {
        e.preventDefault();
        // Check that there is a currently selected vital type
        if (!currentVitalType) {
            alert(translateText('Please select a vital sign type first.'));
            return;
        }
        // Extract the vital type ID if necessary
        let vitalTypeId = currentVitalType;
        if (typeof currentVitalType === 'object' && currentVitalType !== null && currentVitalType.id) {
            vitalTypeId = currentVitalType.id;
        }
        // Create the URL for the specific report
        const reportUrl = `${BASE_URL}patients/${PATIENT_ID}/specific_report?vital_type=${vitalTypeId}&period=${currentPeriod}`;
        // Open the URL in a new window/tab
        window.open(reportUrl, '_blank');
    });
}
/**
 * Update all report links with the current period
 */
function updateAllReportLinks() {
    // Update complete report link
    const completeReportLink = document.querySelector('a[href*="select_all=true"]');
    if (completeReportLink) {
        const patientId = getPatientIdFromUrl();
        if (patientId) {
            completeReportLink.href = `/patients/${patientId}/specific_report?select_all=true&period=${currentPeriod}`;
        }
    }
    // Update all links for parameter-specific reports
    const vitalReportLinks = document.querySelectorAll('.vital-report-link');
    if (vitalReportLinks && vitalReportLinks.length > 0) {
        vitalReportLinks.forEach(link => {
            const vitalType = link.getAttribute('data-vital-type');
            if (vitalType) {
                const patientId = getPatientIdFromUrl();
                if (patientId) {
                    link.href = `/patients/${patientId}/specific_report?vital_type=${vitalType}&period=${currentPeriod}`;
                }
            }
        });
    }
}
/**
 * Find information for a vital parameter type
 * @param {string} vitalType ID of the vital parameter type
 * @returns {Object} Information about the vital parameter type
 */
function findVitalTypeInfo(vitalType) {
    if (currentPlatform && SUPPORTED_DATA_TYPES[currentPlatform]) {
        return SUPPORTED_DATA_TYPES[currentPlatform].find(type => type.id === vitalType);
    }
    return null;
}
// Initialize charts when document is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Initialize global variables
    console.log(translateText('Initializing global variables...'));
    // Initialize charts
    console.log(translateText('Starting initVitalsCharts...'));
    initVitalsCharts();
    console.log(translateText('Status after initVitalsCharts:'), {
        currentPeriod,
        currentPlatform,
        currentVitalType
    });
    // Initialize observations module after charts
    if (typeof initObservations === 'function') {
        console.log(translateText('Starting initObservations...'));
        initObservations();
        console.log(translateText('Status after initObservations:'), {
            currentPeriod,
            currentPlatform,
            currentVitalType
        });
    }
    // Initialize specific report button
    setupSpecificReportButton();
});