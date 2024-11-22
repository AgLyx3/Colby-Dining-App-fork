from flask import Blueprint, redirect, url_for, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import LoginManager, login_user, logout_user, current_user
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.session import SessionStorage
from models import db, Administrator, Student
import os
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


login_manager = LoginManager()
login_manager.login_view = 'auth.google_login'
login_manager.login_message = 'Please log in with your Colby email to access this page.'

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize Google OAuth blueprint
google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    storage=SessionStorage()
    
)

@login_manager.user_loader
def load_user(user_email):
    # Try loading as admin first
    admin = Administrator.query.get(user_email)
    if admin:
        return admin
    # If not admin, try loading as student
    return Student.query.get(user_email)

def init_admin_model():
    """Make Administrator model compatible with Flask-Login"""
    Administrator.get_id = lambda self: self.admin_email
    Administrator.is_authenticated = lambda self: True
    Administrator.is_active = lambda self: True
    Administrator.is_anonymous = lambda self: False

@auth_bp.route('/login')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    return redirect(url_for('main.admin_dashboard'))

@auth_bp.route('/logout')
def logout():
    if google.authorized:
        token = google_bp.token
        if token:
            # Revoke Google OAuth token
            google.post(
                'https://accounts.google.com/o/oauth2/revoke',
                params={'token': token['access_token']},
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash('Failed to log in with Google.', 'error')
        return False

    resp = blueprint.session.get('/oauth2/v2/userinfo')
    if not resp.ok:
        flash('Failed to fetch user info from Google.', 'error')
        return False

    user_info = resp.json()
    email = user_info.get('email', '')

    # Check if email is from Colby
    if not email.endswith('@colby.edu'):
        flash('Please use your Colby email address to log in.', 'error')
        session.clear()
        return False

    # Check if user is an admin
    admin = Administrator.query.get(email)
    if admin:
        login_user(admin)
        session['admin_email'] = admin.admin_email
        session['is_admin'] = True
    else:
        # Handle regular student login
        student = Student.query.get(email)
        if not student:
            # Create new student record if first time login
            student = Student(
                student_email=email,
                student_access_token=token['access_token']
            )
            db.session.add(student)
            db.session.commit()
        
        login_user(student)
        session['student_email'] = student.student_email
        session['is_admin'] = False

    session['google_name'] = user_info.get('name')
    session['google_picture'] = user_info.get('picture')
    
    flash(f'Welcome, {user_info.get("given_name")}!', 'success')
    return False

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You must be logged in to access this page.', 'error')
            return redirect(url_for('auth.google_login'))
        if not isinstance(current_user, Administrator):
            flash('You must be an administrator to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.context_processor
def utility_processor():
    """Make auth checking available in templates"""
    return dict(is_admin=lambda user: isinstance(user, Administrator))