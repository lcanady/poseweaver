"""
Authentication API endpoints for user management.
"""
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt
from app.services.auth_service import AuthService
from app.extensions import jwt

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Token blacklist (in production, use Redis or database)
blacklisted_tokens = set()


# JWT token blacklist checker
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """Check if JWT token is blacklisted."""
    jti = jwt_payload['jti']
    return jti in blacklisted_tokens


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """User registration endpoint.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123",
        "display_name": "User Name"
    }
    
    Returns:
        JSON response with user data and tokens
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        email = data.get('email')
        password = data.get('password')
        display_name = data.get('display_name')
        
        if not email or not password or not display_name:
            return jsonify({
                'error': 'Email, password, and display_name are required'
            }), 400
        
        # Register user
        user = AuthService.register_user(email, password, display_name)
        
        # Generate tokens
        tokens = AuthService.generate_tokens(user)
        
        # Store user info and tokens in session
        session['user_id'] = user.id
        session['access_token'] = tokens['access_token']
        session['refresh_token'] = tokens['refresh_token']
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Returns:
        JSON response with user data and tokens
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'error': 'Email and password are required'
            }), 400
        
        # Authenticate user
        user = AuthService.authenticate_user(email, password)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate tokens
        tokens = AuthService.generate_tokens(user)
        
        # Store user info and tokens in session
        session['user_id'] = user.id
        session['access_token'] = tokens['access_token']
        session['refresh_token'] = tokens['refresh_token']
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        }), 200
        
    except Exception:
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token endpoint.
    
    Requires valid refresh token in Authorization header.
    
    Returns:
        JSON response with new access token
    """
    try:
        # Get current user from refresh token
        current_user = AuthService.get_current_user()
        if not current_user:
            return jsonify({'error': 'Invalid refresh token'}), 401
        
        # Generate new tokens
        tokens = AuthService.generate_tokens(current_user)
        
        return jsonify({
            'success': True,
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        }), 200
        
    except Exception:
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint.
    
    Blacklists the current access token.
    
    Returns:
        JSON response confirming logout
    """
    try:
        # Get current token
        token = get_jwt()
        jti = token['jti']  # JWT ID
        
        # Add token to blacklist
        blacklisted_tokens.add(jti)
        
        # Clear session data
        session.pop('user_id', None)
        session.pop('access_token', None)
        session.pop('refresh_token', None)
        
        return jsonify({
            'success': True,
            'message': 'Successfully logged out'
        }), 200
        
    except Exception:
        return jsonify({'error': 'Logout failed'}), 500


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user information.
    
    Uses session data to retrieve the current user.
    Falls back to JWT token if session data is not available.
    
    Returns:
        JSON response with current user data
    """
    try:
        from flask import current_app
        current_app.logger.info('Attempting to get current user from session')
        
        # Try to get user from session first
        user_id = session.get('user_id')
        
        if user_id:
            from app.models.user_mongo import User
            current_user = User.find_by_id(user_id)
            
            if current_user and current_user.is_active:
                current_app.logger.info(f'Successfully retrieved user from session: {current_user.id}')
                return jsonify({
                    'success': True,
                    'user': current_user.to_dict()
                }), 200
            else:
                current_app.logger.warning(f'User from session not found or inactive: {user_id}')
        
        # Fall back to JWT token if session doesn't have user_id
        current_app.logger.info('Falling back to JWT token authentication')
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            current_user = AuthService.get_current_user()
            
            if not current_user:
                current_app.logger.error('User not found or inactive in database')
                return jsonify({'error': 'User not found or inactive'}), 404
            
            # Update session with user info
            session['user_id'] = current_user.id
            
            current_app.logger.info(f'Successfully retrieved user from JWT: {current_user.id}')
            return jsonify({
                'success': True,
                'user': current_user.to_dict()
            }), 200
        except Exception as e:
            current_app.logger.error(f'JWT authentication failed: {str(e)}')
            return jsonify({'error': 'Authentication required'}), 401
        
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f'Error getting user info: {str(e)}')
        return jsonify({'error': f'Failed to get user info: {str(e)}'}), 500


@auth_bp.route('/update-profile', methods=['POST'])
@jwt_required()
def update_profile():
    """Update user profile endpoint.
    
    Request body:
    {
        "display_name": "New Display Name",
        "email": "new@example.com",
        "bio": "User bio text",
        "avatar_url": "https://example.com/avatar.jpg"
    }
    
    Returns:
        JSON response with updated user data
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        display_name = data.get('display_name')
        email = data.get('email')
        bio = data.get('bio')
        avatar_url = data.get('avatar_url')
        
        if not display_name and not email and bio is None and avatar_url is None:
            return jsonify({
                'error': 'At least one field (display_name, email, bio, or avatar_url) is required'
            }), 400
        
        # Get current user
        current_user = AuthService.get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update profile
        updated_user = AuthService.update_profile(current_user, display_name, email, bio, avatar_url)
        
        if not updated_user:
            return jsonify({
                'error': 'Profile update failed'
            }), 400
        
        return jsonify({
            'success': True,
            'user': updated_user.to_dict(),
            'message': 'Profile updated successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Profile update failed: {str(e)}'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password endpoint.
    
    Request body:
    {
        "current_password": "oldpassword",
        "new_password": "newpassword"
    }
    
    Returns:
        JSON response confirming password change
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                'error': 'Current password and new password are required'
            }), 400
        
        # Get current user
        current_user = AuthService.get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Change password
        success = AuthService.change_password(
            current_user, current_password, new_password
        )
        
        if not success:
            return jsonify({
                'error': 'Invalid current password or new password too short'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception:
        return jsonify({'error': 'Password change failed'}), 500 