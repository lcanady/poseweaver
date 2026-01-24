"""
Scene management service for MongoDB operations.
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, UTC
from ..models.scene import Scene, ScenePose, SceneParticipant, PoseType, SceneHistoryLogEntry
from ..models.character import Character
import os


class SceneService:
    """Service for managing scene data in MongoDB."""
    
    @staticmethod
    def create_scene(
        name: str,
        created_by: str,
        description: str = "",
        max_poses: int = 100,
        initial_participants: Optional[List[str]] = None,
        initial_context: Optional[Dict[str, Any]] = None,
        initial_history_log: Optional[List[Dict[str, Any]]] = None
    ) -> Scene:
        """Create a new scene.
        
        Args:
            name: Name of the scene
            created_by: ID of the user creating the scene
            description: Optional scene description
            max_poses: Maximum number of poses to keep in memory
            initial_participants: Optional list of character IDs to add as participants
            initial_context: Optional initial context data
            initial_history_log: Optional initial history log entries
            
        Returns:
            The created Scene instance
            
        Raises:
            ValueError: If a scene with the same name already exists for the user
        """
        # Check for existing scene with the same name for this user
        existing = Scene.find_all(query={
            'name': name,
            'created_by': created_by,
            'is_active': True
        }, limit=1)
        
        if existing:
            raise ValueError(
                f"A scene named '{name}' already exists for this user"
            )
        
        # Prepare participants data
        participants_data = []
        if initial_participants:
            for char_id in initial_participants:
                character = Character.find_by_id(char_id)
                if character and character.user_id == created_by:
                    participants_data.append({
                        'character_id': char_id,
                        'character_name': character.name
                    })

        # Create and save the scene
        scene = Scene(
            name=name,
            created_by=created_by,
            description=description,
            max_poses=max_poses,
            participants=participants_data,
            context=initial_context or {},
            history_log=initial_history_log or []
        )
        
        # If poses are in the initial context, add them to the main poses array
        if initial_context and 'poses' in initial_context:
            for pose_data in initial_context['poses']:
                if isinstance(pose_data, dict):
                    try:
                        pose = ScenePose(
                            character_id=pose_data.get('character_id', ''),
                            character_name=pose_data.get('character_name', ''),
                            pose_text=pose_data.get('content', 
                                                   pose_data.get('pose_text', '')),
                            pose_type=PoseType(pose_data.get('pose_type', 'action')),
                            enhanced_text=pose_data.get('enhanced_text'),
                            tags=pose_data.get('tags', []),
                            mentions=pose_data.get('mentions', [])
                        )
                        scene.add_pose(pose)
                    except (ValueError, TypeError):
                        # Skip invalid pose data
                        continue
        
        scene.save()
        
        return scene
    
    @staticmethod
    def get_scene(scene_id: str, user_id: Optional[str] = None) -> Optional[Scene]:
        """Get a scene by ID.
        
        Args:
            scene_id: ID of the scene to retrieve
            user_id: Optional user ID to verify ownership
            
        Returns:
            The Scene instance, or None if not found or access denied
        """
        scene = Scene.find_by_id(scene_id)
        if not scene:
            return None
            
        # If user_id is provided, verify ownership
        if user_id and scene.created_by != user_id:
            return None
            
        return scene
    
    @staticmethod
    def list_scenes(
        user_id: str,
        include_inactive: bool = False,
        limit: int = 100,
        skip: int = 0,
        sort_field: str = "updated_at",
        sort_direction: int = -1
    ) -> List[Scene]:
        """List scenes for a user.
        
        Args:
            user_id: ID of the user whose scenes to list
            include_inactive: Whether to include inactive scenes
            limit: Maximum number of scenes to return
            skip: Number of scenes to skip (for pagination)
            sort_field: Field to sort by
            sort_direction: Sort direction (1 for ascending, -1 for descending)
            
        Returns:
            List of Scene instances
        """
        query = {'created_by': user_id}
        if not include_inactive:
            query['is_active'] = True
            
        # Convert sort parameters to MongoDB sort format
        sort = [(sort_field, sort_direction)]
        
        return Scene.find_all(
            query=query,
            limit=limit,
            skip=skip,
            sort=sort
        )
    
    @staticmethod
    def add_pose(
        scene_id: str,
        character_id: str,
        character_name: str,
        pose_text: str,
        pose_type: PoseType = PoseType.ACTION,
        enhanced_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None
    ) -> Optional[Tuple[Scene, ScenePose]]:
        """Add a pose to a scene.
        
        Args:
            scene_id: ID of the scene to add the pose to
            character_id: ID of the character making the pose
            character_name: Name of the character making the pose
            pose_text: The text of the pose
            pose_type: Type of pose (action, dialogue, etc.)
            enhanced_text: Optional enhanced/processed version of the pose
            tags: Optional list of tags for the pose
            mentions: Optional list of character IDs mentioned in the pose
            
        Returns:
            Tuple of (updated Scene, new ScenePose) if successful, or None if failed
        """
        scene = Scene.find_by_id(scene_id)
        if not scene:
            return None
        
        # Create the pose
        pose = ScenePose(
            character_id=character_id,
            character_name=character_name,
            pose_text=pose_text,
            pose_type=pose_type,
            enhanced_text=enhanced_text,
            tags=tags or [],
            mentions=mentions or []
        )
        
        # Add the pose to the scene
        scene.add_pose(pose)
        
        # Ensure updated_at is set when a pose is added
        scene.updated_at = datetime.utcnow()
        scene.save()
        
        return scene, pose
    
    @staticmethod
    def get_recent_poses(
        scene_id: str,
        user_id: str,
        limit: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """Get recent poses from a scene.
        
        Args:
            scene_id: ID of the scene
            user_id: ID of the user making the request
            limit: Maximum number of poses to return
            
        Returns:
            List of pose dictionaries, or None if scene not found or access denied
        """
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return None
        
        # Get poses from the scene's poses array
        poses = scene.get_recent_poses(limit)
        
        # If no poses in the main array, check if poses are stored in context
        if not poses and hasattr(scene.context, 'poses'):
            context_poses = getattr(scene.context, 'poses', [])
            if context_poses:
                # Convert context poses to the expected format
                converted_poses = []
                for pose in context_poses[-limit:]:  # Get the most recent ones
                    if isinstance(pose, dict):
                        # Convert from context format to scene pose format
                        converted_poses.append({
                            'id': pose.get('id', ''),
                            'character_id': pose.get('character_id', ''),
                            'character_name': pose.get('character_name', ''),
                            'pose_text': pose.get('content', pose.get('pose_text', '')),
                            'pose_type': pose.get('pose_type', 'action'),
                            'timestamp': pose.get('timestamp', ''),
                            'created_at': pose.get('timestamp', ''),
                            'enhanced_text': pose.get('enhanced_text', ''),
                            'tags': pose.get('tags', []),
                            'mentions': pose.get('mentions', [])
                        })
                return converted_poses
        
        # Also check if poses are stored in scene.context as a dict with 'poses' key
        if not poses and hasattr(scene, 'context') and hasattr(scene.context, 'to_dict'):
            context_dict = scene.context.to_dict()
            if 'poses' in context_dict and context_dict['poses']:
                context_poses = context_dict['poses']
                converted_poses = []
                for pose in context_poses[-limit:]:  # Get the most recent ones
                    if isinstance(pose, dict):
                        converted_poses.append({
                            'id': pose.get('id', ''),
                            'character_id': pose.get('character_id', ''),
                            'character_name': pose.get('character_name', ''),
                            'pose_text': pose.get('content', pose.get('pose_text', '')),
                            'pose_type': pose.get('pose_type', 'action'),
                            'timestamp': pose.get('timestamp', ''),
                            'created_at': pose.get('timestamp', ''),
                            'enhanced_text': pose.get('enhanced_text', ''),
                            'tags': pose.get('tags', []),
                            'mentions': pose.get('mentions', [])
                        })
                return converted_poses
            
        return poses
    
    @staticmethod
    def update_scene_context(
        scene_id: str,
        user_id: str,
        **updates
    ) -> Optional[Scene]:
        """Update a scene's context.
        
        Args:
            scene_id: ID of the scene to update
            user_id: ID of the user making the update
            **updates: Fields to update in the scene context
            
        Returns:
            The updated Scene instance, or None if not found or access denied
        """
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return None
            
        # Capture context before update for narrative logging
        before_context = scene.context.to_dict()
            
        # Update context fields
        for key, value in updates.items():
            if hasattr(scene.context, key):
                setattr(scene.context, key, value)
        
        # Generate and add narrative log entry
        try:
            from .context_service import ContextService
            from .ai_client import AIClient
            api_key = os.getenv('OPENROUTER_API_KEY')
            if api_key:
                ai_client = AIClient(api_key=api_key)
                context_service = ContextService(ai_client)
                after_context = scene.context.to_dict()
                narrative = context_service.generate_narrative_log_entry(
                    before_context, after_context
                )
                scene.add_history_log_entry(SceneHistoryLogEntry(event_description=narrative))
        except Exception as e:
            # Don't let logging failure break the main update
            print(f"Narrative logging failed: {str(e)}")
        
        scene.save()
        return scene
    
    @staticmethod
    def update_scene(scene_id: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Scene]:
        """Update an existing scene.
        
        Args:
            scene_id: ID of the scene to update
            user_id: ID of the user making the update
            update_data: Dictionary containing fields to update
            
        Returns:
            The updated Scene instance, or None if not found or access denied
        """
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return None
            
        # Update scene fields
        if 'name' in update_data:
            scene.name = update_data['name']
        if 'description' in update_data:
            scene.description = update_data['description']
        if 'context' in update_data:
            # Update the scene context with the provided data
            context_data = update_data['context']
            for key, value in context_data.items():
                if hasattr(scene.context, key):
                    setattr(scene.context, key, value)
            
            # If poses are in the context, add them to the main poses array
            if 'poses' in context_data and context_data['poses']:
                for pose_data in context_data['poses']:
                    if isinstance(pose_data, dict):
                        # Create a ScenePose object and add it to the scene
                        try:
                            pose = ScenePose(
                                character_id=pose_data.get('character_id', ''),
                                character_name=pose_data.get('character_name', ''),
                                pose_text=pose_data.get('content', 
                                                       pose_data.get('pose_text', '')),
                                pose_type=PoseType(pose_data.get('pose_type', 'action')),
                                enhanced_text=pose_data.get('enhanced_text'),
                                tags=pose_data.get('tags', []),
                                mentions=pose_data.get('mentions', [])
                            )
                            # Only add if not already in poses array
                            existing_texts = [p.pose_text for p in scene.poses]
                            if pose.pose_text not in existing_texts:
                                scene.add_pose(pose)
                        except (ValueError, TypeError):
                            # Skip invalid pose data
                            continue
            
        # Ensure updated_at is properly set before saving
        scene.updated_at = datetime.utcnow()
        scene.save()
        return scene
        
    @staticmethod
    def delete_scene(scene_id: str, user_id: str) -> bool:
        """Delete a scene (soft delete).
        
        Args:
            scene_id: ID of the scene to delete
            user_id: ID of the user making the request
            
        Returns:
            True if deleted, False if not found or access denied
        """
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return False
            
        # Soft delete by marking as inactive
        scene.is_active = False
        scene.save()
        return True
    
    @staticmethod
    def add_participant(
        scene_id: str,
        user_id: str,
        character_id: str
    ) -> Optional[Scene]:
        """Add a participant to a scene.
        
        Args:
            scene_id: ID of the scene
            user_id: ID of the user making the request
            character_id: ID of the character to add
            
        Returns:
            The updated Scene instance, or None if not found or access denied
        """
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return None
            
        # Verify the character exists and belongs to the user
        character = Character.find_by_id(character_id)
        if not character or character.user_id != user_id:
            return None
            
        # Add participant if not already in the scene
        if character_id not in scene.participants:
            participant = SceneParticipant(
                character_id=character_id,
                character_name=character.name
            )
            scene.participants[character_id] = participant
            scene.save()
            
        return scene
    
    @staticmethod
    def remove_participant(
        scene_id: str,
        user_id: str,
        character_id: str
    ) -> Optional[Scene]:
        """Remove a participant from a scene.
        
        Args:
            scene_id: ID of the scene
            user_id: ID of the user making the request
            character_id: ID of the character to remove
            
        Returns:
            The updated Scene instance, or None if not found or access denied
        """
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return None
            
        # Remove participant if they exist in the scene
        if character_id in scene.participants:
            del scene.participants[character_id]
            scene.save()
            
        return scene

    @staticmethod
    def save_scene_with_context(
        scene_id: str,
        user_id: str,
        scene_context: Dict[str, Any]
    ) -> Optional[Scene]:
        """Save a scene with updated scene context.
        
        This method ensures scene context is saved when a scene is saved.
        
        Args:
            scene_id: ID of the scene to update
            user_id: ID of the user making the request
            scene_context: Dictionary containing scene context data
            
        Returns:
            The updated Scene instance, or None if not found or access denied
        """
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return None
            
        # Capture context before update for narrative logging
        before_context = scene.context.to_dict()
            
        # Update scene context with provided data
        # For each key in scene_context, update corresponding field in context
        for key, value in scene_context.items():
            if hasattr(scene.context, key):
                setattr(scene.context, key, value)
        
        # If poses are in the context, also add them to the main poses array
        if 'poses' in scene_context and scene_context['poses']:
            for pose_data in scene_context['poses']:
                if isinstance(pose_data, dict):
                    # Create a ScenePose object and add it to the scene
                    pose = ScenePose(
                        character_id=pose_data.get('character_id', ''),
                        character_name=pose_data.get('character_name', ''),
                        pose_text=pose_data.get('content', 
                                               pose_data.get('pose_text', '')),
                        pose_type=PoseType(pose_data.get('pose_type', 'action')),
                        enhanced_text=pose_data.get('enhanced_text'),
                        tags=pose_data.get('tags', []),
                        mentions=pose_data.get('mentions', [])
                    )
                    # Only add if not already in poses array
                    existing_ids = [p.id for p in scene.poses if p.id]
                    if not pose.id or pose.id not in existing_ids:
                        scene.add_pose(pose)
            
        # Ensure updated_at is properly set to current time before saving
        scene.updated_at = datetime.now(UTC)
        
        # Generate and add narrative log entry
        try:
            from .context_service import ContextService
            from .ai_client import AIClient
            api_key = os.getenv('OPENROUTER_API_KEY')
            if api_key:
                ai_client = AIClient(api_key=api_key)
                context_service = ContextService(ai_client)
                after_context = scene.context.to_dict()
                narrative = context_service.generate_narrative_log_entry(
                    before_context, after_context
                )
                scene.add_history_log_entry(SceneHistoryLogEntry(event_description=narrative))
        except Exception as e:
            # Don't let logging failure break the main update
            print(f"Narrative logging failed: {str(e)}")
            
        scene.save()
        return scene
