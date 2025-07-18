"""
Scene Management API endpoints.

Provides CRUD operations for scene management using MongoDB.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from http import HTTPStatus

from app.services.scene_service import SceneService
from app.services.character_mgmt_service import CharacterManagementService
from app.models.scene import PoseType
from app.middleware.auth_middleware import require_auth

# Create blueprint
scenes_bp = Blueprint('scenes', __name__)


@scenes_bp.route('', methods=['POST'])
@require_auth
def create_scene():
    """Create a new scene.
    
    Request body:
    {
        "name": "Scene Name",
        "description": "Scene description",  // Optional
        "max_poses": 100,  // Optional, default: 100
        "initial_participants": ["char_id1", "char_id2"],  // Optional
        "initial_context": {  // Optional
            "setting": "A dark forest at night",
            "mood": "Tense and mysterious",
            "recent_events": ["The party entered the forest"],
            "emotional_tone": "Apprehensive",
            "time_of_day": "Night",
            "location_details": ["Dense foliage", "Misty air"],
            "relationship_dynamics": {"char1_id:char2_id": "Allies"}
        }
    }
    
    Returns:
        201 Created: The created scene
        400 Bad Request: If validation fails or name already exists
        401 Unauthorized: If not authenticated
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    if not data or 'name' not in data:
        return jsonify({
            'success': False,
            'message': 'Scene name is required'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Verify all participant characters exist and belong to the user
        participant_ids = data.get('initial_participants', [])
        for char_id in participant_ids:
            char = CharacterManagementService.get_character(char_id, current_user)
            if not char:
                return jsonify({
                    'success': False,
                    'message': f'Character {char_id} not found or access denied'
                }), HTTPStatus.BAD_REQUEST
        
        # Create the scene
        scene = SceneService.create_scene(
            name=data['name'],
            created_by=current_user,
            description=data.get('description', ''),
            max_poses=int(data.get('max_poses', 100)),
            initial_participants=participant_ids,
            initial_context=data.get('initial_context')
        )
        
        return jsonify({
            'success': True,
            'data': scene.to_dict()
        }), HTTPStatus.CREATED
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        current_app.logger.error(f"Error creating scene: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while creating the scene'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>', methods=['GET'])
@require_auth
def get_scene(scene_id):
    """Get a scene by ID.
    
    Returns:
        200 OK: The scene data
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
    """
    current_user = get_jwt_identity()
    
    try:
        scene = SceneService.get_scene(
            scene_id=scene_id,
            user_id=current_user
        )
        
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
            
        return jsonify({
            'success': True,
            'data': scene.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting scene: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving the scene'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>', methods=['PUT'])
@require_auth
def update_scene(scene_id):
    """Update an existing scene.
    
    Request body:
    {
        "name": "Updated Scene Name",  // Optional
        "description": "Updated description",  // Optional
        "content": "Updated scene content",  // Optional
        "character_id": "char_id"  // Optional, character associated with update
    }
    
    Returns:
        200 OK: The updated scene
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    try:
        # First get the scene to check ownership
        existing_scene = SceneService.get_scene(
            scene_id=scene_id,
            user_id=current_user
        )
        
        if not existing_scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Prepare update data
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'content' in data:
            update_data['content'] = data['content']
        if 'context' in data:
            update_data['context'] = data['context']
            
        # Update the scene
        scene = SceneService.update_scene(
            scene_id=scene_id,
            user_id=current_user,
            update_data=update_data
        )
        
        return jsonify({
            'success': True,
            'data': scene.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating scene: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the scene'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('', methods=['GET'])
@require_auth
def list_scenes():
    """List all scenes for the current user.
    
    Query parameters:
        include_inactive (bool): Include inactive scenes (default: false)
        limit (int): Maximum number of scenes to return (default: 100)
        skip (int): Number of scenes to skip (for pagination, default: 0)
        sort (str): Field to sort by (default: updated_at)
        order (str): Sort order (asc or desc, default: desc)
    
    Returns:
        200 OK: List of scenes
    """
    current_user = get_jwt_identity()
    
    # Get query parameters
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 for safety
    skip = max(0, int(request.args.get('skip', 0)))
    sort_field = request.args.get('sort', 'updated_at')
    sort_direction = -1 if request.args.get('order', 'desc').lower() == 'desc' else 1
    
    try:
        scenes = SceneService.list_scenes(
            user_id=current_user,  # JWT identity is the user ID string
            include_inactive=include_inactive,
            limit=limit,
            skip=skip,
            sort_field=sort_field,
            sort_direction=sort_direction
        )
        
        return jsonify({
            'success': True,
            'data': [scene.to_dict() for scene in scenes],
            'meta': {
                'total': len(scenes),
                'limit': limit,
                'skip': skip
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing scenes: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while listing scenes'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>/poses', methods=['POST'])
@require_auth
def add_pose(scene_id):
    """Add a pose to a scene.
    
    Request body:
    {
        "character_id": "char_id",
        "character_name": "Character Name",
        "pose_text": "*looks around cautiously*",
        "pose_type": "action",  // action, dialogue, narrative, internal, mixed
        "enhanced_text": "Enhanced version of the pose",  // Optional
        "tags": ["emote", "action"],  // Optional
        "mentions": ["char_id1", "char_id2"]  // Optional
    }
    
    Returns:
        201 Created: The updated scene and new pose
        400 Bad Request: If validation fails
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['character_id', 'character_name', 'pose_text', 'pose_type']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            'success': False,
            'message': f'Missing required fields: {", ".join(missing_fields)}'
        }), HTTPStatus.BAD_REQUEST
    
    # Validate pose type
    try:
        pose_type = PoseType(data['pose_type'])
    except ValueError:
        return jsonify({
            'success': False,
            'message': f'Invalid pose_type. Must be one of: {", ".join(t.value for t in PoseType)}'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Add the pose
        result = SceneService.add_pose(
            scene_id=scene_id,
            character_id=data['character_id'],
            character_name=data['character_name'],
            pose_text=data['pose_text'],
            pose_type=pose_type,
            enhanced_text=data.get('enhanced_text'),
            tags=data.get('tags'),
            mentions=data.get('mentions')
        )
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        scene, pose = result
        
        return jsonify({
            'success': True,
            'data': {
                'scene': scene.to_dict(),
                'pose': pose.to_dict()
            }
        }), HTTPStatus.CREATED
        
    except Exception as e:
        current_app.logger.error(f"Error adding pose: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while adding the pose'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>/poses', methods=['GET'])
@require_auth
def get_recent_poses(scene_id):
    """Get recent poses from a scene.
    
    Query parameters:
        limit (int): Number of poses to return (default: 10, max: 100)
    
    Returns:
        200 OK: List of recent poses
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
    """
    current_user = get_jwt_identity()
    limit = min(int(request.args.get('limit', 10)), 100)  # Max 100 for safety
    
    try:
        poses = SceneService.get_recent_poses(
            scene_id=scene_id,
            user_id=current_user,
            limit=limit
        )
        
        if poses is None:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
            
        return jsonify({
            'success': True,
            'data': poses,
            'meta': {
                'total': len(poses),
                'limit': limit
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting recent poses: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving recent poses'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>/context', methods=['PATCH'])
@require_auth
def update_scene_context(scene_id):
    """Update a scene's context.
    
    Request body can include any context fields to update.
    
    Returns:
        200 OK: The updated scene
        400 Bad Request: If validation fails
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided for update'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Update the scene context
        scene = SceneService.update_scene_context(
            scene_id=scene_id,
            user_id=current_user,
            context_updates=data
        )
        
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
            
        return jsonify({
            'success': True,
            'data': scene.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating scene context: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the scene context'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>/participants', methods=['POST'])
@require_auth
def add_participant(scene_id):
    """Add a participant to a scene.
    
    Request body:
    {
        "character_id": "char_id"
    }
    
    Returns:
        200 OK: The updated scene
        400 Bad Request: If validation fails
        403 Forbidden: If not the owner of the scene or character
        404 Not Found: If scene or character doesn't exist
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'character_id' not in data:
        return jsonify({
            'success': False,
            'message': 'character_id is required'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Add the participant
        scene = SceneService.add_participant(
            scene_id=scene_id,
            user_id=current_user,
            character_id=data['character_id']
        )
        
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene or character not found, or access denied'
            }), HTTPStatus.NOT_FOUND
            
        return jsonify({
            'success': True,
            'data': scene.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error adding participant: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while adding the participant'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>/participants/<character_id>', methods=['DELETE'])
@require_auth
def remove_participant(scene_id, character_id):
    """Remove a participant from a scene.
    
    Returns:
        200 OK: The updated scene
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
    """
    current_user = get_jwt_identity()
    
    try:
        # Remove the participant
        scene = SceneService.remove_participant(
            scene_id=scene_id,
            user_id=current_user,
            character_id=character_id
        )
        
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
            
        return jsonify({
            'success': True,
            'data': scene.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error removing participant: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while removing the participant'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>', methods=['DELETE'])
@require_auth
def delete_scene(scene_id):
    """Delete a scene (soft delete).
    
    Returns:
        204 No Content: If deletion was successful
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
    """
    current_user = get_jwt_identity()
    
    try:
        success = SceneService.delete_scene(
            scene_id=scene_id,
            user_id=current_user['id']
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
            
        return '', HTTPStatus.NO_CONTENT
        
    except Exception as e:
        current_app.logger.error(f"Error deleting scene: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the scene'
        }), HTTPStatus.INTERNAL_SERVER_ERROR
        
@scenes_bp.route('/<scene_id>/save_with_context', methods=['POST'])
@require_auth
def save_scene_with_context(scene_id):
    """Save a scene with its context.
    
    Request body:
    {
        "scene_context": {  // Required
            "setting": "A dark forest at night",
            "mood": "Tense and mysterious",
            "active_characters": ["Character1", "Character2"],
            "recent_events": ["The party entered the forest"],
            "emotional_tone": "Apprehensive",
            "time_of_day": "Night",
            "location_details": ["Dense foliage", "Misty air"],
            "relationship_dynamics": {"Character1:Character2": "Allies"}
        }
    }
    
    Returns:
        200 OK: The updated scene
        400 Bad Request: If validation fails
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'scene_context' not in data:
        return jsonify({
            'success': False,
            'message': 'scene_context is required'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Save the scene with context
        scene = SceneService.save_scene_with_context(
            scene_id=scene_id,
            user_id=current_user,
            scene_context=data['scene_context']
        )
        
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
            
        return jsonify({
            'success': True,
            'data': scene.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error saving scene with context: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while saving the scene context'
        }), HTTPStatus.INTERNAL_SERVER_ERROR
