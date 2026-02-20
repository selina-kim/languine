"""Integration tests for image routes.

These tests verify the image search endpoints with mocked Unsplash service.

Run this test file:
    docker compose exec backend pytest src/tests/test_images_integration.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_images_integration.py --cov=routes.images
"""
import pytest
import json
from unittest.mock import patch, Mock


@pytest.fixture
def mock_unsplash_service():
    """Mock UnsplashService for testing routes"""
    import os
    os.environ['UNSPLASH_ACCESS_KEY'] = 'test_key'
    with patch('routes.images.UnsplashService') as mock_service:
        # Keep format_photo_response as the real function
        from services.image_service import UnsplashService
        mock_service.format_photo_response = UnsplashService.format_photo_response
        yield mock_service


def test_search_images_success(client, mock_unsplash_service):
    """Test successful image search"""
    mock_instance = Mock()
    mock_instance.search_photos.return_value = {
        "total": 100,
        "total_pages": 10,
        "results": [
            {
                "id": "photo1",
                "description": "Test photo",
                "urls": {"regular": "https://test.url"},
                "width": 3000,
                "height": 2000,
                "color": "#123456",
                "blur_hash": "ABC123",
                "user": {"name": "Test User", "username": "testuser", "links": {"html": "https://test"}, "profile_image": {"small": "https://test"}},
                "links": {"html": "https://test", "download_location": "https://test"}
            }
        ]
    }
    mock_unsplash_service.return_value = mock_instance
    
    response = client.get("/images/search?query=nature&per_page=10&page=1")
    
    if response.status_code != 200:
        print(f"Error response: {response.data}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["total"] == 100
    assert data["total_pages"] == 10
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "photo1"


def test_search_images_missing_query(client):
    """Test search with missing query parameter"""
    response = client.get("/images/search")
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "Missing query parameter" in data["error"]


def test_search_images_invalid_order_by(client):
    """Test search with invalid order_by parameter"""
    response = client.get("/images/search?query=nature&order_by=invalid")
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "order_by must be" in data["error"]


def test_search_images_invalid_orientation(client):
    """Test search with invalid orientation parameter"""
    response = client.get("/images/search?query=nature&orientation=invalid")
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "orientation must be" in data["error"]


def test_search_images_with_valid_filters(client, mock_unsplash_service):
    """Test search with valid filter parameters"""
    mock_instance = Mock()
    mock_instance.search_photos.return_value = {
        "total": 50,
        "total_pages": 5,
        "results": []
    }
    mock_unsplash_service.return_value = mock_instance
    
    response = client.get(
        "/images/search?query=sunset&orientation=landscape&color=orange&order_by=latest&page=2&per_page=20"
    )
    
    assert response.status_code == 200
    
    # Verify correct parameters were passed to service
    mock_instance.search_photos.assert_called_once_with(
        query="sunset",
        page=2,
        per_page=20,
        order_by="latest",
        orientation="landscape",
        color="orange"
    )


def test_search_images_service_initialization_error(client):
    """Test handling of service initialization error"""
    with patch('routes.images.UnsplashService') as mock_service:
        mock_service.side_effect = ValueError("UNSPLASH_ACCESS_KEY not set in environment")
        
        response = client.get("/images/search?query=nature")
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "UNSPLASH_ACCESS_KEY" in data["error"]


def test_search_images_api_exception(client, mock_unsplash_service):
    """Test handling of API exceptions"""
    mock_instance = Mock()
    mock_instance.search_photos.side_effect = Exception("API error")
    mock_unsplash_service.return_value = mock_instance
    
    response = client.get("/images/search?query=nature")
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data


def test_search_images_default_parameters(client, mock_unsplash_service):
    """Test search uses default parameters when not provided"""
    mock_instance = Mock()
    mock_instance.search_photos.return_value = {
        "total": 0,
        "total_pages": 0,
        "results": []
    }
    mock_unsplash_service.return_value = mock_instance
    
    response = client.get("/images/search?query=test")
    
    assert response.status_code == 200
    
    # Verify default parameters
    call_args = mock_instance.search_photos.call_args
    assert call_args[1]["page"] == 1
    assert call_args[1]["per_page"] == 10
    assert call_args[1]["order_by"] == "relevant"


def test_track_download_success(client, mock_unsplash_service):
    """Test successful download tracking"""
    mock_instance = Mock()
    mock_instance.track_download.return_value = {
        "url": "https://unsplash.com/photos/abc123/download"
    }
    mock_unsplash_service.return_value = mock_instance
    
    response = client.post(
        "/images/download",
        data=json.dumps({"photo_id": "abc123"}),
        content_type="application/json"
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "url" in data
    
    # Verify photo_id was passed to service
    mock_instance.track_download.assert_called_once_with("abc123")


def test_track_download_missing_photo_id(client):
    """Test download tracking with missing photo_id"""
    response = client.post(
        "/images/download",
        data=json.dumps({}),
        content_type="application/json"
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "Missing photo_id parameter" in data["error"]


def test_track_download_no_json_body(client):
    """Test download tracking with no JSON body"""
    response = client.post("/images/download")
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data

def test_track_download_service_initialization_error(client):
    """Test handling of service initialization error for download tracking"""
    with patch('routes.images.UnsplashService') as mock_service:
        mock_service.side_effect = ValueError("UNSPLASH_ACCESS_KEY not set in environment")
        
        response = client.post(
            "/images/download",
            data=json.dumps({"photo_id": "test123"}),
            content_type="application/json"
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data


def test_track_download_api_exception(client, mock_unsplash_service):
    """Test handling of API exceptions for download tracking"""
    mock_instance = Mock()
    mock_instance.track_download.side_effect = Exception("Tracking failed")
    mock_unsplash_service.return_value = mock_instance
    
    response = client.post(
        "/images/download",
        data=json.dumps({"photo_id": "test123"}),
        content_type="application/json"
    )
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data


def test_search_images_formats_results_correctly(client, mock_unsplash_service):
    """Test that search results are formatted using format_photo_response"""
    mock_instance = Mock()
    mock_instance.search_photos.return_value = {
        "total": 1,
        "total_pages": 1,
        "results": [
            {
                "id": "test_photo",
                "description": "Test",
                "urls": {"regular": "https://test.url"},
                "width": 1000,
                "height": 1000,
                "color": "#FFFFFF",
                "blur_hash": "TEST123",
                "user": {
                    "name": "Test",
                    "username": "test",
                    "links": {"html": "https://test"},
                    "profile_image": {"small": "https://test"}
                },
                "links": {
                    "html": "https://test",
                    "download_location": "https://test"
                }
            }
        ]
    }
    mock_unsplash_service.return_value = mock_instance
    
    response = client.get("/images/search?query=test")
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify formatted structure
    result = data["results"][0]
    assert "id" in result
    assert "description" in result
    assert "urls" in result
    assert "user" in result
    assert "links" in result




