package com.vitalink.mobile.util

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys

/**
 * Gestore delle preferenze dell'app che utilizza SharedPreferences crittografate
 * per memorizzare in modo sicuro le informazioni sensibili del paziente.
 */
object PreferenceManager {
    
    private const val PREF_NAME = "vitalink_preferences"
    private const val KEY_PATIENT_UUID = "patient_uuid"
    private const val KEY_PATIENT_ID = "patient_id"
    private const val KEY_PATIENT_NAME = "patient_name"
    private const val KEY_ONBOARDING_COMPLETED = "onboarding_completed"
    private const val KEY_SERVER_URL = "server_url"
    private const val KEY_LAST_SYNC = "last_sync"
    private const val KEY_FITBIT_DEVICE_ADDRESS = "fitbit_device_address"
    
    private lateinit var sharedPreferences: SharedPreferences
    
    /**
     * Inizializza il gestore delle preferenze con il contesto dell'applicazione
     */
    fun init(context: Context) {
        val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)
        
        sharedPreferences = EncryptedSharedPreferences.create(
            PREF_NAME,
            masterKeyAlias,
            context,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }
    
    /**
     * Verifica se l'onboarding è stato completato dall'utente
     */
    fun isOnboardingCompleted(): Boolean {
        return sharedPreferences.getBoolean(KEY_ONBOARDING_COMPLETED, false)
    }
    
    /**
     * Imposta lo stato di completamento dell'onboarding
     */
    fun setOnboardingCompleted(completed: Boolean) {
        sharedPreferences.edit().putBoolean(KEY_ONBOARDING_COMPLETED, completed).apply()
    }
    
    /**
     * Salva l'ID paziente verificato
     */
    fun savePatientInfo(uuid: String, id: Int, name: String) {
        sharedPreferences.edit()
            .putString(KEY_PATIENT_UUID, uuid)
            .putInt(KEY_PATIENT_ID, id)
            .putString(KEY_PATIENT_NAME, name)
            .apply()
    }
    
    /**
     * Ottiene l'UUID del paziente
     */
    fun getPatientUUID(): String? {
        return sharedPreferences.getString(KEY_PATIENT_UUID, null)
    }
    
    /**
     * Ottiene l'ID del paziente
     */
    fun getPatientId(): Int? {
        val id = sharedPreferences.getInt(KEY_PATIENT_ID, -1)
        return if (id != -1) id else null
    }
    
    /**
     * Ottiene il nome del paziente
     */
    fun getPatientName(): String? {
        return sharedPreferences.getString(KEY_PATIENT_NAME, null)
    }
    
    /**
     * Salva l'URL del server
     */
    fun saveServerUrl(url: String) {
        sharedPreferences.edit().putString(KEY_SERVER_URL, url).apply()
    }
    
    /**
     * Ottiene l'URL del server, con valore predefinito
     */
    fun getServerUrl(): String {
        return sharedPreferences.getString(KEY_SERVER_URL, "https://vitalink.replit.app") ?: "https://vitalink.replit.app"
    }
    
    /**
     * Aggiorna il timestamp dell'ultima sincronizzazione
     */
    fun updateLastSync(timestamp: Long) {
        sharedPreferences.edit().putLong(KEY_LAST_SYNC, timestamp).apply()
    }
    
    /**
     * Ottiene il timestamp dell'ultima sincronizzazione
     */
    fun getLastSync(): Long {
        return sharedPreferences.getLong(KEY_LAST_SYNC, 0)
    }
    
    /**
     * Salva l'indirizzo Bluetooth del dispositivo Fitbit associato
     */
    fun saveFitbitDeviceAddress(address: String) {
        sharedPreferences.edit().putString(KEY_FITBIT_DEVICE_ADDRESS, address).apply()
    }
    
    /**
     * Ottiene l'indirizzo Bluetooth del dispositivo Fitbit associato
     */
    fun getFitbitDeviceAddress(): String? {
        return sharedPreferences.getString(KEY_FITBIT_DEVICE_ADDRESS, null)
    }
    
    /**
     * Cancella tutte le preferenze (per logout)
     */
    fun clearAll() {
        sharedPreferences.edit().clear().apply()
    }
}