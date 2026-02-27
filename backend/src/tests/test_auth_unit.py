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
from unittest.mock import patch


# ----------------------------
# Fake API Response Fixtures
# ----------------------------
def fake_google_token_valid(*args, **kwargs):
    """Mock successful Google token verification."""
    return {
        'sub': 'google-id-123',
        'email': 'test@example.com',
        'iss': 'accounts.google.com'
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
        
        response = client.post(
            "/auth/google",
            json={"id_token": "fake-google-token"}
        )
        
        data = json.loads(response.data)
        
        # verify successful response with tokens
        assert response.status_code == 200
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
    
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