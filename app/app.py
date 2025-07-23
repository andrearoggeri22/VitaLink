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
from flask import Flask, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user
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
    Priority order:
    1. DATABASE_URL environment variable (AWS RDS, PostgreSQL, etc.)
    2. Cloud environment configuration (AWS Fargate, Google Cloud Run, etc.)
    3. SQLite fallback for local development
    """
    # Check for direct DATABASE_URL first (AWS RDS, etc.)
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        logger.info(f"Using DATABASE_URL: {database_url[:50]}...")
        return database_url
    
    # Check if running in any cloud environment (AWS Fargate, Google Cloud Run, etc.)
    is_cloud_environment = os.environ.get("CLOUD_RUN_ENVIRONMENT", "false").lower() == "true"
    if is_cloud_environment:
        logger.info("Running in cloud environment (AWS Fargate or Google Cloud Run)")
        try:
            # Try AWS/standard format first
            db_user = os.environ.get("DB_USER")
            db_pass = os.environ.get("DB_PASS") 
            db_name = os.environ.get("DB_NAME")
            db_host = os.environ.get("DB_HOST", os.environ.get("PGHOST", "localhost"))
            db_port = os.environ.get("DB_PORT", os.environ.get("PGPORT", "5432"))
            
            # Check if we have Unix socket (Google Cloud Run)
            unix_socket_path = os.environ.get("INSTANCE_UNIX_SOCKET")
            
            if unix_socket_path:
                # Google Cloud Run with Unix socket
                db_uri = f"postgresql://{db_user}:{db_pass}@{unix_socket_path}/{db_name}"
                logger.info(f"Configured Google Cloud SQL connection via Unix socket")
            else:
                # Standard TCP connection (AWS RDS, etc.)
                db_uri = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
                logger.info(f"Configured cloud PostgreSQL connection to {db_host}:{db_port}")
            
            return db_uri
        except KeyError as e:
            logger.error(f"Missing required environment variable for cloud environment: {e}")
            logger.error("Falling back to SQLite")
    
    # Fallback to SQLite for local development
    db_uri = "sqlite:///healthcare.db"
    logger.info(f"Using SQLite fallback: {db_uri}")
    return db_uri
# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ["SESSION_SECRET"]
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure WTF-CSRF protection
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", os.environ["SESSION_SECRET"])
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
# Root endpoint redirect
@app.route('/')
def index():
    """Root endpoint that redirects to appropriate page."""
    if current_user and current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    return redirect(url_for('auth.login'))

# Health check endpoint for Cloud Run
@app.route('/healthz', methods=['GET'])
@app.route('/health', methods=['GET'])  # Add alternative health endpoint
def health_check():
    """
    Health check endpoint for monitoring system health.
    This endpoint is used by Cloud Run, Kubernetes, or other orchestration systems
    to determine if the application is healthy and ready to receive traffic.
    It performs a basic check without testing database connectivity to avoid issues.
    
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
        # Basic system info without database test
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

# ALB Health check endpoint 
@app.route('/health', methods=['GET'])
def alb_health_check():
    """
    Simple health check endpoint for AWS Application Load Balancer.
    Returns a simple OK response without any complex checks.
    """
    return {"status": "healthy", "service": "vitalink"}, 200
