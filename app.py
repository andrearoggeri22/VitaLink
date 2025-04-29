import os
import logging
from datetime import datetime, timedelta, timezone

from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_babel import Babel
from flask_migrate import Migrate

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///healthcare.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", app.secret_key)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 86400  # 24 hours

# Configure Babel
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
app.config['LANGUAGES'] = {
    'en': 'English',
    'it': 'Italiano'
}

# Function to determine which language to use
def get_locale():
    # First, check if user has explicitly set language in session
    logger.debug(f"get_locale called, session: {session}")
    if 'language' in session:
        logger.debug(f"Language from session: {session['language']}")
        return session['language']
    # Otherwise, try to detect from browser settings
    best_match = request.accept_languages.best_match(app.config['LANGUAGES'].keys())
    logger.debug(f"Best match from accept_languages: {best_match}")
    return best_match

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
babel = Babel(app, locale_selector=get_locale)

# Custom template filters
@app.template_filter('format_datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """Format a datetime to a readable string in UTC+2."""
    if value is None:
        return ""

    # Define the UTC+2 timezone
    utc_plus_2 = timezone(timedelta(hours=2))

    # If the value has no timezone, assume it's UTC
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    # Convert to UTC+2
    value = value.astimezone(utc_plus_2)

    return value.strftime(format)

# Inject common variables into templates
@app.context_processor
def inject_globals():
    """Inject global variables into templates."""
    return {
        'now': datetime.now()
    }

with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import Doctor, Patient, DoctorPatient, Note, AuditLog, HealthPlatformLink, VitalObservation
    
    # Import and register blueprints
    from auth import auth_bp
    from views import views_bp
    from api import api_bp
    from audit import audit_bp
    from language import language_bp
    from health_platforms import health_bp
    from observations import observations_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(language_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(observations_bp)
    
    # Create database tables
    db.create_all()
    
    logger.info("Application initialized successfully")

# Initialize login manager
from models import Doctor

@login_manager.user_loader
def load_user(user_id):
    return Doctor.query.get(int(user_id))
