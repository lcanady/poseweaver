"""
MongoDB service layer for database operations.
"""
import os
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MongoDBService:
    """Service class for MongoDB operations."""
    
    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        
    def connect(self) -> None:
        """Connect to MongoDB."""
        try:
            # Get MongoDB URI from environment or use default localhost connection
            mongodb_uri = os.getenv(
                'MONGODB_URI', 
                'mongodb://admin:password@localhost:27017/mush_pose_editor?authSource=admin'
            )
            db_name = os.getenv('MONGODB_DB', 'mush_pose_editor')
            
            logger.info(f"Attempting to connect to MongoDB: {mongodb_uri.split('@')[0]}@[REDACTED]")
            
            # Configure MongoClient with appropriate timeouts for remote connections
            self._client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
                connectTimeoutMS=10000,         # 10 second timeout for connection
                socketTimeoutMS=10000,          # 10 second timeout for socket operations
                maxPoolSize=10,                 # Maximum connection pool size
                retryWrites=True                # Enable retryable writes
            )
            self._db = self._client[db_name]
            
            # Test the connection with timeout
            self._client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB database: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Don't raise the exception immediately, allow the service to retry later
            self._client = None
            self._db = None
    
    def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Disconnected from MongoDB")
    
    @property
    def db(self) -> Optional[Database]:
        """Get the database instance."""
        if self._db is None:
            self.connect()
        return self._db
    
    def get_collection(self, collection_name: str) -> Optional[Collection]:
        """Get a collection from the database."""
        if self.db is None:
            return None
        return self.db[collection_name]
    
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a single document."""
        # Add timestamp fields
        now = datetime.utcnow()
        document['created_at'] = now
        document['updated_at'] = now
        
        collection = self.get_collection(collection_name)
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    def find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        collection = self.get_collection(collection_name)
        document = collection.find_one(filter_dict)
        
        if document:
            # Convert ObjectId to string for JSON serialization
            document['_id'] = str(document['_id'])
        
        return document
    
    def find_many(self, collection_name: str, filter_dict: Dict[str, Any] = None, 
                  limit: int = 100, skip: int = 0, sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """Find multiple documents with pagination support.
        
        Args:
            collection_name: Name of the collection to query
            filter_dict: Dictionary of query filters
            limit: Maximum number of documents to return (default: 100)
            skip: Number of documents to skip (for pagination)
            sort: List of (field, direction) tuples to sort by
            
        Returns:
            List of matching documents with _id converted to string
        """
        collection = self.get_collection(collection_name)
        
        cursor = collection.find(filter_dict or {})
        
        if sort:
            cursor = cursor.sort(sort)
            
        if skip > 0:
            cursor = cursor.skip(skip)
            
        if limit > 0:
            cursor = cursor.limit(limit)
        
        documents = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            documents.append(doc)
        
        return documents
    
    def update_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                   update_dict: Dict[str, Any]) -> bool:
        """Update a single document."""
        # Always ensure updated_at is set to current time consistently
        update_dict['updated_at'] = datetime.utcnow().isoformat()
        
        collection = self.get_collection(collection_name)
        result = collection.update_one(filter_dict, {'$set': update_dict})
        return result.modified_count > 0
    
    def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document."""
        collection = self.get_collection(collection_name)
        result = collection.delete_one(filter_dict)
        return result.deleted_count > 0
    
    def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents in a collection."""
        collection = self.get_collection(collection_name)
        return collection.count_documents(filter_dict or {})
    
    def create_index(self, collection_name: str, index_spec: str, unique: bool = False) -> None:
        """Create an index on a collection."""
        collection = self.get_collection(collection_name)
        collection.create_index(index_spec, unique=unique)
        logger.info(f"Created index on {collection_name}.{index_spec}")


# Global MongoDB service instance
mongodb_service = MongoDBService()


def get_mongodb_service() -> MongoDBService:
    """Get the global MongoDB service instance."""
    return mongodb_service 