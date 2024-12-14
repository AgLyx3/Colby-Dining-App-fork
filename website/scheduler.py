import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
#from .email_utils import EmailSender


# scheduler.py
class SchedulerService:
    def __init__(self):
        self.scheduler = None
        self.logger = logging.getLogger(__name__)
        
    def init_app(self, app):
        try:
            self.scheduler = BackgroundScheduler()
            
            # Schedule job for 7 AM local time
            self.scheduler.add_job(
                func=lambda: EmailSender.check_favorite_dishes(app),
                trigger=CronTrigger(hour=7, minute=0),
                id='favorite_dishes_notification',
                name='Daily favorite dishes notifications',
                replace_existing=True,
                misfire_grace_time=3600  # Allow 1 hour grace period for misfires
            )
            
            self.scheduler.start()
            self.logger.info("Scheduler started successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing scheduler: {e}")
            raise