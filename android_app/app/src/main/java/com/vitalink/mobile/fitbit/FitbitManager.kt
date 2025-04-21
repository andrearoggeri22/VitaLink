package com.vitalink.mobile.fitbit

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.content.Context
import android.util.Log
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import com.vitalink.mobile.data.model.FitbitData
import com.vitalink.mobile.data.model.FitbitDevice
import com.vitalink.mobile.data.model.SyncStatus
import com.vitalink.mobile.data.model.VitalMeasurement
import com.vitalink.mobile.util.PreferenceManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import kotlin.random.Random

/**
 * Gestisce l'interazione con i dispositivi Fitbit tramite Bluetooth LE
 */
class FitbitManager(private val context: Context) {
    
    private val TAG = "FitbitManager"
    
    private val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
    private val bluetoothAdapter = bluetoothManager.adapter
    
    private val _status = MutableLiveData<SyncStatus>(SyncStatus.IDLE)
    val status: LiveData<SyncStatus> = _status
    
    private val _devices = MutableLiveData<List<FitbitDevice>>(emptyList())
    val devices: LiveData<List<FitbitDevice>> = _devices
    
    private val _currentDevice = MutableLiveData<FitbitDevice?>(null)
    val currentDevice: LiveData<FitbitDevice?> = _currentDevice
    
    /**
     * Controlla se il Bluetooth è abilitato sul dispositivo
     */
    fun isBluetoothEnabled(): Boolean {
        return bluetoothAdapter?.isEnabled == true
    }
    
    /**
     * Avvia la scansione dei dispositivi Fitbit nelle vicinanze
     */
    fun startScan() {
        if (!isBluetoothEnabled()) {
            Log.e(TAG, "Bluetooth non abilitato")
            return
        }
        
        _status.postValue(SyncStatus.CONNECTING)
        
        // Normalmente qui useremmo il Bluetooth LE scanner
        // Per questa demo, simuliamo il rilevamento di dispositivi
        
        CoroutineScope(Dispatchers.IO).launch {
            delay(1500) // Simula il tempo di scansione
            
            // Simula il rilevamento di dispositivi Fitbit
            val simulatedDevices = listOf(
                FitbitDevice(
                    address = "AA:BB:CC:DD:EE:01",
                    name = "Fitbit Versa 3",
                    rssi = -65
                ),
                FitbitDevice(
                    address = "AA:BB:CC:DD:EE:02",
                    name = "Fitbit Sense",
                    rssi = -72
                ),
                FitbitDevice(
                    address = "AA:BB:CC:DD:EE:03",
                    name = "Fitbit Charge 5",
                    rssi = -58
                )
            )
            
            _devices.postValue(simulatedDevices)
            _status.postValue(SyncStatus.IDLE)
        }
    }
    
    /**
     * Connette al dispositivo Fitbit specificato
     */
    fun connectToDevice(device: FitbitDevice) {
        _status.postValue(SyncStatus.CONNECTING)
        _currentDevice.postValue(device)
        
        CoroutineScope(Dispatchers.IO).launch {
            delay(2000) // Simula il tempo di connessione
            
            // Salva l'indirizzo del dispositivo per future connessioni automatiche
            PreferenceManager.saveFitbitDeviceAddress(device.address)
            
            // Aggiorna lo stato
            val connectedDevice = device.copy(isConnected = true)
            _currentDevice.postValue(connectedDevice)
            _status.postValue(SyncStatus.CONNECTED)
        }
    }
    
    /**
     * Disconnette dal dispositivo Fitbit corrente
     */
    fun disconnectFromDevice() {
        _currentDevice.value?.let { device ->
            _status.postValue(SyncStatus.IDLE)
            _currentDevice.postValue(device.copy(isConnected = false))
        }
    }
    
    /**
     * Estrae i dati dal dispositivo Fitbit connesso
     */
    suspend fun syncData(): Result<FitbitData> = withContext(Dispatchers.IO) {
        try {
            if (_currentDevice.value?.isConnected != true) {
                return@withContext Result.failure(Exception("Nessun dispositivo connesso"))
            }
            
            _status.postValue(SyncStatus.SYNCING)
            
            // In un'implementazione reale, qui comunicheremmo con il dispositivo Fitbit
            // Per questa demo, generiamo dati simulati
            delay(3000) // Simula il tempo di sincronizzazione
            
            val fitbitData = generateSimulatedData()
            
            _status.postValue(SyncStatus.SUCCESS)
            
            Result.success(fitbitData)
        } catch (e: Exception) {
            Log.e(TAG, "Errore durante la sincronizzazione dei dati", e)
            _status.postValue(SyncStatus.ERROR)
            Result.failure(e)
        }
    }
    
    /**
     * Genera dati simulati per test e demo
     */
    private fun generateSimulatedData(): FitbitData {
        val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
        val calendar = Calendar.getInstance()
        
        // Genera dati frequenza cardiaca per le ultime 24 ore, a intervalli di 1 ora
        val heartRateData = mutableListOf<VitalMeasurement>()
        for (i in 24 downTo 1) {
            calendar.time = Date()
            calendar.add(Calendar.HOUR, -i)
            
            heartRateData.add(
                VitalMeasurement(
                    timestamp = dateFormat.format(calendar.time),
                    value = 65f + Random.nextFloat() * 30f // 65-95 bpm
                )
            )
        }
        
        // Genera dati passi per gli ultimi 7 giorni
        val stepsData = mutableListOf<VitalMeasurement>()
        calendar.time = Date()
        calendar.set(Calendar.HOUR_OF_DAY, 0)
        calendar.set(Calendar.MINUTE, 0)
        calendar.set(Calendar.SECOND, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        
        val dateOnlyFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
        
        for (i in 7 downTo 1) {
            calendar.time = Date()
            calendar.add(Calendar.DAY_OF_YEAR, -i)
            
            stepsData.add(
                VitalMeasurement(
                    timestamp = dateOnlyFormat.format(calendar.time),
                    value = 5000f + Random.nextFloat() * 7000f // 5000-12000 passi
                )
            )
        }
        
        // Genera dati calorie per gli ultimi 7 giorni
        val caloriesData = mutableListOf<VitalMeasurement>()
        for (i in 7 downTo 1) {
            calendar.time = Date()
            calendar.add(Calendar.DAY_OF_YEAR, -i)
            
            caloriesData.add(
                VitalMeasurement(
                    timestamp = dateOnlyFormat.format(calendar.time),
                    value = 1800f + Random.nextFloat() * 800f // 1800-2600 calorie
                )
            )
        }
        
        // Genera dati distanza per gli ultimi 7 giorni
        val distanceData = mutableListOf<VitalMeasurement>()
        for (i in 7 downTo 1) {
            calendar.time = Date()
            calendar.add(Calendar.DAY_OF_YEAR, -i)
            
            distanceData.add(
                VitalMeasurement(
                    timestamp = dateOnlyFormat.format(calendar.time),
                    value = 3f + Random.nextFloat() * 5f // 3-8 km
                )
            )
        }
        
        // Genera dati minuti attivi per gli ultimi 7 giorni
        val activeMinutesData = mutableListOf<VitalMeasurement>()
        for (i in 7 downTo 1) {
            calendar.time = Date()
            calendar.add(Calendar.DAY_OF_YEAR, -i)
            
            activeMinutesData.add(
                VitalMeasurement(
                    timestamp = dateOnlyFormat.format(calendar.time),
                    value = 30f + Random.nextFloat() * 90f // 30-120 minuti
                )
            )
        }
        
        // Genera dati sonno per gli ultimi 7 giorni
        val sleepData = mutableListOf<VitalMeasurement>()
        for (i in 7 downTo 1) {
            calendar.time = Date()
            calendar.add(Calendar.DAY_OF_YEAR, -i)
            
            sleepData.add(
                VitalMeasurement(
                    timestamp = dateOnlyFormat.format(calendar.time),
                    value = 6f + Random.nextFloat() * 3f // 6-9 ore
                )
            )
        }
        
        // Genera dati piani saliti per gli ultimi 7 giorni
        val floorsData = mutableListOf<VitalMeasurement>()
        for (i in 7 downTo 1) {
            calendar.time = Date()
            calendar.add(Calendar.DAY_OF_YEAR, -i)
            
            floorsData.add(
                VitalMeasurement(
                    timestamp = dateOnlyFormat.format(calendar.time),
                    value = 5f + Random.nextFloat() * 15f // 5-20 piani
                )
            )
        }
        
        return FitbitData(
            heart_rate = heartRateData,
            steps = stepsData,
            calories = caloriesData,
            distance = distanceData,
            active_minutes = activeMinutesData,
            sleep_duration = sleepData,
            floors_climbed = floorsData
        )
    }
    
    /**
     * Verifica se esiste un dispositivo precedentemente associato
     * e, in caso affermativo, tenta di riconnettersi automaticamente
     */
    fun reconnectToSavedDevice() {
        val savedDeviceAddress = PreferenceManager.getFitbitDeviceAddress() ?: return
        
        // Simula la riconnessione a un dispositivo salvato
        val savedDevice = FitbitDevice(
            address = savedDeviceAddress,
            name = if (savedDeviceAddress.endsWith("01")) "Fitbit Versa 3" 
                  else if (savedDeviceAddress.endsWith("02")) "Fitbit Sense" 
                  else "Fitbit Charge 5",
            rssi = -65
        )
        
        connectToDevice(savedDevice)
    }
    
    /**
     * Metodo per aggiornare lo stato manualmente (usato dal ViewModel)
     */
    fun updateStatus(newStatus: SyncStatus) {
        _status.postValue(newStatus)
    }
    
    companion object {
        private var instance: FitbitManager? = null
        
        fun getInstance(context: Context): FitbitManager {
            if (instance == null) {
                synchronized(this) {
                    if (instance == null) {
                        instance = FitbitManager(context.applicationContext)
                    }
                }
            }
            return instance!!
        }
    }
}