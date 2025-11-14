import pytest
from src.main import create_app
from src import db

@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app('testing')
    
    with app.app_context():
        # ===== TO BE IMPLEMENTED ONCE DATABASE IS READY =====
        # Uncomment once models are defined:
        # db.create_all()
        # ===== END PLACEHOLDER =====
        yield app
        # ===== TO BE IMPLEMENTED ONCE DATABASE IS READY =====
        # Uncomment once models are defined:
        # db.session.remove()
        # db.drop_all()
        # ===== END PLACEHOLDER =====

@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()

# ===== TO BE IMPLEMENTED ONCE DATABASE IS READY =====
# Uncomment and add test_user fixture once User model exists:
#
# @pytest.fixture
# def test_user(app):
#     """Create a test user in the database."""
#     from src.models import User
#     
#     user = User(
#         u_id='test-uid-123',
#         google_id='test-google-id-123',
#         email='test@example.com',
#         display_name='Test User',
#         timezone='UTC'
#     )
#     db.session.add(user)
#     db.session.commit()
#     return user
# ===== END PLACEHOLDER =====