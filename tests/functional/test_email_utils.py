import pytest
from website.email_utils import EmailUtils
from datetime import datetime


def test_create_html_email_body():
    """Test the creation of an HTML email body."""
    content = "Hello, this is a test email."
    expected_html = """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <p>Hello, this is a test email.</p>
            </body>
        </html>
    """
    assert EmailUtils.create_html_email_body(content).strip() == expected_html.strip()


def test_create_plain_text_email_body():
    """Test the creation of a plain text email body."""
    content = "Hello, this is a test email."
    expected_text = "Hello, this is a test email."
    assert EmailUtils.create_plain_text_email_body(content) == expected_text


def test_validate_email_address():
    """Test the validation of an email address."""
    valid_email = "testuser@example.com"
    invalid_email = "testuserexample.com"

    assert EmailUtils.validate_email_address(valid_email) is True
    assert EmailUtils.validate_email_address(invalid_email) is False


def test_format_email_subject():
    """Test the formatting of email subject."""
    long_subject = "This is a very long subject line that will exceed the maximum length of 100 characters in an email subject line, so it needs to be truncated."
    short_subject = "Short Subject"

    assert EmailUtils.format_email_subject(
        long_subject) == "[Colby Dining] This is a very long subject line that will exceed the maximum length of 100 char..."
    assert EmailUtils.format_email_subject(short_subject) == "[Colby Dining] Short Subject"


def test_create_multipart_email():
    """Test the creation of a multipart email with attachments."""
    sender = "sender@example.com"
    recipient = "recipient@example.com"
    subject = "Test Email"
    body = "This is a test email body."
    attachments = ["testfile1.txt", "testfile2.png"]

    msg = EmailUtils.create_multipart_email(sender, recipient, subject, body, attachments)

    assert msg['From'] == sender
    assert msg['To'] == recipient
    assert msg['Subject'] == "[Colby Dining] Test Email"
    assert len(msg.get_payload()) == 3  # Body + 2 attachments


def test_get_student_emails():
    """Test the extraction and validation of student email addresses."""
    students = ["valid@example.com", "invalidemail.com", "test@example.org"]
    valid_emails = EmailUtils.get_student_emails(students)

    assert valid_emails == ["valid@example.com", "test@example.org"]


def test_format_datetime_for_email():
    """Test the formatting of a datetime object for email purposes."""
    dt = datetime(2024, 12, 15, 14, 30)
    formatted_dt = EmailUtils.format_datetime_for_email(dt)

    assert formatted_dt == "Sunday, December 15, 2024 at 02:30 PM"


def test_extract_email_from_text():
    """Test the extraction of an email address from text."""
    text = "Please contact us at support@example.com for more information."
    extracted_email = EmailUtils.extract_email_from_text(text)

    assert extracted_email == "support@example.com"


def test_create_welcome_email():
    """Test the creation of a welcome email."""
    student_name = "John Doe"
    email_body = EmailUtils.create_welcome_email(student_name)

    assert "<h2>Welcome to Colby Dining, John Doe!</h2>" in email_body
    assert "We're thrilled to have you as part of our community." in email_body


def test_send_notification_with_unsubscribe_link():
    """Test the creation of an email with an unsubscribe link."""
    student_email = "student@example.com"
    unsubscribe_link = "https://example.com/unsubscribe"
    email_body = EmailUtils.send_notification_with_unsubscribe_link(student_email, unsubscribe_link)

    assert "You are receiving notifications about your favorite dishes." in email_body
    assert f'<a href="{unsubscribe_link}">Unsubscribe</a>' in email_body


def test_create_feedback_email_body():
    """Test the creation of a feedback email body."""
    name = "Jane Doe"
    email = "janedoe@example.com"
    feedback_type = "Suggestion"
    message = "The food options are great, but could you add more vegetarian dishes?"
    email_body = EmailUtils.create_feedback_email_body(name, email, feedback_type, message)

    assert f"<strong>Name:</strong> {name}" in email_body
    assert f"<strong>Email:</strong> {email}" in email_body
    assert f"<strong>Type:</strong> {feedback_type}" in email_body
    assert f"<strong>Message:</strong> {message}" in email_body


def test_create_reset_password_email():
    """Test the creation of a reset password email."""
    user_name = "John Doe"
    reset_link = "https://example.com/reset?token=12345"
    email_body = EmailUtils.create_reset_password_email(user_name, reset_link)

    assert f"Hello {user_name}," in email_body
    assert f'<a href="{reset_link}">Reset Password</a>' in email_body


def test_create_newsletter_email():
    """Test the creation of a newsletter email."""
    title = "Weekly Newsletter"
    body_content = "Here are the updates for this week!"
    email_body = EmailUtils.create_newsletter_email(title, body_content)

    assert f"<h1>{title}</h1>" in email_body
    assert f"<p>{body_content}</p>" in email_body


def test_create_daily_menu_email():
    """Test the creation of a daily menu email."""
    menu_items = ["Spaghetti", "Salad", "Grilled Chicken"]
    email_body = EmailUtils.create_daily_menu_email(menu_items)

    for item in menu_items:
        assert f"<li>{item}</li>" in email_body
    assert "Today's Menu:" in email_body


def test_generate_attachment_part():
    """Test the generation of an email attachment part."""
    attachment_path = "testfile.txt"  # Ensure this file exists in your test setup
    attachment_part = EmailUtils.generate_attachment_part(attachment_path)

    assert "Content-Disposition" in attachment_part["Content-Disposition"]
    assert "attachment" in attachment_part["Content-Disposition"]
    assert attachment_part.get_payload() is not None


def test_generate_subscription_confirmation_email():
    """Test the generation of a subscription confirmation email."""
    user_email = "newuser@example.com"
    email_body = EmailUtils.generate_subscription_confirmation_email(user_email)

    assert "Thank you for subscribing" in email_body
    assert "You will now receive regular updates" in email_body


def test_generate_special_offer_email():
    """Test the generation of a special offer email."""
    offer_details = "50% off on all meals this weekend!"
    email_body = EmailUtils.generate_special_offer_email(offer_details)

    assert "<h1>Special Offer Just for You!</h1>" in email_body
    assert offer_details in email_body

def test_validate_attachment_size():
    """Test the validation of attachment size."""
    valid_file = "small_file.txt"  # Ensure this file exists and is small enough
    invalid_file = "large_file.txt"  # Ensure this file exceeds the size limit

    assert EmailUtils.validate_attachment_size(valid_file)
    assert not EmailUtils.validate_attachment_size(invalid_file)


def test_parse_email_body_from_html():
    """Test the extraction of body content from HTML email."""
    html_content = """
        <html>
            <body>
                <h1>Important Update</h1>
                <p>This is an important update for you.</p>
            </body>
        </html>
    """
    body_content = EmailUtils.parse_email_body_from_html(html_content)

    assert "Important Update" in body_content
    assert "This is an important update for you." in body_content
