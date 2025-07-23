"""
Unit tests for Scene Management Service.

Tests scene lifecycle management, pose addition, history retrieval,
and archiving functionality according to the Scene Memory & Continuity spec.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.scene_management_service import SceneManagementService, PoseData
from app.models.scene_memory import (
    SceneMemory, Pose, SceneStatus, PoseType, Severity
)


class TestSceneManagementService:
    """Test cases for SceneManagementService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = SceneManagementService()
        self.test_owner_id = "test_owner_123"
        self.test_scene_name = "Test Scene"
        self.test_scene_description = "A test scene for unit testing"
        
    @patch('app.models.scene_memory.SceneMemory.find_by_owner')
    @patch('app.models.scene_memory.SceneMemory.save')
    def test_create_scene_success(self, mock_save, mock_find_by_owner):
        """Test successful scene creation."""
        # Mock no existing scenes
        mock_find_by_owner.return_value = []
        mock_save.return_value = "scene_123"
        
        # Create scene
        scene = self.service.create_scene(
            name=self.test_scene_name,
            description=self.test_scene_description,
            owner_id=self.test_owner_id,
            metadata={"test": "data"}
        )
        
        # Verify scene properties
        assert scene.name == self.test_scene_name
        assert scene.description == self.test_scene_description
        assert scene.owner_id == self.test_owner_id
        assert scene.status == SceneStatus.ACTIVE
        assert scene.metadata == {"test": "data"}
        assert scene.participant_count == 0
        assert scene.pose_count == 0
        
        # Verify save was called
        mock_save.assert_called_once()
        
    @patch('app.models.scene_memory.SceneMemory.find_by_owner')
    def test_create_scene_duplicate_name(self, mock_find_by_owner):
        """Test scene creation with duplicate name raises ValueError."""
        # Mock existing scene with same name
        existing_scene = Mock()
        existing_scene.name = self.test_scene_name
        mock_find_by_owner.return_value = [existing_scene]
        
        # Attempt to create scene with duplicate name
        with pytest.raises(ValueError, match="Scene with name .* already exists"):
            self.service.create_scene(
                name=self.test_scene_name,
                description=self.test_scene_description,
                owner_id=self.test_owner_id
            )
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    @patch('app.models.scene_memory.Pose.save')
    def test_add_pose_success(self, mock_pose_save, mock_find_by_id):
        """Test successful pose addition."""
        # Mock active scene
        mock_scene = Mock()
        mock_scene.status = SceneStatus.ACTIVE
        mock_scene.pose_count = 5
        mock_find_by_id.return_value = mock_scene
        mock_pose_save.return_value = "pose_123"
        
        # Create pose data
        pose_data = PoseData(
            character_name="Test Character",
            content="This is a test pose.",
            pose_type=PoseType.ACTION,
            is_ooc=False
        )
        
        # Add pose
        pose = self.service.add_pose("scene_123", pose_data)
        
        # Verify pose properties
        assert pose.scene_id == "scene_123"
        assert pose.character_name == "Test Character"
        assert pose.content == "This is a test pose."
        assert pose.pose_type == PoseType.ACTION
        assert pose.is_ooc is False
        assert isinstance(pose.timestamp, datetime)
        
        # Verify scene was updated
        mock_scene.update_activity.assert_called_once()
        mock_scene.save.assert_called_once()
        assert mock_scene.pose_count == 6
        
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_add_pose_scene_not_found(self, mock_find_by_id):
        """Test pose addition to non-existent scene raises ValueError."""
        mock_find_by_id.return_value = None
        
        pose_data = PoseData(
            character_name="Test Character",
            content="This is a test pose."
        )
        
        with pytest.raises(ValueError, match="Scene .* not found"):
            self.service.add_pose("nonexistent_scene", pose_data)
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_add_pose_inactive_scene(self, mock_find_by_id):
        """Test pose addition to inactive scene raises ValueError."""
        # Mock inactive scene
        mock_scene = Mock()
        mock_scene.status = SceneStatus.ARCHIVED
        mock_find_by_id.return_value = mock_scene
        
        pose_data = PoseData(
            character_name="Test Character",
            content="This is a test pose."
        )
        
        with pytest.raises(ValueError, match="Cannot add pose to inactive scene"):
            self.service.add_pose("scene_123", pose_data)
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    @patch('app.models.scene_memory.Pose.find_by_scene')
    def test_get_scene_history_success(self, mock_find_by_scene, mock_find_by_id):
        """Test successful scene history retrieval."""
        # Mock scene
        mock_scene = Mock()
        mock_find_by_id.return_value = mock_scene
        
        # Mock poses
        mock_poses = [
            Mock(is_ooc=False, timestamp=datetime.utcnow()),
            Mock(is_ooc=True, timestamp=datetime.utcnow()),
            Mock(is_ooc=False, timestamp=datetime.utcnow())
        ]
        mock_find_by_scene.return_value = mock_poses
        
        # Get history
        poses = self.service.get_scene_history("scene_123", limit=10)
        
        # Verify results
        assert len(poses) == 3
        mock_find_by_scene.assert_called_once_with("scene_123", limit=10)
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    @patch('app.models.scene_memory.Pose.find_by_scene')
    def test_get_scene_history_exclude_ooc(self, mock_find_by_scene, mock_find_by_id):
        """Test scene history retrieval excluding OOC poses."""
        # Mock scene
        mock_scene = Mock()
        mock_find_by_id.return_value = mock_scene
        
        # Mock poses (2 IC, 1 OOC)
        mock_poses = [
            Mock(is_ooc=False),
            Mock(is_ooc=True),
            Mock(is_ooc=False)
        ]
        mock_find_by_scene.return_value = mock_poses
        
        # Get history excluding OOC
        poses = self.service.get_scene_history("scene_123", include_ooc=False)
        
        # Verify only IC poses returned
        assert len(poses) == 2
        for pose in poses:
            assert pose.is_ooc is False
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_get_scene_history_scene_not_found(self, mock_find_by_id):
        """Test scene history retrieval for non-existent scene raises ValueError."""
        mock_find_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Scene .* not found"):
            self.service.get_scene_history("nonexistent_scene")
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_update_scene_activity_success(self, mock_find_by_id):
        """Test successful scene activity update."""
        # Mock scene
        mock_scene = Mock()
        mock_find_by_id.return_value = mock_scene
        
        # Update activity
        self.service.update_scene_activity("scene_123")
        
        # Verify scene was updated
        mock_scene.update_activity.assert_called_once()
        mock_scene.save.assert_called_once()
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_update_scene_activity_scene_not_found(self, mock_find_by_id):
        """Test scene activity update for non-existent scene raises ValueError."""
        mock_find_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Scene .* not found"):
            self.service.update_scene_activity("nonexistent_scene")
    
    @patch('app.models.scene_memory.SceneMemory.find_scenes_for_archival')
    def test_archive_inactive_scenes_success(self, mock_find_scenes_for_archival):
        """Test successful archiving of inactive scenes."""
        # Mock scenes to archive
        mock_scenes = [
            Mock(id="scene_1", name="Scene 1"),
            Mock(id="scene_2", name="Scene 2")
        ]
        mock_find_scenes_for_archival.return_value = mock_scenes
        
        # Archive scenes
        archived_ids = self.service.archive_inactive_scenes(days_threshold=30)
        
        # Verify results
        assert archived_ids == ["scene_1", "scene_2"]
        
        # Verify scenes were archived
        for scene in mock_scenes:
            assert scene.status == SceneStatus.ARCHIVED
            scene.save.assert_called_once()
    
    @patch('app.models.scene_memory.SceneMemory.find_scenes_for_archival')
    def test_archive_inactive_scenes_none_found(self, mock_find_scenes_for_archival):
        """Test archiving when no inactive scenes found."""
        mock_find_scenes_for_archival.return_value = []
        
        archived_ids = self.service.archive_inactive_scenes(days_threshold=30)
        
        assert archived_ids == []
    
    @patch('app.models.scene_memory.SceneMemory.find_by_owner')
    def test_get_user_scenes_active_only(self, mock_find_by_owner):
        """Test getting user scenes (active only)."""
        # Mock scenes
        mock_scenes = [Mock(), Mock(), Mock()]
        mock_find_by_owner.return_value = mock_scenes
        
        # Get user scenes
        scenes = self.service.get_user_scenes(self.test_owner_id, include_archived=False)
        
        # Verify results
        assert len(scenes) == 3
        mock_find_by_owner.assert_called_once_with(self.test_owner_id, SceneStatus.ACTIVE)
    
    @patch('app.models.scene_memory.SceneMemory.find_by_owner')
    def test_get_user_scenes_include_archived(self, mock_find_by_owner):
        """Test getting user scenes including archived."""
        # Mock scenes
        mock_scenes = [Mock(), Mock(), Mock(), Mock()]
        mock_find_by_owner.return_value = mock_scenes
        
        # Get user scenes including archived
        scenes = self.service.get_user_scenes(self.test_owner_id, include_archived=True)
        
        # Verify results
        assert len(scenes) == 4
        mock_find_by_owner.assert_called_once_with(self.test_owner_id)
    
    @patch('app.models.scene_memory.SceneMemory.find_by_owner')
    def test_get_user_scenes_with_limit(self, mock_find_by_owner):
        """Test getting user scenes with limit."""
        # Mock more scenes than limit
        mock_scenes = [Mock() for _ in range(10)]
        mock_find_by_owner.return_value = mock_scenes
        
        # Get user scenes with limit
        scenes = self.service.get_user_scenes(self.test_owner_id, limit=5)
        
        # Verify limit applied
        assert len(scenes) == 5
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_pause_scene_success(self, mock_find_by_id):
        """Test successful scene pausing."""
        # Mock active scene
        mock_scene = Mock()
        mock_scene.status = SceneStatus.ACTIVE
        mock_find_by_id.return_value = mock_scene
        
        # Pause scene
        result = self.service.pause_scene("scene_123")
        
        # Verify results
        assert result is True
        assert mock_scene.status == SceneStatus.PAUSED
        mock_scene.save.assert_called_once()
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_pause_scene_not_found(self, mock_find_by_id):
        """Test pausing non-existent scene."""
        mock_find_by_id.return_value = None
        
        result = self.service.pause_scene("nonexistent_scene")
        
        assert result is False
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_pause_scene_not_active(self, mock_find_by_id):
        """Test pausing non-active scene."""
        # Mock archived scene
        mock_scene = Mock()
        mock_scene.status = SceneStatus.ARCHIVED
        mock_find_by_id.return_value = mock_scene
        
        result = self.service.pause_scene("scene_123")
        
        assert result is False
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_resume_scene_success(self, mock_find_by_id):
        """Test successful scene resuming."""
        # Mock paused scene
        mock_scene = Mock()
        mock_scene.status = SceneStatus.PAUSED
        mock_find_by_id.return_value = mock_scene
        
        # Resume scene
        result = self.service.resume_scene("scene_123")
        
        # Verify results
        assert result is True
        assert mock_scene.status == SceneStatus.ACTIVE
        mock_scene.update_activity.assert_called_once()
        mock_scene.save.assert_called_once()
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_resume_scene_not_paused(self, mock_find_by_id):
        """Test resuming non-paused scene."""
        # Mock active scene
        mock_scene = Mock()
        mock_scene.status = SceneStatus.ACTIVE
        mock_find_by_id.return_value = mock_scene
        
        result = self.service.resume_scene("scene_123")
        
        assert result is False
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_complete_scene_success(self, mock_find_by_id):
        """Test successful scene completion."""
        # Mock scene
        mock_scene = Mock()
        mock_find_by_id.return_value = mock_scene
        
        # Complete scene
        result = self.service.complete_scene("scene_123")
        
        # Verify results
        assert result is True
        assert mock_scene.status == SceneStatus.COMPLETED
        mock_scene.save.assert_called_once()
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_complete_scene_not_found(self, mock_find_by_id):
        """Test completing non-existent scene."""
        mock_find_by_id.return_value = None
        
        result = self.service.complete_scene("nonexistent_scene")
        
        assert result is False
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    @patch('app.models.scene_memory.Pose.find_by_scene')
    def test_get_scene_statistics_success(self, mock_find_by_scene, mock_find_by_id):
        """Test successful scene statistics retrieval."""
        # Mock scene
        mock_scene = Mock()
        mock_scene.id = "scene_123"
        mock_scene.name = "Test Scene"
        mock_scene.status = SceneStatus.ACTIVE
        mock_scene.created_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_scene.last_activity = datetime(2023, 1, 2, 12, 0, 0)
        mock_find_by_id.return_value = mock_scene
        
        # Mock poses
        mock_poses = [
            Mock(character_name="Alice", word_count=10),
            Mock(character_name="Bob", word_count=15),
            Mock(character_name="Alice", word_count=20)
        ]
        mock_find_by_scene.return_value = mock_poses
        
        # Get statistics
        stats = self.service.get_scene_statistics("scene_123")
        
        # Verify results
        assert stats['scene_id'] == "scene_123"
        assert stats['name'] == "Test Scene"
        assert stats['status'] == "active"
        assert stats['pose_count'] == 3
        assert stats['participant_count'] == 2
        assert stats['total_words'] == 45
        assert stats['character_counts'] == {"Alice": 2, "Bob": 1}
        assert stats['average_words_per_pose'] == 15.0
    
    @patch('app.models.scene_memory.SceneMemory.find_by_id')
    def test_get_scene_statistics_not_found(self, mock_find_by_id):
        """Test scene statistics for non-existent scene."""
        mock_find_by_id.return_value = None
        
        stats = self.service.get_scene_statistics("nonexistent_scene")
        
        assert stats is None
    
    @patch('app.models.scene_memory.SceneMemory.find_by_owner')
    def test_search_scenes_success(self, mock_find_by_owner):
        """Test successful scene search."""
        # Mock scenes
        mock_scenes = [
            Mock(name="Adventure Scene", description="An exciting adventure"),
            Mock(name="Tavern Scene", description="A quiet tavern"),
            Mock(name="Battle Scene", description="Epic battle adventure")
        ]
        mock_find_by_owner.return_value = mock_scenes
        
        # Search for "adventure"
        results = self.service.search_scenes(self.test_owner_id, "adventure")
        
        # Verify results (should match 2 scenes)
        assert len(results) == 2
        assert results[0].name == "Adventure Scene"
        assert results[1].name == "Battle Scene"
    
    @patch('app.models.scene_memory.SceneMemory.find_by_owner')
    def test_search_scenes_no_matches(self, mock_find_by_owner):
        """Test scene search with no matches."""
        # Mock scenes
        mock_scenes = [
            Mock(name="Adventure Scene", description="An exciting adventure"),
            Mock(name="Tavern Scene", description="A quiet tavern")
        ]
        mock_find_by_owner.return_value = mock_scenes
        
        # Search for non-matching term
        results = self.service.search_scenes(self.test_owner_id, "spaceship")
        
        # Verify no results
        assert len(results) == 0
    
    @patch('app.models.scene_memory.SceneMemory.find_by_owner')
    @patch('app.models.scene_memory.Pose.find_recent_by_scene')
    def test_get_recent_poses_across_scenes(self, mock_find_recent, mock_find_by_owner):
        """Test getting recent poses across multiple scenes."""
        # Mock scenes
        mock_scenes = [
            Mock(id="scene_1"),
            Mock(id="scene_2")
        ]
        mock_find_by_owner.return_value = mock_scenes
        
        # Mock recent poses
        recent_time = datetime.utcnow() - timedelta(hours=1)
        mock_poses_scene1 = [Mock(timestamp=recent_time)]
        mock_poses_scene2 = [Mock(timestamp=recent_time)]
        
        def mock_find_recent_side_effect(scene_id, hours, limit):
            if scene_id == "scene_1":
                return mock_poses_scene1
            elif scene_id == "scene_2":
                return mock_poses_scene2
            return []
        
        mock_find_recent.side_effect = mock_find_recent_side_effect
        
        # Get recent poses
        results = self.service.get_recent_poses_across_scenes(self.test_owner_id, hours=24)
        
        # Verify results
        assert len(results) == 2
        assert all(isinstance(result, tuple) and len(result) == 2 for result in results)


class TestPoseData:
    """Test cases for PoseData class."""
    
    def test_pose_data_creation_minimal(self):
        """Test PoseData creation with minimal parameters."""
        pose_data = PoseData(
            character_name="Test Character",
            content="Test content"
        )
        
        assert pose_data.character_name == "Test Character"
        assert pose_data.content == "Test content"
        assert pose_data.pose_type == PoseType.MIXED
        assert pose_data.is_ooc is False
        assert isinstance(pose_data.timestamp, datetime)
        assert pose_data.analysis_data == {}
    
    def test_pose_data_creation_full(self):
        """Test PoseData creation with all parameters."""
        test_timestamp = datetime(2023, 1, 1, 12, 0, 0)
        test_analysis = {"sentiment": "positive"}
        
        pose_data = PoseData(
            character_name="Test Character",
            content="Test content",
            pose_type=PoseType.DIALOGUE,
            is_ooc=True,
            timestamp=test_timestamp,
            analysis_data=test_analysis
        )
        
        assert pose_data.character_name == "Test Character"
        assert pose_data.content == "Test content"
        assert pose_data.pose_type == PoseType.DIALOGUE
        assert pose_data.is_ooc is True
        assert pose_data.timestamp == test_timestamp
        assert pose_data.analysis_data == test_analysis