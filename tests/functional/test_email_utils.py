"""
Filename:
    test_email_utils.py

Note:
    Testing email utils functionalities
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from website.email_utils import EmailSender

# Setup environment variables for testing
os.environ['EMAIL_USERNAME'] = 'test@example.com'
os.environ['EMAIL_PASSWORD'] = 'testpassword'

@pytest.fixture
def email_sender():
    """
    Fixture to create an EmailSender instance for testing
    """
    return EmailSender()


def test_email_sender_initialization(email_sender):
    """
    Test that EmailSender is initialized correctly
    """
    assert email_sender.smtp_server == "smtp.gmail.com"
    assert email_sender.smtp_port == 587
    assert email_sender.sender_email == 'test@example.com'
    assert email_sender.sender_password == 'testpassword'


@patch('smtplib.SMTP')
def test_send_feedback_email(mock_smtp, email_sender):
    """
    Test sending a feedback email
    """
    # Mock the SMTP connection
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    # Call the method
    result = email_sender.send_feedback_email(
        name='John Doe', 
        email='john@example.com', 
        feedback_type='General', 
        message='Test feedback message'
    )

    # Assert the email was sent successfully
    assert result is True
    
    # Verify SMTP methods were called
    mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with('test@example.com', 'testpassword')
    mock_server.send_message.assert_called_once()


@patch('smtplib.SMTP')
def test_send_favorite_dish_notification(mock_smtp, email_sender):
    """
    Test sending a favorite dish notification email
    """
    # Mock the SMTP connection
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    # Test dishes
    test_dishes = ['Pasta Carbonara', 'Chicken Parmesan']

    # Call the method
    result = email_sender.send_favorite_dish_notification(
        student_email='student@example.com', 
        dishes=test_dishes
    )

    # Assert the email was sent successfully
    assert result is True
    
    # Verify SMTP methods were called
    mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with('test@example.com', 'testpassword')
    mock_server.send_message.assert_called_once()

@patch('website.email_utils.EmailSender.send_async_notification')
@patch('website.email_utils.db.session')
@patch('website.email_utils.BonAppetitAPI')
def test_check_favorite_dishes(mock_bon_appetit_api, mock_db_session, mock_send_async, email_sender):
    """
    Test the check_favorite_dishes method with minimal mocking
    """
    # Create a mock app
    mock_app = MagicMock()
    mock_app.config = {
        'MENU_API_USERNAME': 'test_user',
        'MENU_API_PASSWORD': 'test_pass'
    }

    # Setup mock dining halls
    mock_bon_appetit_api.return_value.DINING_HALLS = {'Main Hall': 1}

    # Setup mock menu data
    mock_bon_appetit_api.return_value.get_menu.return_value = {
        'lunch': [
            {'name': 'Pizza'},
            {'name': 'Chicken Sandwich'}
        ]
    }
    mock_bon_appetit_api.return_value.process_menu_data.return_value = {
        'lunch': [
            {'name': 'Pizza'},
            {'name': 'Chicken Sandwich'}
        ]
    }

    # Setup mock favorite dishes
    mock_favorite_dish = MagicMock()
    mock_favorite_dish.dish_name = 'Pizza'
    mock_favorite_dish.student_email = 'student@example.com'
    
    # Mock the database query to return the favorite dish
    mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_favorite_dish]

    # Call the method
    EmailSender.check_favorite_dishes(mock_app)

    # Verify async notification was sent for the favorite dish
    mock_send_async.assert_called_once_with('student@example.com', ['Pizza'])