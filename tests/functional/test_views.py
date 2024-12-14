"""
Filename:
    test_views.py

Note:
    Testing views
"""
import pytest
from website import create_app
from flask_login import current_user
from website.models import Student, Food, Tag, Favorites, FeedbackQuestion, Administrator
from website.views import menu_bp

def test_index(client):
    """
    Testing home page
    """
    response = client.get('/')
    assert response.status_code == 200


def test_dining_experience(client):
    """
    Testing Dining experience page
    """
    response = client.get('/dining-experience')

    assert response.status_code == 200


def test_team(client):
    """
    Testing Team page
    """
    response = client.get('/team')

    assert response.status_code == 200


def test_menu(client):
    """
    Testing menu page
    """
    response = client.get('/menu')

    assert response.status_code == 200


def test_contact(client):
    """
    Testing contact page
    """
    response = client.get('/contact')

    assert response.status_code == 200


def test_userdashboard(client):
    """
    Testing user dashboard page
    """
    response = client.get('/userdashboard')

    assert response.status_code == 302


def test_admindashboard(client):
    """
    Testing Admin dashboard page
    """
    response = client.get('/admin/dashboard')
    # Being forwarded to dashboard page
    assert response.status_code == 302


def test_logout(client):
    """
    Testing Logout page
    """
    response = client.get('/logout')

    assert response.status_code == 302


def test_menu_page(client):
    """
    Testing menu page
    """
    response = client.get('/menu')
    assert response.status_code == 200
    assert b"Dana" in response.data
    assert b"Vegetarian" in response.data


def test_get_current_menu(client):
    """
    Testing menu api if it returns the food
    """
    response = client.get('/api/menu/current')
    assert response.status_code == 200
    assert b"status" in response.json
    assert b"menus" in response.json


def test_submit_feedback(client):
    """
    Testing feedback plugin
    """
    feedback_data = {
        'name': 'Test User',
        'email': 'testuser@colby.edu',
        'feedback_type': 'Positive',
        'message': 'Great experience!'
    }

    response = client.post('/submit_feedback', data=feedback_data)
    assert response.status_code == 200
    assert b'Thank you for your feedback' in response.data


def test_get_dining_hall_menu(client):
    """
    Testing menu filter if it returns the menu of the selected dining hall
    """
    response = client.get('/menu/Roberts')
    assert response.status_code == 200
    assert b"Roberts" in response.data


# testing apis 
def test_get_weekly_menu(client):
    """
    Testing menu api if it returns the correct menu
    """
    response = client.get('/api/menu/weekly/Dana')
    assert response.status_code == 200
    assert 'weekly_menu' in response.json


def test_get_dining_hours(client):
    """
    Testing menu hours retrieved from menu api
    """
    response = client.get('/api/menu/hours')
    assert response.status_code == 200
    assert 'hours' in response.json
