"""
Base model class for Database models.
"""
from typing import Dict, Any, Optional, TypeVar, Generic, Type
from bson import ObjectId
from datetime import datetime, UTC
from ..extensions import get_db

T = TypeVar('T', bound='BaseModel')

class BaseModel:
    """Base model with common Database operations."""
    
    COLLECTION_NAME: str = ''  # Must be overridden by subclasses
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id')
        if not self.id:
            self.id = kwargs.get('id')
            
        self.created_at = kwargs.get('created_at', datetime.now(UTC))
        self.updated_at = kwargs.get('updated_at', datetime.now(UTC))
    
    def save(self) -> str:
        """Save the model to Database."""
        db = get_db()
        
        # Update timestamps
        now = datetime.now(UTC)
        if not self.id:
            self.created_at = now
        # Always update the updated_at timestamp on save
        self.updated_at = now
        
        # Convert to dict after updating timestamps
        data = self.to_dict()
        
        if self.id:
            # Update existing document
            data.pop('_id', None)  # Remove _id for update
            data.pop('id', None)   # Remove id for update
            data.pop('created_at', None)  # Don't update created_at
            
            # Ensure the updated_at field is explicitly included in the update
            data['updated_at'] = now.isoformat()
            
            # Use id for filter
            db.update_one(
                self.COLLECTION_NAME,
                {'id': self.id},
                data
            )
            return self.id
        else:
            # Insert new document
            self.id = db.insert_one(self.COLLECTION_NAME, data)
            return self.id
    
    def delete(self) -> bool:
        """Delete the model from Database."""
        if not self.id:
            return False
            
        db = get_db()
        # Try both _id and id for compatibility
        return db.delete_one(
            self.COLLECTION_NAME,
            {'id': self.id}
        )
    
    @classmethod
    def find_by_id(cls: Type[T], id: str) -> Optional[T]:
        """Find a model by ID."""
        if not id:
            return None
            
        db = get_db()
        data = db.find_one(
            cls.COLLECTION_NAME,
            {'id': id}
        )
        
        # Fallback for MongoDB ObjectId lookup if string lookup fails?
        # The service layer should handle this if possible or we assume id is string
        if not data and ObjectId.is_valid(id):
             data = db.find_one(
                cls.COLLECTION_NAME,
                {'_id': ObjectId(id)}
            )

        return cls.from_dict(data) if data else None
    
    @classmethod
    def find_all(cls: Type[T], query: Optional[Dict] = None, limit: int = 100, 
                skip: int = 0, sort: Optional[list] = None) -> list[T]:
        """Find all models matching the query."""
        db = get_db()
        results = db.find_many(
            cls.COLLECTION_NAME,
            filter_dict=query or {},
            limit=limit,
            skip=skip,
            sort=sort
        )
        return [cls.from_dict(data) for data in results if data]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        data = self.__dict__.copy()
        
        # Ensure id is included if present
        if self.id:
            data['id'] = str(self.id)
            # Legacy fields - DB implementations might stripe them if needed
            # For API responses, having id is good.
        
        # Convert datetime objects to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
                
        # Ensure all ObjectId instances are converted to strings for JSON serialization
        for key, value in list(data.items()):
            if isinstance(value, ObjectId):
                data[key] = str(value)
        
        return data
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create model from dictionary."""
        if not data:
            return None
            
        # Standardize id
        if '_id' in data:
            data['id'] = str(data['_id'])
            # We don't necessarily pop _id, just ensure id exists
            
        return cls(**data)
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for this model."""
        pass  # Should be overridden by subclasses
