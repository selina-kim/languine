"""Unit tests for DeckService.

Tests the deck import/export service logic without external dependencies:
- Data format transformations (JSON, CSV, Anki)
- Export functionality (deck data to various formats)
- Import functionality (parsing various formats to deck data)
- Data validation and error handling
- Edge cases (empty data, invalid formats, malformed input)
- No database, HTTP, or authentication dependencies

Run this test file:
    docker compose exec backend pytest src/tests/test_decks_unit.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_decks_unit.py --cov=services.deck_service
"""

import pytest
import json
from services.deck_service import DeckService


@pytest.fixture
def sample_deck_data():
    """Sample deck data for testing"""
    return {
        "deck": {
            "deck_name": "Spanish Basics",
            "word_lang": "Spanish",
            "trans_lang": "English",
            "description": "Basic Spanish vocabulary",
            "creation_date": "2026-01-30T00:00:00"
        },
        "cards": [
            {
                "word": "hola",
                "translation": "hello",
                "definition": "A greeting",
                "word_example": "Hola, ¿cómo estás?",
                "trans_example": "Hello, how are you?",
                "word_roman": "oh-lah",
                "trans_roman": "",
                "image": ""
            },
            {
                "word": "adiós",
                "translation": "goodbye",
                "definition": "A farewell",
                "word_example": "Adiós, hasta luego",
                "trans_example": "Goodbye, see you later",
                "word_roman": "ah-dee-ohs",
                "trans_roman": "",
                "image": ""
            }
        ]
    }


class TestDeckExport:
    """Tests for deck export functionality"""
    
    def test_export_to_json_success(self, sample_deck_data):
        """Test successful JSON export"""
        result = DeckService.export_deck_to_json(sample_deck_data)
        
        assert result is not None
        data = json.loads(result)
        assert data["format"] == "capstone_deck_v1"
        assert "exported_at" in data
        assert data["deck"]["deck_name"] == "Spanish Basics"
        assert len(data["cards"]) == 2
        assert data["cards"][0]["word"] == "hola"
    
    def test_export_to_json_empty_cards(self):
        """Test JSON export with no cards"""
        deck_data = {
            "deck": {"deck_name": "Empty", "word_lang": "en", "trans_lang": "es"},
            "cards": []
        }
        result = DeckService.export_deck_to_json(deck_data)
        data = json.loads(result)
        assert len(data["cards"]) == 0
    
    def test_export_to_csv_success(self, sample_deck_data):
        """Test successful CSV export"""
        result = DeckService.export_deck_to_csv(sample_deck_data)
        
        assert result is not None
        lines = result.strip().split('\n')
        assert len(lines) == 3  # header + 2 cards
        assert "word,translation" in lines[0]
        assert "hola,hello" in lines[1]
    
    def test_export_to_csv_empty_cards(self):
        """Test CSV export with no cards returns empty string"""
        deck_data = {"deck": {}, "cards": []}
        result = DeckService.export_deck_to_csv(deck_data)
        assert result == ""
    
    def test_export_to_anki_success(self, sample_deck_data):
        """Test successful Anki export"""
        result = DeckService.export_deck_to_anki(sample_deck_data)
        
        assert result is not None
        lines = result.strip().split('\n')
        
        # Check metadata comments
        assert any("#deck:" in line for line in lines)
        assert any("#tags:" in line for line in lines)
        
        # Check cards are tab-separated
        card_lines = [l for l in lines if not l.startswith('#')]
        assert len(card_lines) == 2
        assert "hola\thello" in card_lines[0]
    
    def test_export_to_anki_with_definition(self):
        """Test Anki export includes definition in extra field"""
        deck_data = {
            "deck": {"deck_name": "Test", "word_lang": "es", "trans_lang": "en"},
            "cards": [{
                "word": "test",
                "translation": "prueba",
                "definition": "A trial",
                "word_example": "",
                "trans_example": "",
                "word_roman": "",
                "trans_roman": "",
                "image": ""
            }]
        }
        result = DeckService.export_deck_to_anki(deck_data)
        assert "<b>Definition:</b> A trial" in result


class TestDeckImport:
    """Tests for deck import functionality"""
    
    def test_import_from_json_success(self, sample_deck_data):
        """Test successful JSON import"""
        json_data = DeckService.export_deck_to_json(sample_deck_data)
        result = DeckService.import_deck_from_json(json_data)
        
        assert result["deck"]["deck_name"] == "Spanish Basics"
        assert len(result["cards"]) == 2
        assert result["cards"][0]["word"] == "hola"
    
    def test_import_from_json_invalid_format(self):
        """Test JSON import with invalid format"""
        with pytest.raises(ValueError, match="Invalid JSON format"):
            DeckService.import_deck_from_json("not valid json")
    
    def test_import_from_json_missing_deck_field(self):
        """Test JSON import missing required deck field"""
        invalid_data = json.dumps({"cards": []})
        with pytest.raises(ValueError, match="Missing 'deck' or 'cards' field"):
            DeckService.import_deck_from_json(invalid_data)
    
    def test_import_from_json_missing_required_deck_info(self):
        """Test JSON import with missing required deck info"""
        invalid_data = json.dumps({
            "deck": {"deck_name": "Test"},
            "cards": []
        })
        with pytest.raises(ValueError, match="Missing required deck field"):
            DeckService.import_deck_from_json(invalid_data)
    
    def test_import_from_json_invalid_card_structure(self):
        """Test JSON import with invalid card structure"""
        invalid_data = json.dumps({
            "deck": {"deck_name": "Test", "word_lang": "es", "trans_lang": "en"},
            "cards": [{"word": "test"}]  # missing translation
        })
        with pytest.raises(ValueError, match="missing required fields"):
            DeckService.import_deck_from_json(invalid_data)
    
    def test_import_from_csv_success(self):
        """Test successful CSV import"""
        csv_data = """word,translation,definition,word_example,trans_example,word_roman,trans_roman,image
hola,hello,A greeting,Hola!,Hello!,oh-lah,,
adiós,goodbye,A farewell,Adiós,Goodbye,ah-dee-ohs,,"""
        
        result = DeckService.import_deck_from_csv(
            csv_data, "Spanish Basics", "Spanish", "English"
        )
        
        assert result["deck"]["deck_name"] == "Spanish Basics"
        assert len(result["cards"]) == 2
        assert result["cards"][0]["word"] == "hola"
        assert result["cards"][1]["translation"] == "goodbye"
    
    def test_import_from_csv_missing_required_columns(self):
        """Test CSV import with missing required columns"""
        csv_data = "word,definition\nhola,greeting"
        
        with pytest.raises(ValueError, match="must contain 'word' and 'translation' columns"):
            DeckService.import_deck_from_csv(csv_data, "Test", "es", "en")
    
    def test_import_from_csv_empty_required_fields(self):
        """Test CSV import with empty required fields"""
        csv_data = "word,translation\nhola,\n,goodbye"
        
        with pytest.raises(ValueError, match="Missing required fields"):
            DeckService.import_deck_from_csv(csv_data, "Test", "es", "en")
    
    def test_import_from_csv_no_valid_cards(self):
        """Test CSV import with no valid cards"""
        csv_data = "word,translation\n"
        
        with pytest.raises(ValueError, match="No valid cards found"):
            DeckService.import_deck_from_csv(csv_data, "Test", "es", "en")
    
    def test_import_from_anki_success(self):
        """Test successful Anki import"""
        anki_data = """#deck: Spanish Basics
#tags: spanish
hola\thello\t<b>Definition:</b> greeting
adiós\tgoodbye"""
        
        result = DeckService.import_deck_from_anki(
            anki_data, "Spanish Basics", "Spanish", "English"
        )
        
        assert result["deck"]["deck_name"] == "Spanish Basics"
        assert len(result["cards"]) == 2
        assert result["cards"][0]["word"] == "hola"
        assert result["cards"][0]["translation"] == "hello"
    
    def test_import_from_anki_skips_comments(self):
        """Test Anki import skips comment lines"""
        anki_data = """#deck: Test
#this is a comment
word1\ttranslation1
#another comment
word2\ttranslation2"""
        
        result = DeckService.import_deck_from_anki(anki_data, "Test", "es", "en")
        assert len(result["cards"]) == 2
    
    def test_import_from_anki_no_valid_cards(self):
        """Test Anki import with no valid cards"""
        anki_data = "#deck: Test\n#only comments"
        
        with pytest.raises(ValueError, match="No valid cards found"):
            DeckService.import_deck_from_anki(anki_data, "Test", "es", "en")
    
    def test_import_from_anki_skips_invalid_lines(self):
        """Test Anki import skips lines with insufficient data"""
        anki_data = """word1\ttranslation1
invalid_line_without_tab
word2\ttranslation2"""
        
        result = DeckService.import_deck_from_anki(anki_data, "Test", "es", "en")
        # Should only import valid lines
        assert len(result["cards"]) == 2
