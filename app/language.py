"""
Language Management Module.
This module provides functionality for managing the application's internationalization (i18n)
and localization (l10n) settings. It includes:
1. Routes for changing the application language
2. Session-based language persistence
3. Utilities for language detection and handling
The module works with Flask-Babel to provide a seamless multilingual experience,
allowing users to switch between available languages (English, Italian, etc.).
"""
from flask import Blueprint, session, redirect, url_for, request, current_app
import logging
logger = logging.getLogger(__name__)
language_bp = Blueprint('language', __name__, url_prefix='/language')
@language_bp.route('/change/<string:lang_code>', methods=['GET'])
def change_language(lang_code):
    """
    Change the language for the application
    Args:
        lang_code: The language code (e.g., 'en', 'it')
    """
    # Log the current state before changes
    logger.debug(f"Changing language to: {lang_code}")
    logger.debug(f"Current session: {session}")
    logger.debug(f"Request path: {request.path}")
    logger.debug(f"Next URL: {request.args.get('next')}")
    # Validate language code
    if lang_code in current_app.config['LANGUAGES']:
        session['language'] = lang_code
        logger.debug(f"Language set in session: {session['language']}")
    else:
        logger.warning(f"Invalid language code: {lang_code}")
    # Get the URL to return to, or default to home
    next_url = request.args.get('next') or url_for('views.index')
    logger.debug(f"Redirecting to: {next_url}")
    return redirect(next_url)