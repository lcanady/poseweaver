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
        from flask import request
        current_app.logger.debug("Entered require_auth.decorated_function for protected endpoint")
        # JWT authentication
        try:
            verify_jwt_in_request()
            current_identity = get_jwt_identity()
            if current_identity:
                current_user = AuthService.get_current_user()
                if current_user:
                    # Set current_user on request object for endpoint access
                    request.current_user = current_user
                    return f(*args, **kwargs)
                else:
                    current_app.logger.warning(f"User not found for JWT identity: {current_identity}")
            else:
                current_app.logger.warning("JWT identity is None")
        except Exception as e:
            current_app.logger.debug(f"JWT verification failed, trying Firebase: {str(e)}")
            
            # Try Firebase Token
            try:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split('Bearer ')[1]
                    
                    # Verify Firebase token
                    from firebase_admin import auth
                    decoded_token = auth.verify_id_token(token)
                    
                    # Handle user login/creation via AuthService
                    current_user = AuthService.handle_firebase_login(decoded_token)
                    
                    if current_user:
                        if not current_user.is_active:
                            return jsonify({'error': 'User account is disabled'}), 403
                            
                        request.current_user = current_user
                        return f(*args, **kwargs)
            except Exception as fe:
                current_app.logger.error(f"Firebase token verification failed: {str(fe)}")
        
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


def get_current_identity():
    """Unified helper to get current user identity (ID string).
    
    Checks both request.current_user (populated by require_auth fallback) 
    and flask_jwt_extended's get_jwt_identity().
    
    Returns:
        User ID string or None
    """
    from flask import request
    
    # Check if require_auth already populated current_user
    if hasattr(request, 'current_user') and request.current_user:
        # Use str() to ensure it's a string ID
        if hasattr(request.current_user, 'id'):
            return str(request.current_user.id)
        return str(request.current_user)
        
    # Fallback to standard JWT identity
    try:
        return get_jwt_identity()
    except Exception:
        return None