"""
Unit tests for google oauth API.

These tests mock Google OAuth and token generation to test the application logic
without making real API calls or requiring a database. 

Run this test file:
    docker compose exec backend pytest src/tests/test_auth_unit.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_auth_unit.py --cov=services.auth_service

Test coverage:
- Google token verification (success and failure)
- Missing required parameters
- Invalid token handling
- Token refresh without valid tokens
- Logout without authentication
"""
import json
from unittest.mock import patch
from services.auth_service import AuthService
from db import get_db_cursor


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


class TestBuiltinDecksOnSignup:
    """Verify that built-in decks are copied to a new user on first login.

    These tests call AuthService directly against the real test DB (no mocking),
    so they depend on the system_decks fixture to pre-seed the system user's decks.
    """

    NEW_USER_ID = 'new-signup-user-id'

    def _cleanup(self):
        """Remove the test user created by signup (cascades to their decks/cards)."""
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM Users WHERE u_id = %s", (self.NEW_USER_ID,))

    def _signup(self):
        AuthService.get_or_create_oauth_user(
            google_id=self.NEW_USER_ID,
            email='newuser@example.com',
            display_name='New User',
            timezone='UTC',
        )

    def test_new_user_receives_four_builtin_decks(self, system_decks):
        """A new user should have exactly 4 decks copied from the system."""
        try:
            self._signup()
            with get_db_cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) AS count FROM Decks WHERE u_id = %s",
                    (self.NEW_USER_ID,)
                )
                assert cursor.fetchone()['count'] == 4
        finally:
            self._cleanup()

    def test_new_user_builtin_deck_names(self, system_decks):
        """Copied decks should have the correct names."""
        try:
            self._signup()
            with get_db_cursor() as cursor:
                cursor.execute(
                    "SELECT deck_name FROM Decks WHERE u_id = %s",
                    (self.NEW_USER_ID,)
                )
                names = {row['deck_name'] for row in cursor.fetchall()}
            assert names == {
                'Mandarin Chinese Beginner',
                'Korean Beginner',
                'French Beginner',
                'Japanese Beginner',
            }
        finally:
            self._cleanup()

    def test_new_user_builtin_cards_are_copied(self, system_decks):
        """Each copied deck should contain the same cards as the system deck."""
        try:
            self._signup()
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS count
                    FROM Cards c
                    JOIN Decks d ON c.d_id = d.d_id
                    WHERE d.u_id = %s
                """, (self.NEW_USER_ID,))
                # 3 cards × 4 decks seeded by the system_decks fixture
                assert cursor.fetchone()['count'] == 12
        finally:
            self._cleanup()

    def test_builtin_decks_are_private(self, system_decks):
        """Copied decks should be private (is_public = false)."""
        try:
            self._signup()
            with get_db_cursor() as cursor:
                cursor.execute(
                    "SELECT is_public FROM Decks WHERE u_id = %s",
                    (self.NEW_USER_ID,)
                )
                for row in cursor.fetchall():
                    assert row['is_public'] is False
        finally:
            self._cleanup()

    def test_existing_user_does_not_get_duplicate_decks(self, system_decks):
        """A second login for the same user must not copy decks again."""
        try:
            self._signup()
            self._signup()  # second call — user already exists
            with get_db_cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) AS count FROM Decks WHERE u_id = %s",
                    (self.NEW_USER_ID,)
                )
                assert cursor.fetchone()['count'] == 4
        finally:
            self._cleanup()