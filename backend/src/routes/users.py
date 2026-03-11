"""
User API endpoints for profile and settings management.
"""

import json
from flask import Blueprint, request, Response
from services.user_service import (
    UserService,
    UserNotFoundError,
    DatabaseError
)
from services.fsrs_service import FsrsService
from flask_jwt_extended import jwt_required, get_jwt_identity

users_bp = Blueprint("users", __name__)
user_service = UserService()
fsrs_service = FsrsService()


def json_response(data, status=200, ensure_ascii=False):
    """Create a JSON response with proper encoding."""
    return Response(
        json.dumps(data, default=str, ensure_ascii=ensure_ascii),
        status=status,
        mimetype="application/json; charset=utf-8" if not ensure_ascii else "application/json"
    )


def error_response(message, status=500):
    """Create an error JSON response."""
    return json_response({"error": message}, status=status)


@users_bp.route("/users/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """
    Get current user's profile.
    
    GET /users/me
    
    Returns: User profile data
    """
    user_id = get_jwt_identity()
    
    try:
        user = user_service.get_user(user_id)
        
        if not user:
            return error_response("User not found", status=404)
        
        return json_response(user)
    
    except DatabaseError as e:
        return error_response(str(e) or "Database error", status=500)
    
    except Exception as e:
        return error_response(f"Failed to retrieve user: {str(e)}", status=500)


@users_bp.route("/users/me", methods=["PUT", "PATCH"])
@jwt_required()
def update_current_user():
    """
    Update current user's profile and settings.
    
    PUT/PATCH /users/me
    
    Body (all optional):
    - display_name: User's display name (max 30 chars)
    - timezone: User's timezone (e.g., 'America/Toronto')
    - new_cards_per_day: Number of new cards per day (integer)
    - desired_retention: Desired retention rate (0.0-1.0)
    - fsrs_parameters: Array of FSRS parameters (array of floats)
    - auto_optimize: Enable/disable auto-optimization (boolean)
    - num_reviews_per_optimize: Number of reviews before optimization (positive integer)
    - total_reviews: Total review count (non-negative integer)
    - reviews_since_last_optimize: Reviews since last optimization (non-negative integer)
    - reset_fsrs_params: resets the fsrs's optimization params to the default params
    
    Returns: Updated user profile
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    
    if not data:
        return error_response("No data provided", status=400)
    
    # Validate specific fields if present
    if 'display_name' in data:
        display_name = str(data['display_name']).strip()
        if not display_name:
            return error_response("display_name cannot be empty", status=400)
        if len(display_name) > 30:
            return error_response("display_name must be 30 characters or less", status=400)
        data['display_name'] = display_name
    
    if 'new_cards_per_day' in data:
        try:
            new_cards = int(data['new_cards_per_day'])
            if new_cards < 0:
                return error_response("new_cards_per_day must be non-negative", status=400)
            data['new_cards_per_day'] = new_cards
        except (ValueError, TypeError):
            return error_response("new_cards_per_day must be an integer", status=400)
    
    if 'desired_retention' in data:
        try:
            retention = float(data['desired_retention'])
            if not (0.0 <= retention <= 1.0):
                return error_response("desired_retention must be between 0.0 and 1.0", status=400)
            data['desired_retention'] = retention
        except (ValueError, TypeError):
            return error_response("desired_retention must be a number", status=400)
    
    if 'auto_optimize' in data:
        if not isinstance(data['auto_optimize'], bool):
            return error_response("auto_optimize must be a boolean", status=400)
    
    if 'num_reviews_per_optimize' in data:
        try:
            num = int(data['num_reviews_per_optimize'])
            if num <= 0:
                return error_response("num_reviews_per_optimize must be positive", status=400)
            data['num_reviews_per_optimize'] = num
        except (ValueError, TypeError):
            return error_response("num_reviews_per_optimize must be an integer", status=400)
    
    if 'total_reviews' in data:
        try:
            total = int(data['total_reviews'])
            if total < 0:
                return error_response("total_reviews must be non-negative", status=400)
            data['total_reviews'] = total
        except (ValueError, TypeError):
            return error_response("total_reviews must be an integer", status=400)
    
    if 'reviews_since_last_optimize' in data:
        try:
            reviews = int(data['reviews_since_last_optimize'])
            if reviews < 0:
                return error_response("reviews_since_last_optimize must be non-negative", status=400)
            data['reviews_since_last_optimize'] = reviews
        except (ValueError, TypeError):
            return error_response("reviews_since_last_optimize must be an integer", status=400)
    
    if 'fsrs_parameters' in data:
        if data['fsrs_parameters'] is not None:
            if not isinstance(data['fsrs_parameters'], list):
                return error_response("fsrs_parameters must be an array", status=400)
            try:
                # Validate all elements are numbers
                data['fsrs_parameters'] = [float(x) for x in data['fsrs_parameters']]
            except (ValueError, TypeError):
                return error_response("fsrs_parameters must contain only numbers", status=400)
    
    if 'reset_fsrs_params' in data:
        try:
            if not isinstance(data['reset_fsrs_params'], bool):
                return error_response("reset_fsrs_params must be a boolean", status=400)
            
            if data['reset_fsrs_params'] == True:
                fsrs_service.reset_optimization_params(user_id)
        except DatabaseError as e:
            return error_response(f"Database error: {str(e)}", status=500)
        
        # make sure to remove reset_fsrs_params from data before trying to pass it to the update_user func
        data.pop('reset_fsrs_params', None)
    
    try:
        updated_user = user_service.update_user(user_id, data)
        
        return json_response({
            "message": "User profile updated successfully",
            "user": updated_user
        })
    
    except UserNotFoundError as e:
        return error_response(str(e) or "User not found", status=404)
    
    except ValueError as e:
        return error_response(str(e), status=400)
    
    except DatabaseError as e:
        return error_response(str(e) or "Database error", status=500)
    
    except Exception as e:
        return error_response(f"Failed to update user: {str(e)}", status=500)


@users_bp.route("/users/me", methods=["DELETE"])
@jwt_required()
def delete_current_user():
    """
    Delete current user's account.
    
    DELETE /users/me
    
    WARNING: This will permanently delete the user and all associated data
    (decks, cards, review logs) due to CASCADE.
    
    Returns: Confirmation message with deletion statistics
    """
    user_id = get_jwt_identity()
    
    try:
        deletion_result = user_service.delete_user(user_id)
        
        return json_response({
            "message": "User account deleted successfully",
            "details": deletion_result
        })
    
    except UserNotFoundError as e:
        return error_response(str(e) or "User not found", status=404)
    
    except DatabaseError as e:
        return error_response(str(e) or "Database error", status=500)
    
    except Exception as e:
        return error_response(f"Failed to delete user: {str(e)}", status=500)
