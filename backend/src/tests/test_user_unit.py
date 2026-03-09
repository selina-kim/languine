"""Unit tests for UserService.

Tests the user service logic with mocked database:
- Get user profile
- Update user settings (profile, FSRS parameters)
- Delete user account with verification
- Error handling for invalid inputs

Run this test file:
    docker compose exec backend pytest src/tests/test_user_unit.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_user_unit.py --cov=services.user_service
"""

import pytest
from unittest.mock import patch, MagicMock
from services.user_service import (
    UserService,
    UserNotFoundError,
    DatabaseError
)


@pytest.fixture
def user_service():
    """Create UserService instance."""
    return UserService()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "u_id": "test-user-123",
        "email": "test@example.com",
        "display_name": "Test User",
        "timezone": "America/Toronto",
        "new_cards_per_day": 10,
        "desired_retention": 0.9,
        "fsrs_parameters": None,
        "auto_optimize": True,
        "num_reviews_per_optimize": 256,
        "total_reviews": 0,
        "reviews_since_last_optimize": 0
    }


class TestGetUser:
    """Tests for get_user method."""
    
    def test_get_user_success(self, user_service, sample_user_data):
        """Test successfully retrieving a user."""
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = sample_user_data
            
            result = user_service.get_user("test-user-123")
            
            assert result == sample_user_data
            assert result["email"] == "test@example.com"
    
    def test_get_user_not_found(self, user_service):
        """Test retrieving non-existent user."""
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = None
            
            result = user_service.get_user("nonexistent-user")
            
            assert result is None
    
    def test_get_user_database_error(self, user_service):
        """Test database error handling."""
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.side_effect = Exception("DB Error")
            
            with pytest.raises(DatabaseError) as exc_info:
                user_service.get_user("test-user-123")
            
            assert "Failed to retrieve user" in str(exc_info.value)


class TestUpdateUser:
    """Tests for update_user method."""
    
    def test_update_display_name(self, user_service, sample_user_data):
        """Test updating display name."""
        updated_data = sample_user_data.copy()
        updated_data["display_name"] = "New Name"
        
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = updated_data
            
            result = user_service.update_user("test-user-123", {"display_name": "New Name"})
            
            assert result["display_name"] == "New Name"
    
    def test_update_timezone(self, user_service, sample_user_data):
        """Test updating timezone."""
        updated_data = sample_user_data.copy()
        updated_data["timezone"] = "America/New_York"
        
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = updated_data
            
            result = user_service.update_user("test-user-123", {"timezone": "America/New_York"})
            
            assert result["timezone"] == "America/New_York"
    
    def test_update_new_cards_per_day(self, user_service, sample_user_data):
        """Test updating new cards per day."""
        updated_data = sample_user_data.copy()
        updated_data["new_cards_per_day"] = 20
        
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = updated_data
            
            result = user_service.update_user("test-user-123", {"new_cards_per_day": 20})
            
            assert result["new_cards_per_day"] == 20
    
    def test_update_desired_retention(self, user_service, sample_user_data):
        """Test updating desired retention rate."""
        updated_data = sample_user_data.copy()
        updated_data["desired_retention"] = 0.85
        
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = updated_data
            
            result = user_service.update_user("test-user-123", {"desired_retention": 0.85})
            
            assert result["desired_retention"] == 0.85
    
    def test_update_fsrs_parameters(self, user_service, sample_user_data):
        """Test updating FSRS parameters."""
        updated_data = sample_user_data.copy()
        updated_data["fsrs_parameters"] = [1.0, 2.0, 3.0]
        
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = updated_data
            
            result = user_service.update_user("test-user-123", {"fsrs_parameters": [1.0, 2.0, 3.0]})
            
            assert result["fsrs_parameters"] == [1.0, 2.0, 3.0]
    
    def test_update_auto_optimize(self, user_service, sample_user_data):
        """Test updating auto-optimize flag."""
        updated_data = sample_user_data.copy()
        updated_data["auto_optimize"] = False
        
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = updated_data
            
            result = user_service.update_user("test-user-123", {"auto_optimize": False})
            
            assert result["auto_optimize"] is False
    
    def test_update_multiple_fields(self, user_service, sample_user_data):
        """Test updating multiple fields at once."""
        updated_data = sample_user_data.copy()
        updated_data["display_name"] = "Updated Name"
        updated_data["new_cards_per_day"] = 15
        
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = updated_data
            
            result = user_service.update_user("test-user-123", {
                "display_name": "Updated Name",
                "new_cards_per_day": 15
            })
            
            assert result["display_name"] == "Updated Name"
            assert result["new_cards_per_day"] == 15
    
    def test_update_no_valid_fields(self, user_service):
        """Test updating with no valid fields."""
        with patch("services.user_service.get_db_cursor"):
            with pytest.raises(ValueError) as exc_info:
                user_service.update_user("test-user-123", {"invalid_field": "value"})
            
            assert "No valid fields to update" in str(exc_info.value)
    
    def test_update_user_not_found(self, user_service):
        """Test updating non-existent user."""
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = None
            
            with pytest.raises(UserNotFoundError) as exc_info:
                user_service.update_user("nonexistent-user", {"display_name": "Test"})
            
            assert "User not found" in str(exc_info.value)


class TestDeleteUser:
    """Tests for delete_user method."""
    
    def test_delete_user_success(self, user_service):
        """Test successfully deleting a user."""
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_instance = mock_cursor.return_value.__enter__.return_value
            
            # Mock stats query
            mock_instance.fetchone.side_effect = [
                {"deck_count": 5, "card_count": 42},  # Stats query
                {"count": 0}  # Verification query
            ]
            mock_instance.rowcount = 1
            
            result = user_service.delete_user("test-user-123")
            
            assert result["deleted"] is True
            assert result["user_id"] == "test-user-123"
            assert result["decks_deleted"] == 5
            assert result["cards_deleted"] == 42
    
    def test_delete_user_not_found(self, user_service):
        """Test deleting non-existent user."""
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_instance = mock_cursor.return_value.__enter__.return_value
            mock_instance.fetchone.return_value = None
            
            with pytest.raises(UserNotFoundError) as exc_info:
                user_service.delete_user("nonexistent-user")
            
            assert "User not found" in str(exc_info.value)
    
    def test_delete_user_verification_failed(self, user_service):
        """Test deletion verification failure."""
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_instance = mock_cursor.return_value.__enter__.return_value
            
            # Mock stats query, successful delete, but failed verification
            mock_instance.fetchone.side_effect = [
                {"deck_count": 5, "card_count": 42},  # Stats query
                {"count": 1}  # Verification query shows user still exists
            ]
            mock_instance.rowcount = 1
            
            with pytest.raises(DatabaseError) as exc_info:
                user_service.delete_user("test-user-123")
            
            assert "verification failed" in str(exc_info.value).lower()
    
    def test_delete_user_no_decks_or_cards(self, user_service):
        """Test deleting user with no decks or cards."""
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_instance = mock_cursor.return_value.__enter__.return_value
            
            mock_instance.fetchone.side_effect = [
                {"deck_count": 0, "card_count": 0},  # No data
                {"count": 0}  # Verification passed
            ]
            mock_instance.rowcount = 1
            
            result = user_service.delete_user("test-user-123")
            
            assert result["deleted"] is True
            assert result["decks_deleted"] == 0
            assert result["cards_deleted"] == 0
