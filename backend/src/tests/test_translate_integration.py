"""Integration tests for translate API.

These tests make real API calls to DeepL for translation.
Requires valid DEEPL_API_KEY in .env file.

Run this test file:
    docker compose exec backend pytest src/tests/test_translate_integration.py -v -m integration

Run with coverage:
    docker compose exec backend pytest src/tests/test_translate_integration.py --cov=services.translate_service -m integration
"""
import pytest
import json
import time


pytestmark = pytest.mark.integration

# test translation via POST
def test_translate_real_api_post(client):
    # send POST request with English text to translate to Korean
    start_time = time.time()
    response = client.post(
        "/translate",
        json={"text": "Hello world", "target_lang": "KO"}
    )
    elapsed_time = time.time() - start_time
    
    print(f"\n[TIMING] Translation POST EN->KO: {elapsed_time:.3f}s")
    
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
    start_time = time.time()
    response = client.get("/translate?text=こんにちは&source=JA&target=EN-US")
    elapsed_time = time.time() - start_time
    
    print(f"\n[TIMING] Translation GET JA->EN-US: {elapsed_time:.3f}s")
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert "translatedText" in data
    assert len(data["translatedText"]) > 0
    assert "detectedSourceLang" in data

# translate sentence
def test_translate_real_api_complex_text(client):
    complex_text = "안녕하세요. 오늘 날씨가 정말 좋네요."
    start_time = time.time()
    response = client.post(
        "/translate",
        json={"text": complex_text, "target_lang": "EN-US"}
    )
    elapsed_time = time.time() - start_time
    
    print(f"\n[TIMING] Translation POST KO->EN-US (complex): {elapsed_time:.3f}s")
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert "detectedSourceLang" in data
    assert data["detectedSourceLang"] is not None
    assert "translatedText" in data
    assert len(data["translatedText"]) > 0
    assert data["translatedText"] != complex_text
