package com.vitalink.mobile.network

import com.vitalink.mobile.data.model.FitbitData
import com.vitalink.mobile.data.model.PatientResponse
import com.vitalink.mobile.data.model.UploadResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

/**
 * Interface che definisce i servizi API per il backend VitaLink
 */
interface ApiService {
    
    /**
     * Verifica l'ID paziente e restituisce informazioni di base se valido
     * 
     * @param request La richiesta contenente l'UUID del paziente
     * @return Una risposta che contiene le informazioni del paziente se trovato
     */
    @POST("api/mobile/patient/verify")
    suspend fun verifyPatient(@Body request: VerifyPatientRequest): Response<PatientResponse>
    
    /**
     * Carica i dati Fitbit nel sistema
     * 
     * @param request La richiesta contenente l'ID paziente e i dati Fitbit
     * @return Una risposta che indica il successo o fallimento del caricamento
     */
    @POST("api/mobile/data/upload")
    suspend fun uploadFitbitData(@Body request: UploadDataRequest): Response<UploadResponse>
}

/**
 * Classe per la richiesta di verifica paziente
 */
data class VerifyPatientRequest(val patient_uuid: String)

/**
 * Classe per la richiesta di caricamento dati
 */
data class UploadDataRequest(
    val patient_id: Int,
    val fitbit_data: FitbitData
)