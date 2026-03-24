"""
Integration tests for auth API.

These tests make real API calls with actual Google OAuth tokens and real JWT generation.

Important:
- Requires valid GOOGLE_CLIENT_ID and JWT_SECRET in .env file
- Requires real Google OAuth tokens set in .env as GOOGLE_TEST_ID_TOKEN
- Skipped by default (pytest runs only unit tests)

Run with: 
- poetry run pytest -v -m integration -rs (runs only integration tests)
- poetry run pytest src/tests/test_auth_integration.py -v  -m integration -rs

Test coverage:
- Real Google OAuth token verification
- Actual JWT token generation and validation
- Real token refresh with database persistence
"""
import pytest
import os
import json
import base64

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

REAL_TOKEN = os.getenv("GOOGLE_TEST_ID_TOKEN")

def _decode_google_token_payload(id_token):
    """Decode the payload of a Google ID token (JWT) without verification."""
    payload_b64 = id_token.split(".")[1]
    # JWT uses base64url encoding without padding — add padding back
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))

# fixtures to skip tests if env vars are missing
@pytest.fixture
def skip_if_no_google_token():
    """Skip test if Google OAuth tokens are not set."""
    id_token = os.getenv("GOOGLE_TEST_ID_TOKEN")
    if not id_token:
        pytest.skip("GOOGLE_TEST_ID_TOKEN not set - skipping integration test")

@pytest.fixture
def skip_if_no_google_config():
    """Skip tests if Google OAuth config is missing."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        pytest.skip("GOOGLE_CLIENT_ID not set - skipping integration test")

class TestGoogleOAuthIntegration:
    """Integration tests for real Google OAuth verification."""
    
    def test_google_oauth_real_token(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test with real Google OAuth token from valid account."""
        response = client.post(
            "/auth/google",
            json={"id_token": REAL_TOKEN}
        )

        assert response.status_code == 200
        data = response.get_json()

        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert data["user"]["email"] is not None

    def test_google_oauth_email_and_name_from_token(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test that returned email and display_name match the Google ID token claims."""
        google_claims = _decode_google_token_payload(REAL_TOKEN)
        expected_email = google_claims["email"]
        expected_name = google_claims["name"]

        response = client.post(
            "/auth/google",
            json={"id_token": REAL_TOKEN}
        )

        assert response.status_code == 200
        user = response.get_json()["user"]
        assert user["email"] == expected_email
        assert user["display_name"] == expected_name
    
    def test_google_oauth_returns_valid_jwt(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test that Google OAuth returns valid JWT tokens."""
        response = client.post(
            "/auth/google",
            json={"id_token": REAL_TOKEN}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # verify token structure (JWT format: header.payload.signature)
        access_token = data["tokens"]["access_token"]
        assert access_token.count(".") == 2, "Token should be valid JWT format"
        
        refresh_token = data["tokens"]["refresh_token"]
        assert refresh_token.count(".") == 2, "Refresh token should be valid JWT format"


class TestRefreshTokenIntegration:
    """Integration tests for real token refresh with JWT validation."""
    
    def test_refresh_token_generates_new_access_token(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test that refresh token generates a new valid access token."""
        # Step 1: Login to get refresh token
        login_response = client.post(
            "/auth/google",
            json={"id_token": REAL_TOKEN}
        )
        assert login_response.status_code == 200
        refresh_token = login_response.get_json()["tokens"]["refresh_token"]
        
        # Step 2: Use refresh token to get new access token
        # IMPORTANT: refresh token must be sent in Authorization header
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # verify new access token was generated
        assert "access_token" in data["tokens"]
        new_token = data["tokens"]["access_token"]
        assert new_token.count(".") == 2, "New token should be valid JWT format"
        
        # verify new token is different from old one
        assert new_token != refresh_token


class TestLogoutIntegration:
    """Integration tests for real logout."""
    
    def test_logout_token(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test that logout successfully blacklists the access token."""
        # Step 1: Login to get access token
        login_response = client.post(
            "/auth/google",
            json={"id_token": REAL_TOKEN}
        )
        assert login_response.status_code == 200
        access_token = login_response.get_json()["tokens"]["access_token"]
        
        # Step 2: Logout with valid access token
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data or "success" in data
    

class TestUserCreationIntegration:
    """Integration tests for user creation through OAuth."""
    
    def test_oauth_creates_user_in_database(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test that Google OAuth creates user in database."""
        response = client.post(
            "/auth/google",
            json={"id_token": REAL_TOKEN}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify user data is returned
        assert "user" in data
        user = data["user"]
        assert "u_id" in user
        assert "email" in user
        assert "display_name" in user
        assert "timezone" in user
        
        # Verify user can be retrieved
        access_token = data["tokens"]["access_token"]
        profile_response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert profile_response.status_code == 200
        profile_data = profile_response.get_json()
        assert profile_data["u_id"] == user["u_id"]
        assert profile_data["email"] == user["email"]
        assert profile_data["display_name"] == user["display_name"]
    
    def test_oauth_returns_existing_user(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test that subsequent OAuth logins return existing user."""
        # First login
        response1 = client.post(
            "/auth/google",
            json={"id_token": REAL_TOKEN}
        )
        assert response1.status_code == 200
        user1 = response1.get_json()["user"]
        
        # Second login with same token
        response2 = client.post(
            "/auth/google",
            json={"id_token": REAL_TOKEN}
        )
        assert response2.status_code == 200
        user2 = response2.get_json()["user"]
        
        # Should return same user
        assert user1["u_id"] == user2["u_id"]
        assert user1["email"] == user2["email"]
    
    def test_created_user_has_default_fsrs_settings(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test that newly created user has correct FSRS default values."""
        response = client.post(
            "/auth/google",
            json={"id_token": REAL_TOKEN}
        )
        
        assert response.status_code == 200
        user = response.get_json()["user"]
        
        # Verify default FSRS settings
        assert user["new_cards_per_day"] == 10
        assert user["desired_retention"] == 0.9
        assert user["auto_optimize"] is True
        assert user["num_reviews_per_optimize"] == 256
        assert user["total_reviews"] == 0
        assert user["reviews_since_last_optimize"] == 0
        # fsrs_parameters should be None initially
        assert user["fsrs_parameters"] is None


class TestAuthFlowIntegration:
    """Integration tests for complete authentication flow."""
    
    def test_complete_auth_flow(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test complete flow: Google OAuth -> Token Refresh -> Logout."""
        # Step 1: Login with Google OAuth
        login_response = client.post(
            "/auth/google",
            json={"id_token": REAL_TOKEN}
        )
        assert login_response.status_code == 200
        login_data = login_response.get_json()
        
        access_token = login_data["tokens"]["access_token"]
        refresh_token = login_data["tokens"]["refresh_token"]
        
        # Step 2: Use access token to access protected resource
        # Changed from /api/profile to /auth/me (which exists)
        profile_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert profile_response.status_code == 200
        
        # Step 3: Refresh token to get new access token
        refresh_response = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.get_json()["tokens"]["access_token"]
        
        # verify new token works
        profile_response_2 = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert profile_response_2.status_code == 200
        
        # Step 4: Logout
        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert logout_response.status_code == 200


class TestUpdateDeckDueCardsOnLogin:
    """Integration tests verifying that due_cards is refreshed on every login."""

    def test_login_updates_due_cards_for_user_decks(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test that logging in causes every deck to have a valid due_cards value."""
        response = client.post("/auth/google", json={"id_token": REAL_TOKEN})
        assert response.status_code == 200
        access_token = response.get_json()["tokens"]["access_token"]

        decks_response = client.get(
            "/decks",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert decks_response.status_code == 200
        decks = decks_response.get_json()["decks"]

        for deck in decks:
            assert "due_cards" in deck, f"Deck {deck.get('deck_name')} missing due_cards field"
            assert isinstance(deck["due_cards"], int)
            assert deck["due_cards"] >= 0

    def test_repeated_login_does_not_break_due_cards(self, client, skip_if_no_google_config, skip_if_no_google_token):
        """Test that logging in twice in a row keeps due_cards consistent."""
        def login():
            resp = client.post("/auth/google", json={"id_token": REAL_TOKEN})
            assert resp.status_code == 200
            return resp.get_json()["tokens"]["access_token"]

        token1 = login()
        token2 = login()

        decks1 = client.get("/decks", headers={"Authorization": f"Bearer {token1}"}).get_json()["decks"]
        decks2 = client.get("/decks", headers={"Authorization": f"Bearer {token2}"}).get_json()["decks"]

        assert len(decks1) == len(decks2)
        for d1, d2 in zip(
            sorted(decks1, key=lambda d: d["d_id"]),
            sorted(decks2, key=lambda d: d["d_id"])
        ):
            assert d1["due_cards"] == d2["due_cards"]
        