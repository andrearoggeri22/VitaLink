# VitaLink - Test Suite

Questa cartella contiene i test completi per il progetto VitaLink. I test coprono funzionalità unitarie e di integrazione per tutti i componenti dell'applicazione.

## Struttura dei Test

La suite di test è organizzata nei seguenti file:

- `test_models.py`: Test dei modelli del database
- `test_auth.py`: Test dell'autenticazione e gestione utenti
- `test_views.py`: Test delle viste web e delle pagine HTML
- `test_api.py`: Test delle API REST
- `test_health_platforms.py`: Test dell'integrazione con piattaforme sanitarie
- `test_reports.py`: Test delle funzionalità di reportistica
- `test_audit.py`: Test del sistema di audit log
- `test_utils.py`: Test delle utilità varie
- `test_i18n.py`: Test dell'internazionalizzazione e traduzione

## Requisiti

Per eseguire i test è necessario aver installato:

- Python 3.8+
- pytest
- pytest-cov (opzionale, per report di copertura)
- Faker (per generazione di dati casuali)

Installare le dipendenze con:

```
pip install pytest pytest-cov Faker
```

## Esecuzione dei Test

### Eseguire tutti i test

Per eseguire tutti i test, usare il comando:

```bash
python run_tests.py
```

Questo script:
1. Crea un account di test nel database se non esiste
2. Avvia tutti i test
3. Genera un report di copertura (se pytest-cov è installato)

### Eseguire test specifici

Per eseguire solo un file di test specifico:

```bash
pytest tests/test_auth.py -v
```

Per eseguire un test specifico:

```bash
pytest tests/test_auth.py::test_login_success -v
```

## Test Database

I test utilizzano un database SQLite in memoria, quindi non interferiscono con il database di produzione o sviluppo. Ogni test inizia con un database pulito.

## Copertura del Codice

Per generare un report di copertura dettagliato:

```bash
pytest --cov=app --cov-report=html:tests/coverage_html tests/
```

Questo genererà un report HTML nella cartella `tests/coverage_html/`.

## Account di Test

Lo script `run_tests.py` crea automaticamente un account di test se non esiste già:

- Email: test@vitalink.com
- Password: TestVitaLink123!

Questo account può essere utilizzato per test manuali.

## Note Importanti

- I test di integrazione con piattaforme sanitarie come Fitbit e Google Health Connect utilizzano mock per simulare le API esterne.
- I test delle funzionalità di reportistica potrebbero generare file temporanei nella cartella di test.
- Alcuni test potrebbero fallire se le API esterne cambiano la loro struttura o comportamento.
