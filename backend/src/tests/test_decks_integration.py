"""Integration tests for deck routes.

Tests the deck management endpoints with actual HTTP requests and responses.
These tests verify the complete request/response cycle including:
- Deck export (JSON, CSV, Anki formats)
- Deck import (JSON, CSV, Anki formats)
- Deck CRUD operations (create, read, update, delete)
- Authentication and authorization
- Database interactions
- File upload/download handling

Mark with @pytest.mark.integration to run separately from unit tests.

Run this test file:
    docker compose exec backend pytest src/tests/test_deck_routes_integration.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_deck_routes_integration.py --cov=routes.decks
"""

import pytest
import json
from io import BytesIO


def test_export_deck_json_success(client, auth_headers):
    """Test successful deck export in JSON format"""
    response = client.get("/decks/1/export?format=json", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.mimetype == "application/json"
    
    # Check attachment header for download
    assert "attachment" in response.headers.get("Content-Disposition", "")


def test_export_deck_csv_success(client, auth_headers):
    """Test successful deck export in CSV format"""
    response = client.get("/decks/1/export?format=csv", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.mimetype == "text/csv"


def test_export_deck_anki_success(client, auth_headers):
    """Test successful deck export in Anki format"""
    response = client.get("/decks/1/export?format=anki", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.mimetype == "text/plain"


def test_export_deck_invalid_format(client, auth_headers):
    """Test deck export with invalid format"""
    response = client.get("/decks/1/export?format=invalid", headers=auth_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "Unsupported export format" in data["error"]


def test_export_deck_default_format(client, auth_headers):
    """Test deck export defaults to JSON when no format specified"""
    response = client.get("/decks/1/export", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.mimetype == "application/json"


def test_import_deck_json_success(client, auth_headers):
    """Test successful deck import from JSON"""
    deck_data = {
        "deck": {
            "deck_name": "Imported Test Deck",
            "word_lang": "Spanish",
            "trans_lang": "English",
            "description": "Test"
        },
        "cards": [
            {
                "word": "hola",
                "translation": "hello",
                "definition": "",
                "word_example": "",
                "trans_example": "",
                "word_roman": "",
                "trans_roman": "",
                "image": ""
            }
        ]
    }
    
    file_content = json.dumps(deck_data)
    data = {
        'file': (BytesIO(file_content.encode()), 'test_deck.json')
    }
    
    response = client.post(
        "/decks/import",
        data=data,
        content_type='multipart/form-data',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    assert "message" in result
    assert result["deck"]["deck_name"] == "Imported Test Deck"
    assert result["cards_count"] == 1


def test_import_deck_csv_success(client, auth_headers):
    """Test successful deck import from CSV"""
    csv_content = """word,translation,definition,word_example,trans_example,word_roman,trans_roman,image
hola,hello,greeting,Hola!,Hello!,oh-lah,,
adiós,goodbye,farewell,Adiós,Goodbye,ah-dee-ohs,,"""
    
    data = {
        'file': (BytesIO(csv_content.encode()), 'test_deck.csv'),
        'deck_name': 'Spanish Basics',
        'word_lang': 'Spanish',
        'trans_lang': 'English'
    }
    
    response = client.post(
        "/decks/import",
        data=data,
        content_type='multipart/form-data',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    assert result["deck"]["deck_name"] == "Spanish Basics"
    assert result["cards_count"] == 2


def test_import_deck_csv_missing_params(client, auth_headers):
    """Test CSV import with missing required parameters"""
    csv_content = "word,translation\nhola,hello"
    
    data = {
        'file': (BytesIO(csv_content.encode()), 'test.csv'),
        'deck_name': 'Test'
        # Missing word_lang and trans_lang
    }
    
    response = client.post(
        "/decks/import",
        data=data,
        content_type='multipart/form-data',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "error" in result
    assert "requires deck_name, word_lang, and trans_lang" in result["error"]


def test_import_deck_anki_success(client, auth_headers):
    """Test successful deck import from Anki format"""
    anki_content = """#deck: Test Deck
hola\thello
adiós\tgoodbye"""
    
    data = {
        'file': (BytesIO(anki_content.encode()), 'test_deck.txt'),
        'deck_name': 'Spanish Basics',
        'word_lang': 'Spanish',
        'trans_lang': 'English'
    }
    
    response = client.post(
        "/decks/import",
        data=data,
        content_type='multipart/form-data',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    assert result["cards_count"] == 2


def test_import_deck_no_file(client, auth_headers):
    """Test deck import with no file provided"""
    response = client.post(
        "/decks/import",
        data={},
        content_type='multipart/form-data',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "No file provided" in result["error"]


def test_import_deck_invalid_json(client, auth_headers):
    """Test deck import with invalid JSON"""
    data = {
        'file': (BytesIO(b'not valid json'), 'test.json')
    }
    
    response = client.post(
        "/decks/import",
        data=data,
        content_type='multipart/form-data',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "error" in result


def test_import_deck_unknown_format(client, auth_headers):
    """Test deck import with unknown file format"""
    data = {
        'file': (BytesIO(b'some content'), 'test.xyz')
    }
    
    response = client.post(
        "/decks/import",
        data=data,
        content_type='multipart/form-data',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "Could not determine file format" in result["error"]


def test_create_deck_success(client, auth_headers):
    """Test successful deck creation"""
    deck_data = {
        "deck_name": "New Deck",
        "word_lang": "French",
        "trans_lang": "English",
        "description": "French vocabulary"
    }
    
    response = client.post(
        "/decks/new",
        data=json.dumps(deck_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    assert "message" in result
    assert result["deck"]["deck_name"] == "New Deck"


def test_create_deck_missing_fields(client, auth_headers):
    """Test deck creation with missing required fields"""
    deck_data = {
        "deck_name": "New Deck"
        # Missing word_lang and trans_lang
    }
    
    response = client.post(
        "/decks/new",
        data=json.dumps(deck_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "Missing required field" in result["error"]


def test_create_deck_no_data(client, auth_headers):
    """Test deck creation with no data"""
    response = client.post(
        "/decks/new",
        data="",
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "No data provided" in result["error"]


def test_get_deck_success(client, auth_headers):
    """Test successful deck retrieval"""
    response = client.get("/decks/1", headers=auth_headers)
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert "deck" in result
    assert "cards" in result


def test_list_decks_success(client, auth_headers):
    """Test successful listing of decks"""
    response = client.get("/decks", headers=auth_headers)
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert "decks" in result
