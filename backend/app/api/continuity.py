"""
Continuity Checking API endpoints for Scene Memory & Continuity Tracking.

Provides comprehensive endpoints for real-time continuity analysis,
flag management, character state tracking, and environment state management.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from http import HTTPStatus
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.services.continuity_service import ContinuityService
from app.services.character_state_service import CharacterStateService
from app.services.environment_state_service import EnvironmentStateService
from app.services.scene_service import SceneService
from app.services.venice_client import VeniceClient
from app.middleware.auth_middleware import require_auth
from app.models.scene_memory import ContinuityFlag, FlagType, Severity
from app.models.scene import PoseType

# Create blueprint
continuity_bp = Blueprint('continuity', __name__)

# Initialize services with lazy initialization


def get_venice_client():
    """Get Venice client with proper API key handling."""
    import os
    api_key = os.getenv('VENICE_API_KEY', 'test-key')
    return VeniceClient(api_key=api_key)


# Initialize services
venice_client = None
continuity_service = None
character_state_service = None
environment_state_service = None


def init_services():
    """Initialize services lazily."""
    global venice_client, continuity_service, character_state_service
    global environment_state_service
    if venice_client is None:
        venice_client = get_venice_client()
        continuity_service = ContinuityService(venice_client)
        character_state_service = CharacterStateService(venice_client)
        environment_state_service = EnvironmentStateService(venice_client)


# Real-time Continuity Analysis Endpoints

@continuity_bp.route('/analyze', methods=['POST'])
@require_auth
def analyze_continuity():
    """Real-time continuity analysis for pose content.
    
    Request body:
    {
        "pose_text": "The character's pose text",  // Required
        "character_id": "char_id",  // Required
        "character_name": "Character Name",  // Required
        "scene_id": "scene_id",  // Required
        "analysis_type": "full",  // Options: full, character, environment,
                                   // plot (optional, default: full)
        "include_suggestions": true,  // Optional, default: true
        "historical_context": true  // Optional, default: true
    }
    
    Returns:
        200 OK: Comprehensive continuity analysis results
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 6.1 - Real-time continuity analysis
    """
    init_services()  # Initialize services
    current_user = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['pose_text', 'character_id', 'character_name', 
                      'scene_id']
    missing_fields = [field for field in required_fields 
                     if field not in data]
    
    if missing_fields:
        return jsonify({
            'success': False,
            'message': f'Missing required fields: {", ".join(missing_fields)}'
        }), HTTPStatus.BAD_REQUEST
    
    pose_text = data.get('pose_text')
    character_id = data.get('character_id')
    character_name = data.get('character_name')
    scene_id = data.get('scene_id')
    analysis_type = data.get('analysis_type', 'full')
    include_suggestions = data.get('include_suggestions', True)
    historical_context = data.get('historical_context', True)
    
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
        
        # Build context for analysis
        analysis_context = {
            'scene_id': scene_id,
            'character_id': character_id,
            'character_name': character_name,
            'pose_text': pose_text,
            'analysis_type': analysis_type,
            'include_suggestions': include_suggestions,
            'historical_context': historical_context
        }
        
        # Perform continuity analysis
        analysis_result = continuity_service.analyze_pose_continuity(
            scene_id=scene_id,
            pose_text=pose_text,
            character_id=character_id,
            analysis_type=analysis_type
        )
        
        # Get character state analysis if requested
        character_analysis = None
        if analysis_type in ['full', 'character']:
            try:
                character_analysis = character_state_service.analyze_character_consistency(
                    scene_id=scene_id,
                    character_name=character_name,
                    pose_text=pose_text
                )
            except Exception as e:
                current_app.logger.warning(f"Character analysis failed: {str(e)}")
        
        # Get environment analysis if requested
        environment_analysis = None
        if analysis_type in ['full', 'environment']:
            try:
                environment_analysis = environment_state_service.analyze_environment_consistency(
                    scene_id=scene_id,
                    pose_text=pose_text
                )
            except Exception as e:
                current_app.logger.warning(f"Environment analysis failed: {str(e)}")
        
        # Build comprehensive response
        response_data = {
            'analysis_id': f"analysis_{datetime.utcnow().isoformat()}",
            'continuity_analysis': analysis_result,
            'character_analysis': character_analysis,
            'environment_analysis': environment_analysis,
            'context': analysis_context,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in continuity analysis: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during continuity analysis'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@continuity_bp.route('/analyze/batch', methods=['POST'])
@require_auth
def analyze_batch_continuity():
    """Batch continuity analysis for multiple poses.
    
    Request body:
    {
        "poses": [
            {
                "pose_text": "First pose text",
                "character_id": "char_id1",
                "character_name": "Character1",
                "scene_id": "scene_id",
                "analysis_type": "full"
            },
            {
                "pose_text": "Second pose text",
                "character_id": "char_id2",
                "character_name": "Character2",
                "scene_id": "scene_id",
                "analysis_type": "character"
            }
        ],
        "include_cross_analysis": true  // Optional, analyze poses for interactions
    }
    
    Returns:
        200 OK: Batch analysis results
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        
    Requirements: 6.1 - Batch continuity analysis capability
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    # Validate request structure
    if not data or 'poses' not in data:
        return jsonify({
            'success': False,
            'message': 'poses array is required'
        }), HTTPStatus.BAD_REQUEST
    
    poses = data.get('poses', [])
    if not poses or len(poses) > 20:  # Limit batch size
        return jsonify({
            'success': False,
            'message': 'poses array must contain 1-20 poses'
        }), HTTPStatus.BAD_REQUEST
    
    include_cross_analysis = data.get('include_cross_analysis', True)
    
    # Validate each pose
    for i, pose in enumerate(poses):
        required_fields = ['pose_text', 'character_id', 'character_name', 'scene_id']
        missing_fields = [field for field in required_fields if field not in pose]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Pose {i+1} missing required fields: {", ".join(missing_fields)}'
            }), HTTPStatus.BAD_REQUEST
    
    try:
        # Verify scenes exist and user has access
        scene_ids = set(pose['scene_id'] for pose in poses)
        for scene_id in scene_ids:
            scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
            if not scene:
                return jsonify({
                    'success': False,
                    'message': f'Scene {scene_id} not found or access denied'
                }), HTTPStatus.NOT_FOUND
        
        # Perform batch analysis
        analysis_results = []
        for i, pose in enumerate(poses):
            try:
                result = continuity_service.analyze_pose_continuity(
                    scene_id=pose['scene_id'],
                    pose_text=pose['pose_text'],
                    character_id=pose['character_id'],
                    analysis_type=pose.get('analysis_type', 'full')
                )
                analysis_results.append({
                    'pose_index': i,
                    'pose_id': f"batch_pose_{i}",
                    'analysis': result,
                    'status': 'completed'
                })
            except Exception as e:
                current_app.logger.warning(f"Analysis failed for pose {i}: {str(e)}")
                analysis_results.append({
                    'pose_index': i,
                    'pose_id': f"batch_pose_{i}",
                    'analysis': None,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Perform cross-analysis if requested
        cross_analysis = None
        if include_cross_analysis and len(poses) > 1:
            try:
                # Cross-analysis not yet implemented
                cross_analysis = {
                    'status': 'not_implemented',
                    'message': 'Cross-analysis feature coming soon'
                }
            except Exception as e:
                current_app.logger.warning(f"Cross-analysis failed: {str(e)}")
        
        return jsonify({
            'success': True,
            'data': {
                'batch_id': f"batch_{datetime.utcnow().isoformat()}",
                'total_poses': len(poses),
                'successful_analyses': len([r for r in analysis_results if r['status'] == 'completed']),
                'failed_analyses': len([r for r in analysis_results if r['status'] == 'failed']),
                'results': analysis_results,
                'cross_analysis': cross_analysis,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in batch continuity analysis: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during batch continuity analysis'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Continuity Flag Management Endpoints

@continuity_bp.route('/flags', methods=['GET'])
@require_auth
def get_continuity_flags():
    """Get continuity flags with filtering and pagination.
    
    Query parameters:
        scene_id (str): Filter by scene ID (optional)
        character_id (str): Filter by character ID (optional)
        flag_type (str): Filter by flag type (optional)
        severity (str): Filter by severity level (optional)
        resolved (bool): Filter by resolved status (optional)
        start_date (str): Filter by creation date start (ISO format, optional)
        end_date (str): Filter by creation date end (ISO format, optional)
        limit (int): Maximum number of flags to return (default: 50, max: 200)
        skip (int): Number of flags to skip for pagination (default: 0)
        sort (str): Sort field - created_at, severity, flag_type (default: created_at)
        order (str): Sort order - asc or desc (default: desc)
    
    Returns:
        200 OK: List of continuity flags with metadata
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        
    Requirements: 6.4 - Continuity flag retrieval and management
    """
    init_services()  # Initialize services
    current_user = get_jwt_identity()
    
    # Get query parameters
    scene_id = request.args.get('scene_id')
    character_id = request.args.get('character_id')
    flag_type = request.args.get('flag_type')
    severity = request.args.get('severity')
    resolved = request.args.get('resolved')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = min(int(request.args.get('limit', 50)), 200)
    skip = max(0, int(request.args.get('skip', 0)))
    sort_field = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    # Validate sort field
    valid_sort_fields = ['created_at', 'severity', 'flag_type', 'confidence_score']
    if sort_field not in valid_sort_fields:
        return jsonify({
            'success': False,
            'message': f'Invalid sort field. Must be one of: {", ".join(valid_sort_fields)}'
        }), HTTPStatus.BAD_REQUEST
    
    # Convert resolved to boolean if provided
    resolved_bool = None
    if resolved:
        resolved_bool = resolved.lower() == 'true'
    
    # Build filters
    filters = {}
    if flag_type:
        filters['flag_type'] = flag_type
    if severity:
        filters['severity'] = severity
    if resolved_bool is not None:
        filters['resolved'] = resolved_bool
    if character_id:
        filters['character_id'] = character_id
    
    # Date range filters
    if start_date or end_date:
        filters['date_range'] = {}
        if start_date:
            try:
                filters['date_range']['start'] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid start_date format. Use ISO format.'
                }), HTTPStatus.BAD_REQUEST
        if end_date:
            try:
                filters['date_range']['end'] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid end_date format. Use ISO format.'
                }), HTTPStatus.BAD_REQUEST
    
    try:
        # If scene_id is provided, verify user has access
        if scene_id:
            scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
            if not scene:
                return jsonify({
                    'success': False,
                    'message': 'Scene not found or access denied'
                }), HTTPStatus.NOT_FOUND
        
        # Get continuity flags
        flags = continuity_service.get_continuity_flags(
            scene_id=scene_id,
            resolved=resolved_bool if 'resolved' in filters else None
        )
        
        # Apply remaining filters in the API layer
        filtered_flags = []
        for flag in flags:
            # Apply flag type filter
            if 'flag_type' in filters and flag.flag_type.value != filters['flag_type']:
                continue
            
            # Apply severity filter
            if 'severity' in filters and flag.severity.value != filters['severity']:
                continue
            
            # Apply character_id filter
            if 'character_id' in filters and flag.character_id != filters['character_id']:
                continue
            
            # Apply date range filter
            if 'date_range' in filters:
                if ('start' in filters['date_range'] and 
                    flag.created_at < filters['date_range']['start']):
                    continue
                if ('end' in filters['date_range'] and 
                    flag.created_at > filters['date_range']['end']):
                    continue
            
            filtered_flags.append(flag)
        
        # Apply sorting
        if sort_field == 'created_at':
            filtered_flags.sort(key=lambda x: x.created_at, 
                              reverse=(sort_order == 'desc'))
        elif sort_field == 'severity':
            filtered_flags.sort(key=lambda x: x.severity.value, 
                              reverse=(sort_order == 'desc'))
        elif sort_field == 'flag_type':
            filtered_flags.sort(key=lambda x: x.flag_type.value, 
                              reverse=(sort_order == 'desc'))
        elif sort_field == 'confidence_score':
            filtered_flags.sort(key=lambda x: x.confidence_score, 
                              reverse=(sort_order == 'desc'))
        
        # Apply pagination
        paginated_flags = filtered_flags[skip:skip+limit]
        
        # Calculate summary statistics based on filtered flags
        total_flags = len(filtered_flags)
        unresolved_flags = len([f for f in filtered_flags if not f.resolved])
        
        flag_type_counts = {}
        severity_counts = {}
        for flag in filtered_flags:
            flag_type_counts[flag.flag_type.value] = flag_type_counts.get(flag.flag_type.value, 0) + 1
            severity_counts[flag.severity.value] = severity_counts.get(flag.severity.value, 0) + 1
        
        return jsonify({
            'success': True,
            'data': [flag.to_dict() for flag in paginated_flags],
            'meta': {
                'total_flags': total_flags,
                'unresolved_flags': unresolved_flags,
                'resolved_flags': total_flags - unresolved_flags,
                'flag_type_distribution': flag_type_counts,
                'severity_distribution': severity_counts,
                'limit': limit,
                'skip': skip,
                'sort_field': sort_field,
                'sort_order': sort_order,
                'filters': filters
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting continuity flags: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving continuity flags'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@continuity_bp.route('/flags/<flag_id>', methods=['GET'])
@require_auth
def get_continuity_flag(flag_id):
    """Get detailed information about a specific continuity flag.
    
    Returns:
        200 OK: Detailed flag information
        401 Unauthorized: If not authenticated
        404 Not Found: If flag doesn't exist or access denied
        
    Requirements: 6.4 - Continuity flag retrieval and management
    """
    current_user = get_jwt_identity()
    
    try:
        # Get flag
        flag = ContinuityFlag.find_by_id(flag_id)
        if not flag:
            return jsonify({
                'success': False,
                'message': 'Continuity flag not found'
            }), HTTPStatus.NOT_FOUND
        
        # Verify user has access to the scene
        scene = SceneService.get_scene(scene_id=flag.scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Access denied to this continuity flag'
            }), HTTPStatus.NOT_FOUND
        
        # Get additional context
        flag_data = flag.to_dict()
        flag_data['scene_name'] = scene.name
        
        # Get related flags if any (feature not yet implemented)
        flag_data['related_flags'] = []
        
        return jsonify({
            'success': True,
            'data': flag_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting continuity flag: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving the continuity flag'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@continuity_bp.route('/flags/<flag_id>/resolve', methods=['POST'])
@require_auth
def resolve_continuity_flag(flag_id):
    """Resolve a continuity flag.
    
    Request body:
    {
        "resolution_notes": "Notes about how the flag was resolved",  // Optional
        "resolution_type": "accepted",  // Options: accepted, dismissed, fixed (optional, default: accepted)
        "update_scene": true  // Optional, update scene with resolution (default: false)
    }
    
    Returns:
        200 OK: Flag resolved successfully
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        404 Not Found: If flag doesn't exist or access denied
        
    Requirements: 6.4 - Continuity flag management
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    resolution_notes = data.get('resolution_notes', '')
    resolution_type = data.get('resolution_type', 'accepted')
    update_scene = data.get('update_scene', False)
    
    # Validate resolution type
    valid_types = ['accepted', 'dismissed', 'fixed']
    if resolution_type not in valid_types:
        return jsonify({
            'success': False,
            'message': f'Invalid resolution_type. Must be one of: {", ".join(valid_types)}'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Get flag
        flag = ContinuityFlag.find_by_id(flag_id)
        if not flag:
            return jsonify({
                'success': False,
                'message': 'Continuity flag not found'
            }), HTTPStatus.NOT_FOUND
        
        # Verify user has access to the scene
        scene = SceneService.get_scene(scene_id=flag.scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Access denied to this continuity flag'
            }), HTTPStatus.NOT_FOUND
        
        # Resolve the flag
        success = continuity_service.resolve_continuity_flag(
            flag_id=flag_id,
            resolution_notes=resolution_notes,
            resolution_type=resolution_type,
            resolved_by=current_user,
            update_scene=update_scene
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Failed to resolve continuity flag'
            }), HTTPStatus.INTERNAL_SERVER_ERROR
        
        # Get updated flag
        updated_flag = ContinuityFlag.find_by_id(flag_id)
        
        return jsonify({
            'success': True,
            'message': 'Continuity flag resolved successfully',
            'data': updated_flag.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error resolving continuity flag: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while resolving the continuity flag'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@continuity_bp.route('/flags/<flag_id>/dismiss', methods=['POST'])
@require_auth
def dismiss_continuity_flag(flag_id):
    """Dismiss a continuity flag without resolving it.
    
    Request body:
    {
        "dismiss_reason": "Reason for dismissal",  // Optional
        "permanent": false  // Optional, permanently dismiss flag (default: false)
    }
    
    Returns:
        200 OK: Flag dismissed successfully
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        404 Not Found: If flag doesn't exist or access denied
        
    Requirements: 6.4 - Continuity flag management
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    dismiss_reason = data.get('dismiss_reason', '')
    permanent = data.get('permanent', False)
    
    try:
        # Get flag
        flag = ContinuityFlag.find_by_id(flag_id)
        if not flag:
            return jsonify({
                'success': False,
                'message': 'Continuity flag not found'
            }), HTTPStatus.NOT_FOUND
        
        # Verify user has access to the scene
        scene = SceneService.get_scene(scene_id=flag.scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Access denied to this continuity flag'
            }), HTTPStatus.NOT_FOUND
        
        # Dismiss the flag (using resolve function for now)
        success = continuity_service.resolve_continuity_flag(
            flag_id=flag_id,
            resolution_notes=dismiss_reason,
            resolved_by=current_user
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Failed to dismiss continuity flag'
            }), HTTPStatus.INTERNAL_SERVER_ERROR
        
        # Get updated flag
        updated_flag = ContinuityFlag.find_by_id(flag_id)
        
        return jsonify({
            'success': True,
            'message': 'Continuity flag dismissed successfully',
            'data': updated_flag.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error dismissing continuity flag: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while dismissing the continuity flag'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Character State Tracking Endpoints

@continuity_bp.route('/character-states/<scene_id>', methods=['GET'])
@require_auth
def get_character_states(scene_id):
    """Get all character states for a scene.
    
    Query parameters:
        character_id (str): Filter by specific character ID (optional)
        include_history (bool): Include state change history (default: false)
        limit (int): Maximum number of states to return (default: 100)
        
    Returns:
        200 OK: List of character states
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 2.1, 2.2, 2.3 - Character state tracking
    """
    init_services()  # Initialize services
    current_user = get_jwt_identity()
    
    # Get query parameters
    character_id = request.args.get('character_id')
    include_history = request.args.get('include_history', 'false').lower() == 'true'
    limit = min(int(request.args.get('limit', 100)), 500)
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get character states
        character_states = character_state_service.get_character_states_for_scene(scene_id)
        
        # Apply filtering if character_id is specified
        if character_id:
            character_states = [cs for cs in character_states if cs.character_id == character_id]
        
        # Apply limit if specified
        if limit and len(character_states) > limit:
            character_states = character_states[:limit]
        
        # Build response data
        states_data = []
        for state in character_states:
            state_data = state.to_dict()
            
            # Add history if requested
            if include_history:
                state_data['state_history'] = character_state_service.get_state_history(
                    scene_id=scene_id,
                    character_name=state.character_name
                )
            
            states_data.append(state_data)
        
        return jsonify({
            'success': True,
            'data': states_data,
            'meta': {
                'scene_id': scene_id,
                'scene_name': scene.name,
                'total_states': len(states_data),
                'filters': {
                    'character_id': character_id,
                    'include_history': include_history
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting character states: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving character states'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@continuity_bp.route('/character-states/<scene_id>/<character_name>', methods=['GET'])
@require_auth
def get_character_state(scene_id, character_name):
    """Get current state for a specific character in a scene.
    
    Query parameters:
        include_history (bool): Include state change history (default: false)
        include_relationships (bool): Include character relationships (default: false)
        
    Returns:
        200 OK: Character state data
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene or character state doesn't exist
        
    Requirements: 2.3 - Display character's last known state
    """
    current_user = get_jwt_identity()
    
    # Get query parameters
    include_history = request.args.get('include_history', 'false').lower() == 'true'
    include_relationships = request.args.get('include_relationships', 'false').lower() == 'true'
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get character state
        character_state = character_state_service.get_character_current_state(
            scene_id=scene_id,
            character_name=character_name
        )
        
        if not character_state:
            return jsonify({
                'success': False,
                'message': 'Character state not found'
            }), HTTPStatus.NOT_FOUND
        
        # Build response data
        state_data = character_state.to_dict()
        
        # Add history if requested
        if include_history:
            state_data['state_history'] = character_state_service.get_state_history(
                scene_id=scene_id,
                character_name=character_name
            )
        
        # Add relationships if requested
        if include_relationships:
            state_data['relationships'] = character_state_service.get_character_relationships(
                scene_id=scene_id,
                character_name=character_name
            )
        
        return jsonify({
            'success': True,
            'data': state_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting character state: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving character state'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@continuity_bp.route('/character-states/<scene_id>/<character_name>', methods=['POST'])
@require_auth
def initialize_character_state(scene_id, character_name):
    """Initialize character state for a scene.
    
    Request body:
    {
        "initial_state": {  // Optional initial state data
            "physical_state": {
                "health": "healthy",
                "injuries": [],
                "fatigue": "rested",
                "condition": "normal"
            },
            "emotional_state": {
                "mood": "neutral",
                "stress_level": "low",
                "dominant_emotion": "calm"
            },
            "equipment": {
                "weapons": [],
                "armor": [],
                "items": [],
                "clothing": []
            },
            "conditions": {
                "magical_effects": [],
                "status_conditions": [],
                "temporary_modifiers": []
            },
            "location": "unknown"
        },
        "auto_detect": true  // Optional, auto-detect state from recent poses (default: false)
    }
    
    Returns:
        201 Created: Character state initialized successfully
        400 Bad Request: If validation fails or state already exists
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 2.1 - Record initial character state when entering scene
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    initial_state = data.get('initial_state')
    auto_detect = data.get('auto_detect', False)
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Check if character state already exists
        existing_state = character_state_service.get_character_current_state(
            scene_id=scene_id,
            character_name=character_name
        )
        
        if existing_state:
            return jsonify({
                'success': False,
                'message': 'Character state already exists for this scene'
            }), HTTPStatus.BAD_REQUEST
        
        # Auto-detect initial state if requested
        if auto_detect:
            detected_state = character_state_service.auto_detect_initial_state(
                scene_id=scene_id,
                character_name=character_name
            )
            if detected_state:
                initial_state = detected_state
        
        # Initialize character state
        character_state = character_state_service.initialize_character_state(
            scene_id=scene_id,
            character_name=character_name,
            initial_state=initial_state
        )
        
        return jsonify({
            'success': True,
            'message': 'Character state initialized successfully',
            'data': character_state.to_dict()
        }), HTTPStatus.CREATED
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        current_app.logger.error(f"Error initializing character state: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while initializing character state'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@continuity_bp.route('/character-states/<scene_id>/<character_name>', methods=['PUT'])
@require_auth
def update_character_state(scene_id, character_name):
    """Update character state with new values.
    
    Request body:
    {
        "updates": {  // Required updates dictionary
            "physical_state": {
                "health": "injured",
                "injuries": ["Minor cut on arm"]
            },
            "emotional_state": {
                "mood": "anxious",
                "stress_level": "high"
            },
            "equipment": {
                "weapons": ["Sword", "Shield"]
            },
            "conditions": {
                "magical_effects": ["Blessing of Protection"]
            },
            "location": "Forest Clearing"
        },
        "change_reason": "Updated from pose analysis",  // Optional
        "auto_detect": false  // Optional, auto-detect changes from recent poses
    }
    
    Returns:
        200 OK: Character state updated successfully
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene or character state doesn't exist
        
    Requirements: 2.2 - Update and track character state changes automatically
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'updates' not in data:
        return jsonify({
            'success': False,
            'message': 'updates dictionary is required'
        }), HTTPStatus.BAD_REQUEST
    
    updates = data.get('updates')
    change_reason = data.get('change_reason', '')
    auto_detect = data.get('auto_detect', False)
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Auto-detect changes if requested
        if auto_detect:
            detected_changes = character_state_service.auto_detect_state_changes(
                scene_id=scene_id,
                character_name=character_name
            )
            if detected_changes:
                # Merge detected changes with provided updates
                updates = {**detected_changes, **updates}
        
        # Update character state
        character_state = character_state_service.update_character_state(
            scene_id=scene_id,
            character_name=character_name,
            updates=updates,
            change_reason=change_reason
        )
        
        return jsonify({
            'success': True,
            'message': 'Character state updated successfully',
            'data': character_state.to_dict()
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        current_app.logger.error(f"Error updating character state: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating character state'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Environment State Management Endpoints

@continuity_bp.route('/environment-states/<scene_id>', methods=['GET'])
@require_auth
def get_environment_states(scene_id):
    """Get all environment states for a scene.
    
    Query parameters:
        current_only (bool): Only return current environment (default: false)
        include_history (bool): Include environment change history (default: false)
        
    Returns:
        200 OK: List of environment states
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 3.1, 3.5 - Environment state tracking and access
    """
    init_services()  # Initialize services
    current_user = get_jwt_identity()
    
    # Get query parameters
    current_only = request.args.get('current_only', 'false').lower() == 'true'
    include_history = request.args.get('include_history', 'false').lower() == 'true'
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get environment states
        if current_only:
            current_env = environment_state_service.get_current_environment(scene_id)
            environments = [current_env] if current_env else []
        else:
            environments = environment_state_service.get_scene_environments(scene_id)
        
        # Build response data
        environments_data = []
        for env in environments:
            env_data = env.to_dict()
            
            # Add history if requested
            if include_history:
                env_data['change_history'] = environment_state_service.get_environment_history(
                    scene_id=scene_id,
                    environment_id=env.id
                )
            
            environments_data.append(env_data)
        
        return jsonify({
            'success': True,
            'data': environments_data,
            'meta': {
                'scene_id': scene_id,
                'scene_name': scene.name,
                'total_environments': len(environments_data),
                'current_environment': environments_data[-1] if environments_data else None,
                'filters': {
                    'current_only': current_only,
                    'include_history': include_history
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting environment states: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving environment states'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@continuity_bp.route('/environment-states/<scene_id>/current', methods=['GET'])
@require_auth
def get_current_environment_state(scene_id):
    """Get current environment state for a scene.
    
    Query parameters:
        include_details (bool): Include detailed environment information (default: true)
        include_consistency (bool): Include consistency check info (default: false)
        
    Returns:
        200 OK: Current environment state
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist or no environment state found
        
    Requirements: 3.5 - Provide quick access to established scene elements
    """
    current_user = get_jwt_identity()
    
    # Get query parameters
    include_details = request.args.get('include_details', 'true').lower() == 'true'
    include_consistency = request.args.get('include_consistency', 'false').lower() == 'true'
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get current environment state
        current_env = environment_state_service.get_current_environment(scene_id)
        
        if not current_env:
            return jsonify({
                'success': False,
                'message': 'No environment state found for this scene'
            }), HTTPStatus.NOT_FOUND
        
        # Build response data
        env_data = current_env.to_dict()
        
        # Add detailed information if requested
        if include_details:
            env_data['detailed_description'] = environment_state_service.get_detailed_description(
                scene_id=scene_id,
                environment_id=current_env.id
            )
        
        # Add consistency information if requested
        if include_consistency:
            env_data['consistency_status'] = environment_state_service.get_consistency_status(
                scene_id=scene_id,
                environment_id=current_env.id
            )
        
        return jsonify({
            'success': True,
            'data': env_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting current environment state: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving current environment state'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@continuity_bp.route('/environment-states/<scene_id>', methods=['POST'])
@require_auth
def initialize_environment_state(scene_id):
    """Initialize environment state for a scene.
    
    Request body:
    {
        "location_name": "Forest Clearing",  // Required
        "description": "A peaceful clearing in the forest",  // Optional
        "weather": {  // Optional
            "condition": "clear",
            "temperature": "mild",
            "wind": "gentle breeze"
        },
        "time_context": {  // Optional
            "time_of_day": "afternoon",
            "season": "spring"
        },
        "physical_details": {  // Optional
            "lighting": "dappled sunlight",
            "sounds": ["birds chirping", "wind in trees"],
            "smells": ["fresh air", "wildflowers"]
        },
        "auto_detect": true  // Optional, auto-detect from recent poses (default: false)
    }
    
    Returns:
        201 Created: Environment state initialized successfully
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 3.1 - Extract and store environmental information
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'location_name' not in data:
        return jsonify({
            'success': False,
            'message': 'location_name is required'
        }), HTTPStatus.BAD_REQUEST
    
    location_name = data.get('location_name')
    description = data.get('description', '')
    weather = data.get('weather')
    time_context = data.get('time_context')
    physical_details = data.get('physical_details')
    auto_detect = data.get('auto_detect', False)
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Auto-detect environment details if requested
        if auto_detect:
            detected_details = environment_state_service.auto_detect_environment_details(scene_id)
            if detected_details:
                weather = weather or detected_details.get('weather')
                time_context = time_context or detected_details.get('time_context')
                physical_details = physical_details or detected_details.get('physical_details')
                if not description:
                    description = detected_details.get('description', '')
        
        # Initialize environment state
        environment_state = environment_state_service.initialize_environment_state(
            scene_id=scene_id,
            location_name=location_name,
            description=description,
            weather=weather,
            time_context=time_context,
            physical_details=physical_details
        )
        
        return jsonify({
            'success': True,
            'message': 'Environment state initialized successfully',
            'data': environment_state.to_dict()
        }), HTTPStatus.CREATED
        
    except Exception as e:
        current_app.logger.error(f"Error initializing environment state: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while initializing environment state'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@continuity_bp.route('/environment-states/<scene_id>/check-consistency', methods=['POST'])
@require_auth
def check_environment_consistency(scene_id):
    """Check environmental consistency for new content.
    
    Request body:
    {
        "content": "The sun suddenly disappeared and it began to snow",  // Required
        "character_name": "Character Name",  // Optional
        "include_suggestions": true  // Optional, include suggestions for fixes
    }
    
    Returns:
        200 OK: Environment consistency check results
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 3.2 - Check for consistency with established details
    """
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({
            'success': False,
            'message': 'content is required'
        }), HTTPStatus.BAD_REQUEST
    
    content = data.get('content')
    character_name = data.get('character_name')
    include_suggestions = data.get('include_suggestions', True)
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get current environment state
        current_env = environment_state_service.get_current_environment(scene_id)
        if not current_env:
            return jsonify({
                'success': False,
                'message': 'No environment state found for this scene'
            }), HTTPStatus.NOT_FOUND
        
        # Check environmental consistency
        consistency_check = environment_state_service.check_environment_consistency(
            scene_id=scene_id,
            content=content,
            character_name=character_name,
            include_suggestions=include_suggestions
        )
        
        return jsonify({
            'success': True,
            'data': consistency_check
        })
        
    except Exception as e:
        current_app.logger.error(f"Error checking environment consistency: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while checking environment consistency'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Summary and Dashboard Endpoints

@continuity_bp.route('/summary/<scene_id>', methods=['GET'])
@require_auth
def get_continuity_summary(scene_id):
    """Get comprehensive continuity summary for a scene.
    
    Query parameters:
        include_stats (bool): Include detailed statistics (default: true)
        include_trends (bool): Include trend analysis (default: false)
        
    Returns:
        200 OK: Continuity summary data
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 6.1, 6.4 - Continuity overview and management
    """
    init_services()  # Initialize services
    current_user = get_jwt_identity()
    
    # Get query parameters
    include_stats = request.args.get('include_stats', 'true').lower() == 'true'
    include_trends = request.args.get('include_trends', 'false').lower() == 'true'
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get continuity summary
        summary = continuity_service.get_scene_continuity_summary(scene_id)
        
        # Add statistics if requested - they're already included in the summary
        if include_stats:
            summary['statistics'] = {
                'total_flags': summary.get('total_flags', 0),
                'unresolved_flags': summary.get('unresolved_flags', 0),
                'resolved_flags': summary.get('resolved_flags', 0),
                'flag_distribution': summary.get('flag_types', {}),
                'severity_distribution': summary.get('severity_distribution', {}),
                'overall_health': summary.get('overall_health', 'unknown')
            }
        
        # Add trends if requested - placeholder for now
        if include_trends:
            summary['trends'] = {
                'flag_creation_rate': 'stable',
                'resolution_rate': 'stable',
                'health_trend': 'stable'
            }
        
        # Add scene metadata
        summary['scene_info'] = {
            'scene_id': scene_id,
            'scene_name': scene.name,
            'created_at': scene.created_at.isoformat() if hasattr(scene.created_at, 'isoformat') else scene.created_at,
            'updated_at': scene.updated_at.isoformat() if hasattr(scene.updated_at, 'isoformat') else scene.updated_at,
            'pose_count': len(scene.poses) if hasattr(scene, 'poses') else 0
        }
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting continuity summary: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving continuity summary'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Health Check Endpoint

@continuity_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for continuity service.
    
    Returns:
        200 OK: Service status and health information
    """
    try:
        # Check service availability
        services_status = {
            'continuity_service': 'healthy',
            'character_state_service': 'healthy',
            'environment_state_service': 'healthy',
            'venice_client': 'healthy' if venice_client else 'unavailable'
        }
        
        # Check database connectivity
        from app.models.scene_memory import ContinuityFlag
        try:
            ContinuityFlag.get_collection().find_one({})
            services_status['database'] = 'healthy'
        except Exception:
            services_status['database'] = 'unavailable'
        
        overall_status = 'healthy' if all(
            status == 'healthy' for status in services_status.values()
        ) else 'degraded'
        
        return jsonify({
            'success': True,
            'service': 'continuity_api',
            'status': overall_status,
            'services': services_status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'service': 'continuity_api',
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), HTTPStatus.INTERNAL_SERVER_ERROR 