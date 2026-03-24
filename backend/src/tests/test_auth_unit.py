"""
Unit tests for google oauth API.

These tests mock Google OAuth and token generation to test the application logic
without making real API calls or requiring a database. 

Run with: 
- poetry run pytest -v (excludes integration by default)
- poetry run pytest src/tests/test_auth_unit.py -v

Test coverage:
- Google token verification (success and failure)
- Missing required parameters
- Invalid token handling
- Token refresh without valid tokens
- Logout without authentication
"""
import json
from unittest.mock import patch, MagicMock


# ----------------------------
# Fake API Response Fixtures
# ----------------------------
def fake_google_token_valid(*args, **kwargs):
    """Mock successful Google token verification."""
    return {
        'sub': 'google-id-123',
        'email': 'test@example.com',
        'name': 'Test User',
        'iss': 'accounts.google.com'
    }


def fake_user_data(*args, **kwargs):
    """Mock user data returned from get_or_create_oauth_user."""
    return {
        'u_id': 'google-id-123',
        'email': 'test@example.com',
        'display_name': 'test',
        'timezone': 'UTC',
        'new_cards_per_day': 10,
        'desired_retention': 0.9,
        'fsrs_parameters': None,
        'auto_optimize': True,
        'num_reviews_per_optimize': 256,
        'total_reviews': 0,
        'reviews_since_last_optimize': 0
    }


def fake_google_token_invalid(*args, **kwargs):
    """Mock invalid Google token."""
    raise ValueError('Invalid token')


def fake_google_token_expired(*args, **kwargs):
    """Mock expired Google token."""
    raise ValueError('Token expired')


# ----------------------------
# Unit Tests (Mocked Google OAuth)
# ----------------------------
class TestGoogleOAuthUnit:
    """Unit tests for Google OAuth with mocked token verification."""
    
    def test_google_token_verification_success(self, client, monkeypatch):
        """Test successful Google token verification."""
        # mock the Google token verification to return valid credentials
        monkeypatch.setattr(
            "routes.auth.id_token.verify_oauth2_token",
            fake_google_token_valid
        )
        # mock the database user creation/retrieval
        monkeypatch.setattr(
            "routes.auth.AuthService.get_or_create_oauth_user",
            fake_user_data
        )
        
        response = client.post(
            "/auth/google",
            json={"id_token": "fake-google-token"}
        )
        
        data = json.loads(response.data)
        
        # verify successful response with tokens
        assert response.status_code == 200
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
    
    def test_google_oauth_creates_new_user(self, client, monkeypatch):
        """Test that Google OAuth creates a new user on first login."""
        # Mock Google token verification
        monkeypatch.setattr(
            "routes.auth.id_token.verify_oauth2_token",
            fake_google_token_valid
        )
        # Mock user creation
        monkeypatch.setattr(
            "routes.auth.AuthService.get_or_create_oauth_user",
            fake_user_data
        )
        
        response = client.post(
            "/auth/google",
            json={"id_token": "fake-google-token"}
        )
        
        data = json.loads(response.data)
        
        # Verify user data is returned
        assert response.status_code == 200
        assert "user" in data
        assert data["user"]["u_id"] == "google-id-123"
        assert data["user"]["email"] == "test@example.com"
        assert "display_name" in data["user"]
        assert "timezone" in data["user"]
        assert "new_cards_per_day" in data["user"]
        assert "desired_retention" in data["user"]
    
    def test_google_oauth_returns_existing_user(self, client, monkeypatch):
        """Test that Google OAuth returns existing user on subsequent logins."""
        # Mock Google token verification
        monkeypatch.setattr(
            "routes.auth.id_token.verify_oauth2_token",
            fake_google_token_valid
        )
        # Mock user retrieval
        monkeypatch.setattr(
            "routes.auth.AuthService.get_or_create_oauth_user",
            fake_user_data
        )
        
        # First login - creates user
        response1 = client.post(
            "/auth/google",
            json={"id_token": "fake-google-token"}
        )
        data1 = json.loads(response1.data)
        assert response1.status_code == 200
        
        # Second login - retrieves existing user
        response2 = client.post(
            "/auth/google",
            json={"id_token": "fake-google-token"}
        )
        data2 = json.loads(response2.data)
        
        assert response2.status_code == 200
        # Should return same user ID
        assert data2["user"]["u_id"] == data1["user"]["u_id"]
        assert data2["user"]["email"] == data1["user"]["email"]
    
    def test_google_oauth_user_has_fsrs_fields(self, client, monkeypatch):
        """Test that created user has all FSRS fields initialized."""
        monkeypatch.setattr(
            "routes.auth.id_token.verify_oauth2_token",
            fake_google_token_valid
        )
        monkeypatch.setattr(
            "routes.auth.AuthService.get_or_create_oauth_user",
            fake_user_data
        )
        
        response = client.post(
            "/auth/google",
            json={"id_token": "fake-google-token"}
        )
        
        data = json.loads(response.data)
        user = data["user"]
        
        # Verify FSRS fields are present
        assert "fsrs_parameters" in user
        assert "auto_optimize" in user
        assert "num_reviews_per_optimize" in user
        assert "total_reviews" in user
        assert "reviews_since_last_optimize" in user
        
        # Verify default values
        assert user["auto_optimize"] is True
        assert user["num_reviews_per_optimize"] == 256
        assert user["total_reviews"] == 0
        assert user["reviews_since_last_optimize"] == 0
    
    def test_google_oauth_missing_token(self, client, monkeypatch):
        """Test error handling when token is missing."""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
        
        # send POST request without id_token
        response = client.post("/auth/google", json={})
        
        data = json.loads(response.data)
        
        # verify 400 Bad Request and error message
        assert response.status_code == 400
        assert "Token required" in data["error"] or "id_token" in data["error"]
    
    def test_google_oauth_invalid_token(self, client, monkeypatch):
        """Test error handling when token is invalid."""
        # mock the Google verification to raise an error
        monkeypatch.setattr(
            "routes.auth.id_token.verify_oauth2_token",
            fake_google_token_invalid
        )
        
        response = client.post(
            "/auth/google",
            json={"id_token": "invalid-token"}
        )
        
        data = json.loads(response.data)
        
        # verify 401 Unauthorized
        assert response.status_code == 401
        assert "Invalid token" in data["error"]
    
    def test_google_oauth_expired_token(self, client, monkeypatch):
        """Test error handling when token is expired."""
        monkeypatch.setattr(
            "routes.auth.id_token.verify_oauth2_token",
            fake_google_token_expired
        )
        
        response = client.post(
            "/auth/google",
            json={"id_token": "expired-token"}
        )
        
        data = json.loads(response.data)
        
        assert response.status_code == 401
        assert "Token expired" in data["error"] or "Invalid token" in data["error"]

    def test_update_deck_due_cards_called_for_existing_user(self):
        """Test that update_deck_due_cards is called when an existing user logs in."""
        existing_user = {
            "u_id": "google-id-123",
            "email": "test@example.com",
            "display_name": "Test User",
            "timezone": "UTC",
            "new_cards_per_day": 10,
            "desired_retention": 0.9,
            "fsrs_parameters": None,
            "auto_optimize": True,
            "num_reviews_per_optimize": 256,
            "total_reviews": 0,
            "reviews_since_last_optimize": 0,
        }
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = existing_user

        with patch("services.auth_service.get_db_cursor") as mock_db, \
             patch("services.auth_service.FsrsService.update_deck_due_cards") as mock_update:
            mock_db.return_value.__enter__.return_value = mock_cursor
            from services.auth_service import AuthService
            AuthService.get_or_create_oauth_user("google-id-123", "test@example.com", "Test User")

        mock_update.assert_called_once_with("google-id-123")

    def test_update_deck_due_cards_called_for_new_user(self):
        """Test that update_deck_due_cards is called when a brand-new user is created."""
        new_user = {
            "u_id": "google-id-456",
            "email": "new@example.com",
            "display_name": "New User",
            "timezone": "UTC",
            "new_cards_per_day": 10,
            "desired_retention": 0.9,
            "fsrs_parameters": None,
            "auto_optimize": True,
            "num_reviews_per_optimize": 256,
            "total_reviews": 0,
            "reviews_since_last_optimize": 0,
        }
        mock_cursor = MagicMock()
        # First fetchone → None (user does not exist yet); second → new user row from INSERT RETURNING
        mock_cursor.fetchone.side_effect = [None, new_user]

        with patch("services.auth_service.get_db_cursor") as mock_db, \
             patch("services.auth_service.FsrsService.update_deck_due_cards") as mock_update:
            mock_db.return_value.__enter__.return_value = mock_cursor
            from services.auth_service import AuthService
            AuthService.get_or_create_oauth_user("google-id-456", "new@example.com", "New User")

        mock_update.assert_called_once_with("google-id-456")


class TestRefreshTokenUnit:
    """Unit tests for token refresh without database."""
    
    def test_refresh_token_missing(self, client, monkeypatch):
        """Test error handling when refresh token is missing."""
        monkeypatch.setenv("JWT_SECRET", "test-secret")
        
        # send POST request without refresh token
        response = client.post("/auth/refresh")
        
        data = json.loads(response.data)
        
        # verify 401 Unauthorized
        assert response.status_code == 401
        assert "Authorization header missing" in data["error"] or "Token required" in data["error"] or "refresh" in data["error"]
    
    def test_refresh_token_invalid(self, client, monkeypatch):
        """Test error handling when refresh token is invalid."""
        monkeypatch.setenv("JWT_SECRET", "test-secret")
        
        # send POST request with invalid token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid-refresh-token"}
        )
        
        data = json.loads(response.data)
        
        # verify 401 Unauthorized
        assert response.status_code == 401


class TestLogoutUnit:
    """Unit tests for logout without database."""
    
    def test_logout_without_token(self, client, monkeypatch):
        """Test error handling when access token is missing during logout."""
        monkeypatch.setenv("JWT_SECRET", "test-secret")
        
        # send POST request without authorization header
        response = client.post("/auth/logout")
        
        data = json.loads(response.data)
        
        # verify 401 Unauthorized
        assert response.status_code == 401
        assert "Token required" in data["error"] or "authorization" in data["error"].lower()
    
    def test_logout_with_invalid_token(self, client, monkeypatch):
        """Test error handling when access token is invalid during logout."""
        monkeypatch.setenv("JWT_SECRET", "test-secret")
        
        # send POST request with invalid authorization header
        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        data = json.loads(response.data)
        
        # verify 401 Unauthorized
        assert response.status_code == 401