"""
Scene Invite model for invitation system.
"""
from typing import Optional, Dict, Any
from datetime import datetime, UTC, timedelta
from enum import Enum
from .base_model import BaseModel


class InviteStatus(str, Enum):
    """Status of a scene invitation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class SceneRole(str, Enum):
    """Roles for scene permissions."""
    OWNER = "owner"           # Full control, can delete scene
    CO_AUTHOR = "co-author"   # Can add poses, manage participants
    PARTICIPANT = "participant"  # Can only add poses
    VIEWER = "viewer"         # Read-only access


class SceneInvite(BaseModel):
    """Scene invitation model."""
    
    COLLECTION_NAME = 'scene_invites'
    
    def __init__(
        self,
        scene_id: str,
        invited_by_user_id: str,
        invited_user_email: str,
        role: SceneRole,
        invite_code: str,
        status: InviteStatus = InviteStatus.PENDING,
        expires_at: Optional[datetime] = None,
        accepted_at: Optional[datetime] = None,
        message: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.scene_id = scene_id
        self.invited_by_user_id = invited_by_user_id
        self.invited_user_email = invited_user_email
        self.role = SceneRole(role) if isinstance(role, str) else role
        self.invite_code = invite_code
        self.status = InviteStatus(status) if isinstance(status, str) else status
        self.expires_at = expires_at or (datetime.now(UTC) + timedelta(days=7))
        self.accepted_at = accepted_at
        self.message = message
    
    def is_expired(self) -> bool:
        """Check if the invite has expired."""
        return datetime.now(UTC) > self.expires_at
    
    def can_accept(self) -> bool:
        """Check if the invite can be accepted."""
        return self.status == InviteStatus.PENDING and not self.is_expired()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Database."""
        data = super().to_dict()
        data.update({
            'scene_id': self.scene_id,
            'invited_by_user_id': self.invited_by_user_id,
            'invited_user_email': self.invited_user_email,
            'role': self.role.value,
            'invite_code': self.invite_code,
            'status': self.status.value,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'message': self.message
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneInvite':
        """Create from dictionary."""
        if not data:
            return None
            
        # Convert string dates to datetime
        for field in ['expires_at', 'accepted_at']:
            if field in data and data[field] and isinstance(data[field], str):
                try:
                    dt = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)
                    data[field] = dt
                except ValueError:
                    data[field] = None
        
        return cls(**data)
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for scene invites."""
        from ..extensions import get_db
        db = get_db()
        
        # Create indexes
        db.create_index(cls.COLLECTION_NAME, 'scene_id')
        db.create_index(cls.COLLECTION_NAME, 'invited_user_email')
        db.create_index(cls.COLLECTION_NAME, 'invite_code', unique=True)
        db.create_index(cls.COLLECTION_NAME, 'status')
        db.create_index(
            cls.COLLECTION_NAME,
            [('invited_user_email', 1), ('status', 1)]
        )
