"""
Base model class for MongoDB models.
"""
from typing import Dict, Any, Optional, TypeVar, Generic, Type
from bson import ObjectId
from datetime import datetime
from ..services.mongodb_service import get_mongodb_service

T = TypeVar('T', bound='BaseModel')

class BaseModel:
    """Base model with common MongoDB operations."""
    
    COLLECTION_NAME: str = ''  # Must be overridden by subclasses
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
    
    def save(self) -> str:
        """Save the model to MongoDB."""
        mongodb = get_mongodb_service()
        
        # Update timestamps
        now = datetime.utcnow()
        if not self.id:
            self.created_at = now
        # Always update the updated_at timestamp on save
        self.updated_at = now
        
        # Convert to dict after updating timestamps
        data = self.to_dict()
        
        if self.id:
            # Update existing document
            data.pop('_id', None)  # Remove _id for update
            data.pop('created_at', None)  # Don't update created_at
            
            # Ensure the updated_at field is explicitly included in the update
            data['updated_at'] = now.isoformat()
            
            mongodb.update_one(
                self.COLLECTION_NAME,
                {'_id': ObjectId(self.id)},
                data
            )
            return self.id
        else:
            # Insert new document
            self.id = mongodb.insert_one(self.COLLECTION_NAME, data)
            return self.id
    
    def delete(self) -> bool:
        """Delete the model from MongoDB."""
        if not self.id:
            return False
            
        mongodb = get_mongodb_service()
        return mongodb.delete_one(
            self.COLLECTION_NAME,
            {'_id': ObjectId(self.id)}
        )
    
    @classmethod
    def find_by_id(cls: Type[T], id: str) -> Optional[T]:
        """Find a model by ID."""
        if not id:
            return None
            
        mongodb = get_mongodb_service()
        data = mongodb.find_one(
            cls.COLLECTION_NAME,
            {'_id': ObjectId(id)}
        )
        
        return cls.from_dict(data) if data else None
    
    @classmethod
    def find_all(cls: Type[T], query: Optional[Dict] = None, limit: int = 100, 
                skip: int = 0, sort: Optional[list] = None) -> list[T]:
        """Find all models matching the query.
        
        Args:
            query: MongoDB query filter
            limit: Maximum number of results to return
            skip: Number of documents to skip (for pagination)
            sort: List of (key, direction) pairs for sorting
            
        Returns:
            List of model instances matching the query
        """
        mongodb = get_mongodb_service()
        results = mongodb.find_many(
            cls.COLLECTION_NAME,
            filter_dict=query or {},
            limit=limit,
            skip=skip,
            sort=sort
        )
        return [cls.from_dict(data) for data in results if data]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB."""
        data = self.__dict__.copy()
        data.pop('id', None)
        
        # Keep _id as is when saving to MongoDB internally
        if hasattr(self, '_id') and not self.id:
            data['_id'] = self._id
        elif self.id:
            # For API responses, use string ID to ensure JSON serialization works
            if '_id' in data:
                data['_id'] = str(data['_id'])
            else:
                data['_id'] = str(self.id)
        
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
            
        # Convert _id to id
        if '_id' in data:
            data['id'] = str(data['_id'])
            data.pop('_id')
            
        return cls(**data)
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for this model."""
        pass  # Should be overridden by subclasses
