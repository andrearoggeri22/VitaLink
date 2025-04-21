package com.vitalink.mobile.util

import android.content.Context
import android.content.SharedPreferences
import java.util.Date

/**
 * Gestione delle preferenze dell'applicazione
 * Questo oggetto fornisce metodi per salvare e recuperare le preferenze dell'utente
 */
object PreferenceManager {
    
    private const val PREF_NAME = "vitalink_preferences"
    
    private const val KEY_PATIENT_ID = "patient_id"
    private const val KEY_PATIENT_NAME = "patient_name"
    private const val KEY_SERVER_URL = "server_url"
    private const val KEY_LAST_SYNC = "last_sync_timestamp"
    private const val KEY_FITBIT_DEVICE_ADDRESS = "fitbit_device_address"
    private const val KEY_LANGUAGE = "app_language"
    private const val KEY_AUTO_SYNC = "auto_sync_enabled"
    private const val KEY_NOTIFICATIONS = "notifications_enabled"
    
    private const val DEFAULT_SERVER_URL = "https://vitalink.replit.app"
    
    private lateinit var preferences: SharedPreferences
    
    /**
     * Inizializza il PreferenceManager con il contesto dell'applicazione
     */
    fun init(context: Context) {
        preferences = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }
    
    /**
     * Salva l'ID del paziente
     */
    fun savePatientId(patientId: Int) {
        preferences.edit().putInt(KEY_PATIENT_ID, patientId).apply()
    }
    
    /**
     * Recupera l'ID del paziente salvato
     */
    fun getPatientId(): Int? {
        val id = preferences.getInt(KEY_PATIENT_ID, -1)
        return if (id != -1) id else null
    }
    
    /**
     * Salva il nome del paziente
     */
    fun savePatientName(name: String) {
        preferences.edit().putString(KEY_PATIENT_NAME, name).apply()
    }
    
    /**
     * Recupera il nome del paziente salvato
     */
    fun getPatientName(): String? {
        return preferences.getString(KEY_PATIENT_NAME, null)
    }
    
    /**
     * Salva l'URL del server
     */
    fun saveServerUrl(url: String) {
        preferences.edit().putString(KEY_SERVER_URL, url).apply()
    }
    
    /**
     * Recupera l'URL del server, utilizzerà l'URL predefinito se non è stato impostato
     */
    fun getServerUrl(): String {
        return preferences.getString(KEY_SERVER_URL, DEFAULT_SERVER_URL) ?: DEFAULT_SERVER_URL
    }
    
    /**
     * Reimposta l'URL del server al valore predefinito
     */
    fun resetServerUrl() {
        preferences.edit().putString(KEY_SERVER_URL, DEFAULT_SERVER_URL).apply()
    }
    
    /**
     * Salva il timestamp dell'ultima sincronizzazione
     */
    fun saveLastSyncTimestamp(timestamp: Long = System.currentTimeMillis()) {
        preferences.edit().putLong(KEY_LAST_SYNC, timestamp).apply()
    }
    
    /**
     * Recupera il timestamp dell'ultima sincronizzazione
     */
    fun getLastSyncTimestamp(): Long? {
        val timestamp = preferences.getLong(KEY_LAST_SYNC, -1)
        return if (timestamp != -1L) timestamp else null
    }
    
    /**
     * Salva l'indirizzo del dispositivo Fitbit connesso
     */
    fun saveFitbitDeviceAddress(address: String) {
        preferences.edit().putString(KEY_FITBIT_DEVICE_ADDRESS, address).apply()
    }
    
    /**
     * Recupera l'indirizzo del dispositivo Fitbit salvato
     */
    fun getFitbitDeviceAddress(): String? {
        return preferences.getString(KEY_FITBIT_DEVICE_ADDRESS, null)
    }
    
    /**
     * Salva la lingua dell'applicazione
     */
    fun saveLanguage(languageCode: String) {
        preferences.edit().putString(KEY_LANGUAGE, languageCode).apply()
    }
    
    /**
     * Recupera la lingua dell'applicazione
     */
    fun getLanguage(): String? {
        return preferences.getString(KEY_LANGUAGE, null)
    }
    
    /**
     * Salva lo stato della sincronizzazione automatica
     */
    fun setAutoSyncEnabled(enabled: Boolean) {
        preferences.edit().putBoolean(KEY_AUTO_SYNC, enabled).apply()
    }
    
    /**
     * Recupera lo stato della sincronizzazione automatica
     */
    fun isAutoSyncEnabled(): Boolean {
        return preferences.getBoolean(KEY_AUTO_SYNC, true)
    }
    
    /**
     * Salva lo stato delle notifiche
     */
    fun setNotificationsEnabled(enabled: Boolean) {
        preferences.edit().putBoolean(KEY_NOTIFICATIONS, enabled).apply()
    }
    
    /**
     * Recupera lo stato delle notifiche
     */
    fun areNotificationsEnabled(): Boolean {
        return preferences.getBoolean(KEY_NOTIFICATIONS, true)
    }
    
    /**
     * Cancella tutte le preferenze (utile per il logout)
     */
    fun clearAll() {
        preferences.edit().clear().apply()
    }
}