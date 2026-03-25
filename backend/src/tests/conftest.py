import pytest
from main import create_app
import os
from flask_jwt_extended import create_access_token
from db import get_db_cursor
from minio import Minio
import psycopg2
import pandas as pd
from datetime import datetime
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import execute_values
from services.fsrs.scheduler import DEFAULT_PARAMETERS

"""
Run all unit tests with:
    docker compose exec backend poetry run pytest
Run all integration tests with:
    docker compose exec backend poetry run pytest -m integration
Unless otherwise specified.
"""

def cleanup_minio_test_data():
    """Clean up all test files from MinIO bucket."""
    try:
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000").replace("http://", "")
        access_key = os.getenv("MINIO_ACCESS_KEY")
        secret_key = os.getenv("MINIO_SECRET_KEY")
        bucket_name = os.getenv("MINIO_BUCKET_NAME", "languine-media")
        
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        
        # List and delete all objects in bucket
        objects = client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            client.remove_object(bucket_name, obj.object_name)
            print(f"Cleaned up MinIO file: {obj.object_name}")
    except Exception as e:
        print(f"MinIO cleanup warning: {e}")

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
    # Use regular psycopg2 cursor with autocommit
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        cursor.execute(sql_script)
        print("Successfully created database schema")
    except Exception as e:
        print(f"Error creating database schema: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
    
    # pass to tests that use this fixture
    yield
    
    # Cleanup after all tests
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DROP TABLE IF EXISTS Review_Logs CASCADE")
        cursor.execute("DROP TABLE IF EXISTS Cards CASCADE")
        cursor.execute("DROP TABLE IF EXISTS Decks CASCADE")
        cursor.execute("DROP TABLE IF EXISTS Users CASCADE")
    
    # Final MinIO cleanup
    cleanup_minio_test_data()

@pytest.fixture(scope="session")
def system_decks(db_schema):
    """Seed the system user and built-in reference decks used by copy-on-signup logic.

    Session-scoped so the data is inserted once and persists across all tests.
    db_setup (function-scoped) only touches 'test-user-id' data and leaves this intact.
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO Users (u_id, email, display_name, timezone)
            VALUES ('system', 'system@languine.app', 'Languine', 'UTC')
            ON CONFLICT (u_id) DO NOTHING
        """)
        cursor.execute("""
            INSERT INTO Decks (u_id, deck_name, word_lang, trans_lang, description, is_public)
            VALUES
                ('system', 'Mandarin Chinese Beginner', 'Chinese (Mandarin)', 'English',
                 'Essential beginner vocabulary for Mandarin Chinese', true),
                ('system', 'Korean Beginner', 'Korean', 'English',
                 'Essential beginner vocabulary for Korean', true),
                ('system', 'French Beginner', 'French', 'English',
                 'Essential beginner vocabulary for French', true), 
                ('system', 'Japanese Beginner', 'Japanese', 'English',
                 'Essential beginner vocabulary for Japanese', true)
            ON CONFLICT (u_id, deck_name) DO NOTHING
        """)
        # Insert 3 sample cards per deck (12 total) — enough to verify copying works
        cursor.execute("""
            WITH deck_cards(deck_name, word, translation, word_example, trans_example) AS (VALUES
                ('Mandarin Chinese Beginner', '你好',  'hello',
                 '你好！很高兴见到你。',           'Hello! I''m happy to see you.'),
                ('Mandarin Chinese Beginner', '您好',  'hello (polite)',
                 '您好，请问这里是图书馆吗？',     'Hello, may I ask if this is the library?'),
                ('Mandarin Chinese Beginner', '早上好', 'good morning',
                 '早上好！你今天睡得好吗？',       'Good morning! Did you sleep well today?'),
                ('Korean Beginner', '안녕하세요', 'hello',
                 '안녕하세요 저는 한국어를 배우고 있는 학생입니다.', 'Hello I am a student learning Korean.'),
                ('Korean Beginner', '감사합니다', 'thank you',
                 '도와주셔서 정말 감사합니다.',     'Thank you very much for helping me.'),
                ('Korean Beginner', '죄송합니다', 'sorry',
                 '늦게 와서 죄송합니다 다음에는 더 일찍 오겠습니다.', 'Sorry for arriving late I will come earlier next time.'),
                ('Japanese Beginner', '一つ', 'one (thing)',
                 'それを一つください。',           'Please give me one of those.'),
                ('Japanese Beginner', '二つ', 'two (things)',
                 'ソフトクリームを二つください。', 'Please give me two ice cream cones.'),
                ('Japanese Beginner', '円', 'yen',
                 'カレーライスは700円です。',       'The curry and rice is 700 yen.'),
                ('French Beginner', 'etre', 'to be',   'tout le monde veut être beau', 'everyone wants to be beautiful'),
                ('French Beginner', 'avoir', 'to have', 'on était six donc tu peux pas avoir une conversation', 'there were six of us so you can`t have a conversation'),
                ('French Beginner', 'il', 'he',  'allez voir s`il est blessé', 'go see if he is injured')
            )
            INSERT INTO Cards (d_id, word, translation, word_example, trans_example)
            SELECT d.d_id, dc.word, dc.translation, dc.word_example, dc.trans_example
            FROM deck_cards dc
            JOIN Decks d ON d.deck_name = dc.deck_name AND d.u_id = 'system'
        """)

    yield

    # Cascade delete removes system decks and cards too
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM Users WHERE u_id = 'system'")


@pytest.fixture
def db_setup(db_schema):
    """Set up test data before each test."""
    with get_db_cursor(commit=True) as cursor:
        # Clean up existing test data
        cursor.execute("DELETE FROM Cards WHERE d_id IN (SELECT d_id FROM Decks WHERE u_id = 'test-user-id')")
        cursor.execute("DELETE FROM Decks WHERE u_id = 'test-user-id'")
        cursor.execute("DELETE FROM Users WHERE u_id = 'test-user-id'")
        cursor.execute("DELETE FROM Review_Logs WHERE c_id IN (SELECT c_id FROM Cards WHERE d_id IN (SELECT d_id FROM Decks WHERE u_id = 'test-user-id'))")

        # Insert test user
        cursor.execute("""
            INSERT INTO Users (u_id, email, display_name, timezone, fsrs_parameters, total_reviews, reviews_since_last_optimize)
            VALUES ('test-user-id', 'test@example.com', 'Test User', 'America/Toronto', %s, 600, 600)
        """, (list(DEFAULT_PARAMETERS),))
        
        # Reset the decks sequence to ensure we get d_id = 1  
        cursor.execute("SELECT setval('decks_d_id_seq', 1, false)")
        
        # Insert test deck with d_id = 1
        cursor.execute("""
            INSERT INTO Decks (u_id, deck_name, word_lang, trans_lang, description)
            VALUES ('test-user-id', 'Test Deck', 'es', 'en', 'Test deck for integration tests')
            RETURNING d_id
        """)
        deck_result = cursor.fetchone()
        test_deck_id = deck_result['d_id']
        
        # Insert test card
        cursor.execute("""
            INSERT INTO Cards (d_id, word, translation, word_roman)
            VALUES (%s, 'hola', 'hello', 'oh-lah')
        """, (test_deck_id,))

        csv_path = os.path.join(os.path.dirname(__file__), 'sample_data', 'sample_logs.csv')
        df = pd.read_csv(csv_path)
        unique_card_ids = list(df['card_id'].unique())

        # Batch-insert one card per unique CSV card_id and collect the generated c_ids.
        # PostgreSQL RETURNING preserves VALUES insertion order, giving us the mapping.
        
        # rows must be tuples, and we need to insert the same number of rows as unique card_ids in the CSV to maintain the mapping logic
        card_rows = [
            (test_deck_id, f'word_{i + 1}', f'translation_{i + 1}')
            for i in range(len(unique_card_ids))
        ]
        # execute_values is more efficient for bulk inserts and allows us to get all generated c_ids in one query, which is crucial for mapping the review logs correctly
        inserted_cards = execute_values(
            cursor,
            "INSERT INTO Cards (d_id, word, translation) VALUES %s RETURNING c_id",
            card_rows,
            fetch=True,
        )

        # Create a mapping from original card_id in CSV to the inserted c_id in the database, based on the order of unique card_ids and the returned inserted_cards
        card_id_map = {
            original_id: inserted_cards[i]['c_id']
            for i, original_id in enumerate(unique_card_ids)
        }

        # Batch-insert all review logs
        log_rows = [
            (
                card_id_map[row['card_id']],
                int(row['grade']),
                datetime.fromisoformat(row['review_datetime']),
                int(row['review_duration']),
            )
            for _, row in df.iterrows()
        ]
        execute_values(
            cursor,
            "INSERT INTO Review_Logs (c_id, grade, review_date, review_duration) VALUES %s",
            log_rows,
        )
    
    yield test_deck_id
    
    # Cleanup after each test
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM Cards WHERE d_id IN (SELECT d_id FROM Decks WHERE u_id = 'test-user-id')")
        cursor.execute("DELETE FROM Decks WHERE u_id = 'test-user-id'")
        cursor.execute("DELETE FROM Users WHERE u_id = 'test-user-id'")
        cursor.execute("DELETE FROM Review_Logs WHERE c_id IN (SELECT c_id FROM Cards WHERE d_id IN (SELECT d_id FROM Decks WHERE u_id = 'test-user-id'))")
    
    # Clean up MinIO test files
    cleanup_minio_test_data()

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


@pytest.fixture
def mock_tts_for_integration(monkeypatch):
    """
    Mock TTS generation for card integration tests.
    
    Integration tests should focus on API behavior, not TTS generation.
    This fixture mocks TTSService.generate_speech to return dummy audio data.
    
    Apply to tests using:
        @pytest.mark.usefixtures("mock_tts_for_integration")
    """
    import numpy as np
    
    # Mock TTSService.generate_speech
    def mock_generate_speech(self, text, language="en", speaker=None, speaker_wav=None):
        """Return dummy audio data instead of generating real TTS."""
        # Return a small dummy audio array (1 second at 22050 Hz sample rate)
        sample_rate = 22050
        duration = 1.0
        samples = int(sample_rate * duration)
        # Generate a simple sine wave as dummy audio
        frequency = 440  # A4 note
        t = np.linspace(0, duration, samples, False)
        dummy_audio = 0.5 * np.sin(2 * np.pi * frequency * t)
        return dummy_audio.astype(np.float32)
    
    # Apply the mock
    from services.tts_service import TTSService
    monkeypatch.setattr(TTSService, 'generate_speech', mock_generate_speech)
    print("TTS mocked for integration test")


@pytest.fixture(scope="module")
def seeded_db(db_schema):
    """Execute 02_seed_builtin_decks.sql once for this module, then clean up.

    NOTE: The COPY commands in the seed SQL read from /docker-entrypoint-initdb.d/
          which is only mounted in Docker. This fixture must be used inside the container.
    """
    if os.path.exists("/database/init/02_seed_builtin_decks.sql"):
        sql_path = "/database/init/02_seed_builtin_decks.sql"
    else:
        sql_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "database", "init", "02_seed_builtin_decks.sql",
        )

    with open(sql_path) as f:
        sql = f.read()

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    try:
        cur.execute(sql)
    finally:
        cur.close()
        conn.close()

    yield

    with get_db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM Users WHERE u_id = 'system'")
