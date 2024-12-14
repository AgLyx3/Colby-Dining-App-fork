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
    assert response.status_code == 200
    assert b'Thank you for your feedback' in response.data


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


def test_get_trending_favorites(client):
    """Test get_trending_favorites"""
    response = client.get('/api/trending-favorites')
    assert response.status_code == 200
