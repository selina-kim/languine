from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token

# ===== TO BE IMPLEMENTED ONCE DATABASE IS READY =====
# Import User model: from src.models import User
# Import db: from src import db
# ===== END PLACEHOLDER =====

class AuthService:
    @staticmethod
    def get_or_create_oauth_user(google_id: str, email: str, display_name: str, timezone: str = 'UTC', **user_info):
        """
        Get existing OAuth user or create new one.
        
        ===== TO BE IMPLEMENTED ONCE DATABASE IS READY =====
        Replace this entire method with actual database logic:
        
        user = User.query.filter_by(google_id=google_id).first()
        
        if user:
            user.last_login = datetime.utcnow()
            db.session.commit()
            return user
        
        user = User(
            google_id=google_id,
            email=email,
            display_name=display_name,
            timezone=timezone
        )
        db.session.add(user)
        db.session.commit()
        return user
        ===== END PLACEHOLDER =====
        """
        # Placeholder - will be replaced with DB logic
        return {
            'u_id': 'temp-uid',
            'email': email,
            'display_name': display_name,
            'timezone': timezone,
            'google_id': google_id
        }
    
    @staticmethod
    def generate_tokens(user_uid: str) -> dict:
        """Generate access and refresh tokens."""
        access_token = create_access_token(
            identity=user_uid,
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=user_uid,
            expires_delta=timedelta(days=30)
        )
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }