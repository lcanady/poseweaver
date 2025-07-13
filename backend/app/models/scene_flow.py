"""
Scene flow models for tracking pose conversation history.

This module provides data structures for managing ongoing roleplay scenes,
tracking pose history, participants, and contextual information that builds
over the course of a scene.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class PoseType(Enum):
    """Types of poses in a scene."""
    ACTION = "action"           # Character actions and movements
    DIALOGUE = "dialogue"       # Character speech
    NARRATIVE = "narrative"     # Scene setting and description
    INTERNAL = "internal"       # Character thoughts/internal monologue
    MIXED = "mixed"            # Combination of types


@dataclass
class ScenePose:
    """A single pose within a scene flow."""
    id: str
    character_name: str
    pose_text: str
    pose_type: PoseType
    timestamp: datetime
    enhanced_text: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)  # Other characters mentioned
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['pose_type'] = self.pose_type.value
        return data


@dataclass
class SceneParticipant:
    """A character participating in the scene."""
    name: str
    last_pose_id: Optional[str] = None
    pose_count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.first_seen:
            data['first_seen'] = self.first_seen.isoformat()
        if self.last_seen:
            data['last_seen'] = self.last_seen.isoformat()
        return data


@dataclass
class SceneContext:
    """Contextual information extracted from scene history."""
    setting: str = ""
    mood: str = ""
    active_characters: List[str] = field(default_factory=list)
    recent_events: List[str] = field(default_factory=list)
    emotional_tone: str = ""
    time_of_day: str = ""
    location_details: List[str] = field(default_factory=list)
    relationship_dynamics: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class SceneFlow:
    """Manages the flow of poses in a roleplay scene."""
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    poses: List[ScenePose] = field(default_factory=list)
    participants: Dict[str, SceneParticipant] = field(default_factory=dict)
    context: SceneContext = field(default_factory=SceneContext)
    max_poses: int = 50  # Maximum poses before compression
    compressed_history: str = ""  # Compressed older poses
    is_active: bool = True
    
    def add_pose(self, pose: ScenePose) -> None:
        """Add a new pose to the scene flow."""
        self.poses.append(pose)
        self.updated_at = datetime.now()
        
        # Update participant tracking
        if pose.character_name not in self.participants:
            self.participants[pose.character_name] = SceneParticipant(
                name=pose.character_name,
                first_seen=pose.timestamp
            )
        
        participant = self.participants[pose.character_name]
        participant.last_pose_id = pose.id
        participant.pose_count += 1
        participant.last_seen = pose.timestamp
        
        # Check if compression is needed
        if len(self.poses) > self.max_poses:
            self._compress_history()
    
    def _compress_history(self) -> None:
        """Compress older poses when history gets too long."""
        # Keep the most recent 20 poses, compress the rest
        poses_to_compress = self.poses[:-20]
        self.poses = self.poses[-20:]
        
        # Create compressed summary
        if poses_to_compress:
            compressed_text = self._create_compressed_summary(poses_to_compress)
            if self.compressed_history:
                self.compressed_history += "\n\n" + compressed_text
            else:
                self.compressed_history = compressed_text
    
    def _create_compressed_summary(self, poses: List[ScenePose]) -> str:
        """Create a compressed summary of poses."""
        # Group poses by character and type
        character_actions = {}
        key_events = []
        
        for pose in poses:
            char = pose.character_name
            if char not in character_actions:
                character_actions[char] = []
            
            # Summarize the pose (first 100 characters)
            summary = pose.pose_text[:100] + "..." if len(pose.pose_text) > 100 else pose.pose_text
            character_actions[char].append(summary)
            
            # Track key events (dialogue, major actions)
            if pose.pose_type in [PoseType.DIALOGUE, PoseType.ACTION]:
                key_events.append(f"{char}: {summary}")
        
        # Create compressed narrative
        compressed = f"Earlier in the scene ({len(poses)} poses):\n"
        for char, actions in character_actions.items():
            compressed += f"- {char}: {len(actions)} poses\n"
        
        if key_events:
            compressed += "\nKey events:\n"
            for event in key_events[-5:]:  # Last 5 key events
                compressed += f"- {event}\n"
        
        return compressed.strip()
    
    def get_recent_context(self, num_poses: int = 10) -> List[ScenePose]:
        """Get the most recent poses for context."""
        return self.poses[-num_poses:] if self.poses else []
    
    def get_character_history(self, character_name: str, num_poses: int = 5) -> List[ScenePose]:
        """Get recent poses from a specific character."""
        character_poses = [p for p in self.poses if p.character_name == character_name]
        return character_poses[-num_poses:] if character_poses else []
    
    def get_full_context_text(self) -> str:
        """Get full context including compressed history and recent poses."""
        context_parts = []
        
        # Add compressed history
        if self.compressed_history:
            context_parts.append("SCENE BACKGROUND:")
            context_parts.append(self.compressed_history)
            context_parts.append("")
        
        # Add recent poses
        if self.poses:
            context_parts.append("RECENT POSES:")
            for pose in self.poses[-10:]:  # Last 10 poses
                timestamp = pose.timestamp.strftime("%H:%M")
                context_parts.append(f"[{timestamp}] {pose.character_name}: {pose.pose_text}")
            context_parts.append("")
        
        # Add scene context
        if self.context.setting or self.context.mood:
            context_parts.append("SCENE CONTEXT:")
            if self.context.setting:
                context_parts.append(f"Setting: {self.context.setting}")
            if self.context.mood:
                context_parts.append(f"Mood: {self.context.mood}")
            if self.context.active_characters:
                context_parts.append(f"Active characters: {', '.join(self.context.active_characters)}")
        
        return "\n".join(context_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'poses': [pose.to_dict() for pose in self.poses],
            'participants': {name: participant.to_dict() for name, participant in self.participants.items()},
            'context': self.context.to_dict(),
            'max_poses': self.max_poses,
            'compressed_history': self.compressed_history,
            'is_active': self.is_active
        } 