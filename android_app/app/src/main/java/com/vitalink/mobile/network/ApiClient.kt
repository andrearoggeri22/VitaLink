package com.vitalink.mobile.network

import android.content.Context
import android.util.Log
import com.vitalink.mobile.data.model.FitbitData
import com.vitalink.mobile.data.model.PatientResponse
import com.vitalink.mobile.data.model.UploadResponse
import com.vitalink.mobile.util.PreferenceManager
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Client per le API REST del backend VitaLink
 */
class ApiClient {
    
    private val TAG = "ApiClient"
    
    private val apiService: ApiService
    
    init {
        val httpClient = createHttpClient()
        
        val retrofit = Retrofit.Builder()
            .baseUrl(PreferenceManager.getServerUrl())
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        
        apiService = retrofit.create(ApiService::class.java)
    }
    
    /**
     * Crea e configura un client HTTP con logging e timeout
     */
    private fun createHttpClient(): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        
        return OkHttpClient.Builder()
            .addInterceptor(logging)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }
    
    /**
     * Verifica l'UUID del paziente con il server
     * 
     * @param patientUuid UUID del paziente da verificare
     * @return Risultato della verifica
     */
    suspend fun verifyPatient(patientUuid: String): Result<PatientResponse> {
        return try {
            val request = VerifyPatientRequest(patientUuid)
            val response = apiService.verifyPatient(request)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                val errorMessage = response.errorBody()?.string() ?: "Errore sconosciuto"
                Log.e(TAG, "Errore durante la verifica del paziente: $errorMessage")
                Result.failure(Exception(errorMessage))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Eccezione durante la verifica del paziente", e)
            Result.failure(e)
        }
    }
    
    /**
     * Carica i dati Fitbit nel sistema
     * 
     * @param patientId ID del paziente a cui appartengono i dati
     * @param data I dati Fitbit da caricare
     * @return Risultato del caricamento
     */
    suspend fun uploadFitbitData(patientId: Int, data: FitbitData): Result<UploadResponse> {
        return try {
            val request = UploadDataRequest(patientId, data)
            val response = apiService.uploadFitbitData(request)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                val errorMessage = response.errorBody()?.string() ?: "Errore sconosciuto"
                Log.e(TAG, "Errore durante il caricamento dati: $errorMessage")
                Result.failure(Exception(errorMessage))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Eccezione durante il caricamento dati", e)
            Result.failure(e)
        }
    }
    
    companion object {
        private var instance: ApiClient? = null
        
        fun getInstance(): ApiClient {
            if (instance == null) {
                synchronized(this) {
                    if (instance == null) {
                        instance = ApiClient()
                    }
                }
            }
            return instance!!
        }
    }
}