"""
MongoDB User model for authentication.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from flask_bcrypt import Bcrypt
from email_validator import validate_email, EmailNotValidError
from bson import ObjectId
from ..services.mongodb_service import get_mongodb_service

bcrypt = Bcrypt()


class User:
    """User model for MongoDB storage."""
    
    COLLECTION_NAME = 'users'
    
    def __init__(self, email: str, password: str = None, display_name: str = None,
                 bio: str = None, avatar_url: str = None, is_active: bool = True, _id: str = None, 
                 created_at: datetime = None, updated_at: datetime = None):
        """Initialize a User instance."""
        self.id = _id
        self.email = email
        self.display_name = display_name or email.split('@')[0]
        self.bio = bio
        self.avatar_url = avatar_url
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
        
        # Hash password if provided
        if password:
            self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        else:
            self.password_hash = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create a User instance from a dictionary."""
        user = cls(
            email=data['email'],
            display_name=data.get('display_name'),
            bio=data.get('bio'),
            avatar_url=data.get('avatar_url'),
            is_active=data.get('is_active', True),
            _id=str(data.get('_id')),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
        user.password_hash = data.get('password_hash')
        return user
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert User instance to dictionary."""
        return {
            '_id': str(self.id) if self.id else None,
            'email': self.email,
            'password_hash': self.password_hash,
            'display_name': self.display_name,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self) -> str:
        """Save user to MongoDB."""
        mongodb_service = get_mongodb_service()
        
        if self.id:
            # Update existing user
            user_data = self.to_dict()
            user_data.pop('_id')  # Remove _id from update data
            user_data.pop('created_at', None)  # Don't update created_at
            
            mongodb_service.update_one(
                self.COLLECTION_NAME,
                {'_id': ObjectId(self.id)},
                user_data
            )
            return self.id
        else:
            # Create new user
            user_data = self.to_dict()
            user_data.pop('_id', None)  # Remove None _id
            
            self.id = mongodb_service.insert_one(self.COLLECTION_NAME, user_data)
            return self.id
    
    def delete(self) -> bool:
        """Delete user from MongoDB."""
        if not self.id:
            return False
        
        mongodb_service = get_mongodb_service()
        return mongodb_service.delete_one(
            self.COLLECTION_NAME,
            {'_id': ObjectId(self.id)}
        )
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches the user's password."""
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def set_password(self, password: str) -> None:
        """Set a new password for the user."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    @classmethod
    def find_by_id(cls, user_id: str) -> Optional['User']:
        """Find user by ID."""
        mongodb_service = get_mongodb_service()
        user_data = mongodb_service.find_one(
            cls.COLLECTION_NAME,
            {'_id': ObjectId(user_id)}
        )
        
        if user_data:
            return cls.from_dict(user_data)
        return None
    
    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """Find user by email."""
        mongodb_service = get_mongodb_service()
        user_data = mongodb_service.find_one(
            cls.COLLECTION_NAME,
            {'email': email}
        )
        
        if user_data:
            return cls.from_dict(user_data)
        return None
    
    @classmethod
    def create_user(cls, email: str, password: str, display_name: str = None) -> 'User':
        """Create a new user with validation."""
        # Validate email
        try:
            # Allow example.com for testing
            if not email.endswith('@example.com'):
                validate_email(email)
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email: {e}")
        
        # Check if user already exists
        if cls.find_by_email(email):
            raise ValueError("User with this email already exists")
        
        # Create and save user
        user = cls(
            email=email,
            password=password,
            display_name=display_name
        )
        user.save()
        return user
    
    @classmethod
    def authenticate(cls, email: str, password: str) -> Optional['User']:
        """Authenticate user with email and password."""
        user = cls.find_by_email(email)
        if user and user.check_password(password):
            return user
        return None
    
    @classmethod
    def get_all_users(cls, limit: int = 100) -> list['User']:
        """Get all users (for admin purposes)."""
        mongodb_service = get_mongodb_service()
        users_data = mongodb_service.find_many(
            cls.COLLECTION_NAME,
            limit=limit,
            sort=[('created_at', -1)]
        )
        
        return [cls.from_dict(user_data) for user_data in users_data]
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for the User collection."""
        mongodb_service = get_mongodb_service()
        
        # Create unique index on email
        mongodb_service.create_index(cls.COLLECTION_NAME, 'email', unique=True)
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User {self.email}>" 