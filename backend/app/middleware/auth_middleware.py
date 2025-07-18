"""
Authentication middleware for protecting API routes.
"""
from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.services.auth_service import AuthService


def require_auth(f):
    """Decorator to require authentication for API endpoints.
    
    Args:
        f: Function to wrap
        
    Returns:
        Wrapped function that requires authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_app.logger.debug("Entered require_auth.decorated_function for protected endpoint")
        # JWT authentication
        try:
            verify_jwt_in_request()
            current_identity = get_jwt_identity()
            if current_identity:
                current_user = AuthService.get_current_user()
                if current_user:
                    return f(*args, **kwargs)
                else:
                    current_app.logger.warning(f"User not found for JWT identity: {current_identity}")
            else:
                current_app.logger.warning("JWT identity is None")
        except Exception as e:
            current_app.logger.error(f"JWT verification error: {str(e)}")
        
        # Authentication failed
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated_function


def optional_auth(f):
    """Decorator for optional authentication.
    
    Args:
        f: Function to wrap
        
    Returns:
        Wrapped function that works with or without authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            return f(*args, **kwargs)
        except Exception:
            return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges.
    
    Args:
        f: Function to wrap
        
    Returns:
        Wrapped function that requires admin authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = AuthService.get_current_user()
            if not current_user:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user is admin (you can add admin field to User model)
            # For now, we'll just check if user exists and is active
            if not current_user.is_active:
                return jsonify({'error': 'Admin privileges required'}), 403
                
            return f(*args, **kwargs)
        except Exception:
            return jsonify({'error': 'Invalid or expired token'}), 401
    
    return decorated_function 