// vitals.js - JavaScript for vital signs functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize vital signs form
    initVitalsForm();
    
    // Initialize charts for vital signs visualization
    initVitalsCharts();
    
    // Initialize filter functionality
    initVitalsFilter();
});

/**
 * Initialize vital signs form functionality
 */
function initVitalsForm() {
    const vitalsForm = document.getElementById('vitalsForm');
    
    if (vitalsForm) {
        // Update units based on selected vital sign type
        const typeSelect = document.getElementById('vitalType');
        const unitInput = document.getElementById('vitalUnit');
        
        if (typeSelect && unitInput) {
            const units = {
                'heart_rate': 'bpm',
                'blood_pressure': 'mmHg',
                'oxygen_saturation': '%',
                'temperature': '°C',
                'respiratory_rate': 'breaths/min',
                'glucose': 'mg/dL',
                'weight': 'kg',
                // Nuovi parametri Fitbit
                'steps': 'steps',
                'calories': 'kcal',
                'distance': 'km',
                'active_minutes': 'min',
                'sleep_duration': 'hours',
                'floors_climbed': 'floors'
            };
            
            // Set initial unit
            if (typeSelect.value) {
                unitInput.value = units[typeSelect.value] || '';
            }
            
            // Update unit when type changes
            typeSelect.addEventListener('change', function() {
                unitInput.value = units[this.value] || '';
            });
        }
        
        // Form validation
        vitalsForm.addEventListener('submit', function(event) {
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
 */
function initVitalsCharts() {
    // Controlla se siamo nella pagina dei parametri vitali
    const patientIdMatch = window.location.pathname.match(/\/patients\/(\d+)\/vitals/);
    if (!patientIdMatch) return;
    
    const patientId = patientIdMatch[1];
    
    // Estrai i parametri di filtro dall'URL
    const urlParams = new URLSearchParams(window.location.search);
    const startDate = urlParams.get('start_date');
    const endDate = urlParams.get('end_date');
    const vitalType = urlParams.get('type');
    
    // Costruisci l'URL dell'API con i parametri di filtro
    let apiUrl = `/api/patients/${patientId}/vitals`;
    const apiParams = [];
    
    if (startDate) apiParams.push(`start_date=${startDate}`);
    if (endDate) apiParams.push(`end_date=${endDate}`);
    if (vitalType) apiParams.push(`type=${vitalType}`);
    
    if (apiParams.length > 0) {
        apiUrl += `?${apiParams.join('&')}`;
    }
    
    // Ottieni i dati tramite API
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
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
                const labels = values.map(v => new Date(v.recorded_at));
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
                                    text: 'Date'
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
                                    title: function(tooltipItems) {
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
            console.error('Error fetching vital signs data:', error);
        });
}

/**
 * Initialize filter functionality for vital signs
 */
function initVitalsFilter() {
    const filterForm = document.getElementById('vitalsFilterForm');
    
    if (filterForm) {
        // Set max date for date inputs to today
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        
        if (startDateInput && endDateInput) {
            const today = new Date().toISOString().split('T')[0];
            
            startDateInput.setAttribute('max', today);
            endDateInput.setAttribute('max', today);
            
            // Ensure start date is not after end date
            startDateInput.addEventListener('change', function() {
                if (endDateInput.value && this.value > endDateInput.value) {
                    endDateInput.value = this.value;
                }
            });
            
            // Ensure end date is not before start date
            endDateInput.addEventListener('change', function() {
                if (startDateInput.value && this.value < startDateInput.value) {
                    startDateInput.value = this.value;
                }
            });
        }
    }
}

/**
 * Format a date object to a readable string
 */
function formatDate(date) {
    if (!date) return '';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(date).toLocaleDateString(document.documentElement.lang || 'en', options);
}

/**
 * Generate a random color for charts
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
