"""Unit tests for translate API.

These tests mock the DeepL API responses to test the application logic
without making real API calls. 

Test coverage:
- Success cases (POST/GET with auto-detected and explicit source language)
- Missing required parameters (text, target_lang)
- Missing API key configuration
- API errors and exceptions
- Unicode text handling (Korean, emoji)
- Empty string validation

Run this test file:
    docker compose exec backend pytest src/tests/test_translate_unit.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_translate_unit.py --cov=services.translate_service
"""
import json

# test successful translation via POST request with auto-detected source language
def test_translate_post_success(client, monkeypatch):
    # mock translation result object that mimics deepl.TextResult
    class MockTranslationResult:
        def __init__(self):
            self.text = "안녕하세요"
            self.detected_source_lang = "EN"
    
    # mock Translator client
    class MockTranslator:
        def translate_text(self, text, target_lang=None, source_lang=None):
            return MockTranslationResult()
    
    # replace the _client with our mock
    monkeypatch.setattr("services.translate_service._client", MockTranslator())
    
    # set API key
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    # sent POST
    response = client.post(
        "/translate",
        json={"text": "Hello", "target_lang": "KO"}
    )
    
    # parse the JSON response into dict
    data = json.loads(response.data)
    
    # verify HTTP OK, EN source language, and korean translated text
    assert response.status_code == 200
    assert data["detectedSourceLang"] == "EN"
    assert data["translatedText"] == "안녕하세요"

# test successful translation via POST with specified source language.
def test_translate_post_with_source_lang(client, monkeypatch):
    
    # create mock result for French to English translation
    class MockTranslationResult:
        def __init__(self):
            self.text = "Hello"
            self.detected_source_lang = "FR"
    
    class MockTranslator:
        def translate_text(self, text, target_lang=None, source_lang=None):
            return MockTranslationResult()
    
    monkeypatch.setattr("services.translate_service._client", MockTranslator())
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    # send POST request with source_lang
    response = client.post(
        "/translate",
        json={"text": "Bonjour", "source_lang": "FR", "target_lang": "EN-US"}
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["detectedSourceLang"] == "FR"
    assert data["translatedText"] == "Hello"

# test successful translation via GET with source language in URL path
def test_translate_get_with_source_lang(client, monkeypatch):
    
    class MockTranslationResult:
        def __init__(self):
            self.text = "How are you?"
            self.detected_source_lang = "JA"
    
    class MockTranslator:
        def translate_text(self, text, target_lang=None, source_lang=None):
            return MockTranslationResult()
    
    monkeypatch.setattr("services.translate_service._client", MockTranslator())
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    # send GET request with query parameters: text, source, and target
    response = client.get("/translate?text=ご機嫌いかがですか&source=JA&target=EN-US")
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["detectedSourceLang"] == "JA"
    assert data["translatedText"] == "How are you?"

# test successful translation via GET with auto-detected source language
def test_translate_get_without_source_lang(client, monkeypatch):
    
    class MockTranslationResult:
        def __init__(self):
            self.text = "您好"
            self.detected_source_lang = "EN"
    
    class MockTranslator:
        def translate_text(self, text, target_lang=None, source_lang=None):
            return MockTranslationResult()
    
    monkeypatch.setattr("services.translate_service._client", MockTranslator())
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    # send GET request with query parameters: text and target (source auto-detected)
    response = client.get("/translate?text=Hello&target=ZH")
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["detectedSourceLang"] == "EN"
    assert data["translatedText"] == "您好"

# test error handling when text is missing from POST request
def test_translate_missing_text(client, monkeypatch):
    """"""

    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    # send POST request with only target_lang
    response = client.post(
        "/translate",
        json={"target_lang": "KO"}
    )
    
    data = json.loads(response.data)
    
    # verify HTTP status code, error message
    assert response.status_code == 400
    assert "Missing text or target_lang" in data["error"]

# test error handling when target_lang parameter is missing from POST request
def test_translate_missing_target_lang(client, monkeypatch):
    """"""
    
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    response = client.post(
        "/translate",
        json={"text": "Hello"}
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 400
    assert "Missing text or target_lang" in data["error"]

# test error handling when DEEPL_API_KEY environment variable is not set
# Note: Since the translate_service module initializes _client at import time,
# the app must have DEEPL_API_KEY set during startup. This test verifies
# the error handling exists, but in production the service would fail at startup.
def test_translate_missing_api_key(client, monkeypatch):
    # Mock a client that simulates missing API key behavior
    class MockTranslator:
        def translate_text(self, text, target_lang=None, source_lang=None):
            raise ValueError("DEEPL_API_KEY not set in environment")
    
    monkeypatch.setattr("services.translate_service._client", MockTranslator())
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    # Send valid POST request
    response = client.post(
        "/translate",
        json={"text": "Hello", "target_lang": "KO"}
    )
    
    data = json.loads(response.data)
    
    # verify 500 Internal Server Error
    assert response.status_code == 500
    assert "DEEPL_API_KEY not set in environment" in data["error"]

# test error handling when DeepL API raises an exception during translation
def test_translate_api_error(client, monkeypatch):
    
    class MockTranslator:
        def translate_text(self, text, target_lang=None, source_lang=None):
            raise Exception("DeepL API connection failed")
    
    monkeypatch.setattr("services.translate_service._client", MockTranslator())
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    # send valid POST request
    response = client.post(
        "/translate",
        json={"text": "Hello", "target_lang": "KO"}
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 500
    assert "DeepL API connection failed" in data["error"]

# test translation with Unicode characters
def test_translate_unicode_text(client, monkeypatch):

    class MockTranslationResult:
        def __init__(self):
            self.text = "Hello, how are you? 😊"
            self.detected_source_lang = "KO"
    
    class MockTranslator:
        def translate_text(self, text, target_lang=None, source_lang=None):
            return MockTranslationResult()
    
    monkeypatch.setattr("services.translate_service._client", MockTranslator())
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    # POST request with Korean text and emoji
    response = client.post(
        "/translate",
        json={"text": "안녕하세요, 어떻게 지내세요? 😊", "target_lang": "EN"}
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["detectedSourceLang"] == "KO"
    # verify Unicode characters are preserved in response
    assert data["translatedText"] == "Hello, how are you? 😊"


def test_translate_empty_string(client, monkeypatch):
    """Test error handling when text is an empty string."""
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    # send POST request with empty text string
    response = client.post(
        "/translate",
        json={"text": "", "target_lang": "KO"}
    )
    
    data = json.loads(response.data)
    
    # verify 400 Bad Request, error message
    assert response.status_code == 400
    assert "Missing text or target_lang" in data["error"]


def test_get_supported_languages_success(client, monkeypatch):
    """Test successful retrieval of supported languages."""
    # mock language objects
    class MockLanguage:
        def __init__(self, code, name):
            self.code = code
            self.name = name
    
    class MockTranslator:
        def get_source_languages(self):
            return [
                MockLanguage("EN", "English"),
                MockLanguage("FR", "French"),
                MockLanguage("DE", "German")
            ]
        
        def get_target_languages(self):
            return [
                MockLanguage("ES", "Spanish"),
                MockLanguage("KO", "Korean"),
                MockLanguage("JA", "Japanese"),
                MockLanguage("ZH", "Chinese (simplified)")
            ]
    
    monkeypatch.setattr("services.translate_service._client", MockTranslator())
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    # send GET request
    response = client.get("/translate/languages")
    data = json.loads(response.data)
    
    # verify response structure
    assert response.status_code == 200
    assert "source" in data
    assert "target" in data
    assert isinstance(data["source"], list)
    assert isinstance(data["target"], list)
    
    # verify source languages
    assert len(data["source"]) == 3
    assert data["source"][0]["code"] == "EN"
    assert data["source"][0]["name"] == "English"
    
    # verify target languages
    assert len(data["target"]) == 4
    assert data["target"][0]["code"] == "ES"
    assert data["target"][1]["code"] == "KO"


def test_get_supported_languages_api_error(client, monkeypatch):
    """Test error handling when fetching languages fails."""
    class MockTranslator:
        def get_source_languages(self):
            raise Exception("DeepL API error")
    
    monkeypatch.setattr("services.translate_service._client", MockTranslator())
    monkeypatch.setenv("DEEPL_API_KEY", "test_api_key_12345")
    
    response = client.get("/translate/languages")
    data = json.loads(response.data)
    
    assert response.status_code == 500
    assert "error" in data
    assert "Failed to fetch supported languages" in data["error"]
