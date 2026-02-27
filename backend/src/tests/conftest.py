import pytest
from main import create_app
import os
from flask_jwt_extended import create_access_token
from db import get_db_cursor

"""
Run all unit tests with:
    docker compose exec backend poetry run pytest
Run all integration tests with:
    docker compose exec backend poetry run pytest -m integration
Unless otherwise specified.
"""

@pytest.fixture(scope="session")
def db_schema():
    """Set up test database schema from SQL file. Runs once per test session."""
    # Setup code before tests run
    # Read the SQL file
    # In Docker: /database/init/01_create_table.sql (mounted volume)
    # In local: relative path from tests folder
    import os
    if os.path.exists('/database/init/01_create_table.sql'):
        sql_file_path = '/database/init/01_create_table.sql'
    else:
        # Fallback for local development
        sql_file_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'database', 'init', '01_create_table.sql')
    
    with open(sql_file_path, 'r') as f:
        sql_script = f.read()
    
    # Drop existing tables first to ensure clean slate
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DROP TABLE IF EXISTS Review_Logs CASCADE")
        cursor.execute("DROP TABLE IF EXISTS Cards CASCADE")
        cursor.execute("DROP TABLE IF EXISTS Decks CASCADE")
        cursor.execute("DROP TABLE IF EXISTS Users CASCADE")
    
    # Create tables from SQL file
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(sql_script)
    
    # pass to tests that use this fixture
    yield
    
    # Cleanup after all tests
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DROP TABLE IF EXISTS Review_Logs CASCADE")
        cursor.execute("DROP TABLE IF EXISTS Cards CASCADE")
        cursor.execute("DROP TABLE IF EXISTS Decks CASCADE")
        cursor.execute("DROP TABLE IF EXISTS Users CASCADE")

@pytest.fixture
def db_setup(db_schema):
    """Set up test data before each test."""
    with get_db_cursor(commit=True) as cursor:
        # Clean up existing test data
        cursor.execute("DELETE FROM Cards WHERE d_id IN (SELECT d_id FROM Decks WHERE u_id = 'test-user-id')")
        cursor.execute("DELETE FROM Decks WHERE u_id = 'test-user-id'")
        cursor.execute("DELETE FROM Users WHERE u_id = 'test-user-id'")
        
        # Insert test user
        cursor.execute("""
            INSERT INTO Users (u_id, email, display_name, timezone)
            VALUES ('test-user-id', 'test@example.com', 'Test User', 'America/Toronto')
        """)
        
        # Reset the decks sequence to ensure we get d_id = 1  
        cursor.execute("SELECT setval('decks_d_id_seq', 1, false)")
        
        # Insert test deck with d_id = 1
        cursor.execute("""
            INSERT INTO Decks (u_id, deck_name, word_lang, trans_lang, description)
            VALUES ('test-user-id', 'Test Deck', 'Spanish', 'English', 'Test deck for integration tests')
            RETURNING d_id
        """)
        deck_result = cursor.fetchone()
        test_deck_id = deck_result['d_id']
        
        # Insert test card
        cursor.execute("""
            INSERT INTO Cards (d_id, word, translation, word_roman)
            VALUES (%s, 'hola', 'hello', 'oh-lah')
        """, (test_deck_id,))
    
    yield test_deck_id
    
    # Cleanup after each test
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM Cards WHERE d_id IN (SELECT d_id FROM Decks WHERE u_id = 'test-user-id')")
        cursor.execute("DELETE FROM Decks WHERE u_id = 'test-user-id'")
        cursor.execute("DELETE FROM Users WHERE u_id = 'test-user-id'")

@pytest.fixture
def app(db_setup):
    """Create and configure a test app instance."""
    # Set environment variables before creating app so they're picked up during initialization
    os.environ['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID', 'test-client-id')
    os.environ['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'test-secret-key')
    
    app = create_app()
    app.config['TESTING'] = True

    yield app

@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()

@pytest.fixture
def auth_token(app):
    """Create a test JWT access token."""
    with app.app_context():
        token = create_access_token(identity='test-user-id')
        return token

@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers with JWT token."""
    return {'Authorization': f'Bearer {auth_token}'}

