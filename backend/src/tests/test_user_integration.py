"""Integration tests for user routes.

Tests the user management endpoints with actual HTTP requests and responses.
These tests verify the complete request/response cycle including:
- Get user profile
- Update user settings (profile, FSRS parameters)
- Delete user account
- Authentication and authorization
- Database interactions
- Input validation and error handling

All tests in this file are marked as integration tests.

Run this test file:
    docker compose exec backend pytest src/tests/test_user_integration.py -v -m integration

Run with coverage:
    docker compose exec backend pytest src/tests/test_user_integration.py --cov=routes.users -m integration
"""

import pytest
import json

pytestmark = pytest.mark.integration


# ==================== Get User Profile Tests ====================


def test_get_current_user_success(client, auth_headers):
    """Test successfully retrieving current user profile."""
    response = client.get(
        "/users/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["u_id"] == "test-user-id"
    assert result["email"] == "test@example.com"
    assert result["display_name"] == "Test User"
    assert result["timezone"] == "America/Toronto"
    assert "new_cards_per_day" in result
    assert "desired_retention" in result


def test_get_current_user_no_auth(client):
    """Test getting user profile without authentication."""
    response = client.get("/users/me")
    
    assert response.status_code == 401
    result = json.loads(response.data)
    assert "error" in result


def test_get_current_user_invalid_token(client):
    """Test getting user profile with invalid token."""
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == 401


# ==================== Update User Profile Tests ====================


def test_update_display_name(client, auth_headers):
    """Test updating user display name."""
    update_data = {
        "display_name": "Updated Name"
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["user"]["display_name"] == "Updated Name"


def test_update_timezone(client, auth_headers):
    """Test updating user timezone."""
    update_data = {
        "timezone": "America/New_York"
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["user"]["timezone"] == "America/New_York"


def test_update_new_cards_per_day(client, auth_headers):
    """Test updating new cards per day."""
    update_data = {
        "new_cards_per_day": 20
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["user"]["new_cards_per_day"] == 20


def test_update_desired_retention(client, auth_headers):
    """Test updating desired retention rate."""
    update_data = {
        "desired_retention": 0.85
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["user"]["desired_retention"] == 0.85


def test_update_auto_optimize(client, auth_headers):
    """Test updating auto-optimize flag."""
    update_data = {
        "auto_optimize": False
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["user"]["auto_optimize"] is False


def test_update_fsrs_parameters(client, auth_headers):
    """Test updating FSRS parameters."""
    update_data = {
        "fsrs_parameters": [1.0, 2.0, 3.0, 4.0]
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["user"]["fsrs_parameters"] == [1.0, 2.0, 3.0, 4.0]


def test_update_multiple_fields(client, auth_headers):
    """Test updating multiple fields at once."""
    update_data = {
        "display_name": "Multi Update",
        "new_cards_per_day": 15,
        "desired_retention": 0.88
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["user"]["display_name"] == "Multi Update"
    assert result["user"]["new_cards_per_day"] == 15
    assert result["user"]["desired_retention"] == 0.88


def test_update_empty_display_name(client, auth_headers):
    """Test updating with empty display name fails validation."""
    update_data = {
        "display_name": "   "
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "cannot be empty" in result["error"]


def test_update_display_name_too_long(client, auth_headers):
    """Test updating with display name exceeding max length."""
    update_data = {
        "display_name": "a" * 31  # Max is 30
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "30 characters" in result["error"]


def test_update_negative_new_cards(client, auth_headers):
    """Test updating with negative new cards per day."""
    update_data = {
        "new_cards_per_day": -5
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "non-negative" in result["error"]


def test_update_invalid_desired_retention(client, auth_headers):
    """Test updating with desired retention out of range."""
    update_data = {
        "desired_retention": 1.5  # Must be 0.0-1.0
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "between 0.0 and 1.0" in result["error"]


def test_update_invalid_auto_optimize_type(client, auth_headers):
    """Test updating with invalid auto_optimize type."""
    update_data = {
        "auto_optimize": "yes"  # Must be boolean
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "boolean" in result["error"]


def test_update_invalid_fsrs_parameters(client, auth_headers):
    """Test updating with invalid FSRS parameters."""
    update_data = {
        "fsrs_parameters": "not an array"
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "array" in result["error"]


def test_update_fsrs_parameters_invalid_elements(client, auth_headers):
    """Test updating with FSRS parameters containing non-numeric values."""
    update_data = {
        "fsrs_parameters": [1.0, "invalid", 3.0]
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "numbers" in result["error"]


def test_update_no_data_provided(client, auth_headers):
    """Test update with no data provided."""
    response = client.patch(
        "/users/me",
        data=json.dumps({}),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "No valid fields" in result["error"] or "No data provided" in result["error"]


def test_update_without_auth(client):
    """Test updating user without authentication."""
    update_data = {
        "display_name": "Test"
    }
    
    response = client.patch(
        "/users/me",
        data=json.dumps(update_data),
        content_type='application/json'
    )
    
    assert response.status_code == 401


# ==================== Delete User Tests ====================


def test_delete_user_success(client, auth_headers):
    """Test successfully deleting user account."""
    response = client.delete(
        "/users/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert "deleted successfully" in result["message"]
    assert "details" in result
    assert result["details"]["deleted"] is True
    assert "user_id" in result["details"]
    assert "decks_deleted" in result["details"]
    assert "cards_deleted" in result["details"]


def test_delete_user_without_auth(client):
    """Test deleting user without authentication."""
    response = client.delete("/users/me")
    
    assert response.status_code == 401


def test_delete_user_verifies_deletion(client, auth_headers):
    """Test that user deletion is actually verified in database."""
    # First, verify user exists
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    
    # Delete user
    response = client.delete("/users/me", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify user no longer exists (should fail authentication)
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code in [401, 404]  # Either unauthorized or not found
