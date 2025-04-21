package com.vitalink.mobile.util

import android.content.Context
import android.content.res.Configuration
import android.content.res.Resources
import android.os.Build
import java.util.Locale

/**
 * Helper per la gestione delle impostazioni linguistiche dell'app
 */
object LocaleHelper {
    
    private const val LANGUAGE_PREFERENCE = "language_preference"
    
    /**
     * Imposta la lingua dell'applicazione
     * 
     * @param context Contesto dell'applicazione
     * @param languageCode Codice della lingua (es. "it", "en")
     * @return Contesto aggiornato con la nuova impostazione linguistica
     */
    fun setLocale(context: Context, languageCode: String): Context {
        saveLanguagePreference(context, languageCode)
        
        return updateResources(context, languageCode)
    }
    
    /**
     * Ottiene la lingua corrente dell'applicazione
     * 
     * @param context Contesto dell'applicazione
     * @return Codice della lingua corrente (es. "it", "en")
     */
    fun getLanguage(context: Context): String {
        return PreferenceManager.getLanguage() ?: getDeviceLanguage()
    }
    
    /**
     * Salva la preferenza linguistica
     * 
     * @param context Contesto dell'applicazione
     * @param languageCode Codice della lingua da salvare
     */
    private fun saveLanguagePreference(context: Context, languageCode: String) {
        PreferenceManager.saveLanguage(languageCode)
    }
    
    /**
     * Aggiorna le risorse con la lingua specificata
     * 
     * @param context Contesto dell'applicazione
     * @param languageCode Codice della lingua da impostare
     * @return Contesto aggiornato con la nuova configurazione
     */
    private fun updateResources(context: Context, languageCode: String): Context {
        val locale = Locale(languageCode)
        Locale.setDefault(locale)
        
        val configuration = Configuration(context.resources.configuration)
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            configuration.setLocale(locale)
            return context.createConfigurationContext(configuration)
        } else {
            configuration.locale = locale
            context.resources.updateConfiguration(configuration, context.resources.displayMetrics)
            return context
        }
    }
    
    /**
     * Ottiene la lingua del dispositivo
     * 
     * @return Codice della lingua del dispositivo o "en" come default
     */
    private fun getDeviceLanguage(): String {
        return Locale.getDefault().language.let { if (it == "it" || it == "en") it else "en" }
    }
    
    /**
     * Applica la lingua salvata al contesto corrente
     * 
     * @param context Contesto dell'applicazione
     * @return Contesto aggiornato con la lingua salvata
     */
    fun applyStoredLanguage(context: Context): Context {
        val language = getLanguage(context)
        return setLocale(context, language)
    }
}