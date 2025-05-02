/**
 * vitals.js - JavaScript for vital signs functionality
 * 
 * This file provides functionality for managing, displaying, and filtering vital signs data
 * including charts visualization, form handling, and data filtering.
 */

/**
 * Initialize all vital signs components when the DOM is fully loaded
 * 
 * This event handler serves as the main entry point for the vital signs functionality.
 * It initializes the form, charts, and filter components in the correct sequence.
 * 
 * @listens DOMContentLoaded
 */
document.addEventListener('DOMContentLoaded', function () {
    // Initialize the vital signs form
    initVitalsForm();

    // Initialize charts for vital signs visualization
    initVitalsCharts();

    // Initialize filter functionality
    initVitalsFilter();
});

/**
 * Initialize the functionality of the vital signs form
 * 
 * Sets up unit auto-selection based on the selected vital sign type and 
 * implements form validation. The function automatically updates the unit field
 * when a user selects a different vital sign type.
 *
 * @returns {void}
 */
function initVitalsForm() {
    const vitalsForm = document.getElementById('vitalsForm');

    if (vitalsForm) {
        // Update units based on the selected vital sign type
        const typeSelect = document.getElementById('vitalType');
        const unitInput = document.getElementById('vitalUnit');
        if (typeSelect && unitInput) {
            const units = {
                // Main vital parameters
                'heart_rate': 'bpm',
                'oxygen_saturation': '%',
                'breathing_rate': 'resp/min',
                'weight': 'kg',
                'temperature_core': '°C',
                'temperature_skin': '°C',

                // Physical activity parameters
                'steps': translateText('steps'),
                'calories': 'kcal',
                'distance': 'km',
                'active_minutes': translateText('min'),
                'sleep_duration': translateText('hours'),
                'floors_climbed': translateText('floors'),
                'elevation': 'm',

                // Metabolism and detailed activity parameters
                'activity_calories': 'kcal',
                'calories_bmr': 'kcal',
                'minutes_sedentary': translateText('min'),
                'minutes_lightly_active': translateText('min'),
                'minutes_fairly_active': translateText('min'),

                // Nutrition and hydration
                'calories_in': 'kcal',
                'water': 'ml'
            };


            // Set initial unit
            if (typeSelect.value) {
                unitInput.value = units[typeSelect.value] || '';
            }

            // Update unit on type change
            typeSelect.addEventListener('change', function () {
                unitInput.value = units[this.value] || '';
            });
        }

        // Form validation
        vitalsForm.addEventListener('submit', function (event) {
            if (!vitalsForm.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            vitalsForm.classList.add('was-validated');
        });
    }
}

/**
 * Initialize charts for vital signs visualization
 * 
 * Fetches vital signs data from the API based on URL parameters (patient ID, date range, type),
 * and creates interactive line charts for each vital sign type using Chart.js.
 * Each chart displays the recorded values over time with appropriate formatting and units.
 * 
 * @returns {void}
 */
function initVitalsCharts() {
    // Check if we are on the vital parameters page
    const patientIdMatch = window.location.pathname.match(/\/patients\/(\d+)\/vitals/);
    if (!patientIdMatch) return;

    const patientId = patientIdMatch[1];

    // Extract filter parameters from URL
    const urlParams = new URLSearchParams(window.location.search);
    const startDate = urlParams.get('start_date');
    const endDate = urlParams.get('end_date');
    const vitalType = urlParams.get('type');

    // Build API URL with filter parameters
    let apiUrl = `/api/patients/${patientId}/vitals`;
    const apiParams = [];

    if (startDate) apiParams.push(`start_date=${startDate}`);
    if (endDate) apiParams.push(`end_date=${endDate}`);
    if (vitalType) apiParams.push(`type=${vitalType}`);

    if (apiParams.length > 0) {
        apiUrl += `?${apiParams.join('&')}`;
    }

    // Get data via API
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(translateText('Network response was not ok'));
            }
            return response.json();
        })
        .then(vitalsData => {
            // Create charts for each vital sign type
            for (const [type, values] of Object.entries(vitalsData)) {
                if (!values || values.length === 0) continue;

                const canvasId = `chart-${type}`;

                // Check if canvas element exists
                const canvas = document.getElementById(canvasId);
                if (!canvas) continue;

                // Prepare data for the chart
                const labels = values.map(v => new Date(v.recorded_at || v.timestamp));
                const data = values.map(v => v.value);
                const unit = values[0].unit || '';

                // Format type name for display
                const typeDisplay = type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

                // Create the chart
                new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: `${typeDisplay} (${unit})`,
                            data: data,
                            borderColor: getRandomColor(),
                            backgroundColor: 'rgba(0, 0, 0, 0.1)',
                            borderWidth: 2,
                            tension: 0.1,
                            pointRadius: 3,
                            pointHoverRadius: 5
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    unit: 'day',
                                    displayFormats: {
                                        day: 'MMM d'
                                    }
                                },
                                title: {
                                    display: true,
                                    text: translateText('Data')
                                }
                            },
                            y: {
                                beginAtZero: false,
                                title: {
                                    display: true,
                                    text: unit
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top'
                            },
                            tooltip: {
                                callbacks: {
                                    title: function (tooltipItems) {
                                        if (tooltipItems && tooltipItems[0]) {
                                            const value = tooltipItems[0].parsed ?
                                                tooltipItems[0].parsed.x :
                                                (tooltipItems[0].raw ? tooltipItems[0].raw : tooltipItems[0].label);
                                            return formatDate(value);
                                        }
                                        return '';
                                    }
                                }
                            }
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.error(translateText('Error fetching vital signs data:'), error);
        });
}

/**
 * Display a message when no data is available for a chart
 * 
 * Removes any existing chart from the canvas, hides the canvas element,
 * and displays a user-friendly message in its place. This provides feedback
 * to the user when no data is available for visualization.
 * 
 * @param {HTMLCanvasElement} canvas - The canvas element where the chart would be displayed
 * @param {string} message - The message to display to the user
 * @returns {void}
 */
function displayNoDataMessage(canvas, message) {
    // Remove any existing chart
    if (Chart.getChart(canvas)) {
        Chart.getChart(canvas).destroy();
    }

    // Get the canvas container
    const container = canvas.parentElement;

    // Create a message element
    const messageElement = document.createElement('div');
    messageElement.className = 'no-data-message';
    messageElement.textContent = message;
    messageElement.style.textAlign = 'center';
    messageElement.style.padding = '20px';
    messageElement.style.color = '#666';
    messageElement.style.fontStyle = 'italic';

    // Hide the canvas and add the message
    canvas.style.display = 'none';
    container.appendChild(messageElement);
}

/**
 * Initialize the filter functionality for vital signs
 * 
 * Sets up the date range filter form with validation logic to ensure
 * that the start date is not after the end date and vice versa.
 * Also sets the maximum selectable date to the current date to prevent
 * future date selection.
 * 
 * @returns {void}
 */
function initVitalsFilter() {
    const filterForm = document.getElementById('vitalsFilterForm');
    if (filterForm) {
        // Set the maximum date for date inputs to today
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');

        if (startDateInput && endDateInput) {
            const today = new Date().toISOString().split('T')[0];

            startDateInput.setAttribute('max', today);
            endDateInput.setAttribute('max', today);

            // Ensure start date is not after end date
            startDateInput.addEventListener('change', function () {
                if (endDateInput.value && this.value > endDateInput.value) {
                    endDateInput.value = this.value;
                }
            });

            // Ensure end date is not before start date
            endDateInput.addEventListener('change', function () {
                if (startDateInput.value && this.value < startDateInput.value) {
                    startDateInput.value = this.value;
                }
            });
        }
    }
}

/**
 * Format a date object to a readable string
 * 
 * Converts a date object or timestamp string into a localized, human-readable
 * date and time string using the browser's locale settings or the document's
 * language setting. Includes year, month, day, hour, and minute.
 * 
 * @param {Date|string|number} date - Date object or timestamp to format
 * @returns {string} Formatted date string or empty string if input is invalid
 * @example
 * // Returns "May 2, 2025, 10:30 AM" (format depends on locale)
 * formatDate(new Date(2025, 4, 2, 10, 30));
 */
function formatDate(date) {
    if (!date) return '';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(date).toLocaleDateString(document.documentElement.lang || 'en', options);
}

/**
 * Generate a random color for charts
 * 
 * Returns a random color from a predefined palette of visually distinct colors
 * for use in charts and visualizations. The palette includes colors that are
 * accessible and work well together for data visualization.
 * 
 * @returns {string} Hex color code (e.g., "#4285F4")
 * @example
 * // Might return "#4285F4" or any other color from the palette
 * const lineColor = getRandomColor();
 */
function getRandomColor() {
    const colors = [
        '#4285F4', // Blue
        '#34A853', // Green
        '#FBBC05', // Yellow
        '#EA4335', // Red
        '#8AB4F8', // Light blue
        '#137333', // Dark green
        '#F29900', // Orange
        '#9C27B0', // Purple
        '#009688', // Teal
        '#FF5722'  // Deep orange
    ];

    return colors[Math.floor(Math.random() * colors.length)];
}
