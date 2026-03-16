"""Unit tests for image service.

These tests mock the Unsplash API responses to test the application logic
without making real API calls.

Run this test file:
    docker compose exec backend pytest src/tests/test_images_unit.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_images_unit.py --cov=services.image_service
"""
import pytest
from unittest.mock import Mock, patch
from services.image_service import UnsplashService


@pytest.fixture
def mock_unsplash_response():
    """Mock response from Unsplash API for search"""
    return {
        "total": 100,
        "total_pages": 10,
        "results": [
            {
                "id": "photo1",
                "description": "A beautiful landscape",
                "alt_description": "mountain view",
                "urls": {
                    "raw": "https://images.unsplash.com/photo1?raw",
                    "full": "https://images.unsplash.com/photo1?full",
                    "regular": "https://images.unsplash.com/photo1?regular",
                    "small": "https://images.unsplash.com/photo1?small",
                    "thumb": "https://images.unsplash.com/photo1?thumb"
                },
                "width": 4000,
                "height": 3000,
                "color": "#2C3E50",
                "blur_hash": "LKO2?U%2Tw=w]~RBVZRi};RPxuwH",
                "user": {
                    "name": "John Doe",
                    "username": "johndoe",
                    "links": {
                        "html": "https://unsplash.com/@johndoe"
                    },
                    "profile_image": {
                        "small": "https://images.unsplash.com/profile-john?small"
                    }
                },
                "links": {
                    "html": "https://unsplash.com/photos/photo1",
                    "download_location": "https://api.unsplash.com/photos/photo1/download"
                }
            }
        ]
    }


class TestUnsplashServiceInit:
    """Tests for UnsplashService initialization"""
    
    def test_init_with_access_key(self):
        """Test initialization with provided access key"""
        service = UnsplashService(access_key="test_key_123")
        assert service.access_key == "test_key_123"
        assert service.headers["Authorization"] == "Client-ID test_key_123"
        assert service.headers["Accept-Version"] == "v1"
    
    @patch.dict('os.environ', {'UNSPLASH_ACCESS_KEY': 'env_key_456'})
    def test_init_with_env_variable(self):
        """Test initialization with environment variable"""
        service = UnsplashService()
        assert service.access_key == "env_key_456"
        assert service.headers["Authorization"] == "Client-ID env_key_456"
        assert service.timeout_seconds == 10.0

    @patch.dict('os.environ', {'UNSPLASH_ACCESS_KEY': 'env_key_456', 'UNSPLASH_TIMEOUT_SECONDS': '3.5'})
    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout from environment variable"""
        service = UnsplashService()
        assert service.timeout_seconds == 3.5
    
    @patch.dict('os.environ', {}, clear=True)
    def test_init_without_key_raises_error(self):
        """Test initialization without key raises ValueError"""
        with pytest.raises(ValueError, match="UNSPLASH_ACCESS_KEY not set"):
            UnsplashService()


class TestSearchPhotos:
    """Tests for search_photos method"""
    
    @patch('services.image_service.requests.get')
    def test_search_photos_success(self, mock_get, mock_unsplash_response):
        """Test successful photo search"""
        mock_response = Mock()
        mock_response.json.return_value = mock_unsplash_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = UnsplashService(access_key="test_key")
        result = service.search_photos(query="nature", page=1, per_page=10)
        
        assert result == mock_unsplash_response
        assert result["total"] == 100
        assert len(result["results"]) == 1
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://api.unsplash.com/search/photos" in call_args[0]
        assert call_args[1]["params"]["query"] == "nature"
        assert call_args[1]["params"]["page"] == 1
        assert call_args[1]["params"]["per_page"] == 10
        assert call_args[1]["timeout"] == 10.0
    
    @patch('services.image_service.requests.get')
    def test_search_photos_with_filters(self, mock_get, mock_unsplash_response):
        """Test photo search with orientation and color filters"""
        mock_response = Mock()
        mock_response.json.return_value = mock_unsplash_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = UnsplashService(access_key="test_key")
        result = service.search_photos(
            query="sunset",
            orientation="landscape",
            color="orange",
            order_by="latest"
        )
        
        # Verify filters are passed
        call_args = mock_get.call_args[1]["params"]
        assert call_args["orientation"] == "landscape"
        assert call_args["color"] == "orange"
        assert call_args["order_by"] == "latest"
        assert mock_get.call_args[1]["timeout"] == 10.0
    
    @patch('services.image_service.requests.get')
    def test_search_photos_respects_max_per_page(self, mock_get, mock_unsplash_response):
        """Test that per_page is capped at 30"""
        mock_response = Mock()
        mock_response.json.return_value = mock_unsplash_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = UnsplashService(access_key="test_key")
        service.search_photos(query="test", per_page=100)
        
        # Verify per_page is capped at 30
        call_args = mock_get.call_args[1]["params"]
        assert call_args["per_page"] == 30
        assert mock_get.call_args[1]["timeout"] == 10.0
    
    @patch('services.image_service.requests.get')
    def test_search_photos_request_exception(self, mock_get):
        """Test handling of request exceptions"""
        mock_get.side_effect = Exception("Network error")
        
        service = UnsplashService(access_key="test_key")
        
        with pytest.raises(Exception, match="Failed to search Unsplash photos"):
            service.search_photos(query="nature")


class TestTrackDownload:
    """Tests for track_download method"""
    
    @patch('services.image_service.requests.get')
    def test_track_download_success(self, mock_get):
        """Test successful download tracking"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "url": "https://unsplash.com/photos/abc123/download"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = UnsplashService(access_key="test_key")
        result = service.track_download(photo_id="abc123")
        
        assert "url" in result
        
        # Verify API call
        mock_get.assert_called_once()
        assert "https://api.unsplash.com/photos/abc123/download" in mock_get.call_args[0]
        assert mock_get.call_args[1]["timeout"] == 10.0
    
    @patch('services.image_service.requests.get')
    def test_track_download_request_exception(self, mock_get):
        """Test handling of request exceptions"""
        mock_get.side_effect = Exception("Download tracking failed")
        
        service = UnsplashService(access_key="test_key")
        
        with pytest.raises(Exception, match="Failed to track download"):
            service.track_download(photo_id="abc123")


class TestFormatPhotoResponse:
    """Tests for format_photo_response static method"""
    
    def test_format_photo_response_complete(self):
        """Test formatting with all fields present"""
        raw_photo = {
            "id": "photo123",
            "description": "A test photo",
            "alt_description": "test image",
            "urls": {
                "raw": "https://raw.url",
                "full": "https://full.url",
                "regular": "https://regular.url",
                "small": "https://small.url",
                "thumb": "https://thumb.url"
            },
            "width": 4000,
            "height": 3000,
            "color": "#FF5733",
            "blur_hash": "LEHV6nWB2yk8pyo0adR*.7kCMdnj",
            "user": {
                "name": "Test User",
                "username": "testuser",
                "links": {
                    "html": "https://unsplash.com/@testuser"
                },
                "profile_image": {
                    "small": "https://profile.url"
                }
            },
            "links": {
                "html": "https://unsplash.com/photos/photo123",
                "download_location": "https://api.unsplash.com/photos/photo123/download"
            }
        }
        
        result = UnsplashService.format_photo_response(raw_photo)
        
        assert result["id"] == "photo123"
        assert result["description"] == "A test photo"
        assert result["urls"]["raw"] == "https://raw.url"
        assert result["urls"]["regular"] == "https://regular.url"
        assert result["width"] == 4000
        assert result["height"] == 3000
        assert result["color"] == "#FF5733"
        assert result["blur_hash"] == "LEHV6nWB2yk8pyo0adR*.7kCMdnj"
        assert result["user"]["name"] == "Test User"
        assert result["user"]["username"] == "testuser"
        assert result["links"]["html"] == "https://unsplash.com/photos/photo123"
    
    def test_format_photo_response_missing_description(self):
        """Test formatting falls back to alt_description when description is missing"""
        raw_photo = {
            "id": "photo123",
            "description": None,
            "alt_description": "alternative description",
            "urls": {},
            "user": {},
            "links": {}
        }
        
        result = UnsplashService.format_photo_response(raw_photo)
        
        assert result["description"] == "alternative description"
    
    def test_format_photo_response_missing_fields(self):
        """Test formatting handles missing fields gracefully"""
        raw_photo = {
            "id": "photo123",
            "urls": {},
            "user": {},
            "links": {}
        }
        
        result = UnsplashService.format_photo_response(raw_photo)
        
        assert result["id"] == "photo123"
        assert result["description"] is None
        assert result["urls"]["raw"] is None
        assert result["user"]["name"] is None
        assert result["links"]["html"] is None
    
    def test_format_photo_response_nested_missing_fields(self):
        """Test formatting handles deeply nested missing fields"""
        raw_photo = {
            "id": "photo123",
            "user": {
                "name": "User"
                # Missing username, links, profile_image
            },
            "urls": {},
            "links": {}
        }
        
        result = UnsplashService.format_photo_response(raw_photo)
        
        assert result["user"]["name"] == "User"
        assert result["user"]["username"] is None
        assert result["user"]["profile_url"] is None
        assert result["user"]["profile_image"] is None
