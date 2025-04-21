package com.vitalink.mobile.ui.settings

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.RadioButton
import android.widget.RadioGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import com.vitalink.mobile.R
import com.vitalink.mobile.MainActivity
import com.vitalink.mobile.util.LocaleHelper
import java.util.Locale

/**
 * Fragment per la gestione delle impostazioni della lingua
 */
class LanguageSettingsFragment : Fragment() {
    
    private lateinit var radioGroup: RadioGroup
    private lateinit var radioEnglish: RadioButton
    private lateinit var radioItalian: RadioButton
    private lateinit var titleText: TextView
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val view = inflater.inflate(R.layout.fragment_language_settings, container, false)
        
        titleText = view.findViewById(R.id.language_settings_title)
        radioGroup = view.findViewById(R.id.language_radio_group)
        radioEnglish = view.findViewById(R.id.radio_english)
        radioItalian = view.findViewById(R.id.radio_italian)
        
        // Imposta il titolo
        titleText.text = getString(R.string.settings_language)
        
        // Imposta i testi dei radio button
        radioEnglish.text = getString(R.string.settings_language_english)
        radioItalian.text = getString(R.string.settings_language_italian)
        
        // Seleziona il radio button corrispondente alla lingua corrente
        val currentLanguage = LocaleHelper.getLanguage(requireContext())
        when (currentLanguage) {
            "en" -> radioEnglish.isChecked = true
            "it" -> radioItalian.isChecked = true
        }
        
        // Aggiungi listener per il cambio di lingua
        radioGroup.setOnCheckedChangeListener { _, checkedId ->
            val languageCode = when (checkedId) {
                R.id.radio_english -> "en"
                R.id.radio_italian -> "it"
                else -> "en" // Default a inglese
            }
            
            // Se la lingua è cambiata, applica e riavvia l'attività
            if (languageCode != currentLanguage) {
                LocaleHelper.setLocale(requireContext(), languageCode)
                restartApp()
            }
        }
        
        return view
    }
    
    /**
     * Riavvia l'app per applicare il cambio di lingua
     */
    private fun restartApp() {
        val intent = Intent(activity, MainActivity::class.java)
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK)
        startActivity(intent)
        activity?.finish()
    }
}