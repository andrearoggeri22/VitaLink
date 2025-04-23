/**
 * Observations JavaScript
 * 
 * Gestisce la visualizzazione e la modifica delle osservazioni sui parametri vitali
 * 
 * Funzionalità:
 * - Caricamento osservazioni per il periodo corrente
 * - Aggiunta, modifica e eliminazione osservazioni
 * - Visualizzazione delle osservazioni nella UI
 */

// Variabili globali
let currentObservations = [];
let observationModal = null;

/**
 * Inizializza la gestione delle osservazioni
 */
function initObservations() {
    console.log('Inizializzazione gestione osservazioni');
    
    // Inizializza il modal per le osservazioni
    observationModal = new bootstrap.Modal(document.getElementById('observationModal'));
    
    // Aggiungi event listener al pulsante di aggiunta osservazione
    const addObservationBtn = document.getElementById('addObservationBtn');
    if (addObservationBtn) {
        addObservationBtn.addEventListener('click', function() {
            openObservationModal();
        });
    }
    
    // Aggiungi event listener al pulsante di salvataggio
    const saveObservationBtn = document.getElementById('saveObservationBtn');
    if (saveObservationBtn) {
        saveObservationBtn.addEventListener('click', function() {
            saveObservation();
        });
    }
    
    // Aggiungi event listener al pulsante di eliminazione
    const deleteObservationBtn = document.getElementById('deleteObservationBtn');
    if (deleteObservationBtn) {
        deleteObservationBtn.addEventListener('click', function() {
            deleteObservation();
        });
    }
    
    // Aggiungi event listener al cambio di periodo
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Le osservazioni verranno ricaricate quando i grafici vengono ricaricati
            setTimeout(loadObservations, 500);
        });
    });
    
    // Carica le osservazioni iniziali
    loadObservations();
}

/**
 * Carica le osservazioni per il periodo corrente
 */
function loadObservations() {
    const patientId = getPatientIdFromUrl();
    if (!patientId) {
        console.error('Impossibile determinare l\'ID del paziente');
        updateObservationsUI([]);
        return;
    }
    
    // Mostra loading
    document.getElementById('observationsLoading').classList.remove('d-none');
    document.getElementById('noObservations').classList.add('d-none');
    document.getElementById('observationsList').classList.add('d-none');
    
    // Calcola date di inizio e fine in base al periodo corrente
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - currentPeriod);
    
    // Formato date per l'API
    const startDateStr = formatDateForAPI(startDate);
    const endDateStr = formatDateForAPI(endDate);
    
    // Costruisci l'URL dell'API
    const apiUrl = `/web/observations/${patientId}?start_date=${startDateStr}&end_date=${endDateStr}`;
    
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Errore nel caricamento delle osservazioni');
            }
            return response.json();
        })
        .then(data => {
            console.log('Osservazioni caricate:', data);
            currentObservations = data;
            updateObservationsUI(data);
        })
        .catch(error => {
            console.error('Errore nel caricamento delle osservazioni:', error);
            updateObservationsUI([]);
        });
}

/**
 * Aggiorna l'interfaccia con le osservazioni caricate
 * @param {Array} observations Array di osservazioni
 */
function updateObservationsUI(observations) {
    // Nascondi loading
    document.getElementById('observationsLoading').classList.add('d-none');
    
    // Container per la lista delle osservazioni
    const observationsList = document.getElementById('observationsList');
    
    if (observations.length === 0) {
        // Mostra messaggio di nessuna osservazione
        document.getElementById('noObservations').classList.remove('d-none');
        observationsList.classList.add('d-none');
        return;
    }
    
    // Mostra la lista delle osservazioni
    document.getElementById('noObservations').classList.add('d-none');
    observationsList.classList.remove('d-none');
    
    // Svuota la lista
    observationsList.innerHTML = '';
    
    // Raggruppa le osservazioni per tipo
    const groupedObservations = {};
    observations.forEach(obs => {
        if (!groupedObservations[obs.vital_type]) {
            groupedObservations[obs.vital_type] = [];
        }
        groupedObservations[obs.vital_type].push(obs);
    });
    
    // Crea elementi UI per ogni gruppo di osservazioni
    for (const type in groupedObservations) {
        const typeObservations = groupedObservations[type];
        
        // Trova le informazioni sul tipo
        let typeName = type.replace('_', ' ');
        let typeColor = '#007bff'; // Default blue
        
        // Cerca nelle definizioni dei tipi supportati
        for (const platform in SUPPORTED_DATA_TYPES) {
            const supportedTypes = SUPPORTED_DATA_TYPES[platform];
            const typeInfo = supportedTypes.find(t => t.id === type);
            if (typeInfo) {
                typeName = typeInfo.name;
                typeColor = typeInfo.color;
                break;
            }
        }
        
        // Crea il gruppo di osservazioni
        const observationGroup = document.createElement('div');
        observationGroup.className = 'card mb-3';
        observationGroup.innerHTML = `
            <div class="card-header" style="background-color: ${typeColor}20;">
                <h6 class="mb-0" style="color: ${typeColor};">
                    <i class="fas fa-clipboard-list me-2"></i> ${typeName}
                </h6>
            </div>
            <div class="card-body p-0">
                <ul class="list-group list-group-flush observation-list" data-type="${type}"></ul>
            </div>
        `;
        
        // Aggiungi le singole osservazioni alla lista
        const observationList = observationGroup.querySelector('.observation-list');
        typeObservations.forEach(obs => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.setAttribute('data-id', obs.id);
            
            // Formatta le date
            const startDate = new Date(obs.start_date);
            const endDate = new Date(obs.end_date);
            const dateStr = `${formatDateForDisplay(startDate)} - ${formatDateForDisplay(endDate)}`;
            
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="mb-1">${obs.content}</p>
                        <small class="text-muted">
                            <i class="fas fa-calendar-alt me-1"></i> ${dateStr}
                        </small>
                    </div>
                    <button class="btn btn-sm btn-outline-primary edit-observation-btn">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            `;
            
            // Aggiungi event listener al pulsante di modifica
            const editBtn = item.querySelector('.edit-observation-btn');
            editBtn.addEventListener('click', function() {
                openObservationModal(obs);
            });
            
            observationList.appendChild(item);
        });
        
        observationsList.appendChild(observationGroup);
    }
}

/**
 * Apre il modal per aggiungere una nuova osservazione
 * @param {Object} observation Osservazione esistente solo per visualizzare i dettagli ed eventuale eliminazione
 */
function openObservationModal(observation = null) {
    // Titolo del modal
    const modalTitle = document.getElementById('observationModalLabel');
    modalTitle.textContent = translateText('Aggiungi osservazione');
    
    // Form
    const form = document.getElementById('observationForm');
    if (form) {
        form.reset();
    }
    
    // Popola le opzioni per i tipi di vitali disponibili
    populateVitalTypeOptions();
    
    // ID osservazione (solo per eliminazione)
    const observationIdInput = document.getElementById('observationId');
    if (observationIdInput) {
        observationIdInput.value = observation ? observation.id : '';
    }
    
    // Pulsante di eliminazione - visibile solo se si tratta di un'osservazione esistente
    const deleteBtn = document.getElementById('deleteObservationBtn');
    const saveBtn = document.getElementById('saveObservationBtn');
    
    if (deleteBtn && saveBtn) {
        if (observation) {
            // Se è un'osservazione esistente, mostra solo il pulsante di eliminazione
            deleteBtn.classList.remove('d-none');
            saveBtn.classList.add('d-none');  // Nascondi il pulsante Salva
        } else {
            // Se è una nuova osservazione, mostra solo il pulsante di salvataggio
            deleteBtn.classList.add('d-none');
            saveBtn.classList.remove('d-none');
        }
    }
    
    // Date predefinite in base al periodo corrente (solo per nuove osservazioni)
    if (!observation) {
        const startDateInput = document.getElementById('observationStartDate');
        const endDateInput = document.getElementById('observationEndDate');
        
        if (startDateInput && endDateInput) {
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - currentPeriod);
            
            startDateInput.value = formatDateForInput(startDate);
            endDateInput.value = formatDateForInput(endDate);
        }
        
        // Seleziona automaticamente il tipo di parametro vitale corrente
        if (currentVitalType) {
            const typeSelect = document.getElementById('observationType');
            if (typeSelect) {
                typeSelect.value = currentVitalType.toLowerCase();
            }
        }
    }
    
    // Mostra il modal
    observationModal.show();
}

/**
 * Popola le opzioni per i tipi di vitali disponibili
 */
function populateVitalTypeOptions() {
    const typeSelect = document.getElementById('observationType');
    if (!typeSelect) return;
    
    // Mantieni l'opzione vuota
    typeSelect.innerHTML = '<option value="">Seleziona parametro</option>';
    
    // Aggiungi opzioni per i tipi supportati dalla piattaforma attuale
    if (currentPlatform && SUPPORTED_DATA_TYPES[currentPlatform.toUpperCase()]) {
        const types = SUPPORTED_DATA_TYPES[currentPlatform.toUpperCase()];
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type.id;
            option.textContent = type.name;
            typeSelect.appendChild(option);
        });
    }
}

/**
 * Salva una nuova osservazione
 */
function saveObservation() {
    // Recupera dati dal form
    const form = document.getElementById('observationForm');
    if (!form) return;
    
    const vitalType = document.getElementById('observationType').value;
    const content = document.getElementById('observationContent').value;
    const startDate = document.getElementById('observationStartDate').value;
    const endDate = document.getElementById('observationEndDate').value;
    
    // Validazione base
    if (!vitalType || !content || !startDate || !endDate) {
        showAlert('Compila tutti i campi obbligatori', 'danger');
        return;
    }
    
    // Verifica che la data di inizio sia precedente alla data di fine
    if (new Date(startDate) > new Date(endDate)) {
        showAlert('La data di inizio deve essere precedente alla data di fine', 'danger');
        return;
    }
    
    // Prepara i dati per l'invio
    const patientId = PATIENT_ID || getPatientIdFromUrl();
    const observationData = {
        patient_id: patientId,
        vital_type: vitalType.toLowerCase(), // Assicuriamo che sia in minuscolo come nell'enum
        content: content,
        start_date: startDate,
        end_date: endDate
    };
    
    // URL e metodo dell'API - sempre POST per una nuova osservazione
    const apiUrl = `/web/observations`;
    const method = 'POST';
    
    console.log('Saving observation:', observationData);
    
    // Chiamata API
    fetch(apiUrl, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(observationData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Errore nel salvataggio dell\'osservazione');
        }
        return response.json();
    })
    .then(data => {
        console.log('Osservazione salvata:', data);
        
        // Chiudi il modal
        observationModal.hide();
        
        // Mostra messaggio di successo
        showAlert('Osservazione aggiunta con successo', 'success');
        
        // Ricarica le osservazioni
        loadObservations();
    })
    .catch(error => {
        console.error('Errore nel salvataggio dell\'osservazione:', error);
        showAlert('Errore nel salvataggio dell\'osservazione. Riprova più tardi.', 'danger');
    });
}

/**
 * Elimina un'osservazione
 */
function deleteObservation() {
    // Recupera ID dell'osservazione
    const id = document.getElementById('observationId').value;
    if (!id) return;
    
    // Chiedi conferma
    if (!confirm('Sei sicuro di voler eliminare questa osservazione?')) {
        return;
    }
    
    // URL dell'API
    const apiUrl = `/web/observations/${id}`;
    
    // Chiamata API
    fetch(apiUrl, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Errore nell\'eliminazione dell\'osservazione');
        }
        return response.json();
    })
    .then(data => {
        console.log('Osservazione eliminata:', data);
        
        // Chiudi il modal
        observationModal.hide();
        
        // Mostra messaggio di successo
        showAlert('Osservazione eliminata con successo', 'success');
        
        // Ricarica le osservazioni
        loadObservations();
    })
    .catch(error => {
        console.error('Errore nell\'eliminazione dell\'osservazione:', error);
        showAlert('Errore nell\'eliminazione dell\'osservazione. Riprova più tardi.', 'danger');
    });
}

/**
 * Mostra un messaggio di alert nell'interfaccia
 * @param {string} message Messaggio da mostrare
 * @param {string} type Tipo di alert (success, danger, warning, info)
 */
function showAlert(message, type = 'info') {
    // Crea l'elemento alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Aggiungi alla pagina
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Rimuovi automaticamente dopo 5 secondi
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
    }
}

/**
 * Formatta una data per l'input di tipo date
 * @param {Date} date Data da formattare
 * @returns {string} Data formattata YYYY-MM-DD
 */
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Formatta una data per l'API
 * @param {Date} date Data da formattare
 * @returns {string} Data formattata in formato ISO YYYY-MM-DD
 */
function formatDateForAPI(date) {
    return formatDateForInput(date);
}

/**
 * Formatta una data per la visualizzazione
 * @param {Date} date Data da formattare
 * @returns {string} Data formattata DD/MM/YYYY
 */
function formatDateForDisplay(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
}

// Inizializza quando il documento è caricato
document.addEventListener('DOMContentLoaded', function() {
    // L'inizializzazione sarà chiamata dopo il caricamento dei grafici
    // Vedi vitals_charts.js
});