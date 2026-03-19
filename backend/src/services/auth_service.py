from datetime import timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
from db import get_db_cursor

class AuthService:
    @staticmethod
    def get_or_create_oauth_user(google_id: str, email: str, display_name: str, timezone: str = 'UTC', **user_info):
        """
        Get existing OAuth user or create new one.
        Google ID is stored as u_id (from 'sub' field in Google ID token).
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                # Try to get existing user
                cursor.execute("""
                    SELECT u_id, email, display_name, timezone, 
                           new_cards_per_day, desired_retention,
                           fsrs_parameters, auto_optimize,
                           num_reviews_per_optimize, total_reviews,
                           reviews_since_last_optimize
                    FROM Users
                    WHERE u_id = %s
                """, (google_id,))
                
                user = cursor.fetchone()
                
                if user:
                    # User exists, return their data
                    return dict(user)
                
                # User doesn't exist, create new one
                cursor.execute("""
                    INSERT INTO Users (u_id, email, display_name, timezone)
                    VALUES (%s, %s, %s, %s)
                    RETURNING u_id, email, display_name, timezone, 
                              new_cards_per_day, desired_retention,
                              fsrs_parameters, auto_optimize,
                              num_reviews_per_optimize, total_reviews,
                              reviews_since_last_optimize
                """, (google_id, email, display_name, timezone))
                
                new_user = cursor.fetchone()

                # Copy built-in system decks and their cards to the new user.
                # A single CTE handles both inserts atomically:
                #   1. Insert one deck per system deck, returning the new d_id + deck_name.
                #   2. Join back to the system cards and insert copies into the new decks.
                # due_date is set to CURRENT_TIMESTAMP so cards are immediately reviewable.
                cursor.execute("""
                    WITH new_decks AS (
                        INSERT INTO Decks (u_id, deck_name, word_lang, trans_lang, description, is_public)
                        SELECT %s, deck_name, word_lang, trans_lang, description, false
                        FROM Decks
                        WHERE u_id = 'system'
                        RETURNING d_id, deck_name
                    )
                    INSERT INTO Cards (d_id, word, translation, due_date)
                    SELECT nd.d_id, c.word, c.translation, CURRENT_TIMESTAMP
                    FROM Cards c
                    JOIN Decks sd ON c.d_id = sd.d_id AND sd.u_id = 'system'
                    JOIN new_decks nd ON nd.deck_name = sd.deck_name
                """, (google_id,))

                return dict(new_user)
                
        except Exception as e:
            raise Exception(f"Failed to get or create user: {str(e)}")
    
    @staticmethod
    def generate_tokens(user_uid: str) -> dict:
        """Generate access and refresh tokens."""
        access_token = create_access_token(
            identity=user_uid,
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=user_uid,
            expires_delta=timedelta(days=30)
        )
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
