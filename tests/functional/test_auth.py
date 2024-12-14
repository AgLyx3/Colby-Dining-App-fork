"""
Filename:
    test_auth.py

Note:
    Testing auth blueprint
"""
import pytest
from flask import url_for, session
from flask_dance.consumer.storage import MemoryStorage
from website.models import Student

class TestGoogleAuthentication:
    def test_login_redirect_to_google(self, client):
        """Test that /login/google redirects to Google OAuth."""
        response = client.get('/login/google')
        assert response.status_code in (302, 303)
        assert 'oauth' in response.location.lower()
    
    def test_non_colby_email_rejected(self, client):
        """Test that non-Colby emails are rejected."""
        # First simulate a failed login attempt with non-Colby email
        with client.session_transaction() as session:
            # Clear any existing session data
            session.clear()
            # Set up session as if Google OAuth returned a non-Colby email
            session['google_oauth_token'] = {'access_token': 'fake-token'}
            session['user_info'] = {
                'email': 'test@example.com',
                'name': 'Test User'
            }
        # Try to access a protected route
        response = client.get('/userdashboard')
        # Should be redirected to login or unauthorized
        assert response.status_code in (302, 401, 403)
        # If it's a redirect, make sure it goes to login
        if response.status_code == 302:
            assert '/login' in response.location.lower()
        # Check that we're not authenticated
        assert session.get('is_authenticated') is not True
    
    def test_logout(self, auth_client):
        """Test logout functionality."""
        with auth_client.session_transaction() as session2:
            session2['user_info'] = {'email': 'test@colby.edu'}
        
        response = auth_client.get('/logout')
        assert response.status_code in (302, 303)
        assert 'user_info' not in session2
    
    def test_admin_required_decorator(self, client):
        """Test admin-only routes are protected."""
        response = client.get('/admin/dashboard')
        assert response.status_code in (302, 303)
        assert 'login' in response.location.lower()
    
    def test_successful_admin_login(self, admin_client):
        """Test successful admin login."""
        with admin_client.session_transaction() as session:
            session['google_oauth_token'] = {'access_token': 'fake-token'}
            session['user_info'] = {
                'email': 'admin@colby.edu',
                'name': 'Admin User'
            }
            session['is_admin'] = True
            
        response = admin_client.get('/admin/dashboard')
        assert response.status_code in (200, 302)
    
    def test_first_time_student_registration(self, client):
        """Test first-time student registration flow."""
        with client.session_transaction() as session:
            session['google_oauth_token'] = {'access_token': 'fake-token'}
            session['user_info'] = {
                'email': 'student@colby.edu',
                'name': 'New Student'
            }
        
        response = client.get('/')
        assert response.status_code in (200, 302)