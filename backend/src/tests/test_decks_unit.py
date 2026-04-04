"""Unit tests for DeckService.

Tests the deck service logic with mocked dependencies:
- Deck CRUD operations (create, read, list)
- Deck queries (due cards, recent decks)
- Import/export support methods
- Database error handling

Run this test file:
    docker compose exec backend pytest src/tests/test_decks_unit.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_decks_unit.py --cov=services.deck_service
"""

import pytest
import psycopg2
from datetime import datetime
from unittest.mock import MagicMock, patch
from services.deck_service import (
    DeckService,
    DuplicateDeckNameError,
    UserNotFoundError,
    DatabaseError
)


class _FakeIntegrityError(psycopg2.IntegrityError):
    """Custom IntegrityError that allows setting pgcode."""
    def __init__(self, msg: str, pgcode: str):
        super().__init__(msg)
        self._pgcode = pgcode
    
    @property
    def pgcode(self):
        return self._pgcode


@pytest.fixture
def deck_service():
    """Fixture for DeckService instance"""
    return DeckService()


@pytest.fixture
def sample_deck_response():
    """Sample deck row from database"""
    return {
        "d_id": 1,
        "deck_name": "Spanish Basics",
        "word_lang": "es",
        "trans_lang": "en",
        "description": "Basic Spanish vocabulary",
        "creation_date": datetime(2026, 1, 15),
        "last_reviewed": None,
        "is_public": False
    }


@pytest.fixture
def sample_card_response():
    """Sample card row from database"""
    return {
        "c_id": 1,
        "word": "hola",
        "translation": "hello",
        "definition": "A greeting",
        "word_example": "Hola, ¿cómo estás?",
        "trans_example": "Hello, how are you?",
        "word_roman": "oh-lah",
        "trans_roman": "",
        "image": "",
        "learning_state": 0,
        "difficulty": 0.3,
        "stability": 1.0,
        "due_date": "2026-01-15T00:00:00"
    }


class TestDeckInitMinio:
    def test_deck_service_init_minio_no_creds(self, monkeypatch):
        """Test init without credentials."""
        monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
        monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
        monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
        service = DeckService()
        assert service.minio_client is None
        
    @patch('minio.Minio')
    def test_deck_service_init_minio_exception(self, MockMinio, monkeypatch):
        """Test init with minio exception."""
        monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "access")
        monkeypatch.setenv("MINIO_SECRET_KEY", "secret")
        MockMinio.side_effect = Exception("minio connect error")
        service = DeckService()
        assert service.minio_client is None

class TestDeckServiceMinio:
    """Tests for MinIO interactions in DeckService."""

    def test_delete_from_minio_empty(self, deck_service):
        """Test delete with empty object_id."""
        result = deck_service._delete_from_minio("")
        assert result is True

    def test_delete_from_minio_none(self, deck_service):
        """Test delete with None object_id."""
        result = deck_service._delete_from_minio(None)
        assert result is True

    def test_delete_from_minio_no_client(self, deck_service):
        """Test delete when MinIO client is unavailable."""
        deck_service.minio_client = None
        result = deck_service._delete_from_minio("some/object/path")
        assert result is True

    def test_delete_from_minio_success(self, deck_service):
        """Test successful MinIO object deletion."""
        mock_minio = MagicMock()
        deck_service.minio_client = mock_minio
        
        result = deck_service._delete_from_minio("images/card_123.jpg")
        
        assert result is True
        mock_minio.remove_object.assert_called_once_with("languine-media", "images/card_123.jpg")

    def test_delete_from_minio_handles_errors(self, deck_service):
        """Test delete handles MinIO errors gracefully."""
        mock_minio = MagicMock()
        mock_minio.remove_object.side_effect = Exception("MinIO error")
        deck_service.minio_client = mock_minio
        
        result = deck_service._delete_from_minio("images/card_123.jpg")
        
        assert result is False

class TestGetDeckWithCards:
    """Tests for get_deck_with_cards method."""
    
    def test_get_deck_with_cards_success(self, deck_service, sample_deck_response, sample_card_response):
        """Test successful deck retrieval with cards."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_deck_response
        mock_cursor.fetchall.return_value = [sample_card_response]
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.get_deck_with_cards("user-123", 1)
        
        assert result is not None
        assert result["deck"]["deck_name"] == "Spanish Basics"
        assert len(result["cards"]) == 1
        assert result["cards"][0]["word"] == "hola"
    
    def test_get_deck_with_cards_not_found(self, deck_service):
        """Test retrieval of non-existent deck."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.get_deck_with_cards("user-123", 999)
        
        assert result is None
    
    def test_get_deck_with_cards_empty_deck(self, deck_service, sample_deck_response):
        """Test deck with no cards."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_deck_response
        mock_cursor.fetchall.return_value = []
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.get_deck_with_cards("user-123", 1)
        
        assert result is not None
        assert len(result["cards"]) == 0


class TestGetDeckForExport:
    """Tests for get_deck_for_export method."""
    
    def test_get_deck_for_export_success(self, deck_service, sample_deck_response, sample_card_response):
        """Test successful deck export data retrieval."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_deck_response
        mock_cursor.fetchall.return_value = [sample_card_response]
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.get_deck_for_export("user-123", 1)
        
        assert result is not None
        assert "deck" in result
        assert "cards" in result
        assert result["deck"]["deck_name"] == "Spanish Basics"
    
    def test_get_deck_for_export_not_found(self, deck_service):
        """Test export data for non-existent deck."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.get_deck_for_export("user-123", 999)
        
        assert result is None


class TestListUserDecks:
    """Tests for list_user_decks method."""
    
    def test_list_user_decks_success(self, deck_service, sample_deck_response):
        """Test listing user's decks."""
        deck_with_count = {**sample_deck_response, "card_count": 10}
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [deck_with_count]
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.list_user_decks("user-123")
        
        assert len(result) == 1
        assert result[0]["deck_name"] == "Spanish Basics"
        assert result[0]["card_count"] == 10
    
    def test_list_user_decks_empty(self, deck_service):
        """Test listing when user has no decks."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.list_user_decks("user-123")
        
        assert len(result) == 0


class TestCreateDeck:
    """Tests for create_deck method."""
    
    def test_create_deck_success(self, deck_service, sample_deck_response):
        """Test successful deck creation."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_deck_response
        
        deck_data = {
            "deck_name": "Spanish Basics",
            "word_lang": "es",
            "trans_lang": "en",
            "description": "Basic Spanish vocabulary"
        }
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.create_deck("user-123", deck_data)
        
        assert result["deck_name"] == "Spanish Basics"
        assert "d_id" in result
    
    def test_create_deck_duplicate_name(self, deck_service):
        """Test deck creation with duplicate name."""
        mock_cursor = MagicMock()
        
        # Simulate unique constraint violation
        integrity_error = _FakeIntegrityError("duplicate key", "23505")
        mock_cursor.execute.side_effect = integrity_error
        
        deck_data = {
            "deck_name": "Duplicate",
            "word_lang": "es",
            "trans_lang": "en"
        }
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with pytest.raises(DuplicateDeckNameError):
                DeckService.create_deck("user-123", deck_data)
    
    def test_create_deck_user_not_found(self, deck_service):
        """Test deck creation with non-existent user."""
        mock_cursor = MagicMock()
        
        # Simulate foreign key violation
        integrity_error = _FakeIntegrityError("foreign key violation", "23503")
        mock_cursor.execute.side_effect = integrity_error
        
        deck_data = {
            "deck_name": "Test",
            "word_lang": "es",
            "trans_lang": "en"
        }
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with pytest.raises(UserNotFoundError):
                DeckService.create_deck("invalid-user", deck_data)
    
    def test_create_deck_database_error(self, deck_service):
        """Test deck creation with database error."""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.ProgrammingError("syntax error")
        
        deck_data = {
            "deck_name": "Test",
            "word_lang": "es",
            "trans_lang": "en"
        }
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with pytest.raises(DatabaseError):
                DeckService.create_deck("user-123", deck_data)
    
    def test_create_deck_integrity_error_other(self, deck_service):
        """Test deck creation with other integrity error."""
        mock_cursor = MagicMock()
        integrity_error = _FakeIntegrityError("other integrity error", "11111")
        mock_cursor.execute.side_effect = integrity_error
        
        deck_data = {
            "deck_name": "Test",
            "word_lang": "es",
            "trans_lang": "en"
        }
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with pytest.raises(DatabaseError):
                DeckService.create_deck("user-123", deck_data)


class TestSaveImportedDeck:
    """Tests for save_imported_deck method."""
    
    def test_save_imported_deck_success(self, deck_service, sample_deck_response):
        """Test successful save of imported deck."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_deck_response
        
        imported_data = {
            "deck": {
                "deck_name": "Imported Deck",
                "word_lang": "fr",
                "trans_lang": "en",
                "description": "Imported"
            },
            "cards": [
                {
                    "word": "bonjour",
                    "translation": "hello",
                    "definition": "",
                    "word_example": "",
                    "trans_example": "",
                    "word_roman": "",
                    "trans_roman": "",
                    "image": ""
                }
            ]
        }
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.save_imported_deck("user-123", imported_data)
        
        assert "deck_id" in result
        assert result["cards_count"] == 1
    
    def test_save_imported_deck_missing_deck(self, deck_service):
        """Test save imported deck with no cards."""
        mock_cursor = MagicMock()
        
        imported_data = {
            "cards": []
        }
        
        with pytest.raises(KeyError):
            with patch('services.deck_service.get_db_cursor') as mock_db:
                mock_db.return_value.__enter__.return_value = mock_cursor
                result = DeckService.save_imported_deck("user-123", imported_data)
        
    def test_save_imported_deck_null_description(self, deck_service, sample_deck_response):
        """Test save imported deck with missing or none description."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_deck_response
        
        imported_data = {
            "deck": {
                "deck_name": "Empty Deck",
                "word_lang": "fr",
                "trans_lang": "en",
                "description": None
            },
            "cards": []
        }
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.save_imported_deck("user-123", imported_data)
        
        assert result["cards_count"] == 0

    def test_save_imported_deck_empty_cards(self, deck_service, sample_deck_response):
        """Test save imported deck with no cards."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_deck_response
        
        imported_data = {
            "deck": {
                "deck_name": "Empty Deck",
                "word_lang": "fr",
                "trans_lang": "en"
            },
            "cards": []
        }
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.save_imported_deck("user-123", imported_data)
        
        assert result["cards_count"] == 0


class TestGetDecksWithDueCards:
    """Tests for get_decks_with_due_cards method."""
    
    def test_get_decks_with_due_cards_success(self, deck_service):
        """Test retrieval of decks with due cards."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"d_id": 1, "deck_name": "Spanish", "due_count": 5, "total_cards": 10}
        ]
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.get_decks_with_due_cards("user-123")
        
        assert len(result) == 1
        assert result[0]["due_count"] == 5


class TestGetRecentDecks:
    """Tests for get_recent_decks method."""
    
    def test_get_recent_decks_success(self, deck_service):
        """Test retrieval of recently reviewed decks."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"d_id": 1, "deck_name": "Spanish", "card_count": 10}
        ]
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.get_recent_decks("user-123")
        
        assert len(result) == 1
    
    def test_get_recent_decks_with_limit(self, deck_service):
        """Test limit parameter for recent decks."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            DeckService.get_recent_decks("user-123", limit=5)
        
        # Verify the query was called with correct parameters
        assert mock_cursor.execute.called
        query, params = mock_cursor.execute.call_args[0]
        
        # Verify limit parameter is in the query params (exact position may vary)
        assert 5 in params, "Limit parameter should be passed to query"


class TestUpdateDeck:
    """Tests for update_deck method."""
    
    def test_update_deck_success_partial(self, deck_service, sample_deck_response):
        """Test successful partial deck update."""
        updated_deck = sample_deck_response.copy()
        updated_deck["deck_name"] = "Updated Spanish Basics"
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = updated_deck
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.update_deck(
                "user-123",
                1,
                {"deck_name": "Updated Spanish Basics"}
            )
        
        assert result is not None
        assert result["deck_name"] == "Updated Spanish Basics"
        assert mock_cursor.execute.called
    
    def test_update_deck_success_all_fields(self, deck_service, sample_deck_response):
        """Test successful update of all fields."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_deck_response
        
        update_data = {
            "deck_name": "New Name",
            "word_lang": "fr",
            "trans_lang": "en",
            "description": "Updated description",
            "is_public": True,
            "link": "https://example.com"
        }
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.update_deck("user-123", 1, update_data)
        
        assert result is not None
        assert mock_cursor.execute.called
    
    def test_update_deck_not_found(self, deck_service):
        """Test update of non-existent deck."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.update_deck(
                "user-123",
                999,
                {"deck_name": "New Name"}
            )
        
        assert result is None
    
    def test_update_deck_duplicate_name(self, deck_service):
        """Test update fails with duplicate deck name."""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = _FakeIntegrityError("Duplicate", "23505")
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            
            with pytest.raises(DuplicateDeckNameError):
                DeckService.update_deck(
                    "user-123",
                    1,
                    {"deck_name": "Existing Deck"}
                )
    
    def test_update_deck_no_changes(self, deck_service, sample_deck_response):
        """Test update with empty data returns existing deck."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_deck_response
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.update_deck("user-123", 1, {})
        
        assert result is not None
        assert result["deck_name"] == "Spanish Basics"
    
    def test_update_deck_database_error(self, deck_service):
        """Test update fails with database error."""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.ProgrammingError("Database programming error")
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            
            with pytest.raises(DatabaseError):
                DeckService.update_deck(
                    "user-123",
                    1,
                    {"deck_name": "New Name"}
                )

    def test_update_deck_integrity_error_other(self, deck_service):
        """Test deck update with other integrity error."""
        mock_cursor = MagicMock()
        
        integrity_error = _FakeIntegrityError("other integrity error", "11111")
        mock_cursor.execute.side_effect = integrity_error
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with pytest.raises(DatabaseError):
                DeckService.update_deck(
                    "user-123",
                    1,
                    {"deck_name": "Test"}
                )


    def test_cleanup_deck_media_exception(self, deck_service):
        """Test cleanup handles database errors."""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.DatabaseError("DB error in cleanup")
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with pytest.raises(psycopg2.DatabaseError):
                deck_service._cleanup_deck_media("user-123", 1)

class TestDeleteDeck:
    """Tests for delete_deck method."""
    
    def test_delete_deck_success(self, deck_service):
        """Test successful deck deletion."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            # Mock the MinIO cleanup method
            with patch.object(deck_service, '_cleanup_deck_media'):
                result = deck_service.delete_deck("user-123", 1)
        
        assert result is True
        assert mock_cursor.execute.called
        
        # Verify DELETE query was executed
        query = mock_cursor.execute.call_args[0][0]
        assert "DELETE FROM Decks" in query
    
    def test_delete_deck_not_found(self, deck_service):
        """Test deletion of non-existent deck."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with patch.object(deck_service, '_cleanup_deck_media'):
                result = deck_service.delete_deck("user-123", 999)
        
        assert result is False
    
    def test_delete_deck_unauthorized(self, deck_service):
        """Test deletion fails when user doesn't own deck."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with patch.object(deck_service, '_cleanup_deck_media'):
                result = deck_service.delete_deck("wrong-user", 1)
        
        assert result is False
    
    def test_delete_deck_database_error(self, deck_service):
        """Test deletion fails with database error."""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("Database error")
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with patch.object(deck_service, '_cleanup_deck_media'):
                with pytest.raises(DatabaseError):
                    deck_service.delete_deck("user-123", 1)
    
    def test_delete_deck_cleans_up_media(self, deck_service):
        """Test that deck deletion cleans up MinIO media files."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with patch.object(deck_service, '_cleanup_deck_media') as mock_cleanup:
                deck_service.delete_deck("user-123", 1)
                
                # Verify cleanup was called with correct parameters
                mock_cleanup.assert_called_once_with("user-123", 1)


class TestCleanupDeckMedia:
    """Tests for _cleanup_deck_media method."""
    
    def test_cleanup_deck_media_success(self, deck_service):
        """Test successful cleanup of deck media files."""
        mock_cursor = MagicMock()
        
        # Mock deck exists and user owns it
        mock_cursor.fetchone.return_value = {"d_id": 1}
        
        # Mock cards with media files
        mock_cursor.fetchall.return_value = [
            {"image": "img1.jpg", "word_audio": "audio1.wav", "trans_audio": "audio2.wav"},
            {"image": "img2.jpg", "word_audio": None, "trans_audio": "audio3.wav"},
            {"image": None, "word_audio": "audio4.wav", "trans_audio": None}
        ]
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with patch.object(deck_service, '_delete_from_minio') as mock_delete:
                deck_service._cleanup_deck_media("user-123", 1)
                
                # Verify all media files were marked for deletion (6 total non-None files)
                assert mock_delete.call_count == 6
                mock_delete.assert_any_call("img1.jpg")
                mock_delete.assert_any_call("audio1.wav")
                mock_delete.assert_any_call("audio2.wav")
                mock_delete.assert_any_call("img2.jpg")
                mock_delete.assert_any_call("audio3.wav")
                mock_delete.assert_any_call("audio4.wav")
    
    def test_cleanup_deck_media_no_files(self, deck_service):
        """Test cleanup when deck has no media files."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"d_id": 1}
        mock_cursor.fetchall.return_value = []
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with patch.object(deck_service, '_delete_from_minio') as mock_delete:
                deck_service._cleanup_deck_media("user-123", 1)
                
                # Verify no deletion calls were made
                mock_delete.assert_not_called()
    
    def test_cleanup_deck_media_deck_not_found(self, deck_service):
        """Test cleanup when deck doesn't exist or user doesn't own it."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        
        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            with patch.object(deck_service, '_delete_from_minio') as mock_delete:
                deck_service._cleanup_deck_media("user-123", 999)
                
                # Should return early without attempting deletion
                mock_delete.assert_not_called()
