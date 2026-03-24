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
        "is_public": False,
        "due_cards": 0,
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
        assert "due_cards" in result["deck"]
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
        assert "due_cards" in result[0]
    
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
            {"d_id": 1, "deck_name": "Spanish", "due_count": 5}
        ]

        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.get_decks_with_due_cards("user-123")

        assert len(result) == 1
        assert result[0]["due_count"] == 5

    def test_get_decks_with_due_cards_excludes_zero(self, deck_service):
        """Test that decks with due_cards=0 are not returned (filtered by the query)."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.get_decks_with_due_cards("user-123")

        assert result == []


class TestGetRecentDecks:
    """Tests for get_recent_decks method."""
    
    def test_get_recent_decks_success(self, deck_service):
        """Test retrieval of recently reviewed decks."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"d_id": 1, "deck_name": "Spanish", "card_count": 10, "due_cards": 3}
        ]

        with patch('services.deck_service.get_db_cursor') as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = DeckService.get_recent_decks("user-123")

        assert len(result) == 1
        assert "due_cards" in result[0]
    
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
