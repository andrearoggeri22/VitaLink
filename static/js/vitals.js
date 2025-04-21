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
    // Check if the vitals data container exists
    const vitalsDataContainer = document.getElementById('vitalsData');
    
    if (!vitalsDataContainer) return;
    
    // Get vital signs data from the data container
    let vitalsData;
    try {
        vitalsData = JSON.parse(vitalsDataContainer.getAttribute('data-vitals'));
    } catch (error) {
        console.error('Error parsing vital signs data:', error);
        return;
    }
    
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
                                return formatDate(tooltipItems[0].raw.x);
                            }
                        }
                    }
                }
            }
        });
    }
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
