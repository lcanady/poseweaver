"""
Scene Memory & Continuity Tracking models.

This module provides persistent storage models for scene history, character states,
environmental details, plot threads, and continuity tracking for MUSH roleplay sessions.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from bson import ObjectId
from .base_model import BaseModel


class SceneStatus(str, Enum):
    """Scene status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class PoseType(str, Enum):
    """Pose type enumeration."""
    ACTION = "action"
    DIALOGUE = "dialogue"
    NARRATIVE = "narrative"
    INTERNAL = "internal"
    MIXED = "mixed"



class PlotStatus(str, Enum):
    """Plot thread status enumeration."""
    INTRODUCED = "introduced"
    DEVELOPING = "developing"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class SceneMemory(BaseModel):
    """
    Scene model for persistent scene storage.
    
    Stores scene metadata, ownership, and activity tracking for MUSH roleplay sessions.
    Supports scene lifecycle management from creation to archival.
    """
    
    COLLECTION_NAME = 'scene_memory'
    
    def __init__(
        self,
        name: str,
        owner_id: str,
        description: str = "",
        status: Union[SceneStatus, str] = SceneStatus.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
        participant_count: int = 0,
        pose_count: int = 0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.name = name
        self.owner_id = owner_id
        self.description = description
        self.status = SceneStatus(status) if isinstance(status, str) else status
        self.last_activity = kwargs.get('last_activity', datetime.utcnow())
        self.metadata = metadata or {}
        self.participant_count = participant_count
        self.pose_count = pose_count
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'owner_id': self.owner_id,
            'description': self.description,
            'status': self.status.value,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'metadata': self.metadata,
            'participant_count': self.participant_count,
            'pose_count': self.pose_count
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneMemory':
        """Create from dictionary."""
        if not data:
            return None
            
        # Convert string timestamps to datetime
        for time_field in ['last_activity']:
            if time_field in data and data[time_field] and isinstance(data[time_field], str):
                data[time_field] = datetime.fromisoformat(data[time_field])
                
        return cls(**data)
    
    @classmethod
    def find_by_owner(cls, owner_id: str, status: Optional[SceneStatus] = None) -> List['SceneMemory']:
        """Find scenes by owner ID."""
        query = {'owner_id': owner_id}
        if status:
            query['status'] = status.value
        return cls.find_all(query=query, sort=[('last_activity', -1)])
    
    @classmethod
    def find_active_scenes(cls, limit: int = 50) -> List['SceneMemory']:
        """Find all active scenes ordered by last activity."""
        return cls.find_all(
            query={'status': SceneStatus.ACTIVE.value},
            sort=[('last_activity', -1)],
            limit=limit
        )
    
    @classmethod
    def find_scenes_for_archival(cls, days_threshold: int = 30) -> List['SceneMemory']:
        """Find scenes that should be archived due to inactivity."""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        return cls.find_all(
            query={
                'status': SceneStatus.ACTIVE.value,
                'last_activity': {'$lt': cutoff_date}
            },
            sort=[('last_activity', 1)]
        )
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for scenes."""
        from ..services.mongodb_service import get_mongodb_service
        mongodb = get_mongodb_service()
        
        # Create indexes
        mongodb.create_index(cls.COLLECTION_NAME, 'owner_id')
        mongodb.create_index(cls.COLLECTION_NAME, 'status')
        mongodb.create_index(cls.COLLECTION_NAME, 'last_activity')
        mongodb.create_index(
            cls.COLLECTION_NAME,
            [('owner_id', 1), ('status', 1)]
        )


class Pose(BaseModel):
    """
    Pose model for individual poses within scenes.
    
    Stores pose content, metadata, and analysis results for continuity tracking.
    Each pose represents a single roleplay action, dialogue, or narrative element.
    """
    
    COLLECTION_NAME = 'poses'
    
    def __init__(
        self,
        scene_id: str,
        character_name: str,
        content: str,
        pose_type: Union[PoseType, str] = PoseType.MIXED,
        timestamp: Optional[datetime] = None,
        is_ooc: bool = False,
        analysis_data: Optional[Dict[str, Any]] = None,
        word_count: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.scene_id = scene_id
        self.character_name = character_name
        self.content = content
        self.pose_type = PoseType(pose_type) if isinstance(pose_type, str) else pose_type
        self.timestamp = timestamp or datetime.utcnow()
        self.is_ooc = is_ooc
        self.analysis_data = analysis_data or {}
        self.word_count = word_count or len(content.split()) if content else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = super().to_dict()
        data.update({
            'scene_id': self.scene_id,
            'character_name': self.character_name,
            'content': self.content,
            'pose_type': self.pose_type.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_ooc': self.is_ooc,
            'analysis_data': self.analysis_data,
            'word_count': self.word_count
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pose':
        """Create from dictionary."""
        if not data:
            return None
            
        # Convert string timestamp to datetime
        if 'timestamp' in data and data['timestamp'] and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            
        return cls(**data)
    
    @classmethod
    def find_by_scene(cls, scene_id: str, limit: int = 100) -> List['Pose']:
        """Find poses by scene ID."""
        return cls.find_all(
            query={'scene_id': scene_id},
            sort=[('timestamp', 1)],
            limit=limit
        )
    
    @classmethod
    def find_by_character(cls, character_name: str, scene_id: Optional[str] = None) -> List['Pose']:
        """Find poses by character name."""
        query = {'character_name': character_name}
        if scene_id:
            query['scene_id'] = scene_id
        return cls.find_all(query=query, sort=[('timestamp', 1)])
    
    @classmethod
    def find_recent_by_scene(cls, scene_id: str, hours: int = 24, limit: int = 50) -> List['Pose']:
        """Find recent poses in a scene within the specified time window."""
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return cls.find_all(
            query={
                'scene_id': scene_id,
                'timestamp': {'$gte': cutoff_time}
            },
            sort=[('timestamp', -1)],
            limit=limit
        )
    
    @classmethod
    def search_content(cls, search_text: str, scene_id: Optional[str] = None, limit: int = 20) -> List['Pose']:
        """Search pose content using text search."""
        query = {'$text': {'$search': search_text}}
        if scene_id:
            query['scene_id'] = scene_id
        
        return cls.find_all(query=query, limit=limit)
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for poses."""
        from ..services.mongodb_service import get_mongodb_service
        mongodb = get_mongodb_service()
        
        # Create indexes
        mongodb.create_index(cls.COLLECTION_NAME, 'scene_id')
        mongodb.create_index(cls.COLLECTION_NAME, 'character_name')
        mongodb.create_index(cls.COLLECTION_NAME, 'timestamp')
        mongodb.create_index(
            cls.COLLECTION_NAME,
            [('scene_id', 1), ('timestamp', 1)]
        )
        mongodb.create_index(
            cls.COLLECTION_NAME,
            [('scene_id', 1), ('character_name', 1)]
        )


class CharacterState(BaseModel):
    """
    Character state tracking within scenes.
    
    Maintains character physical condition, emotional state, equipment, and status effects
    throughout a scene to ensure consistency in roleplay.
    """
    
    COLLECTION_NAME = 'character_states'
    
    def __init__(
        self,
        scene_id: str,
        character_name: str,
        physical_state: Optional[Dict[str, Any]] = None,
        emotional_state: Optional[Dict[str, Any]] = None,
        equipment: Optional[Dict[str, Any]] = None,
        conditions: Optional[Dict[str, Any]] = None,
        location: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.scene_id = scene_id
        self.character_name = character_name
        self.physical_state = physical_state or {}
        self.emotional_state = emotional_state or {}
        self.equipment = equipment or {}
        self.conditions = conditions or {}
        self.location = location
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = super().to_dict()
        data.update({
            'scene_id': self.scene_id,
            'character_name': self.character_name,
            'physical_state': self.physical_state,
            'emotional_state': self.emotional_state,
            'equipment': self.equipment,
            'conditions': self.conditions,
            'location': self.location
        })
        return data
    
    def update_state(self, **updates) -> None:
        """Update character state with new values."""
        for key, value in updates.items():
            if hasattr(self, key):
                if isinstance(getattr(self, key), dict) and isinstance(value, dict):
                    # Merge dictionaries for nested state objects
                    getattr(self, key).update(value)
                else:
                    setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterState':
        """Create from dictionary."""
        if not data:
            return None
        return cls(**data)
    
    @classmethod
    def find_by_scene(cls, scene_id: str) -> List['CharacterState']:
        """Find character states by scene ID."""
        return cls.find_all(query={'scene_id': scene_id})
    
    @classmethod
    def find_by_character(cls, scene_id: str, character_name: str) -> Optional['CharacterState']:
        """Find character state by scene and character name."""
        results = cls.find_all(query={'scene_id': scene_id, 'character_name': character_name})
        return results[0] if results else None
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for character states."""
        from ..services.mongodb_service import get_mongodb_service
        mongodb = get_mongodb_service()
        
        # Create indexes
        mongodb.create_index(cls.COLLECTION_NAME, 'scene_id')
        mongodb.create_index(cls.COLLECTION_NAME, 'character_name')
        mongodb.create_index(
            cls.COLLECTION_NAME,
            [('scene_id', 1), ('character_name', 1)],
            unique=True
        )


class EnvironmentState(BaseModel):
    """Environment state tracking within scenes."""
    
    COLLECTION_NAME = 'environment_states'
    
    def __init__(
        self,
        scene_id: str,
        location_name: str,
        description: str = "",
        weather: Optional[Dict[str, Any]] = None,
        time_context: Optional[Dict[str, Any]] = None,
        physical_details: Optional[Dict[str, Any]] = None,
        established_at: Optional[datetime] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.scene_id = scene_id
        self.location_name = location_name
        self.description = description
        self.weather = weather or {}
        self.time_context = time_context or {}
        self.physical_details = physical_details or {}
        self.established_at = established_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = super().to_dict()
        data.update({
            'scene_id': self.scene_id,
            'location_name': self.location_name,
            'description': self.description,
            'weather': self.weather,
            'time_context': self.time_context,
            'physical_details': self.physical_details,
            'established_at': self.established_at.isoformat() if self.established_at else None
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentState':
        """Create from dictionary."""
        if not data:
            return None
            
        # Convert string timestamp to datetime
        if 'established_at' in data and data['established_at'] and isinstance(data['established_at'], str):
            data['established_at'] = datetime.fromisoformat(data['established_at'])
            
        return cls(**data)
    
    @classmethod
    def find_by_scene(cls, scene_id: str) -> List['EnvironmentState']:
        """Find environment states by scene ID."""
        return cls.find_all(
            query={'scene_id': scene_id},
            sort=[('established_at', 1)]
        )
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for environment states."""
        from ..services.mongodb_service import get_mongodb_service
        mongodb = get_mongodb_service()
        
        # Create indexes
        mongodb.create_index(cls.COLLECTION_NAME, 'scene_id')
        mongodb.create_index(cls.COLLECTION_NAME, 'location_name')
        mongodb.create_index(cls.COLLECTION_NAME, 'established_at')


class PlotThread(BaseModel):
    """
    Plot thread tracking within scenes.
    
    Tracks ongoing story elements, plot developments, and narrative threads
    to maintain story coherence and remind players of unresolved elements.
    """
    
    COLLECTION_NAME = 'plot_threads'
    
    def __init__(
        self,
        scene_id: str,
        title: str,
        description: str = "",
        status: Union[PlotStatus, str] = PlotStatus.INTRODUCED,
        introduced_at: Optional[datetime] = None,
        last_referenced: Optional[datetime] = None,
        related_poses: Optional[List[str]] = None,
        importance_score: float = 0.5,
        resolution_notes: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.scene_id = scene_id
        self.title = title
        self.description = description
        self.status = PlotStatus(status) if isinstance(status, str) else status
        self.introduced_at = introduced_at or datetime.utcnow()
        self.last_referenced = last_referenced or datetime.utcnow()
        self.related_poses = related_poses or []
        self.importance_score = max(0.0, min(1.0, importance_score))  # Clamp between 0 and 1
        self.resolution_notes = resolution_notes
    
    def update_reference(self):
        """Update the last referenced timestamp."""
        self.last_referenced = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = super().to_dict()
        data.update({
            'scene_id': self.scene_id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'introduced_at': self.introduced_at.isoformat() if self.introduced_at else None,
            'last_referenced': self.last_referenced.isoformat() if self.last_referenced else None,
            'related_poses': self.related_poses,
            'importance_score': self.importance_score,
            'resolution_notes': self.resolution_notes
        })
        return data
    
    def add_related_pose(self, pose_id: str) -> None:
        """Add a pose ID to the related poses list."""
        if pose_id not in self.related_poses:
            self.related_poses.append(pose_id)
            self.update_reference()
    
    def resolve(self, resolution_notes: Optional[str] = None) -> None:
        """Mark the plot thread as resolved."""
        self.status = PlotStatus.RESOLVED
        if resolution_notes:
            self.resolution_notes = resolution_notes
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlotThread':
        """Create from dictionary."""
        if not data:
            return None
            
        # Convert string timestamps to datetime
        for time_field in ['introduced_at', 'last_referenced']:
            if time_field in data and data[time_field] and isinstance(data[time_field], str):
                data[time_field] = datetime.fromisoformat(data[time_field])
                
        return cls(**data)
    
    @classmethod
    def find_by_scene(cls, scene_id: str, status: Optional[PlotStatus] = None) -> List['PlotThread']:
        """Find plot threads by scene ID."""
        query = {'scene_id': scene_id}
        if status:
            query['status'] = status.value
        return cls.find_all(query=query, sort=[('last_referenced', -1)])
    
    @classmethod
    def find_stale_threads(cls, scene_id: str, days_threshold: int = 7) -> List['PlotThread']:
        """Find plot threads that haven't been referenced recently."""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        return cls.find_all(
            query={
                'scene_id': scene_id,
                'status': {'$in': [PlotStatus.INTRODUCED.value, PlotStatus.DEVELOPING.value]},
                'last_referenced': {'$lt': cutoff_date}
            },
            sort=[('importance_score', -1), ('last_referenced', 1)]
        )
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for plot threads."""
        from ..services.mongodb_service import get_mongodb_service
        mongodb = get_mongodb_service()
        
        # Create indexes
        mongodb.create_index(cls.COLLECTION_NAME, 'scene_id')
        mongodb.create_index(cls.COLLECTION_NAME, 'status')
        mongodb.create_index(cls.COLLECTION_NAME, 'last_referenced')
        mongodb.create_index(
            cls.COLLECTION_NAME,
            [('scene_id', 1), ('status', 1)]
        )

