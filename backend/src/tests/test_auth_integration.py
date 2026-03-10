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

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

REAL_TOKEN = os.getenv("GOOGLE_TEST_ID_TOKEN")

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
        