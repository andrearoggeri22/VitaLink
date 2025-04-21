package com.vitalink.mobile.data.model

/**
 * Risposta dalla verifica del paziente
 */
data class PatientResponse(
    val patient_id: Int,
    val name: String,
    val success: Boolean = false,
    val error: String? = null
)

/**
 * Risposta dal caricamento dei dati
 */
data class UploadResponse(
    val success: Boolean,
    val vitals_saved: Int,
    val errors: List<String> = emptyList()
)

/**
 * Classe che rappresenta i dati Fitbit da caricare
 */
data class FitbitData(
    val heart_rate: List<VitalMeasurement> = emptyList(),
    val steps: List<VitalMeasurement> = emptyList(),
    val calories: List<VitalMeasurement> = emptyList(),
    val distance: List<VitalMeasurement> = emptyList(),
    val active_minutes: List<VitalMeasurement> = emptyList(),
    val sleep_duration: List<VitalMeasurement> = emptyList(),
    val floors_climbed: List<VitalMeasurement> = emptyList()
)

/**
 * Classe che rappresenta una singola misurazione di un parametro vitale
 */
data class VitalMeasurement(
    val timestamp: String,
    val value: Float
)

/**
 * Modello per il dispositivo Fitbit
 */
data class FitbitDevice(
    val address: String,
    val name: String,
    val rssi: Int, // Indicatore di potenza del segnale
    val isConnected: Boolean = false
)

/**
 * Stati possibili del servizio di sincronizzazione
 */
enum class SyncStatus {
    IDLE,             // Servizio in attesa
    CONNECTING,       // Connessione al dispositivo in corso
    CONNECTED,        // Connesso al dispositivo
    SYNCING,          // Sincronizzazione dati in corso
    UPLOADING,        // Caricamento dati al server in corso
    SUCCESS,          // Sincronizzazione completata con successo
    ERROR             // Errore durante la sincronizzazione
}