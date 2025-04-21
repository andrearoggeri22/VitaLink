package com.vitalink.mobile

import android.app.Application
import android.content.Intent
import androidx.work.Configuration
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.vitalink.mobile.service.FitbitSyncService
import com.vitalink.mobile.service.FitbitSyncWorker
import com.vitalink.mobile.util.PreferenceManager
import java.util.concurrent.TimeUnit

class VitaLinkApplication : Application(), Configuration.Provider {

    override fun onCreate() {
        super.onCreate()
        
        // Inizializza il gestore delle preferenze
        PreferenceManager.init(this)
        
        // Se l'utente ha già completato l'onboarding e ha un paziente verificato
        // avviamo automaticamente il servizio di sincronizzazione
        if (PreferenceManager.isOnboardingCompleted() && PreferenceManager.getPatientId() != null) {
            // Avvia il servizio di sincronizzazione in background
            startFitbitSyncService()
            
            // Configura il worker per la sincronizzazione periodica
            setupPeriodicSync()
        }
    }
    
    /**
     * Avvia il servizio di sincronizzazione Fitbit in background
     */
    private fun startFitbitSyncService() {
        val serviceIntent = Intent(this, FitbitSyncService::class.java)
        startService(serviceIntent)
    }
    
    /**
     * Configura la sincronizzazione periodica dei dati con WorkManager
     */
    private fun setupPeriodicSync() {
        // Definisce i vincoli per l'esecuzione del worker
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED) // Richiede connessione internet
            .build()
        
        // Crea una richiesta di lavoro periodico che si ripete ogni 6 ore
        val syncWorkRequest = PeriodicWorkRequestBuilder<FitbitSyncWorker>(
            6, TimeUnit.HOURS
        )
        .setConstraints(constraints)
        .build()
        
        // Pianifica il worker e sostituisce qualsiasi lavoro esistente con lo stesso nome
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "fitbit_periodic_sync",
            ExistingPeriodicWorkPolicy.REPLACE,
            syncWorkRequest
        )
    }
    
    override fun getWorkManagerConfiguration(): Configuration {
        return Configuration.Builder()
            .setMinimumLoggingLevel(android.util.Log.INFO)
            .build()
    }
}