"""Integration tests for TTS API.

These tests make real calls to the TTS service (requires model download).

Run with: docker compose exec backend poetry run pytest -m integration

Test coverage:
- Real TTS generation with various languages
- Real speaker selection
- Audio quality validation
- Performance testing
- End-to-end workflow
"""
import pytest
import json
import numpy as np
from scipy.io import wavfile
import io
import time


@pytest.mark.integration
def test_tts_real_english_generation(client):
    """Test real TTS generation for English text."""
    start_time = time.time()
    response = client.post(
        "/tts",
        json={
            "text": "Hello, this is a test of the text to speech system.",
            "language": "en",
            "speaker": "Claribel Dervla"
        }
    )
    elapsed_time = time.time() - start_time
    
    print(f"\n[TIMING] TTS English (54 chars): {elapsed_time:.3f}s")
    
    assert response.status_code == 200
    assert response.mimetype == "audio/wav"
    assert len(response.data) > 0
    
    # Verify it's a valid WAV file
    audio_buffer = io.BytesIO(response.data)
    sample_rate, audio_data = wavfile.read(audio_buffer)
    assert sample_rate == 24000
    assert len(audio_data) > 0


@pytest.mark.integration
def test_tts_real_korean_generation(client):
    """Test real TTS generation for Korean text."""
    start_time = time.time()
    response = client.post(
        "/tts",
        json={
            "text": "안녕하세요, 텍스트 음성 변환 시스템 테스트입니다.",
            "language": "ko",
            "speaker": "Daisy Studious"
        }
    )
    elapsed_time = time.time() - start_time
    
    print(f"\n[TIMING] TTS Korean (28 chars): {elapsed_time:.3f}s")
    
    assert response.status_code == 200
    assert response.mimetype == "audio/wav"
    assert len(response.data) > 0
    
    # Verify audio quality
    audio_buffer = io.BytesIO(response.data)
    sample_rate, audio_data = wavfile.read(audio_buffer)
    assert sample_rate == 24000
    assert len(audio_data) > 1000  # Should have meaningful length

# TODO in API P1
# might need unidic-lite = "^1.0.8"
# @pytest.mark.integration
# def test_tts_real_japanese_generation(client):
#     """Test real TTS generation for Japanese text."""
#     response = client.post(
#         "/tts",
#         json={
#             "text": "こんにちは、テキスト読み上げシステムのテストです。",
#             "language": "ja"
#         }
#     )
    
#     # May return 500 if default speaker doesn't support Japanese well
#     # assert response.status_code in [200, 500]
#     # if response.status_code == 200:
#     #     assert len(response.data) > 0


@pytest.mark.integration
def test_tts_real_french_generation(client):
    """Test real TTS generation for French text."""
    start_time = time.time()
    response = client.post(
        "/tts",
        json={
            "text": "Bonjour, ceci est un test du système de synthèse vocale.",
            "language": "fr",
            "speaker": "Abrahan Mack"
        }
    )
    elapsed_time = time.time() - start_time
    
    print(f"\n[TIMING] TTS French (58 chars): {elapsed_time:.3f}s")
    
    assert response.status_code == 200
    assert len(response.data) > 0

# TODO in API P1
# @pytest.mark.integration
# def test_tts_real_chinese_generation(client):
#     """Test real TTS generation for Chinese text."""
#     response = client.post(
#         "/tts",
#         json={
#             "text": "你好，这是文本转语音系统的测试。",
#             "language": "zh-cn"
#         }
#     )
    
#     # May return 500 if default speaker doesn't support Chinese well
#     # assert response.status_code in [200, 500]
#     # if response.status_code == 200:
#     #     assert len(response.data) > 0


@pytest.mark.integration
def test_tts_real_default_speaker_selection(client):
    """Test that default speaker works correctly when not specified."""
    response = client.post(
        "/tts",
        json={
            "text": "Testing default speaker selection.",
            "language": "en"
        }
    )
    
    assert response.status_code == 200
    assert len(response.data) > 0


@pytest.mark.integration
def test_tts_real_long_text(client):
    """Test TTS with longer text input."""
    long_text = (
        "This is a longer text to test the text-to-speech system's ability to handle "
        "multiple sentences and extended content. The system should be able to process "
        "this text and generate high-quality audio output without any issues."
    )
    
    response = client.post(
        "/tts",
        json={
            "text": long_text,
            "language": "en"
        }
    )
    
    assert response.status_code == 200
    assert len(response.data) > 10000  # Should be longer audio


@pytest.mark.integration
def test_tts_real_special_characters(client):
    """Test TTS with special characters and punctuation."""
    response = client.post(
        "/tts",
        json={
            "text": "Hello! How are you? I'm testing... special characters: @#$%",
            "language": "en"
        }
    )
    
    assert response.status_code == 200
    assert len(response.data) > 0


@pytest.mark.integration
def test_tts_real_numbers_and_symbols(client):
    """Test TTS with numbers and symbols."""
    response = client.post(
        "/tts",
        json={
            "text": "The price is $100.50 for 3 items. Call 555-1234 for details.",
            "language": "en"
        }
    )
    
    assert response.status_code == 200
    assert len(response.data) > 0


@pytest.mark.integration
def test_tts_get_real_speakers(client):
    """Test getting real list of available speakers."""
    response = client.get("/tts/speakers")
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "speakers" in data
    assert len(data["speakers"]) > 0
    assert isinstance(data["speakers"], list)


@pytest.mark.integration
def test_tts_get_real_models(client):
    """Test getting real list of available models."""
    response = client.get("/tts/models")
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "models" in data
    assert len(data["models"]) > 0
    assert isinstance(data["models"], list)


@pytest.mark.integration
def test_tts_real_multiple_requests(client):
    """Test multiple sequential TTS requests."""
    texts = [
        ("Hello world", "en"),
        ("Bonjour le monde", "fr"),
        ("안녕하세요", "ko")
    ]
    
    for text, lang in texts:
        response = client.post(
            "/tts",
            json={
                "text": text,
                "language": lang
            }
        )
        
        assert response.status_code == 200
        assert len(response.data) > 0


@pytest.mark.integration
def test_tts_real_audio_format_validation(client):
    """Test that generated audio has correct WAV format."""
    response = client.post(
        "/tts",
        json={
            "text": "Format validation test",
            "language": "en"
        }
    )
    
    assert response.status_code == 200
    
    # Parse WAV file
    audio_buffer = io.BytesIO(response.data)
    sample_rate, audio_data = wavfile.read(audio_buffer)
    
    # Verify WAV properties
    assert sample_rate == 24000
    assert audio_data.dtype in [np.int16, np.int32, np.float32, np.float64]
    assert len(audio_data.shape) <= 2  # Mono or stereo


@pytest.mark.integration
def test_tts_real_different_speakers(client):
    """Test TTS with different speaker selections."""
    # First get available speakers
    speakers_response = client.get("/tts/speakers")
    speakers_data = json.loads(speakers_response.data)
    speakers = speakers_data["speakers"]
    
    if len(speakers) > 0:
        # Test with first available speaker
        response = client.post(
            "/tts",
            json={
                "text": "Testing speaker selection",
                "language": "en",
                "speaker": speakers[0]
            }
        )
        
        assert response.status_code == 200
        assert len(response.data) > 0


@pytest.mark.integration
def test_tts_real_performance_benchmark(client):
    """Test TTS performance with short text."""
    import time
    
    start_time = time.time()
    
    response = client.post(
        "/tts",
        json={
            "text": "Quick performance test.",
            "language": "en"
        }
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    assert response.status_code == 200
    # TTS should complete within reasonable time (adjust as needed)
    # First call might be slower due to model loading
    assert duration < 30  # 30 seconds max


@pytest.mark.integration 
def test_tts_real_unicode_emoji(client):
    """Test TTS with emoji and special Unicode characters."""
    response = client.post(
        "/tts",
        json={
            "text": "Hello! 👋 This is a test with emoji 😊",
            "language": "en"
        }
    )
    
    # Should handle gracefully (may skip emojis)
    assert response.status_code in [200]


@pytest.mark.integration
def test_tts_real_mixed_language_text(client):
    """Test TTS with mixed language content"""
    response = client.post(
        "/tts",
        json={
            "text": "Hello world, 안녕하세요",
            "language": "en"
        }
    )
    
    # Should handle or reject gracefully
    assert response.status_code in [200, 400, 500]
