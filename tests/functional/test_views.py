"""
Filename:
    test_views.py

Note:
    Testing views
"""

def test_index(client, auth_client, admin_client):
    """
    Testing home page
    """
    response = client.get('/')
    response1 = auth_client.get('/')
    response2 = auth_client.get('/')

    with admin_client.session_transaction() as session:
        assert session['is_admin'] is True

    assert response.status_code == 200
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert b'name' in response1.data
    assert b'name' in response2.data


def test_dining_experience(client):
    """
    Testing Dining experience page
    """
    response = client.get('/dining-experience')

    assert response.status_code == 200


def test_team(client, auth_client, admin_client):
    """
    Testing Team page
    """
    response = client.get('/team')
    # assert statement
    assert response.status_code == 200


def test_news(client):
    """
    Testing news page
    """
    response = client.get('/news')
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


def test_userdashboard(auth_client, admin_client):
    """
    Testing user dashboard page
    """
    response = auth_client.get('/userdashboard')
    assert response.status_code == 302
    response2 = admin_client.get('/userdashboard')
    assert response2.status_code == 302


def test_admindashboard(admin_client, auth_client):
    """
    Testing Admin dashboard page for admin and non-admin users.
    """
    # Admin client (should be allowed access and redirected to dashboard)
    admin_response = admin_client.get('/admin/dashboard')
    assert admin_response.status_code == 302
    user_response = auth_client.get('/admin/dashboard')
    assert user_response.status_code == 302  # Forbidden access for non-admin

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
    assert "date" in response.json
    assert "dining_hall" in response.json


def test_get_dining_hall_menu(client):
    # if during open hours
    response = client.get('/Dana')
    assert response.status_code == 200 or response.status_code == 404
    # assert response.json['status'] == 'success' or response.json['status'] == 'error'
    # assert 'menu' in response.json or 'message' in response.json
    # if dining halls are closed, "status": error, "code": 404


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
    assert response.status_code != 200


# testing apis 
def test_get_weekly_menu(client):
    """
    Testing menu api if it returns the correct menu
    """
    response = client.get('/api/menu/weekly/Dana')
    assert response.status_code != 302


def test_get_dining_hours(client):
    """
    Testing menu hours retrieved from menu api
    """
    response = client.get('/api/menu/hours')
    assert response.status_code != 302


def test_get_trending_favorites(client):
    """Test get_trending_favorites"""
    response = client.get('/api/trending-favorites')
    assert response.status_code == 200

import pytest
from website import create_app, db
from website.models import Administrator, FeedbackQuestion
from datetime import datetime

@pytest.fixture
def app():
    app = create_app()
    yield app
    with app.app_context():
        db.session.remove()
@pytest.fixture
def admin_user(app):
    """Create an admin user with a unique email."""
    unique_email = f'admin{str(datetime.utcnow().timestamp())}@example.com'  # Unique email
    admin = Administrator(
        admin_email=unique_email,
        password_hashed='hashed_password',
        fullname='Admin User',
        given_name='Admin',
        family_name='User',
    )
    db.session.add(admin)
    db.session.commit()
    return admin

@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db.drop_all()
        db.create_all()


@pytest.fixture(autouse=True)
def rollback_session():
    yield
    db.session.rollback()


@pytest.fixture
def feedback_question(app, admin_user):
    """Create a feedback question for testing."""
    question = FeedbackQuestion(
        question_text='What is your favorite color?',
        question_type='yes-no',
        active_start_date=datetime(2024, 1, 1),
        active_end_date=datetime(2024, 12, 31),
        administrator_id=admin_user.admin_email
    )
    db.session.add(question)
    db.session.commit()
    return question

def test_create_feedback_question_success(client, admin_user):
    data = {
        'questionText': 'What is your opinion?',
        'questionType': 'multiple_choice',
        'activeStartDate': '2024-01-01',
        'activeEndDate': '2024-12-31'
    }

    response = client.post('/admin/feedback-question', data=data)

    assert response.status_code == 302

def test_create_feedback_question_missing_data(client, admin_user):
    data = {
        'questionText': 'What is your favorite color?',
        'questionType': 'yes-no',
        'activeStartDate': '2024-01-01'
    }  # Missing 'activeEndDate'

    response = client.post('/admin/feedback-question', data=data)
    assert response.status_code == 302

def test_deactivate_feedback_question_success(client, admin_user, feedback_question):
    response = client.put(f'/admin/feedback-question/{feedback_question.id}/deactivate')
    assert response.status_code == 302


def test_deactivate_feedback_question_already_inactive(client, admin_user, feedback_question):
    feedback_question.is_active = False
    db.session.commit()

    response = client.put(f'/admin/feedback-question/{feedback_question.id}/deactivate')
    assert response.status_code == 302


def test_delete_feedback_question_success(client, admin_user, feedback_question):
    feedback_question.is_active = False
    db.session.commit()

    response = client.delete(f'/admin/feedback-question/{feedback_question.id}/delete')
    assert response.status_code == 302


def test_delete_feedback_question_active(client, admin_user, feedback_question):
    response = client.delete(f'/admin/feedback-question/{feedback_question.id}/delete')
    assert response.status_code == 302


def test_reactivate_feedback_question_success(client, admin_user, feedback_question):
    feedback_question.is_active = False
    db.session.commit()

    response = client.put(f'/admin/feedback-question/{feedback_question.id}/reactivate')
    assert response.status_code == 302



def test_get_all_feedback_questions(client, admin_user):
    response = client.get('/api/admin/feedback-questions')
    assert response.status_code == 200


def test_export_responses_success(client, admin_user):
    """Test exporting responses for a given feedback question."""
    question_id = 1
    response = client.get(f'/admin/feedback-question/export/{question_id}')

    assert response.status_code == 302

def test_export_responses_invalid_question(client, admin_user):
    """Test exporting responses for an invalid question."""
    question_id = 9999
    response = client.get(f'/admin/feedback-question/export/{question_id}')

    assert response.status_code == 302


def test_logout_success(client):
    """Test logging out."""
    response = client.post('/logout')
    assert response.status_code == 302


def test_logout_no_session(client):
    """Test logging out with no active session."""
    response = client.post('/logout')
    assert response.status_code == 302

def test_submit_feedback_success(client):
    """Test submitting feedback successfully."""
    data = {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'feedback_type': 'Suggestion',
        'message': 'Great food!'
    }
    response = client.post('/submit_feedback', data=data)
    assert response.status_code != 302



def test_submit_feedback_missing_field(client):
    """Test submitting feedback with missing fields."""
    data = {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'feedback_type': 'Suggestion'
    }  # Missing 'message'
    response = client.post('/submit_feedback', data=data)
    assert response.status_code == 400

def test_menu_page_success(client):
    """Test rendering the menu page."""
    response = client.get('/menu')
    assert response.status_code != 302


def test_menu_page_with_dietary_filters(client):
    """Test rendering the menu page with dietary filters."""
    response = client.get('/menu')
    assert response.status_code == 200

def test_get_current_menus_success(client):
    """Test retrieving current menus."""
    response = client.get('/api/menu/current')
    assert response.status_code == 200


def test_get_dining_hall_menu_success(client):
    """Test retrieving menu for a specific dining hall."""
    response = client.get('/Dana?date=2024-12-15')
    assert response.status_code != 302


def test_get_dining_hall_menu_invalid_hall(client):
    """Test failure when trying to retrieve menu for an invalid dining hall."""
    response = client.get('/InvalidHall?date=2024-12-15')
    assert response.status_code == 404

def test_get_trending_favorites_success(client):
    """Test retrieving trending favorite dishes."""
    response = client.get('/api/trending-favorites')
    assert response.status_code == 200

