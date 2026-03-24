"""
User service - handles user profile and settings operations.
"""

from typing import Dict, Any, Optional
from db import get_db_cursor
import psycopg2


class UserNotFoundError(Exception):
    pass


class DatabaseError(Exception):
    pass


class UserService:
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user profile by user ID.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dictionary containing user data or None if not found
        """
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT u_id, email, display_name, timezone, 
                           new_cards_per_day, desired_retention,
                           fsrs_parameters, auto_optimize, 
                           num_reviews_per_optimize, total_reviews, 
                           reviews_since_last_optimize, total_due_cards_count
                    FROM Users
                    WHERE u_id = %s
                """, (user_id,))
                
                user = cursor.fetchone()
                return dict(user) if user else None
                
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")
    
    def update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile and settings.
        
        Args:
            user_id: User's unique identifier
            data: Dictionary containing fields to update
            
        Returns:
            Updated user data
            
        Raises:
            UserNotFoundError: If user doesn't exist
            DatabaseError: If database operation fails
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                # Build dynamic UPDATE query based on provided fields
                allowed_fields = {
                    'display_name', 'timezone', 
                    'new_cards_per_day', 'desired_retention',
                    'auto_optimize', 'num_reviews_per_optimize', 
                    'total_reviews', 'reviews_since_last_optimize'
                }
                
                # Filter to only allowed fields that are present in data
                update_fields = {k: v for k, v in data.items() if k in allowed_fields}
                
                if not update_fields:
                    raise ValueError("No valid fields to update")
                
                # Build SET clause dynamically
                set_clause = ", ".join([f"{field} = %s" for field in update_fields.keys()])
                values = list(update_fields.values())
                values.append(user_id)  # For WHERE clause
                
                query = f"""
                    UPDATE Users
                    SET {set_clause}
                    WHERE u_id = %s
                    RETURNING u_id, email, display_name, timezone, 
                              new_cards_per_day, desired_retention,
                              auto_optimize, num_reviews_per_optimize, 
                              total_reviews, reviews_since_last_optimize
                """
                
                cursor.execute(query, values)
                updated_user = cursor.fetchone()
                
                if not updated_user:
                    raise UserNotFoundError(f"User not found: {user_id}")
                
                return dict(updated_user)
                
        except UserNotFoundError:
            raise
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise DatabaseError(f"Failed to update user: {str(e)}")
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Delete a user account (cascades to decks and cards).
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dictionary with deletion statistics and verification
            
        Raises:
            UserNotFoundError: If user doesn't exist
            DatabaseError: If database operation fails
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                # Get counts before deletion for reporting
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT d.d_id) as deck_count,
                        COUNT(DISTINCT c.c_id) as card_count
                    FROM Users u
                    LEFT JOIN Decks d ON u.u_id = d.u_id
                    LEFT JOIN Cards c ON d.d_id = c.d_id
                    WHERE u.u_id = %s
                """, (user_id,))
                
                stats = cursor.fetchone()
                if stats is None:
                    raise UserNotFoundError(f"User not found: {user_id}")
                
                deck_count = stats['deck_count'] or 0
                card_count = stats['card_count'] or 0
                
                # Delete user (CASCADE handles related data)
                cursor.execute("""
                    DELETE FROM Users
                    WHERE u_id = %s
                """, (user_id,))
                
                if cursor.rowcount == 0:
                    raise UserNotFoundError(f"User not found: {user_id}")
                
                # Verify deletion
                cursor.execute("""
                    SELECT COUNT(*) as count FROM Users WHERE u_id = %s
                """, (user_id,))
                
                verification = cursor.fetchone()
                if verification['count'] > 0:
                    raise DatabaseError("User deletion verification failed")
                
                return {
                    'deleted': True,
                    'user_id': user_id,
                    'decks_deleted': deck_count,
                    'cards_deleted': card_count
                }
                
        except UserNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to delete user: {str(e)}")
