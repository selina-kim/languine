"""Integration tests for dictionary API.

These tests make real API calls to Merriam-Webster Dictionary API.
Requires valid MW_DICT_API_KEY in .env file.

Test coverage:
- Real API call with common word
- Invalid word handling (spelling suggestions)
- Complex word with multiple definitions

Run this test file:
    docker compose exec backend pytest src/tests/test_dictionary_integration.py -v -m integration

Run with coverage:
    docker compose exec backend pytest src/tests/test_dictionary_integration.py --cov=services.dictionary_service -m integration
"""
import pytest
import os
import time

# mark all tests in this file as integration tests
pytestmark = pytest.mark.integration
MAX_DICTIONARY_API_SECONDS = 20.0

@pytest.fixture
def skip_if_no_api_key():
    """Skip test if API key is not set."""
    api_key = os.getenv("MW_DICT_API_KEY")
    if not api_key or api_key == "fake-key":
        pytest.skip("MW_DICT_API_KEY not set - skipping integration test")

def test_define_real_api_call(client, skip_if_no_api_key):
    
    # make real api call
    start_time = time.time()
    response = client.get("/define/hello")
    elapsed_time = time.time() - start_time
    
    print(f"\n[TIMING] Dictionary /define/hello: {elapsed_time:.3f}s")
    assert elapsed_time < MAX_DICTIONARY_API_SECONDS

    # verify successful response
    assert response.status_code == 200
    data = response.get_json()
    
    # verify response structure
    assert "word" in data
    assert "definitions" in data
    assert "pronunciation" in data 
    assert "audio_url" in data 
    
    # verify content
    assert data["word"] == "hello"
    assert len(data["definitions"]) > 0
    assert data["definitions"][0]["definition"] == "an expression or gesture of greeting"
    assert data["pronunciation"] == "hə-ˈlō"
    assert data["audio_url"] == "https://media.merriam-webster.com/audio/prons/en/us/mp3/h/hello001.mp3"

def test_define_real_api_invalid_word(client, skip_if_no_api_key):
    # test with misspelled word
    start_time = time.time()
    response = client.get("/define/hellooooo")
    
    assert response.status_code == 200
    data = response.get_json()
    
    # have suggestions for invalid word
    assert data["word"] == "hellooooo"
    if "suggestions" in data:
        assert len(data["suggestions"]) > 0
    else:
        # fallback: if API doesn't provide suggestions, check for "not found" message
        assert "not found" in data["definitions"][0]["definition"].lower() 

def test_define_real_api_complex_word(client, skip_if_no_api_key):
    # test word with multiple definitions."""
    start_time = time.time()
    response = client.get("/define/run")
    elapsed_time = time.time() - start_time
    
    print(f"\n[TIMING] Dictionary /define/run (complex): {elapsed_time:.3f}s")
    assert elapsed_time < MAX_DICTIONARY_API_SECONDS
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data["word"] == "run"
    assert len(data["definitions"]) > 1 
    
    # at least one definition has an example sentence
    has_examples = any(
        len(defn["example_sentences"]) > 0  # check each definition
        for defn in data["definitions"]
    )
    assert has_examples, "At least one definition should have example sentences"
