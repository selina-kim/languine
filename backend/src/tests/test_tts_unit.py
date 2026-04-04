"""Unit tests for TTS API.

These tests mock the TTS service responses to test the application logic
without making real TTS calls.

Test coverage:
- Success cases (with and without speaker, default speaker selection)
- Missing required parameters (text, language)
- Unsupported language validation
- Audio generation and WAV file response
- Unicode text handling (Korean, Japanese, special characters)
- Empty audio handling
- Exception handling

Run this test file:
    docker compose exec backend pytest src/tests/test_tts_unit.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_tts_unit.py --cov=services.tts_service
"""
import json
import numpy as np
from unittest.mock import patch, MagicMock


def test_tts_post_success_with_speaker(client, monkeypatch):
    """Test successful TTS generation with explicit speaker."""
    # Mock audio data
    mock_audio = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)

    # Mock TTSService
    class MockTTSService:
        def generate_speech(self, text, language, speaker=None):
            assert text == "Hello world"
            assert language == "en"
            assert speaker == "Claribel Dervla"
            return mock_audio

    # Replace the service
    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())

    response = client.post(
        "/tts",
        json={"text": "Hello world", "language": "en", "speaker": "Claribel Dervla"},
    )

    assert response.status_code == 200
    assert response.mimetype == "audio/wav"
    assert len(response.data) > 0


def test_tts_post_success_with_default_speaker(client, monkeypatch):
    """Test successful TTS generation using default speaker for language."""
    mock_audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    class MockTTSService:
        def generate_speech(self, text, language, speaker=None):
            assert text == "안녕하세요"
            assert language == "ko"
            assert speaker == "Daisy Studious"  # Default for Korean
            return mock_audio

    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())

    response = client.post("/tts", json={"text": "안녕하세요", "language": "ko"})

    assert response.status_code == 200
    assert response.mimetype == "audio/wav"


def test_tts_post_success_korean_text(client, monkeypatch):
    """Test TTS with Korean Unicode text."""
    mock_audio = np.array([0.5, 0.6, 0.7], dtype=np.float32)

    class MockTTSService:
        def generate_speech(self, text, language, speaker=None):
            return mock_audio

    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())

    response = client.post(
        "/tts",
        json={
            "text": "한국어 텍스트 테스트",
            "language": "ko",
            "speaker": "Daisy Studious",
        },
    )

    assert response.status_code == 200


def test_tts_post_success_japanese_text(client, monkeypatch):
    """Test TTS with Japanese Unicode text."""
    mock_audio = np.array([0.1, 0.2], dtype=np.float32)

    class MockTTSService:
        def generate_speech(self, text, language, speaker=None):
            return mock_audio

    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())

    response = client.post("/tts", json={"text": "こんにちは世界", "language": "ja"})

    assert response.status_code == 200


def test_tts_post_missing_text(client):
    """Test error when text field is missing."""
    response = client.post("/tts", json={"language": "en"})

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "text" in data["error"].lower()


def test_tts_post_missing_language(client):
    """Test error when language field is missing."""
    response = client.post("/tts", json={"text": "Hello world"})

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "language" in data["error"].lower()


def test_tts_post_empty_text(client):
    """Test error when text is empty string."""
    response = client.post("/tts", json={"text": "", "language": "en"})

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_tts_post_no_json_data(client):
    """Test error when no JSON data is provided."""
    response = client.post("/tts", content_type="application/json")

    # Can be 400 or 500 depending on how Flask handles missing JSON
    assert response.status_code in [400, 500]
    data = json.loads(response.data)
    assert "error" in data


def test_tts_post_unsupported_language(client):
    """Test error when unsupported language is provided."""
    response = client.post("/tts", json={"text": "Hello", "language": "xyz"})

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "unsupported" in data["error"].lower()


def test_tts_post_empty_audio_generation(client, monkeypatch):
    """Test error when audio generation returns empty data."""

    class MockTTSService:
        def generate_speech(self, text, language, speaker=None):
            return np.array([])  # Empty audio

    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())

    response = client.post("/tts", json={"text": "Test", "language": "en"})

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert "failed" in data["error"].lower()


def test_tts_post_service_exception(client, monkeypatch):
    """Test error handling when TTS service raises exception."""

    class MockTTSService:
        def generate_speech(self, text, language, speaker=None, speaker_wav=None):
            raise Exception("TTS service failed")

    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())

    response = client.post("/tts", json={"text": "Test", "language": "en"})

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data


def test_tts_get_speakers_success(client, monkeypatch):
    """Test successful retrieval of speaker list."""

    class MockTTSService:
        def get_speakers(self, model_name=None):
            return ["Speaker 1", "Speaker 2", "Speaker 3"]

    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())

    response = client.get("/tts/speakers")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "speakers" in data
    assert len(data["speakers"]) == 3
    assert "Speaker 1" in data["speakers"]


def test_tts_get_speakers_exception(client, monkeypatch):
    """Test error handling when speaker retrieval fails."""

    class MockTTSService:
        def get_speakers(self, model_name=None):
            raise Exception("Failed to get speakers")

    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())

    response = client.get("/tts/speakers")

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data


def test_tts_get_languages_success(client):
    """Test successful retrieval of supported languages."""
    response = client.get("/tts/languages")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "languages" in data
    assert "en" in data["languages"]
    assert "ko" in data["languages"]
    assert "ja" in data["languages"]
    assert data["languages"]["en"] == "English"


def test_tts_default_speaker_fallback(client, monkeypatch):
    """Test fallback to default speaker when language has no default."""
    mock_audio = np.array([0.1, 0.2], dtype=np.float32)

    class MockTTSService:
        def generate_speech(self, text, language, speaker=None, speaker_wav=None):
            # Should use fallback speaker
            assert speaker == "Claribel Dervla"
            return mock_audio

    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())

    # Mock an unsupported language code temporarily by removing from dict
    from routes import tts

    original_defaults = tts.DEFAULT_SPEAKERS.copy()

    # Add a supported language without default speaker
    tts.SUPPORTED_LANGUAGES["test"] = "Test Language"

    try:
        response = client.post("/tts", json={"text": "Test", "language": "test"})

        assert response.status_code == 200
    finally:
        # Restore
        tts.DEFAULT_SPEAKERS.clear()
        tts.DEFAULT_SPEAKERS.update(original_defaults)
        del tts.SUPPORTED_LANGUAGES["test"]


class TestTTSServiceClass:
    """Unit tests for TTSService class."""

    def test_tts_service_init(self):
        """Test TTSService initialization."""
        from services.tts_service import TTSService

        with patch("services.tts_service.torch") as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            service = TTSService()
            assert service.device == "cuda"

            mock_torch.cuda.is_available.return_value = False
            service = TTSService()
            assert service.device == "cpu"

    def test_tts_service_get_model(self):
        """Test _get_model caching."""
        from services.tts_service import TTSService

        service = TTSService()
        with patch("services.tts_service.TTS") as mock_tts_class:
            mock_model = MagicMock()
            mock_tts_class.return_value.to.return_value = mock_model

            # First call should instantiate
            model1 = service._get_model("test_model")
            assert model1 == mock_model
            mock_tts_class.assert_called_with("test_model")

            # Second call should use cache
            mock_tts_class.reset_mock()
            model2 = service._get_model("test_model")
            assert model2 == mock_model
            mock_tts_class.assert_not_called()

    def test_tts_service_generate_speech(self):
        """Test generate_speech variations."""
        from services.tts_service import TTSService

        service = TTSService()
        mock_model = MagicMock()
        mock_model.speakers = ["Speaker 1", "Speaker 2"]
        mock_model.tts.return_value = [0.1, 0.2]
        service.models[service.default_model] = mock_model

        # Text without speaker uses first speaker
        res1 = service.generate_speech("hello", "en")
        assert isinstance(res1, np.ndarray)
        mock_model.tts.assert_called_with(
            text="hello", speaker="Speaker 1", language="en"
        )

        # Text with specific speaker
        res2 = service.generate_speech("hello", "en", "Speaker 2")
        mock_model.tts.assert_called_with(
            text="hello", speaker="Speaker 2", language="en"
        )

    def test_tts_service_generate_speech_to_file(self):
        """Test generate_speech_to_file variations."""
        from services.tts_service import TTSService

        service = TTSService()
        mock_model = MagicMock()
        mock_model.speakers = ["Speaker 1", "Speaker 2"]
        service.models[service.default_model] = mock_model

        # File generation without specifying speaker
        service.generate_speech_to_file("hello", "test.wav", "en")
        mock_model.tts_to_file.assert_called_with(
            text="hello", speaker="Speaker 1", language="en", file_path="test.wav"
        )

        # File generation with specific speaker
        service.generate_speech_to_file("hello", "test.wav", "en", "Speaker 2")
        mock_model.tts_to_file.assert_called_with(
            text="hello", speaker="Speaker 2", language="en", file_path="test.wav"
        )

    def test_tts_service_get_speakers(self):
        """Test get_speakers works or handles missing."""
        from services.tts_service import TTSService

        service = TTSService()
        mock_model = MagicMock()
        mock_model.speakers = ["Spk1", "Spk2"]
        service.models[service.default_model] = mock_model

        # Has speakers
        assert service.get_speakers() == ["Spk1", "Spk2"]

        # Has no speakers
        mock_model.speakers = None
        assert service.get_speakers() == []
