"""
API endpoints for CRUD operations on scene poses with debounce.
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from ..models.scene_memory import PoseType
from ..services.scene_poses_crud_service import ScenePosesCrudService

router = APIRouter(prefix="/api/scenes", tags=["scene_poses"])

# Initialize service
scene_poses_service = ScenePosesCrudService()


class CreatePoseRequest(BaseModel):
    """Create pose request model."""
    character_name: str
    content: str
    pose_type: str = PoseType.MIXED.value
    is_ooc: bool = False
    analysis_data: Optional[Dict[str, Any]] = None


class UpdatePoseRequest(BaseModel):
    """Update pose request model."""
    content: Optional[str] = None
    pose_type: Optional[str] = None
    is_ooc: Optional[bool] = None
    analysis_data: Optional[Dict[str, Any]] = None


class PoseResponse(BaseModel):
    """Pose response model."""
    id: str
    scene_id: str
    character_name: str
    content: str
    pose_type: str
    is_ooc: bool
    timestamp: str
    analysis_data: Optional[Dict[str, Any]] = None
    word_count: Optional[int] = None


@router.post("/{scene_id}/poses", response_model=Dict[str, str])
async def create_pose(scene_id: str, pose_data: CreatePoseRequest):
    """
    Create a new pose in the scene with debounced saving.
    """
    try:
        pose_id = scene_poses_service.create_pose(
            scene_id=scene_id,
            character_name=pose_data.character_name,
            content=pose_data.content,
            pose_type=PoseType(pose_data.pose_type),
            is_ooc=pose_data.is_ooc,
            analysis_data=pose_data.analysis_data
        )
        return {"id": pose_id, "message": "Pose created successfully (debounced)"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create pose: {str(e)}")


@router.get("/{scene_id}/poses", response_model=List[Dict[str, Any]])
async def get_poses(
    scene_id: str,
    limit: int = Query(100, ge=1, le=1000),
    include_ooc: bool = Query(True)
):
    """
    Get all poses for a scene.
    """
    try:
        poses = scene_poses_service.read_poses(
            scene_id=scene_id,
            limit=limit,
            include_ooc=include_ooc
        )
        return poses
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve poses: {str(e)}")


@router.put("/{scene_id}/poses/{pose_id}", response_model=Dict[str, str])
async def update_pose(scene_id: str, pose_id: str, pose_data: UpdatePoseRequest):
    """
    Update an existing pose with debounced saving.
    """
    try:
        # Convert pose_type string to enum if provided
        pose_type = None
        if pose_data.pose_type:
            pose_type = PoseType(pose_data.pose_type)
            
        scene_poses_service.update_pose(
            scene_id=scene_id,
            pose_id=pose_id,
            content=pose_data.content,
            pose_type=pose_type,
            is_ooc=pose_data.is_ooc,
            analysis_data=pose_data.analysis_data
        )
        return {"message": "Pose update scheduled (debounced)"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update pose: {str(e)}")


@router.delete("/{scene_id}/poses/{pose_id}", response_model=Dict[str, str])
async def delete_pose(scene_id: str, pose_id: str):
    """
    Delete a pose from a scene with debounced saving.
    """
    try:
        scene_poses_service.delete_pose(
            scene_id=scene_id,
            pose_id=pose_id
        )
        return {"message": "Pose deletion scheduled (debounced)"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete pose: {str(e)}")
