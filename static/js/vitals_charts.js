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
        { id: 'HEART_RATE', name: 'Frequenza cardiaca', unit: 'bpm', color: '#FF5252' },
        { id: 'STEPS', name: 'Passi', unit: 'passi', color: '#2196F3' },
        { id: 'DISTANCE', name: 'Distanza', unit: 'km', color: '#4CAF50' },
        { id: 'CALORIES', name: 'Calorie', unit: 'kcal', color: '#FF9800' },
        { id: 'ACTIVE_MINUTES', name: 'Minuti attivi', unit: 'min', color: '#9C27B0' },
        { id: 'SLEEP_DURATION', name: 'Durata sonno', unit: 'ore', color: '#3F51B5' },
        { id: 'FLOORS_CLIMBED', name: 'Piani saliti', unit: 'piani', color: '#795548' },
        { id: 'WEIGHT', name: 'Peso', unit: 'kg', color: '#607D8B' }
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
            btn.classList.remove('btn-light');
            btn.classList.add('btn-primary', 'active');
        }
        
        // Aggiungi event listener
        btn.addEventListener('click', function() {
            // Aggiorna lo stile dei pulsanti
            periodButtons.forEach(b => {
                b.classList.remove('btn-primary', 'active');
                b.classList.add('btn-light');
            });
            this.classList.remove('btn-light');
            this.classList.add('btn-primary', 'active');
            
            // Imposta il nuovo periodo
            currentPeriod = period;
            
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
    
    // Nascondi il contenitore dei pulsanti del periodo
    try {
        const periodContainer = document.querySelector('.btn-group[role="group"][aria-label="Periodo di tempo"]').closest('.mb-4');
        if (periodContainer) {
            periodContainer.classList.add('d-none');
            console.log('Periodo nascosto: nessuna connessione attiva');
        }
    } catch (error) {
        console.error('Errore nel nascondere i pulsanti del periodo:', error);
    }
    
    // Disabilita i pulsanti del periodo (per sicurezza)
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
    try {
        // Mostra il contenitore dei pulsanti del periodo
        const periodContainer = document.querySelector('.btn-group[role="group"][aria-label="Periodo di tempo"]').closest('.mb-4');
        if (periodContainer) {
            periodContainer.classList.remove('d-none');
            console.log('Periodo mostrato: connessione attiva con', platform);
        }
    } catch (error) {
        console.error('Errore nel mostrare i pulsanti del periodo:', error);
    }
    
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
        // Imposta il tipo di parametro vitale iniziale
        currentVitalType = dataTypes[0].id;
        console.log(`Tipo vitale iniziale impostato a: ${currentVitalType}`);
        
        // Carica i dati per il grafico
        loadDataForType(dataTypes[0].id);
        
        // Ricarica le osservazioni con il filtro del tipo corrente
        if (typeof loadObservations === 'function') {
            setTimeout(loadObservations, 500);
        }
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
            
            // Aggiorna il tipo di parametro vitale corrente
            currentVitalType = typeId;
            console.log(`Tipo vitale corrente impostato a: ${currentVitalType}`);
            
            // Carica i dati per il grafico
            loadDataForType(typeId);
            
            // Ricarica le osservazioni con il filtro aggiornato (se la funzione esiste)
            if (typeof loadObservations === 'function') {
                console.log('Ricarica osservazioni con filtro sul tipo vitale corrente');
                loadObservations();
            }
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
        
        // Aggiorna il tipo di parametro vitale corrente
        currentVitalType = typeId;
        
        // Carica i dati per il grafico
        loadDataForType(typeId);
        
        // Ricarica le osservazioni con il filtro del tipo corrente
        if (typeof loadObservations === 'function') {
            setTimeout(loadObservations, 500);
        }
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
        loadingOverlay.style.backgroundColor = 'transparent';
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
 * Genera un array di date per il periodo selezionato, anche se non ci sono dati per tutte le date
 * @param {Array} data Dati ricevuti dall'API
 * @param {Object} typeInfo Informazioni sul tipo di dati
 * @returns {Object} Dati formattati per Chart.js
 */
function prepareChartData(data, typeInfo) {
    // Genera array di date per il periodo selezionato
    const today = new Date();
    const startDate = new Date();
    startDate.setDate(today.getDate() - currentPeriod);
    
    // Crea array con tutte le date del periodo
    const allDates = [];
    const allLabels = [];
    const currentDate = new Date(startDate);
    
    // Aggiungi tutte le date dal periodo di inizio a oggi
    while (currentDate <= today) {
        allDates.push(new Date(currentDate));
        allLabels.push(formatTimestamp(currentDate));
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    // Se i dati sono vuoti, restituisci un set di dati vuoto ma con le date del periodo
    if (!data || !data.length) {
        // Crea array di valori nulli per tutte le date
        const emptyValues = allDates.map(() => null);
        
        return {
            labels: allLabels,
            datasets: [{
                label: `${typeInfo.name} (${typeInfo.unit})`,
                data: emptyValues,
                borderColor: typeInfo.color,
                backgroundColor: `${typeInfo.color}33`, // Colore con opacità 0.2
                fill: true,
                tension: 0.4
            }]
        };
    }
    
    // Ordina i dati per timestamp
    data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    // Crea un mapping dei dati per data
    const dataByDate = {};
    data.forEach(item => {
        const date = new Date(item.timestamp);
        const dateKey = formatDateForAPI(date);
        dataByDate[dateKey] = item.value;
    });
    
    // Prepara i valori per tutte le date del periodo
    // Importante: se il valore è 0, deve essere visualizzato come 0 e non come null
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
            backgroundColor: `${typeInfo.color}33`, // Colore con opacità 0.2
            fill: true,
            tension: 0.4,
            // Importante: consenti la visualizzazione della linea anche con valori nulli/mancanti
            spanGaps: true
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
 * Aggiorna la tabella dei dati in "Anamnesi dei parametri vitali"
 * Mostra solo i dati del tipo correntemente selezionato, per sincronizzare con il grafico
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
        
        // Rimuovi tutte le righe esistenti
        const existingRows = tableBody.querySelectorAll('tr:not(#noVitalsDataRow)');
        existingRows.forEach(row => row.remove());
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
    
    // Rimuovi tutte le righe esistenti e aggiungi le nuove
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

/**
 * Gestisce il clic sul pulsante per generare un report specifico
 * Reindirizza alla URL per generare il PDF con il tipo vitale e periodo correnti
 */
function setupSpecificReportButton() {
    const reportBtn = document.getElementById('generateSpecificReportBtn');
    if (!reportBtn) return;
    
    reportBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Verifica che ci sia un tipo vitale attualmente selezionato
        if (!currentVitalType) {
            alert(translateText('Seleziona prima un tipo di parametro vitale.'));
            return;
        }
        
        // Crea l'URL per il report specifico
        const reportUrl = `${BASE_URL}patients/${PATIENT_ID}/specific_report?vital_type=${currentVitalType}&period=${currentPeriod}`;
        
        // Apri l'URL in una nuova finestra/tab
        window.open(reportUrl, '_blank');
    });
}

// Inizializza i grafici quando il documento è caricato
document.addEventListener('DOMContentLoaded', function() {
    initVitalsCharts();
    
    // Inizializza il modulo delle osservazioni dopo i grafici
    if (typeof initObservations === 'function') {
        initObservations();
    }
    
    // Inizializza il pulsante per il report specifico
    setupSpecificReportButton();
});