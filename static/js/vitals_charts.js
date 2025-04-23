/**
 * Vitals Charts JavaScript
 * 
 * Gestisce la visualizzazione dei grafici delle tendenze dei parametri vitali
 * e la tabella dei dati storici ottenuti dalle piattaforme di salute
 * 
 * Funzionalità:
 * - Caricamento dati dalle API delle piattaforme (Fitbit, ecc.)
 * - Visualizzazione grafici con periodi personalizzabili
 * - Aggiornamento tabella dati storici
 */

// Costanti e variabili globali
const SUPPORTED_DATA_TYPES = {
    FITBIT: [
        { id: 'heart_rate', name: 'Frequenza cardiaca', unit: 'bpm', color: '#FF5252' },
        { id: 'steps', name: 'Passi', unit: 'passi', color: '#2196F3' },
        { id: 'distance', name: 'Distanza', unit: 'km', color: '#4CAF50' },
        { id: 'calories', name: 'Calorie', unit: 'kcal', color: '#FF9800' },
        { id: 'active_minutes', name: 'Minuti attivi', unit: 'min', color: '#9C27B0' },
        { id: 'sleep_duration', name: 'Durata sonno', unit: 'ore', color: '#3F51B5' },
        { id: 'floors_climbed', name: 'Piani saliti', unit: 'piani', color: '#795548' },
        { id: 'weight', name: 'Peso', unit: 'kg', color: '#607D8B' }
    ]
};

let currentPeriod = 7; // Default: 7 giorni
let activeCharts = {}; // Memorizza i riferimenti ai grafici attivi
let currentPlatform = null; // Piattaforma attualmente connessa

/**
 * Inizializza i grafici e gli eventi associati
 */
function initVitalsCharts() {
    console.log('Inizializzazione grafici parametri vitali');
    
    // Recupera il periodo dai parametri URL o usa il default
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('period')) {
        currentPeriod = parseInt(urlParams.get('period')) || 7;
    }
    
    // Gestisce click sui pulsanti del periodo
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(btn => {
        const period = parseInt(btn.getAttribute('data-period'));
        
        // Imposta il pulsante attivo in base al periodo corrente
        if (period === currentPeriod) {
            btn.classList.remove('btn-outline-primary');
            btn.classList.add('btn-primary');
        }
        
        // Aggiungi event listener
        btn.addEventListener('click', function() {
            // Aggiorna lo stile dei pulsanti
            periodButtons.forEach(b => {
                b.classList.remove('btn-primary');
                b.classList.add('btn-outline-primary');
            });
            this.classList.remove('btn-outline-primary');
            this.classList.add('btn-primary');
            
            // Aggiorna il periodo corrente
            currentPeriod = period;
            
            // Ricarica i dati per tutti i grafici attivi
            reloadAllCharts();
        });
    });
    
    // Controlla lo stato della connessione per caricare i dati
    checkPlatformConnection();
}

/**
 * Controlla se è attiva una connessione con una piattaforma
 */
function checkPlatformConnection() {
    const patientId = getPatientIdFromUrl();
    if (!patientId) {
        console.error('Impossibile determinare l\'ID del paziente');
        updateUIForNoConnection();
        return;
    }
    
    fetch(`/health/check_connection/${patientId}`)
        .then(response => response.json())
        .then(data => {
            if (data.connected) {
                // Salva la piattaforma connessa
                currentPlatform = data.platform;
                
                // Aggiorna l'interfaccia per la piattaforma connessa
                updateUIForConnectedPlatform(data.platform);
                
                // Carica i dati disponibili per la piattaforma
                loadAvailableDataTypes(data.platform);
            } else {
                // Aggiorna l'interfaccia per nessuna connessione
                updateUIForNoConnection();
            }
        })
        .catch(error => {
            console.error('Errore nel controllo della connessione:', error);
            updateUIForNoConnection();
        });
}

/**
 * Aggiorna l'interfaccia quando non c'è una connessione attiva
 */
function updateUIForNoConnection() {
    // Mostra il messaggio di nessun dato
    const noDataMessage = document.getElementById('noDataMessage');
    if (noDataMessage) {
        noDataMessage.classList.remove('d-none');
        noDataMessage.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                ${translateText('Collegati ad una piattaforma di salute per visualizzare i dati dei parametri vitali.')}
            </div>
        `;
    }
    
    // Aggiorna il messaggio nella tabella
    const vitalsTableMessage = document.getElementById('vitalsTableMessage');
    if (vitalsTableMessage) {
        vitalsTableMessage.textContent = translateText('Nessun dato disponibile. Collega una piattaforma di salute.');
    }
    
    // Disabilita i pulsanti del periodo
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(btn => {
        btn.disabled = true;
    });
}

/**
 * Aggiorna l'interfaccia quando c'è una connessione attiva
 * @param {string} platform Nome della piattaforma connessa
 */
function updateUIForConnectedPlatform(platform) {
    // Abilita i pulsanti del periodo
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(btn => {
        btn.disabled = false;
    });
    
    // Nascondi il messaggio di nessun dato
    const noDataMessage = document.getElementById('noDataMessage');
    if (noDataMessage) {
        noDataMessage.classList.add('d-none');
    }
}

/**
 * Carica i tipi di dati disponibili per la piattaforma specificata
 * @param {string} platform Nome della piattaforma
 */
function loadAvailableDataTypes(platform) {
    platform = platform.toUpperCase();
    
    // Controlla se la piattaforma è supportata
    if (!SUPPORTED_DATA_TYPES[platform]) {
        console.error(`Piattaforma non supportata: ${platform}`);
        return;
    }
    
    // Recupera i tipi di dati supportati per questa piattaforma
    const dataTypes = SUPPORTED_DATA_TYPES[platform];
    
    // Aggiorna le tab per i grafici
    updateChartTabs(dataTypes);
    
    // Carica i dati per il primo tipo
    if (dataTypes.length > 0) {
        loadDataForType(dataTypes[0].id);
    }
}

/**
 * Aggiorna le schede dei grafici con i tipi di dati disponibili
 * @param {Array} dataTypes Array di tipi di dati disponibili
 */
function updateChartTabs(dataTypes) {
    const tabsContainer = document.getElementById('vitalsChartTabs');
    const tabContent = document.getElementById('vitalsChartTabContent');
    
    if (!tabsContainer || !tabContent) {
        console.error('Container delle tab non trovato');
        return;
    }
    
    // Pulisci le tab esistenti
    tabsContainer.innerHTML = '';
    
    // Pulisci il contenuto delle tab esistenti
    // Mantieni il messaggio di nessun dato
    const noDataMessage = document.getElementById('noDataMessage');
    tabContent.innerHTML = '';
    if (noDataMessage) {
        tabContent.appendChild(noDataMessage);
    }
    
    // Crea le nuove tab
    dataTypes.forEach((type, index) => {
        // Crea la tab
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
        
        // Crea il contenuto della tab
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
    
    // Aggiungi event listener per le tab
    const tabButtons = tabsContainer.querySelectorAll('.nav-link');
    tabButtons.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const typeId = event.target.id.replace('tab-', '');
            loadDataForType(typeId);
        });
    });
}

/**
 * Carica i dati per un tipo specifico e li visualizza nel grafico
 * @param {string} typeId ID del tipo di dati
 */
function loadDataForType(typeId) {
    const patientId = getPatientIdFromUrl();
    if (!patientId || !typeId) {
        console.error('Impossibile determinare l\'ID del paziente o il tipo di dati');
        return;
    }
    
    // Mostra indicatore di caricamento
    showChartLoading(typeId);
    
    // Calcola date di inizio e fine in base al periodo corrente
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - currentPeriod);
    
    // Formato date per l'API
    const startDateStr = formatDateForAPI(startDate);
    const endDateStr = formatDateForAPI(endDate);
    
    // Costruisci l'URL dell'API
    const apiUrl = `/health/data/${typeId}/${patientId}?start_date=${startDateStr}&end_date=${endDateStr}`;
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            // Aggiorna il grafico con i dati
            updateChart(typeId, data);
            
            // Aggiorna la tabella dei dati
            updateDataTable(typeId, data);
        })
        .catch(error => {
            console.error(`Errore nel caricamento dei dati per ${typeId}:`, error);
            showChartError(typeId);
        });
}

/**
 * Ricarica tutti i grafici attivi
 */
function reloadAllCharts() {
    // Trova la tab attiva
    const activeTab = document.querySelector('#vitalsChartTabs .nav-link.active');
    if (activeTab) {
        const typeId = activeTab.id.replace('tab-', '');
        loadDataForType(typeId);
    }
}

/**
 * Mostra indicatore di caricamento nel grafico
 * @param {string} typeId ID del tipo di dati
 */
function showChartLoading(typeId) {
    const chartContainer = document.querySelector(`#chart-tab-${typeId} .vitals-chart-container`);
    if (!chartContainer) return;
    
    // Aggiungi overlay di caricamento
    let loadingOverlay = chartContainer.querySelector('.chart-loading-overlay');
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'chart-loading-overlay';
        loadingOverlay.style.position = 'absolute';
        loadingOverlay.style.top = '0';
        loadingOverlay.style.left = '0';
        loadingOverlay.style.width = '100%';
        loadingOverlay.style.height = '100%';
        loadingOverlay.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        loadingOverlay.style.display = 'flex';
        loadingOverlay.style.justifyContent = 'center';
        loadingOverlay.style.alignItems = 'center';
        loadingOverlay.style.zIndex = '10';
        
        loadingOverlay.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary mb-2" role="status">
                    <span class="visually-hidden">Caricamento...</span>
                </div>
                <p class="mb-0">${translateText('Caricamento dati...')}</p>
            </div>
        `;
        
        chartContainer.appendChild(loadingOverlay);
    } else {
        loadingOverlay.style.display = 'flex';
    }
}

/**
 * Mostra errore nel grafico
 * @param {string} typeId ID del tipo di dati
 */
function showChartError(typeId) {
    const chartContainer = document.querySelector(`#chart-tab-${typeId} .vitals-chart-container`);
    if (!chartContainer) return;
    
    // Rimuovi overlay di caricamento
    const loadingOverlay = chartContainer.querySelector('.chart-loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
    
    // Aggiungi overlay di errore
    let errorOverlay = chartContainer.querySelector('.chart-error-overlay');
    if (!errorOverlay) {
        errorOverlay = document.createElement('div');
        errorOverlay.className = 'chart-error-overlay';
        errorOverlay.style.position = 'absolute';
        errorOverlay.style.top = '0';
        errorOverlay.style.left = '0';
        errorOverlay.style.width = '100%';
        errorOverlay.style.height = '100%';
        errorOverlay.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        errorOverlay.style.display = 'flex';
        errorOverlay.style.justifyContent = 'center';
        errorOverlay.style.alignItems = 'center';
        errorOverlay.style.zIndex = '10';
        
        errorOverlay.innerHTML = `
            <div class="text-center">
                <i class="fas fa-exclamation-circle text-danger fa-3x mb-3"></i>
                <p class="mb-0">${translateText('Errore nel caricamento dei dati. Riprova più tardi.')}</p>
                <button class="btn btn-outline-primary mt-3 retry-btn">
                    <i class="fas fa-sync me-1"></i> ${translateText('Riprova')}
                </button>
            </div>
        `;
        
        chartContainer.appendChild(errorOverlay);
        
        // Aggiungi event listener per il pulsante di ripetizione
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
 * Aggiorna il grafico con i dati ricevuti
 * @param {string} typeId ID del tipo di dati
 * @param {Array} data Dati ricevuti dall'API
 */
function updateChart(typeId, data) {
    // Trova le informazioni sul tipo di dati
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
        console.error(`Tipo di dati non supportato: ${typeId}`);
        return;
    }
    
    // Rimuovi overlay di caricamento
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
    
    // Prepara i dati per il grafico
    const chartData = prepareChartData(data, typeInfo);
    
    // Aggiorna o crea il grafico
    updateOrCreateChart(typeId, chartData, typeInfo);
}

/**
 * Prepara i dati per il grafico
 * @param {Array} data Dati ricevuti dall'API
 * @param {Object} typeInfo Informazioni sul tipo di dati
 * @returns {Object} Dati formattati per Chart.js
 */
function prepareChartData(data, typeInfo) {
    // Se i dati sono vuoti, restituisci un set di dati vuoto
    if (!data || !data.length) {
        return {
            labels: [],
            datasets: [{
                label: typeInfo.name,
                data: [],
                borderColor: typeInfo.color,
                backgroundColor: `${typeInfo.color}33`, // Colore con opacità 0.2
                fill: true,
                tension: 0.4
            }]
        };
    }
    
    // Ordina i dati per timestamp
    data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    // Prepara etichette e valori
    const labels = data.map(item => formatTimestamp(item.timestamp));
    const values = data.map(item => item.value);
    
    return {
        labels: labels,
        datasets: [{
            label: `${typeInfo.name} (${typeInfo.unit})`,
            data: values,
            borderColor: typeInfo.color,
            backgroundColor: `${typeInfo.color}33`, // Colore con opacità 0.2
            fill: true,
            tension: 0.4
        }]
    };
}

/**
 * Aggiorna o crea un grafico
 * @param {string} typeId ID del tipo di dati
 * @param {Object} chartData Dati formattati per Chart.js
 * @param {Object} typeInfo Informazioni sul tipo di dati
 */
function updateOrCreateChart(typeId, chartData, typeInfo) {
    const canvas = document.getElementById(`chart-${typeId}`);
    if (!canvas) {
        console.error(`Canvas non trovato per il grafico ${typeId}`);
        return;
    }
    
    // Distruggi il grafico esistente se presente
    if (activeCharts[typeId]) {
        activeCharts[typeId].destroy();
    }
    
    // Crea un nuovo grafico
    activeCharts[typeId] = new Chart(canvas, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${typeInfo.name} - Ultimi ${currentPeriod} giorni`,
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
                        text: 'Data'
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
 * Aggiorna la tabella dei dati
 * @param {string} typeId ID del tipo di dati
 * @param {Array} data Dati ricevuti dall'API
 */
function updateDataTable(typeId, data) {
    const tableBody = document.querySelector('#vitalsDataTable tbody');
    const noDataRow = document.getElementById('noVitalsDataRow');
    
    if (!tableBody) {
        console.error('Corpo della tabella dati non trovato');
        return;
    }
    
    // Trova le informazioni sul tipo di dati
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
        console.error(`Tipo di dati non supportato: ${typeId}`);
        return;
    }
    
    // Se i dati sono vuoti, mostra un messaggio
    if (!data || !data.length) {
        if (noDataRow) {
            const message = document.getElementById('vitalsTableMessage');
            if (message) {
                message.textContent = translateText(`Nessun dato disponibile per ${typeInfo.name.toLowerCase()}`);
            }
            noDataRow.style.display = 'table-row';
        }
        return;
    }
    
    // Nascondi la riga di nessun dato
    if (noDataRow) {
        noDataRow.style.display = 'none';
    }
    
    // Ordina i dati per timestamp (più recenti prima)
    data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Limita a 50 righe per non rallentare il browser
    const maxRows = 50;
    const limitedData = data.slice(0, maxRows);
    
    // Crea le righe della tabella
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
                    ${item.value} ${typeInfo.unit}
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
    
    // Aggiungi le righe alla tabella
    const existingRows = tableBody.querySelectorAll('tr:not(#noVitalsDataRow)');
    existingRows.forEach(row => row.remove());
    
    tableBody.insertAdjacentHTML('afterbegin', rows);
}

/**
 * Estrae l'ID del paziente dall'URL
 * @returns {number|null} ID del paziente o null se non trovato
 */
function getPatientIdFromUrl() {
    const urlPath = window.location.pathname;
    const matches = urlPath.match(/\/patients\/(\d+)/);
    return matches && matches.length > 1 ? parseInt(matches[1]) : null;
}

/**
 * Formatta una data per l'API (YYYY-MM-DD)
 * @param {Date} date Data da formattare
 * @returns {string} Data formattata
 */
function formatDateForAPI(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Formatta un timestamp per le etichette del grafico
 * @param {string} timestamp Timestamp in formato ISO
 * @returns {string} Data formattata
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    
    // Se il periodo è 1 giorno, mostra solo l'ora
    if (currentPeriod === 1) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Altrimenti mostra la data
    return date.toLocaleDateString();
}

/**
 * Funzione di traduzione (segnaposto, da sostituire con la funzione reale)
 * @param {string} text Testo da tradurre
 * @returns {string} Testo tradotto
 */
function translateText(text) {
    // Per ora restituisce il testo originale
    // In futuro potrà essere sostituita con la vera funzione di traduzione
    return text;
}

// Inizializza i grafici quando il documento è caricato
document.addEventListener('DOMContentLoaded', function() {
    initVitalsCharts();
});