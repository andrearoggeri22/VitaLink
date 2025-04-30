import pytest
import json
from datetime import datetime, timedelta
import os
from unittest.mock import patch, MagicMock

def test_generate_vital_report(authenticated_client, test_patient, test_vital_observation):
    """Verifica la generazione di un report per i parametri vitali."""
    # Ottieni il tipo di parametro vitale dall'osservazione di test
    vital_type = test_vital_observation.vital_type.value
    
    # Richiedi la generazione di un report
    from_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    to_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/reports/generate',
        data={
            'report_type': 'vital',
            'vital_type': vital_type,
            'from_date': from_date,
            'to_date': to_date
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il report sia stato generato correttamente
    success_indicators = [b'report', b'generato', b'generated', b'download', b'scarica']
    assert any(indicator in response.data.lower() for indicator in success_indicators)
    
    # Verifica l'audit log
    from app.models import AuditLog, ActionType, EntityType
    audit = AuditLog.query.filter_by(
        action_type=ActionType.EXPORT,
        entity_type=EntityType.REPORT
    ).first()
    assert audit is not None
    assert audit.patient_id == test_patient.id

@patch('app.reports.create_vital_chart')
def test_vital_chart_generation(mock_create_chart, authenticated_client, test_patient, test_vital_observation):
    """Verifica la generazione di un grafico per i parametri vitali."""
    # Configura il mock
    mock_chart_path = os.path.join(os.getcwd(), 'test_chart.png')
    mock_create_chart.return_value = mock_chart_path
    
    # Ottieni il tipo di parametro vitale dall'osservazione di test
    vital_type = test_vital_observation.vital_type.value
    
    # Richiedi la generazione di un grafico
    from_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    to_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    response = authenticated_client.get(
        f'/patients/{test_patient.uuid}/vitals/chart?type={vital_type}&from={from_date}&to={to_date}'
    )
    assert response.status_code == 200
    
    # Verifica che il mock sia stato chiamato correttamente
    mock_create_chart.assert_called_once()
    args = mock_create_chart.call_args[0]
    assert args[0] == test_patient
    assert args[1] == test_vital_observation.vital_type

def test_patient_summary_report(authenticated_client, test_patient, test_note, test_vital_observation):
    """Verifica la generazione di un report di riepilogo per un paziente."""
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/reports/generate',
        data={
            'report_type': 'summary'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il report sia stato generato correttamente
    success_indicators = [b'report', b'generato', b'generated', b'download', b'scarica']
    assert any(indicator in response.data.lower() for indicator in success_indicators)

    # Verifica l'audit log
    from app.models import AuditLog, ActionType, EntityType
    audit = AuditLog.query.filter_by(
        action_type=ActionType.EXPORT,
        entity_type=EntityType.REPORT,
        patient_id=test_patient.id
    ).order_by(AuditLog.timestamp.desc()).first()
    assert audit is not None

@patch('app.reports.create_pdf')
def test_specific_report_generation(mock_create_pdf, authenticated_client, test_patient, test_note):
    """Verifica la generazione di un report specifico."""
    # Configura il mock
    mock_pdf_path = os.path.join(os.getcwd(), 'test_report.pdf')
    mock_create_pdf.return_value = mock_pdf_path
    
    # Richiedi la generazione di un report specifico
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/reports/specific',
        data={
            'title': 'Report di test',
            'description': 'Questo è un report di test per verificare la funzionalità',
            'content': 'Il paziente presenta i seguenti sintomi: test, test, test.',
            'include_vitals': 'true',
            'include_notes': 'true'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il report sia stato generato correttamente
    success_indicators = [b'report', b'generato', b'generated', b'download', b'scarica']
    assert any(indicator in response.data.lower() for indicator in success_indicators)
    
    # Verifica che il mock sia stato chiamato correttamente
    mock_create_pdf.assert_called_once()
    
    # Verifica l'audit log
    from app.models import AuditLog, ActionType, EntityType
    audit = AuditLog.query.filter_by(
        action_type=ActionType.EXPORT,
        entity_type=EntityType.REPORT,
        patient_id=test_patient.id
    ).order_by(AuditLog.timestamp.desc()).first()
    assert audit is not None

def test_export_patient_data(authenticated_client, test_patient, test_note, test_vital_observation):
    """Verifica l'esportazione dei dati di un paziente in formato JSON."""
    response = authenticated_client.get(
        f'/patients/{test_patient.uuid}/export'
    )
    assert response.status_code == 200
    
    # Verifica che la risposta sia in formato JSON
    assert response.content_type == 'application/json'
    
    # Verifica il contenuto
    data = json.loads(response.data)
    assert 'patient' in data
    assert data['patient']['uuid'] == test_patient.uuid
    
    # Verifica che ci siano le note e le osservazioni vitali
    assert 'notes' in data
    assert len(data['notes']) > 0
    
    assert 'vital_observations' in data
    assert len(data['vital_observations']) > 0
    
    # Verifica l'audit log
    from app.models import AuditLog, ActionType, EntityType
    audit = AuditLog.query.filter_by(
        action_type=ActionType.EXPORT,
        entity_type=EntityType.PATIENT,
        patient_id=test_patient.id
    ).order_by(AuditLog.timestamp.desc()).first()
    assert audit is not None
