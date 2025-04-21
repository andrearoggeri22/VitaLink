package com.vitalink.mobile

import android.app.Application
import android.content.Context
import android.content.res.Configuration
import com.vitalink.mobile.util.LocaleHelper
import com.vitalink.mobile.util.PreferenceManager

/**
 * Classe principale dell'applicazione VitaLink Mobile
 * Inizializza i componenti globali dell'app
 */
class VitaLinkApplication : Application() {
    
    companion object {
        lateinit var appContext: Context
            private set
    }
    
    override fun onCreate() {
        super.onCreate()
        appContext = applicationContext
        
        // Inizializza il PreferenceManager
        PreferenceManager.init(this)
        
        // Inizializza altri componenti dell'app se necessario
    }
    
    /**
     * Override di attachBaseContext per applicare la lingua salvata
     * prima che il contesto base venga creato
     */
    override fun attachBaseContext(base: Context) {
        // Applica la lingua salvata nelle preferenze
        val context = LocaleHelper.applyStoredLanguage(base)
        super.attachBaseContext(context)
    }
    
    /**
     * Override di onConfigurationChanged per mantenere la lingua selezionata
     * anche quando la configurazione del dispositivo cambia
     */
    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        // Riapplica la lingua quando cambia la configurazione
        LocaleHelper.applyStoredLanguage(this)
    }
}