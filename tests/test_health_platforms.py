import pytest
import json
from datetime import datetime, timedelta
import uuid
from unittest.mock import patch, MagicMock

def test_health_platform_link_generation(authenticated_client, test_patient):
    """Verifica la generazione di un link per l'integrazione con piattaforme sanitarie."""
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/health-platforms/generate-link',
        data={'platform': 'fitbit'},
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il link sia stato generato
    assert b'success' in response.data.lower() or b'generato' in response.data.lower() or b'generated' in response.data.lower()
    
    # Verifica nel database
    from app.models import HealthPlatformLink, HealthPlatform
    link = HealthPlatformLink.query.filter_by(
        patient_id=test_patient.id,
        platform=HealthPlatform.FITBIT
    ).first()
    assert link is not None
    assert link.uuid is not None
    assert link.used is False
    assert link.expires_at > datetime.utcnow()

# Test dell'integrazione con Fitbit (mock)
@patch('app.health_platforms.FitbitAPI')
def test_fitbit_integration(mock_fitbit_api, authenticated_client, test_doctor, test_patient):
    """Test dell'integrazione con Fitbit (simulato)."""
    # Configura il mock per simulare l'API Fitbit
    mock_instance = MagicMock()
    mock_fitbit_api.return_value = mock_instance
    
    # Simula una risposta di autorizzazione OAuth
    mock_instance.exchange_authorization_code.return_value = {
        'access_token': 'mock_access_token',
        'refresh_token': 'mock_refresh_token',
        'expires_in': 3600  # 1 ora
    }
    
    # Simula i dati di activity
    mock_instance.get_activities.return_value = {
        'activities': [
            {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'steps': 8500,
                'calories': 2200,
                'distance': 6.7,
                'floors': 15,
                'elevation': 45.7,
                'minutesSedentary': 480,
                'minutesLightlyActive': 120,
                'minutesFairlyActive': 60,
                'minutesVeryActive': 30
            }
        ]
    }
    
    # Crea un nuovo link per l'integrazione
    from app.app import db
    from app.models import HealthPlatformLink, HealthPlatform
    
    link = HealthPlatformLink(
        uuid=str(uuid.uuid4()),
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        platform=HealthPlatform.FITBIT,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        used=False
    )
    db.session.add(link)
    db.session.commit()
    
    # Simula il callback di OAuth con il codice di autorizzazione
    response = authenticated_client.get(
        f'/health-connect/callback?code=mock_auth_code&state={link.uuid}',
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il link sia stato contrassegnato come utilizzato
    link = HealthPlatformLink.query.get(link.id)
    assert link.used is True
    
    # Verifica che il paziente abbia i token salvati
    test_patient = db.session.query(db.session.query(test_patient.__class__).get(test_patient.id))
    assert test_patient.platform_access_token == 'mock_access_token'
    assert test_patient.platform_refresh_token == 'mock_refresh_token'
    assert test_patient.connected_platform == HealthPlatform.FITBIT
    
    # Test della sincronizzazione dei dati
    with patch('app.health_platforms.is_token_expired', return_value=False):
        response = authenticated_client.post(
            f'/patients/{test_patient.uuid}/health-platforms/sync',
            data={'platform': 'fitbit'},
            follow_redirects=True
        )
        assert response.status_code == 200
    
    # Verifica che il mock sia stato chiamato correttamente
    mock_instance.get_activities.assert_called()
    
    # Verifica che siano state create le osservazioni vitali
    from app.models import VitalObservation, VitalSignType
    
    steps_observation = VitalObservation.query.filter_by(
        patient_id=test_patient.id,
        vital_type=VitalSignType.STEPS
    ).first()
    assert steps_observation is not None
    
    calories_observation = VitalObservation.query.filter_by(
        patient_id=test_patient.id,
        vital_type=VitalSignType.CALORIES
    ).first()
    assert calories_observation is not None

# Test dell'integrazione con Google Health Connect (mock)
@patch('app.health_platforms.GoogleHealthConnectAPI')
def test_google_health_connect_integration(mock_ghc_api, authenticated_client, test_doctor, test_patient):
    """Test dell'integrazione con Google Health Connect (simulato)."""
    # Configura il mock
    mock_instance = MagicMock()
    mock_ghc_api.return_value = mock_instance
    
    # Simula una risposta di autorizzazione
    mock_instance.exchange_authorization_code.return_value = {
        'access_token': 'mock_ghc_token',
        'refresh_token': 'mock_ghc_refresh',
        'expires_in': 3600
    }
    
    # Simula i dati di salute
    mock_instance.get_health_data.return_value = {
        'heart_rate': [
            {'value': 72, 'timestamp': datetime.now().isoformat()},
            {'value': 75, 'timestamp': (datetime.now() - timedelta(hours=1)).isoformat()}
        ],
        'steps': [
            {'value': 9800, 'timestamp': datetime.now().isoformat()}
        ],
        'oxygen_saturation': [
            {'value': 98, 'timestamp': datetime.now().isoformat()}
        ]
    }
    
    # Crea un nuovo link per l'integrazione
    from app.app import db
    from app.models import HealthPlatformLink, HealthPlatform
    
    link = HealthPlatformLink(
        uuid=str(uuid.uuid4()),
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        platform=HealthPlatform.GOOGLE_HEALTH_CONNECT,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        used=False
    )
    db.session.add(link)
    db.session.commit()
    
    # Simula il callback di OAuth con il codice di autorizzazione
    response = authenticated_client.get(
        f'/health-connect/callback?code=mock_auth_code&state={link.uuid}',
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il link sia stato contrassegnato come utilizzato
    link = HealthPlatformLink.query.get(link.id)
    assert link.used is True
    
    # Verifica che il paziente abbia i token salvati
    test_patient = db.session.query(db.session.query(test_patient.__class__).get(test_patient.id))
    assert test_patient.platform_access_token == 'mock_ghc_token'
    assert test_patient.platform_refresh_token == 'mock_ghc_refresh'
    assert test_patient.connected_platform == HealthPlatform.GOOGLE_HEALTH_CONNECT
    
    # Test della sincronizzazione dei dati
    with patch('app.health_platforms.is_token_expired', return_value=False):
        response = authenticated_client.post(
            f'/patients/{test_patient.uuid}/health-platforms/sync',
            data={'platform': 'google_health_connect'},
            follow_redirects=True
        )
        assert response.status_code == 200
    
    # Verifica che il mock sia stato chiamato correttamente
    mock_instance.get_health_data.assert_called()
    
    # Verifica che siano state create le osservazioni vitali
    from app.models import VitalObservation, VitalSignType
    
    hr_observation = VitalObservation.query.filter_by(
        patient_id=test_patient.id,
        vital_type=VitalSignType.HEART_RATE
    ).first()
    assert hr_observation is not None
    
    spo2_observation = VitalObservation.query.filter_by(
        patient_id=test_patient.id,
        vital_type=VitalSignType.OXYGEN_SATURATION
    ).first()
    assert spo2_observation is not None

def test_disconnect_health_platform(authenticated_client, test_doctor, test_patient):
    """Verifica la disconnessione di una piattaforma sanitaria."""
    # Prima configura una piattaforma collegata
    test_patient.connected_platform = HealthPlatform.FITBIT
    test_patient.platform_access_token = 'test_token'
    test_patient.platform_refresh_token = 'test_refresh'
    test_patient.platform_token_expires_at = datetime.utcnow() + timedelta(hours=1)
    
    from app.app import db
    db.session.commit()
    
    # Disconnetti la piattaforma
    response = authenticated_client.post(
        f'/patients/{test_patient.uuid}/health-platforms/disconnect',
        data={'platform': 'fitbit'},
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che la piattaforma sia stata disconnessa
    test_patient = db.session.query(db.session.query(test_patient.__class__).get(test_patient.id))
    assert test_patient.connected_platform is None
    assert test_patient.platform_access_token is None
    assert test_patient.platform_refresh_token is None
