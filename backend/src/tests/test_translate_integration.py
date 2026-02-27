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


def test_get_supported_languages_real_api(client):
    """Test fetching real supported languages from DeepL API."""
    start_time = time.time()
    response = client.get("/translate/languages")
    elapsed_time = time.time() - start_time
    
    print(f"\n[TIMING] Get supported languages: {elapsed_time:.3f}s")
    
    data = json.loads(response.data)
    
    # verify response structure
    assert response.status_code == 200
    assert "source" in data
    assert "target" in data
    assert isinstance(data["source"], list)
    assert isinstance(data["target"], list)
    
    # verify we got actual languages
    assert len(data["source"]) > 0
    assert len(data["target"]) > 0
    
    # verify language structure (each should have code and name)
    for lang in data["source"]:
        assert "code" in lang
        assert "name" in lang
        assert len(lang["code"]) >= 2
        assert len(lang["name"]) > 0
    
    for lang in data["target"]:
        assert "code" in lang
        assert "name" in lang
        assert len(lang["code"]) >= 2
        assert len(lang["name"]) > 0
    
    # verify common languages are present
    source_codes = [lang["code"] for lang in data["source"]]
    target_codes = [lang["code"] for lang in data["target"]]
    
    # check for common source languages
    assert "EN" in source_codes
    assert "ES" in source_codes or "FR" in source_codes
    
    # check for common target languages we use in tests
    assert "KO" in target_codes
    assert "JA" in target_codes
    assert "ZH" in target_codes or "ZH-HANS" in target_codes  # Chinese simplified
