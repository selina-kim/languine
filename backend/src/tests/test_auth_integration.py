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
from time import time

import pytest
import os
import json
import base64
from flask_jwt_extended import create_access_token
from main import create_app
from db import get_db_cursor

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

    try:
        exp = _decode_google_token_payload(id_token).get("exp", 0)
        if exp < time():
            pytest.skip("GOOGLE_TEST_ID_TOKEN has expired - refresh the token to run these tests")
    except Exception:
        pytest.skip("GOOGLE_TEST_ID_TOKEN is malformed - skipping integration test")

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


# ---------------------------------------------------------------------------
# Built-in deck copy-on-signup integration tests
# ---------------------------------------------------------------------------

_BUILTIN_TEST_USER_ID = "builtin-decks-test-user"

_EXPECTED_DECK_NAMES = {
    "Mandarin Chinese Beginner",
    "Korean Beginner",
    "French Beginner",
    "Japanese Beginner",
}

# Number of cards seeded per system deck in the system_decks conftest fixture
_CARDS_PER_DECK = 3


def _fake_builtin_token(*args, **kwargs):
    """Return fake Google token payload for _BUILTIN_TEST_USER_ID."""
    return {
        "sub": _BUILTIN_TEST_USER_ID,
        "email": "builtin-test@example.com",
        "name": "Builtin Test User",
        "iss": "accounts.google.com",
    }


def _delete_builtin_test_user():
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM Users WHERE u_id = %s", (_BUILTIN_TEST_USER_ID,))


@pytest.fixture
def builtin_app(system_decks):
    """App backed by the real DB with system decks already seeded."""
    os.environ["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID", "test-client-id")
    os.environ["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "test-secret-key")
    application = create_app()
    application.config["TESTING"] = True
    yield application


@pytest.fixture
def builtin_client(builtin_app):
    return builtin_app.test_client()


@pytest.fixture
def builtin_auth_headers(builtin_app):
    """JWT for _BUILTIN_TEST_USER_ID so deck endpoints can be called directly."""
    with builtin_app.app_context():
        token = create_access_token(identity=_BUILTIN_TEST_USER_ID)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=False)
def builtin_cleanup():
    """Remove the test user before and after each test that requests this fixture."""
    _delete_builtin_test_user()
    yield
    _delete_builtin_test_user()


def _do_signup(client, monkeypatch):
    """POST /auth/google with a mocked token for _BUILTIN_TEST_USER_ID."""
    monkeypatch.setattr(
        "routes.auth.id_token.verify_oauth2_token",
        _fake_builtin_token,
    )
    return client.post("/auth/google", json={"id_token": "fake-token"})


class TestBuiltinDecksOnSignupIntegration:
    """Verify that built-in decks are copied to a new user on first login.

    Google token verification is mocked; all DB interactions use the real
    test database seeded by the session-scoped system_decks fixture.
    """

    def test_signup_returns_200(self, builtin_client, builtin_cleanup, monkeypatch):
        """POST /auth/google succeeds and returns user + tokens."""
        response = _do_signup(builtin_client, monkeypatch)
        assert response.status_code == 200
        data = response.get_json()
        assert "user" in data
        assert "tokens" in data

    def test_new_user_receives_four_decks(
        self, builtin_client, builtin_auth_headers, builtin_cleanup, monkeypatch
    ):
        """Signing up copies exactly 4 built-in decks to the new user."""
        _do_signup(builtin_client, monkeypatch)

        response = builtin_client.get("/decks", headers=builtin_auth_headers)
        assert response.status_code == 200
        assert len(response.get_json()["decks"]) == 4

    def test_new_user_deck_names_are_correct(
        self, builtin_client, builtin_auth_headers, builtin_cleanup, monkeypatch
    ):
        """The copied deck names match the four expected system deck names."""
        _do_signup(builtin_client, monkeypatch)

        response = builtin_client.get("/decks", headers=builtin_auth_headers)
        names = {d["deck_name"] for d in response.get_json()["decks"]}
        assert names == _EXPECTED_DECK_NAMES

    def test_new_user_decks_are_private(
        self, builtin_client, builtin_auth_headers, builtin_cleanup, monkeypatch
    ):
        """Copied decks are private (is_public = false)."""
        _do_signup(builtin_client, monkeypatch)

        response = builtin_client.get("/decks", headers=builtin_auth_headers)
        for deck in response.get_json()["decks"]:
            assert deck["is_public"] is False, (
                f"Expected {deck['deck_name']} to be private"
            )

    def test_each_deck_has_correct_card_count(
        self, builtin_client, builtin_auth_headers, builtin_cleanup, monkeypatch
    ):
        """The card_count field in the deck list equals _CARDS_PER_DECK for each deck."""
        _do_signup(builtin_client, monkeypatch)

        response = builtin_client.get("/decks", headers=builtin_auth_headers)
        for deck in response.get_json()["decks"]:
            assert deck["card_count"] == _CARDS_PER_DECK, (
                f"{deck['deck_name']}: expected {_CARDS_PER_DECK} cards, "
                f"got {deck['card_count']}"
            )

    def test_deck_detail_endpoint_returns_cards(
        self, builtin_client, builtin_auth_headers, builtin_cleanup, monkeypatch
    ):
        """GET /decks/<id> returns the correct number of cards for each deck."""
        _do_signup(builtin_client, monkeypatch)

        decks = builtin_client.get("/decks", headers=builtin_auth_headers).get_json()["decks"]
        for deck in decks:
            response = builtin_client.get(
                f'/decks/{deck["d_id"]}', headers=builtin_auth_headers
            )
            assert response.status_code == 200
            cards = response.get_json()["cards"]
            assert len(cards) == _CARDS_PER_DECK, (
                f"{deck['deck_name']}: expected {_CARDS_PER_DECK} cards in detail view"
            )

    def test_cards_are_immediately_reviewable(
        self, builtin_client, builtin_auth_headers, builtin_cleanup, monkeypatch
    ):
        """Built-in cards have due_date = now, so at least one deck appears as due."""
        _do_signup(builtin_client, monkeypatch)

        response = builtin_client.get("/decks/due?limit=20", headers=builtin_auth_headers)
        assert response.status_code == 200
        assert len(response.get_json()["decks"]) > 0, (
            "Expected at least one deck with due cards immediately after signup"
        )

    def test_second_signup_does_not_duplicate_decks(
        self, builtin_client, builtin_auth_headers, builtin_cleanup, monkeypatch
    ):
        """A second login for the same user must not copy decks again."""
        _do_signup(builtin_client, monkeypatch)
        _do_signup(builtin_client, monkeypatch)

        response = builtin_client.get("/decks", headers=builtin_auth_headers)
        assert response.status_code == 200
        assert len(response.get_json()["decks"]) == 4

    def test_signup_response_contains_user_fields(
        self, builtin_client, builtin_cleanup, monkeypatch
    ):
        """The signup response embeds the full user object with expected fields."""
        response = _do_signup(builtin_client, monkeypatch)
        user = response.get_json()["user"]

        for field in (
            "u_id", "email", "display_name", "timezone",
            "new_cards_per_day", "desired_retention",
            "auto_optimize", "num_reviews_per_optimize",
            "total_reviews", "reviews_since_last_optimize",
        ):
            assert field in user, f"Missing field '{field}' in signup response"

        assert user["u_id"] == _BUILTIN_TEST_USER_ID
        assert user["email"] == "builtin-test@example.com"
        assert user["display_name"] == "Builtin Test User"


# ---------------------------------------------------------------------------
# Edge-case and protected-endpoint coverage tests (no real Google token needed)
# ---------------------------------------------------------------------------

class TestGoogleOAuthEdgeCases:
    """Cover error-handling branches in POST /auth/google."""

    def test_missing_token_returns_400(self, builtin_client):
        """POST /auth/google with no id_token field returns 400."""
        response = builtin_client.post("/auth/google", json={})
        assert response.status_code == 400
        assert response.get_json()["error"] == "Token required"

    def test_null_token_returns_400(self, builtin_client):
        """POST /auth/google with null id_token returns 400."""
        response = builtin_client.post("/auth/google", json={"id_token": None})
        assert response.status_code == 400
        assert response.get_json()["error"] == "Token required"

    def test_invalid_token_returns_401(self, builtin_client, monkeypatch):
        """POST /auth/google with a token that fails verification returns 401."""
        def fake_raise_value_error(*args, **kwargs):
            raise ValueError("Invalid token: signature mismatch")

        monkeypatch.setattr(
            "routes.auth.id_token.verify_oauth2_token",
            fake_raise_value_error,
        )
        response = builtin_client.post("/auth/google", json={"id_token": "bad-token"})
        assert response.status_code == 401
        assert "error" in response.get_json()


class TestProtectedEndpoints:
    """Cover GET /auth/me and POST /auth/logout using pre-built JWT tokens."""

    def test_get_current_user_returns_200(self, builtin_client, builtin_auth_headers):
        """GET /auth/me with a valid access token returns 200 and the user's u_id."""
        response = builtin_client.get("/auth/me", headers=builtin_auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "user" in data
        assert data["user"]["u_id"] == _BUILTIN_TEST_USER_ID

    def test_get_current_user_without_token_returns_401(self, builtin_client):
        """GET /auth/me without an Authorization header returns 401."""
        response = builtin_client.get("/auth/me")
        assert response.status_code == 401

    def test_logout_returns_success_message(self, builtin_client, builtin_auth_headers):
        """POST /auth/logout with a valid access token returns 200."""
        response = builtin_client.post("/auth/logout", headers=builtin_auth_headers)
        assert response.status_code == 200
        assert response.get_json()["message"] == "Logged out successfully"

    def test_logout_without_token_returns_401(self, builtin_client):
        """POST /auth/logout without an Authorization header returns 401."""
        response = builtin_client.post("/auth/logout")
        assert response.status_code == 401


class TestRefreshEndpointMocked:
    """Cover POST /auth/refresh using a refresh JWT (no real Google token needed)."""

    def test_refresh_with_valid_refresh_token(self, builtin_app, builtin_client):
        """POST /auth/refresh with a valid refresh token returns a new access token."""
        from flask_jwt_extended import create_refresh_token

        with builtin_app.app_context():
            refresh_tok = create_refresh_token(identity=_BUILTIN_TEST_USER_ID)

        response = builtin_client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_tok}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert data["tokens"]["access_token"].count(".") == 2

    def test_refresh_with_access_token_returns_401(self, builtin_client, builtin_auth_headers):
        """POST /auth/refresh with an access token (not a refresh token) returns 401."""
        response = builtin_client.post("/auth/refresh", headers=builtin_auth_headers)
        assert response.status_code == 401

    def test_refresh_without_token_returns_401(self, builtin_client):
        """POST /auth/refresh without any token returns 401."""
        response = builtin_client.post("/auth/refresh")
        assert response.status_code == 401
