"""Unit tests for dictionary API.

These tests mock the Merriam-Webster API responses to test the application logic
without making real API calls. Run with: pytest (excludes integration by default)

Test coverage:
- Success case with full data (pronunciation, audio, definitions, examples)
- API errors (500, 429, timeout, connection errors)
- Missing/partial data handling
- Multiple definitions
- Word not found with suggestions
"""
import requests

# ----------------------------
# Fake API Response Fixtures
# ----------------------------
def fake_response_success(*args, **kwargs):
    class FakeResponse:
        status_code = 200
        def json(self):
            return [
                {
                    "meta": {
                        "id": "soup",
                        "uuid": "747b61b5-0ee9-43cb-8322-c53d6c0815d4",
                        "sort": "222744000",
                        "src": "collegiate",
                        "section": "alpha",
                        "stems": ["soup", "soups"],
                        "offensive": False
                    },
                    "hwi": {
                        "hw": "soup",
                        "prs": [
                            {
                                "mw": "ˈsüp",
                                "sound": {
                                    "audio": "soup0001",
                                    "ref": "c",
                                    "stat": "1"
                                }
                            }
                        ]
                    },
                    "fl": "noun",
                    "def": [
                        {
                            "sseq": [
                                [
                                    [
                                        "sense",
                                        {
                                            "sn": "1",
                                            "dt": [
                                                [
                                                    "text",
                                                    "{bc}a liquid food especially with a meat, fish, or vegetable stock as a base and often containing pieces of solid food"
                                                ],
                                                [
                                                    "vis",
                                                    [
                                                        {
                                                            "t": "I had a bowl of chicken {wi}soup{/wi} for lunch"
                                                        }
                                                    ]
                                                ]
                                            ]
                                        }
                                    ]
                                ]
                            ]
                        }
                    ],
                    "shortdef": [
                        "a liquid food especially with a meat, fish, or vegetable stock as a base and often containing pieces of solid food"
                    ]
                }
            ]
    return FakeResponse()

def fake_response_error(*args, **kwargs):
    class FakeResponse:
        status_code = 500
        def json(self):
            return {}
    return FakeResponse()

def fake_response_missing_data(*args, **kwargs):
    class FakeResponse:
        status_code = 200
        def json(self):
            return []  # Empty data
    return FakeResponse()

def fake_response_partial(*args, **kwargs):
    class FakeResponse:
        status_code = 200
        def json(self):
            return [{"hwi": {}, "def": []}]  # Missing pronunciation, audio, definitions
    return FakeResponse()

def fake_response_word_not_found(*args, **kwargs):
    class FakeResponse:
        status_code = 200
        def json(self):
            # When word is not found, API returns suggestions as strings
            return ["soap", "group", "sup", "sou", "coup"]
    return FakeResponse()

def fake_response_rate_limit(*args, **kwargs):
    class FakeResponse:
        status_code = 429
        def json(self):
            return {"error": "Rate limit exceeded"}
    return FakeResponse()

def fake_response_timeout(*args, **kwargs):
    raise requests.exceptions.Timeout("Connection timeout")

def fake_response_connection_error(*args, **kwargs):
    raise requests.exceptions.ConnectionError("Network error")

def fake_response_multiple_defs(*args, **kwargs):
    class FakeResponse:
        status_code = 200
        def json(self):
            return [
                {
                    "meta": {
                        "id": "run",
                        "uuid": "abc-123",
                        "sort": "180000000",
                        "src": "collegiate",
                        "section": "alpha",
                        "stems": ["run", "runs"],
                        "offensive": False
                    },
                    "hwi": {
                        "hw": "run",
                        "prs": [
                            {
                                "mw": "ˈrən",
                                "sound": {
                                    "audio": "run00001",
                                    "ref": "r",
                                    "stat": "1"
                                }
                            }
                        ]
                    },
                    "fl": "verb",
                    "def": [
                        {
                            "sseq": [
                                [
                                    [
                                        "sense",
                                        {
                                            "sn": "1",
                                            "dt": [
                                                [
                                                    "text",
                                                    "{bc}to go faster than a walk"
                                                ],
                                                [
                                                    "vis",
                                                    [
                                                        {
                                                            "t": "He can {wi}run{/wi} very fast"
                                                        },
                                                        {
                                                            "t": "She {wi}runs{/wi} every morning"
                                                        }
                                                    ]
                                                ]
                                            ]
                                        }
                                    ]
                                ],
                                [
                                    [
                                        "sense",
                                        {
                                            "sn": "2",
                                            "dt": [
                                                [
                                                    "text",
                                                    "{bc}to operate or function"
                                                ],
                                                [
                                                    "vis",
                                                    [
                                                        {
                                                            "t": "The engine {wi}runs{/wi} smoothly"
                                                        }
                                                    ]
                                                ]
                                            ]
                                        }
                                    ]
                                ]
                            ]
                        }
                    ],
                    "shortdef": [
                        "to go faster than a walk",
                        "to operate or function"
                    ]
                }
            ]
    return FakeResponse()

# ----------------------------
# Tests
# ----------------------------
def test_define_success(client, monkeypatch):
    """Normal API response with definitions, pronunciation, audio."""
    # set up fake environment to mock the API call
    # add fake API key to environment
    monkeypatch.setenv("MW_DICT_API_KEY", "fake-key")  
    # replace requests.get with our fake response
    monkeypatch.setattr("src.services.dictionary_api.requests.get", fake_response_success)  

    response = client.get("/define/soup")
    
    # verify successful response status
    assert response.status_code == 200  
    data = response.get_json()
    
    # verify word information
    assert data["word"] == "soup"  
    assert data["pronunciation"] == "ˈsüp"  
    assert data["audio_url"] == "https://media.merriam-webster.com/audio/prons/en/us/mp3/s/soup0001.mp3"  # Should construct audio URL from sound.audio
    
    # verify definitions
    assert len(data["definitions"]) == 1  
    assert data["definitions"][0]["definition"] == "a liquid food especially with a meat, fish, or vegetable stock as a base and often containing pieces of solid food"  
    
    # verify example sentences
    assert len(data["definitions"][0]["example_sentences"]) == 1  
    # verify complete example text (should be cleaned of markup like {wi})
    assert data["definitions"][0]["example_sentences"][0] == "I had a bowl of chicken soup for lunch"  

def test_define_api_error(client, monkeypatch):
    """MW API returns error (non-200)."""
    # mock API to return 500 error
    monkeypatch.setenv("MW_DICT_API_KEY", "fake-key")
    monkeypatch.setattr("src.services.dictionary_api.requests.get", fake_response_error)

    response = client.get("/define/soup")
    
    # should return same error code
    assert response.status_code == 500  
    data = response.get_json()
    assert data["error"] == "Failed to fetch data"

def test_define_missing_data(client, monkeypatch):
    """MW API returns empty/malformed data."""
    # mock API to return empty array
    monkeypatch.setenv("MW_DICT_API_KEY", "fake-key")
    monkeypatch.setattr("src.services.dictionary_api.requests.get", fake_response_missing_data)

    response = client.get("/define/soup")
    
    # no data but 200 status
    assert response.status_code == 200  
    data = response.get_json()
    # verify fallback for missing definition
    assert data["definitions"][0]["definition"] == "Definition not found"

def test_define_partial_data(client, monkeypatch):
    """MW API returns missing pronunciation/audio."""
    # mock API to return incomplete data
    monkeypatch.setenv("MW_DICT_API_KEY", "fake-key")
    monkeypatch.setattr("src.services.dictionary_api.requests.get", fake_response_partial)

    response = client.get("/define/soup")
    data = response.get_json()
    assert response.status_code == 200
    assert data["pronunciation"] is None
    assert data["audio_url"] is None
    assert data["definitions"][0]["definition"] == "Definition not found"

def test_define_multiple_definitions(client, monkeypatch):
    """Test word with multiple definitions and example sentences."""
    # mock API to return word with 2 definitions
    monkeypatch.setenv("MW_DICT_API_KEY", "fake-key")
    monkeypatch.setattr("src.services.dictionary_api.requests.get", fake_response_multiple_defs)

    response = client.get("/define/run")
    assert response.status_code == 200
    data = response.get_json()

    # check word info
    assert data["word"] == "run"
    assert data["pronunciation"] == "ˈrən"
    assert data["audio_url"] == "https://media.merriam-webster.com/audio/prons/en/us/mp3/r/run00001.mp3"

    # check multiple definitions exist
    defs = data["definitions"]
    assert len(defs) == 2 
    
    # verify first definition
    assert defs[0]["definition"] == "to go faster than a walk"
    assert len(defs[0]["example_sentences"]) == 2
    assert defs[0]["example_sentences"][0] == "He can run very fast"
    assert defs[0]["example_sentences"][1] == "She runs every morning"
    
    # verify second definition
    assert defs[1]["definition"] == "to operate or function"
    assert len(defs[1]["example_sentences"]) == 1
    assert defs[1]["example_sentences"][0] == "The engine runs smoothly"

def test_define_word_not_found(client, monkeypatch):
    """Test when word is not found - API returns suggestions."""
    # mock API to return suggestions when word is misspelled (array)
    monkeypatch.setenv("MW_DICT_API_KEY", "fake-key")
    monkeypatch.setattr("src.services.dictionary_api.requests.get", fake_response_word_not_found)

    response = client.get("/define/soupppp")
    assert response.status_code == 200
    data = response.get_json()

    # verify word not found scenario
    assert data["word"] == "soupppp"  
    assert data["definitions"][0]["definition"] == "Word not found" 
    assert data["pronunciation"] is None  
    assert data["audio_url"] is None 
    # should include spelling suggestions
    assert "suggestions" in data  
    # at least 1 suggestion
    assert len(data["suggestions"]) > 0 
    # check one of the expected suggestions
    assert "soap" in data["suggestions"] 

def test_define_rate_limit(client, monkeypatch):
    """Test when API rate limit is exceeded."""
    # mock API to return 429 rate limit error
    monkeypatch.setenv("MW_DICT_API_KEY", "fake-key")
    monkeypatch.setattr("src.services.dictionary_api.requests.get", fake_response_rate_limit)

    response = client.get("/define/soup")
    
    assert response.status_code == 429  
    data = response.get_json()
    assert data["error"] == "Rate limit exceeded" 

def test_define_timeout(client, monkeypatch):
    """Test when API request times out."""
    # mock API to raise timeout exception
    monkeypatch.setenv("MW_DICT_API_KEY", "fake-key")
    monkeypatch.setattr("src.services.dictionary_api.requests.get", fake_response_timeout)

    response = client.get("/define/soup")
    
    assert response.status_code == 504
    data = response.get_json()
    assert data["error"] == "Request timeout"

def test_define_connection_error(client, monkeypatch):
    """Test when network connection fails."""
    # mock API to raise connection error exception
    monkeypatch.setenv("MW_DICT_API_KEY", "fake-key")
    monkeypatch.setattr("src.services.dictionary_api.requests.get", fake_response_connection_error)

    response = client.get("/define/soup")
    
    assert response.status_code == 503
    data = response.get_json()
    assert data["error"] == "Network connection error"
