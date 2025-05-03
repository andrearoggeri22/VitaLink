"""
Flask Application Module.

This module initializes and configures the Flask application and its extensions:
- SQLAlchemy for database ORM
- Flask-Migrate for database migrations
- Flask-JWT-Extended for JSON web token authentication
- Flask-Login for session-based authentication
- Flask-Babel for internationalization

It sets up logging, database connections, JWT authentication, user session management,
localization, and registers all blueprints with the application.
"""

import os
import logging
import sys
from datetime import datetime, timedelta, timezone

from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_babel import Babel
from flask_migrate import Migrate

# Configure logging
logging_level = os.environ.get("LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(
    level=getattr(logging, logging_level),
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Define base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)

# Function to configure database URI based on environment
def get_database_uri():
    """
    Configure the database connection URI based on the runtime environment.
    
    This function determines whether the application is running in a cloud environment
    or locally, and returns the appropriate database connection URI. 
    
    In cloud environments, it uses PostgreSQL with Unix socket connections.
    In local environments, it defaults to SQLite or uses the DATABASE_URL environment variable.
    
    Returns:
        str: Database connection URI for SQLAlchemy
    
    Environment variables used:
        CLOUD_RUN_ENVIRONMENT: "true" if running in cloud environment
        DB_USER: Database username (cloud environment only)
        DB_PASS: Database password (cloud environment only)
        DB_NAME: Database name (cloud environment only)
        INSTANCE_UNIX_SOCKET: Unix socket path (cloud environment only)
        DATABASE_URL: Database connection string (local environment only)
    """
    is_cloud_environment = os.environ.get("CLOUD_RUN_ENVIRONMENT", "false").lower() == "true"
    logger.info(f"Running in cloud environment: {is_cloud_environment}")
    
    if is_cloud_environment:
        # Cloud SQL with Unix socket connection
        try:
            db_user = os.environ["DB_USER"]
            db_pass = os.environ["DB_PASS"]
            db_name = os.environ["DB_NAME"]
            unix_socket_path = os.environ["INSTANCE_UNIX_SOCKET"]
            
            # PostgreSQL connection via Unix socket
            db_uri = f"postgresql://{db_user}:{db_pass}@/{db_name}?host={unix_socket_path}"
            logger.info(f"Configured Cloud SQL connection via Unix socket at {unix_socket_path}")
            return db_uri
        except KeyError as e:
            logger.error(f"Missing required environment variable for Cloud SQL: {e}")
            logger.error("Falling back to default connection string")
    
    # Default database connection (local environment)
    db_uri = os.environ.get("DATABASE_URL", "sqlite:///healthcare.db")
    logger.info(f"Using database connection: {db_uri}")
    return db_uri

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ["SESSION_SECRET"]
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 30,
    "pool_size": 5,
    "max_overflow": 10,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure JWT
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
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
    """
    Determine which language to use for the current request.
    
    This function implements a language selection strategy for Flask-Babel:
    1. First checks if user has explicitly set a language preference in their session
    2. If no session preference exists, detects language from browser's Accept-Language header
    
    The function is used as the locale_selector for Flask-Babel to dynamically
    determine the appropriate language for each request.
    
    Returns:
        str: Language code ('en', 'it', etc.) to use for the current request
    """
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
login_manager.login_message = ''
babel = Babel(app, locale_selector=get_locale)

# Custom template filters
@app.template_filter('format_datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """
    Format a datetime object to a readable string in UTC+2 timezone.
    
    This template filter is used in Jinja templates to format datetime objects
    consistently throughout the application. It handles timezone conversion
    from UTC to UTC+2 (Central European Time) and applies the specified format.
    
    Args:
        value (datetime): The datetime object to format
        format (str, optional): Format string using Python's strftime format codes.
                                Defaults to '%Y-%m-%d %H:%M:%S'.
    
    Returns:
        str: Formatted datetime string in UTC+2 timezone, or empty string if value is None
        
    Example usage in template:
        {{ patient.created_at|format_datetime('%d %b %Y') }}
    """
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
    """
    Inject global variables into all templates.
    
    This context processor makes certain variables available to all templates
    without having to explicitly pass them in each render_template call.
    This ensures consistency and reduces repetitive code in route handlers.
    
    Variables injected:
        now (datetime): Current datetime, useful for displaying current time
                       or calculating relative time differences in templates
    
    Returns:
        dict: Dictionary of variables to inject into template context
    """
    return {
        'now': datetime.now()
    }

with app.app_context():
    # Compile translation files (.po to .mo)
    try:
        from .compile_translations import main as compile_translations
        logger.info("Compiling translation files (.po to .mo)...")
        compile_translations()
        logger.info("Translation compilation completed")
    except Exception as e:
        logger.error(f"Error during translation compilation: {e}")
    
    # Import models to ensure they're registered with SQLAlchemy
    from .models import Doctor
    
    # Import and register blueprints
    from .auth import auth_bp
    from .views import views_bp
    from .api import api_bp
    from .audit import audit_bp
    from .language import language_bp
    from .health_platforms import health_bp
    from .observations import observations_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(language_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(observations_bp)
    
    # Test database connection
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to the database")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
    
    # Create database tables
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    
    # Log application startup information
    cloud_env = os.environ.get("CLOUD_RUN_ENVIRONMENT", "false").lower() == "true"
    env_type = "Cloud Run" if cloud_env else "Local"
    logger.info(f"Application initialized successfully in {env_type} environment")
    logger.info(f"Host: {os.environ.get('HOST', '0.0.0.0')}, Port: {os.environ.get('PORT', '5000')}")

# Initialize login manager
from .models import Doctor

@login_manager.user_loader
def load_user(user_id):
    """
    Load a user from the database for Flask-Login.
    
    This function is required by Flask-Login to load a user object from the database
    based on the user ID stored in the session. It's called automatically by
    Flask-Login when a page requires authentication.
    
    Args:
        user_id (str): The ID of the user to load, as a string
        
    Returns:
        Doctor: The Doctor object if found, or None if not found
    """
    return Doctor.query.get(int(user_id))

# Health check endpoint for Cloud Run
@app.route('/healthz', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring system health.
    
    This endpoint is used by Cloud Run, Kubernetes, or other orchestration systems
    to determine if the application is healthy and ready to receive traffic.
    It performs a basic check by testing database connectivity.
    
    Returns:
        tuple: JSON response with health status and HTTP status code
            - 200 OK with system information if healthy
            - 500 Internal Server Error with error details if unhealthy
            
    Response format (healthy):
        {
            "status": "healthy",
            "environment": "Cloud Run" or "Local",
            "timestamp": "2023-05-01T12:34:56.789Z",
            "version": "0.1.0"
        }
        
    Response format (unhealthy):
        {
            "status": "unhealthy",
            "error": "Error message",
            "timestamp": "2023-05-01T12:34:56.789Z"
        }
    """
    try:
        # Check database connection
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Basic system info
        cloud_env = os.environ.get("CLOUD_RUN_ENVIRONMENT", "false").lower() == "true"
        env_type = "Cloud Run" if cloud_env else "Local"
        
        return {
            "status": "healthy",
            "environment": env_type,
            "timestamp": datetime.now().isoformat(),
            "version": "0.1.0"
        }, 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, 500
