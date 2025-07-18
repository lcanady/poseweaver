"""
Character management service for MongoDB operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from ..models.character import Character
from ..models.user_mongo import User

class CharacterManagementService:
    """Service for managing character data in MongoDB."""
    
    @staticmethod
    def create_character(
        user_id: str,
        name: str,
        description: str = "",
        profile_image: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Character:
        """Create a new character.
        
        Args:
            user_id: ID of the user creating the character
            name: Character name
            description: Character description
            profile_image: URL to character's profile image
            tags: List of tags for the character
            metadata: Additional metadata for the character
            
        Returns:
            The created Character instance
            
        Raises:
            ValueError: If character with the same name already exists for the user
        """
        # Create and save the character
        # Note: Duplicate name check is handled in the model's save() method
        character = Character(
            name=name,
            user_id=user_id,
            description=description,
            profile_image=profile_image,
            tags=tags or [],
            metadata=metadata or {}
        )
        character.save()
        return character
    
    @staticmethod
    def get_character(character_id: str, user_id: Optional[str] = None) -> Optional[Character]:
        """Get a character by ID.
        
        Args:
            character_id: ID of the character to retrieve
            user_id: Optional user ID to verify ownership
            
        Returns:
            The Character instance, or None if not found or access denied
        """
        character = Character.find_by_id(character_id)
        if not character:
            return None
            
        # If user_id is provided, verify ownership
        if user_id and character.user_id != user_id:
            return None
            
        return character
    
    @staticmethod
    def list_characters(
        user_id: str,
        include_inactive: bool = False,
        limit: int = 100,
        skip: int = 0,
        sort_field: str = "name",
        sort_direction: int = 1
    ) -> List[Character]:
        """List characters for a user.
        
        Args:
            user_id: ID of the user whose characters to list
            include_inactive: Whether to include inactive characters
            limit: Maximum number of characters to return
            skip: Number of characters to skip (for pagination)
            sort_field: Field to sort by
            sort_direction: Sort direction (1 for ascending, -1 for descending)
            
        Returns:
            List of Character instances
        """
        # Use the find_by_user method which handles user_id conversion properly
        characters = Character.find_by_user(user_id, include_inactive=include_inactive)
        
        # Apply sorting, skip, and limit in memory since find_by_user already handles user_id conversion
        # Sort the characters by the specified field and direction
        if sort_field == "name":
            characters.sort(key=lambda c: c.name.lower(), reverse=(sort_direction == -1))
        elif hasattr(Character, sort_field):
            characters.sort(key=lambda c: getattr(c, sort_field), reverse=(sort_direction == -1))
        
        # Apply pagination
        start = skip
        end = skip + limit if limit > 0 else None
        return characters[start:end]
    
    @staticmethod
    def update_character(
        character_id: str,
        user_id: str,
        **updates
    ) -> Optional[Character]:
        """Update a character.
        
        Args:
            character_id: ID of the character to update
            user_id: ID of the user making the update
            **updates: Fields to update
            
        Returns:
            The updated Character instance, or None if not found or access denied
            
        Raises:
            ValueError: If trying to update to a name that's already in use
        """
        character = Character.find_by_id(character_id)
        if not character or character.user_id != user_id:
            return None
            
        # Check for name conflicts if name is being updated
        if 'name' in updates and updates['name'] != character.name:
            existing = Character.find_by_name(updates['name'], user_id=user_id)
            if existing and existing.id != character_id:
                raise ValueError(f"Character with name '{updates['name']}' already exists for this user")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(character, key):
                setattr(character, key, value)
        
        # Update timestamps
        character.updated_at = datetime.utcnow()
        
        # Save changes
        character.save()
        return character
    
    @staticmethod
    def delete_character(character_id: str, user_id: str) -> bool:
        """Delete a character.
        
        Args:
            character_id: ID of the character to delete
            user_id: ID of the user making the request
            
        Returns:
            True if deleted, False if not found or access denied
        """
        character = Character.find_by_id(character_id)
        if not character or character.user_id != user_id:
            return False
            
        # Soft delete by marking as inactive
        character.is_active = False
        character.save()
        return True
    
    @staticmethod
    def search_characters(
        user_id: str,
        query: str,
        limit: int = 20,
        include_inactive: bool = False
    ) -> List[Character]:
        """Search for characters by name or tags.
        
        Args:
            user_id: ID of the user whose characters to search
            query: Search query string
            limit: Maximum number of results to return
            include_inactive: Whether to include inactive characters
            
        Returns:
            List of matching Character instances
        """
        # First get all characters for the user
        all_characters = Character.find_by_user(user_id, include_inactive=include_inactive)
        
        # Filter in memory to avoid MongoDB query issues
        results = []
        query_lower = query.lower()
        
        for character in all_characters:
            # Check if query matches name (case-insensitive)
            if query_lower in character.name.lower():
                results.append(character)
                continue
                
            # Check if query matches any tag
            if character.tags and any(query_lower in tag.lower() for tag in character.tags):
                results.append(character)
                continue
                
        # Sort by name and apply limit
        results.sort(key=lambda c: c.name.lower())
        return results[:limit]
