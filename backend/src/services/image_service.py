import os
import requests
from typing import Optional, Dict, Any, List


class UnsplashService:
    """Service for interacting with Unsplash API"""
    
    BASE_URL = "https://api.unsplash.com"
    DEFAULT_TIMEOUT_SECONDS = 10.0
    
    def __init__(self, access_key: Optional[str] = None):
        self.access_key = access_key or os.getenv("UNSPLASH_ACCESS_KEY")
        if not self.access_key:
            raise ValueError("UNSPLASH_ACCESS_KEY not set in environment")

        timeout_value = os.getenv("UNSPLASH_TIMEOUT_SECONDS", str(self.DEFAULT_TIMEOUT_SECONDS))
        try:
            self.timeout_seconds = float(timeout_value)
        except (TypeError, ValueError):
            self.timeout_seconds = self.DEFAULT_TIMEOUT_SECONDS
        
        self.headers = {
            "Authorization": f"Client-ID {self.access_key}",
            "Accept-Version": "v1"
        }
    
    def search_photos(
        self,
        query: str,
        page: int = 1,
        per_page: int = 5,
        order_by: str = "relevant",
        orientation: Optional[str] = None,
        colour: Optional[str] = None,
        content_filter: str = "high"
    ) -> Dict[str, Any]:
        """
        Search for photos on Unsplash
        
        Args:
            query: Search terms
            page: Page number (default: 1)
            per_page: Number of items per page (default: 5, max: 30)
            order_by: How to sort photos (relevant or latest)
            orientation: Filter by orientation (landscape, portrait, squarish)
            colour: Filter by colour (e.g., black_and_white, black, white, yellow, etc.)
            content_filter: Content safety filter (low or high)
        
        Returns:
            Dictionary containing search results with total count and photo list
        """
        endpoint = f"{self.BASE_URL}/search/photos"
        
        params = {
            "query": query,
            "page": page,
            "per_page": min(per_page, 30),  # Unsplash max is 30
            "order_by": order_by,
            "content_filter": content_filter
        }
        
        if orientation:
            params["orientation"] = orientation
        if colour:
            params["colour"] = colour
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to search Unsplash photos: {str(e)}")
    
    def track_download(self, photo_id: str) -> Dict[str, Any]:
        """
        Track a photo download (required by Unsplash API guidelines)
        
        Args:
            photo_id: The photo's ID
        
        Returns:
            Dictionary with download URL
        """
        endpoint = f"{self.BASE_URL}/photos/{photo_id}/download"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to track download: {str(e)}")
    
    @staticmethod
    def format_photo_response(photo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format photo data for frontend consumption
        
        Args:
            photo: Raw photo object from Unsplash API
        
        Returns:
            Formatted photo dictionary with essential fields
        """
        return {
            "id": photo.get("id"),
            "description": photo.get("description") or photo.get("alt_description"),
            "urls": {
                "raw": photo.get("urls", {}).get("raw"),
                "full": photo.get("urls", {}).get("full"),
                "regular": photo.get("urls", {}).get("regular"),
                "small": photo.get("urls", {}).get("small"),
                "thumb": photo.get("urls", {}).get("thumb")
            },
            "width": photo.get("width"),
            "height": photo.get("height"),
            "colour": photo.get("colour"),
            "blur_hash": photo.get("blur_hash"),
            "user": {
                "name": photo.get("user", {}).get("name"),
                "username": photo.get("user", {}).get("username"),
                "profile_url": photo.get("user", {}).get("links", {}).get("html"),
                "profile_image": photo.get("user", {}).get("profile_image", {}).get("small")
            },
            "links": {
                "html": photo.get("links", {}).get("html")
            }
        }
