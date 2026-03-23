"""
Card service - handles card CRUD and media storage (MinIO).
"""

import os
import uuid
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from db import get_db_cursor
import psycopg2


class CardNotFoundError(Exception):
    pass


class DeckNotFoundError(Exception):
    pass


class UnauthorizedError(Exception):
    pass


class DatabaseError(Exception):
    pass


class CardService:

    def __init__(self):
        self.minio_client = None
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "languine-media")
        self._init_minio()

    def _init_minio(self):
        """
        Set up MinIO client for object storage.
        Env vars: MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME
        """
        try:
            from minio import Minio

            # Get MinIO configuration from environment
            endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
            access_key = os.getenv("MINIO_ACCESS_KEY")
            secret_key = os.getenv("MINIO_SECRET_KEY")

            # Parse endpoint (remove protocol if present)
            secure = False
            if endpoint.startswith("https://"):
                secure = True
                endpoint = endpoint.replace("https://", "")
            elif endpoint.startswith("http://"):
                endpoint = endpoint.replace("http://", "")

            # Initialize MinIO client
            self.minio_client = Minio(
                endpoint, access_key=access_key, secret_key=secret_key, secure=secure
            )

            # Use bucket name from env or default
            self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "languine-media")

            # Ensure bucket exists
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                print(f"Created MinIO bucket: {self.bucket_name}")
            else:
                print(f"MinIO initialized: bucket '{self.bucket_name}' ready")

        except ImportError:
            print("Warning: minio library not installed. Media storage disabled.")
            self.minio_client = None
        except Exception as e:
            print(f"Warning: MinIO initialization failed: {e}")
            self.minio_client = None

    # ==================== MinIO Storage ====================

    def _download_and_store_image(self, image_url: str, card_id: int) -> Optional[str]:
        """
        Download image from URL, store in MinIO, return object ID.
        Returns None if download/upload fails or MinIO is unavailable.
        """
        if not image_url or not self._is_url(image_url):
            return None

        if not self.minio_client:
            print("Warning: MinIO client not available, skipping image storage")
            return None

        try:
            # Step 1: Download image from URL
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            content_type = response.headers.get("Content-Type", "image/jpeg")

            # Determine file extension from content type
            ext_map = {
                "image/jpeg": "jpg",
                "image/png": "png",
                "image/gif": "gif",
                "image/webp": "webp",
                "image/svg+xml": "svg",
            }
            extension = ext_map.get(content_type, "jpg")

            # Step 2: Generate object ID (one image per card)
            object_id = f"images/card_{card_id}.{extension}"

            # Step 3: Upload to MinIO
            from io import BytesIO

            self.minio_client.put_object(
                self.bucket_name,
                object_id,
                BytesIO(image_data),
                length=len(image_data),
                content_type=content_type,
            )

            print(f"Image stored successfully: {object_id}")
            return object_id

        except requests.RequestException as e:
            print(f"Failed to download image from {image_url}: {e}")
            return None
        except Exception as e:
            print(f"Failed to store image in MinIO: {e}")
            return None

    def _delete_from_minio(self, object_id: str) -> bool:
        """Delete object from MinIO. Returns True on success or if object doesn't exist."""
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

    def get_presigned_image_url(self, object_id: str) -> Optional[str]:
        """
        Generate a presigned URL for accessing an image object in MinIO.
        Returns a URL that can be used to retrieve the image (valid for 7 days).
        Returns None if the object doesn't exist or MinIO is unavailable.
        """
        if not object_id or not self.minio_client:
            return None

        try:
            from datetime import timedelta

            # Generate presigned GET URL valid for 7 days
            url = self.minio_client.presigned_get_object(
                self.bucket_name,
                object_id,
                expires=timedelta(days=7),
            )
            return url
        except Exception as e:
            print(f"Failed to generate presigned URL for {object_id}: {e}")
            return None

    def _generate_and_store_tts(
        self, text: str, language: str, card_id: int, field_type: str = "word"
    ) -> Optional[str]:
        """
        Generate TTS audio, store in MinIO, return object ID.
        Returns None if generation/upload fails or MinIO is unavailable.
        """
        if not text:
            return None

        if not self.minio_client:
            print("Warning: MinIO client not available, skipping TTS storage")
            return None

        try:
            # Step 1: Generate TTS audio
            from services.tts_service import TTSService
            from routes.tts import DEFAULT_SPEAKERS
            from io import BytesIO
            import wave

            tts_service = TTSService()

            # Get default speaker for language
            speaker = DEFAULT_SPEAKERS.get(language, "Claribel Dervla")

            audio_array = tts_service.generate_speech(text, language, speaker=speaker)

            # Step 2: Generate object ID
            object_id = f"audio/card_{card_id}_{field_type}.wav"

            # Step 3: Convert numpy array to WAV format in memory
            buffer = BytesIO()

            # Write WAV file to buffer
            with wave.open(buffer, "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(22050)  # Sample rate

                # Convert float32 array to int16
                audio_int16 = (audio_array * 32767).astype("int16")
                wav_file.writeframes(audio_int16.tobytes())

            # Reset buffer position to beginning
            buffer.seek(0)
            audio_data = buffer.getvalue()

            # Step 4: Upload to MinIO
            self.minio_client.put_object(
                self.bucket_name,
                object_id,
                BytesIO(audio_data),
                length=len(audio_data),
                content_type="audio/wav",
            )

            print(f"TTS audio stored successfully: {object_id}")
            return object_id

        except ImportError:
            print("Warning: TTSService not available, skipping TTS generation")
            return None
        except Exception as e:
            print(f"Failed to generate/store TTS: {e}")
            return None

    @staticmethod
    def _is_url(value: str) -> bool:
        if not value:
            return False
        return value.startswith(("http://", "https://"))

    # ==================== Card CRUD ====================

    def create_card(self, user_id: str, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new card. Auto-generates TTS if word_audio/trans_audio not provided.
        Downloads and stores image if URL is provided.
        """
        deck_id = card_data.get("d_id")

        if not self._verify_deck_ownership(user_id, deck_id):
            raise DeckNotFoundError("Deck not found or access denied")

        deck_info = self._get_deck_info(deck_id)
        word_lang = deck_info.get("word_lang", "en") if deck_info else "en"
        trans_lang = deck_info.get("trans_lang", "en") if deck_info else "en"

        # Create card first to get c_id, then handle image/TTS

        try:
            with get_db_cursor(commit=True) as cursor:
                # Insert card without image/audio first
                cursor.execute(
                    """
                    INSERT INTO Cards (
                        d_id, word, translation, definition, word_example,
                        trans_example, word_roman, trans_roman, due_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING c_id, d_id, word, translation, definition,
                              word_example, trans_example, word_roman, trans_roman,
                              image, word_audio, trans_audio
                    """,
                    (
                        deck_id,
                        (card_data.get("word") or "").strip(),
                        (card_data.get("translation") or "").strip(),
                        (card_data.get("definition") or "").strip() or None,
                        (card_data.get("word_example") or "").strip() or None,
                        (card_data.get("trans_example") or "").strip() or None,
                        (card_data.get("word_roman") or "").strip() or None,
                        (card_data.get("trans_roman") or "").strip() or None,
                    ),
                )
                card = dict(cursor.fetchone())
                card_id = card["c_id"]

        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to create card: {str(e)}")

        image_object_id = None
        word_audio_id = None
        trans_audio_id = None

        # Download and store image if URL provided
        image_url = card_data.get("image")
        if image_url and self._is_url(image_url):
            image_object_id = self._download_and_store_image(image_url, card_id)
            # Fallback: persist the original URL if MinIO storage fails.
            if not image_object_id:
                image_object_id = image_url

        # Generate TTS if not provided
        if not card_data.get("word_audio"):
            word_audio_id = self._generate_and_store_tts(
                card_data.get("word", ""), word_lang, card_id, "word"
            )
        if not card_data.get("trans_audio"):
            trans_audio_id = self._generate_and_store_tts(
                card_data.get("translation", ""), trans_lang, card_id, "translation"
            )

        # Update card with generated media object IDs
        if any([image_object_id, word_audio_id, trans_audio_id]):
            try:
                with get_db_cursor(commit=True) as cursor:
                    cursor.execute(
                        """
                        UPDATE Cards
                        SET image = COALESCE(%s, image),
                            word_audio = COALESCE(%s, word_audio),
                            trans_audio = COALESCE(%s, trans_audio)
                        WHERE c_id = %s
                        RETURNING c_id, d_id, word, translation, definition,
                                  word_example, trans_example, word_roman, trans_roman,
                                  image, word_audio, trans_audio
                        """,
                        (image_object_id, word_audio_id, trans_audio_id, card_id),
                    )
                    card = dict(cursor.fetchone())
            except psycopg2.Error as e:
                print(f"Warning: Media storage update failed: {e}")

        return card

    def get_card(
        self, user_id: str, card_id: int, deck_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get card by ID. Returns None if not found or unauthorized."""
        with get_db_cursor() as cursor:
            if deck_id:
                cursor.execute(
                    """
                    SELECT c.c_id, c.d_id, c.word, c.translation, c.definition,
                           c.image, c.word_example, c.trans_example,
                           c.word_audio, c.trans_audio, c.word_roman, c.trans_roman,
                           c.learning_state, c.step, c.difficulty, c.stability,
                           c.due_date, c.last_review, c.successful_reps, c.fail_count
                    FROM Cards c
                    JOIN Decks d ON c.d_id = d.d_id
                    WHERE c.c_id = %s AND c.d_id = %s AND d.u_id = %s
                    """,
                    (card_id, deck_id, user_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT c.c_id, c.d_id, c.word, c.translation, c.definition,
                           c.image, c.word_example, c.trans_example,
                           c.word_audio, c.trans_audio, c.word_roman, c.trans_roman,
                           c.learning_state, c.step, c.difficulty, c.stability,
                           c.due_date, c.last_review, c.successful_reps, c.fail_count
                    FROM Cards c
                    JOIN Decks d ON c.d_id = d.d_id
                    WHERE c.c_id = %s AND d.u_id = %s
                    """,
                    (card_id, user_id),
                )
            card = cursor.fetchone()

            return dict(card) if card else None

    def update_card(
        self,
        user_id: str,
        card_id: int,
        update_data: Dict[str, Any],
        deck_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Update card fields. Re-downloads image if URL changes.
        Regenerates TTS if word/translation changes.
        """
        # Verify card exists and user has access
        current_card = self.get_card(user_id, card_id, deck_id)
        if not current_card:
            raise CardNotFoundError("Card not found or access denied")

        # Get deck language settings for TTS generation
        deck_id = current_card["d_id"]
        deck_info = self._get_deck_info(deck_id)
        word_lang = deck_info.get("word_lang", "en") if deck_info else "en"
        trans_lang = deck_info.get("trans_lang", "en") if deck_info else "en"

        # --- Handle image updates ---
        # If new image URL provided, delete old and download new
        # If image set to None, delete old image and clear field
        new_image_id = None
        image_changed = False
        if "image" in update_data:
            image_value = update_data["image"]
            old_image_id = current_card.get("image")

            if image_value and self._is_url(image_value):
                # New image URL provided - delete old and download new
                if old_image_id:
                    self._delete_from_minio(old_image_id)
                new_image_id = self._download_and_store_image(image_value, card_id)
                # Fallback: keep original external URL if MinIO storage fails.
                if not new_image_id:
                    new_image_id = image_value
                image_changed = True
            elif image_value is None or image_value == "":
                # Image removal requested - delete old and set to NULL
                if old_image_id:
                    self._delete_from_minio(old_image_id)
                new_image_id = None
                image_changed = True

        # --- Handle TTS audio updates ---
        # Regenerate audio if word or translation text changes
        new_word_audio = None
        new_trans_audio = None
        new_word = (update_data.get("word") or "").strip()
        new_translation = (update_data.get("translation") or "").strip()

        # If word changed, regenerate word audio
        if new_word and new_word != current_card.get("word"):
            old_audio_id = current_card.get("word_audio")
            if old_audio_id:
                self._delete_from_minio(old_audio_id)
            new_word_audio = self._generate_and_store_tts(
                new_word, word_lang, card_id, "word"
            )

        # If translation changed, regenerate translation audio
        if new_translation and new_translation != current_card.get("translation"):
            old_audio_id = current_card.get("trans_audio")
            if old_audio_id:
                self._delete_from_minio(old_audio_id)
            new_trans_audio = self._generate_and_store_tts(
                new_translation, trans_lang, card_id, "translation"
            )

        # --- Build dynamic UPDATE query ---
        updates = []  # List of "column = %s" strings
        params = []  # List of values to substitute

        # Map of request keys to database columns for text fields
        field_mapping = {
            "word": "word",
            "translation": "translation",
            "definition": "definition",
            "word_example": "word_example",
            "trans_example": "trans_example",
            "word_roman": "word_roman",
            "trans_roman": "trans_roman",
        }

        # Add text field updates if provided in update_data
        for data_key, db_col in field_mapping.items():
            if data_key in update_data:
                updates.append(f"{db_col} = %s")
                params.append(
                    update_data[data_key].strip() if update_data[data_key] else None
                )

        # Add media field updates if new media was generated
        if image_changed:
            updates.append("image = %s")
            params.append(new_image_id)

        if new_word_audio:
            updates.append("word_audio = %s")
            params.append(new_word_audio)

        if new_trans_audio:
            updates.append("trans_audio = %s")
            params.append(new_trans_audio)

        # If nothing to update, return current card as-is
        if not updates:
            return current_card

        # Add card_id as final parameter for WHERE clause
        params.append(card_id)

        # --- Execute UPDATE query ---
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    f"""
                    UPDATE Cards
                    SET {", ".join(updates)}
                    WHERE c_id = %s
                    RETURNING c_id, d_id, word, translation, definition,
                              word_example, trans_example, word_roman, trans_roman,
                              image, word_audio, trans_audio, learning_state,
                              difficulty, stability, due_date
                    """,
                    tuple(params),
                )
                card = cursor.fetchone()
                return dict(card)

        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to update card: {str(e)}")

    def delete_card(
        self, user_id: str, card_id: int, deck_id: Optional[int] = None
    ) -> bool:
        """Delete card and its MinIO objects (image, audio)."""
        card = self.get_card(user_id, card_id, deck_id)
        if not card:
            raise CardNotFoundError("Card not found or access denied")

        # Clean up MinIO
        if card.get("image"):
            self._delete_from_minio(card["image"])
        if card.get("word_audio"):
            self._delete_from_minio(card["word_audio"])
        if card.get("trans_audio"):
            self._delete_from_minio(card["trans_audio"])

        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    DELETE FROM Cards
                    WHERE c_id = %s
                    """,
                    (card_id,),
                )
                return True

        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to delete card: {str(e)}")

    # ==================== Deck-level Queries ====================

    def get_cards_for_deck(
        self, user_id: str, deck_id: int, page: int = 1, per_page: int = 50
    ) -> Optional[Dict[str, Any]]:
        """Get paginated cards for a deck."""
        if not self._verify_deck_ownership(user_id, deck_id):
            return None

        offset = (page - 1) * per_page

        with get_db_cursor() as cursor:
            # Get total count
            cursor.execute(
                "SELECT COUNT(*) as total FROM Cards WHERE d_id = %s", (deck_id,)
            )
            total = cursor.fetchone()["total"]

            cursor.execute(
                """
                SELECT c_id, d_id, word, translation, definition,
                       image, word_example, trans_example,
                       word_audio, trans_audio, word_roman, trans_roman,
                       learning_state, step, difficulty, stability,
                       due_date, last_review, successful_reps, fail_count
                FROM Cards
                WHERE d_id = %s
                ORDER BY c_id
                LIMIT %s OFFSET %s
                """,
                (deck_id, per_page, offset),
            )
            cards = cursor.fetchall()

            return {
                "cards": [dict(card) for card in cards],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page,
                },
            }

    def get_cards_for_review(
        self, user_id: str, deck_id: int, limit: int = 20
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cards due for review (due_date <= now)."""
        if not self._verify_deck_ownership(user_id, deck_id):
            return None

        now = datetime.now(timezone.utc)

        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT c_id, d_id, word, translation, definition,
                       image, word_example, trans_example,
                       word_audio, trans_audio, word_roman, trans_roman,
                       learning_state, step, difficulty, stability,
                       due_date, last_review, successful_reps, fail_count
                FROM Cards
                WHERE d_id = %s
                  AND due_date <= %s
                ORDER BY due_date ASC
                LIMIT %s
                """,
                (deck_id, now, limit),
            )

            cards = cursor.fetchall()
            return [dict(card) for card in cards]

    # ==================== Helpers ====================

    def _verify_deck_ownership(self, user_id: str, deck_id: int) -> bool:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT d_id FROM Decks WHERE d_id = %s AND u_id = %s",
                (deck_id, user_id),
            )
            return cursor.fetchone() is not None

    def _get_deck_info(self, deck_id: int) -> Optional[Dict[str, Any]]:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT d_id, deck_name, word_lang, trans_lang
                FROM Decks
                WHERE d_id = %s
                """,
                (deck_id,),
            )
            deck = cursor.fetchone()
            return dict(deck) if deck else None
