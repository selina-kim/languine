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
import pytest
import json
import numpy as np
from io import BytesIO


def test_tts_post_success_with_speaker(client, monkeypatch):
    """Test successful TTS generation with explicit speaker."""
    # Mock audio data
    mock_audio = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    
    # Mock TTSService
    class MockTTSService:
        def generate_speech(self, text, language, model_name=None, speaker=None, speaker_wav=None):
            assert text == "Hello world"
            assert language == "en"
            assert speaker == "Claribel Dervla"
            return mock_audio
    
    # Replace the service
    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())
    
    response = client.post(
        "/tts",
        json={
            "text": "Hello world",
            "language": "en",
            "speaker": "Claribel Dervla"
        }
    )
    
    assert response.status_code == 200
    assert response.mimetype == "audio/wav"
    assert len(response.data) > 0


def test_tts_post_success_with_default_speaker(client, monkeypatch):
    """Test successful TTS generation using default speaker for language."""
    mock_audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    
    class MockTTSService:
        def generate_speech(self, text, language, model_name=None, speaker=None, speaker_wav=None):
            assert text == "안녕하세요"
            assert language == "ko"
            assert speaker == "Daisy Studious"  # Default for Korean
            return mock_audio
    
    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())
    
    response = client.post(
        "/tts",
        json={
            "text": "안녕하세요",
            "language": "ko"
        }
    )
    
    assert response.status_code == 200
    assert response.mimetype == "audio/wav"


def test_tts_post_success_korean_text(client, monkeypatch):
    """Test TTS with Korean Unicode text."""
    mock_audio = np.array([0.5, 0.6, 0.7], dtype=np.float32)
    
    class MockTTSService:
        def generate_speech(self, text, language, model_name=None, speaker=None, speaker_wav=None):
            return mock_audio
    
    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())
    
    response = client.post(
        "/tts",
        json={
            "text": "한국어 텍스트 테스트",
            "language": "ko",
            "speaker": "Daisy Studious"
        }
    )
    
    assert response.status_code == 200


def test_tts_post_success_japanese_text(client, monkeypatch):
    """Test TTS with Japanese Unicode text."""
    mock_audio = np.array([0.1, 0.2], dtype=np.float32)
    
    class MockTTSService:
        def generate_speech(self, text, language, model_name=None, speaker=None, speaker_wav=None):
            return mock_audio
    
    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())
    
    response = client.post(
        "/tts",
        json={
            "text": "こんにちは世界",
            "language": "ja"
        }
    )
    
    assert response.status_code == 200

def test_tts_post_missing_text(client):
    """Test error when text field is missing."""
    response = client.post(
        "/tts",
        json={
            "language": "en"
        }
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "text" in data["error"].lower()


def test_tts_post_missing_language(client):
    """Test error when language field is missing."""
    response = client.post(
        "/tts",
        json={
            "text": "Hello world"
        }
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "language" in data["error"].lower()


def test_tts_post_empty_text(client):
    """Test error when text is empty string."""
    response = client.post(
        "/tts",
        json={
            "text": "",
            "language": "en"
        }
    )
    
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
    response = client.post(
        "/tts",
        json={
            "text": "Hello",
            "language": "xyz"
        }
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "unsupported" in data["error"].lower()


def test_tts_post_empty_audio_generation(client, monkeypatch):
    """Test error when audio generation returns empty data."""
    class MockTTSService:
        def generate_speech(self, text, language, model_name=None, speaker=None, speaker_wav=None):
            return np.array([])  # Empty audio
    
    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())
    
    response = client.post(
        "/tts",
        json={
            "text": "Test",
            "language": "en"
        }
    )
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert "failed" in data["error"].lower()


def test_tts_post_service_exception(client, monkeypatch):
    """Test error handling when TTS service raises exception."""
    class MockTTSService:
        def generate_speech(self, text, language, model_name=None, speaker=None, speaker_wav=None):
            raise Exception("TTS service failed")
    
    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())
    
    response = client.post(
        "/tts",
        json={
            "text": "Test",
            "language": "en"
        }
    )
    
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


def test_tts_get_models_success(client, monkeypatch):
    """Test successful retrieval of available models."""
    class MockTTSService:
        def list_available_models(self):
            return ["model1", "model2", "model3"]
    
    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())
    
    response = client.get("/tts/models")
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "models" in data
    assert len(data["models"]) == 3


def test_tts_get_models_exception(client, monkeypatch):
    """Test error handling when model retrieval fails."""
    class MockTTSService:
        def list_available_models(self):
            raise Exception("Failed to list models")
    
    monkeypatch.setattr("routes.tts.tts_service", MockTTSService())
    
    response = client.get("/tts/models")
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data


def test_tts_default_speaker_fallback(client, monkeypatch):
    """Test fallback to default speaker when language has no default."""
    mock_audio = np.array([0.1, 0.2], dtype=np.float32)
    
    class MockTTSService:
        def generate_speech(self, text, language, model_name=None, speaker=None, speaker_wav=None):
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
        response = client.post(
            "/tts",
            json={
                "text": "Test",
                "language": "test"
            }
        )
        
        assert response.status_code == 200
    finally:
        # Restore
        tts.DEFAULT_SPEAKERS.clear()
        tts.DEFAULT_SPEAKERS.update(original_defaults)
        del tts.SUPPORTED_LANGUAGES["test"]
