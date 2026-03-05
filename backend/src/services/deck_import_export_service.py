"""
Deck Import/Export Service - handles data format transformations.

Pure functions for converting between deck formats:
- JSON export/import
- CSV export/import  
- Anki TSV export/import

No database or external dependencies.
"""

import json
import csv
import io
from typing import Dict, Any
from datetime import datetime


class DeckImportExportService:
    """Service for handling deck data format transformations"""

    @staticmethod
    def export_deck_to_json(deck_data: Dict[str, Any]) -> str:
        """
        Export deck and its cards to JSON format
        
        Args:
            deck_data: Dictionary containing deck info and cards
                {
                    "deck": {
                        "deck_name": str,
                        "word_lang": str,
                        "trans_lang": str,
                        "description": str,
                        "creation_date": str (ISO format)
                    },
                    "cards": [
                        {
                            "word": str,
                            "translation": str,
                            "definition": str,
                            "image": str,
                            "word_example": str,
                            "trans_example": str,
                            "word_roman": str,
                            "trans_roman": str
                        }
                    ]
                }
        
        Returns:
            JSON string of the deck data
        """
        export_data = {
            "format": "capstone_deck_v1",
            "exported_at": datetime.utcnow().isoformat(),
            "deck": deck_data.get("deck", {}),
            "cards": deck_data.get("cards", [])
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)

    @staticmethod
    def export_deck_to_csv(deck_data: Dict[str, Any]) -> str:
        """
        Export deck cards to CSV format
        
        Args:
            deck_data: Dictionary containing deck info and cards
        
        Returns:
            CSV string of the cards data
        """
        output = io.StringIO()
        cards = deck_data.get("cards", [])
        
        if not cards:
            return ""
        
        # Define CSV columns
        fieldnames = [
            "word",
            "translation",
            "definition",
            "word_example",
            "trans_example",
            "word_roman",
            "trans_roman",
            "image"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for card in cards:
            # Only include fields that exist in fieldnames
            row = {k: card.get(k, "") for k in fieldnames}
            writer.writerow(row)
        
        return output.getvalue()

    @staticmethod
    def export_deck_to_anki(deck_data: Dict[str, Any]) -> str:
        """
        Export deck to Anki-compatible format (tab-separated values)
        
        Args:
            deck_data: Dictionary containing deck info and cards
        
        Returns:
            TSV string compatible with Anki import
        """
        output = io.StringIO()
        cards = deck_data.get("cards", [])
        deck_info = deck_data.get("deck", {})
        
        # Add deck metadata as comments (Anki ignores lines starting with #)
        output.write(f"#deck: {deck_info.get('deck_name', 'Unknown')}\n")
        output.write(f"#tags: {deck_info.get('word_lang', '')} {deck_info.get('trans_lang', '')}\n")
        output.write("#separator:tab\n")
        output.write("#html:true\n")
        
        for card in cards:
            # Anki format: Front\tBack\tExtra Info
            front = card.get("word", "")
            back = card.get("translation", "")
            
            # Build extra info with examples and definition
            extra_parts = []
            if card.get("definition"):
                extra_parts.append(f"<b>Definition:</b> {card.get('definition')}")
            if card.get("word_example"):
                extra_parts.append(f"<b>Example:</b> {card.get('word_example')}")
            if card.get("trans_example"):
                extra_parts.append(f"<b>Translation:</b> {card.get('trans_example')}")
            if card.get("word_roman"):
                extra_parts.append(f"<b>Pronunciation:</b> {card.get('word_roman')}")
            
            extra = "<br>".join(extra_parts)
            
            output.write(f"{front}\t{back}\t{extra}\n")
        
        return output.getvalue()

    @staticmethod
    def import_deck_from_json(json_data: str) -> Dict[str, Any]:
        """
        Import deck from JSON format
        
        Args:
            json_data: JSON string containing deck data
        
        Returns:
            Dictionary with deck and cards data
        
        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        
        # Validate format
        if not isinstance(data, dict):
            raise ValueError("Invalid deck format: Expected object at root level")
        
        # Check for required fields
        if "deck" not in data or "cards" not in data:
            raise ValueError("Invalid deck format: Missing 'deck' or 'cards' field")
        
        deck_info = data["deck"]
        cards = data["cards"]
        
        # Validate deck info
        required_deck_fields = ["deck_name", "word_lang", "trans_lang"]
        for field in required_deck_fields:
            if field not in deck_info:
                raise ValueError(f"Missing required deck field: {field}")
        
        # Validate cards
        if not isinstance(cards, list):
            raise ValueError("Invalid format: 'cards' must be an array")
        
        for i, card in enumerate(cards):
            if not isinstance(card, dict):
                raise ValueError(f"Invalid card at index {i}: Expected object")
            if "word" not in card or "translation" not in card:
                raise ValueError(f"Card at index {i} missing required fields: 'word' or 'translation'")
        
        return {
            "deck": deck_info,
            "cards": cards
        }

    @staticmethod
    def import_deck_from_csv(csv_data: str, deck_name: str, word_lang: str, trans_lang: str) -> Dict[str, Any]:
        """
        Import deck from CSV format
        
        Args:
            csv_data: CSV string containing cards data
            deck_name: Name for the imported deck
            word_lang: Language of the words
            trans_lang: Translation language
        
        Returns:
            Dictionary with deck and cards data
        
        Raises:
            ValueError: If CSV is invalid or missing required columns
        """
        input_stream = io.StringIO(csv_data)
        
        try:
            reader = csv.DictReader(input_stream)
            cards = []
            
            # Check for required columns
            if not reader.fieldnames or "word" not in reader.fieldnames or "translation" not in reader.fieldnames:
                raise ValueError("CSV must contain 'word' and 'translation' columns")
            
            for i, row in enumerate(reader):
                if not row.get("word") or not row.get("translation"):
                    raise ValueError(f"Row {i + 1}: Missing required fields 'word' or 'translation'")
                
                card = {
                    "word": row.get("word", "").strip(),
                    "translation": row.get("translation", "").strip(),
                    "definition": row.get("definition", "").strip(),
                    "word_example": row.get("word_example", "").strip(),
                    "trans_example": row.get("trans_example", "").strip(),
                    "word_roman": row.get("word_roman", "").strip(),
                    "trans_roman": row.get("trans_roman", "").strip(),
                    "image": row.get("image", "").strip()
                }
                cards.append(card)
            
            if not cards:
                raise ValueError("No valid cards found in CSV")
            
        except csv.Error as e:
            raise ValueError(f"Invalid CSV format: {str(e)}")
        
        return {
            "deck": {
                "deck_name": deck_name,
                "word_lang": word_lang,
                "trans_lang": trans_lang,
                "description": f"Imported from CSV",
                "creation_date": datetime.utcnow().isoformat()
            },
            "cards": cards
        }

    @staticmethod
    def import_deck_from_anki(tsv_data: str, deck_name: str, word_lang: str, trans_lang: str) -> Dict[str, Any]:
        """
        Import deck from Anki TSV format
        
        Args:
            tsv_data: Tab-separated values string (Anki export format)
            deck_name: Name for the imported deck
            word_lang: Language of the words
            trans_lang: Translation language
        
        Returns:
            Dictionary with deck and cards data
        """
        lines = tsv_data.strip().split('\n')
        cards = []
        
        for i, line in enumerate(lines):
            # Skip comment lines
            if line.startswith('#'):
                continue
            
            # Split by tab
            parts = line.split('\t')
            
            if len(parts) < 2:
                continue  # Skip invalid lines
            
            front = parts[0].strip()
            back = parts[1].strip()
            
            if not front or not back:
                continue
            
            # Basic card structure
            card = {
                "word": front,
                "translation": back,
                "definition": "",
                "word_example": "",
                "trans_example": "",
                "word_roman": "",
                "trans_roman": "",
                "image": ""
            }
            
            # Parse extra info if available (third column)
            if len(parts) >= 3:
                extra = parts[2].strip()
                # Very basic parsing - could be enhanced
                card["definition"] = extra
            
            cards.append(card)
        
        if not cards:
            raise ValueError("No valid cards found in Anki file")
        
        return {
            "deck": {
                "deck_name": deck_name,
                "word_lang": word_lang,
                "trans_lang": trans_lang,
                "description": f"Imported from Anki",
                "creation_date": datetime.utcnow().isoformat()
            },
            "cards": cards
        }
