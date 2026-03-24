"""
Deck Service - handles deck CRUD operations and queries.

Manages deck database operations:
- Deck creation and retrieval
- Deck queries (due cards, recent decks)
- Deck data for export
- Import deck saving to database
"""

from typing import Dict, Any, List, Optional
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
    """Service for handling deck database operations"""

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
                       creation_date, last_reviewed, is_public, due_cards
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
                       d.is_public, d.due_cards, COUNT(c.c_id) as card_count
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
    
    @staticmethod
    def get_decks_with_due_cards(user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get decks that have cards needing review, using the due_cards field maintained by FsrsService.update_deck_due_cards."""
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT d_id, deck_name, word_lang, trans_lang, last_reviewed, due_cards as due_count
                FROM Decks
                WHERE u_id = %s AND due_cards > 0
                ORDER BY due_cards DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            decks = cursor.fetchall()
            return [dict(deck) for deck in decks]
    
    @staticmethod
    def get_recent_decks(user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get most recently reviewed decks."""
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT d.d_id, d.deck_name, d.word_lang, d.trans_lang,
                       d.description, d.last_reviewed, d.due_cards,
                       COUNT(c.c_id) as card_count
                FROM Decks d
                LEFT JOIN Cards c ON d.d_id = c.d_id
                WHERE d.u_id = %s AND d.last_reviewed IS NOT NULL
                GROUP BY d.d_id, d.deck_name, d.word_lang, d.trans_lang,
                         d.description, d.last_reviewed, d.due_cards
                ORDER BY d.last_reviewed DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            decks = cursor.fetchall()
            return [dict(deck) for deck in decks]
