"""
Filename:
    email_utils.py
"""
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from threading import Thread
import smtplib
from website import db
from .menu_api import BonAppetitAPI
from .models import FavoriteDish, Student
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List


class EmailSender:
    """Class name: EmailSender"""
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv('EMAIL_USERNAME')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
    def send_feedback_email(self, name, email, feedback_type, message):
        """send feedback email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = "ztariq26@colby.edu"  # Replace with recipient email
            msg['Subject'] = f"Colby Dining Feedback - {feedback_type}"
            body = f"""
            New feedback received from Colby Dining website:
            
            Name: {name}
            Email: {email}
            Type: {feedback_type}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  
            Message:
            {message}
            """
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print("Error sending email: %s", str(e))
            return False
    def send_favorite_dish_notification(self, student_email, dishes):
        """
        Send notification for favorite dishes
        """
        try:
            msg = MIMEMultipart('alternative')
# Use alternative to support both plain text and HTML
            msg['From'] = self.sender_email
            msg['To'] = student_email
            msg['Subject'] = "Your Favorite Dishes are Available Today at Colby Dining!"

            # Create both plain text and HTML versions of the message
            text_content = f"""
            Hello!

            Good news! The following favorite dishes are available today at Colby Dining:

            {chr(10).join('• ' + dish for dish in dishes)}

            Visit our dining halls to enjoy your favorite meals!

            Best regards,
            Colby Dining Team
            """
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <p>Hello!</p>
                    
                    <p>Good news! The following favorite dishes are available today at Colby Dining:</p>
                    
                    <ul style="list-style-type: disc; padding-left: 20px;">
                        {chr(10).join(f'<li style="margin-bottom: 8px;">{dish}</li>' for dish in dishes)}
                    </ul>
                    
                    <p>Visit our dining halls to enjoy your favorite meals!</p>
                    
                    <p>Best regards,<br>
                    Colby Dining Team</p>
                </body>
            </html>
            """
            # Attach both versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            logging.info("Successfully sent notification to %s", student_email)
            return True

        except Exception as e:
            logging.error("Error sending notification email to %s: %s", student_email, str(e))
            return False

    def send_async_notification(self, student_email, dishes):
        """Send notification in a separate thread"""
        thread = Thread(target=self.send_favorite_dish_notification, args=(student_email, dishes))
        thread.start()

    @staticmethod
    def check_favorite_dishes(app):
        """Check favorite dishes with proper app context"""
        with app.app_context():
            try:
                logger = logging.getLogger(__name__)
                logger.info("Starting favorite dishes check...")
                menu_service = BonAppetitAPI(
                    username=app.config['MENU_API_USERNAME'],
                    password=app.config['MENU_API_PASSWORD']
                )
                email_sender = EmailSender()
# Get all available dishes for today
                all_dishes = set()
                for hall_id in menu_service.DINING_HALLS.values():
                    try:
                        menu_data = menu_service.get_menu(hall_id)
                        if menu_data:
                            menu = menu_service.process_menu_data(menu_data)
                            for period in menu.values():
                                for item in period:
                                    all_dishes.add(item['name'].lower().strip())
                            logger.info("Found %d meal periods in hall %d", len(menu), hall_id)
                    except Exception as e:
                        logger.error("Error fetching menu for hall %d : %s", hall_id, str(e))
                        continue
                # Get all favorite dishes
                favorites = db.session.query(FavoriteDish)\
                    .join(Student)\
                    .filter(Student.student_email.isnot(None))\
                    .all()
                logger.info("Found %d favorite dishes in database",len(favorites))
                # Group notifications by student
                notifications = {}
                for favorite in favorites:
                    if favorite.dish_name.lower().strip() in all_dishes:
                        if favorite.student_email not in notifications:
                            notifications[favorite.student_email] = []
                        notifications[favorite.student_email].append(favorite.dish_name)
                logger.info("Sending notifications to %d students", len(notifications))
                # Send notifications
                for student_email, dishes in notifications.items():
                    try:
                        logger.info("Sending notification to %s about %d dishes",
student_email, len(dishes))
                        email_sender.send_async_notification(student_email, dishes)
                    except Exception as e:
                        logger.error("Error sending notification to %s: %s", student_email, str(e))
            except Exception as e:
                logger.error("Error in check_favorite_dishes: %s", str(e))


class EmailUtils:
    """General Email Utility Class for common email operations."""

    @staticmethod
    def create_html_email_body(content: str) -> str:
        """
        Creates a simple HTML email body.

        Args:
            content (str): The plain text content that will be embedded in the HTML email.

        Returns:
            str: The HTML body as a string.
        """
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <p>{content}</p>
            </body>
        </html>
        """

    @staticmethod
    def create_plain_text_email_body(content: str) -> str:
        """
        Creates a plain text email body.

        Args:
            content (str): The plain text content of the email.

        Returns:
            str: The plain text body.
        """
        return content

    @staticmethod
    def validate_email_address(email: str) -> bool:
        """
        Validates whether an email address is in a valid format.

        Args:
            email (str): The email address to be validated.

        Returns:
            bool: True if valid, False otherwise.
        """
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        return re.match(email_regex, email) is not None

    @staticmethod
    def format_email_subject(subject: str) -> str:
        """
        Format email subject by trimming and adding a prefix if needed.

        Args:
            subject (str): The subject line for the email.

        Returns:
            str: The formatted subject line.
        """
        if len(subject) > 100:
            subject = subject[:97] + "..."
        return f"[Colby Dining] {subject}"

    @staticmethod
    def create_multipart_email(sender: str, recipient: str, subject: str, body: str,
                               attachments: List[str] = None) -> MIMEMultipart:
        """
        Creates a multipart email message, optionally including attachments.

        Args:
            sender (str): Sender email address.
            recipient (str): Recipient email address.
            subject (str): Subject of the email.
            body (str): Email body (can be plain text or HTML).
            attachments (List[str], optional): A list of file paths to attach.

        Returns:
            MIMEMultipart: The email message.
        """
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = EmailUtils.format_email_subject(subject)

        # Attach the body
        body_part = MIMEText(body, 'html' if body.strip().startswith("<html>") else 'plain')
        msg.attach(body_part)

        # Attach files if provided
        if attachments:
            for attachment in attachments:
                try:
                    part = MIMEBase('application', "octet-stream")
                    with open(attachment, "rb") as f:
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment)}"')
                    msg.attach(part)
                except Exception as e:
                    logging.error(f"Error attaching file {attachment}: {str(e)}")
                    continue

        return msg

    @staticmethod
    def get_student_emails(students: List[str]) -> List[str]:
        """
        Extracts and validates student email addresses from a list.

        Args:
            students (List[str]): List of student email addresses.

        Returns:
            List[str]: List of valid email addresses.
        """
        valid_emails = []
        for email in students:
            if EmailUtils.validate_email_address(email):
                valid_emails.append(email)
            else:
                logging.warning(f"Invalid email address: {email}")
        return valid_emails

    @staticmethod
    def format_datetime_for_email(dt: datetime) -> str:
        """
        Formats a datetime object to a readable string for emails.

        Args:
            dt (datetime): The datetime to be formatted.

        Returns:
            str: A formatted datetime string.
        """
        return dt.strftime("%A, %B %d, %Y at %I:%M %p")

    @staticmethod
    def extract_email_from_text(text: str) -> str:
        """
        Extracts the first valid email address from a given text.

        Args:
            text (str): The input text from which to extract the email.

        Returns:
            str: The extracted email address, if any.
        """
        match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
        return match.group(0) if match else ""

    @staticmethod
    def create_welcome_email(student_name: str) -> str:
        """
        Creates a welcome email body for a new student.

        Args:
            student_name (str): The name of the new student.

        Returns:
            str: The welcome email body.
        """
        return f"""
        <html>
            <body>
                <h2>Welcome to Colby Dining, {student_name}!</h2>
                <p>We're thrilled to have you as part of our community. Enjoy delicious meals and stay updated with your favorite dishes.</p>
                <p>Best regards,</p>
                <p>The Colby Dining Team</p>
            </body>
        </html>
        """

    @staticmethod
    def send_notification_with_unsubscribe_link(student_email: str, unsubscribe_link: str) -> str:
        """
        Creates an email with an unsubscribe link.

        Args:
            student_email (str): The student's email address.
            unsubscribe_link (str): The unsubscribe link to be included in the email.

        Returns:
            str: The email body with an unsubscribe link.
        """
        return f"""
        <html>
            <body>
                <p>Hello, {student_email},</p>
                <p>You are receiving notifications about your favorite dishes. If you'd like to unsubscribe, click the link below:</p>
                <a href="{unsubscribe_link}">Unsubscribe</a>
            </body>
        </html>
        """

    @staticmethod
    def create_feedback_email_body(name: str, email: str, feedback_type: str, message: str) -> str:
        """
        Creates the body of a feedback email.

        Args:
            name (str): The name of the person providing feedback.
            email (str): The email address of the person providing feedback.
            feedback_type (str): The type of feedback (e.g., "Complaint", "Suggestion").
            message (str): The feedback message.

        Returns:
            str: The formatted feedback email body.
        """
        return f"""
        <html>
            <body>
                <h2>New Feedback Received</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Type:</strong> {feedback_type}</p>
                <p><strong>Message:</strong> {message}</p>
            </body>
        </html>
        """
    @staticmethod
    def create_reset_password_email(user_name, reset_link):
        """Create a reset password email with a custom message."""
        html_body = f"""
                <html>
                    <body>
                        <p>Hello {user_name},</p>
                        <p>We received a request to reset your password. Please click the link below to reset it:</p>
                        <p><a href="{reset_link}">Reset Password</a></p>
                        <p>If you didn't request a password reset, please ignore this email.</p>
                    </body>
                </html>
            """
        return html_body

    @staticmethod
    def create_newsletter_email(title, body_content):
        """Create a newsletter email with a specific title and body content."""
        html_body = f"""
                <html>
                    <body>
                        <h1>{title}</h1>
                        <p>{body_content}</p>
                        <footer>Colby Dining News - All rights reserved.</footer>
                    </body>
                </html>
            """
        return html_body

    @staticmethod
    def create_daily_menu_email(menu_items):
        """Create a daily menu email for subscribers with a list of menu items."""
        html_body = "<html><body><h2>Today's Menu:</h2><ul>"
        for item in menu_items:
            html_body += f"<li>{item}</li>"
        html_body += "</ul><footer>Enjoy your meal!</footer></body></html>"
        return html_body

    @staticmethod
    def generate_attachment_part(attachment_path):
        """Generate an email part for an attachment."""
        with open(attachment_path, 'rb') as attachment_file:
            attachment_data = attachment_file.read()
        attachment_part = MIMEText(attachment_data, 'base64')
        attachment_part.add_header(
            'Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"'
        )
        return attachment_part

    @staticmethod
    def generate_subscription_confirmation_email(user_email):
        """Create a subscription confirmation email for new subscribers."""
        html_body = f"""
                <html>
                    <body>
                        <p>Thank you for subscribing to Colby Dining's newsletter!</p>
                        <p>You will now receive regular updates about menus, promotions, and events.</p>
                        <p>If you have any questions, feel free to reply to this email.</p>
                    </body>
                </html>
            """
        return html_body

    @staticmethod
    def generate_special_offer_email(offer_details):
        """Generate an email for a special offer to students."""
        html_body = f"""
                <html>
                    <body>
                        <h1>Special Offer Just for You!</h1>
                        <p>{offer_details}</p>
                        <p>Don't miss out on this limited-time offer. Visit our dining halls today!</p>
                    </body>
                </html>
            """
        return html_body

    @staticmethod
    def validate_attachment_size(attachment_path, max_size_mb=5):
        """Check if the attachment size exceeds the maximum allowed size."""
        file_size = os.path.getsize(attachment_path) / (1024 * 1024)  # Convert bytes to MB
        return file_size <= max_size_mb

    @staticmethod
    def parse_email_body_from_html(html_content):
        """Extract and return the body content from an HTML email."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        body = soup.find('body')
        return body.get_text() if body else ""