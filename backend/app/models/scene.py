"""
Scene model for roleplay scenes.
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from bson import ObjectId
from .base_model import BaseModel

class PoseType(str, Enum):
    """Types of poses in a scene."""
    ACTION = "action"           # Character actions and movements
    DIALOGUE = "dialogue"       # Character speech
    NARRATIVE = "narrative"     # Scene setting and description
    INTERNAL = "internal"       # Character thoughts/internal monologue
    MIXED = "mixed"            # Combination of types

class ScenePose:
    """A single pose within a scene."""
    
    def __init__(
        self,
        character_id: str,
        character_name: str,
        pose_text: str,
        pose_type: Union[PoseType, str],
        timestamp: Optional[datetime] = None,
        enhanced_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
        **kwargs
    ):
        self.id = kwargs.get('id')
        self.character_id = character_id
        self.character_name = character_name
        self.pose_text = pose_text
        self.pose_type = PoseType(pose_type) if isinstance(pose_type, str) else pose_type
        self.timestamp = timestamp or datetime.utcnow()
        self.enhanced_text = enhanced_text
        self.tags = tags or []
        self.mentions = mentions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB."""
        return {
            'id': self.id,
            'character_id': self.character_id,
            'character_name': self.character_name,
            'pose_text': self.pose_text,
            'pose_type': self.pose_type.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'enhanced_text': self.enhanced_text,
            'tags': self.tags,
            'mentions': self.mentions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScenePose':
        """Create from dictionary."""
        if not data:
            return None
            
        # Convert string timestamp to datetime
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            
        return cls(**data)


class SceneParticipant:
    """A character participating in a scene."""
    
    def __init__(
        self,
        character_id: str,
        character_name: str,
        last_pose_id: Optional[str] = None,
        pose_count: int = 0,
        first_seen: Optional[datetime] = None,
        last_seen: Optional[datetime] = None,
        **kwargs
    ):
        self.character_id = character_id
        self.character_name = character_name
        self.last_pose_id = last_pose_id
        self.pose_count = pose_count
        self.first_seen = first_seen or datetime.utcnow()
        self.last_seen = last_seen or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB."""
        return {
            'character_id': self.character_id,
            'character_name': self.character_name,
            'last_pose_id': self.last_pose_id,
            'pose_count': self.pose_count,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneParticipant':
        """Create from dictionary."""
        if not data:
            return None
            
        # Convert string timestamps to datetime
        for time_field in ['first_seen', 'last_seen']:
            if time_field in data and data[time_field] and isinstance(data[time_field], str):
                data[time_field] = datetime.fromisoformat(data[time_field])
                
        return cls(**data)


class SceneContext:
    """Contextual information for a scene."""
    
    def __init__(
        self,
        setting: str = "",
        mood: str = "",
        active_characters: Optional[List[str]] = None,
        recent_events: Optional[List[str]] = None,
        emotional_tone: str = "",
        time_of_day: str = "",
        location_details: Optional[List[str]] = None,
        relationship_dynamics: Optional[Dict[str, str]] = None,
        poses: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        self.setting = setting
        self.mood = mood
        self.active_characters = active_characters or []
        self.recent_events = recent_events or []
        self.emotional_tone = emotional_tone
        self.time_of_day = time_of_day
        self.location_details = location_details or []
        self.relationship_dynamics = relationship_dynamics or {}
        self.poses = poses or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB."""
        return {
            'setting': self.setting,
            'mood': self.mood,
            'active_characters': self.active_characters,
            'recent_events': self.recent_events,
            'emotional_tone': self.emotional_tone,
            'time_of_day': self.time_of_day,
            'location_details': self.location_details,
            'relationship_dynamics': self.relationship_dynamics,
            'poses': self.poses
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneContext':
        """Create from dictionary."""
        if not data:
            return cls()
        return cls(**data)


class Scene(BaseModel):
    """Scene model for roleplay scenes."""
    
    COLLECTION_NAME = 'scenes'
    
    def __init__(
        self,
        name: str,
        created_by: str,  # User ID
        description: str = "",
        is_active: bool = True,
        max_poses: int = 100,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.name = name
        self.description = description
        self.created_by = created_by
        self.is_active = is_active
        self.max_poses = max_poses
        
        # Initialize collections
        self.poses: List[ScenePose] = [
            ScenePose.from_dict(pose) 
            for pose in kwargs.get('poses', [])
        ]
        
        self.participants: Dict[str, SceneParticipant] = {
            p['character_id']: SceneParticipant.from_dict(p)
            for p in kwargs.get('participants', [])
        }
        
        context_data = kwargs.get('context', {})
        if 'active_characters' not in context_data:
            context_data['active_characters'] = [p.character_id for p in self.participants.values()]
        self.context = SceneContext.from_dict(context_data)
        self.compressed_history = kwargs.get('compressed_history', "")
    
    def add_pose(self, pose: ScenePose) -> None:
        """Add a new pose to the scene."""
        # Add pose
        pose.id = str(ObjectId())
        self.poses.append(pose)
        
        # Update participant info
        if pose.character_id not in self.participants:
            self.participants[pose.character_id] = SceneParticipant(
                character_id=pose.character_id,
                character_name=pose.character_name
            )
        
        participant = self.participants[pose.character_id]
        participant.last_pose_id = pose.id
        participant.pose_count += 1
        participant.last_seen = datetime.utcnow()
        
        # Update context
        self._update_context(pose)
        
        # Compress history if needed
        if len(self.poses) > self.max_poses * 1.5:  # 1.5x buffer
            self._compress_history()
    
    def _update_context(self, pose: ScenePose) -> None:
        """Update scene context based on new pose."""
        # Add character to active characters if not already present
        if pose.character_name not in self.context.active_characters:
            self.context.active_characters.append(pose.character_name)
        
        # Update last seen time for active characters
        # (In a real implementation, you might want to track last activity)
    
    def _compress_history(self) -> None:
        """Compress older poses to save space."""
        # Keep recent poses (last max_poses)
        recent_poses = self.poses[-self.max_poses:]
        
        # Create summary of older poses
        old_poses = self.poses[:-self.max_poses]
        if old_poses:
            summary = self._create_compressed_summary(old_poses)
            self.compressed_history = (self.compressed_history + "\n\n" + summary).strip()
        
        # Update poses to keep only recent ones
        self.poses = recent_poses
    
    def _create_compressed_summary(self, poses: List[ScenePose]) -> str:
        """Create a compressed summary of poses."""
        # In a real implementation, you might use an LLM to summarize
        summary = []
        current_character = None
        current_poses = []
        
        for pose in poses:
            if pose.character_name != current_character:
                if current_character and current_poses:
                    summary.append(f"{current_character}: {' '.join(current_poses)}")
                current_character = pose.character_name
                current_poses = []
            current_poses.append(pose.pose_text)
        
        if current_character and current_poses:
            summary.append(f"{current_character}: {' '.join(current_poses)}")
        
        return "\n".join(summary)
    
    def get_recent_poses(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent poses."""
        return [pose.to_dict() for pose in self.poses[-count:]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB."""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'created_by': str(self.created_by) if self.created_by else None,
            'is_active': self.is_active,
            'max_poses': self.max_poses,
            'poses': [pose.to_dict() for pose in self.poses],
            'participants': [p.to_dict() for p in self.participants.values()],
            'context': self.context.to_dict(),
            'compressed_history': self.compressed_history
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scene':
        """Create from dictionary."""
        if not data:
            return None
            
        # Make a copy to avoid modifying the original
        data_copy = data.copy()
            
        # Convert ObjectId to string for created_by
        if 'created_by' in data_copy and isinstance(data_copy['created_by'], ObjectId):
            data_copy['created_by'] = str(data_copy['created_by'])
            
        return cls(**data_copy)
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for scenes."""
        from ..services.mongodb_service import get_mongodb_service
        mongodb = get_mongodb_service()
        
        # Create indexes
        mongodb.create_index(cls.COLLECTION_NAME, 'created_by')
        mongodb.create_index(cls.COLLECTION_NAME, 'is_active')
        mongodb.create_index(
            cls.COLLECTION_NAME,
            [('created_by', 1), ('name', 1)],
            unique=True
        )
        mongodb.create_index(
            cls.COLLECTION_NAME,
            'participants.character_id'
        )
