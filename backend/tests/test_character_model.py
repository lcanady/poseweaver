"""
Tests for the Character model and service.
"""
import pytest
from bson import ObjectId
from datetime import datetime, timedelta

from app.models.character import Character
from app.services.character_mgmt_service import CharacterManagementService

@pytest.fixture
def sample_character_data():
    """Sample character data for testing."""
    return {
        'name': 'Test Character',
        'description': 'A test character',
        'profile_image': 'https://example.com/test.jpg',
        'tags': ['test', 'adventurer'],
        'metadata': {'level': 5, 'class': 'Warrior'}
    }

def test_character_creation(sample_character_data):
    """Test creating a new character."""
    user_id = str(ObjectId())
    
    # Create character
    character = Character(
        user_id=user_id,
        **sample_character_data
    )
    character.save()
    
    # Verify the character was saved
    assert character.id is not None
    assert character.created_at is not None
    assert character.updated_at is not None
    assert character.is_active is True
    
    # Clean up
    character.delete()

def test_character_retrieval(sample_character_data):
    """Test retrieving a character by ID."""
    user_id = str(ObjectId())
    
    # Create a test character
    character = Character(
        user_id=user_id,
        **sample_character_data
    )
    character.save()
    
    try:
        # Retrieve the character
        retrieved = Character.find_by_id(character.id)
        
        # Verify the retrieved character matches
        assert retrieved is not None
        assert retrieved.id == character.id
        assert retrieved.name == sample_character_data['name']
        assert retrieved.description == sample_character_data['description']
        assert retrieved.tags == sample_character_data['tags']
        assert retrieved.metadata == sample_character_data['metadata']
        
    finally:
        # Clean up
        character.delete()

def test_character_update(sample_character_data):
    """Test updating a character."""
    user_id = str(ObjectId())
    
    # Create a test character
    character = Character(
        user_id=user_id,
        **sample_character_data
    )
    character.save()
    
    try:
        # Update the character
        updated_name = 'Updated Test Character'
        updated_description = 'Updated description'
        
        character.name = updated_name
        character.description = updated_description
        character.tags.append('updated')
        character.metadata['level'] = 6
        
        # Save the updates
        original_updated_at = character.updated_at
        import time
        time.sleep(0.1)  # Ensure timestamp changes
        character.save()
        
        # Verify updates were saved
        assert character.name == updated_name
        assert character.description == updated_description
        assert 'updated' in character.tags
        assert character.metadata['level'] == 6
        
        # Verify the updated_at timestamp was updated
        assert character.updated_at > original_updated_at
        
        # Verify we can retrieve the updated character
        retrieved = Character.find_by_id(character.id)
        assert retrieved is not None
        assert retrieved.name == updated_name
        assert retrieved.description == updated_description
        
    finally:
        # Clean up
        character.delete()

def test_character_deletion(sample_character_data):
    """Test soft deleting a character."""
    user_id = str(ObjectId())
    
    # Create a test character
    character = Character(
        user_id=user_id,
        **sample_character_data
    )
    character.save()
    character_id = character.id
    
    try:
        # Verify the character exists
        retrieved = Character.find_by_id(character_id)
        assert retrieved is not None
        print(f"Character found by ID: {retrieved.id}, is_active={retrieved.is_active}")
        
        # Soft delete the character
        character.is_active = False
        character.save()
        
        # Verify it's marked as inactive
        assert character.is_active is False
        
        # Verify it's not returned in active queries
        active_chars = Character.find_by_user(user_id, include_inactive=False)
        print(f"Active chars count: {len(active_chars)}")
        assert not any(c.id == character_id for c in active_chars)
        
        # But is returned when including inactive
        all_chars = Character.find_by_user(user_id, include_inactive=True)
        print(f"All chars count: {len(all_chars)}")
        for c in all_chars:
            print(f"Found character: {c.id}, is_active={c.is_active}, name={c.name}")
            
        # Check if the character is still in the database
        direct_check = Character.find_by_id(character_id)
        print(f"Direct check: {direct_check.id if direct_check else 'Not found'}, is_active={direct_check.is_active if direct_check else None}")
        
        assert any(c.id == character_id for c in all_chars)
        
    finally:
        # Clean up
        character.delete()

def test_character_service_create():
    """Test creating a character using the service."""
    user_id = str(ObjectId())
    
    # Create character using service
    character = CharacterManagementService.create_character(
        user_id=user_id,
        name='Service Test Character',
        description='Created via service',
        tags=['service', 'test']
    )
    
    try:
        assert character is not None
        assert character.id is not None
        assert character.user_id == user_id
        assert character.name == 'Service Test Character'
        assert character.description == 'Created via service'
        assert 'service' in character.tags
        assert 'test' in character.tags
        
    finally:
        # Clean up
        character.delete()

def test_character_service_duplicate_name():
    """Test that duplicate character names are not allowed for the same user."""
    user_id = str(ObjectId())
    name = 'Duplicate Test Character'
    
    # Create first character
    char1 = CharacterManagementService.create_character(
        user_id=user_id,
        name=name,
        description='First character'
    )
    
    try:
        # Try to create another character with the same name for the same user
        with pytest.raises(ValueError) as excinfo:
            CharacterManagementService.create_character(
                user_id=user_id,
                name=name.upper(),  # Test case-insensitive match
                description='Second character with same name'
            )
            
        assert 'already exists' in str(excinfo.value).lower()
        
        # Verify a different user can create a character with the same name
        other_user = str(ObjectId())
        char3 = CharacterManagementService.create_character(
            user_id=other_user,
            name=name,
            description='Same name, different user'
        )
        assert char3 is not None
        
    finally:
        # Clean up
        char1.delete()

def test_character_service_list():
    """Test listing characters with pagination and sorting."""
    user_id = str(ObjectId())
    
    # Create test characters
    chars = []
    try:
        # Create characters in reverse order to test sorting
        for i in range(4, -1, -1):
            char = CharacterManagementService.create_character(
                user_id=user_id,
                name=f'List Test Character {i}',
                description=f'Character {i} for listing test'
            )
            chars.append(char)
        
        # List characters with pagination (should be sorted by name)
        result = CharacterManagementService.list_characters(
            user_id=user_id,
            limit=2,
            skip=1,
            sort_field='name',
            sort_direction=1  # Ascending
        )
        
        # Verify pagination and sorting
        assert len(result) == 2
        # Characters are sorted lexicographically, so '1' comes before '2'
        assert result[0].name == 'List Test Character 1'  # First item after skip
        assert result[1].name == 'List Test Character 2'  # Second item
        
        # Test searching with case-insensitive match
        search_results = CharacterManagementService.search_characters(
            user_id=user_id,
            query='LIST TEST CHARACTER 3',  # Uppercase to test case-insensitivity
            limit=10
        )
        
        assert len(search_results) == 1
        assert search_results[0].name == 'List Test Character 3'
        
    finally:
        # Clean up
        for char in chars:
            char.delete()
