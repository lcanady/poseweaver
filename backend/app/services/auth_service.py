"""
Authentication service for JWT token management.
"""
from datetime import timedelta
from typing import Dict, Optional, Any
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token,
    decode_token,
    get_jwt_identity,
    verify_jwt_in_request
)
from app.models.user_mongo import User


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        user = User.find_by_email(email)
        if user and user.is_active and user.check_password(password):
            return user
        return None
    
    @staticmethod
    def generate_tokens(user: User) -> Dict[str, str]:
        """Generate access and refresh tokens for user.
        
        Args:
            user: User instance
            
        Returns:
            Dictionary containing access_token and refresh_token
        """
        # Use user ID as the subject
        identity = str(user.id)
        
        # Generate tokens
        access_token = create_access_token(
            identity=identity,
            expires_delta=timedelta(hours=12)
        )
        refresh_token = create_refresh_token(
            identity=identity,
            expires_delta=timedelta(days=30)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token if successful, None otherwise
        """
        try:
            # Decode the refresh token
            decoded_token = decode_token(refresh_token)
            identity = decoded_token['sub']
            
            # Verify user still exists and is active
            user = User.find_by_id(identity)
            if not user or not user.is_active:
                return None
            
            # Generate new access token
            new_access_token = create_access_token(
                identity=identity,
                expires_delta=timedelta(hours=12)
            )
            
            return new_access_token
            
        except Exception:
            return None
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """Get current authenticated user from JWT token.
        
        Returns:
            User instance if authenticated, None otherwise
        """
        try:
            from flask import current_app
            
            # Verify JWT token in request
            verify_jwt_in_request()
            identity = get_jwt_identity()
            
            current_app.logger.debug(f"JWT identity: {identity}")
            
            if not identity:
                current_app.logger.warning("No identity found in JWT token")
                return None
                
            # Find user by ID
            user = User.find_by_id(identity)
            
            if not user:
                current_app.logger.warning(f"User with ID {identity} not found")
                return None
                
            if not user.is_active:
                current_app.logger.warning(f"User with ID {identity} is not active")
                return None
                
            return user
            
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error in get_current_user: {str(e)}")
            return None
    
    @staticmethod
    def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            decoded_token = decode_token(token)
            return decoded_token
        except Exception:
            return None
    
    @staticmethod
    def register_user(email: str, password: str, 
                      display_name: str) -> User:
        """Register a new user.
        
        Args:
            email: User's email address
            password: Plain text password
            display_name: User's display name
            
        Returns:
            Created user instance
            
        Raises:
            ValueError: If registration fails
        """
        # Validate input
        if not email or not email.strip():
            raise ValueError("Email is required")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        if not display_name or not display_name.strip():
            raise ValueError("Display name is required")
        
        # Create user
        try:
            user = User.create_user(
                email=email.strip(),
                password=password,
                display_name=display_name.strip()
            )
            return user
        except ValueError as e:
            # Re-raise user creation errors
            raise e
        except Exception as e:
            raise ValueError(f"Registration failed: {str(e)}")
    
    @staticmethod
    def update_profile(user: User, display_name: Optional[str] = None, 
                      email: Optional[str] = None, bio: Optional[str] = None,
                      avatar_url: Optional[str] = None) -> Optional[User]:
        """Update user profile information.
        
        Args:
            user: User instance to update
            display_name: New display name (optional)
            email: New email address (optional)
            bio: New bio text (optional)
            avatar_url: New avatar URL (optional)
            
        Returns:
            Updated user instance if successful, None otherwise
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate and update display name
            if display_name is not None:
                display_name = display_name.strip()
                if not display_name:
                    raise ValueError("Display name cannot be empty")
                user.display_name = display_name
            
            # Validate and update email
            if email is not None:
                email = email.strip().lower()
                if not email:
                    raise ValueError("Email cannot be empty")
                
                # Check if email is already taken by another user
                existing_user = User.find_by_email(email)
                if existing_user and existing_user.id != user.id:
                    raise ValueError("Email is already taken")
                
                user.email = email
            
            # Update bio (can be empty)
            if bio is not None:
                user.bio = bio.strip() if bio else None
            
            # Update avatar URL (can be empty)
            if avatar_url is not None:
                user.avatar_url = avatar_url.strip() if avatar_url else None
            
            # Save changes
            user.save()
            return user
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise ValueError(f"Profile update failed: {str(e)}")
    
    @staticmethod
    def authenticate_or_create_google_user(email: str, display_name: str, 
                                         avatar_url: Optional[str] = None,
                                         google_id: Optional[str] = None) -> Optional[User]:
        """Authenticate or create user with Google OAuth.
        
        Args:
            email: User's email address from Google
            display_name: User's display name from Google
            avatar_url: User's avatar URL from Google (optional)
            google_id: Google user ID (optional)
            
        Returns:
            User instance if successful, None otherwise
            
        Raises:
            ValueError: If user creation/update fails
        """
        try:
            # Try to find existing user by email
            user = User.find_by_email(email)
            
            if user:
                # Update existing user with Google info if needed
                updated = False
                
                # Update avatar if provided and user doesn't have one
                if avatar_url and not user.avatar_url:
                    user.avatar_url = avatar_url
                    updated = True
                
                # Update display name if user's current name is just email prefix
                if user.display_name == email.split('@')[0] and display_name != email.split('@')[0]:
                    user.display_name = display_name
                    updated = True
                
                # Save updates if any
                if updated:
                    user.save()
                
                # Ensure user is active
                if not user.is_active:
                    return None
                    
                return user
            else:
                # Create new user for Google OAuth
                # Check if this is the FIRST user in the system
                from app.extensions import get_db
                db = get_db()
                try:
                    user_count = db.count_documents('users', {})
                    is_admin = (user_count == 0)
                except Exception:
                    # Fallback if count fails (e.g. some DB error), default to False
                    is_admin = False

                # Generate a random password since Google users don't need it
                import secrets
                import string
                random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
                
                user = User.create_user(
                    email=email,
                    password=random_password,  # Random password, won't be used
                    display_name=display_name,
                    avatar_url=avatar_url
                )

                if is_admin:
                    user.is_admin = True
                    user.save()
                    from flask import current_app
                    current_app.logger.info(f"First user {email} (Google) created as ADMIN")
                
                return user
                
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Google OAuth user creation/authentication failed: {str(e)}")
            return None

    @staticmethod
    def handle_firebase_login(decoded_token: Dict[str, Any]) -> Optional[User]:
        """Handle login with verified Firebase token.
        
        Args:
            decoded_token: Decoded Firebase token claims
            
        Returns:
            User instance if successful, None otherwise
        """
        try:
            uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            name = decoded_token.get('name', email.split('@')[0] if email else 'User')
            picture = decoded_token.get('picture')
            
            if not email:
                # Fallback if email not in token (e.g. anonymous auth upgraded?)
                # ideally we require email
                return None
                
            # Check if user exists
            user = User.find_by_email(email)
            
            if user:
                # Update existing user
                updated = False
                if picture and not user.avatar_url:
                    user.avatar_url = picture
                    updated = True
                
                # Update firebase uid mapping if needed (could store in extra field)
                
                if updated:
                    user.save()
                    
                return user
            else:
                # Create new user
                # Check if this is the FIRST user in the system
                from app.extensions import get_db
                db = get_db()
                try:
                    user_count = db.count_documents('users', {})
                    is_admin = (user_count == 0)
                except Exception:
                    is_admin = False
                
                # Generate random password
                import secrets
                import string
                random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
                
                user = User.create_user(
                    email=email,
                    password=random_password,
                    display_name=name,
                    avatar_url=picture
                )
                
                if is_admin:
                    user.is_admin = True
                    user.save()
                    from flask import current_app
                    current_app.logger.info(f"First user {email} created as ADMIN")
                
                return user
                
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Firebase login handler error: {str(e)}")
            return None
    
    @staticmethod
    def change_password(user: User, current_password: str, 
                       new_password: str) -> bool:
        """Change user's password.
        
        Args:
            user: User instance
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if password changed successfully, False otherwise
        """
        # Verify current password
        if not user.check_password(current_password):
            return False
        
        # Validate new password
        if len(new_password) < 6:
            return False
        
        # Update password
        user.set_password(new_password)
        user.save()
        return True

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID (for WebSocket authentication).
        
        Args:
            user_id: ID of the user to find
            
        Returns:
            User dictionary if found, None otherwise
        """
        user = User.find_by_id(user_id)
        if user:
            return user.to_dict()
        return None
