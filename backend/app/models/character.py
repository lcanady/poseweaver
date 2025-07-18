"""
Character model for roleplay characters.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId
from .base_model import BaseModel
from ..services.mongodb_service import get_mongodb_service

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
        self.user_id = user_id
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
        if 'user_id' in data and data['user_id'] and isinstance(data['user_id'], ObjectId):
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
        # Since MongoDB could have stored user_id as either string or ObjectId,
        # we need to check both possibilities
        try:
            user_id_obj = ObjectId(user_id)
            # Create a query that matches either the string or ObjectId version
            query = {'$or': [
                {'user_id': user_id_obj},  # Match ObjectId version
                {'user_id': str(user_id)}  # Match string version
            ]}
        except:
            # If conversion fails, just use the string version
            query = {'user_id': user_id}
            
        if not include_inactive:
            query['is_active'] = True
            
        # Debug log the query to help diagnose issues
        from flask import current_app
        current_app.logger.debug(f"Character.find_by_user query: {query}")
        
        # Get results
        result = cls.find_all(query=query, sort=[('name', 1)])
        
        # Debug log the result count
        current_app.logger.debug(f"Character.find_by_user found {len(result)} characters")
        
        return result
        
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
            # Escape special regex characters in name
            import re
            escaped_name = re.escape(name)
            query['name'] = {'$regex': f'^{escaped_name}$', '$options': 'i'}  # Case-insensitive exact match
            
        if user_id:
            # Convert user_id to ObjectId for query if it's a valid ObjectId
            try:
                user_id_obj = ObjectId(user_id)
            except:
                user_id_obj = user_id
            query['user_id'] = user_id_obj
            
        return cls.find_all(query=query)
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for characters."""
        mongodb = get_mongodb_service()
        
        # Create indexes
        mongodb.create_index(cls.COLLECTION_NAME, 'user_id')
        mongodb.create_index(
            cls.COLLECTION_NAME, 
            [('user_id', 1), ('name', 1)], 
            unique=True
        )
        mongodb.create_index(
            cls.COLLECTION_NAME,
            'name',
            unique=False
        )
        mongodb.create_index(
            cls.COLLECTION_NAME,
            'tags',
            unique=False
        )
