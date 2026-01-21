"""
Character model for roleplay characters.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId
from .base_model import BaseModel
from ..extensions import get_db

class Character(BaseModel):
    """Character model for roleplay characters."""
    
    COLLECTION_NAME = 'characters'
    
    def __init__(
        self,
        name: str,
        user_id: str,  # ID of the user who owns this character
        description: str = "",
        profile_image: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_active: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.name = name
        self.user_id = str(user_id) if user_id else None
        self.description = description
        self.profile_image = profile_image
        self.tags = tags or []
        self.is_active = is_active
        self.last_played = kwargs.get('last_played')
        self.play_count = kwargs.get('play_count', 0)
        self.metadata = kwargs.get('metadata', {})  # For any additional data
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
    
    def save(self) -> str:
        """Save the character to the database.
        
        Returns:
            The ID of the saved character
            
        Raises:
            ValueError: If a character with the same name already exists for this user
        """
        # Check for duplicate names for this user
        if self.name and self.user_id:
            existing = self.find_by_name(self.name, str(self.user_id))
            # If this is an update, exclude the current character from the check
            if self.id:
                existing = [c for c in existing if c.id != self.id]
            if existing:
                raise ValueError(f"A character named '{self.name}' already exists for this user")
        
        return super().save()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary for JSON serialization."""
        data = super().to_dict()
        
        # Convert ObjectId fields to strings for JSON serialization
        if '_id' in data and isinstance(data['_id'], ObjectId):
            data['_id'] = str(data['_id'])
            
        # Convert user_id to string for JSON if it's an ObjectId
        if 'user_id' in data and isinstance(data['user_id'], ObjectId):
            data['user_id'] = str(data['user_id'])
        
        # Handle any nested ObjectIds in metadata
        if 'metadata' in data and isinstance(data['metadata'], dict):
            self._convert_objectids_in_dict(data['metadata'])
            
        return data
        
    def _convert_objectids_in_dict(self, d):
        """Recursively convert any ObjectId values to strings in a dictionary."""
        if not isinstance(d, dict):
            return
            
        for k, v in d.items():
            if isinstance(v, ObjectId):
                d[k] = str(v)
            elif isinstance(v, dict):
                self._convert_objectids_in_dict(v)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, ObjectId):
                        v[i] = str(item)
                    elif isinstance(item, dict):
                        self._convert_objectids_in_dict(item)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Create character from dictionary."""
        if not data:
            return None
            
        # Convert ObjectId to string for user_id
        if 'user_id' in data and data['user_id']:
             if isinstance(data['user_id'], ObjectId):
                 data['user_id'] = str(data['user_id'])
            
        return cls(**data)
    
    @classmethod
    def find_by_user(cls, user_id: str, include_inactive: bool = False) -> List['Character']:
        """Find all characters for a specific user.
        
        Args:
            user_id: ID of the user whose characters to find
            include_inactive: Whether to include inactive characters
            
        Returns:
            List of Character instances belonging to the user
        """
        # Simplified query assuming user_id normalization
        query = {'user_id': str(user_id)}
            
        if not include_inactive:
            query['is_active'] = True
            
        return cls.find_all(query=query, sort=[('name', 1)])
        
    @classmethod
    def find_by_name(cls, name: str, user_id: Optional[str] = None) -> List['Character']:
        """Find characters by name (case-insensitive).
        
        Args:
            name: Name to search for (case-insensitive exact match)
            user_id: Optional user ID to filter by
            
        Returns:
            List of matching Character instances
        """
        query = {}
        if name:
             # Basic exact match for cross-db compatibility first
             # Regex is Mongo specific. Firestore requires specific index or client side filtering often
             # or 'where name == value'. For case insensitive, best to store normalized name.
             # For now, we will assume exact match or let the generic repository handle it.
             # If using our MongoService, it supports regex. FirebaseService... not so much yet.
             # We will pass the regex if it's Mongo, but ideally we abstract this.
             # For migration safety, let's just pass exact name for now or handle locally?
             # Existing logic uses regex:
             # import re
             # escaped_name = re.escape(name)
             # query['name'] = {'$regex': f'^{escaped_name}$', '$options': 'i'}
             # This will crash FirebaseService potentially or be ignored.
             
             # Attempt to use 'name' eq 'name' for simplicity in transition
             # or keep regex but aware it won't work in Firebase without full text search engine (Algolia etc)
             query['name'] = name 
            
        if user_id:
            query['user_id'] = str(user_id)
            
        return cls.find_all(query=query)
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for characters."""
        db = get_db()
        
        # Create indexes
        db.create_index(cls.COLLECTION_NAME, 'user_id')
        db.create_index(
            cls.COLLECTION_NAME, 
            [('user_id', 1), ('name', 1)], 
            unique=True
        )
        db.create_index(
            cls.COLLECTION_NAME,
            'name',
            unique=False
        )
        db.create_index(
            cls.COLLECTION_NAME,
            'tags',
            unique=False
        )
