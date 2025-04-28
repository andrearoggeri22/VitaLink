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
// Utilizziamo la variabile currentVitalType definita in vitals_charts.js

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
    }    // Gestisci il submit del form per aggiunta
    const observationForm = document.getElementById('observationForm');
    if (observationForm) {
        observationForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Controlla l'azione da eseguire (add o delete)
            const action = document.getElementById('formAction').value;
            
            if (action === 'add') {
                submitAddObservation(this);
            }
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
 * Carica tutte le osservazioni per il paziente, senza filtri di periodo
 * Tutte le osservazioni verranno mostrate indipendentemente dal periodo
 */
function loadObservations() {
    // Verifica che la variabile currentVitalType sia disponibile (definita in vitals_charts.js)
    if (typeof currentVitalType === 'undefined') {
        console.error('La variabile currentVitalType non è disponibile');
        // Non blocchiamo l'esecuzione, poiché il caricamento dovrebbe funzionare lo stesso
    }
    
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
    
    // Costruisci l'URL dell'API senza parametri di date
    // per recuperare TUTTE le osservazioni per il paziente
    const apiUrl = `/web/observations/${patientId}`;
    
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
    
    // Assicuriamoci che observations sia un array
    if (!Array.isArray(observations)) {
        console.error('updateObservationsUI: observations non è un array', observations);
        observations = [];
    }
    
    // Container per la lista delle osservazioni
    const observationsList = document.getElementById('observationsList');      // Filtra le osservazioni in base al tipo di parametro vitale correntemente selezionato
    let filteredObservations = observations;
    try {
        if (typeof currentVitalType !== 'undefined' && currentVitalType !== null) {
            console.log("Tipo corrente:", currentVitalType, typeof currentVitalType);
            
            // Estrai l'ID del tipo di parametro vitale (gestisci sia stringa che oggetto)
            let vitalTypeId;
            if (typeof currentVitalType === 'string') {
                vitalTypeId = currentVitalType.toLowerCase();
            } else if (typeof currentVitalType === 'object' && currentVitalType !== null) {
                vitalTypeId = currentVitalType.id ? currentVitalType.id.toLowerCase() : '';
            } else {
                vitalTypeId = '';
            }
            
            if (vitalTypeId) {
                filteredObservations = observations.filter(obs => obs.vital_type === vitalTypeId);
                console.log(`Mostrando solo osservazioni per il tipo: ${vitalTypeId}`);
            }
        }
    } catch (error) {
        console.error('Errore nel filtraggio delle osservazioni:', error);
        // In caso di errore, mostra tutte le osservazioni
        filteredObservations = observations;
    }
    
    if (filteredObservations.length === 0) {
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
    filteredObservations.forEach(obs => {
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
        `;            // Aggiungi le singole osservazioni alla lista
        const observationList = observationGroup.querySelector('.observation-list');        typeObservations.forEach(obs => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.setAttribute('data-id', obs.id);
            
            // Formatta le date
            const startDate = new Date(obs.start_date);
            const endDate = new Date(obs.end_date);
            const dateStr = `${formatDateForDisplay(startDate)} - ${formatDateForDisplay(endDate)}`;            // Verifica se l'osservazione appartiene al medico corrente
            let isCurrentDoctorObservation = false;
              try {
                // Recupera l'ID del medico corrente dal meta tag
                const currentDoctorIdElement = document.querySelector('meta[name="current-doctor-id"]');
                const currentDoctorId = currentDoctorIdElement ? parseInt(currentDoctorIdElement.getAttribute('content')) : null;
                
                console.log('Controllo proprietà:', obs.id, '- Medico attuale:', currentDoctorId, '- Medico osservazione:', obs.doctor_id);
                
                // Converti entrambi gli ID in numeri interi per fare un confronto coerente
                // Se entrambi gli ID sono disponibili, confrontali
                if (currentDoctorId && obs.doctor_id) {
                    const doctorIdFromObs = parseInt(obs.doctor_id);
                    isCurrentDoctorObservation = doctorIdFromObs === currentDoctorId;
                    console.log('Confronto ID:', doctorIdFromObs, '===', currentDoctorId, '=', isCurrentDoctorObservation);
                } else {
                    // Se mancano gli ID, mostriamo sempre il pulsante per mantenere la funzionalità esistente
                    // Questo è un fallback che assicura di non bloccare le funzionalità base
                    isCurrentDoctorObservation = true;
                    console.log('ID mancanti, mostrando pulsante per sicurezza');
                }
            } catch (error) {
                // In caso di errore, mostriamo il pulsante per mantenere la funzionalità
                isCurrentDoctorObservation = true;
                console.error('Errore nel controllo del proprietario dell\'osservazione:', error);
            }
              // HTML con nome del dottore e pulsante di eliminazione solo se è il proprietario
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="mb-1">${obs.content}</p>
                        <div class="d-flex align-items-center text-muted small">
                            <span class="me-3">
                                <i class="fas fa-calendar-alt me-1"></i> ${dateStr}
                            </span>
                            <span>
                                <i class="fas fa-user-md me-1"></i> ${obs.doctor_name || 'Unknown Doctor'}
                            </span>
                        </div>
                    </div>
                    ${isCurrentDoctorObservation ? 
                      `<button class="btn btn-sm btn-outline-danger delete-observation-btn">
                         <i class="fas fa-trash-alt"></i>
                       </button>` : ''}
                </div>
            `;
            
            // Aggiungi event listener al pulsante di eliminazione solo se esiste
            const deleteBtn = item.querySelector('.delete-observation-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', function() {
                    openObservationModal(obs);
                });
            }
            
            observationList.appendChild(item);
        });
        
        observationsList.appendChild(observationGroup);
    }
}

/**
 * Apre il modal per aggiungere una nuova osservazione o eliminare un'osservazione esistente
 * @param {Object} observation Osservazione esistente solo per eventuale eliminazione
 */
function openObservationModal(observation = null) {
    // Elementi UI
    const modalTitle = document.getElementById('observationModalLabel');
    const addContent = document.getElementById('addObservationContent');
    const deleteContent = document.getElementById('deleteObservationContent');
    const form = document.getElementById('observationForm');
    const formAction = document.getElementById('formAction');
    const addObs = document.getElementById('modal-footer-add');
    const delObs = document.getElementById('modal-footer-delete');
    const observationIdInput = document.getElementById('observationId');
    
    if (observation) {
        // Se è un'osservazione esistente, mostra la conferma di eliminazione
        modalTitle.textContent = translateText('Elimina osservazione');
        
        // Impostazione per eliminazione
        formAction.value = 'delete';
        addObs.classList.add('d-none');
        delObs.classList.remove('d-none');
        
        // Mostra il contenuto di eliminazione e nascondi il form di aggiunta
        addContent.classList.add('d-none');
        deleteContent.classList.remove('d-none');
        
        // Prepara il contenuto di eliminazione
        if (deleteContent) {
            // Assicurati che il contenitore sia visibile
            deleteContent.classList.remove('d-none');
            
            // Svuota il contenuto precedente e inserisci il nuovo messaggio
            deleteContent.innerHTML = `
                <div>
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>${translateText('Attenzione')}</strong>: ${translateText('Sei sicuro di voler eliminare questa osservazione?')}
                </div>
            `;
        }
        
        // Salva l'ID dell'osservazione
        if (observationIdInput) {
            observationIdInput.value = observation.id;
        }
    } else {
        // Se è una nuova osservazione
        modalTitle.textContent = translateText('Aggiungi osservazione');
        
        // Impostazione per aggiunta
        formAction.value = 'add';
        delObs.classList.add('d-none');
        addObs.classList.remove('d-none');
        
        // Mostra il form di aggiunta e nascondi il contenuto di eliminazione
        addContent.classList.remove('d-none');
        deleteContent.classList.add('d-none');
        
        // Reset form
        if (form) {
            form.reset();
        }
        
        // Popola le opzioni per i tipi di vitali disponibili
        populateVitalTypeOptions();
          // Date predefinite in base al periodo corrente
        const startDateInput = document.getElementById('observationStartDate');
        const endDateInput = document.getElementById('observationEndDate');
        
        if (startDateInput && endDateInput) {
            const endDate = new Date();
            const startDate = new Date();
            
            // Usa il periodo corrente se disponibile, altrimenti usa 7 giorni come default
            const period = (typeof currentPeriod !== 'undefined' && currentPeriod) ? currentPeriod : 7;
            startDate.setDate(startDate.getDate() - period);
            
            startDateInput.value = formatDateForInput(startDate);
            endDateInput.value = formatDateForInput(endDate);
        }// Seleziona automaticamente il tipo di parametro vitale corrente
        try {
            if (typeof currentVitalType !== 'undefined' && currentVitalType !== null) {
                const typeSelect = document.getElementById('observationType');
                if (typeSelect) {
                    // Estrai l'ID del tipo vitale (gestisci sia stringa che oggetto)
                    let vitalTypeId;
                    if (typeof currentVitalType === 'string') {
                        vitalTypeId = currentVitalType.toLowerCase();
                    } else if (typeof currentVitalType === 'object' && currentVitalType !== null) {
                        vitalTypeId = currentVitalType.id ? currentVitalType.id.toLowerCase() : '';
                    } else {
                        vitalTypeId = '';
                    }
                    
                    if (vitalTypeId) {
                        typeSelect.value = vitalTypeId;
                    }
                }
            }
        } catch (error) {
            console.error('Errore nella selezione del tipo vitale:', error);
            // In caso di errore, non impostiamo alcun valore predefinito
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
    
    // Pulisci le opzioni esistenti, tranne la prima (selezione vuota)
    while (typeSelect.options.length > 1) {
        typeSelect.remove(1);
    }
    
    try {
        // Aggiungi opzioni per i tipi supportati dalla piattaforma attuale
        // Verifica che currentPlatform sia definita (potrebbe essere definita in vitals_charts.js)
        if (typeof currentPlatform !== 'undefined' && currentPlatform && typeof SUPPORTED_DATA_TYPES !== 'undefined' && SUPPORTED_DATA_TYPES[currentPlatform.toUpperCase()]) {
            const types = SUPPORTED_DATA_TYPES[currentPlatform.toUpperCase()];
            types.forEach(type => {
                const option = document.createElement('option');
                option.value = type.id;
                option.textContent = type.name;
                typeSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Errore nel popolamento delle opzioni:', error);
    }
}

/**
 * Invia il form per aggiungere una nuova osservazione
 * @param {HTMLFormElement} form - Il form da inviare
 */
function submitAddObservation(form) {
    if (!form) return;
    
    const errorDiv = document.getElementById('observationError');
    // Nascondi eventuali messaggi di errore precedenti nel div di errore
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
      // Ottieni i valori dal form
    const formData = new FormData(form);
    const vitalType = formData.get('vital_type');
    const content = formData.get('content');
    const startDate = formData.get('start_date');
    const endDate = formData.get('end_date');
    
    // Reset di eventuali messaggi di validazione personalizzati precedenti
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.setCustomValidity('');
    });
      // Validazione base - utilizziamo la validazione HTML5 per questi campi
    if (!vitalType || !content || !startDate || !endDate) {
        return;
    }// Verifica che la data di inizio sia precedente alla data di fine
    if (new Date(startDate) > new Date(endDate)) {
        // Ottieni i riferimenti ai campi data
        const startDateInput = document.getElementById('observationStartDate');
        
        // Imposta la validità personalizzata sul campo della data di fine
        startDateInput.setCustomValidity(document.documentElement.lang === "it"
            ? "La data di inizio deve essere precedente alla data di fine"
            : "Start date must be before end date");
            
        // Forza la visualizzazione del messaggio di errore
        startDateInput.reportValidity();
        
        // Aggiungi un listener per ripulire l'errore quando il valore cambia
        startDateInput.addEventListener('input', function() {
            this.setCustomValidity('');
            const today = new Date();
            const isoToday = today.toISOString().split('T')[0];
            observationStartDate.max = isoToday;
            observationEndDate.max = isoToday;
        }, { once: true });
        
        return;
    }
    
    // Aggiungi l'ID del paziente ai dati
    const patientId = PATIENT_ID || getPatientIdFromUrl();
    const observationData = {
        patient_id: patientId,
        vital_type: vitalType.toLowerCase(),
        content: content,
        start_date: startDate,
        end_date: endDate
    };
    
    // URL per la richiesta API
    const apiUrl = `/web/observations`;
    
    console.log('Invio osservazione:', observationData);
    
    // Chiamata API
    fetch(apiUrl, {
        method: 'POST',
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
    })    .catch(error => {
        console.error('Errore nel salvataggio dell\'osservazione:', error);
        // Mostra l'errore di API come messaggio personalizzato visibile nella parte superiore del form
        const errorMessage = error.message || (document.documentElement.lang === "it"
            ? "Errore nel salvataggio dell'osservazione. Riprova più tardi."
            : "Error saving observation. Please try again later.");
            
        // Mostra l'errore nella parte alta del form
        if (errorDiv) {
            errorDiv.textContent = errorMessage;
            errorDiv.style.display = 'block';
            errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
            console.log('Mostro errore API:', errorDiv.textContent);
        }
    });
}

/**
 * Elimina un'osservazione
 */
function deleteObservation() {
    // Recupera ID dell'osservazione
    const id = document.getElementById('observationId').value;
    if (!id) return;
    
    // URL dell'API (non serve più la conferma del browser, abbiamo già la conferma nel modal)
    const apiUrl = `/web/observations/${id}`;
    const errorDiv = document.getElementById('observationError');
    
    // Nascondi eventuali messaggi di errore precedenti
    if (errorDiv) {
        errorDiv.textContent = '';
        errorDiv.style.display = 'none';
    }
    
    console.log('Eliminando osservazione con ID:', id);
    
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
    })    .catch(error => {
        console.error('Errore nell\'eliminazione dell\'osservazione:', error);
        
        if (errorDiv) {
            errorDiv.textContent = error.message || (document.documentElement.lang === "it"
                ? "Errore nell'eliminazione dell'osservazione. Riprova più tardi."
                : "Error deleting observation. Please try again later.");
            errorDiv.style.display = 'block';
            errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            showAlert('Errore nell\'eliminazione dell\'osservazione. Riprova più tardi.', 'danger');
        }
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
      // Inserisci l'alert nella stessa posizione dei flash messages di Flask (all'inizio del main container)
    const mainContainer = document.querySelector('main.container');
    if (mainContainer) {
        // Controlliamo se esiste già un alert, in tal caso inseriamo prima di esso,
        // altrimenti inseriamo prima del primo elemento nel main container
        const existingAlert = mainContainer.querySelector('.alert');
        if (existingAlert) {
            mainContainer.insertBefore(alertDiv, existingAlert);
        } else {
            mainContainer.insertBefore(alertDiv, mainContainer.firstChild);
        }
    } else {
        // Fallback: usa il container standard se main.container non esiste
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }
    }
    
    // Rimuovi automaticamente dopo 5 secondi
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
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