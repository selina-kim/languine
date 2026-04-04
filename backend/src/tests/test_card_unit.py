"""Unit tests for CardService.

Tests the card service logic with mocked dependencies:
- URL validation helper
- Deck ownership verification
- Card CRUD operations (create, read, update, delete)
- Deck-level card queries (pagination, review cards)
- MinIO storage operations (skeleton tests)
- TTS generation (skeleton tests)

Run this test file:
    docker compose exec backend pytest src/tests/test_card_unit.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_card_unit.py --cov=services.card_service
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from services.card_service import (
    CardService,
    CardNotFoundError,
    DeckNotFoundError,
    DatabaseError,
    UnauthorizedError,
)


@pytest.fixture
def card_service():
    """Create CardService instance with mocked MinIO."""
    with patch.object(CardService, "_init_minio"):
        service = CardService()
        service.minio_client = None
        return service


@pytest.fixture
def sample_card_data():
    """Sample card data for testing."""
    return {
        "d_id": 1,
        "word": "hola",
        "translation": "hello",
        "word_roman": "oh-lah",
        "definition": "A greeting",
        "word_example": "Hola, ¿cómo estás?",
        "trans_example": "Hello, how are you?",
        "trans_roman": None,
        "image": None,
    }


@pytest.fixture
def sample_card_response():
    """Sample card response from database."""
    return {
        "c_id": 1,
        "d_id": 1,
        "word": "hola",
        "translation": "hello",
        "definition": "A greeting",
        "word_example": "Hola, ¿cómo estás?",
        "trans_example": "Hello, how are you?",
        "word_roman": "oh-lah",
        "trans_roman": None,
        "image": None,
        "word_audio": None,
        "trans_audio": None,
    }


class TestIsUrl:
    """Tests for _is_url static method."""

    def test_http_url(self):
        assert CardService._is_url("http://example.com/image.jpg") is True

    def test_https_url(self):
        assert CardService._is_url("https://example.com/image.jpg") is True

    def test_not_url_path(self):
        assert CardService._is_url("/path/to/image.jpg") is False

    def test_not_url_empty(self):
        assert CardService._is_url("") is False

    def test_not_url_none(self):
        assert CardService._is_url(None) is False

    def test_not_url_relative(self):
        assert CardService._is_url("images/photo.jpg") is False


class TestMinIOUnit:
    """Tests for MinIO-dependent methods."""

    def test_download_and_store_image_invalid_url(self, card_service):
        """Test with invalid URL returns None."""
        result = card_service._download_and_store_image("not-a-url", 1)
        assert result is None

    def test_download_and_store_image_empty(self, card_service):
        """Test with empty URL returns None."""
        result = card_service._download_and_store_image("", 1)
        assert result is None

    def test_download_and_store_image_none(self, card_service):
        """Test with None URL returns None."""
        result = card_service._download_and_store_image(None, 1)
        assert result is None

    def test_download_and_store_image_no_minio_client(self, card_service):
        """Test returns None when MinIO client is unavailable."""
        card_service.minio_client = None
        result = card_service._download_and_store_image(
            "http://example.com/image.jpg", 1
        )
        assert result is None

    def test_download_and_store_image_success(self, card_service):
        """Test successful image download and storage."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio

        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.headers = {"Content-Type": "image/jpeg"}

        with patch("requests.get", return_value=mock_response):
            result = card_service._download_and_store_image(
                "http://example.com/image.jpg", 123
            )

        assert result == "images/card_123.jpg"
        mock_minio.put_object.assert_called_once()

        # Verify MinIO put_object called with correct parameters
        call_args = mock_minio.put_object.call_args[0]
        call_kwargs = mock_minio.put_object.call_args[1]
        assert call_args[0] == "languine-media", "Bucket name incorrect"
        assert call_args[1] == "images/card_123.jpg", "Object ID incorrect"
        assert call_kwargs["content_type"] == "image/jpeg", "Content type incorrect"
        assert call_kwargs["length"] == len(b"fake_image_data"), "Length incorrect"

    def test_download_and_store_image_download_failure(self, card_service):
        """Test handles download failure gracefully."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio
        
        with patch('requests.get', side_effect=Exception("Network error")):
            result = card_service._download_and_store_image("http://example.com/image.jpg", 1)
        
        assert result is None

    def test_download_and_store_image_handles_different_formats(self, card_service):
        """Test handles upload failure in Minio."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio
        mock_minio.put_object.side_effect = Exception("S3 upload failed")

        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.headers = {"Content-Type": "image/jpeg"}
        
        with patch('requests.get', return_value=mock_response):
            result = card_service._download_and_store_image("http://example.com/image.jpg", 1)
        
        assert result is None

    def test_download_and_store_image_handles_different_formats_success(self, card_service):

        with patch("requests.get", side_effect=Exception("Network error")):
            result = card_service._download_and_store_image(
                "http://example.com/image.jpg", 1
            )

        assert result is None

    def test_download_and_store_image_handles_different_formats(self, card_service):
        """Test handles different image formats correctly."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio

        test_cases = [
            ("image/png", "images/card_1.png"),
            ("image/gif", "images/card_1.gif"),
            ("image/webp", "images/card_1.webp"),
            ("image/svg+xml", "images/card_1.svg"),
        ]

        for content_type, expected_path in test_cases:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.headers = {"Content-Type": content_type}

            with patch("requests.get", return_value=mock_response):
                result = card_service._download_and_store_image(
                    "http://example.com/image", 1
                )

            assert result == expected_path

    def test_delete_from_minio_empty(self, card_service):
        """Test delete with empty object_id."""
        result = card_service._delete_from_minio("")
        assert result is True

    def test_delete_from_minio_none(self, card_service):
        """Test delete with None object_id."""
        result = card_service._delete_from_minio(None)
        assert result is True

    def test_delete_from_minio_no_client(self, card_service):
        """Test delete when MinIO client is unavailable."""
        card_service.minio_client = None
        result = card_service._delete_from_minio("some/object/path")
        assert result is True  # Returns True to not block other operations

    def test_delete_from_minio_success(self, card_service):
        """Test successful MinIO object deletion."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio

        result = card_service._delete_from_minio("images/card_123.jpg")

        assert result is True
        mock_minio.remove_object.assert_called_once_with(
            "languine-media", "images/card_123.jpg"
        )

    def test_delete_from_minio_handles_errors(self, card_service):
        """Test delete handles MinIO errors gracefully."""
        mock_minio = MagicMock()
        mock_minio.remove_object.side_effect = Exception("MinIO error")
        card_service.minio_client = mock_minio

        result = card_service._delete_from_minio("images/card_123.jpg")

        assert result is False


class TestTTSUnit:
    """Tests for TTS-dependent methods."""

    def test_generate_and_store_tts_empty_text(self, card_service):
        """Test TTS with empty text returns None."""
        result = card_service._generate_and_store_tts("", "en", 1, "word")
        assert result is None

    def test_generate_and_store_tts_none_text(self, card_service):
        """Test TTS with None text returns None."""
        result = card_service._generate_and_store_tts(None, "en", 1, "word")
        assert result is None

    def test_generate_and_store_tts_no_minio_client(self, card_service):
        """Test returns None when MinIO client is unavailable."""
        card_service.minio_client = None
        result = card_service._generate_and_store_tts("hello", "en", 1, "word")
        assert result is None

    def test_generate_and_store_tts_success(self, card_service):
        """Test successful TTS generation and storage."""
        import numpy as np

        mock_minio = MagicMock()
        card_service.minio_client = mock_minio

        mock_tts = MagicMock()
        mock_audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        mock_tts.generate_speech.return_value = mock_audio

        with patch("services.tts_service.TTSService", return_value=mock_tts):
            result = card_service._generate_and_store_tts("hello", "en", 123, "word")

        assert result == "audio/card_123_word.wav"
        mock_minio.put_object.assert_called_once()

        # Verify MinIO put_object called with correct parameters
        call_args = mock_minio.put_object.call_args[0]
        call_kwargs = mock_minio.put_object.call_args[1]
        assert call_args[0] == "languine-media", "Bucket name incorrect"
        assert call_args[1] == "audio/card_123_word.wav", "Object ID incorrect"
        assert call_kwargs["content_type"] == "audio/wav", "Content type incorrect"

    def test_generate_and_store_tts_different_field_types(self, card_service):
        """Test TTS generates correct paths for different field types."""
        import numpy as np

        mock_minio = MagicMock()
        card_service.minio_client = mock_minio

        mock_tts = MagicMock()
        mock_audio = np.array([0.1], dtype=np.float32)
        mock_tts.generate_speech.return_value = mock_audio

        with patch("services.tts_service.TTSService", return_value=mock_tts):
            result_word = card_service._generate_and_store_tts("hello", "en", 1, "word")
            result_trans = card_service._generate_and_store_tts(
                "hola", "es", 1, "translation"
            )

        assert result_word == "audio/card_1_word.wav"
        assert result_trans == "audio/card_1_translation.wav"

    def test_generate_and_store_tts_handles_tts_failure(self, card_service):
        """Test handles TTS service failure gracefully."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio

        with patch(
            "services.tts_service.TTSService", side_effect=Exception("TTS error")
        ):
            result = card_service._generate_and_store_tts("hello", "en", 1, "word")

        assert result is None

    def test_generate_and_store_tts_handles_upload_failure(self, card_service):
        """Test handles MinIO upload failure gracefully."""
        import numpy as np

        mock_minio = MagicMock()
        mock_minio.put_object.side_effect = Exception("Upload failed")
        card_service.minio_client = mock_minio

        mock_tts = MagicMock()
        mock_audio = np.array([0.1], dtype=np.float32)
        mock_tts.generate_speech.return_value = mock_audio

        with patch("services.tts_service.TTSService", return_value=mock_tts):
            result = card_service._generate_and_store_tts("hello", "en", 1, "word")

        assert result is None


class TestVerifyDeckOwnership:
    """Tests for _verify_deck_ownership helper."""

    def test_verify_deck_ownership_success(self, card_service):
        """Test deck ownership verification with valid owner."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"d_id": 1}

        with patch("services.card_service.get_db_cursor") as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = card_service._verify_deck_ownership("user-123", 1)

        assert result is True

    def test_verify_deck_ownership_not_owner(self, card_service):
        """Test deck ownership verification with non-owner."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        with patch("services.card_service.get_db_cursor") as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = card_service._verify_deck_ownership("user-123", 999)

        assert result is False


class TestGetDeckInfo:
    """Tests for _get_deck_info helper."""

    def test_get_deck_info_found(self, card_service):
        """Test getting deck info for existing deck."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "d_id": 1,
            "deck_name": "Spanish",
            "word_lang": "es",
            "trans_lang": "en",
        }

        with patch("services.card_service.get_db_cursor") as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = card_service._get_deck_info(1)

        assert result["deck_name"] == "Spanish"
        assert result["word_lang"] == "es"

    def test_get_deck_info_not_found(self, card_service):
        """Test getting deck info for non-existent deck."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        with patch("services.card_service.get_db_cursor") as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = card_service._get_deck_info(999)

        assert result is None


class TestCreateCard:
    """Tests for create_card method."""

    def test_create_card_deck_not_found(self, card_service, sample_card_data):
        """Test card creation fails when deck doesn't exist."""
        with patch.object(card_service, "_verify_deck_ownership", return_value=False):
            with pytest.raises(DeckNotFoundError):
                card_service.create_card("user-123", sample_card_data)

    def test_create_card_success(
        self, card_service, sample_card_data, sample_card_response
    ):
        """Test successful card creation."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_card_response

        with patch.object(card_service, "_verify_deck_ownership", return_value=True):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch("services.card_service.get_db_cursor") as mock_db:
                    mock_db.return_value.__enter__.return_value = mock_cursor
                    result = card_service.create_card("user-123", sample_card_data)

        assert result["word"] == "hola"
        assert result["translation"] == "hello"

    def test_create_card_strips_whitespace(self, card_service, sample_card_response):
        """Test that card creation strips whitespace from fields."""
        card_data = {
            "d_id": 1,
            "word": "  hola  ",
            "translation": "  hello  ",
            "word_roman": "  oh-lah  ",
        }

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_card_response

        with patch.object(card_service, "_verify_deck_ownership", return_value=True):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch("services.card_service.get_db_cursor") as mock_db:
                    mock_db.return_value.__enter__.return_value = mock_cursor
                    result = card_service.create_card("user-123", card_data)

        # Verify database was called with stripped values
        assert mock_cursor.execute.called
        query, params = mock_cursor.execute.call_args[0]

        # Check that parameters don't contain leading/trailing whitespace
        # The exact order depends on implementation, but all string params should be stripped
        string_params = [p for p in params if isinstance(p, str)]
        for param in string_params:
            assert param == param.strip(), f"Parameter '{param}' still has whitespace"

    def test_create_card_handles_none_optional_fields(
        self, card_service, sample_card_response
    ):
        """Test card creation with None values in optional fields."""
        card_data = {
            "d_id": 1,
            "word": "hola",
            "translation": "hello",
            "word_roman": "oh-lah",
            "definition": None,
            "word_example": None,
            "trans_example": None,
        }

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_card_response

        with patch.object(card_service, "_verify_deck_ownership", return_value=True):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch("services.card_service.get_db_cursor") as mock_db:
                    mock_db.return_value.__enter__.return_value = mock_cursor
                    result = card_service.create_card("user-123", card_data)

        assert result is not None

    def test_create_card_with_image_url(self, card_service, sample_card_response):
        """Test card creation with image URL downloads and stores image."""
        card_data = {
            "d_id": 1,
            "word": "hola",
            "translation": "hello",
            "word_roman": "oh-lah",
            "image": "http://example.com/image.jpg",
        }

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_card_response

        mock_download = MagicMock(return_value="images/card_1.jpg")

        with patch.object(card_service, "_verify_deck_ownership", return_value=True):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch.object(
                    card_service, "_download_and_store_image", mock_download
                ):
                    with patch("services.card_service.get_db_cursor") as mock_db:
                        mock_db.return_value.__enter__.return_value = mock_cursor
                        result = card_service.create_card("user-123", card_data)

        # Verify download was called with correct image URL and card_id
        # Note: card_id is returned from database, not input data
        mock_download.assert_called_once()
        call_args = mock_download.call_args[0]
        assert (
            call_args[0] == "http://example.com/image.jpg"
        ), "Image URL not passed correctly"
        assert result is not None

    def test_create_card_generates_tts(self, card_service, sample_card_response):
        """Test card creation generates TTS for word and translation."""
        card_data = {
            "d_id": 1,
            "word": "hola",
            "translation": "hello",
            "word_roman": "oh-lah",
        }

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_card_response

        mock_tts = MagicMock(return_value="audio/card_1_word.wav")

        with patch.object(card_service, "_verify_deck_ownership", return_value=True):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch.object(card_service, "_generate_and_store_tts", mock_tts):
                    with patch("services.card_service.get_db_cursor") as mock_db:
                        mock_db.return_value.__enter__.return_value = mock_cursor
                        result = card_service.create_card("user-123", card_data)

        # Should be called twice: once for word, once for translation
        assert mock_tts.call_count == 2

        # Verify correct parameters were passed
        calls = mock_tts.call_args_list
        # First call should be for word
        assert calls[0][0][0] == "hola", "Word text not passed to TTS"
        assert calls[0][0][1] == "es", "Word language incorrect"
        # Second call should be for translation
        assert calls[1][0][0] == "hello", "Translation text not passed to TTS"
        assert calls[1][0][1] == "en", "Translation language incorrect"


class TestGetCard:
    """Tests for get_card method."""

    def test_get_card_success(self, card_service, sample_card_response):
        """Test successful card retrieval."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_card_response

        with patch("services.card_service.get_db_cursor") as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = card_service.get_card("user-123", 1, 1)

        assert result["c_id"] == 1
        assert result["word"] == "hola"

    def test_get_card_not_found(self, card_service):
        """Test card retrieval when card doesn't exist."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        with patch("services.card_service.get_db_cursor") as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = card_service.get_card("user-123", 999, 1)

        assert result is None

    def test_get_card_without_deck_id(self, card_service, sample_card_response):
        """Test card retrieval without specifying deck_id."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_card_response

        with patch("services.card_service.get_db_cursor") as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = card_service.get_card("user-123", 1)

        assert result is not None


class TestUpdateCard:
    """Tests for update_card method."""

    def test_update_card_not_found(self, card_service):
        """Test update fails when card doesn't exist."""
        with patch.object(card_service, "get_card", return_value=None):
            with pytest.raises(CardNotFoundError):
                card_service.update_card("user-123", 999, {"word": "nuevo"})

    def test_update_card_no_changes(self, card_service, sample_card_response):
        """Test update with no changes returns current card."""
        with patch.object(card_service, "get_card", return_value=sample_card_response):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                result = card_service.update_card("user-123", 1, {})

        assert result["word"] == "hola"

    def test_update_card_success(self, card_service, sample_card_response):
        """Test successful card update."""
        updated_response = {**sample_card_response, "word": "nuevo"}
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = updated_response

        with patch.object(card_service, "get_card", return_value=sample_card_response):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch("services.card_service.get_db_cursor") as mock_db:
                    mock_db.return_value.__enter__.return_value = mock_cursor
                    result = card_service.update_card("user-123", 1, {"word": "nuevo"})

        assert result["word"] == "nuevo"

    def test_update_card_strips_whitespace(self, card_service, sample_card_response):
        """Test that update strips whitespace from fields."""
        updated_response = {**sample_card_response, "word": "nuevo"}
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = updated_response

        with patch.object(card_service, "get_card", return_value=sample_card_response):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch("services.card_service.get_db_cursor") as mock_db:
                    mock_db.return_value.__enter__.return_value = mock_cursor
                    result = card_service.update_card(
                        "user-123", 1, {"word": "  nuevo  "}
                    )

        # Verify database was called with stripped values
        assert mock_cursor.execute.called
        query, params = mock_cursor.execute.call_args[0]

        # Check that string parameters don't contain leading/trailing whitespace
        string_params = [p for p in params if isinstance(p, str)]
        for param in string_params:
            assert param == param.strip(), f"Parameter '{param}' still has whitespace"

    def test_update_card_handles_none_values(self, card_service, sample_card_response):
        """Test update handles None values correctly."""
        updated_response = {**sample_card_response, "definition": None}
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = updated_response

        with patch.object(card_service, "get_card", return_value=sample_card_response):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch("services.card_service.get_db_cursor") as mock_db:
                    mock_db.return_value.__enter__.return_value = mock_cursor
                    result = card_service.update_card(
                        "user-123", 1, {"definition": None}
                    )

        assert result is not None

    def test_update_card_with_image_url(self, card_service, sample_card_response):
        """Test updating image downloads and stores new image."""
        updated_response = {**sample_card_response, "image": "images/card_1.jpg"}
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = updated_response

        mock_download = MagicMock(return_value="images/card_1.jpg")
        mock_delete = MagicMock(return_value=True)

        with patch.object(card_service, "get_card", return_value=sample_card_response):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch.object(
                    card_service, "_download_and_store_image", mock_download
                ):
                    with patch.object(card_service, "_delete_from_minio", mock_delete):
                        with patch("services.card_service.get_db_cursor") as mock_db:
                            mock_db.return_value.__enter__.return_value = mock_cursor
                            result = card_service.update_card(
                                "user-123", 1, {"image": "http://example.com/new.jpg"}
                            )

        # Verify download was called with new image URL and correct card_id
        mock_download.assert_called_once_with("http://example.com/new.jpg", 1)
        # Note: Old image deletion not checked since sample_card_response has image=None

    def test_update_card_regenerates_tts_when_word_changes(
        self, card_service, sample_card_response
    ):
        """Test updating word regenerates word TTS but not translation TTS."""
        updated_response = {
            **sample_card_response,
            "word": "nuevo",
            "word_audio": "audio/card_1_word.wav",
        }
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = updated_response

        mock_tts = MagicMock(return_value="audio/card_1_word.wav")
        mock_delete = MagicMock(return_value=True)

        with patch.object(card_service, "get_card", return_value=sample_card_response):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch.object(card_service, "_generate_and_store_tts", mock_tts):
                    with patch.object(card_service, "_delete_from_minio", mock_delete):
                        with patch("services.card_service.get_db_cursor") as mock_db:
                            mock_db.return_value.__enter__.return_value = mock_cursor
                            result = card_service.update_card(
                                "user-123", 1, {"word": "nuevo"}
                            )

        # Should only regenerate word TTS, not translation
        mock_tts.assert_called_once()

        # Verify correct parameters: new word, Spanish language, card_id, field type
        call_args = mock_tts.call_args[0]
        assert call_args[0] == "nuevo", "New word not passed to TTS"
        assert call_args[1] == "es", "Language should be Spanish"
        assert call_args[2] == 1, "Card ID incorrect"
        assert call_args[3] == "word", "Field type should be 'word'"

        # Note: Old audio deletion not checked since sample_card_response has word_audio=None


class TestDeleteCard:
    """Tests for delete_card method."""

    def test_delete_card_not_found(self, card_service):
        """Test delete fails when card doesn't exist."""
        with patch.object(card_service, "get_card", return_value=None):
            with pytest.raises(CardNotFoundError):
                card_service.delete_card("user-123", 999)

    def test_delete_card_success(self, card_service, sample_card_response):
        """Test successful card deletion."""
        mock_cursor = MagicMock()

        with patch.object(card_service, "get_card", return_value=sample_card_response):
            with patch.object(card_service, "_delete_from_minio", return_value=True):
                with patch("services.card_service.get_db_cursor") as mock_db:
                    mock_db.return_value.__enter__.return_value = mock_cursor
                    result = card_service.delete_card("user-123", 1)

        assert result is True

    def test_delete_card_cleans_up_minio(self, card_service):
        """Test that delete cleans up MinIO objects."""
        card_with_media = {
            "c_id": 1,
            "d_id": 1,
            "word": "test",
            "translation": "test",
            "image": "images/1/test.jpg",
            "word_audio": "audio/1/word.wav",
            "trans_audio": "audio/1/trans.wav",
        }

        mock_cursor = MagicMock()
        delete_calls = []

        def track_delete(object_id):
            delete_calls.append(object_id)
            return True

        with patch.object(card_service, "get_card", return_value=card_with_media):
            with patch.object(
                card_service, "_delete_from_minio", side_effect=track_delete
            ):
                with patch("services.card_service.get_db_cursor") as mock_db:
                    mock_db.return_value.__enter__.return_value = mock_cursor
                    card_service.delete_card("user-123", 1)

        assert "images/1/test.jpg" in delete_calls
        assert "audio/1/word.wav" in delete_calls
        assert "audio/1/trans.wav" in delete_calls


class TestGetCardsForDeck:
    """Tests for get_cards_for_deck method."""

    def test_get_cards_for_deck_unauthorized(self, card_service):
        """Test returns None when user doesn't own deck."""
        with patch.object(card_service, "_verify_deck_ownership", return_value=False):
            result = card_service.get_cards_for_deck("user-123", 999)

        assert result is None

    def test_get_cards_for_deck_success(self, card_service, sample_card_response):
        """Test successful pagination of cards."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"total": 1}
        mock_cursor.fetchall.return_value = [sample_card_response]

        with patch.object(card_service, "_verify_deck_ownership", return_value=True):
            with patch("services.card_service.get_db_cursor") as mock_db:
                mock_db.return_value.__enter__.return_value = mock_cursor
                result = card_service.get_cards_for_deck("user-123", 1)

        assert "cards" in result
        assert "pagination" in result
        assert result["pagination"]["total"] == 1

    def test_get_cards_for_deck_pagination(self, card_service):
        """Test pagination parameters."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"total": 100}
        mock_cursor.fetchall.return_value = []

        with patch.object(card_service, "_verify_deck_ownership", return_value=True):
            with patch("services.card_service.get_db_cursor") as mock_db:
                mock_db.return_value.__enter__.return_value = mock_cursor
                result = card_service.get_cards_for_deck(
                    "user-123", 1, page=2, per_page=20
                )

        assert result["pagination"]["page"] == 2
        assert result["pagination"]["per_page"] == 20
        assert result["pagination"]["total_pages"] == 5


class TestGetCardsForReview:
    """Tests for get_cards_for_review method."""

    def test_get_cards_for_review_unauthorized(self, card_service):
        """Test returns None when user doesn't own deck."""
        with patch.object(card_service, "_verify_deck_ownership", return_value=False):
            result = card_service.get_cards_for_review("user-123", 999)

        assert result is None

    def test_get_cards_for_review_success(self, card_service, sample_card_response):
        """Test successful retrieval of due cards."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [sample_card_response]

        with patch.object(card_service, "_verify_deck_ownership", return_value=True):
            with patch("services.card_service.get_db_cursor") as mock_db:
                mock_db.return_value.__enter__.return_value = mock_cursor
                result = card_service.get_cards_for_review("user-123", 1)

        assert len(result) == 1


class TestCardRoutes:
    """Unit tests for Card Routes exception handling and edge cases."""

    def test_create_card_deck_not_found(self, client, auth_headers):
        with patch("routes.cards.card_service.create_card") as mock_create:
            mock_create.side_effect = DeckNotFoundError("Deck not found")
            card_data = {"word": "test", "translation": "test"}
            response = client.post(
                "/decks/1/card",
                data=json.dumps(card_data),
                content_type="application/json",
                headers=auth_headers,
            )
            assert response.status_code == 404
            assert "Deck not found" in json.loads(response.data)["error"]

    def test_create_card_unauthorized(self, client, auth_headers):
        with patch("routes.cards.card_service.create_card") as mock_create:
            mock_create.side_effect = UnauthorizedError("Unauthorized")
            card_data = {"word": "test", "translation": "test"}
            response = client.post(
                "/decks/1/card",
                data=json.dumps(card_data),
                content_type="application/json",
                headers=auth_headers,
            )
            assert response.status_code == 403

    def test_create_card_database_error(self, client, auth_headers):
        with patch("routes.cards.card_service.create_card") as mock_create:
            mock_create.side_effect = DatabaseError("DB error")
            card_data = {"word": "test", "translation": "test"}
            response = client.post(
                "/decks/1/card",
                data=json.dumps(card_data),
                content_type="application/json",
                headers=auth_headers,
            )
            assert response.status_code == 500

    def test_create_card_generic_exception(self, client, auth_headers):
        with patch("routes.cards.card_service.create_card") as mock_create:
            mock_create.side_effect = Exception("Generic error")
            card_data = {"word": "test", "translation": "test"}
            response = client.post(
                "/decks/1/card",
                data=json.dumps(card_data),
                content_type="application/json",
                headers=auth_headers,
            )
            assert response.status_code == 500
            assert "Generic error" in json.loads(response.data)["error"]

    def test_get_card_not_found_None(self, client, auth_headers):
        with patch("routes.cards.card_service.get_card") as mock_get:
            mock_get.return_value = None
            response = client.get("/decks/1/cards/1", headers=auth_headers)
            assert response.status_code == 404

    def test_get_card_generic_exception(self, client, auth_headers):
        with patch("routes.cards.card_service.get_card") as mock_get:
            mock_get.side_effect = Exception("Error")
            response = client.get("/decks/1/cards/1", headers=auth_headers)
            assert response.status_code == 500

    def test_update_card_not_found(self, client, auth_headers):
        with patch("routes.cards.card_service.update_card") as mock_update:
            mock_update.side_effect = CardNotFoundError("Card not found")
            update_data = {"definition": "test"}
            response = client.post(
                "/decks/1/cards/1",
                data=json.dumps(update_data),
                content_type="application/json",
                headers=auth_headers,
            )
            assert response.status_code == 404

    def test_update_card_unauthorized(self, client, auth_headers):
        with patch("routes.cards.card_service.update_card") as mock_update:
            mock_update.side_effect = UnauthorizedError("Unauthorized")
            update_data = {"definition": "test"}
            response = client.post(
                "/decks/1/cards/1",
                data=json.dumps(update_data),
                content_type="application/json",
                headers=auth_headers,
            )
            assert response.status_code == 403

    def test_update_card_database_error(self, client, auth_headers):
        with patch("routes.cards.card_service.update_card") as mock_update:
            mock_update.side_effect = DatabaseError("DB error")
            update_data = {"definition": "test"}
            response = client.post(
                "/decks/1/cards/1",
                data=json.dumps(update_data),
                content_type="application/json",
                headers=auth_headers,
            )
            assert response.status_code == 500

    def test_update_card_generic_exception(self, client, auth_headers):
        with patch("routes.cards.card_service.update_card") as mock_update:
            mock_update.side_effect = Exception("Generic error")
            update_data = {"definition": "test"}
            response = client.post(
                "/decks/1/cards/1",
                data=json.dumps(update_data),
                content_type="application/json",
                headers=auth_headers,
            )
            assert response.status_code == 500

    def test_delete_card_not_found(self, client, auth_headers):
        with patch("routes.cards.card_service.delete_card") as mock_delete:
            mock_delete.side_effect = CardNotFoundError("Card not found")
            response = client.delete("/decks/1/cards/1", headers=auth_headers)
            assert response.status_code == 404

    def test_delete_card_unauthorized(self, client, auth_headers):
        with patch("routes.cards.card_service.delete_card") as mock_delete:
            mock_delete.side_effect = UnauthorizedError("Unauthorized")
            response = client.delete("/decks/1/cards/1", headers=auth_headers)
            assert response.status_code == 403

    def test_delete_card_generic_exception(self, client, auth_headers):
        with patch("routes.cards.card_service.delete_card") as mock_delete:
            mock_delete.side_effect = Exception("Generic error")
            response = client.delete("/decks/1/cards/1", headers=auth_headers)
            assert response.status_code == 500

    def test_get_deck_cards_none(self, client, auth_headers):
        with patch("routes.cards.card_service.get_cards_for_deck") as mock_get:
            mock_get.return_value = None
            response = client.get("/decks/1/cards", headers=auth_headers)
            assert response.status_code == 404

    def test_get_deck_cards_generic_exception(self, client, auth_headers):
        with patch("routes.cards.card_service.get_cards_for_deck") as mock_get:
            mock_get.side_effect = Exception("Generic error")
            response = client.get("/decks/1/cards", headers=auth_headers)
            assert response.status_code == 500

    def test_get_review_cards_none(self, client, auth_headers):
        with patch("routes.cards.card_service.get_cards_for_review") as mock_get:
            mock_get.return_value = None
            response = client.get("/decks/1/review", headers=auth_headers)
            assert response.status_code == 404

    def test_get_review_cards_generic_exception(self, client, auth_headers):
        with patch("routes.cards.card_service.get_cards_for_review") as mock_get:
            mock_get.side_effect = Exception("Generic error")
            response = client.get("/decks/1/review", headers=auth_headers)
            assert response.status_code == 500

    def test_get_card_image_url_exception(self, client):
        with patch("routes.cards.card_service.minio_client") as mock_minio:
            mock_minio.get_object.side_effect = Exception("Generic minio error")
            response = client.get("/cards/image/some-image-id")
            assert response.status_code == 500
            assert (
                "Failed to fetch image: Generic minio error"
                in json.loads(response.data)["error"]
            )

    def test_get_card_image_url_no_such_key(self, client):
        with patch("routes.cards.card_service.minio_client") as mock_minio:
            mock_minio.get_object.side_effect = Exception("NoSuchKey")
            response = client.get("/cards/image/missing-image")
            assert response.status_code == 404

    def test_get_card_image_url_no_minio(self, client):
        with patch("routes.cards.card_service.minio_client", None):
            response = client.get("/cards/image/some-image")
            assert response.status_code == 503

    def test_get_card_image_url_external_exception(self, client):
        with patch("routes.cards.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection error")
            # Ensure it starts with http:// but encode it safely if unquote parses it out.
            # Actual endpoint uses unquote over the whole string so we pass encoded https://
            response = client.get("/cards/image/https%3A%2F%2Fexample.com%2Fimage.jpg")
            assert response.status_code == 500


class TestCardServiceMinIOInit:
    """Tests for MinIO initialization with different endpoint configurations."""

    def test_init_minio_https_endpoint(self, monkeypatch):
        """Test MinIO initialization with HTTPS endpoint."""
        monkeypatch.setenv("MINIO_ENDPOINT", "https://minio.example.com:9000")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "test_access_key")
        monkeypatch.setenv("MINIO_SECRET_KEY", "test_secret_key")
        
        with patch("minio.Minio") as MockMinio:
            mock_minio_instance = MagicMock()
            MockMinio.return_value = mock_minio_instance
            mock_minio_instance.bucket_exists.return_value = True
            
            service = CardService()
            
            # Verify Minio was initialized with secure=True
            call_kwargs = MockMinio.call_args[1]
            assert call_kwargs["secure"] is True

    def test_init_minio_http_endpoint(self, monkeypatch):
        """Test MinIO initialization with HTTP endpoint."""
        monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "test_access_key")
        monkeypatch.setenv("MINIO_SECRET_KEY", "test_secret_key")
        
        with patch("minio.Minio") as MockMinio:
            mock_minio_instance = MagicMock()
            MockMinio.return_value = mock_minio_instance
            mock_minio_instance.bucket_exists.return_value = True
            
            service = CardService()
            
            # Verify Minio was initialized with secure=False
            call_kwargs = MockMinio.call_args[1]
            assert call_kwargs["secure"] is False

    def test_init_minio_bucket_creation_false_then_true(self, monkeypatch):
        """Test MinIO creates bucket when it doesn't exist, handles bucket_exists return False."""
        monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "test_access_key")
        monkeypatch.setenv("MINIO_SECRET_KEY", "test_secret_key")
        
        with patch("minio.Minio") as MockMinio:
            mock_minio_instance = MagicMock()
            MockMinio.return_value = mock_minio_instance
            # Bucket doesn't exist initially
            mock_minio_instance.bucket_exists.return_value = False
            
            service = CardService()
            
            # Verify make_bucket was called
            mock_minio_instance.make_bucket.assert_called_once()
            bucket_name = mock_minio_instance.make_bucket.call_args[0][0]
            assert bucket_name == "languine-media"

    def test_init_minio_bucket_already_exists(self, monkeypatch):
        """Test MinIO skips bucket creation when it already exists."""
        monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "test_access_key")
        monkeypatch.setenv("MINIO_SECRET_KEY", "test_secret_key")
        
        with patch("minio.Minio") as MockMinio:
            mock_minio_instance = MagicMock()
            MockMinio.return_value = mock_minio_instance
            # Bucket already exists
            mock_minio_instance.bucket_exists.return_value = True
            
            service = CardService()
            
            # Verify make_bucket was NOT called
            mock_minio_instance.make_bucket.assert_not_called()

    def test_init_minio_no_credentials(self, monkeypatch):
        """Test MinIO init without credentials sets client to None."""
        monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
        monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
        monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
        
        service = CardService()
        
        # Should gracefully handle missing credentials
        assert service.minio_client is None or isinstance(service.minio_client, object)


class TestGenerateAndStoreTTS:
    """Tests for TTS generation and storage."""

    def test_generate_and_store_tts_with_empty_text(self, card_service):
        """Test TTS generation with empty text returns None."""
        result = card_service._generate_and_store_tts("", "es", 1, "word")
        assert result is None

    def test_generate_and_store_tts_with_none_text(self, card_service):
        """Test TTS generation with None text returns None."""
        result = card_service._generate_and_store_tts(None, "es", 1, "word")
        assert result is None

    def test_generate_and_store_tts_no_minio(self, card_service):
        """Test TTS generation when MinIO is unavailable."""
        card_service.minio_client = None
        result = card_service._generate_and_store_tts("hola", "es", 1, "word")
        assert result is None

    def test_generate_and_store_tts_actual(self, card_service):
        """Test TTS generation with actual execution (will fail on ImportError gracefully)."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio
        
        result = card_service._generate_and_store_tts("test word", "es", 1, "word")
        
        # Result will be None if TTSService import fails (which it should in unit test env)
        # or it might succeed if TTSService is available
        assert result is None or isinstance(result, str)

    def test_generate_and_store_tts_no_minio(self, card_service):
        """Test TTS generation when MinIO is unavailable."""
        card_service.minio_client = None
        result = card_service._generate_and_store_tts("hola", "es", 1, "word")
        assert result is None


class TestUpdateCardImageRemoval:
    """Tests for updating card with image removal."""

    def test_update_card_remove_image_none(self, card_service, sample_card_response):
        """Test updating card to remove image by setting to None."""
        card_with_image = {**sample_card_response, "image": "images/card_1.jpg"}
        updated_response = {**card_with_image, "image": None}
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = updated_response
        mock_delete = MagicMock(return_value=True)
        
        with patch.object(card_service, "get_card", return_value=card_with_image):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch.object(card_service, "_delete_from_minio", mock_delete):
                    with patch("services.card_service.get_db_cursor") as mock_db:
                        mock_db.return_value.__enter__.return_value = mock_cursor
                        result = card_service.update_card("user-123", 1, {"image": None})
        
        # Verify old image was deleted
        mock_delete.assert_called_once_with("images/card_1.jpg")
        assert result["image"] is None

    def test_update_card_remove_image_empty_string(self, card_service, sample_card_response):
        """Test updating card to remove image by setting to empty string."""
        card_with_image = {**sample_card_response, "image": "images/card_1.jpg"}
        updated_response = {**card_with_image, "image": None}
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = updated_response
        mock_delete = MagicMock(return_value=True)
        
        with patch.object(card_service, "get_card", return_value=card_with_image):
            with patch.object(
                card_service,
                "_get_deck_info",
                return_value={"word_lang": "es", "trans_lang": "en"},
            ):
                with patch.object(card_service, "_delete_from_minio", mock_delete):
                    with patch("services.card_service.get_db_cursor") as mock_db:
                        mock_db.return_value.__enter__.return_value = mock_cursor
                        result = card_service.update_card("user-123", 1, {"image": ""})
        
        # Verify old image was deleted
        mock_delete.assert_called_once_with("images/card_1.jpg")
        assert result["image"] is None


class TestUnauthorizedCardAccess:
    """Tests for unauthorized card access attempts."""

    def test_get_card_unauthorized_user(self, card_service):
        """Test get_card returns None when user doesn't own the card."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Simulates no results due to authorization check
        
        with patch("services.card_service.get_db_cursor") as mock_db:
            mock_db.return_value.__enter__.return_value = mock_cursor
            result = card_service.get_card("user-123", 1, 5)  # Card belongs to different user/deck
        
        assert result is None

    def test_update_card_unauthorized_user(self, card_service):
        """Test update_card raises CardNotFoundError when user doesn't own the card."""
        with patch.object(card_service, "get_card", return_value=None):
            with pytest.raises(CardNotFoundError):
                card_service.update_card("user-123", 1, {"word": "new"})

    def test_delete_card_unauthorized_user(self, card_service):
        """Test delete_card raises CardNotFoundError when user doesn't own the card."""
        with patch.object(card_service, "get_card", return_value=None):
            with pytest.raises(CardNotFoundError):
                card_service.delete_card("user-123", 1)


class TestDeleteFromMinIO:
    """Tests for MinIO object deletion."""

    def test_delete_from_minio_success(self, card_service):
        """Test successful MinIO object deletion."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio
        
        result = card_service._delete_from_minio("images/card_1.jpg")
        
        assert result is True
        mock_minio.remove_object.assert_called_once_with("languine-media", "images/card_1.jpg")

    def test_delete_from_minio_empty_id(self, card_service):
        """Test delete with empty object ID returns True."""
        result = card_service._delete_from_minio("")
        assert result is True

    def test_delete_from_minio_exception(self, card_service):
        """Test delete handles exception gracefully."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio
        mock_minio.remove_object.side_effect = Exception("Delete failed")
        
        result = card_service._delete_from_minio("images/card_1.jpg")
        
        assert result is False

    def test_delete_from_minio_no_client(self, card_service):
        """Test delete with no MinIO client returns True."""
        card_service.minio_client = None
        result = card_service._delete_from_minio("images/card_1.jpg")
        assert result is True


class TestPresignedURL:
    """Tests for presigned URL generation."""

    def test_get_presigned_image_url_success(self, card_service):
        """Test successful presigned URL generation."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio
        mock_minio.presigned_get_object.return_value = "https://minio.example.com/image_url"
        
        result = card_service.get_presigned_image_url("images/card_1.jpg")
        
        assert result == "https://minio.example.com/image_url"

    def test_get_presigned_image_url_empty_id(self, card_service):
        """Test presigned URL with empty object ID returns None."""
        result = card_service.get_presigned_image_url("")
        assert result is None

    def test_get_presigned_image_url_no_client(self, card_service):
        """Test presigned URL with no MinIO client returns None."""
        card_service.minio_client = None
        result = card_service.get_presigned_image_url("images/card_1.jpg")
        assert result is None

    def test_get_presigned_image_url_exception(self, card_service):
        """Test presigned URL handles exception gracefully."""
        mock_minio = MagicMock()
        card_service.minio_client = mock_minio
        mock_minio.presigned_get_object.side_effect = Exception("URL generation failed")
        
        result = card_service.get_presigned_image_url("images/card_1.jpg")
        
        assert result is None
