"""
Filename: test_views.py
"""
import pytest
from datetime import datetime
from website import create_app
from flask_login import current_user
from website.models import Student, Food, Tag, Favorites, FeedbackQuestion, Response, Administrator, SurveyLink
from website.views import menu_bp
from website.menu_api import BonAppetitAPI
import json
from unittest import mock


def test_index(client):
    response = client.get('/')
    assert response.status_code == 200


def test_dining_experience(client):
    response = client.get('/dining-experience')

    assert response.status_code == 200

def test_team(client):
    response = client.get('/team')
    
    assert response.status_code == 200

def test_news(client):
    """
    Testing news page
    """
    response = client.get('/news')

    assert response.status_code == 200

def test_menu(client):
    response = client.get('/menu')

    assert response.status_code == 200


def test_contact(client):
    response = client.get('/contact')

    assert response.status_code == 200


def test_userdashboard(client):
    response = client.get('/userdashboard')

    assert response.status_code == 302

def test_admindashboard(client):

    response = client.get('/admin/dashboard')

    assert response.status_code == 302

def test_get_wait_times(client):
    """Test the /api/wait-times endpoint."""

    response = client.get('/api/wait-times')
    
    assert response.status_code == 200
    
    response_json = response.get_json()
    assert 'status' in response_json
    assert response_json['status'] == 'success'
    assert 'timestamp' in response_json
    assert 'predictions' in response_json
    
def test_logout(client):
    response = client.get('/logout')

    assert response.status_code == 302



def test_menu_page(client):

    response = client.get('/menu')
    assert response.status_code == 200
    assert b"Dana" in response.data
    assert b"Vegetarian" in response.data



def test_get_current_menu(client):

    response = client.get('/api/menu/current')
    assert response.status_code == 200
    assert "date" in response.json
    assert "dining_hall" in response.json

def test_get_dining_hall_menu(client):
    response = client.get('/Dana')  
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert 'menu' in response.json 


def test_submit_feedback(client):

    feedback_data = {
        'name': 'Test User',
        'email': 'testuser@colby.edu',
        'feedback_type': 'Positive',
        'message': 'Great experience!'
    }

    response = client.post('/submit_feedback', data=feedback_data)
    assert response.status_code == 200
    assert b'Thank you for your feedback' in response.data


# testing apis 
def test_get_weekly_menu(client):
    response = client.get('/api/menu/weekly/Dana')
    assert response.status_code == 200
    assert 'weekly_menu' in response.json

def test_get_dining_hours(client):
    response = client.get('/api/menu/hours')
    assert response.status_code == 200
    assert 'hours' in response.json

def test_get_trending_favorites(client):
    """Test get_trending_favorites"""
    response = client.get('/api/trending-favorites')
    assert response.status_code == 200