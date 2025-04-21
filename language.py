from flask import Blueprint, session, redirect, url_for, request, render_template, current_app
from flask_babel import _

language_bp = Blueprint('language', __name__, url_prefix='/language')

@language_bp.route('/change/<string:lang_code>', methods=['GET'])
def change_language(lang_code):
    """
    Change the language for the application
    
    Args:
        lang_code: The language code (e.g., 'en', 'it')
    """
    # Validate language code
    if lang_code in current_app.config['LANGUAGES']:
        session['language'] = lang_code
    
    # Get the URL to return to, or default to home
    next_url = request.args.get('next') or url_for('views.index')
    
    return redirect(next_url)