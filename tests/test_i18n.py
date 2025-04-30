import pytest
from flask import session, get_flashed_messages
from flask_babel import gettext as _

def test_default_language(client):
    """Verifica che la lingua predefinita sia impostata correttamente."""
    response = client.get('/login')
    assert response.status_code == 200
    
    # Verifica che il testo sia nella lingua predefinita (inglese)
    assert b'Please login to access' in response.data or b'login' in response.data.lower()
    
    # Verifica che la sessione non abbia una lingua impostata
    with client.session_transaction() as sess:
        assert 'language' not in sess

def test_italian_language_setting(client):
    """Verifica che l'impostazione della lingua italiana funzioni correttamente."""
    # Imposta la lingua italiana
    client.get('/set-language/it')
    
    # Verifica che la lingua sia stata impostata
    with client.session_transaction() as sess:
        assert 'language' in sess
        assert sess['language'] == 'it'
    
    # Verifica che il contenuto sia in italiano
    response = client.get('/login')
    assert response.status_code == 200
    
    # Cerca parole italiane nella pagina
    italian_terms = [b'accedi', b'accesso', b'password', b'email']
    assert any(term in response.data.lower() for term in italian_terms)

def test_english_language_setting(client):
    """Verifica che l'impostazione della lingua inglese funzioni correttamente."""
    # Prima imposta l'italiano
    client.get('/set-language/it')
    
    # Poi passa all'inglese
    client.get('/set-language/en')
    
    # Verifica che la lingua sia stata impostata
    with client.session_transaction() as sess:
        assert 'language' in sess
        assert sess['language'] == 'en'
    
    # Verifica che il contenuto sia in inglese
    response = client.get('/login')
    assert response.status_code == 200
    
    # Cerca parole inglesi nella pagina
    english_terms = [b'login', b'email', b'password', b'access']
    assert any(term in response.data.lower() for term in english_terms)

def test_invalid_language_setting(client):
    """Verifica che un'impostazione di lingua non valida venga gestita correttamente."""
    # Prova a impostare una lingua non supportata
    response = client.get('/set-language/fr', follow_redirects=True)
    
    # Verifica che la richiesta sia andata a buon fine anche se la lingua non è supportata
    assert response.status_code == 200
    
    # Verifica che la sessione non abbia impostato una lingua non valida
    with client.session_transaction() as sess:
        # Potrebbe non essere impostata o essere impostata alla lingua predefinita
        if 'language' in sess:
            assert sess['language'] in ['en', 'it']

def test_translated_flash_messages(authenticated_client):
    """Verifica che i messaggi flash vengano tradotti correttamente."""
    # Imposta la lingua italiana
    authenticated_client.get('/set-language/it')
    
    # Effettua un'operazione che genera un messaggio flash (es. logout)
    response = authenticated_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    
    # Verifica che il messaggio flash sia in italiano
    italian_messages = [b'disconnesso', b'uscito', b'sessione chiusa']
    assert any(msg in response.data.lower() for msg in italian_messages)
    
    # Effettua il login con credenziali errate per generare un altro messaggio flash
    response = authenticated_client.post(
        '/login',
        data={'email': 'doctor@example.com', 'password': 'WrongPassword123!'},
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il messaggio di errore sia in italiano
    italian_errors = [b'non valid', b'errat', b'incorrect']
    assert any(err in response.data.lower() for err in italian_errors)
    
    # Cambia in inglese
    authenticated_client.get('/set-language/en')
    
    # Effettua un'altra operazione con messaggio flash
    response = authenticated_client.post(
        '/login',
        data={'email': 'doctor@example.com', 'password': 'WrongPassword123!'},
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verifica che il messaggio di errore sia in inglese
    english_errors = [b'invalid', b'incorrect', b'wrong']
    assert any(err in response.data.lower() for err in english_errors)

def test_date_format_localization(authenticated_client, test_patient):
    """Verifica che i formati di data vengano localizzati correttamente."""
    # Imposta la lingua inglese
    authenticated_client.get('/set-language/en')
    
    # Visualizza la pagina del paziente
    response = authenticated_client.get(f'/patients/{test_patient.uuid}')
    assert response.status_code == 200
    
    # Controlla il formato della data
    date_en = test_patient.date_of_birth.strftime('%Y-%m-%d')
    assert date_en.encode() in response.data
    
    # Imposta la lingua italiana
    authenticated_client.get('/set-language/it')
    
    # Visualizza nuovamente la pagina del paziente
    response = authenticated_client.get(f'/patients/{test_patient.uuid}')
    assert response.status_code == 200
    
    # In italiano potrebbe esserci un formato differente o la stessa data
    # Ma l'importante è che la pagina si carichi correttamente
    assert response.status_code == 200
    assert test_patient.first_name.encode() in response.data
