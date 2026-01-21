"""
Character and Plot Tracking API endpoints for Scene Memory & Continuity Tracking.

Provides comprehensive endpoints for character state management, plot thread tracking,
relationship management, and character consistency checking.
"""
from flask import Blueprint, request, jsonify, current_app
from http import HTTPStatus
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.services.character_state_service import CharacterStateService
from app.services.plot_thread_service import PlotThreadService

from app.services.scene_service import SceneService
from app.services.ai_client import AIClient
from app.middleware.auth_middleware import require_auth, get_current_identity
from app.models.scene_memory import PlotThread, PlotStatus, CharacterState
from app.models.scene import PoseType

# Create blueprint
character_plot_bp = Blueprint('character_plot_tracking', __name__)

# Initialize services with lazy initialization


def get_ai_client():
    """Get OpenRouter client with proper API key handling."""
    import os
    api_key = os.getenv('OPENROUTER_API_KEY', 'test-key')
    return AIClient(api_key=api_key)


# Initialize services
ai_client = None
character_state_service = None
plot_thread_service = None



def init_services():
    """Initialize services lazily."""
    global ai_client, character_state_service, plot_thread_service
    if ai_client is None:
        ai_client = get_ai_client()
        character_state_service = CharacterStateService(ai_client)
        plot_thread_service = PlotThreadService(ai_client)



# Plot Thread Management Endpoints

@character_plot_bp.route('/plot-threads/<scene_id>', methods=['GET'])
@require_auth
def get_plot_threads(scene_id):
    """Get plot threads for a scene with filtering and pagination.
    
    Query parameters:
        status (str): Filter by plot thread status (optional)
        importance_min (float): Minimum importance score (optional)
        importance_max (float): Maximum importance score (optional)
        include_resolved (bool): Include resolved threads (default: true)
        include_abandoned (bool): Include abandoned threads (default: false)
        limit (int): Maximum number of threads to return (default: 50, max: 200)
        skip (int): Number of threads to skip for pagination (default: 0)
        sort (str): Sort field - created_at, importance, status (default: created_at)
        order (str): Sort order - asc or desc (default: desc)
        
    Returns:
        200 OK: List of plot threads with metadata
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 4.1, 4.2 - Plot thread identification and tracking
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    status = request.args.get('status')
    importance_min = request.args.get('importance_min', type=float)
    importance_max = request.args.get('importance_max', type=float)
    include_resolved = request.args.get('include_resolved', 'true').lower() == 'true'
    include_abandoned = request.args.get('include_abandoned', 'false').lower() == 'true'
    limit = min(int(request.args.get('limit', 50)), 200)
    skip = max(0, int(request.args.get('skip', 0)))
    sort_field = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    # Validate parameters
    if importance_min is not None and (importance_min < 0 or importance_min > 1):
        return jsonify({
            'success': False,
            'message': 'importance_min must be between 0 and 1'
        }), HTTPStatus.BAD_REQUEST
    
    if importance_max is not None and (importance_max < 0 or importance_max > 1):
        return jsonify({
            'success': False,
            'message': 'importance_max must be between 0 and 1'
        }), HTTPStatus.BAD_REQUEST
    
    valid_sort_fields = ['created_at', 'importance', 'status', 'last_referenced']
    if sort_field not in valid_sort_fields:
        return jsonify({
            'success': False,
            'message': f'Invalid sort field. Must be one of: {", ".join(valid_sort_fields)}'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get all plot threads for the scene
        all_threads = PlotThread.find_by_scene(scene_id)
        
        # Apply filters
        filtered_threads = []
        for thread in all_threads:
            # Status filtering
            if status and thread.status.value != status:
                continue
            
            # Resolved/abandoned filtering
            if not include_resolved and thread.status == PlotStatus.RESOLVED:
                continue
            if not include_abandoned and thread.status == PlotStatus.ABANDONED:
                continue
            
            # Importance filtering
            if importance_min is not None and thread.importance_score < importance_min:
                continue
            if importance_max is not None and thread.importance_score > importance_max:
                continue
            
            filtered_threads.append(thread)
        
        # Sort threads
        reverse = sort_order == 'desc'
        if sort_field == 'created_at':
            filtered_threads.sort(key=lambda t: t.created_at, reverse=reverse)
        elif sort_field == 'importance':
            filtered_threads.sort(key=lambda t: t.importance_score, reverse=reverse)
        elif sort_field == 'status':
            filtered_threads.sort(key=lambda t: t.status.value, reverse=reverse)
        elif sort_field == 'last_referenced':
            filtered_threads.sort(key=lambda t: t.last_referenced or t.created_at, reverse=reverse)
        
        # Apply pagination
        paginated_threads = filtered_threads[skip:skip + limit]
        
        # Calculate summary statistics
        total_threads = len(all_threads)
        active_threads = len([t for t in all_threads if t.status in [PlotStatus.INTRODUCED, PlotStatus.DEVELOPING]])
        stale_threads = plot_thread_service.get_stale_plot_threads(scene_id)
        
        status_counts = {}
        for thread in all_threads:
            status = thread.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return jsonify({
            'success': True,
            'data': [thread.to_dict() for thread in paginated_threads],
            'meta': {
                'scene_id': scene_id,
                'scene_name': scene.name,
                'total_threads': total_threads,
                'active_threads': active_threads,
                'stale_threads': len(stale_threads),
                'status_distribution': status_counts,
                'pagination': {
                    'limit': limit,
                    'skip': skip,
                    'returned': len(paginated_threads),
                    'total_filtered': len(filtered_threads)
                },
                'filters': {
                    'status': status,
                    'importance_min': importance_min,
                    'importance_max': importance_max,
                    'include_resolved': include_resolved,
                    'include_abandoned': include_abandoned
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting plot threads: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving plot threads'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@character_plot_bp.route('/plot-threads/<scene_id>/<thread_id>', methods=['GET'])
@require_auth
def get_plot_thread(scene_id, thread_id):
    """Get detailed information about a specific plot thread.
    
    Query parameters:
        include_related (bool): Include related plot threads (default: true)
        include_poses (bool): Include related poses (default: true)
        include_timeline (bool): Include timeline information (default: false)
        
    Returns:
        200 OK: Detailed plot thread information
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene or thread doesn't exist
        
    Requirements: 4.1, 4.2 - Plot thread retrieval and context
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    include_related = request.args.get('include_related', 'true').lower() == 'true'
    include_poses = request.args.get('include_poses', 'true').lower() == 'true'
    include_timeline = request.args.get('include_timeline', 'false').lower() == 'true'
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get plot thread
        thread = PlotThread.find_by_id(thread_id)
        if not thread or thread.scene_id != scene_id:
            return jsonify({
                'success': False,
                'message': 'Plot thread not found'
            }), HTTPStatus.NOT_FOUND
        
        # Build response data
        thread_data = thread.to_dict()
        
        # Add related threads if requested
        if include_related:
            thread_data['related_threads'] = plot_thread_service.get_related_threads(thread_id)
        
        # Add poses if requested
        if include_poses:
            thread_data['related_poses'] = plot_thread_service.get_thread_poses(thread_id)
        
        # Add timeline if requested
        if include_timeline:
            thread_data['timeline'] = plot_thread_service.get_thread_timeline(thread_id)
        
        return jsonify({
            'success': True,
            'data': thread_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting plot thread: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving plot thread'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@character_plot_bp.route('/plot-threads/<scene_id>/<thread_id>', methods=['PUT'])
@require_auth
def update_plot_thread(scene_id, thread_id):
    """Update a plot thread's status, importance, or other details.
    
    Request body:
    {
        "status": "introduced|developing|resolved|abandoned",  // Optional
        "importance_score": 0.8,  // Optional, 0.0-1.0
        "resolution_notes": "How the thread was resolved",  // Optional
        "title": "Updated thread title",  // Optional
        "description": "Updated description"  // Optional
    }
    
    Returns:
        200 OK: Updated plot thread
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene or thread doesn't exist
        
    Requirements: 4.4 - Plot thread status tracking and updates
    """
    init_services()
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'Request body is required'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get plot thread
        thread = PlotThread.find_by_id(thread_id)
        if not thread or thread.scene_id != scene_id:
            return jsonify({
                'success': False,
                'message': 'Plot thread not found'
            }), HTTPStatus.NOT_FOUND
        
        # Validate and apply updates
        if 'status' in data:
            try:
                new_status = PlotStatus(data['status'])
                if new_status == PlotStatus.RESOLVED:
                    resolution_notes = data.get('resolution_notes', '')
                    success = plot_thread_service.update_plot_thread_status(
                        thread_id, new_status, resolution_notes
                    )
                    if not success:
                        return jsonify({
                            'success': False,
                            'message': 'Failed to update plot thread status'
                        }), HTTPStatus.INTERNAL_SERVER_ERROR
                else:
                    success = plot_thread_service.update_plot_thread_status(
                        thread_id, new_status
                    )
                    if not success:
                        return jsonify({
                            'success': False,
                            'message': 'Failed to update plot thread status'
                        }), HTTPStatus.INTERNAL_SERVER_ERROR
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid status value'
                }), HTTPStatus.BAD_REQUEST
        
        if 'importance_score' in data:
            importance = data['importance_score']
            if not isinstance(importance, (int, float)) or importance < 0 or importance > 1:
                return jsonify({
                    'success': False,
                    'message': 'importance_score must be a number between 0 and 1'
                }), HTTPStatus.BAD_REQUEST
            thread.importance_score = importance
        
        if 'title' in data:
            thread.title = data['title']
        
        if 'description' in data:
            thread.description = data['description']
        
        # Save changes
        thread.save()
        
        # Get updated thread
        updated_thread = PlotThread.find_by_id(thread_id)
        
        return jsonify({
            'success': True,
            'message': 'Plot thread updated successfully',
            'data': updated_thread.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating plot thread: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating plot thread'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@character_plot_bp.route('/plot-threads/<scene_id>/<thread_id>/analyze', methods=['POST'])
@require_auth
def analyze_plot_thread(scene_id, thread_id):
    """Analyze a plot thread for connections and development opportunities.
    
    Request body:
    {
        "analysis_type": "connections|development|resolution|all",  // Optional, default: all
        "include_suggestions": true,  // Optional, default: true
        "context_depth": 5  // Optional, number of recent poses to consider
    }
    
    Returns:
        200 OK: Plot thread analysis results
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene or thread doesn't exist
        
    Requirements: 4.2, 4.3 - Plot thread analysis and linking
    """
    init_services()
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    analysis_type = data.get('analysis_type', 'all')
    include_suggestions = data.get('include_suggestions', True)
    context_depth = data.get('context_depth', 5)
    
    # Validate analysis type
    valid_types = ['connections', 'development', 'resolution', 'all']
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
        
        # Get plot thread
        thread = PlotThread.find_by_id(thread_id)
        if not thread or thread.scene_id != scene_id:
            return jsonify({
                'success': False,
                'message': 'Plot thread not found'
            }), HTTPStatus.NOT_FOUND
        
        # Perform analysis
        analysis_result = plot_thread_service.analyze_plot_thread(
            thread_id=thread_id,
            analysis_type=analysis_type,
            include_suggestions=include_suggestions,
            context_depth=context_depth
        )
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
        
    except Exception as e:
        current_app.logger.error(f"Error analyzing plot thread: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while analyzing plot thread'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@character_plot_bp.route('/plot-threads/<scene_id>/reminders', methods=['GET'])
@require_auth
def get_plot_reminders(scene_id):
    """Get reminders for stale plot threads.
    
    Query parameters:
        days_threshold (int): Days since last reference (default: 7)
        importance_threshold (float): Minimum importance for reminders (default: 0.4)
        limit (int): Maximum number of reminders (default: 10)
        
    Returns:
        200 OK: List of plot thread reminders
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 4.3 - Remind users of pending story elements
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    days_threshold = int(request.args.get('days_threshold', 7))
    importance_threshold = float(request.args.get('importance_threshold', 0.4))
    limit = min(int(request.args.get('limit', 10)), 50)
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Generate reminders
        reminders = plot_thread_service.generate_plot_reminders(
            scene_id=scene_id,
            days_threshold=days_threshold
        )
        
        # Filter by importance threshold
        important_reminders = [
            r for r in reminders 
            if r.importance_score >= importance_threshold
        ]
        
        # Apply limit
        limited_reminders = important_reminders[:limit]
        
        return jsonify({
            'success': True,
            'data': [
                {
                    'thread_id': r.thread_id,
                    'title': r.title,
                    'days_since_reference': r.days_since_reference,
                    'importance_score': r.importance_score,
                    'suggested_action': r.suggested_action,
                    'reminder_text': r.reminder_text
                }
                for r in limited_reminders
            ],
            'meta': {
                'scene_id': scene_id,
                'scene_name': scene.name,
                'total_reminders': len(reminders),
                'important_reminders': len(important_reminders),
                'returned': len(limited_reminders),
                'thresholds': {
                    'days': days_threshold,
                    'importance': importance_threshold
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting plot reminders: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving plot reminders'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@character_plot_bp.route('/plot-threads/<scene_id>/summary', methods=['GET'])
@require_auth
def get_plot_thread_summary(scene_id):
    """Get a summary of plot threads for a scene.
    
    Returns:
        200 OK: Plot thread summary statistics
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 4.4 - Plot thread overview and status tracking
    """
    init_services()
    current_user = get_current_identity()
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get plot thread summary
        summary = plot_thread_service.get_plot_thread_summary(scene_id)
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting plot thread summary: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving plot thread summary'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Character Consistency Checking Endpoints

@character_plot_bp.route('/character-consistency/<scene_id>/<character_name>/check', methods=['POST'])
@require_auth
def check_character_consistency(scene_id, character_name):
    """Check character consistency for a specific character.
    
    Request body:
    {
        "pose_text": "The character's pose content",  // Required
        "analysis_depth": 10,  // Optional, number of recent poses to analyze
        "consistency_types": ["voice", "behavior", "relationships"],  // Optional
        "include_suggestions": true  // Optional, default: true
    }
    
    Returns:
        200 OK: Character consistency analysis results
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 6.2 - Character behavior consistency checking
    """
    init_services()
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data or 'pose_text' not in data:
        return jsonify({
            'success': False,
            'message': 'pose_text is required'
        }), HTTPStatus.BAD_REQUEST
    
    pose_text = data.get('pose_text')
    analysis_depth = data.get('analysis_depth', 10)
    consistency_types = data.get('consistency_types', ['voice', 'behavior', 'relationships'])
    include_suggestions = data.get('include_suggestions', True)
    
    # Validate consistency types
    valid_types = ['voice', 'behavior', 'relationships', 'personality', 'emotions']
    invalid_types = [t for t in consistency_types if t not in valid_types]
    if invalid_types:
        return jsonify({
            'success': False,
            'message': f'Invalid consistency types: {", ".join(invalid_types)}'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Perform character consistency check
        consistency_result = character_state_service.check_character_consistency(
            scene_id=scene_id,
            character_name=character_name,
            pose_text=pose_text,
            analysis_depth=analysis_depth,
            consistency_types=consistency_types,
            include_suggestions=include_suggestions
        )
        
        return jsonify({
            'success': True,
            'data': consistency_result
        })
        
    except Exception as e:
        current_app.logger.error(f"Error checking character consistency: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while checking character consistency'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@character_plot_bp.route('/character-consistency/<scene_id>/<character_name>/history', methods=['GET'])
@require_auth
def get_character_consistency_history(scene_id, character_name):
    """Get character consistency history and trends.
    
    Query parameters:
        limit (int): Maximum number of consistency checks to return (default: 20)
        include_trends (bool): Include trend analysis (default: true)
        
    Returns:
        200 OK: Character consistency history and trends
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 6.2 - Character consistency tracking over time
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    limit = min(int(request.args.get('limit', 20)), 100)
    include_trends = request.args.get('include_trends', 'true').lower() == 'true'
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get consistency history
        history = character_state_service.get_character_consistency_history(
            scene_id=scene_id,
            character_name=character_name,
            limit=limit,
            include_trends=include_trends
        )
        
        return jsonify({
            'success': True,
            'data': history
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting character consistency history: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving character consistency history'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Character Relationship Tracking Endpoints

@character_plot_bp.route('/relationships/<scene_id>', methods=['GET'])
@require_auth
def get_character_relationships(scene_id):
    """Get character relationships for a scene.
    
    Query parameters:
        character_name (str): Filter by specific character (optional)
        relationship_type (str): Filter by relationship type (optional)
        include_history (bool): Include relationship history (default: false)
        min_interactions (int): Minimum interaction count (default: 1)
        
    Returns:
        200 OK: Character relationships data
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 5.1, 5.2 - Relationship tracking and updates
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    character_name = request.args.get('character_name')
    relationship_type = request.args.get('relationship_type')
    include_history = request.args.get('include_history', 'false').lower() == 'true'
    min_interactions = int(request.args.get('min_interactions', 1))
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get relationships
        relationships = character_state_service.get_scene_relationships(
            scene_id=scene_id,
            character_name=character_name,
            relationship_type=relationship_type,
            include_history=include_history,
            min_interactions=min_interactions
        )
        
        return jsonify({
            'success': True,
            'data': relationships,
            'meta': {
                'scene_id': scene_id,
                'scene_name': scene.name,
                'total_relationships': len(relationships),
                'filters': {
                    'character_name': character_name,
                    'relationship_type': relationship_type,
                    'min_interactions': min_interactions
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting character relationships: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving character relationships'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@character_plot_bp.route('/relationships/<scene_id>/<character1>/<character2>', methods=['GET'])
@require_auth
def get_character_relationship(scene_id, character1, character2):
    """Get detailed relationship information between two characters.
    
    Query parameters:
        include_history (bool): Include interaction history (default: true)
        include_analysis (bool): Include relationship analysis (default: false)
        
    Returns:
        200 OK: Detailed relationship information
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene or relationship doesn't exist
        
    Requirements: 5.1, 5.4 - Relationship details and context
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    include_history = request.args.get('include_history', 'true').lower() == 'true'
    include_analysis = request.args.get('include_analysis', 'false').lower() == 'true'
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get relationship details
        relationship = character_state_service.get_character_relationship(
            scene_id=scene_id,
            character1=character1,
            character2=character2,
            include_history=include_history,
            include_analysis=include_analysis
        )
        
        if not relationship:
            return jsonify({
                'success': False,
                'message': 'Relationship not found'
            }), HTTPStatus.NOT_FOUND
        
        return jsonify({
            'success': True,
            'data': relationship
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting character relationship: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving character relationship'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@character_plot_bp.route('/relationships/<scene_id>/<character1>/<character2>/analyze', methods=['POST'])
@require_auth
def analyze_character_relationship(scene_id, character1, character2):
    """Analyze relationship dynamics between two characters.
    
    Request body:
    {
        "analysis_type": "compatibility|conflict|development|all",  // Optional, default: all
        "context_depth": 10,  // Optional, number of interactions to analyze
        "include_suggestions": true  // Optional, default: true
    }
    
    Returns:
        200 OK: Relationship analysis results
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 5.3, 5.4 - Relationship analysis and context
    """
    init_services()
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    analysis_type = data.get('analysis_type', 'all')
    context_depth = data.get('context_depth', 10)
    include_suggestions = data.get('include_suggestions', True)
    
    # Validate analysis type
    valid_types = ['compatibility', 'conflict', 'development', 'all']
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
        
        # Perform relationship analysis
        analysis_result = character_state_service.analyze_character_relationship(
            scene_id=scene_id,
            character1=character1,
            character2=character2,
            analysis_type=analysis_type,
            context_depth=context_depth,
            include_suggestions=include_suggestions
        )
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
        
    except Exception as e:
        current_app.logger.error(f"Error analyzing character relationship: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while analyzing character relationship'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@character_plot_bp.route('/relationships/<scene_id>/detect-inconsistencies', methods=['POST'])
@require_auth
def detect_relationship_inconsistencies(scene_id):
    """Detect inconsistencies in character relationship portrayals.
    
    Request body:
    {
        "character_pairs": [["char1", "char2"], ["char1", "char3"]],  // Optional, all pairs if omitted
        "analysis_depth": 20,  // Optional, number of recent interactions to analyze
        "severity_threshold": "low"  // Optional, minimum severity to report
    }
    
    Returns:
        200 OK: Relationship inconsistency analysis
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 5.3 - Flag inconsistencies in relationship portrayals
    """
    init_services()
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    character_pairs = data.get('character_pairs')
    analysis_depth = data.get('analysis_depth', 20)
    severity_threshold = data.get('severity_threshold', 'low')
    
    # Validate severity threshold
    valid_severities = ['low', 'medium', 'high']
    if severity_threshold not in valid_severities:
        return jsonify({
            'success': False,
            'message': f'Invalid severity_threshold. Must be one of: {", ".join(valid_severities)}'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Detect inconsistencies
        inconsistencies = character_state_service.detect_relationship_inconsistencies(
            scene_id=scene_id,
            character_pairs=character_pairs,
            analysis_depth=analysis_depth,
            severity_threshold=severity_threshold
        )
        
        return jsonify({
            'success': True,
            'data': inconsistencies,
            'meta': {
                'scene_id': scene_id,
                'scene_name': scene.name,
                'analysis_depth': analysis_depth,
                'severity_threshold': severity_threshold,
                'total_inconsistencies': len(inconsistencies)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error detecting relationship inconsistencies: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while detecting relationship inconsistencies'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Character State Management Endpoints (Enhanced)

@character_plot_bp.route('/character-states/<scene_id>/<character_name>/profile', methods=['GET'])
@require_auth
def get_character_profile(scene_id, character_name):
    """Get comprehensive character profile for a scene.
    
    Query parameters:
        include_relationships (bool): Include relationship information (default: true)
        include_consistency (bool): Include consistency metrics (default: true)
        include_development (bool): Include character development tracking (default: false)
        
    Returns:
        200 OK: Comprehensive character profile
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene or character doesn't exist
        
    Requirements: 2.3, 2.4, 2.5 - Character profile and development tracking
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    include_relationships = request.args.get('include_relationships', 'true').lower() == 'true'
    include_consistency = request.args.get('include_consistency', 'true').lower() == 'true'
    include_development = request.args.get('include_development', 'false').lower() == 'true'
    
    try:
        # Verify scene exists and user has access
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Get character profile
        profile = character_state_service.get_character_profile(
            scene_id=scene_id,
            character_name=character_name,
            include_relationships=include_relationships,
            include_consistency=include_consistency,
            include_development=include_development
        )
        
        if not profile:
            return jsonify({
                'success': False,
                'message': 'Character profile not found'
            }), HTTPStatus.NOT_FOUND
        
        return jsonify({
            'success': True,
            'data': profile
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting character profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving character profile'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Health Check Endpoint

@character_plot_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for character and plot tracking service.
    
    Returns:
        200 OK: Service status and health information
    """
    try:
        # Check service availability
        services_status = {
            'character_state_service': 'healthy',
            'plot_thread_service': 'healthy',
            'continuity_service': 'healthy',
            'ai_client': 'healthy' if ai_client else 'unavailable'
        }
        
        # Check database connectivity
        from app.models.scene_memory import PlotThread
        try:
            PlotThread.get_collection().find_one({})
            services_status['database'] = 'healthy'
        except Exception:
            services_status['database'] = 'unavailable'
        
        overall_status = 'healthy' if all(
            status == 'healthy' for status in services_status.values()
        ) else 'degraded'
        
        return jsonify({
            'success': True,
            'service': 'character_plot_tracking_api',
            'status': overall_status,
            'services': services_status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'service': 'character_plot_tracking_api',
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), HTTPStatus.INTERNAL_SERVER_ERROR 