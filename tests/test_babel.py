import pytest
from flask import session
from app.app import app, babel, get_locale

def test_babel_init():
    """Verifica che Babel sia inizializzato correttamente."""
    assert babel is not None
    # Il locale selector dovrebbe essere la funzione get_locale
    assert babel.locale_selector_func == get_locale

def test_get_locale_function():
    """Verifica il funzionamento della funzione get_locale."""
    # Test all'interno del contesto dell'applicazione
    with app.test_request_context():
        # Senza lingua impostata nella sessione, dovrebbe usare l'Accept-Languages
        locale = get_locale()
        assert locale in app.config['LANGUAGES'].keys()
        
        # Con lingua impostata nella sessione, dovrebbe usare quella
        session['language'] = 'it'
        locale = get_locale()
        assert locale == 'it'
        
        # Con lingua non valida, dovrebbe usare l'Accept-Languages
        session['language'] = 'invalid'
        locale = get_locale()
        # Dovrebbe tornare una lingua valida o la default
        assert locale in app.config['LANGUAGES'].keys()

def test_babel_translation_directories():
    """Verifica che le directory delle traduzioni siano configurate correttamente."""
    assert 'BABEL_TRANSLATION_DIRECTORIES' in app.config
    assert app.config['BABEL_TRANSLATION_DIRECTORIES'] == 'translations'

def test_languages_config():
    """Verifica la configurazione delle lingue supportate."""
    assert 'LANGUAGES' in app.config
    assert 'en' in app.config['LANGUAGES']
    assert 'it' in app.config['LANGUAGES']
