from flask import Blueprint, request, Response, jsonify
import json
from services.image_service import UnsplashService

images_bp = Blueprint("images", __name__)

# GET: http://127.0.0.1:8080/images/search?query=nature&per_page=10&page=1
@images_bp.route("/images/search", methods=["GET"])
def search_images():
    """
    Search for images using Unsplash API
    """
    try:
        query = request.args.get("query")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        orientation = request.args.get("orientation")
        color = request.args.get("color")
        order_by = request.args.get("order_by", "relevant")
        
        # Validate required fields
        if not query:
            return Response(
                json.dumps({"error": "Missing query parameter"}, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )
        
        # Validate parameters
        if order_by not in ["relevant", "latest"]:
            return Response(
                json.dumps({"error": "order_by must be 'relevant' or 'latest'"}, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )
        
        if orientation and orientation not in ["landscape", "portrait", "squarish"]:
            return Response(
                json.dumps({"error": "orientation must be 'landscape', 'portrait', or 'squarish'"}, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )
        
        # Initialize Unsplash service
        try:
            unsplash = UnsplashService()
        except ValueError as e:
            return Response(
                json.dumps({"error": str(e)}, ensure_ascii=False),
                status=500,
                mimetype="application/json; charset=utf-8"
            )
        
        # Search for photos
        results = unsplash.search_photos(
            query=query,
            page=page,
            per_page=per_page,
            order_by=order_by,
            orientation=orientation,
            color=color
        )
        
        # Format response
        formatted_results = {
            "total": results.get("total", 0),
            "total_pages": results.get("total_pages", 0),
            "results": [
                UnsplashService.format_photo_response(photo) 
                for photo in results.get("results", [])
            ]
        }
        
        return Response(
            json.dumps(formatted_results, ensure_ascii=False),
            status=200,
            mimetype="application/json; charset=utf-8"
        )
        
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            status=500,
            mimetype="application/json; charset=utf-8"
        )


# POST: curl -X POST http://127.0.0.1:8080/images/download -H "Content-Type: application/json" -d '{"photo_id":"abc123"}'
@images_bp.route("/images/download", methods=["POST"])
def track_download():
    """
    Track a photo download (required by Unsplash API guidelines)
    This endpoint should be called when a user downloads/uses an image
    Doesn't actually download the image
    """
    try:
        data = request.get_json(silent=True)
        if data is None:
            return Response(
                json.dumps({"error": "Missing JSON body"}, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )
        photo_id = data.get("photo_id")
        
        # Validate required fields
        if not photo_id:
            return Response(
                json.dumps({"error": "Missing photo_id parameter"}, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )
        
        # Initialize Unsplash service
        try:
            unsplash = UnsplashService()
        except ValueError as e:
            return Response(
                json.dumps({"error": str(e)}, ensure_ascii=False),
                status=500,
                mimetype="application/json; charset=utf-8"
            )
        
        # Track download
        result = unsplash.track_download(photo_id)
        
        return Response(
            json.dumps(result, ensure_ascii=False),
            status=200,
            mimetype="application/json; charset=utf-8"
        )
        
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            status=500,
            mimetype="application/json; charset=utf-8"
        )
