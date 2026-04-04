"""Integration tests for deck routes.

Tests the deck management endpoints with actual HTTP requests and responses.
These tests verify the complete request/response cycle including:
- Deck export (JSON, CSV, Anki formats)
- Deck import (JSON, CSV, Anki formats)
- Deck CRUD operations (create, read, update, delete)
- Authentication and authorization
- Database interactions
- File upload/download handling

All tests in this file are marked as integration tests.

Run this test file:
    docker compose exec backend pytest src/tests/test_decks_integration.py -v -m integration

Run with coverage:
    docker compose exec backend pytest src/tests/test_decks_integration.py --cov=routes.decks -m integration
"""

import pytest
import json
from io import BytesIO


pytestmark = pytest.mark.integration


def test_export_deck_json_success(client, auth_headers, deck_id):
    """Test successful deck export in JSON format"""
    response = client.get(f"/decks/{deck_id}/export?format=json", headers=auth_headers)

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    
    # Check attachment header for download
    assert "attachment" in response.headers.get("Content-Disposition", "")


def test_export_deck_csv_success(client, auth_headers, deck_id):
    """Test successful deck export in CSV format"""
    response = client.get(f"/decks/{deck_id}/export?format=csv", headers=auth_headers)

    assert response.status_code == 200
    assert response.mimetype == "text/csv"


def test_export_deck_anki_success(client, auth_headers, deck_id):
    """Test successful deck export in Anki format"""
    response = client.get(f"/decks/{deck_id}/export?format=anki", headers=auth_headers)

    assert response.status_code == 200
    assert response.mimetype == "text/plain"


def test_export_deck_invalid_format(client, auth_headers, deck_id):
    """Test deck export with invalid format"""
    response = client.get(f"/decks/{deck_id}/export?format=invalid", headers=auth_headers)

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "Unsupported export format" in data["error"]


def test_export_deck_default_format(client, auth_headers, deck_id):
    """Test deck export defaults to JSON when no format specified"""
    response = client.get(f"/decks/{deck_id}/export", headers=auth_headers)

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


def test_get_deck_success(client, auth_headers, deck_id):
    """Test successful deck retrieval"""
    response = client.get(f"/decks/{deck_id}", headers=auth_headers)

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


def test_update_deck_success(client, auth_headers, deck_id):
    """Test successful deck update with all fields"""
    update_data = {
        "deck_name": "Updated Deck Name",
        "word_lang": "French",
        "trans_lang": "English",
        "description": "Updated description",
        "is_public": True,
        "link": "https://example.com"
    }
    
    response = client.put(
        f"/decks/{deck_id}",
        data=json.dumps(update_data),
        content_type="application/json",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["message"] == "Deck updated successfully"
    assert "deck" in result
    assert result["deck"]["deck_name"] == "Updated Deck Name"


def test_update_deck_partial(client, auth_headers, deck_id):
    """Test partial deck update (only description)"""
    update_data = {
        "description": "Just updating the description"
    }
    
    response = client.put(
        f"/decks/{deck_id}",
        data=json.dumps(update_data),
        content_type="application/json",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert "deck" in result


def test_update_deck_empty_name(client, auth_headers, deck_id):
    """Test update with empty deck name fails"""
    update_data = {
        "deck_name": "   "
    }
    
    response = client.put(
        f"/decks/{deck_id}",
        data=json.dumps(update_data),
        content_type="application/json",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "error" in result
    assert "cannot be empty" in result["error"]


def test_update_deck_not_found(client, auth_headers):
    """Test update of non-existent deck"""
    update_data = {
        "deck_name": "New Name"
    }
    
    response = client.put(
        "/decks/99999",
        data=json.dumps(update_data),
        content_type="application/json",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    result = json.loads(response.data)
    assert "error" in result


def test_update_deck_no_data(client, auth_headers, deck_id):
    """Test update with no data provided"""
    response = client.put(
        f"/decks/{deck_id}",
        data="",
        content_type="application/json",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "No data provided" in result["error"]


def test_update_deck_unauthorized(client, auth_headers, deck_id):
    """Test update without authentication"""
    update_data = {
        "deck_name": "New Name"
    }
    
    response = client.put(
        f"/decks/{deck_id}",
        data=json.dumps(update_data),
        content_type="application/json"
    )
    
    assert response.status_code == 401


def test_delete_deck_success(client, auth_headers, deck_id):
    """Test successful deck deletion"""
    response = client.delete(f"/decks/{deck_id}", headers=auth_headers)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["message"] == "Deck deleted successfully"


def test_delete_deck_not_found(client, auth_headers):
    """Test deletion of non-existent deck"""
    response = client.delete("/decks/99999", headers=auth_headers)
    
    assert response.status_code == 404
    result = json.loads(response.data)
    assert "error" in result


def test_delete_deck_unauthorized(client, deck_id):
    """Test deletion without authentication"""
    response = client.delete(f"/decks/{deck_id}")

    assert response.status_code == 401


def test_get_decks_with_due_cards(client, auth_headers):
    """Test getting decks with due cards"""
    response = client.get("/decks/due?limit=5", headers=auth_headers)
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert "decks" in result


def test_get_recent_decks(client, auth_headers):
    """Test getting recently reviewed decks"""
    response = client.get("/decks/recent?limit=5", headers=auth_headers)
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert "decks" in result


def test_export_deck_database_error(client, auth_headers, deck_id):
    """Test export endpoint when database error occurs"""
    from unittest.mock import patch
    
    with patch("routes.decks.deck_service.get_deck_for_export") as mock_export:
        mock_export.side_effect = Exception("DB connection failed")
        
        response = client.get(f"/decks/{deck_id}/export?format=json", headers=auth_headers)
        
        assert response.status_code == 500
        result = json.loads(response.data)
        assert "Database error" in result["error"]


def test_export_deck_not_found(client, auth_headers):
    """Test export of non-existent deck"""
    response = client.get("/decks/99999/export?format=json", headers=auth_headers)
    
    assert response.status_code == 404
    result = json.loads(response.data)
    assert "error" in result
    assert "not found" in result["error"].lower()


def test_import_deck_database_error(client, auth_headers):
    """Test import endpoint when database error occurs"""
    from unittest.mock import patch
    
    deck_data = {
        "deck": {
            "deck_name": "Test Deck",
            "word_lang": "Spanish",
            "trans_lang": "English",
            "description": "Test"
        },
        "cards": []
    }
    
    with patch("routes.decks.deck_service.save_imported_deck") as mock_save:
        mock_save.side_effect = Exception("DB connection failed")
        
        file_content = json.dumps(deck_data)
        data = {
            'file': (BytesIO(file_content.encode()), 'test.json')
        }
        
        response = client.post(
            "/decks/import",
            data=data,
            content_type='multipart/form-data',
            headers=auth_headers
        )
        
        assert response.status_code == 500
        result = json.loads(response.data)
        assert "error" in result


def test_import_deck_empty_file(client, auth_headers):
    """Test import with empty file"""
    data = {
        'file': (BytesIO(b''), 'test.json')
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


def test_create_deck_duplicate_name_error(client, auth_headers):
    """Test deck creation with duplicate name"""
    from unittest.mock import patch
    from services.deck_service import DuplicateDeckNameError
    
    deck_data = {
        "deck_name": "Spanish",
        "word_lang": "es",
        "trans_lang": "en"
    }
    
    with patch("routes.decks.deck_service.create_deck") as mock_create:
        mock_create.side_effect = DuplicateDeckNameError("Deck name already exists")
        
        response = client.post(
            "/decks/new",
            data=json.dumps(deck_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 409
        result = json.loads(response.data)
        assert "error" in result


def test_create_deck_user_not_found_error(client, auth_headers):
    """Test deck creation when user not found"""
    from unittest.mock import patch
    from services.deck_service import UserNotFoundError
    
    deck_data = {
        "deck_name": "Test Deck",
        "word_lang": "es",
        "trans_lang": "en"
    }
    
    with patch("routes.decks.deck_service.create_deck") as mock_create:
        mock_create.side_effect = UserNotFoundError("User not found")
        
        response = client.post(
            "/decks/new",
            data=json.dumps(deck_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 401
        result = json.loads(response.data)
        assert "error" in result


def test_create_deck_database_error(client, auth_headers):
    """Test deck creation when database error occurs"""
    from unittest.mock import patch
    from services.deck_service import DatabaseError
    
    deck_data = {
        "deck_name": "Test Deck",
        "word_lang": "es",
        "trans_lang": "en"
    }
    
    with patch("routes.decks.deck_service.create_deck") as mock_create:
        mock_create.side_effect = DatabaseError("DB error")
        
        response = client.post(
            "/decks/new",
            data=json.dumps(deck_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 500
        result = json.loads(response.data)
        assert "error" in result


def test_list_decks_database_error(client, auth_headers):
    """Test listing decks when database error occurs"""
    from unittest.mock import patch
    
    with patch("routes.decks.deck_service.list_user_decks") as mock_list:
        mock_list.side_effect = Exception("DB connection failed")
        
        response = client.get("/decks", headers=auth_headers)
        
        assert response.status_code == 500
        result = json.loads(response.data)
        assert "Database error" in result["error"]


def test_get_deck_database_error(client, auth_headers, deck_id):
    """Test getting a deck when database error occurs"""
    from unittest.mock import patch
    
    with patch("routes.decks.deck_service.get_deck_with_cards") as mock_get:
        mock_get.side_effect = Exception("DB connection failed")
        
        response = client.get(f"/decks/{deck_id}", headers=auth_headers)
        
        assert response.status_code == 500
        result = json.loads(response.data)
        assert "Database error" in result["error"]


def test_get_decks_due_database_error(client, auth_headers):
    """Test getting due decks when database error occurs"""
    from unittest.mock import patch
    
    with patch("routes.decks.deck_service.get_decks_with_due_cards") as mock_get:
        mock_get.side_effect = Exception("DB connection failed")
        
        response = client.get("/decks/due", headers=auth_headers)
        
        assert response.status_code == 500
        result = json.loads(response.data)
        assert "Database error" in result["error"]


def test_get_recent_decks_database_error(client, auth_headers):
    """Test getting recent decks when database error occurs"""
    from unittest.mock import patch
    
    with patch("routes.decks.deck_service.get_recent_decks") as mock_get:
        mock_get.side_effect = Exception("DB connection failed")
        
        response = client.get("/decks/recent", headers=auth_headers)
        
        assert response.status_code == 500
        result = json.loads(response.data)
        assert "Database error" in result["error"]


def test_update_deck_duplicate_name_error(client, auth_headers, deck_id):
    """Test updating deck with duplicate name"""
    from unittest.mock import patch
    from services.deck_service import DuplicateDeckNameError
    
    update_data = {
        "deck_name": "Spanish"
    }
    
    with patch("routes.decks.deck_service.update_deck") as mock_update:
        mock_update.side_effect = DuplicateDeckNameError("Deck name already exists")
        
        response = client.put(
            f"/decks/{deck_id}",
            data=json.dumps(update_data),
            content_type="application/json",
            headers=auth_headers
        )
        
        assert response.status_code == 409
        result = json.loads(response.data)
        assert "error" in result


def test_update_deck_database_error(client, auth_headers, deck_id):
    """Test updating deck when database error occurs"""
    from unittest.mock import patch
    from services.deck_service import DatabaseError
    
    update_data = {
        "deck_name": "Updated Name"
    }
    
    with patch("routes.decks.deck_service.update_deck") as mock_update:
        mock_update.side_effect = DatabaseError("DB error")
        
        response = client.put(
            f"/decks/{deck_id}",
            data=json.dumps(update_data),
            content_type="application/json",
            headers=auth_headers
        )
        
        assert response.status_code == 500
        result = json.loads(response.data)
        assert "error" in result


def test_delete_deck_database_error(client, auth_headers, deck_id):
    """Test deleting deck when database error occurs"""
    from unittest.mock import patch
    from services.deck_service import DatabaseError
    
    with patch("routes.decks.deck_service.delete_deck") as mock_delete:
        mock_delete.side_effect = DatabaseError("DB error")
        
        response = client.delete(f"/decks/{deck_id}", headers=auth_headers)
        
        assert response.status_code == 500
        result = json.loads(response.data)
        assert "error" in result
