"""
Core Scene Management Service for Scene Memory & Continuity Tracking.

This service provides scene lifecycle management, pose storage, history retrieval,
and archiving functionality according to the Scene Memory & Continuity spec.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging
from ..models.scene_memory import (
    SceneMemory, Pose, CharacterState, EnvironmentState, 
    PlotThread, SceneStatus, PoseType
)

logger = logging.getLogger(__name__)


class PoseData:
    """Data structure for pose creation."""
    
    def __init__(
        self,
        character_name: str,
        content: str,
        pose_type: PoseType = PoseType.MIXED,
        is_ooc: bool = False,
        timestamp: Optional[datetime] = None,
        analysis_data: Optional[Dict[str, Any]] = None
    ):
        self.character_name = character_name
        self.content = content
        self.pose_type = pose_type
        self.is_ooc = is_ooc
        self.timestamp = timestamp or datetime.utcnow()
        self.analysis_data = analysis_data or {}


class SceneManagementService:
    """
    Core service for managing scene lifecycle, pose storage, and basic scene operations.
    
    This service handles:
    - Scene creation and lifecycle management
    - Pose addition and storage
    - Scene history retrieval
    - Scene archiving for inactive scenes
    - Activity tracking and updates
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_scene(
        self, 
        name: str, 
        description: str, 
        owner_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SceneMemory:
        """
        Create a new scene with the specified parameters.
        
        Args:
            name: Name of the scene
            description: Description of the scene
            owner_id: ID of the user creating the scene
            metadata: Optional metadata dictionary
            
        Returns:
            The created SceneMemory instance
            
        Raises:
            ValueError: If a scene with the same name already exists for the owner
            
        Requirements: 1.1 - Scene creation with unique identifier
        """
        self.logger.info(f"Creating scene '{name}' for owner {owner_id}")
        
        # Check for existing scene with same name for this owner
        existing_scenes = SceneMemory.find_by_owner(owner_id, SceneStatus.ACTIVE)
        for scene in existing_scenes:
            if scene.name == name:
                raise ValueError(f"Scene with name '{name}' already exists for this owner")
        
        # Create the scene
        scene = SceneMemory(
            name=name,
            description=description,
            owner_id=owner_id,
            status=SceneStatus.ACTIVE,
            metadata=metadata or {},
            participant_count=0,
            pose_count=0
        )
        
        # Save to database
        scene_id = scene.save()
        self.logger.info(f"Created scene {scene_id} successfully")
        
        return scene
    
    def add_pose(self, scene_id: str, pose_data: PoseData) -> Pose:
        """
        Add a pose to an existing scene.
        
        Args:
            scene_id: ID of the scene to add the pose to
            pose_data: PoseData instance containing pose information
            
        Returns:
            The created Pose instance
            
        Raises:
            ValueError: If scene not found or is not active
            
        Requirements: 1.2 - Automatic pose storage with timestamp and character attribution
        """
        self.logger.info(f"Adding pose to scene {scene_id} by {pose_data.character_name}")
        
        # Verify scene exists and is active
        scene = SceneMemory.find_by_id(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        if scene.status != SceneStatus.ACTIVE:
            raise ValueError(f"Cannot add pose to inactive scene {scene_id}")
        
        # Create the pose
        pose = Pose(
            scene_id=scene_id,
            character_name=pose_data.character_name,
            content=pose_data.content,
            pose_type=pose_data.pose_type,
            timestamp=pose_data.timestamp,
            is_ooc=pose_data.is_ooc,
            analysis_data=pose_data.analysis_data
        )
        
        # Save the pose
        pose_id = pose.save()
        
        # Update scene activity and pose count
        scene.pose_count += 1
        scene.update_activity()
        scene.save()
        
        self.logger.info(f"Added pose {pose_id} to scene {scene_id}")
        return pose
    
    def get_scene_history(
        self, 
        scene_id: str, 
        limit: int = 100,
        include_ooc: bool = True
    ) -> List[Pose]:
        """
        Retrieve scene history with poses in chronological order.
        
        Args:
            scene_id: ID of the scene
            limit: Maximum number of poses to return
            include_ooc: Whether to include out-of-character poses
            
        Returns:
            List of Pose instances in chronological order
            
        Requirements: 1.5 - Display poses in chronological order with character attribution
        """
        self.logger.debug(f"Retrieving history for scene {scene_id}, limit={limit}")
        
        # Verify scene exists
        scene = SceneMemory.find_by_id(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        # Get poses for the scene
        poses = Pose.find_by_scene(scene_id, limit=limit)
        
        # Filter out OOC poses if requested
        if not include_ooc:
            poses = [pose for pose in poses if not pose.is_ooc]
        
        self.logger.debug(f"Retrieved {len(poses)} poses for scene {scene_id}")
        return poses
    
    def update_scene_activity(self, scene_id: str) -> None:
        """
        Update the last activity timestamp for a scene.
        
        Args:
            scene_id: ID of the scene to update
            
        Raises:
            ValueError: If scene not found
            
        Requirements: 1.3 - Maintain continuity across session breaks
        """
        self.logger.debug(f"Updating activity for scene {scene_id}")
        
        scene = SceneMemory.find_by_id(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        scene.update_activity()
        scene.save()
        
        self.logger.debug(f"Updated activity timestamp for scene {scene_id}")
    
    def archive_inactive_scenes(self, days_threshold: int = 30) -> List[str]:
        """
        Archive scenes that have been inactive for the specified number of days.
        
        Args:
            days_threshold: Number of days of inactivity before archiving
            
        Returns:
            List of scene IDs that were archived
            
        Requirements: 1.4 - Archive inactive scenes but keep them accessible
        """
        self.logger.info(f"Archiving scenes inactive for {days_threshold} days")
        
        # Find scenes to archive
        scenes_to_archive = SceneMemory.find_scenes_for_archival(days_threshold)
        archived_scene_ids = []
        
        for scene in scenes_to_archive:
            self.logger.info(f"Archiving scene {scene.id}: {scene.name}")
            scene.status = SceneStatus.ARCHIVED
            scene.save()
            archived_scene_ids.append(scene.id)
        
        self.logger.info(f"Archived {len(archived_scene_ids)} scenes")
        return archived_scene_ids
    
    def get_user_scenes(
        self, 
        user_id: str, 
        include_archived: bool = False,
        limit: int = 50
    ) -> List[SceneMemory]:
        """
        Get all scenes for a specific user.
        
        Args:
            user_id: ID of the user
            include_archived: Whether to include archived scenes
            limit: Maximum number of scenes to return
            
        Returns:
            List of SceneMemory instances ordered by last activity
        """
        self.logger.debug(f"Getting scenes for user {user_id}")
        
        if include_archived:
            scenes = SceneMemory.find_by_owner(user_id)
        else:
            scenes = SceneMemory.find_by_owner(user_id, SceneStatus.ACTIVE)
        
        # Apply limit
        scenes = scenes[:limit]
        
        self.logger.debug(f"Found {len(scenes)} scenes for user {user_id}")
        return scenes
    
    def get_scene(self, scene_id: str) -> Optional[SceneMemory]:
        """
        Get a scene by ID.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            SceneMemory instance or None if not found
        """
        return SceneMemory.find_by_id(scene_id)
    
    def pause_scene(self, scene_id: str) -> bool:
        """
        Pause an active scene.
        
        Args:
            scene_id: ID of the scene to pause
            
        Returns:
            True if successful, False if scene not found or not active
        """
        scene = SceneMemory.find_by_id(scene_id)
        if not scene or scene.status != SceneStatus.ACTIVE:
            return False
        
        scene.status = SceneStatus.PAUSED
        scene.save()
        
        self.logger.info(f"Paused scene {scene_id}")
        return True
    
    def resume_scene(self, scene_id: str) -> bool:
        """
        Resume a paused scene.
        
        Args:
            scene_id: ID of the scene to resume
            
        Returns:
            True if successful, False if scene not found or not paused
        """
        scene = SceneMemory.find_by_id(scene_id)
        if not scene or scene.status != SceneStatus.PAUSED:
            return False
        
        scene.status = SceneStatus.ACTIVE
        scene.update_activity()
        scene.save()
        
        self.logger.info(f"Resumed scene {scene_id}")
        return True
    
    def complete_scene(self, scene_id: str) -> bool:
        """
        Mark a scene as completed.
        
        Args:
            scene_id: ID of the scene to complete
            
        Returns:
            True if successful, False if scene not found
        """
        scene = SceneMemory.find_by_id(scene_id)
        if not scene:
            return False
        
        scene.status = SceneStatus.COMPLETED
        scene.save()
        
        self.logger.info(f"Completed scene {scene_id}")
        return True
    
    def get_scene_statistics(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            Dictionary containing scene statistics or None if scene not found
        """
        scene = SceneMemory.find_by_id(scene_id)
        if not scene:
            return None
        
        poses = Pose.find_by_scene(scene_id)
        
        # Calculate statistics
        character_counts = {}
        total_words = 0
        
        for pose in poses:
            character_counts[pose.character_name] = character_counts.get(pose.character_name, 0) + 1
            total_words += pose.word_count or 0
        
        return {
            'scene_id': scene_id,
            'name': scene.name,
            'status': scene.status.value,
            'created_at': scene.created_at.isoformat(),
            'last_activity': scene.last_activity.isoformat(),
            'pose_count': len(poses),
            'participant_count': len(character_counts),
            'total_words': total_words,
            'character_counts': character_counts,
            'average_words_per_pose': total_words / len(poses) if poses else 0
        }
    
    def search_scenes(
        self, 
        owner_id: str, 
        query: str, 
        limit: int = 20
    ) -> List[SceneMemory]:
        """
        Search scenes by name or description.
        
        Args:
            owner_id: ID of the scene owner
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching SceneMemory instances
        """
        # Get all scenes for the owner
        scenes = SceneMemory.find_by_owner(owner_id)
        
        # Filter by query (simple text matching)
        query_lower = query.lower()
        matching_scenes = []
        
        for scene in scenes:
            if (query_lower in scene.name.lower() or 
                query_lower in scene.description.lower()):
                matching_scenes.append(scene)
                
                if len(matching_scenes) >= limit:
                    break
        
        return matching_scenes
    
    def get_recent_poses_across_scenes(
        self, 
        owner_id: str, 
        hours: int = 24, 
        limit: int = 50
    ) -> List[Tuple[SceneMemory, Pose]]:
        """
        Get recent poses across all scenes owned by a user.
        
        Args:
            owner_id: ID of the scene owner
            hours: Number of hours to look back
            limit: Maximum number of poses to return
            
        Returns:
            List of (SceneMemory, Pose) tuples ordered by timestamp
        """
        # Get active scenes for the owner
        scenes = SceneMemory.find_by_owner(owner_id, SceneStatus.ACTIVE)
        
        # Collect recent poses from all scenes
        all_poses = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for scene in scenes:
            recent_poses = Pose.find_recent_by_scene(scene.id, hours, limit)
            for pose in recent_poses:
                if pose.timestamp >= cutoff_time:
                    all_poses.append((scene, pose))
        
        # Sort by timestamp (most recent first)
        all_poses.sort(key=lambda x: x[1].timestamp, reverse=True)
        
        return all_poses[:limit]