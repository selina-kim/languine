import json
import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
from db import get_db_cursor
import psycopg2

class DuplicateDeckNameError(Exception):
    """Deck name already exists for this user (UNIQUE(u_id, deck_name))."""
    pass

class UserNotFoundError(Exception):
    """User id does not exist in Users table (FK violation)."""
    pass

class DatabaseError(Exception):
    """Any other database error."""
    pass


class DeckService:
    """Service for handling deck import/export operations"""

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

    @staticmethod
    def get_deck_with_cards(user_id: str, deck_id: int) -> Optional[Dict[str, Any]]:
        """
        Get deck details and all its cards from database
        
        Args:
            user_id: User ID to verify ownership
            deck_id: Deck ID to fetch
        
        Returns:
            Dictionary with deck info and cards, or None if not found
        """
        with get_db_cursor() as cursor:
            # Get deck info and verify ownership
            cursor.execute(
                """
                SELECT d_id, deck_name, word_lang, trans_lang, description,
                       creation_date, last_reviewed, is_public
                FROM Decks
                WHERE d_id = %s AND u_id = %s
                """,
                (deck_id, user_id)
            )
            deck = cursor.fetchone()
            
            if not deck:
                return None
            
            # Get all cards for this deck
            cursor.execute(
                """
                SELECT c_id, word, translation, definition, word_example,
                       trans_example, word_roman, trans_roman, image,
                       learning_state, difficulty, stability, due_date
                FROM Cards
                WHERE d_id = %s
                ORDER BY c_id
                """,
                (deck_id,)
            )
            cards = cursor.fetchall()
            
            return {
                "deck": dict(deck),
                "cards": [dict(card) for card in cards]
            }

    @staticmethod
    def get_deck_for_export(user_id: str, deck_id: int) -> Optional[Dict[str, Any]]:
        """
        Get deck and cards formatted for export
        
        Args:
            user_id: User ID to verify ownership
            deck_id: Deck ID to fetch
        
        Returns:
            Dictionary with deck data for export, or None if not found
        """
        with get_db_cursor() as cursor:
            # Get deck info and verify ownership
            cursor.execute(
                """
                SELECT d_id, deck_name, word_lang, trans_lang, description, creation_date
                FROM Decks
                WHERE d_id = %s AND u_id = %s
                """,
                (deck_id, user_id)
            )
            deck = cursor.fetchone()
            
            if not deck:
                return None
            
            # Get all cards for this deck
            cursor.execute(
                """
                SELECT word, translation, definition, word_example, trans_example,
                       word_roman, trans_roman, image
                FROM Cards
                WHERE d_id = %s
                ORDER BY c_id
                """,
                (deck_id,)
            )
            cards = cursor.fetchall()
            
            # Format data for export
            return {
                "deck": {
                    "deck_name": deck['deck_name'],
                    "word_lang": deck['word_lang'],
                    "trans_lang": deck['trans_lang'],
                    "description": deck['description'] or "",
                    "creation_date": deck['creation_date'].isoformat() if deck['creation_date'] else ""
                },
                "cards": [
                    {
                        "word": card['word'],
                        "translation": card['translation'],
                        "definition": card['definition'] or "",
                        "word_example": card['word_example'] or "",
                        "trans_example": card['trans_example'] or "",
                        "word_roman": card['word_roman'] or "",
                        "trans_roman": card['trans_roman'] or "",
                        "image": card['image'] or ""
                    }
                    for card in cards
                ]
            }

    @staticmethod
    def list_user_decks(user_id: str) -> List[Dict[str, Any]]:
        """
        List all decks for a user with card counts
        
        Args:
            user_id: User ID
        
        Returns:
            List of deck dictionaries with metadata
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT d.d_id, d.deck_name, d.word_lang, d.trans_lang,
                       d.description, d.creation_date, d.last_reviewed,
                       d.is_public, COUNT(c.c_id) as card_count
                FROM Decks d
                LEFT JOIN Cards c ON d.d_id = c.d_id
                WHERE d.u_id = %s
                GROUP BY d.d_id, d.deck_name, d.word_lang, d.trans_lang,
                         d.description, d.creation_date, d.last_reviewed, d.is_public
                ORDER BY d.creation_date DESC
                """,
                (user_id,)
            )
            decks = cursor.fetchall()
            
            return [dict(deck) for deck in decks]

    @staticmethod
    def create_deck(user_id: str, deck_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new deck in the database.

        Raises:
            DuplicateDeckNameError: UNIQUE(u_id, deck_name) violation (23505)
            UserNotFoundError: FK violation on u_id (23503)
            DatabaseError: other DB errors
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO Decks (u_id, deck_name, word_lang, trans_lang, description, is_public, link)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING d_id, deck_name, word_lang, trans_lang, description, is_public, link, creation_date
                    """,
                    (
                        user_id,
                        deck_data["deck_name"],
                        deck_data["word_lang"],
                        deck_data["trans_lang"],
                        deck_data.get("description", ""),
                        bool(deck_data.get("is_public", False)),
                        deck_data.get("link"),
                    ),
                )
                deck = cursor.fetchone()
                return dict(deck)

        except psycopg2.IntegrityError as e:
            code = getattr(e, "pgcode", None)
            if code == "23505":
                raise DuplicateDeckNameError("A deck with this name already exists for you") from e
            if code == "23503":
                raise UserNotFoundError("User not registered") from e
            raise DatabaseError(f"Database integrity error: {str(e)}") from e

        except psycopg2.Error as e:
            raise DatabaseError(f"Database error: {str(e)}") from e

    @staticmethod
    def save_imported_deck(user_id: str, imported_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save an imported deck and its cards to the database
        
        Args:
            user_id: User ID
            imported_data: Dictionary with 'deck' and 'cards' keys
        
        Returns:
            Dictionary with deck_id, deck info, and cards_count
        """
        with get_db_cursor(commit=True) as cursor:
            # Create deck record
            cursor.execute(
                """
                INSERT INTO Decks (u_id, deck_name, word_lang, trans_lang, description)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING d_id
                """,
                (
                    user_id,
                    imported_data['deck']['deck_name'],
                    imported_data['deck']['word_lang'],
                    imported_data['deck']['trans_lang'],
                    imported_data['deck'].get('description', '')
                )
            )
            deck_id = cursor.fetchone()['d_id']
            
            # Create card records
            for card in imported_data['cards']:
                cursor.execute(
                    """
                    INSERT INTO Cards (
                        d_id, word, translation, definition, word_example,
                        trans_example, word_roman, trans_roman, image
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        deck_id,
                        card['word'],
                        card['translation'],
                        card.get('definition', ''),
                        card.get('word_example', ''),
                        card.get('trans_example', ''),
                        card.get('word_roman', ''),
                        card.get('trans_roman', ''),
                        card.get('image', '')
                    )
                )
        
            return {
                "deck_id": deck_id,
                "deck": imported_data['deck'],
                "cards_count": len(imported_data['cards'])
            }
