import logging
from datetime import datetime
from functools import wraps

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email, Length
from flask_babel import lazy_gettext as _

from .app import db
from .models import Doctor
from .utils import (validate_email, is_valid_password)

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Registration form
class RegistrationForm(FlaskForm):
    email = EmailField(_('Email'), validators=[DataRequired(), Email()])
    first_name = StringField(_('First Name'), validators=[DataRequired(), Length(min=2, max=100)])
    last_name = StringField(_('Last Name'), validators=[DataRequired(), Length(min=2, max=100)])
    specialty = StringField(_('Specialty'))
    password = PasswordField(_('Password'), validators=[
        DataRequired(),
        Length(min=8, message=_("Password must be at least 8 characters long"))
    ])
    # We remove the EqualTo validator since we verify manually in the controller
    confirm_password = PasswordField(_('Confirm Password'), validators=[
        DataRequired()
    ])

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    
    form = RegistrationForm()
    
    if request.method == 'POST':
        # Verify password match manually before form validation
        if form.password.data != form.confirm_password.data:
            logger.info("Password mismatch during registration")
            flash(_('Passwords do not match'), 'danger')
            return render_template('register.html', form=form, now=datetime.now())
    
        if form.validate_on_submit():
            email = form.email.data
            
            # Check if email already exists
            existing_doctor = Doctor.query.filter_by(email=email).first()
            if existing_doctor:
                flash(_('An account with this Email already exists'), 'danger')
                return render_template('register.html', form=form, now=datetime.now())
            
            # Check password strength
            is_strong, message = is_valid_password(form.password.data)
            if not is_strong:
                flash(message, 'danger')
                return render_template('register.html', form=form, now=datetime.now())
          # Create new doctor account
        doctor = Doctor(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            specialty=form.specialty.data
        )
        doctor.set_password(form.password.data)
        
        try:
            db.session.add(doctor)
            db.session.commit()
            flash(_('Registration completed. Now you can access'), 'success')
            logger.info(f"New doctor registered: {email}")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {str(e)}")
            flash(_('An error occurred. Please try again'), 'danger')
    
    return render_template('register.html', form=form, now=datetime.now())
    
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash(_('Please provide both email and password'), 'danger')
            return render_template('login.html', now=datetime.now())
        
        if not validate_email(email):
            flash(_('Invalid email format'), 'danger')
            return render_template('login.html', now=datetime.now())
        
        doctor = Doctor.query.filter_by(email=email).first()
        
        if doctor and doctor.check_password(password):
            login_user(doctor)
            logger.info(f"Doctor {doctor.id} logged in successfully")
            return redirect(url_for('views.dashboard'))
        else:
            flash(_('Invalid email or password'), 'danger')
            
    return render_template('login.html', now=datetime.now())

@auth_bp.route('/logout')
@login_required
def logout():
    logger.info(f"Doctor {current_user.id} logged out")
    logout_user()
    flash(_('You have been disconnected'), 'success')
    return redirect(url_for('auth.login'))

# API endpoints for JWT authentication
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    if not request.is_json:
        return jsonify({"error": _("Missing JSON in request")}), 400
    
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    
    if not email or not password:
        return jsonify({"error": _("Missing email or password")}), 400
    
    doctor = Doctor.query.filter_by(email=email).first()
    
    if not doctor or not doctor.check_password(password):
        return jsonify({"error": _("Invalid email or password")}), 401
    
    # Create access token and refresh token
    access_token = create_access_token(identity=doctor.id)
    refresh_token = create_refresh_token(identity=doctor.id)
    
    logger.info(f"API login successful for doctor {doctor.id}")
    
    return jsonify({
        "message": _("Login successful"),
        "doctor": doctor.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200

@auth_bp.route('/api/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    
    logger.info(f"Token refreshed for doctor {identity}")
    
    return jsonify({
        "access_token": access_token
    }), 200

# Decorator for API authentication
def api_doctor_required(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        doctor_id = get_jwt_identity()
        doctor = Doctor.query.get(doctor_id)
        
        if not doctor:
            return jsonify({"error": _("Doctor not found")}), 404
            
        return f(doctor, *args, **kwargs)
    
    return decorated

# Decorator for web routes that require doctor authentication
def doctor_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        # Flask-Login already ensures the user is authenticated
        # We just need to check if the user is a doctor
        if not hasattr(current_user, 'id'):
            flash(_('Authentication required'), 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated
