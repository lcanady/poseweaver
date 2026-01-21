"""
Scene Management API endpoints.

Provides CRUD operations for scene management using MongoDB.
"""
from flask import Blueprint, request, jsonify, current_app
from http import HTTPStatus

from app.services.scene_service import SceneService
from app.services.character_mgmt_service import CharacterManagementService
from app.models.scene import PoseType
from app.middleware.auth_middleware import require_auth, get_current_identity, get_current_identity
from app.services.search_service import SearchService
from app.services.summary_service import SummaryService, SummaryOptions

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
    current_user = get_current_identity()
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
    current_user = get_current_identity()
    
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
    current_user = get_current_identity()
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
    current_user = get_current_identity()
    
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
    current_user = get_current_identity()
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
    current_user = get_current_identity()
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
    current_user = get_current_identity()
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
    current_user = get_current_identity()
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
    current_user = get_current_identity()
    
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
    current_user = get_current_identity()
    
    try:
        success = SceneService.delete_scene(
            scene_id=scene_id,
            user_id=current_user
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
    current_user = get_current_identity()
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

# Scene History API endpoints
@scenes_bp.route('/<scene_id>/history', methods=['GET'])
@require_auth
def get_scene_history(scene_id):
    """Get scene history with poses in chronological order.
    
    Query parameters:
        limit (int): Maximum number of poses to return (default: 100, max: 500)
        include_ooc (bool): Include out-of-character poses (default: true)
        character_id (str): Filter by specific character ID (optional)
        start_date (str): Start date filter in ISO format (optional)
        end_date (str): End date filter in ISO format (optional)
    
    Returns:
        200 OK: List of poses in chronological order
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 1.1, 1.2, 1.5 - Scene history storage and retrieval
    """
    current_user = get_current_identity()
    
    # Get query parameters
    limit = min(int(request.args.get('limit', 100)), 500)  # Max 500 for performance
    include_ooc = request.args.get('include_ooc', 'true').lower() == 'true'
    character_id = request.args.get('character_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get scene history
        from app.services.scene_management_service import SceneManagementService
        scene_mgmt_service = SceneManagementService()
        
        poses = scene_mgmt_service.get_scene_history(
            scene_id=scene_id,
            limit=limit,
            include_ooc=include_ooc
        )
        
        # Apply additional filters if provided
        if character_id:
            poses = [pose for pose in poses if pose.character_id == character_id]
        
        if start_date:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            poses = [pose for pose in poses if pose.timestamp >= start_dt]
        
        if end_date:
            from datetime import datetime
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            poses = [pose for pose in poses if pose.timestamp <= end_dt]
        
        return jsonify({
            'success': True,
            'data': [pose.to_dict() for pose in poses],
            'meta': {
                'scene_id': scene_id,
                'scene_name': scene.name,
                'total_poses': len(poses),
                'limit': limit,
                'filters': {
                    'include_ooc': include_ooc,
                    'character_id': character_id,
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting scene history: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving scene history'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Scene Search API endpoints
@scenes_bp.route('/search', methods=['GET'])
@require_auth
def search_scenes():
    """Search for scenes matching the query.
    
    Query parameters:
        q (str): Search query text (required)
        limit (int): Maximum number of results (default: 10, max: 100)
        skip (int): Number of results to skip for pagination (default: 0)
        sort (str): Sort field - relevance, name, created_at, updated_at (default: relevance)
        order (str): Sort order - asc or desc (default: desc)
        include_inactive (bool): Include inactive scenes (default: false)
        date_range_start (str): Start date filter in ISO format (optional)
        date_range_end (str): End date filter in ISO format (optional)
        participants (str): Comma-separated character IDs to filter by (optional)
        tags (str): Comma-separated tags to filter by (optional)
    
    Returns:
        200 OK: List of matching scenes with relevance scores
        400 Bad Request: If query parameter is missing
        
    Requirements: 7.1, 7.2, 7.3 - Scene search functionality
    """
    current_user = get_current_identity()
    
    # Get query parameters
    query = request.args.get('q')
    if not query:
        return jsonify({
            'success': False,
            'message': 'Search query parameter "q" is required'
        }), HTTPStatus.BAD_REQUEST
    
    limit = min(int(request.args.get('limit', 10)), 100)
    skip = max(0, int(request.args.get('skip', 0)))
    sort_field = request.args.get('sort', 'relevance')
    sort_order = request.args.get('order', 'desc')
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    # Build filters
    filters = {}
    if not include_inactive:
        filters['is_active'] = True
    
    # Date range filters
    if request.args.get('date_range_start'):
        if 'date_range' not in filters:
            filters['date_range'] = {}
        filters['date_range']['start'] = request.args.get('date_range_start')
    
    if request.args.get('date_range_end'):
        if 'date_range' not in filters:
            filters['date_range'] = {}
        filters['date_range']['end'] = request.args.get('date_range_end')
    
    # Participants filter
    if request.args.get('participants'):
        participant_ids = request.args.get('participants').split(',')
        filters['participants'] = [pid.strip() for pid in participant_ids]
    
    # Tags filter
    if request.args.get('tags'):
        tag_list = request.args.get('tags').split(',')
        filters['tags'] = [tag.strip() for tag in tag_list]
    
    try:
        # Perform search
        search_results = SearchService.search_scenes(
            query=query,
            user_id=current_user,
            filters=filters,
            limit=limit,
            skip=skip,
            sort_field=sort_field,
            sort_direction=-1 if sort_order == 'desc' else 1
        )
        
        return jsonify({
            'success': True,
            'data': [result.to_dict() for result in search_results],
            'meta': {
                'query': query,
                'total_results': len(search_results),
                'limit': limit,
                'skip': skip,
                'sort_field': sort_field,
                'sort_order': sort_order,
                'filters': filters
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error searching scenes: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while searching scenes'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>/search/poses', methods=['GET'])
@require_auth
def search_poses(scene_id):
    """Search for poses within a specific scene.
    
    Query parameters:
        q (str): Search query text (required)
        limit (int): Maximum number of results (default: 20, max: 100)
        skip (int): Number of results to skip for pagination (default: 0)
        character_id (str): Filter by specific character ID (optional)
        pose_type (str): Filter by pose type (optional)
        date_range_start (str): Start date filter in ISO format (optional)
        date_range_end (str): End date filter in ISO format (optional)
    
    Returns:
        200 OK: List of matching poses with relevance scores
        400 Bad Request: If query parameter is missing
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 7.1, 7.2, 7.3 - Scene search functionality
    """
    current_user = get_current_identity()
    
    # Get query parameters
    query = request.args.get('q')
    if not query:
        return jsonify({
            'success': False,
            'message': 'Search query parameter "q" is required'
        }), HTTPStatus.BAD_REQUEST
    
    limit = min(int(request.args.get('limit', 20)), 100)
    skip = max(0, int(request.args.get('skip', 0)))
    character_id = request.args.get('character_id')
    pose_type = request.args.get('pose_type')
    
    # Build filters
    filters = {}
    if pose_type:
        filters['pose_type'] = pose_type
    
    # Date range filters
    if request.args.get('date_range_start') or request.args.get('date_range_end'):
        filters['date_range'] = {}
        if request.args.get('date_range_start'):
            filters['date_range']['start'] = request.args.get('date_range_start')
        if request.args.get('date_range_end'):
            filters['date_range']['end'] = request.args.get('date_range_end')
    
    try:
        # Perform search
        search_results = SearchService.search_poses(
            query=query,
            scene_id=scene_id,
            user_id=current_user,
            character_id=character_id,
            filters=filters,
            limit=limit,
            skip=skip
        )
        
        return jsonify({
            'success': True,
            'data': [result.to_dict() for result in search_results],
            'meta': {
                'scene_id': scene_id,
                'query': query,
                'total_results': len(search_results),
                'limit': limit,
                'skip': skip,
                'filters': filters
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error searching poses: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while searching poses'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

# Scene Summary Generation API endpoints
@scenes_bp.route('/<scene_id>/summary', methods=['POST'])
@require_auth
def generate_scene_summary(scene_id):
    """Generate a summary for a scene.
    
    Request body:
    {
        "summary_type": "comprehensive",  // Options: comprehensive, character, plot, environment
        "character_id": "char_id",  // Required if summary_type is "character"
        "max_length": 500,  // Maximum words (optional, default: 500)
        "include_details": true,  // Whether to include detailed descriptions (optional, default: true)
        "formal_style": false,  // Whether to use formal writing style (optional, default: false)
        "chronological": true,  // Whether to organize chronologically (optional, default: true)
        "highlight_key_events": true  // Whether to highlight key events (optional, default: true)
    }
    
    Returns:
        200 OK: The generated summary
        400 Bad Request: If validation fails
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 8.1, 8.2 - Scene summary generation
    """
    current_user = get_current_identity()
    data = request.get_json()
    
    # Validate required fields
    if not data:
        data = {}
    
    summary_type = data.get('summary_type', 'comprehensive')
    character_id = data.get('character_id')
    max_length = data.get('max_length', 500)
    include_details = data.get('include_details', True)
    formal_style = data.get('formal_style', False)
    chronological = data.get('chronological', True)
    highlight_key_events = data.get('highlight_key_events', True)
    
    # Validate summary type
    valid_types = ['comprehensive', 'character', 'plot', 'environment']
    if summary_type not in valid_types:
        return jsonify({
            'success': False,
            'message': f'Invalid summary_type. Must be one of: {", ".join(valid_types)}'
        }), HTTPStatus.BAD_REQUEST
    
    # Validate character_id if needed
    if summary_type == 'character' and not character_id:
        return jsonify({
            'success': False,
            'message': 'character_id is required when summary_type is "character"'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Create summary options
        options = SummaryOptions(
            focus=summary_type,
            character_id=character_id,
            max_length=max_length,
            include_details=include_details,
            formal_style=formal_style,
            chronological=chronological,
            highlight_key_events=highlight_key_events
        )
        
        # Generate summary
        summary = SummaryService.generate_summary(
            scene_id=scene_id,
            user_id=current_user,
            options=options
        )
        
        if not summary:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        return jsonify({
            'success': True,
            'data': summary.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating scene summary: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while generating the scene summary'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>/summary/catchup', methods=['POST'])
@require_auth
def generate_catchup_brief(scene_id):
    """Generate a catch-up brief for a scene.
    
    Request body:
    {
        "since_timestamp": "2024-01-01T00:00:00Z",  // Optional, defaults to 7 days ago
        "max_length": 300,  // Optional, default: 300 words
        "include_details": true,  // Optional, default: true
        "formal_style": false  // Optional, default: false
    }
    
    Returns:
        200 OK: The generated catch-up brief
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 8.3 - Catch-up brief generation
    """
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    since_timestamp_str = data.get('since_timestamp')
    max_length = data.get('max_length', 300)
    include_details = data.get('include_details', True)
    formal_style = data.get('formal_style', False)
    
    # Parse since_timestamp if provided
    since_timestamp = None
    if since_timestamp_str:
        try:
            from datetime import datetime
            since_timestamp = datetime.fromisoformat(since_timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid since_timestamp format. Use ISO format like "2024-01-01T00:00:00Z"'
            }), HTTPStatus.BAD_REQUEST
    
    try:
        # Create summary options
        options = SummaryOptions(
            focus='comprehensive',
            max_length=max_length,
            include_details=include_details,
            formal_style=formal_style,
            chronological=True
        )
        
        # Generate catch-up brief
        brief = SummaryService.generate_catchup_brief(
            scene_id=scene_id,
            user_id=current_user,
            since_timestamp=since_timestamp,
            options=options
        )
        
        if not brief:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        return jsonify({
            'success': True,
            'data': brief.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating catch-up brief: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while generating the catch-up brief'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

# Continuity Analysis Integration
@scenes_bp.route('/<scene_id>/poses/<pose_id>/continuity', methods=['POST'])
@require_auth
def analyze_pose_continuity(scene_id, pose_id):
    """Analyze continuity for a specific pose within a scene.
    
    Request body:
    {
        "pose_text": "The character's pose text",  // Required
        "character_id": "char_id",  // Required
        "analysis_type": "full"  // Options: full, character, environment, plot (optional, default: full)
    }
    
    Returns:
        200 OK: Continuity analysis results
        400 Bad Request: If validation fails
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene or pose doesn't exist
        
    Requirements: 6.1, 6.2, 6.3 - Continuity checking and alerts
    """
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'Request body is required'
        }), HTTPStatus.BAD_REQUEST
    
    pose_text = data.get('pose_text')
    character_id = data.get('character_id')
    analysis_type = data.get('analysis_type', 'full')
    
    # Validate required fields
    if not pose_text or not character_id:
        return jsonify({
            'success': False,
            'message': 'pose_text and character_id are required'
        }), HTTPStatus.BAD_REQUEST
    
    # Validate analysis type
    valid_types = ['full', 'character', 'environment', 'plot']
    if analysis_type not in valid_types:
        return jsonify({
            'success': False,
            'message': f'Invalid analysis_type. Must be one of: {", ".join(valid_types)}'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Perform continuity analysis
        from app.services.continuity_service import ContinuityService
        continuity_service = ContinuityService()
        
        analysis_result = continuity_service.analyze_pose_continuity(
            scene_id=scene_id,
            pose_text=pose_text,
            character_id=character_id,
            analysis_type=analysis_type
        )
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
        
    except Exception as e:
        current_app.logger.error(f"Error analyzing pose continuity: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while analyzing pose continuity'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>/continuity/flags', methods=['GET'])
@require_auth
def get_continuity_flags(scene_id):
    """Get continuity flags for a scene.
    
    Query parameters:
        flag_type (str): Filter by flag type (optional)
        severity (str): Filter by severity level (optional)
        resolved (bool): Filter by resolved status (optional)
        limit (int): Maximum number of flags to return (default: 50, max: 200)
        skip (int): Number of flags to skip for pagination (default: 0)
    
    Returns:
        200 OK: List of continuity flags
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 6.4 - Continuity flag management
    """
    current_user = get_current_identity()
    
    # Get query parameters
    flag_type = request.args.get('flag_type')
    severity = request.args.get('severity')
    resolved = request.args.get('resolved')
    limit = min(int(request.args.get('limit', 50)), 200)
    skip = max(0, int(request.args.get('skip', 0)))
    
    # Convert resolved to boolean if provided
    resolved_bool = None
    if resolved:
        resolved_bool = resolved.lower() == 'true'
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get continuity flags
        from app.services.continuity_service import ContinuityService
        continuity_service = ContinuityService()
        
        flags = continuity_service.get_continuity_flags(
            scene_id=scene_id,
            flag_type=flag_type,
            severity=severity,
            resolved=resolved_bool,
            limit=limit,
            skip=skip
        )
        
        return jsonify({
            'success': True,
            'data': [flag.to_dict() for flag in flags],
            'meta': {
                'scene_id': scene_id,
                'total_flags': len(flags),
                'limit': limit,
                'skip': skip,
                'filters': {
                    'flag_type': flag_type,
                    'severity': severity,
                    'resolved': resolved_bool
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting continuity flags: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving continuity flags'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@scenes_bp.route('/<scene_id>/poses', methods=['POST'])
@require_auth
def add_pose_with_continuity(scene_id):
    """Add a pose to a scene with integrated continuity analysis.
    
    This endpoint extends the existing pose addition functionality by integrating
    continuity analysis to detect potential issues before the pose is added.
    
    Request body:
    {
        "character_id": "char_id",
        "character_name": "Character Name",
        "pose_text": "*looks around cautiously*",
        "pose_type": "action",  // action, dialogue, narrative, internal, mixed
        "enhanced_text": "Enhanced version of the pose",  // Optional
        "tags": ["emote", "action"],  // Optional
        "mentions": ["char_id1", "char_id2"],  // Optional
        "analyze_continuity": true,  // Optional, default: true
        "continuity_analysis_type": "full"  // Options: full, character, environment, plot (optional, default: full)
    }
    
    Returns:
        201 Created: The updated scene, new pose, and continuity analysis results
        400 Bad Request: If validation fails
        403 Forbidden: If not the owner of the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 1.2, 6.1, 6.2 - Pose submission with continuity analysis
    """
    current_user = get_current_identity()
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
    
    # Get continuity analysis options
    analyze_continuity = data.get('analyze_continuity', True)
    continuity_analysis_type = data.get('continuity_analysis_type', 'full')
    
    try:
        # Perform continuity analysis first if requested
        continuity_analysis = None
        if analyze_continuity:
            from app.services.continuity_service import ContinuityService
            continuity_service = ContinuityService()
            
            continuity_analysis = continuity_service.analyze_pose_continuity(
                scene_id=scene_id,
                pose_text=data['pose_text'],
                character_id=data['character_id'],
                analysis_type=continuity_analysis_type
            )
        
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
        
        # Prepare response data
        response_data = {
            'scene': scene.to_dict(),
            'pose': pose.to_dict()
        }
        
        # Include continuity analysis if performed
        if continuity_analysis:
            response_data['continuity_analysis'] = continuity_analysis
        
        return jsonify({
            'success': True,
            'data': response_data
        }), HTTPStatus.CREATED
        
    except Exception as e:
        current_app.logger.error(f"Error adding pose with continuity analysis: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while adding the pose'
        }), HTTPStatus.INTERNAL_SERVER_ERROR
