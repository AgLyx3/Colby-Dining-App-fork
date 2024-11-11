from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required
from models import db, Student
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import logout_user
auth_blueprint = Blueprint('auth', __name__)


login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Redirects to 'auth.login' if not logged in

@login_manager.user_loader
def load_user(user_email):
    """Given the email, return the corresponding user object."""
    return Student.query.get(user_email)


def create_initial_users():
    """Add initial users if they do not already exist in the database."""

    initial_users = [
        ("admin@example.com", "adminpass"),
        ("user1@example.com", "user1pass"),
        ("user2@example.com", "user2pass"),
    ]

    for email, access_token in initial_users:

        existing_user = Student.query.filter_by(student_email=email).first()
        if not existing_user:

            hashed_token = generate_password_hash(access_token)
            new_user = Student(student_email=email, student_access_token=hashed_token)
            db.session.add(new_user)
            print(f"Added initial user: {email}")

    # Commit all changes
    db.session.commit()


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        access_token = request.form.get('access_token')

        # Fetch the user from the database
        user = Student.query.filter_by(student_email=email).first()

        if user and check_password_hash(user.student_access_token, access_token):
            login_user(user)
            return redirect(url_for('main.userdashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')  # Flash error message

    return render_template('login.html')


@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))