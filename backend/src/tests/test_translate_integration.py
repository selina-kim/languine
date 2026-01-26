"""
Integration tests for the translate route with real DeepL API calls.
These tests require a valid DEEPL_API_KEY in the .env file.

Run with: docker compose exec backend poetry run pytest -m integration
"""
import pytest
import json


pytestmark = pytest.mark.integration

# test translation via POST
def test_translate_real_api_post(client):
    # send POST request with English text to translate to Korean
    response = client.post(
        "/translate",
        json={"text": "Hello world", "target_lang": "KO"}
    )
    
    # parse the JSON response body
    data = json.loads(response.data)
    
    # verify 200 OK, source language present, translated text present
    assert response.status_code == 200
    assert "detectedSourceLang" in data
    assert data["detectedSourceLang"] is not None
    assert "translatedText" in data
    assert len(data["translatedText"]) > 0

# test translation via GET with source language
def test_translate_real_api_get_with_source(client):
    # send GET request with query parameters: text, source, and target
    # translate from Japanese to English (DeepL uses EN-US or EN-GB for English)
    response = client.get("/translate?text=こんにちは&source=JA&target=EN-US")
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert "translatedText" in data
    assert len(data["translatedText"]) > 0
    assert "detectedSourceLang" in data

# translate sentence
def test_translate_real_api_complex_text(client):
    complex_text = "안녕하세요. 오늘 날씨가 정말 좋네요."
    response = client.post(
        "/translate",
        json={"text": complex_text, "target_lang": "EN-US"}
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert "detectedSourceLang" in data
    assert data["detectedSourceLang"] is not None
    assert "translatedText" in data
    assert len(data["translatedText"]) > 0
    assert data["translatedText"] != complex_text
