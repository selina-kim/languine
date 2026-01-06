import pytest
from main import create_app
import os

@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID', 'test-client-id')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'test-secret-key')

    yield app

@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()

