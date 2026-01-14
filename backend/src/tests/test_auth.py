from unittest.mock import patch

class TestGoogleOAuthWithoutDB:
    """Basic Google OAuth tests that work without database."""
    
    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_token_verification(self, mock_verify, client):
        """Test that Google token is verified correctly."""
        mock_verify.return_value = {
            'sub': 'google-id-123',
            'email': 'test@example.com',
            'iss': 'accounts.google.com'
        }
        
        response = client.post('/auth/google', json={
            'id_token': 'fake-google-token'
        })

        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        assert response.status_code == 200
        assert 'access_token' in response.json['tokens']
        assert 'refresh_token' in response.json['tokens']
    
    def test_google_oauth_missing_token(self, client):
        """Test that missing token returns 400."""
        response = client.post('/auth/google', json={})
        
        assert response.status_code == 400
        assert 'Token required' in response.json['error']
    
    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_oauth_invalid_token(self, mock_verify, client):
        """Test that invalid token returns 401."""
        mock_verify.side_effect = ValueError('Invalid token')
        
        response = client.post('/auth/google', json={
            'id_token': 'invalid-token'
        })
        
        assert response.status_code == 401

class TestRefreshToken:
    """Tests for token refresh that work without database."""
    
    def test_refresh_token_missing(self, client):
        """Test refreshing token without token."""
        response = client.post('/auth/refresh')
        
        assert response.status_code == 401

class TestLogout:
    """Tests for logout that work without database."""
    
    def test_logout_without_token(self, client):
        """Test logout without token."""
        response = client.post('/auth/logout')
        
        assert response.status_code == 401
