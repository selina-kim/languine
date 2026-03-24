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
import os

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
    
    def __init__(self):
        self.minio_client = None
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "languine-media")
        self._init_minio()
    
    def _init_minio(self):
        """
        Initialize MinIO client for object storage cleanup.
        Env vars: MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME
        """
        try:
            from minio import Minio
            
            # Get MinIO configuration from environment
            endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
            access_key = os.getenv("MINIO_ACCESS_KEY")
            secret_key = os.getenv("MINIO_SECRET_KEY")
            
            # Strip http:// prefix if present
            endpoint = endpoint.replace("http://", "")
            
            if not access_key or not secret_key:
                print("Warning: MinIO credentials not configured")
                return
            
            # Initialize MinIO client
            self.minio_client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=False
            )
            
            self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "languine-media")
            print(f"MinIO client initialized for deck service: {endpoint}/{self.bucket_name}")
        
        except Exception as e:
            print(f"Failed to initialize MinIO client: {e}")
            self.minio_client = None
    
    def _delete_from_minio(self, object_id: str) -> bool:
        """Delete an object from MinIO storage."""
        if not object_id:
            return True
        
        if not self.minio_client:
            print("Warning: MinIO client not available, skipping deletion")
            return True
        
        try:
            self.minio_client.remove_object(self.bucket_name, object_id)
            print(f"Deleted from MinIO: {object_id}")
            return True
        except Exception as e:
            print(f"Failed to delete from MinIO ({object_id}): {e}")
            return False
    
    def _cleanup_deck_media(self, user_id: str, deck_id: int):
        """
        Query all MinIO object IDs from cards in a deck and remove from MinIO.
        Called before deleting a deck to clean up all associated media files.
        """
        with get_db_cursor() as cursor:
            # First verify deck ownership
            cursor.execute(
                "SELECT d_id FROM Decks WHERE d_id = %s AND u_id = %s",
                (deck_id, user_id)
            )
            if not cursor.fetchone():
                return  # Deck not found or not owned by user
            
            # Query all media file IDs from cards in this deck
            cursor.execute(
                """
                SELECT image, word_audio, trans_audio
                FROM Cards
                WHERE d_id = %s
                  AND (image IS NOT NULL OR word_audio IS NOT NULL OR trans_audio IS NOT NULL)
                """,
                (deck_id,)
            )
            cards = cursor.fetchall()
            
            # Delete all media files from MinIO
            for card in cards:
                if card['image']:
                    self._delete_from_minio(card['image'])
                if card['word_audio']:
                    self._delete_from_minio(card['word_audio'])
                if card['trans_audio']:
                    self._delete_from_minio(card['trans_audio'])

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
                       creation_date, last_reviewed, is_public, due_cards_count
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
                       d.is_public, d.due_cards_count, COUNT(c.c_id) as card_count
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
        """Get decks that have cards needing review, using the due_cards_count field maintained by FsrsService.update_deck_due_cards."""
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT d_id, deck_name, word_lang, trans_lang, last_reviewed, due_cards_count
                FROM Decks
                WHERE u_id = %s AND due_cards_count > 0
                ORDER BY due_cards_count DESC
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
                       d.description, d.last_reviewed, d.due_cards_count,
                       COUNT(c.c_id) as card_count
                FROM Decks d
                LEFT JOIN Cards c ON d.d_id = c.d_id
                WHERE d.u_id = %s AND d.last_reviewed IS NOT NULL
                GROUP BY d.d_id, d.deck_name, d.word_lang, d.trans_lang,
                         d.description, d.last_reviewed, d.due_cards_count
                ORDER BY d.last_reviewed DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            decks = cursor.fetchall()
            return [dict(deck) for deck in decks]

    @staticmethod
    def update_deck(user_id: str, deck_id: int, deck_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing deck's information.
        
        Args:
            user_id: User ID to verify ownership
            deck_id: Deck ID to update
            deck_data: Dictionary with fields to update
        
        Returns:
            Updated deck dictionary or None if not found/unauthorized
        
        Raises:
            DuplicateDeckNameError: UNIQUE(u_id, deck_name) violation
            DatabaseError: other DB errors
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                # Build dynamic update query for provided fields
                update_fields = []
                params = []
                
                if "deck_name" in deck_data:
                    update_fields.append("deck_name = %s")
                    params.append(deck_data["deck_name"])
                
                if "word_lang" in deck_data:
                    update_fields.append("word_lang = %s")
                    params.append(deck_data["word_lang"])
                
                if "trans_lang" in deck_data:
                    update_fields.append("trans_lang = %s")
                    params.append(deck_data["trans_lang"])
                
                if "description" in deck_data:
                    update_fields.append("description = %s")
                    params.append(deck_data["description"])
                
                if "is_public" in deck_data:
                    update_fields.append("is_public = %s")
                    params.append(bool(deck_data["is_public"]))
                
                if "link" in deck_data:
                    update_fields.append("link = %s")
                    params.append(deck_data["link"])
                
                if not update_fields:
                    # Nothing to update, fetch and return existing deck
                    cursor.execute(
                        """
                        SELECT d_id, deck_name, word_lang, trans_lang, description,
                               is_public, link, creation_date, last_reviewed
                        FROM Decks
                        WHERE d_id = %s AND u_id = %s
                        """,
                        (deck_id, user_id)
                    )
                    deck = cursor.fetchone()
                    return dict(deck) if deck else None
                
                # Add WHERE clause parameters
                params.extend([deck_id, user_id])
                
                # Execute update
                query = f"""
                    UPDATE Decks
                    SET {', '.join(update_fields)}
                    WHERE d_id = %s AND u_id = %s
                    RETURNING d_id, deck_name, word_lang, trans_lang, description,
                              is_public, link, creation_date, last_reviewed
                """
                
                cursor.execute(query, params)
                deck = cursor.fetchone()
                
                return dict(deck) if deck else None
        
        except psycopg2.IntegrityError as e:
            code = getattr(e, "pgcode", None)
            if code == "23505":
                raise DuplicateDeckNameError("A deck with this name already exists for you") from e
            raise DatabaseError(f"Database integrity error: {str(e)}") from e
        
        except psycopg2.Error as e:
            raise DatabaseError(f"Database error: {str(e)}") from e

    def delete_deck(self, user_id: str, deck_id: int) -> bool:
        """
        Delete a deck and all its associated cards (cascade).
        Also cleans up all MinIO media files (images, audio) from the deck's cards.
        
        Args:
            user_id: User ID to verify ownership
            deck_id: Deck ID to delete
        
        Returns:
            True if deleted, False if not found or unauthorized
        
        Raises:
            DatabaseError: Database errors
        """
        try:
            # First, clean up all MinIO media files for cards in this deck
            self._cleanup_deck_media(user_id, deck_id)
            
            # Then delete the deck (cascade will delete all cards)
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    DELETE FROM Decks
                    WHERE d_id = %s AND u_id = %s
                    """,
                    (deck_id, user_id)
                )
                
                # Check if any rows were deleted
                return cursor.rowcount > 0
        
        except psycopg2.Error as e:
            raise DatabaseError(f"Database error: {str(e)}") from e
