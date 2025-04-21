package com.vitalink.mobile

import android.content.Intent
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import com.vitalink.mobile.data.model.SyncStatus
import com.vitalink.mobile.fitbit.FitbitManager
import com.vitalink.mobile.ui.settings.SettingsActivity
import com.vitalink.mobile.util.PreferenceManager
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : AppCompatActivity() {
    
    private lateinit var fitbitManager: FitbitManager
    private lateinit var viewModel: MainViewModel
    
    private lateinit var statusTextView: TextView
    private lateinit var lastSyncTextView: TextView
    private lateinit var deviceNameTextView: TextView
    private lateinit var patientInfoTextView: TextView
    private lateinit var syncButton: Button
    private lateinit var scanButton: Button
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Inizializza il FitbitManager
        fitbitManager = FitbitManager.getInstance(this)
        
        // Inizializza ViewModel
        viewModel = ViewModelProvider(this)[MainViewModel::class.java]
        
        // Inizializza le views
        setupViews()
        
        // Controlla se l'utente è già registrato
        checkUserRegistered()
        
        // Configura i listeners
        setupListeners()
        
        // Osserva i cambiamenti di stato
        observeState()
    }
    
    private fun setupViews() {
        // Trova le views nell'interfaccia
        statusTextView = findViewById(R.id.status_text)
        lastSyncTextView = findViewById(R.id.last_sync_text)
        deviceNameTextView = findViewById(R.id.device_name_text)
        patientInfoTextView = findViewById(R.id.patient_info_text)
        syncButton = findViewById(R.id.sync_button)
        scanButton = findViewById(R.id.scan_button)
        
        // Imposta la toolbar
        setSupportActionBar(findViewById(R.id.toolbar))
    }
    
    private fun checkUserRegistered() {
        // Controlla se l'utente ha già inserito il suo ID paziente
        if (PreferenceManager.getPatientId() == null) {
            // Se non registrato, vai alla schermata di onboarding
            // In una implementazione reale, dovremmo avviare OnboardingActivity
            // Per questa demo, usiamo dati simulati
            simulatePatientRegistration()
        } else {
            // Mostra i dati del paziente
            updatePatientInfo()
            
            // Prova a riconnettersi al dispositivo Fitbit salvato
            fitbitManager.reconnectToSavedDevice()
        }
    }
    
    private fun simulatePatientRegistration() {
        // Solo per scopi di demo
        PreferenceManager.savePatientId(12345)
        PreferenceManager.savePatientName("Mario Rossi")
        updatePatientInfo()
    }
    
    private fun updatePatientInfo() {
        val patientName = PreferenceManager.getPatientName() ?: "Paziente"
        val patientId = PreferenceManager.getPatientId()
        patientInfoTextView.text = "$patientName (ID: $patientId)"
    }
    
    private fun setupListeners() {
        // Listener per il pulsante di sincronizzazione
        syncButton.setOnClickListener {
            if (fitbitManager.isBluetoothEnabled()) {
                syncData()
            } else {
                showBluetoothDisabledMessage()
            }
        }
        
        // Listener per il pulsante di scansione
        scanButton.setOnClickListener {
            if (fitbitManager.isBluetoothEnabled()) {
                fitbitManager.startScan()
            } else {
                showBluetoothDisabledMessage()
            }
        }
    }
    
    private fun observeState() {
        // Osserva lo stato della sincronizzazione
        fitbitManager.status.observe(this) { status ->
            updateSyncStatus(status)
        }
        
        // Osserva il dispositivo corrente
        fitbitManager.currentDevice.observe(this) { device ->
            device?.let {
                deviceNameTextView.text = getString(R.string.fitbit_device_name, it.name)
                deviceNameTextView.visibility = View.VISIBLE
            } ?: run {
                deviceNameTextView.visibility = View.GONE
            }
        }
        
        // Osserva i dispositivi trovati
        fitbitManager.devices.observe(this) { devices ->
            if (devices.isNotEmpty()) {
                // In una implementazione reale, mostreremmo una lista di dispositivi
                // Per semplicità, ci connettiamo automaticamente al primo dispositivo
                fitbitManager.connectToDevice(devices[0])
            }
        }
    }
    
    private fun updateSyncStatus(status: SyncStatus) {
        // Aggiorna il testo dello stato
        val statusString = when (status) {
            SyncStatus.IDLE -> getString(R.string.status_idle)
            SyncStatus.CONNECTING -> getString(R.string.status_connecting)
            SyncStatus.CONNECTED -> getString(R.string.status_connected)
            SyncStatus.SYNCING -> getString(R.string.status_syncing)
            SyncStatus.UPLOADING -> getString(R.string.status_uploading)
            SyncStatus.SUCCESS -> getString(R.string.status_success)
            SyncStatus.ERROR -> getString(R.string.status_error)
        }
        
        statusTextView.text = getString(R.string.sync_status, statusString)
        
        // Aggiorna l'UI in base allo stato
        when (status) {
            SyncStatus.IDLE, SyncStatus.CONNECTED, SyncStatus.SUCCESS, SyncStatus.ERROR -> {
                syncButton.isEnabled = true
                scanButton.isEnabled = true
            }
            SyncStatus.CONNECTING, SyncStatus.SYNCING, SyncStatus.UPLOADING -> {
                syncButton.isEnabled = false
                scanButton.isEnabled = false
            }
        }
    }
    
    private fun syncData() {
        viewModel.syncFitbitData(this)
        
        // Aggiorna l'ora dell'ultima sincronizzazione
        PreferenceManager.saveLastSyncTimestamp()
        updateLastSyncTime()
    }
    
    private fun updateLastSyncTime() {
        val lastSyncTime = PreferenceManager.getLastSyncTimestamp()
        
        if (lastSyncTime != null) {
            val dateFormat = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault())
            val formattedDate = dateFormat.format(Date(lastSyncTime))
            lastSyncTextView.text = getString(R.string.last_sync, formattedDate)
        } else {
            lastSyncTextView.text = getString(R.string.never_synced)
        }
    }
    
    private fun showBluetoothDisabledMessage() {
        // In una implementazione reale, mostreremmo un dialog
        // Per semplicità, aggiorniamo solo il testo dello stato
        statusTextView.text = getString(R.string.error_bluetooth_disabled)
    }
    
    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.main_menu, menu)
        return true
    }
    
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_settings -> {
                startActivity(Intent(this, SettingsActivity::class.java))
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
    
    override fun onResume() {
        super.onResume()
        updateLastSyncTime()
    }
}