"""
Filename:
    conftest.py

Note:
    Define fixtures and set up the testing database
"""
import pytest
from website import create_app
from website.models import db as _db


class TestConfig(dict):
    """Test configuration."""
    SECRET_KEY = 'test'
    TESTING = True
    # Explicitly set the database URI as a class attribute
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False

    # Mock Google OAuth settings
    GOOGLE_OAUTH_CLIENT_ID = 'test-client-id'
    GOOGLE_OAUTH_CLIENT_SECRET = 'test-client-secret'
    OAUTHLIB_RELAX_TOKEN_SCOPE = True
    OAUTHLIB_INSECURE_TRANSPORT = True

    # Mock API credentials
    MENU_API_USERNAME = 'test-api-user'
    MENU_API_PASSWORD = 'test-api-pass'

    # Other settings
    SERVER_NAME = 'localhost'
    CACHE_DIR = 'tests/test_cache'
    PREFERRED_URL_SCHEME = 'http'

    def __iter__(self):
        for key in dir(self):
            if not key.startswith('_'):
                yield key

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Create an instance of TestConfig
    # test_config = TestConfig()
    # Create the app with the test config
    _app = create_app()
    # Explicitly update the config
    _app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True,
        'SECRET_KEY': 'test',
        'WTF_CSRF_ENABLED': False,
        'GOOGLE_OAUTH_CLIENT_ID': 'test-client-id',
        'GOOGLE_OAUTH_CLIENT_SECRET': 'test-client-secret',
        'OAUTHLIB_RELAX_TOKEN_SCOPE': True,
        'OAUTHLIB_INSECURE_TRANSPORT': True,
        'MENU_API_USERNAME': 'test-api-user',
        'MENU_API_PASSWORD': 'test-api-pass',
        'SERVER_NAME': 'localhost',
        'PREFERRED_URL_SCHEME': 'http',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })

    # Setup app context
    ctx = _app.app_context()
    ctx.push()
    # Initialize and create database
    _db.init_app(_app)
    _db.create_all()
    yield _app
    # Cleanup
    _db.session.remove()
    _db.drop_all()
    ctx.pop()


@pytest.fixture
def db(app):
    """Create a fresh database for each test."""
    _db.drop_all()
    _db.create_all()
    return _db


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client):
    """Create an authenticated test client."""
    with client.session_transaction() as session:
        session['google_oauth_token'] = {'access_token': 'fake-token'}
        session['user_info'] = {
            'email': 'test@colby.edu',
            'name': 'Test User'
        }
    return client


@pytest.fixture
def admin_client(client):
    """Create an admin test client."""
    with client.session_transaction() as session:
        session['google_oauth_token'] = {'access_token': 'fake-token'}
        session['user_info'] = {
            'email': 'admin@colby.edu',
            'name': 'Admin User'
        }
        session['is_admin'] = True
    return client
