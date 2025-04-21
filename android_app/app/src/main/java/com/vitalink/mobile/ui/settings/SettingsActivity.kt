package com.vitalink.mobile.ui.settings

import android.os.Bundle
import android.view.MenuItem
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.commit
import com.vitalink.mobile.BuildConfig
import com.vitalink.mobile.R
import com.vitalink.mobile.util.PreferenceManager

/**
 * Activity per la gestione delle impostazioni dell'app
 */
class SettingsActivity : AppCompatActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)
        
        // Configura la toolbar
        setSupportActionBar(findViewById(R.id.toolbar))
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = getString(R.string.settings_title)
        
        // Imposta il titolo della versione
        val versionView = findViewById<TextView>(R.id.settings_version)
        versionView.text = getString(R.string.settings_version, BuildConfig.VERSION_NAME)
        
        // Configura i click listener per le varie sezioni
        setupLanguageSettings()
        setupServerSettings()
        setupNotificationSettings()
        setupSyncSettings()
        setupLogoutButton()
    }
    
    /**
     * Configura la sezione delle impostazioni della lingua
     */
    private fun setupLanguageSettings() {
        val languageSettingsView = findViewById<LinearLayout>(R.id.settings_language_container)
        languageSettingsView.setOnClickListener {
            // Apre il fragment per le impostazioni della lingua
            supportFragmentManager.commit {
                replace(R.id.settings_fragment_container, LanguageSettingsFragment())
                addToBackStack(null)
            }
            
            // Mostra il container del fragment e nasconde la lista delle impostazioni
            findViewById<View>(R.id.settings_list_container).visibility = View.GONE
            findViewById<View>(R.id.settings_fragment_container).visibility = View.VISIBLE
        }
    }
    
    /**
     * Configura la sezione delle impostazioni del server
     */
    private fun setupServerSettings() {
        val serverUrlView = findViewById<TextView>(R.id.settings_server_url_value)
        serverUrlView.text = PreferenceManager.getServerUrl()
        
        val serverContainer = findViewById<LinearLayout>(R.id.settings_server_container)
        serverContainer.setOnClickListener {
            // Implementazione per modificare l'URL del server
            showServerUrlDialog()
        }
        
        val resetServerButton = findViewById<TextView>(R.id.settings_server_reset)
        resetServerButton.setOnClickListener {
            PreferenceManager.resetServerUrl()
            serverUrlView.text = PreferenceManager.getServerUrl()
        }
    }
    
    /**
     * Configura la sezione delle impostazioni delle notifiche
     */
    private fun setupNotificationSettings() {
        val notificationSwitch = findViewById<androidx.appcompat.widget.SwitchCompat>(R.id.settings_notification_switch)
        notificationSwitch.isChecked = PreferenceManager.areNotificationsEnabled()
        
        notificationSwitch.setOnCheckedChangeListener { _, isChecked ->
            PreferenceManager.setNotificationsEnabled(isChecked)
        }
    }
    
    /**
     * Configura la sezione delle impostazioni di sincronizzazione
     */
    private fun setupSyncSettings() {
        val syncSwitch = findViewById<androidx.appcompat.widget.SwitchCompat>(R.id.settings_sync_switch)
        syncSwitch.isChecked = PreferenceManager.isAutoSyncEnabled()
        
        syncSwitch.setOnCheckedChangeListener { _, isChecked ->
            PreferenceManager.setAutoSyncEnabled(isChecked)
            // Qui andrebbe aggiunta la logica per programmare o cancellare i job di sincronizzazione
        }
    }
    
    /**
     * Configura il pulsante di logout
     */
    private fun setupLogoutButton() {
        val logoutButton = findViewById<LinearLayout>(R.id.settings_logout_container)
        logoutButton.setOnClickListener {
            showLogoutConfirmationDialog()
        }
    }
    
    /**
     * Mostra una dialog per confermare il logout
     */
    private fun showLogoutConfirmationDialog() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.settings_logout))
            .setMessage("Sei sicuro di voler disconnettere l'app? Tutti i dati locali verranno eliminati.")
            .setPositiveButton(getString(R.string.ok_button)) { _, _ ->
                // Esegue il logout
                PreferenceManager.clearAll()
                // Torna alla schermata di onboarding
                // In una implementazione reale, dovremmo lanciare l'OnboardingActivity
                // e chiudere tutte le altre activity
                finish()
            }
            .setNegativeButton(getString(R.string.cancel_button), null)
            .show()
    }
    
    /**
     * Mostra una dialog per modificare l'URL del server
     */
    private fun showServerUrlDialog() {
        // In una implementazione reale, qui andrebbe mostrata una dialog
        // con un campo di testo per inserire il nuovo URL
    }
    
    /**
     * Gestisce il pulsante indietro nella toolbar
     */
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        if (item.itemId == android.R.id.home) {
            // Se siamo in un fragment e non nella lista principale delle impostazioni
            if (findViewById<View>(R.id.settings_fragment_container).visibility == View.VISIBLE) {
                onBackPressed()
                return true
            }
            finish()
            return true
        }
        return super.onOptionsItemSelected(item)
    }
    
    /**
     * Gestisce il pulsante indietro del dispositivo
     */
    override fun onBackPressed() {
        // Se siamo in un fragment, torna alla lista delle impostazioni
        if (findViewById<View>(R.id.settings_fragment_container).visibility == View.VISIBLE) {
            supportFragmentManager.popBackStack()
            findViewById<View>(R.id.settings_list_container).visibility = View.VISIBLE
            findViewById<View>(R.id.settings_fragment_container).visibility = View.GONE
            return
        }
        
        super.onBackPressed()
    }
}