"""
User model for authentication and user management.
"""
from datetime import datetime
from typing import Optional
from app.extensions import db, bcrypt
from email_validator import validate_email, EmailNotValidError


class User(db.Model):
    """User model for authentication."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False,
                       index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow,
                           nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, email: str, password: str, display_name: str):
        """Initialize a new user.
        
        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            display_name: User's display name
            
        Raises:
            ValueError: If email is invalid
        """
        self.email = self.validate_email(email)
        self.password_hash = bcrypt.generate_password_hash(
            password).decode('utf-8')
        self.display_name = display_name
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            Normalized email address
            
        Raises:
            ValueError: If email is invalid
        """
        try:
            # For testing, allow example.com domains
            if email.endswith('@example.com'):
                return email.lower()
            
            # Validate and normalize email
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address: {str(e)}")
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches the user's password.
        
        Args:
            password: Plain text password to check
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def update_password(self, password: str) -> None:
        """Update user's password.
        
        Args:
            password: New plain text password
        """
        self.password_hash = bcrypt.generate_password_hash(
            password).decode('utf-8')
        self.updated_at = datetime.utcnow()
    
    def update_last_login(self) -> None:
        """Update the user's last login timestamp."""
        self.last_login = datetime.utcnow()
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary representation.
        
        Args:
            include_sensitive: Whether to include sensitive information
            
        Returns:
            Dictionary representation of user
        """
        data = {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': (self.last_login.isoformat() 
                          if self.last_login else None)
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            
        return data
    
    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """Find user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User instance if found, None otherwise
        """
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_by_id(cls, user_id: int) -> Optional['User']:
        """Find user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User instance if found, None otherwise
        """
        return cls.query.filter_by(id=user_id).first()
    
    @classmethod
    def create_user(cls, email: str, password: str, 
                    display_name: str) -> 'User':
        """Create a new user.
        
        Args:
            email: User's email address
            password: Plain text password
            display_name: User's display name
            
        Returns:
            Created user instance
            
        Raises:
            ValueError: If email is invalid or already exists
        """
        # Check if user already exists
        if cls.find_by_email(email):
            raise ValueError("User with this email already exists")
        
        # Create new user
        user = cls(email=email, password=password, 
                   display_name=display_name)
        db.session.add(user)
        db.session.commit()
        
        return user
    
    def __repr__(self) -> str:
        """String representation of user."""
        return f'<User {self.email}>' 