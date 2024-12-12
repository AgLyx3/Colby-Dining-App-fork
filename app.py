from flask import Flask
from scheduler import SchedulerService
from models import db
from flask_login import LoginManager
from views import main_blueprint
from menu_routes import menu_bp
from utils import create_tags
from auth import auth_bp, google_bp, login_manager, init_admin_model
from dotenv import load_dotenv
import os
import logging
import sys

# Configure root logger at module level
logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

def create_app(test_config=None):
    # Load environment variables
    load_dotenv()
    
    # Initialize Flask app
    app = Flask(__name__, static_folder='static')
    
    logger.info("Starting application initialization...")

    # Load configurations
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.getenv('SECRET_KEY'),
            SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            GOOGLE_OAUTH_CLIENT_ID=os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
            GOOGLE_OAUTH_CLIENT_SECRET=os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
            OAUTHLIB_RELAX_TOKEN_SCOPE=os.getenv('OAUTHLIB_RELAX_TOKEN_SCOPE', True),
            OAUTHLIB_INSECURE_TRANSPORT=os.getenv('OAUTHLIB_INSECURE_TRANSPORT', False),
            MENU_API_USERNAME=os.getenv('MENU_API_USERNAME'),
            MENU_API_PASSWORD=os.getenv('MENU_API_PASSWORD'),
            CACHE_DIR=os.getenv('CACHE_DIR', 'instance/cache')
        )
    else:
        app.config.update(test_config)

    # Initialize extensions
    try:
        db.init_app(app)
        login_manager.init_app(app)
        init_admin_model()
        
        # Initialize scheduler within app context
        scheduler = SchedulerService()
        with app.app_context():
            try:
                scheduler.init_app(app)
                logger.info("Scheduler initialized successfully")
            except Exception as e:
                logger.error(f"Scheduler initialization error: {e}")
                # Don't raise here - we can still run without the scheduler
                
        logger.info("Core services initialized successfully")
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(main_blueprint)
    app.register_blueprint(menu_bp, url_prefix='/api/menu')

    # Store scheduler instance on app
    app.scheduler = scheduler

    return app

if __name__ == '__main__':
    app = create_app()
    
    # We can now use the logger directly since it's configured at module level
    with app.app_context():
        try:
            db.create_all()
            create_tags()
            logger.info("Database initialized successfully")
            app.run(debug=os.getenv('FLASK_ENV') == 'development', port=8000)
        except Exception as e:
            logger.error(f"Startup error: {e}", exc_info=True)  # Added exc_info for full traceback