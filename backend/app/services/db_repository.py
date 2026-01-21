"""
Database repository interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union

class DatabaseRepository(ABC):
    """Abstract base class for database repositories."""

    @abstractmethod
    def connect(self) -> None:
        """Connect to the database."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the database."""
        pass

    @abstractmethod
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """
        Insert a single document.
        Returns the ID of the inserted document.
        """
        pass

    @abstractmethod
    def find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the filter."""
        pass

    @abstractmethod
    def find_many(self, 
                  collection_name: str, 
                  filter_dict: Optional[Dict[str, Any]] = None,
                  limit: int = 100, 
                  skip: int = 0, 
                  sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """Find multiple documents with pagination and sorting."""
        pass

    @abstractmethod
    def update_one(self, collection_name: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> bool:
        """
        Update a single document.
        Returns True if a document was modified, False otherwise.
        """
        pass

    @abstractmethod
    def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """
        Delete a single document.
        Returns True if a document was deleted, False otherwise.
        """
        pass
        
    @abstractmethod
    def count_documents(self, collection_name: str, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching the filter."""
        pass

    @abstractmethod
    def create_index(self, collection_name: str, index_spec: Union[str, List[tuple]], unique: bool = False) -> None:
        """Create an index on the collection."""
        pass
