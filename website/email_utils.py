"""
Filename:
    email_utils.py
"""
import logging
from website.models import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from threading import Thread
from website.menu_api import BonAppetitAPI
from website.models import FavoriteDish, Student

class EmailSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "colbydining.feedback@gmail.com" 
        self.sender_password = "snft lurw wmsw uzov"
        
    def send_feedback_email(self, name, email, feedback_type, message):
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
            print(f"Error sending email: {str(e)}")
            return False
        
    def send_favorite_dish_notification(self, student_email, dishes):
        try:
            msg = MIMEMultipart('alternative')  # Use alternative to support both plain text and HTML
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
                
            logging.info(f"Successfully sent notification to {student_email}")
            return True

        except Exception as e:
            logging.error(f"Error sending notification email to {student_email}: {str(e)}")
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
                            logger.info(f"Found {len(menu)} meal periods in hall {hall_id}")
                    except Exception as e:
                        logger.error(f"Error fetching menu for hall {hall_id}: {e}")
                        continue
                
                # Get all favorite dishes
                favorites = db.session.query(FavoriteDish)\
                    .join(Student)\
                    .filter(Student.student_email.isnot(None))\
                    .all()
                
                logger.info(f"Found {len(favorites)} favorite dishes in database")
                
                # Group notifications by student
                notifications = {}
                for favorite in favorites:
                    if favorite.dish_name.lower().strip() in all_dishes:
                        if favorite.student_email not in notifications:
                            notifications[favorite.student_email] = []
                        notifications[favorite.student_email].append(favorite.dish_name)
                
                logger.info(f"Sending notifications to {len(notifications)} students")
                
                # Send notifications
                for student_email, dishes in notifications.items():
                    try:
                        logger.info(f"Sending notification to {student_email} about {len(dishes)} dishes")
                        email_sender.send_async_notification(student_email, dishes)
                    except Exception as e:
                        logger.error(f"Error sending notification to {student_email}: {e}")
                        
            except Exception as e:
                logger.error(f"Error in check_favorite_dishes: {e}")