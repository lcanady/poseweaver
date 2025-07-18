"""
Tests for the Scene model and service.
"""
import pytest
from bson import ObjectId
from datetime import datetime, timedelta

from app.models.scene import Scene, ScenePose, PoseType, SceneParticipant, SceneContext
from app.models.character import Character
from app.services.scene_service import SceneService
from app.services.character_mgmt_service import CharacterManagementService

@pytest.fixture
def sample_character():
    """Create a sample character for testing."""
    user_id = str(ObjectId())
    char = CharacterManagementService.create_character(
        user_id=user_id,
        name='Test Character',
        description='A test character'
    )
    yield char
    char.delete()

@pytest.fixture
def sample_scene(sample_character):
    """Create a sample scene for testing."""
    user_id = sample_character.user_id
    
    # Create a scene
    scene = SceneService.create_scene(
        name='Test Scene',
        created_by=user_id,
        description='A test scene',
        max_poses=50,
        initial_participants=[sample_character.id],
        initial_context={
            'setting': 'A dark forest',
            'mood': 'Tense',
            'recent_events': ['The party entered the forest'],
            'time_of_day': 'Night'
        }
    )
    
    yield scene
    
    # Clean up
    scene.delete()

def test_scene_creation(sample_scene, sample_character):
    """Test creating a new scene."""
    assert sample_scene is not None
    assert sample_scene.id is not None
    assert sample_scene.name == 'Test Scene'
    assert sample_scene.created_by == sample_character.user_id
    assert sample_scene.description == 'A test scene'
    assert sample_scene.max_poses == 50
    assert sample_scene.is_active is True
    
    # Verify context was set
    assert sample_scene.context is not None
    assert sample_scene.context.setting == 'A dark forest'
    assert sample_scene.context.mood == 'Tense'
    assert 'The party entered the forest' in sample_scene.context.recent_events
    assert sample_scene.context.time_of_day == 'Night'
    
    # Verify participant was added
    assert len(sample_scene.participants) == 1
    assert sample_character.id in sample_scene.participants
    participant = sample_scene.participants[sample_character.id]
    assert participant.character_id == sample_character.id
    assert participant.character_name == sample_character.name

def test_add_pose(sample_scene, sample_character):
    """Test adding a pose to a scene."""
    # Add a pose
    result = SceneService.add_pose(
        scene_id=sample_scene.id,
        character_id=sample_character.id,
        character_name=sample_character.name,
        pose_text="*looks around cautiously*",
        pose_type=PoseType.ACTION,
        tags=["emote"],
        mentions=[]
    )
    
    assert result is not None
    scene, pose = result
    
    # Verify the pose was added
    assert len(scene.poses) == 1
    assert pose.id is not None
    assert pose.character_id == sample_character.id
    assert pose.character_name == sample_character.name
    assert pose.pose_text == "*looks around cautiously*"
    assert pose.pose_type == PoseType.ACTION
    assert "emote" in pose.tags
    
    # Verify participant was updated
    participant = scene.participants[sample_character.id]
    assert participant.last_pose_id == pose.id
    assert participant.pose_count == 1
    assert participant.first_seen is not None
    assert participant.last_seen is not None

def test_add_multiple_poses(sample_scene, sample_character):
    """Test adding multiple poses to a scene."""
    # Add several poses
    for i in range(3):
        SceneService.add_pose(
            scene_id=sample_scene.id,
            character_id=sample_character.id,
            character_name=sample_character.name,
            pose_text=f"Test pose {i+1}",
            pose_type=PoseType.ACTION
        )
    
    # Reload the scene
    scene = Scene.find_by_id(sample_scene.id)
    
    # Verify all poses were added
    assert len(scene.poses) == 3
    assert scene.poses[0].pose_text == "Test pose 1"
    assert scene.poses[1].pose_text == "Test pose 2"
    assert scene.poses[2].pose_text == "Test pose 3"
    
    # Verify participant stats
    participant = scene.participants[sample_character.id]
    assert participant.pose_count == 3
    assert participant.last_pose_id == scene.poses[-1].id

def test_scene_compression(sample_scene, sample_character):
    """Test that old poses are compressed when the limit is reached."""
    # Set a low max_poses for testing
    sample_scene.max_poses = 3
    sample_scene.save()
    
    # Add more poses than the limit
    for i in range(5):
        SceneService.add_pose(
            scene_id=sample_scene.id,
            character_id=sample_character.id,
            character_name=sample_character.name,
            pose_text=f"Pose {i+1}",
            pose_type=PoseType.ACTION
        )
    
    # Reload the scene
    scene = Scene.find_by_id(sample_scene.id)
    
    # Verify compression occurred
    assert len(scene.poses) <= 3  # Should be at or below max_poses
    assert scene.compressed_history  # Should have compressed history
    
    # Verify the most recent poses are preserved
    pose_texts = [p.pose_text for p in scene.poses]
    assert "Pose 3" in pose_texts or "Pose 4" in pose_texts or "Pose 5" in pose_texts

def test_scene_participant_management(sample_scene, sample_character):
    """Test adding and removing participants from a scene."""
    # Create another character
    char2 = CharacterManagementService.create_character(
        user_id=sample_character.user_id,
        name='Another Character',
        description='Another test character'
    )
    
    try:
        # Add the new character to the scene
        updated_scene = SceneService.add_participant(
            scene_id=sample_scene.id,
            user_id=sample_character.user_id,
            character_id=char2.id
        )
        
        # Verify the participant was added
        assert updated_scene is not None
        assert len(updated_scene.participants) == 2
        assert char2.id in updated_scene.participants
        
        # Remove the participant
        updated_scene = SceneService.remove_participant(
            scene_id=sample_scene.id,
            user_id=sample_character.user_id,
            character_id=char2.id
        )
        
        # Verify the participant was removed
        assert updated_scene is not None
        assert len(updated_scene.participants) == 1
        assert char2.id not in updated_scene.participants
        
    finally:
        # Clean up
        char2.delete()

def test_scene_context_update(sample_scene):
    """Test updating a scene's context."""
    # Update the context
    updated_scene = SceneService.update_scene_context(
        scene_id=sample_scene.id,
        user_id=sample_scene.created_by,
        mood='Relaxed',
        time_of_day='Afternoon',
        recent_events=['The party took a break']
    )
    
    # Verify the updates
    assert updated_scene is not None
    assert updated_scene.context.mood == 'Relaxed'
    assert updated_scene.context.time_of_day == 'Afternoon'
    assert 'The party took a break' in updated_scene.context.recent_events
    
    # Verify the original context is still there
    assert updated_scene.context.setting == 'A dark forest'

def test_scene_deletion(sample_scene):
    """Test soft deleting a scene."""
    # Delete the scene
    success = SceneService.delete_scene(
        scene_id=sample_scene.id,
        user_id=sample_scene.created_by
    )
    
    # Verify deletion
    assert success is True
    
    # Try to retrieve the scene
    scene = Scene.find_by_id(sample_scene.id)
    assert scene is not None  # Should still exist
    assert scene.is_active is False  # But be marked as inactive
    
    # Verify it's not returned in active queries
    active_scenes = Scene.find_all({'created_by': sample_scene.created_by, 'is_active': True})
    assert not any(s.id == sample_scene.id for s in active_scenes)
