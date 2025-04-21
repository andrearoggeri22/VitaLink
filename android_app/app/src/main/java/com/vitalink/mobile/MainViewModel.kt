package com.vitalink.mobile

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalink.mobile.data.model.SyncStatus
import com.vitalink.mobile.fitbit.FitbitManager
import com.vitalink.mobile.network.ApiClient
import com.vitalink.mobile.util.PreferenceManager
import kotlinx.coroutines.launch

/**
 * ViewModel principale dell'applicazione
 */
class MainViewModel : ViewModel() {
    
    private val fitbitManager = FitbitManager.getInstance(VitaLinkApplication.appContext)
    private val apiClient = ApiClient.getInstance()
    
    /**
     * Sincronizza i dati dal dispositivo Fitbit e li carica sul server
     */
    fun syncFitbitData(context: Context) {
        viewModelScope.launch {
            val patientId = PreferenceManager.getPatientId() ?: return@launch
            
            // Verifica se il dispositivo è connesso
            if (fitbitManager.currentDevice.value?.isConnected != true) {
                fitbitManager.reconnectToSavedDevice()
            }
            
            // Estrai i dati dal dispositivo
            val dataResult = fitbitManager.syncData()
            
            if (dataResult.isSuccess) {
                // Aggiorna lo stato a "uploading"
                (fitbitManager as FitbitManager).updateStatus(SyncStatus.UPLOADING)
                
                // Carica i dati sul server
                val uploadResult = apiClient.uploadFitbitData(patientId, dataResult.getOrThrow())
                
                if (uploadResult.isSuccess) {
                    // Aggiorna lo stato a "success"
                    (fitbitManager as FitbitManager).updateStatus(SyncStatus.SUCCESS)
                } else {
                    // Aggiorna lo stato a "error"
                    (fitbitManager as FitbitManager).updateStatus(SyncStatus.ERROR)
                }
            } else {
                // Aggiorna lo stato a "error"
                (fitbitManager as FitbitManager).updateStatus(SyncStatus.ERROR)
            }
        }
    }
}