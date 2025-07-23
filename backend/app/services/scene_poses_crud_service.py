"""
Scene Poses CRUD Service for scene pose management with debounce.

This service provides create, read, update and delete operations for poses
in a scene with a debounced save mechanism to improve performance.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable
import time
import threading
import logging
import atexit
from ..models.scene_memory import (
    SceneMemory, Pose, PoseType
)
from .scene_management_service import SceneManagementService, PoseData

logger = logging.getLogger(__name__)


class ScenePosesCrudService:
    """
    Service for managing CRUD operations on scene poses with debounced saving.
    
    This service provides:
    - Create/Add pose to scene
    - Read/Get poses from scene 
    - Update existing poses in scene
    - Delete poses from scene
    - All state-changing operations are debounced by 1 second before saving
    """
    
    def __init__(self, scene_management_service: SceneManagementService = None):
        """
        Initialize the Scene Poses CRUD service.
        
        Args:
            scene_management_service: Optional SceneManagementService instance
        """
        self.logger = logging.getLogger(__name__)
        self.scene_management_service = scene_management_service or SceneManagementService()
        
        # Debounce related attributes
        self._save_timers = {}  # Dictionary to track debounce timers by scene_id
        self._pending_changes = {}  # Dictionary to track pending changes by scene_id
        self.debounce_time = 1.0  # 1 second debounce time
        
        # Register cleanup handler to execute pending operations on exit
        atexit.register(self._cleanup)
    
    def create_pose(
        self,
        scene_id: str,
        character_name: str,
        content: str,
        pose_type: PoseType = PoseType.MIXED,
        is_ooc: bool = False,
        analysis_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new pose in the scene with debounced saving.
        
        Args:
            scene_id: ID of the scene to add the pose to
            character_name: Name of the character making the pose
            content: Text content of the pose
            pose_type: Type of pose (action, dialogue, etc.)
            is_ooc: Whether the pose is out-of-character
            analysis_data: Optional metadata for the pose
            
        Returns:
            Temporary ID for the created pose
            
        Raises:
            ValueError: If scene not found or invalid parameters
        """
        self.logger.info(f"Creating pose in scene {scene_id} for character {character_name}")
        
        # Validate scene exists
        scene = SceneMemory.find_by_id(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        # Create pose data
        pose_data = PoseData(
            character_name=character_name,
            content=content,
            pose_type=pose_type,
            is_ooc=is_ooc,
            timestamp=datetime.utcnow(),
            analysis_data=analysis_data or {}
        )
        
        # Generate temporary ID for the pose
        import uuid
        temp_pose_id = f"temp_{uuid.uuid4()}"
        
        # Schedule the save operation with debounce
        self._schedule_debounced_operation(
            scene_id=scene_id,
            operation_key=f"create_{temp_pose_id}",
            operation=lambda: self.scene_management_service.add_pose(scene_id, pose_data),
            operation_type="create"
        )
        
        return temp_pose_id
    
    def read_poses(
        self,
        scene_id: str,
        limit: int = 100,
        include_ooc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Read poses from a scene.
        
        Args:
            scene_id: ID of the scene
            limit: Maximum number of poses to return
            include_ooc: Whether to include out-of-character poses
            
        Returns:
            List of pose dictionaries
            
        Raises:
            ValueError: If scene not found
        """
        self.logger.info(f"Reading poses from scene {scene_id}")
        
        # This is a read operation, so we don't need to debounce
        return self.scene_management_service.get_scene_history(
            scene_id=scene_id,
            limit=limit,
            include_ooc=include_ooc
        )
    
    def update_pose(
        self,
        scene_id: str,
        pose_id: str,
        content: Optional[str] = None,
        pose_type: Optional[PoseType] = None,
        is_ooc: Optional[bool] = None,
        analysis_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing pose with debounced saving.
        
        Args:
            scene_id: ID of the scene containing the pose
            pose_id: ID of the pose to update
            content: New text content (if changing)
            pose_type: New pose type (if changing)
            is_ooc: New OOC status (if changing)
            analysis_data: New analysis data (if changing)
            
        Returns:
            True if the update was scheduled successfully
            
        Raises:
            ValueError: If pose not found or invalid parameters
        """
        self.logger.info(f"Updating pose {pose_id} in scene {scene_id}")
        
        # Find the pose to verify it exists
        pose = Pose.find_by_id(pose_id)
        if not pose:
            raise ValueError(f"Pose {pose_id} not found")
        
        # Make sure the pose belongs to the specified scene
        if pose.scene_id != scene_id:
            raise ValueError(f"Pose {pose_id} does not belong to scene {scene_id}")
        
        # Create update data dictionary with only the fields that are changing
        update_data = {}
        if content is not None:
            update_data['content'] = content
        if pose_type is not None:
            update_data['pose_type'] = pose_type if isinstance(pose_type, str) else pose_type.value
        if is_ooc is not None:
            update_data['is_ooc'] = is_ooc
        if analysis_data is not None:
            update_data['analysis_data'] = analysis_data
        
        # Schedule the update operation with debounce
        self._schedule_debounced_operation(
            scene_id=scene_id,
            operation_key=f"update_{pose_id}",
            operation=lambda: self._update_pose_impl(pose_id, update_data),
            operation_type="update"
        )
        
        return True
    
    def delete_pose(self, scene_id: str, pose_id: str) -> bool:
        """
        Delete a pose from a scene with debounced saving.
        
        Args:
            scene_id: ID of the scene containing the pose
            pose_id: ID of the pose to delete
            
        Returns:
            True if the deletion was scheduled successfully
            
        Raises:
            ValueError: If pose not found or invalid parameters
        """
        self.logger.info(f"Deleting pose {pose_id} from scene {scene_id}")
        
        # Find the pose to verify it exists
        pose = Pose.find_by_id(pose_id)
        if not pose:
            self.logger.error(f"Pose {pose_id} not found during delete verification")
            raise ValueError(f"Pose {pose_id} not found")
        
        # Make sure the pose belongs to the specified scene
        if pose.scene_id != scene_id:
            self.logger.error(f"Pose {pose_id} does not belong to scene {scene_id}")
            raise ValueError(f"Pose {pose_id} does not belong to scene {scene_id}")
        
        self.logger.info(f"Scheduling debounced deletion for pose {pose_id} in scene {scene_id}")
        # Schedule the delete operation with debounce
        self._schedule_debounced_operation(
            scene_id=scene_id,
            operation_key=f"delete_{pose_id}",
            operation=lambda: self._delete_pose_impl(pose_id),
            operation_type="delete"
        )
        
        return True
    
    def _update_pose_impl(self, pose_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Implementation of pose update operation.
        
        Args:
            pose_id: ID of the pose to update
            update_data: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pose = Pose.find_by_id(pose_id)
            if not pose:
                self.logger.warning(f"Pose {pose_id} not found during update implementation")
                return False
            
            # Update the pose fields
            for key, value in update_data.items():
                setattr(pose, key, value)
            
            # Update timestamp
            pose.updated_at = datetime.utcnow()
            
            # Save the updated pose
            pose.save()
            self.logger.info(f"Updated pose {pose_id} successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error updating pose {pose_id}: {e}")
            return False
    
    def _delete_pose_impl(self, pose_id: str) -> bool:
        """
        Implementation of pose deletion operation.
        
        Args:
            pose_id: ID of the pose to delete
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Executing deletion implementation for pose {pose_id}")
        try:
            pose = Pose.find_by_id(pose_id)
            if not pose:
                self.logger.warning(f"Pose {pose_id} not found during delete implementation")
                return False
            
            # Store scene_id before deletion for reference
            scene_id = pose.scene_id
            
            # Delete the pose
            self.logger.info(f"Calling delete() on pose {pose_id}")
            result = pose.delete()
            self.logger.info(f"Delete operation result: {result}")
            
            # Update scene metadata (pose count)
            scene = SceneMemory.find_by_id(scene_id)
            if scene and scene.pose_count > 0:
                scene.pose_count -= 1
                self.logger.info(f"Updating scene {scene_id} pose count to {scene.pose_count}")
                scene.save()
            else:
                self.logger.warning(f"Scene {scene_id} not found or pose count already 0")
            
            self.logger.info(f"Deleted pose {pose_id} from scene {scene_id} successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting pose {pose_id}: {e}")
            return False
    
    def _schedule_debounced_operation(
        self,
        scene_id: str,
        operation_key: str,
        operation: Callable[[], Any],
        operation_type: str
    ):
        """
        Schedule a debounced operation.
        
        Args:
            scene_id: ID of the scene for the operation
            operation_key: Unique key for the operation
            operation: Function to call for the operation
            operation_type: Type of operation (create/update/delete)
        """
        # For deletion operations, execute immediately without debounce
        # This ensures pose deletions happen right away and aren't lost
        if operation_type == "delete":
            self.logger.info(f"Executing delete operation {operation_key} immediately")
            try:
                result = operation()
                self.logger.info(f"Immediate delete operation result: {result}")
                return
            except Exception as e:
                self.logger.error(f"Error executing immediate delete operation: {e}")
                return
        
        # For non-delete operations, use the debounce system as before
        # Ensure scene_id is in the pending changes dictionary
        if scene_id not in self._pending_changes:
            self._pending_changes[scene_id] = {}
        
        # Store the operation in pending changes
        self._pending_changes[scene_id][operation_key] = {
            'operation': operation,
            'type': operation_type,
            'timestamp': time.time()
        }
        
        # Cancel any existing timer for this scene
        if scene_id in self._save_timers and self._save_timers[scene_id] is not None:
            try:
                self._save_timers[scene_id].cancel()
            except Exception:
                pass
        
        # Create a new timer
        timer = threading.Timer(
            self.debounce_time,
            self._execute_debounced_operations,
            args=[scene_id]
        )
        timer.daemon = False  # Change to non-daemon to ensure it completes
        self._save_timers[scene_id] = timer
        timer.start()
    
    def _execute_debounced_operations(self, scene_id: str):
        """
        Execute all pending operations for a scene after debounce period.
        
        Args:
            scene_id: ID of the scene
        """
        try:
            self.logger.info(f"Executing debounced operations for scene {scene_id}")
            
            if scene_id not in self._pending_changes:
                return
            
            # Get the pending operations for this scene
            operations = self._pending_changes[scene_id]
            
            # Clear pending operations before executing them
            self._pending_changes[scene_id] = {}
            
            # Execute operations in order: creates first, then updates, then deletes
            for operation_type in ["create", "update", "delete"]:
                for key, operation_data in operations.items():
                    if operation_data['type'] == operation_type:
                        try:
                            result = operation_data['operation']()
                            self.logger.info(f"Executed {operation_type} operation {key} with result: {result}")
                        except Exception as e:
                            self.logger.error(f"Error executing {operation_type} operation {key}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error executing debounced operations for scene {scene_id}: {e}")
        finally:
            # Clean up the timer
            if scene_id in self._save_timers:
                self._save_timers[scene_id] = None
