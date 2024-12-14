"""
Filename:
    __init__.py
"""
import os
import logging
import sys
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app(test_config=None):
    """create app"""
    # Load environment variables
    load_dotenv()

    from .scheduler import SchedulerService
    y = SchedulerService()
    # Initialize Flask app
    app = Flask(__name__, static_folder='static')
    with app.app_context():
        y.init_app(app)

    # Configure logging
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info("Starting application initialization...")

    from .views import main_blueprint
    from .menu_routes import menu_bp
    from .utils import create_tags
    from .auth import auth_bp, google_bp, login_manager, init_admin_model

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

        # JawsDB Support
        # database_url = os.getenv('JAWSDB_URL')
        # if database_url:
        #     database_url = database_url.replace('mysql://', 'mysql+mysqlconnector://')
        #     app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        #     logger.info("Using JawsDB URL for database connection")
        # else:
        #    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
        #    logger.info("Using default database URL")

    else:
        app.config.update(test_config)

    # Initialize extensions
    try:
        db.init_app(app)
        login_manager.init_app(app)
        init_admin_model()
        logger.info("Core services initialized successfully")
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise

    with app.app_context():
        try:
            db.create_all()  # Create the database tables
            create_tags()  # Assuming this function creates necessary initial data
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Startup error: {e}")

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(main_blueprint)
    app.register_blueprint(menu_bp, url_prefix='/api/menu')

    app.config.update({
        'MENU_API_USERNAME': os.getenv('MENU_API_USERNAME'),
        'MENU_API_PASSWORD': os.getenv('MENU_API_PASSWORD')
    })

    return app
