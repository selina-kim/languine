"""Unit tests for UserService and user routes.

Tests the user service logic with mocked database:
- Get user profile
- Update user settings (profile, FSRS parameters)
- Delete user account with verification
- Error handling for invalid inputs
- Input validation (display_name length, data types)
- FSRS parameter validation and constraints

Run this test file:
    docker compose exec backend pytest src/tests/test_user_unit.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_user_unit.py --cov=services.user_service --cov=routes.users
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from services.user_service import UserService, UserNotFoundError, DatabaseError


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
        "reviews_since_last_optimize": 0,
    }


class TestGetUser:
    """Tests for get_user method."""

    def test_get_user_success(self, user_service, sample_user_data):
        """Test successfully retrieving a user."""
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
                sample_user_data
            )

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
            mock_cursor.return_value.__enter__.return_value.fetchone.side_effect = (
                Exception("DB Error")
            )

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
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
                updated_data
            )

            result = user_service.update_user(
                "test-user-123", {"display_name": "New Name"}
            )

            assert result["display_name"] == "New Name"

    def test_update_timezone(self, user_service, sample_user_data):
        """Test updating timezone."""
        updated_data = sample_user_data.copy()
        updated_data["timezone"] = "America/New_York"

        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
                updated_data
            )

            result = user_service.update_user(
                "test-user-123", {"timezone": "America/New_York"}
            )

            assert result["timezone"] == "America/New_York"

    def test_update_new_cards_per_day(self, user_service, sample_user_data):
        """Test updating new cards per day."""
        updated_data = sample_user_data.copy()
        updated_data["new_cards_per_day"] = 20

        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
                updated_data
            )

            result = user_service.update_user(
                "test-user-123", {"new_cards_per_day": 20}
            )

            assert result["new_cards_per_day"] == 20

    def test_update_desired_retention(self, user_service, sample_user_data):
        """Test updating desired retention rate."""
        updated_data = sample_user_data.copy()
        updated_data["desired_retention"] = 0.85

        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
                updated_data
            )

            result = user_service.update_user(
                "test-user-123", {"desired_retention": 0.85}
            )

            assert result["desired_retention"] == 0.85

    def test_update_auto_optimize(self, user_service, sample_user_data):
        """Test updating auto-optimize flag."""
        updated_data = sample_user_data.copy()
        updated_data["auto_optimize"] = False

        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
                updated_data
            )

            result = user_service.update_user("test-user-123", {"auto_optimize": False})

            assert result["auto_optimize"] is False

    def test_update_multiple_fields(self, user_service, sample_user_data):
        """Test updating multiple fields at once."""
        updated_data = sample_user_data.copy()
        updated_data["display_name"] = "Updated Name"
        updated_data["new_cards_per_day"] = 15

        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
                updated_data
            )

            result = user_service.update_user(
                "test-user-123",
                {"display_name": "Updated Name", "new_cards_per_day": 15},
            )

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

    # testing updating FSRS parameters with reset_fsrs_params flag will be tested in the unit tests for fsrs_service


class TestDeleteUser:
    """Tests for delete_user method."""

    def test_delete_user_success(self, user_service):
        """Test successfully deleting a user."""
        with patch("services.user_service.get_db_cursor") as mock_cursor:
            mock_instance = mock_cursor.return_value.__enter__.return_value

            # Mock stats query
            mock_instance.fetchone.side_effect = [
                {"deck_count": 5, "card_count": 42},  # Stats query
                {"count": 0},  # Verification query
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
                {"count": 1},  # Verification query shows user still exists
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
                {"count": 0},  # Verification passed
            ]
            mock_instance.rowcount = 1

            result = user_service.delete_user("test-user-123")

            assert result["deleted"] is True
            assert result["decks_deleted"] == 0
            assert result["cards_deleted"] == 0


class TestUpdateCurrentUserRoute:
    """Tests for PUT/PATCH /users/me endpoint - input validation only."""

    def test_update_user_no_data(self, client, auth_headers):
        """Test update with no JSON data."""
        response = client.put("/users/me", headers=auth_headers)
        assert response.status_code == 400
        assert "No data provided" in json.loads(response.data)["error"]

    def test_update_user_display_name_empty(self, client, auth_headers):
        """Test update with empty display_name."""
        response = client.put(
            "/users/me", json={"display_name": "   "}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "display_name cannot be empty" in data["error"]

    def test_update_user_display_name_too_long(self, client, auth_headers):
        """Test update with display_name exceeding max length."""
        long_name = "a" * 31
        response = client.put(
            "/users/me", json={"display_name": long_name}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "30 characters" in data["error"]

    def test_update_user_new_cards_per_day_invalid_type(self, client, auth_headers):
        """Test update with non-integer new_cards_per_day."""
        response = client.put(
            "/users/me", json={"new_cards_per_day": "not_an_int"}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "must be an integer" in data["error"]

    def test_update_user_new_cards_per_day_negative(self, client, auth_headers):
        """Test update with negative new_cards_per_day."""
        response = client.put(
            "/users/me", json={"new_cards_per_day": -5}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "non-negative" in data["error"]

    def test_update_user_desired_retention_invalid_type(self, client, auth_headers):
        """Test update with non-numeric desired_retention."""
        response = client.put(
            "/users/me",
            json={"desired_retention": "not_a_number"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "must be a number" in data["error"]

    def test_update_user_desired_retention_out_of_range(self, client, auth_headers):
        """Test update with desired_retention outside 0.0-1.0."""
        response = client.put(
            "/users/me", json={"desired_retention": 1.5}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "between 0.0 and 1.0" in data["error"]

    def test_update_user_auto_optimize_invalid_type(self, client, auth_headers):
        """Test update with non-boolean auto_optimize."""
        response = client.put(
            "/users/me", json={"auto_optimize": "yes"}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "must be a boolean" in data["error"]

    def test_update_user_num_reviews_per_optimize_invalid_type(
        self, client, auth_headers
    ):
        """Test update with non-integer num_reviews_per_optimize."""
        response = client.put(
            "/users/me",
            json={"num_reviews_per_optimize": "not_an_int"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "must be an integer" in data["error"]

    def test_update_user_num_reviews_per_optimize_zero(self, client, auth_headers):
        """Test update with zero num_reviews_per_optimize."""
        response = client.put(
            "/users/me", json={"num_reviews_per_optimize": 0}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "must be positive" in data["error"]

    def test_update_user_total_reviews_invalid_type(self, client, auth_headers):
        """Test update with non-integer total_reviews."""
        response = client.put(
            "/users/me", json={"total_reviews": "not_an_int"}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "must be an integer" in data["error"]

    def test_update_user_total_reviews_negative(self, client, auth_headers):
        """Test update with negative total_reviews."""
        response = client.put(
            "/users/me", json={"total_reviews": -10}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "non-negative" in data["error"]

    def test_update_user_reviews_since_last_optimize_invalid_type(
        self, client, auth_headers
    ):
        """Test update with non-integer reviews_since_last_optimize."""
        response = client.put(
            "/users/me",
            json={"reviews_since_last_optimize": "not_an_int"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "must be an integer" in data["error"]

    def test_update_user_reviews_since_last_optimize_negative(
        self, client, auth_headers
    ):
        """Test update with negative reviews_since_last_optimize."""
        response = client.put(
            "/users/me", json={"reviews_since_last_optimize": -5}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "non-negative" in data["error"]

    def test_update_user_reset_fsrs_params_invalid_type(self, client, auth_headers):
        """Test update with non-boolean reset_fsrs_params."""
        response = client.put(
            "/users/me", json={"reset_fsrs_params": "yes"}, headers=auth_headers
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "must be a boolean" in data["error"]

    def test_update_user_database_error(self, client, auth_headers):
        """Test update with DatabaseError from service."""
        with patch("routes.users.user_service.update_user") as mock_update:
            mock_update.side_effect = DatabaseError("DB connection failed")

            response = client.put(
                "/users/me", json={"display_name": "Test"}, headers=auth_headers
            )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Database error" in data["error"]

    def test_update_user_value_error(self, client, auth_headers):
        """Test update with ValueError from service."""
        with patch("routes.users.user_service.update_user") as mock_update:
            mock_update.side_effect = ValueError("Invalid value")

            response = client.put(
                "/users/me", json={"timezone": "Invalid/Timezone"}, headers=auth_headers
            )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid value" in data["error"]

    def test_update_user_generic_exception(self, client, auth_headers):
        """Test update with generic exception."""
        with patch("routes.users.user_service.update_user") as mock_update:
            mock_update.side_effect = Exception("Unexpected error")

            response = client.put(
                "/users/me", json={"display_name": "Test"}, headers=auth_headers
            )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Internal server error" in data["error"]


class TestDeleteCurrentUserRoute:
    """Tests for DELETE /users/me route."""

    def test_delete_user_success(self, client, auth_headers):
        """Test successful user deletion."""
        with patch("routes.users.user_service.delete_user") as mock_delete:
            mock_delete.return_value = {"decks_deleted": 5, "cards_deleted": 100}

            response = client.delete("/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "deleted successfully" in data["message"]
        assert data["details"]["decks_deleted"] == 5

    def test_delete_user_not_found(self, client, auth_headers):
        """Test delete non-existent user."""
        with patch("routes.users.user_service.delete_user") as mock_delete:
            mock_delete.side_effect = UserNotFoundError("User not found")

            response = client.delete("/users/me", headers=auth_headers)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "not found" in data["error"]

    def test_delete_user_database_error(self, client, auth_headers):
        """Test delete with DatabaseError."""
        with patch("routes.users.user_service.delete_user") as mock_delete:
            mock_delete.side_effect = DatabaseError("DB connection failed")

            response = client.delete("/users/me", headers=auth_headers)

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Database error" in data["error"]

    def test_delete_user_generic_exception(self, client, auth_headers):
        """Test delete with generic exception."""
        with patch("routes.users.user_service.delete_user") as mock_delete:
            mock_delete.side_effect = Exception("Unexpected error")

            response = client.delete("/users/me", headers=auth_headers)

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Internal server error" in data["error"]


class TestGetCurrentUserRoute:
    """Tests for GET /users/me route."""

    def test_get_user_success(self, client, auth_headers):
        """Test successful user retrieval."""
        user_data = {
            "u_id": "user-123",
            "display_name": "Test User",
            "timezone": "America/Toronto",
        }

        with patch("routes.users.user_service.get_user") as mock_get:
            mock_get.return_value = user_data

            response = client.get("/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["u_id"] == "user-123"

    def test_get_user_not_found(self, client, auth_headers):
        """Test get non-existent user."""
        with patch("routes.users.user_service.get_user") as mock_get:
            mock_get.return_value = None

            response = client.get("/users/me", headers=auth_headers)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "not found" in data["error"]

    def test_get_user_database_error(self, client, auth_headers):
        """Test get with DatabaseError."""
        with patch("routes.users.user_service.get_user") as mock_get:
            mock_get.side_effect = DatabaseError("DB connection failed")

            response = client.get("/users/me", headers=auth_headers)

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Database error" in data["error"]

    def test_get_user_generic_exception(self, client, auth_headers):
        """Test get with generic exception."""
        with patch("routes.users.user_service.get_user") as mock_get:
            mock_get.side_effect = Exception("Unexpected error")

            response = client.get("/users/me", headers=auth_headers)

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Internal server error" in data["error"]
