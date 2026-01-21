"""
Firebase service layer for database operations.
"""
import os
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from flask import current_app
from .db_repository import DatabaseRepository

logger = logging.getLogger(__name__)

class FirebaseService(DatabaseRepository):
    """Service class for Firebase Firestore operations."""

    def __init__(self):
        self._db = None

    def connect(self) -> None:
        """Connect to Firebase Firestore.
           Note: Firebase Admin SDK is usually initialized at app startup,
           this method gets the client.
        """
        try:
            # Check if already initialized (usually by extensions.py)
            if not firebase_admin._apps:
                # Fallback initialization if extensions.py hasn't run or this is used independently
                cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                else:
                    firebase_admin.initialize_app()
            
            self._db = firestore.client()
            logger.info("Connected to Firestore")
        except Exception as e:
            logger.error(f"Failed to connect to Firestore: {e}")
            self._db = None

    def disconnect(self) -> None:
        """Disconnect from Firestore (No-op as Firestore client is stateless/managed by SDK)."""
        pass

    @property
    def db(self):
        if self._db is None:
            self.connect()
        return self._db

    def _serialize_document(self, doc_snapshot) -> Dict[str, Any]:
        """Convert Firestore document snapshot to dict with id."""
        if not doc_snapshot.exists:
            return None
        data = doc_snapshot.to_dict()
        data['id'] = doc_snapshot.id
        # Compatibility with Mongo models seeking _id
        data['_id'] = doc_snapshot.id 
        return data

    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a single document."""
        # Handle _id removal if present (from Mongo compatibility) and use as Doc ID if feasible
        doc_id = document.pop('_id', None)
        document.pop('id', None) # Remove 'id' if present to avoid duplication

        # Add timestamps
        now = datetime.utcnow()
        if 'created_at' not in document:
            document['created_at'] = now
        document['updated_at'] = now
        
        # Convert datetime objects to compatible format if needed by Firestore SDK
        # (Firestore Admin SDK handles python datetime objects natively)

        collection_ref = self.db.collection(collection_name)
        if doc_id:
            # If we have a specific ID preference (migration), use it
            doc_ref = collection_ref.document(str(doc_id))
            doc_ref.set(document)
            return str(doc_id)
        else:
            # Auto-generate ID
            update_time, doc_ref = collection_ref.add(document)
            return doc_ref.id

    def find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        collection_ref = self.db.collection(collection_name)
        
        # Optimization: If filter is only by _id or id, get directly
        if '_id' in filter_dict and len(filter_dict) == 1:
            doc = collection_ref.document(str(filter_dict['_id'])).get()
            return self._serialize_document(doc) if doc.exists else None
        if 'id' in filter_dict and len(filter_dict) == 1:
            doc = collection_ref.document(str(filter_dict['id'])).get()
            return self._serialize_document(doc) if doc.exists else None

        # Query
        query = collection_ref
        for key, value in filter_dict.items():
            if key in ['_id', 'id']:
                 # Cannot query equality on document ID field in general query builder easily mixed with others 
                 # without using FieldPath.documentId(). 
                 # For simplicity, if mixed, we might do client side filter or adjust strategy.
                 # But usually find_one with ID is handled above.
                 # If ID is part of composite filter, skip it here and warn? or assume it's a property?
                 # Firestore docs don't have 'id' field unless explicit. 
                 continue
            query = query.where(key, '==', value)
        
        # multiple results possible, limit 1
        docs = query.limit(1).stream()
        for doc in docs:
            return self._serialize_document(doc)
        
        return None

    def find_many(self, collection_name: str, filter_dict: Optional[Dict[str, Any]] = None, 
                  limit: int = 100, skip: int = 0, sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        query = self.db.collection(collection_name)
        
        if filter_dict:
            for key, value in filter_dict.items():
                if key == '$in':
                    # Firestore 'in' query implementation would need field name
                    # Mongo: {field: {$in: [...]}} -> Firestore: where(field, 'in', [...])
                    # Does not support root level $in without key
                    continue
                
                # Handle Mongo-style operators if possible
                if isinstance(value, dict):
                     for op, op_val in value.items():
                        if op == '$in':
                            query = query.where(key, 'in', op_val)
                        elif op == '$gte':
                            query = query.where(key, '>=', op_val)
                        elif op == '$lte':
                            query = query.where(key, '<=', op_val)
                        elif op == '$gt':
                            query = query.where(key, '>', op_val)
                        elif op == '$lt':
                            query = query.where(key, '<', op_val)
                        elif op == '$ne':
                            query = query.where(key, '!=', op_val)
                        # contains_any? array-contains?
                        # Mongo: {tags: {$in: [..]}} matches if ANY tag matches.
                        # Firestore: array-contains-any
                else:
                    query = query.where(key, '==', value)

        if sort:
            for field, direction in sort:
                descending = (direction == -1)
                direction_str = firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
                query = query.order_by(field, direction=direction_str)
        
        # Firestore offset is expensive but supported
        if skip > 0:
            query = query.offset(skip)
            
        if limit > 0:
            query = query.limit(limit)

        results = []
        try:
            docs = query.stream()
            results = [self._serialize_document(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error executing find_many query on {collection_name}: {e}")
            
        return results

    def update_one(self, collection_name: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> bool:
        """Update a single document."""
        # Find document ref first
        doc_data = self.find_one(collection_name, filter_dict)
        if not doc_data:
            return False
        
        doc_id = doc_data['id']
        doc_ref = self.db.collection(collection_name).document(doc_id)
        
        # Prepare updates
        # Mongo sends {'$set': {...}} often. our abstraction sends plain dict for updates?
        # The base model calls this with {'key': 'val'}, but we should check if it sends $set wrappers or not.
        # Looking at mongodb_service implementation: 
        #   update_dict['updated_at'] = ...
        #   collection.update_one(filter_dict, {'$set': update_dict})
        # So the input `update_dict` is the actual fields to set.
        
        if 'updated_at' not in update_dict:
            update_dict['updated_at'] = datetime.utcnow()
            
        try:
            doc_ref.update(update_dict)
            return True
        except Exception as e:
            logger.error(f"Failed to update document {doc_id} in {collection_name}: {e}")
            return False

    def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document."""
        doc_data = self.find_one(collection_name, filter_dict)
        if not doc_data:
            return False
            
        doc_id = doc_data['id']
        try:
            self.db.collection(collection_name).document(doc_id).delete()
            return True
        except Exception as e:
             logger.error(f"Failed to delete document {doc_id} in {collection_name}: {e}")
             return False

    def count_documents(self, collection_name: str, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """Count documents. Note: Aggregation query in Firestore."""
        query = self.db.collection(collection_name)
        if filter_dict:
            # Apply same filtering logic as find_many
            # For simplicity, minimal filtering here or re-use logic
            for key, value in filter_dict.items():
                 if isinstance(value, dict):
                     # Skip complex filters for count for now or implement deeply
                     continue 
                 query = query.where(key, '==', value)

        # Count count() is a proper aggregation query now supported
        try:
            count_query = query.count()
            return count_query.get()[0][0].value
        except Exception:
            # Fallback for older SDKs or emulators
            return len(list(query.stream()))

    def create_index(self, collection_name: str, index_spec: Union[str, List[tuple]], unique: bool = False) -> None:
        """
        Create index. 
        Note: Firestore indexes are managed via firebase.json or Console. 
        Programmatic creation is not standard in the same way as Mongo.
        We log a warning or no-op.
        """
        logger.info(f"Skipping programmatic index creation for {collection_name}. Manage Firestore indexes via Console or firebase.json.")
