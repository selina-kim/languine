"""Integration tests for card routes.

Tests the card management endpoints with actual HTTP requests and responses.
These tests verify the complete request/response cycle including:
- Card CRUD operations (create, read, update, delete)
- Deck-level card queries with pagination
- Authentication and authorization
- Database interactions
- Input validation and error handling

All tests in this file are marked as integration tests.

Run this test file:
    docker compose exec backend pytest src/tests/test_card_integration.py -v -m integration

Run with coverage:
    docker compose exec backend pytest src/tests/test_card_integration.py --cov=routes.cards -m integration
"""

import pytest
import json

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("mock_tts_for_integration")]


# ==================== Card Creation Tests ====================


def test_create_card_success(client, auth_headers, deck_id):
    """Test successful card creation."""
    card_data = {
        "word": "안녕하세요",
        "translation": "hello",
        "definition": "A polite greeting",
        "word_example": "안녕하세요, 반갑습니다",
        "trans_example": "Hello, nice to meet you"
    }
    
    response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    assert "card" in result
    assert result["card"]["word"] == "안녕하세요"
    assert result["card"]["translation"] == "hello"


def test_create_card_missing_word(client, auth_headers, deck_id):
    """Test card creation fails without required word field."""
    card_data = {
        "translation": "thank you"
    }
    
    response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "Missing required field" in result["error"]


def test_create_card_missing_translation(client, auth_headers, deck_id):
    """Test card creation fails without required translation field."""
    card_data = {
        "word": "Bonjour"
    }
    
    response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "Missing required field" in result["error"]


def test_create_card_no_data(client, auth_headers, deck_id):
    """Test card creation fails with no data."""
    response = client.post(
        f"/decks/{deck_id}/card",
        data="",
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "No data provided" in result["error"]


def test_create_card_deck_not_found(client, auth_headers):
    """Test card creation fails for non-existent deck."""
    card_data = {
        "word": "谢谢",
        "translation": "thank you"
    }
    
    response = client.post(
        "/decks/9999/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_create_card_unauthorized(client, deck_id):
    """Test card creation fails without auth token."""
    card_data = {
        "word": "Merci",
        "translation": "thank you"
    }
    
    response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json'
    )
    
    assert response.status_code == 401


# ==================== Card Retrieval Tests ====================


def test_get_card_success(client, auth_headers, deck_id):
    """Test successful card retrieval."""
    card_data = {
        "word": "你好",
        "translation": "hello"
    }
    
    create_response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    card_id = json.loads(create_response.data)["card"]["c_id"]

    response = client.get(f"/decks/{deck_id}/cards/{card_id}", headers=auth_headers)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["word"] == "你好"
    assert result["translation"] == "hello"


def test_get_card_not_found(client, auth_headers, deck_id):
    """Test card retrieval for non-existent card."""
    response = client.get(f"/decks/{deck_id}/cards/9999", headers=auth_headers)

    assert response.status_code == 404


def test_get_card_wrong_deck(client, auth_headers):
    """Test card retrieval with wrong deck ID."""
    response = client.get("/decks/9999/cards/1", headers=auth_headers)
    
    assert response.status_code == 404


def test_get_card_unauthorized(client, deck_id):
    """Test card retrieval fails without auth token."""
    response = client.get(f"/decks/{deck_id}/cards/1")

    assert response.status_code == 401


# ==================== Card Update Tests ====================


def test_update_card_success(client, auth_headers, deck_id):
    """Test successful card update."""
    # First create a card to update
    card_data = {
        "word": "Bonjour",
        "translation": "hello"
    }
    
    create_response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    card_id = json.loads(create_response.data)["card"]["c_id"]
    
    # Now update it
    update_data = {
        "definition": "Updated definition"
    }
    
    response = client.post(
        f"/decks/{deck_id}/cards/{card_id}",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["card"]["definition"] == "Updated definition"


def test_update_card_word(client, auth_headers, deck_id):
    """Test updating card word field."""
    # First create a card to update
    card_data = {
        "word": "ありがとう",
        "translation": "thank you"
    }
    
    create_response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    card_id = json.loads(create_response.data)["card"]["c_id"]
    
    # Now update the word
    update_data = {
        "word": "どうも"
    }
    
    response = client.post(
        f"/decks/{deck_id}/cards/{card_id}",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["card"]["word"] == "どうも"


def test_update_card_not_found(client, auth_headers, deck_id):
    """Test update for non-existent card."""
    update_data = {
        "definition": "Updated"
    }
    
    response = client.post(
        f"/decks/{deck_id}/cards/9999",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_update_card_no_data(client, auth_headers, deck_id):
    """Test update with no data."""
    response = client.post(
        f"/decks/{deck_id}/cards/1",
        data="",
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "No data provided" in result["error"]


def test_update_card_unauthorized(client, deck_id):
    """Test update fails without auth token."""
    update_data = {
        "definition": "Updated"
    }
    
    response = client.post(
        f"/decks/{deck_id}/cards/1",
        data=json.dumps(update_data),
        content_type='application/json'
    )
    
    assert response.status_code == 401


# ==================== Card Deletion Tests ====================


def test_delete_card_success(client, auth_headers, deck_id):
    """Test successful card deletion."""
    # First create a card to delete
    card_data = {
        "word": "감사합니다",
        "translation": "thank you"
    }
    
    create_response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    card_id = json.loads(create_response.data)["card"]["c_id"]
    
    # Now delete it
    response = client.delete(f"/decks/{deck_id}/cards/{card_id}", headers=auth_headers)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert "deleted" in result["message"].lower()
    
    # Verify it's gone
    get_response = client.get(f"/decks/{deck_id}/cards/{card_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_delete_card_not_found(client, auth_headers, deck_id):
    """Test delete for non-existent card."""
    response = client.delete(f"/decks/{deck_id}/cards/9999", headers=auth_headers)

    assert response.status_code == 404


def test_delete_card_unauthorized(client, deck_id):
    """Test delete fails without auth token."""
    response = client.delete(f"/decks/{deck_id}/cards/1")

    assert response.status_code == 401


# ==================== Deck-Level Card Queries ====================


def test_get_deck_cards_success(client, auth_headers, deck_id):
    """Test successful retrieval of all cards in a deck."""
    response = client.get(f"/decks/{deck_id}/cards", headers=auth_headers)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert "cards" in result
    assert "pagination" in result
    assert len(result["cards"]) >= 1


def test_get_deck_cards_pagination(client, auth_headers, deck_id):
    """Test pagination parameters for deck cards."""
    response = client.get(f"/decks/{deck_id}/cards?page=1&per_page=10", headers=auth_headers)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["per_page"] == 10


def test_get_deck_cards_deck_not_found(client, auth_headers):
    """Test cards retrieval for non-existent deck."""
    response = client.get("/decks/9999/cards", headers=auth_headers)
    
    assert response.status_code == 404


def test_get_deck_cards_unauthorized(client, deck_id):
    """Test cards retrieval fails without auth token."""
    response = client.get(f"/decks/{deck_id}/cards")

    assert response.status_code == 401


def test_create_multiple_cards(client, auth_headers, deck_id):
    """Test creating multiple cards in a deck."""
    cards = [
        {"word": "一", "translation": "one"},
        {"word": "二", "translation": "two"},
        {"word": "三", "translation": "three"}
    ]
    
    for card_data in cards:
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code == 201
    
    # Verify all cards are in the deck
    response = client.get(f"/decks/{deck_id}/cards", headers=auth_headers)
    result = json.loads(response.data)
    assert result["pagination"]["total"] >= 4  # 1 from setup + 3 new


# ==================== Card Field Combinations ====================


def test_card_fields_preserved(client, auth_headers, deck_id):
    """Test that all optional fields are preserved."""
    card_data = {
        "word": "고양이",
        "translation": "cat",
        "word_roman": "go-yang-i",
        "definition": "A small feline",
        "word_example": "고양이가 귀여워요",
        "trans_example": "The cat is cute",
        "trans_roman": "kat"
    }
    
    response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    card = result["card"]
    
    assert card["word"] == "고양이"
    assert card["translation"] == "cat"
    assert card["word_roman"] == "go-yang-i"
    assert card["definition"] == "A small feline"
    assert card["word_example"] == "고양이가 귀여워요"
    assert card["trans_example"] == "The cat is cute"
    assert card["trans_roman"] == "kat"


def test_card_with_definition_only(client, auth_headers, deck_id):
    """Test creating card with definition but no examples."""
    card_data = {
        "word": "Liberté",
        "translation": "freedom",
        "definition": "The state of being free; liberty, independence"
    }
    
    response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    card = result["card"]
    
    assert card["word"] == "Liberté"
    assert card["translation"] == "freedom"
    assert card["definition"] == "The state of being free; liberty, independence"
    assert card["word_example"] is None


def test_card_with_examples_only(client, auth_headers, deck_id):
    """Test creating card with examples but no definition."""
    card_data = {
        "word": "食べる",
        "translation": "to eat",
        "word_example": "朝ごはんを食べる",
        "trans_example": "to eat breakfast"
    }
    
    response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    card = result["card"]
    
    assert card["word"] == "食べる"
    assert card["translation"] == "to eat"
    assert card["word_example"] == "朝ごはんを食べる"
    assert card["trans_example"] == "to eat breakfast"
    assert card["definition"] is None


def test_card_with_long_definition(client, auth_headers, deck_id):
    """Test creating card with lengthy definition text."""
    card_data = {
        "word": "Schadenfreude",
        "translation": "schadenfreude",
        "definition": "A German word meaning pleasure derived from the misfortunes of others. This emotional experience involves feeling joy or satisfaction when witnessing someone else's troubles, failures, or humiliation. It's a complex emotion that reflects aspects of human psychology and social behavior."
    }
    
    response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    card = result["card"]
    
    assert card["word"] == "Schadenfreude"
    assert len(card["definition"]) > 100  # Verify long text is preserved
    assert "German word" in card["definition"]


# --- Field Update Tests ---

def test_update_card_add_examples(client, auth_headers, deck_id):
    """Test adding examples to existing card."""
    # Create basic card
    card_data = {
        "word": "Belle",
        "translation": "beautiful"
    }
    
    create_response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    card_id = json.loads(create_response.data)["card"]["c_id"]
    
    # Add examples
    update_data = {
        "word_example": "Une belle journée",
        "trans_example": "A beautiful day"
    }
    
    update_response = client.post(
        f"/decks/{deck_id}/cards/{card_id}",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert update_response.status_code == 200
    result = json.loads(update_response.data)
    assert result["card"]["word_example"] == "Une belle journée"
    assert result["card"]["trans_example"] == "A beautiful day"


def test_card_with_special_characters(client, auth_headers, deck_id):
    """Test creating card with various special characters."""
    card_data = {
        "word": "Ça va?",
        "translation": "How are you?",
        "word_example": "Salut! Ça va bien?",
        "trans_example": "Hi! Are you doing well?"
    }
    
    response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    card = result["card"]
    
    # Verify special characters are preserved
    assert card["word"] == "Ça va?"
    assert "ç" in card["word"].lower()
    assert card["word_example"] == "Salut! Ça va bien?"


def test_update_multiple_fields(client, auth_headers, deck_id):
    """Test updating multiple fields at once."""
    # First create a card to update
    card_data = {
        "word": "original",
        "translation": "original"
    }
    
    create_response = client.post(
        f"/decks/{deck_id}/card",
        data=json.dumps(card_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    card_id = json.loads(create_response.data)["card"]["c_id"]
    
    # Now update multiple fields
    update_data = {
        "word": "Au revoir",
        "translation": "goodbye",
        "definition": "French farewell"
    }
    
    response = client.post(
        f"/decks/{deck_id}/cards/{card_id}",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    card = result["card"]
    
    assert card["word"] == "Au revoir"
    assert card["translation"] == "goodbye"
    assert card["definition"] == "French farewell"


# ==================== Review System Tests ====================


def test_get_cards_for_review_success(client, auth_headers, deck_id):
    """Test retrieving cards due for review."""
    response = client.get(f"/decks/{deck_id}/review", headers=auth_headers)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert "cards" in result
    assert isinstance(result["cards"], list)


def test_get_cards_for_review_with_limit(client, auth_headers, deck_id):
    """Test review endpoint respects limit parameter."""
    response = client.get(f"/decks/{deck_id}/review?limit=5", headers=auth_headers)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert len(result["cards"]) <= 5


def test_get_cards_for_review_limit_clamping(client, auth_headers, deck_id):
    """Test that limit is clamped between 1 and 100."""
    # Test limit too high
    response = client.get(f"/decks/{deck_id}/review?limit=200", headers=auth_headers)
    assert response.status_code == 200
    result = json.loads(response.data)
    assert len(result["cards"]) <= 100
    
    # Test limit too low (should default to 1)
    response = client.get(f"/decks/{deck_id}/review?limit=0", headers=auth_headers)
    assert response.status_code == 200


def test_get_cards_for_review_deck_not_found(client, auth_headers):
    """Test review endpoint with non-existent deck."""
    response = client.get("/decks/99999/review", headers=auth_headers)
    
    assert response.status_code == 404
    result = json.loads(response.data)
    assert "error" in result


def test_get_cards_for_review_unauthorized(client, deck_id):
    """Test review endpoint without authentication."""
    response = client.get(f"/decks/{deck_id}/review")

    assert response.status_code == 401


def test_get_cards_for_review_empty_deck(client, auth_headers, deck_id):
    """Test review endpoint with deck that has no cards."""
    # This test assumes deck 1 is empty or has no due cards
    response = client.get(f"/decks/{deck_id}/review", headers=auth_headers)

    assert response.status_code == 200
    result = json.loads(response.data)
    # Result may be empty or have cards depending on test data
    assert "cards" in result
    assert isinstance(result["cards"], list)


# ==================== Pagination Edge Cases ====================


def test_get_deck_cards_negative_page(client, auth_headers, deck_id):
    """Test that negative page numbers are handled gracefully by clamping to page 1."""
    response = client.get(f"/decks/{deck_id}/cards?page=-1", headers=auth_headers)

    # Should clamp to page 1 and return successfully
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["pagination"]["page"] == 1  # Clamped to minimum


def test_get_deck_cards_zero_per_page(client, auth_headers, deck_id):
    """Test that zero per_page is handled gracefully by clamping to minimum value."""
    response = client.get(f"/decks/{deck_id}/cards?per_page=0", headers=auth_headers)

    # Should clamp to minimum (1) and return successfully
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["pagination"]["per_page"] >= 1  # Clamped to minimum


def test_get_deck_cards_excessive_per_page(client, auth_headers, deck_id):
    """Test that excessively large per_page values are clamped to maximum."""
    response = client.get(f"/decks/{deck_id}/cards?per_page=10000", headers=auth_headers)

    # Should clamp to maximum (200) and return successfully
    assert response.status_code == 200
    result = json.loads(response.data)
    assert "cards" in result
    assert "pagination" in result
    assert result["pagination"]["per_page"] <= 200  # Clamped to maximum


# ==================== MinIO Integration Tests ====================

class TestImageIntegration:
    """Integration tests for image upload with MinIO."""

    def test_create_card_with_image_url(self, client, auth_headers, deck_id):
        """Test card creation with image URL."""
        # Using a real image URL that should be accessible
        card_data = {
            "word": "猫",
            "translation": "cat",
            "image": "https://picsum.photos/200/300.jpg"  # Placeholder image service
        }
        
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        card = result["card"]
        
        # Card should be created successfully
        assert card["word"] == "猫"
        
        # Image field should either contain MinIO path or None (if MinIO unavailable)
        # Both outcomes are acceptable depending on MinIO availability
        assert "image" in card
        if card["image"]:
            # If image was stored, it should follow naming convention
            assert "images/card_" in card["image"] or card["image"].startswith("images/")

    def test_create_card_with_invalid_image_url(self, client, auth_headers, deck_id):
        """Test card creation with invalid/unreachable image URL."""
        card_data = {
            "word": "犬",
            "translation": "dog",
            "image": "http://this-domain-does-not-exist-12345.com/image.jpg"
        }
        
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Card should still be created even if image download fails
        assert response.status_code == 201
        result = json.loads(response.data)
        card = result["card"]
        
        assert card["word"] == "犬"
        # Image URL is stored as-is (download failures don't prevent storage)
        assert card["image"] == "http://this-domain-does-not-exist-12345.com/image.jpg"
    
    def test_update_card_with_image_url(self, client, auth_headers, deck_id):
        """Test updating card with new image URL."""
        # First create a card
        card_data = {
            "word": "Maison",
            "translation": "house"
        }
        
        create_response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        card_id = json.loads(create_response.data)["card"]["c_id"]
        
        # Update with image URL
        update_data = {
            "image": "https://picsum.photos/200/300.jpg"
        }
        
        update_response = client.post(
            f"/decks/{deck_id}/cards/{card_id}",
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        result = json.loads(update_response.data)
        
        # Image field should be updated (or None if MinIO unavailable)
        assert "image" in result["card"]

    def test_update_card_remove_image(self, client, auth_headers, deck_id):
        """Test removing image from card by setting to None/empty."""
        # Create card with image placeholder
        card_data = {
            "word": "책",
            "translation": "book",
            "image": "https://picsum.photos/200/300.jpg"
        }
        
        create_response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        card_id = json.loads(create_response.data)["card"]["c_id"]
        
        # Update to remove image
        update_data = {"image": None}
        
        update_response = client.post(
            f"/decks/{deck_id}/cards/{card_id}",
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        result = json.loads(update_response.data)
        # Image should be removed (set to None/NULL)
        assert result["card"]["image"] is None

    def test_delete_card_with_image(self, client, auth_headers, deck_id):
        """Test that deleting card handles image cleanup."""
        # Create card with image
        card_data = {
            "word": "テーブル",
            "translation": "table",
            "image": "https://picsum.photos/200/300.jpg"
        }
        
        create_response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        card_id = json.loads(create_response.data)["card"]["c_id"]
        
        # Delete the card
        delete_response = client.delete(
            f"/decks/{deck_id}/cards/{card_id}",
            headers=auth_headers
        )
        
        # Should delete successfully (image cleanup handled internally)
        assert delete_response.status_code == 200
        
        # Verify card is actually deleted
        get_response = client.get(
            f"/decks/{deck_id}/cards/{card_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_create_card_with_placeholder_image(self, client, auth_headers, deck_id):
        """Test that placeholder/non-URL images are not treated as URLs."""
        card_data = {
            "word": "Eau",
            "translation": "water",
            "image": "PLACEHOLDER"
        }
        
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        
        # Non-URL strings are not treated as valid images (stored as None)
        assert result["card"]["image"] is None


# ==================== TTS Integration Tests ====================

class TestTTSIntegration:
    """Integration tests for TTS audio generation."""

    def test_create_card_with_tts(self, client, auth_headers, deck_id):
        """Test card creation attempts TTS generation."""
        card_data = {
            "word": "おはよう",
            "translation": "good morning"
        }
        
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        card = result["card"]
        
        # Audio fields should be present (may be None if TTS/MinIO unavailable)
        assert "word_audio" in card
        assert "trans_audio" in card
        
        # If TTS is available, audio paths should follow naming convention
        if card["word_audio"]:
            assert "audio/card_" in card["word_audio"] and "_word.wav" in card["word_audio"]
        if card["trans_audio"]:
            assert "audio/card_" in card["trans_audio"] and "_translation.wav" in card["trans_audio"]

    def test_update_card_word_regenerates_tts(self, client, auth_headers, deck_id):
        """Test updating word field triggers TTS regeneration."""
        # Create initial card
        card_data = {
            "word": "네",
            "translation": "yes"
        }
        
        create_response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        card_id = json.loads(create_response.data)["card"]["c_id"]
        original_audio = json.loads(create_response.data)["card"]["word_audio"]
        
        # Verify audio was generated on creation
        assert original_audio is not None, "Audio should have been generated on card creation"
        expected_path = f"audio/card_{card_id}_word.wav"
        assert original_audio == expected_path
        
        # Update the word
        update_data = {"word": "아니요"}
        
        update_response = client.post(
            f"/decks/{deck_id}/cards/{card_id}",
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        result = json.loads(update_response.data)
        
        # Word should be updated
        assert result["card"]["word"] == "아니요"
        
        # Verify audio was regenerated (same path, new content)
        assert result["card"]["word_audio"] == expected_path, \
            f"Audio should be regenerated at same path: {expected_path}"

    def test_update_card_definition_preserves_tts(self, client, auth_headers, deck_id):
        """Test updating non-audio fields doesn't change TTS."""
        # Create card
        card_data = {
            "word": "可能",
            "translation": "maybe"
        }
        
        create_response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        card_id = json.loads(create_response.data)["card"]["c_id"]
        original_word_audio = json.loads(create_response.data)["card"]["word_audio"]
        
        # Verify audio was generated
        assert original_word_audio is not None, "Audio should have been generated"
        
        # Update only definition (non-audio field)
        update_data = {"definition": "perhaps, possibly"}
        
        update_response = client.post(
            f"/decks/{deck_id}/cards/{card_id}",
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        result = json.loads(update_response.data)
        
        # Audio should remain unchanged
        assert result["card"]["word_audio"] == original_word_audio

    def test_delete_card_with_audio(self, client, auth_headers, deck_id):
        """Test deleting card handles audio cleanup."""
        # Create card with audio
        card_data = {
            "word": "さようなら",
            "translation": "goodbye"
        }
        
        create_response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        card_id = json.loads(create_response.data)["card"]["c_id"]
        
        # Delete card
        delete_response = client.delete(
            f"/decks/{deck_id}/cards/{card_id}",
            headers=auth_headers
        )
        
        # Should delete successfully (audio cleanup handled internally)
        assert delete_response.status_code == 200

    def test_tts_with_accented_characters(self, client, auth_headers, deck_id):
        """Test TTS handles accented and special characters."""
        card_data = {
            "word": "Garçon",
            "translation": "boy"
        }
        
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result["card"]["word"] == "Garçon"

    def test_tts_with_long_text(self, client, auth_headers, deck_id):
        """Test TTS handles longer text passages."""
        card_data = {
            "word": "저는 서울에 살고 있습니다",
            "translation": "I live in Seoul"
        }
        
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 201


# ==================== FSRS Scheduling Tests ====================
# Tests for FSRS (Free Spaced Repetition Scheduler) fields and defaults

class TestFSRSIntegration:
    """Integration tests for FSRS scheduling fields."""

    def test_card_has_fsrs_fields(self, client, auth_headers, deck_id):
        """Test that card response includes FSRS scheduling fields."""
        # First create a card to test
        card_data = {
            "word": "テスト",
            "translation": "test"
        }
        
        create_response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        card_id = json.loads(create_response.data)["card"]["c_id"]
        
        # Fetch the card
        response = client.get(f"/decks/{deck_id}/cards/{card_id}", headers=auth_headers)

        assert response.status_code == 200
        result = json.loads(response.data)
        
        # FSRS fields should be present
        assert "learning_state" in result
        assert "step" in result
        assert "difficulty" in result
        assert "stability" in result
        assert "due_date" in result

    def test_new_card_default_fsrs_values(self, client, auth_headers, deck_id):
        """Test that new cards have default FSRS values."""
        card_data = {
            "word": "新しい",
            "translation": "new"
        }
        
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 201
        card = json.loads(response.data)["card"]
        
        # Fetch the card to verify all FSRS defaults
        card_id = card["c_id"]

        get_response = client.get(f"/decks/{deck_id}/cards/{card_id}", headers=auth_headers)
        assert get_response.status_code == 200
        result = json.loads(get_response.data)
        
        # New cards have NULL/None for most FSRS fields until first review
        # Only successful_reps and fail_count have defaults (0)
        assert "learning_state" in result
        assert "step" in result
        assert "difficulty" in result
        assert "stability" in result
        assert "due_date" in result
        assert "last_review" in result
        
        # These fields have database defaults
        assert result["successful_reps"] == 0
        assert result["fail_count"] == 0
        
        # last_review should be None for new cards
        assert result["last_review"] is None


# ==================== Image Retrieval Endpoint Tests ====================
# Tests for GET /cards/image/<object_id> endpoint

class TestImageRetrievalEndpoint:
    """Tests for the card image retrieval endpoint."""
    
    def test_get_card_image_with_minios_object_id(self, client):
        """Test retrieving image from MinIO with valid object ID."""
        # Use a valid MinIO object ID format
        object_id = "images/card_123_image.jpg"
        
        response = client.get(f"/cards/image/{object_id}")
        
        # Should return 404 since object doesn't exist or 503 if MinIO unavailable
        assert response.status_code in [404, 503]
    
    def test_get_card_image_with_minio_unavailable(self, client):
        """Test image endpoint when MinIO is not available."""
        object_id = "images/nonexistent.jpg"
        
        response = client.get(f"/cards/image/{object_id}")
        
        # Should return 404 for missing object or 503 for unavailable service
        assert response.status_code in [404, 503]
    
    def test_get_card_image_with_legacy_external_url(self, client):
        """Test backward compatibility with legacy URL-encoded external URLs."""
        # Test with URL-encoded https URL (legacy stored format)
        external_url = "https%3A%2F%2Fpicsum.photos%2F200%2F300.jpg"
        
        response = client.get(f"/cards/image/{external_url}")
        
        # Should attempt to fetch from external URL
        # May return 200 with image or fail if external URL unreachable
        assert response.status_code in [200, 404, 503, 500]
    
    def test_get_card_image_with_encoded_http_url(self, client):
        """Test backward compatibility with HTTP URLs."""
        # Test with URL-encoded http URL
        external_url = "http%3A%2F%2Fexample.com%2Fimage.jpg"
        
        response = client.get(f"/cards/image/{external_url}")
        
        # Should attempt to fetch or return error
        assert response.status_code in [404, 500]
    
    def test_get_card_image_with_plain_minio_path(self, client):
        """Test with plain MinIO path format."""
        # Test with non-URL MinIO object ID
        minio_id = "cards/card_456_image"
        
        response = client.get(f"/cards/image/{minio_id}")
        
        # Should try to fetch from MinIO
        assert response.status_code in [404, 503]
    
    def test_get_card_image_content_type_for_jpeg(self, client):
        """Test that JPEG images return correct content type."""

        object_id = "images/test.jpg"
        
        response = client.get(f"/cards/image/{object_id}")
        
        # If image exists, should have image content type
        if response.status_code == 200:
            assert "image" in response.content_type
    
    def test_get_card_image_with_special_characters_in_path(self, client):
        """Test image retrieval with special characters in object ID."""
        object_id = "images/card_special%20chars.jpg"
        
        response = client.get(f"/cards/image/{object_id}")
        
        # Should handle URL encoding properly
        assert response.status_code in [404, 503, 500]
    
    def test_get_card_image_with_nested_path(self, client):
        """Test image retrieval with nested directory path."""
        object_id = "images/cards/nested/image.jpg"
        
        response = client.get(f"/cards/image/{object_id}")
        
        # Should handle nested paths
        assert response.status_code in [404, 503]
    
    def test_get_card_image_with_empty_object_id(self, client):
        """Test image endpoint with empty object ID."""
        response = client.get("/cards/image/")
        
        # Should return 404 for empty path
        assert response.status_code == 404
    
    def test_get_card_image_with_invalid_url_format(self, client):
        """Test with invalid URL in legacy format."""
        # Test with malformed URL that doesn't start with http
        invalid_url = "https%3Amalformed"
        
        response = client.get(f"/cards/image/{invalid_url}")
        
        # Should handle gracefully
        assert response.status_code in [404, 500, 503]


# ==================== Error Handling and Edge Cases ====================

class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_create_card_with_empty_required_field(self, client, auth_headers, deck_id):
        """Test card creation with empty required fields."""
        card_data = {
            "word": "   ",  # Whitespace only
            "translation": "hello"
        }
        
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 400
        result = json.loads(response.data)
        assert "Missing required field" in result["error"] or "required" in result["error"].lower()
    
    def test_create_card_with_empty_translation(self, client, auth_headers, deck_id):
        """Test card creation with empty translation field."""
        card_data = {
            "word": "hello",
            "translation": ""
        }
        
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 400
        result = json.loads(response.data)
        assert "Missing required field" in result["error"] or "required" in result["error"].lower()
    
    def test_get_card_with_large_ids(self, client, auth_headers, deck_id):
        """Test get_card handles very large card IDs gracefully."""
        # Try to get a card with very large IDs
        response = client.get(f"/decks/{deck_id}/cards/999999999", headers=auth_headers)
        
        # Should return 404 since card doesn't exist
        assert response.status_code == 404
    
    def test_update_card_with_empty_fields(self, client, auth_headers, deck_id):
        """Test update with empty string and None values."""
        # Create a card first
        card_data = {
            "word": "test",
            "translation": "test"
        }
        
        create_response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        card_id = json.loads(create_response.data)["card"]["c_id"]
        
        # Update with empty string and None values (should be accepted)
        update_data = {
            "word_roman": "",  # Empty string
            "definition": None  # None value
        }
        
        response = client.post(
            f"/decks/{deck_id}/cards/{card_id}",
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Should succeed (empty/null values are accepted)
        assert response.status_code == 200
    
    def test_pagination_with_invalid_types(self, client, auth_headers, deck_id):
        """Test pagination with invalid parameter types."""
        # Send non-integer pagination values
        response = client.get(f"/decks/{deck_id}/cards?page=invalid&per_page=abc", headers=auth_headers)
        
        # Invalid values default to defaults (200)
        assert response.status_code == 200
    
    def test_review_endpoint_with_invalid_limit_type(self, client, auth_headers, deck_id):
        """Test review endpoint with invalid limit type."""
        response = client.get(f"/decks/{deck_id}/review?limit=not-a-number", headers=auth_headers)
        
        # Invalid values default to defaults (200)
        assert response.status_code == 200
    
    def test_deck_not_found_error_consistency(self, client, auth_headers):
        """Test that all endpoints handle deck not found consistently."""
        nonexistent_deck = 99999
        
        # Test create
        card_data = {"word": "test", "translation": "test"}
        create_resp = client.post(
            f"/decks/{nonexistent_deck}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        assert create_resp.status_code == 404
        
        # Test get cards
        get_cards_resp = client.get(f"/decks/{nonexistent_deck}/cards", headers=auth_headers)
        assert get_cards_resp.status_code == 404
        
        # Test review
        review_resp = client.get(f"/decks/{nonexistent_deck}/review", headers=auth_headers)
        assert review_resp.status_code == 404


# ==================== Response Format Tests ====================

class TestResponseFormat:
    """Tests for response formatting and structure."""
    
    def test_create_card_response_structure(self, client, auth_headers, deck_id):
        """Test that create response has correct structure."""
        card_data = {
            "word": "структура",
            "translation": "structure"
        }
        
        response = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        
        # Should have message and card
        assert "message" in result
        assert "card" in result
        assert "Card created successfully" in result["message"]
    
    def test_update_card_response_structure(self, client, auth_headers, deck_id):
        """Test that update response has correct structure."""
        # Create a card first
        card_data = {"word": "test", "translation": "test"}
        create_resp = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        card_id = json.loads(create_resp.data)["card"]["c_id"]
        
        # Update it
        update_data = {"definition": "test definition"}
        response = client.post(
            f"/decks/{deck_id}/cards/{card_id}",
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = json.loads(response.data)
        
        # Should have message and card
        assert "message" in result
        assert "card" in result
        assert "updated" in result["message"].lower()
    
    def test_delete_card_response_structure(self, client, auth_headers, deck_id):
        """Test that delete response has correct structure."""
        # Create a card first
        card_data = {"word": "test", "translation": "test"}
        create_resp = client.post(
            f"/decks/{deck_id}/card",
            data=json.dumps(card_data),
            content_type='application/json',
            headers=auth_headers
        )
        card_id = json.loads(create_resp.data)["card"]["c_id"]
        
        # Delete it
        response = client.delete(f"/decks/{deck_id}/cards/{card_id}", headers=auth_headers)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        
        # Should have message
        assert "message" in result
        assert "deleted" in result["message"].lower()
    
    def test_error_response_has_error_field(self, client, auth_headers, deck_id):
        """Test that error responses have error field."""
        # Try invalid request
        response = client.post(
            f"/decks/{deck_id}/card",
            data="",
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert "error" in result
