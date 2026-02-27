from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.auth_service import AuthService
import google.auth.transport.requests
from google.oauth2 import id_token

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

class GoogleOAuthValidator:
    """Validate Google OAuth tokens."""
    @staticmethod
    def verify_google_token(token: str) -> dict:
        """Verify and decode Google OAuth token."""
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google.auth.transport.requests.Request(),
                current_app.config['GOOGLE_CLIENT_ID']
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return idinfo
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")

@auth_bp.route('/google', methods=['POST'])
def google_oauth():
    """Handle Google OAuth login/signup."""
    try:
        data = request.get_json()
        token = data.get('id_token')
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        # Verify Google token
        idinfo = GoogleOAuthValidator.verify_google_token(token)
        
        # Get or create user
        user = AuthService.get_or_create_oauth_user(
            google_id=idinfo['sub'],
            email=idinfo['email'],
            display_name=idinfo.get('email').split('@')[0],
            timezone='UTC'
        )
        
        # Extract u_id from user object: user_uid = user.u_id
        # For now, extracting from dict:
        user_uid = user.get('u_id') if isinstance(user, dict) else user.u_id
        
        tokens = AuthService.generate_tokens(user_uid)
        
        return jsonify({
            'message': 'Google authentication successful',
            'user': user,
            'tokens': tokens
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': 'Authentication failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token."""
    user_uid = get_jwt_identity()
    tokens = AuthService.generate_tokens(user_uid)
    
    return jsonify({
        'message': 'Token refreshed',
        'tokens': tokens
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current logged-in user."""
    user_uid = get_jwt_identity()
    
    return jsonify({
        'user': {'u_id': user_uid, 'message': 'Database not yet implemented'}
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client-side token invalidation)."""
    return jsonify({'message': 'Logged out successfully'}), 200