"""
Search and Summary API endpoints for Scene Memory & Continuity Tracking.

Provides comprehensive endpoints for scene search, pose search, character search,
timeline search, summary generation, and export functionality.
"""
from flask import Blueprint, request, jsonify, current_app, Response
from http import HTTPStatus
from datetime import datetime, timedelta
import json
import csv
import io
from typing import Dict, Any, List, Optional

from app.services.search_service import SearchService
from app.services.summary_service import SummaryService, SummaryOptions
from app.services.scene_service import SceneService
from app.services.ai_client import AIClient
from app.middleware.auth_middleware import require_auth, get_current_identity
from app.models.scene import Scene
from app.models.scene_memory import SceneMemory

# Create blueprint
search_summary_bp = Blueprint('search_summary', __name__)

# Initialize services with lazy initialization


def get_ai_client():
    """Get OpenRouter client with proper API key handling."""
    import os
    api_key = os.getenv('OPENROUTER_API_KEY', 'test-key')
    return AIClient(api_key=api_key)


# Initialize services
ai_client = None
search_service = None
summary_service = None


def init_services():
    """Initialize services lazily."""
    global ai_client, search_service, summary_service
    if ai_client is None:
        ai_client = get_ai_client()
        search_service = SearchService()
        summary_service = SummaryService()


# Scene Search Endpoints

@search_summary_bp.route('/search/scenes', methods=['GET'])
@require_auth
def search_scenes():
    """Search for scenes with comprehensive filtering capabilities.
    
    Query parameters:
        q (str): Search query text (optional)
        active (bool): Filter by active status (default: true)
        start_date (str): Start date filter in ISO format (optional)
        end_date (str): End date filter in ISO format (optional)
        participants (str): Comma-separated character IDs (optional)
        tags (str): Comma-separated tags (optional)
        limit (int): Maximum number of results (default: 20, max: 100)
        skip (int): Number of results to skip for pagination (default: 0)
        sort (str): Sort field - relevance, created_at, updated_at, name (default: relevance)
        order (str): Sort order - asc or desc (default: desc)
        
    Returns:
        200 OK: List of search results with metadata
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        
    Requirements: 7.1, 7.2 - Full-text search with filtering
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    query = request.args.get('q', '')
    active = request.args.get('active', 'true').lower() == 'true'
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    participants = request.args.get('participants')
    tags = request.args.get('tags')
    limit = min(int(request.args.get('limit', 20)), 100)
    skip = max(0, int(request.args.get('skip', 0)))
    sort_field = request.args.get('sort', 'relevance')
    sort_order = request.args.get('order', 'desc')
    
    # Validate sort field
    valid_sort_fields = ['relevance', 'created_at', 'updated_at', 'name']
    if sort_field not in valid_sort_fields:
        return jsonify({
            'success': False,
            'message': f'Invalid sort field. Must be one of: {", ".join(valid_sort_fields)}'
        }), HTTPStatus.BAD_REQUEST
    
    # Build filters
    filters = {}
    
    # Active status filter
    if active is not None:
        filters['is_active'] = active
    
    # Date range filter
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
    
    # Participants filter
    if participants:
        filters['participants'] = [p.strip() for p in participants.split(',')]
    
    # Tags filter
    if tags:
        filters['tags'] = [t.strip() for t in tags.split(',')]
    
    try:
        # Perform search
        results = search_service.search_scenes(
            query=query,
            user_id=current_user,
            filters=filters,
            limit=limit,
            skip=skip,
            sort_field=sort_field,
            sort_direction=-1 if sort_order == 'desc' else 1
        )
        
        # Build response
        return jsonify({
            'success': True,
            'data': [result.to_dict() for result in results],
            'meta': {
                'query': query,
                'total_results': len(results),
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


@search_summary_bp.route('/search/poses', methods=['GET'])
@require_auth
def search_poses():
    """Search for poses with comprehensive filtering capabilities.
    
    Query parameters:
        q (str): Search query text (optional)
        scene_id (str): Filter by specific scene ID (optional)
        character_id (str): Filter by specific character ID (optional)
        pose_type (str): Filter by pose type (optional)
        start_date (str): Start date filter in ISO format (optional)
        end_date (str): End date filter in ISO format (optional)
        tags (str): Comma-separated tags (optional)
        limit (int): Maximum number of results (default: 20, max: 100)
        skip (int): Number of results to skip for pagination (default: 0)
        
    Returns:
        200 OK: List of pose search results with metadata
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        
    Requirements: 7.1, 7.2 - Full-text search across poses
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    query = request.args.get('q', '')
    scene_id = request.args.get('scene_id')
    character_id = request.args.get('character_id')
    pose_type = request.args.get('pose_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    tags = request.args.get('tags')
    limit = min(int(request.args.get('limit', 20)), 100)
    skip = max(0, int(request.args.get('skip', 0)))
    
    # Build filters
    filters = {}
    
    # Pose type filter
    if pose_type:
        filters['pose_type'] = pose_type
    
    # Date range filter
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
    
    # Tags filter
    if tags:
        filters['tags'] = [t.strip() for t in tags.split(',')]
    
    try:
        # Perform search
        results = search_service.search_poses(
            query=query,
            scene_id=scene_id,
            user_id=current_user,
            character_id=character_id,
            filters=filters,
            limit=limit,
            skip=skip
        )
        
        # Build response
        return jsonify({
            'success': True,
            'data': [result.to_dict() for result in results],
            'meta': {
                'query': query,
                'scene_id': scene_id,
                'character_id': character_id,
                'total_results': len(results),
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


@search_summary_bp.route('/search/characters', methods=['GET'])
@require_auth
def search_characters():
    """Search for characters with filtering capabilities.
    
    Query parameters:
        q (str): Search query text (optional)
        scene_id (str): Filter by specific scene ID (optional)
        limit (int): Maximum number of results (default: 20, max: 100)
        skip (int): Number of results to skip for pagination (default: 0)
        
    Returns:
        200 OK: List of character search results with metadata
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        
    Requirements: 7.2 - Character-specific search
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    query = request.args.get('q', '')
    scene_id = request.args.get('scene_id')
    limit = min(int(request.args.get('limit', 20)), 100)
    skip = max(0, int(request.args.get('skip', 0)))
    
    try:
        # Perform search
        results = search_service.search_characters(
            query=query,
            scene_id=scene_id,
            user_id=current_user,
            limit=limit,
            skip=skip
        )
        
        # Build response
        return jsonify({
            'success': True,
            'data': [result.to_dict() for result in results],
            'meta': {
                'query': query,
                'scene_id': scene_id,
                'total_results': len(results),
                'limit': limit,
                'skip': skip
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error searching characters: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while searching characters'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@search_summary_bp.route('/search/plot-elements', methods=['GET'])
@require_auth
def search_plot_elements():
    """Search for plot elements within scenes.
    
    Query parameters:
        q (str): Search query text (required)
        scene_id (str): Scene ID to search within (required)
        limit (int): Maximum number of results (default: 20, max: 100)
        skip (int): Number of results to skip for pagination (default: 0)
        
    Returns:
        200 OK: List of plot element search results with metadata
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        
    Requirements: 7.3 - Plot keyword search
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    query = request.args.get('q')
    scene_id = request.args.get('scene_id')
    limit = min(int(request.args.get('limit', 20)), 100)
    skip = max(0, int(request.args.get('skip', 0)))
    
    # Validate required parameters
    if not query:
        return jsonify({
            'success': False,
            'message': 'Query parameter q is required'
        }), HTTPStatus.BAD_REQUEST
    
    if not scene_id:
        return jsonify({
            'success': False,
            'message': 'Query parameter scene_id is required'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Perform search
        results = search_service.search_plot_elements(
            query=query,
            scene_id=scene_id,
            user_id=current_user,
            limit=limit,
            skip=skip
        )
        
        # Build response
        return jsonify({
            'success': True,
            'data': [result.to_dict() for result in results],
            'meta': {
                'query': query,
                'scene_id': scene_id,
                'total_results': len(results),
                'limit': limit,
                'skip': skip
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error searching plot elements: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while searching plot elements'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@search_summary_bp.route('/search/timeline', methods=['GET'])
@require_auth
def search_timeline():
    """Search for events in timeline format with date-based filtering.
    
    Query parameters:
        q (str): Search query text (optional)
        scene_id (str): Filter by specific scene ID (optional)
        character_id (str): Filter by specific character ID (optional)
        start_date (str): Start date filter in ISO format (optional)
        end_date (str): End date filter in ISO format (optional)
        event_types (str): Comma-separated event types (optional)
        limit (int): Maximum number of results (default: 50, max: 200)
        skip (int): Number of results to skip for pagination (default: 0)
        
    Returns:
        200 OK: List of timeline events with metadata
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        
    Requirements: 7.4 - Timeline search with date filtering
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    query = request.args.get('q', '')
    scene_id = request.args.get('scene_id')
    character_id = request.args.get('character_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    event_types = request.args.get('event_types')
    limit = min(int(request.args.get('limit', 50)), 200)
    skip = max(0, int(request.args.get('skip', 0)))
    
    # Parse date filters
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid start_date format. Use ISO format.'
            }), HTTPStatus.BAD_REQUEST
    
    if end_date:
        try:
            end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid end_date format. Use ISO format.'
            }), HTTPStatus.BAD_REQUEST
    
    # Parse event types
    event_types_list = None
    if event_types:
        event_types_list = [t.strip() for t in event_types.split(',')]
    
    try:
        # Perform timeline search
        results = search_service.search_timeline(
            query=query,
            scene_id=scene_id,
            user_id=current_user,
            character_id=character_id,
            start_date=start_date_obj,
            end_date=end_date_obj,
            event_types=event_types_list,
            limit=limit,
            skip=skip
        )
        
        # Build response
        return jsonify({
            'success': True,
            'data': results,
            'meta': {
                'query': query,
                'scene_id': scene_id,
                'character_id': character_id,
                'total_results': len(results),
                'limit': limit,
                'skip': skip,
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'event_types': event_types_list
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error searching timeline: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while searching timeline'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Scene Summary Generation Endpoints

@search_summary_bp.route('/summaries/scenes/<scene_id>', methods=['POST'])
@require_auth
def generate_scene_summary(scene_id):
    """Generate a summary for a specific scene.
    
    Request body:
    {
        "focus": "comprehensive|character|plot|environment",  // Optional, default: comprehensive
        "character_id": "char_id",  // Required if focus is 'character'
        "max_length": 500,  // Optional, default: 500 words
        "include_details": true,  // Optional, default: true
        "formal_style": false,  // Optional, default: false
        "chronological": true,  // Optional, default: true
        "highlight_key_events": true  // Optional, default: true
    }
    
    Returns:
        200 OK: Generated scene summary
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 8.1, 8.2 - Scene summary generation
    """
    init_services()
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    # Build summary options
    options = SummaryOptions(
        focus=data.get('focus', 'comprehensive'),
        character_id=data.get('character_id'),
        max_length=data.get('max_length', 500),
        include_details=data.get('include_details', True),
        formal_style=data.get('formal_style', False),
        chronological=data.get('chronological', True),
        highlight_key_events=data.get('highlight_key_events', True)
    )
    
    # Validate focus and character_id combination
    if options.focus == 'character' and not options.character_id:
        return jsonify({
            'success': False,
            'message': 'character_id is required when focus is set to character'
        }), HTTPStatus.BAD_REQUEST
    
    # Validate focus value
    valid_focus_values = ['comprehensive', 'character', 'plot', 'environment']
    if options.focus not in valid_focus_values:
        return jsonify({
            'success': False,
            'message': f'Invalid focus value. Must be one of: {", ".join(valid_focus_values)}'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Generate summary
        summary = summary_service.generate_summary(
            scene_id=scene_id,
            user_id=current_user,
            options=options
        )
        
        if not summary:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Build response
        return jsonify({
            'success': True,
            'data': {
                'scene_id': summary.scene_id,
                'summary_text': summary.summary_text,
                'summary_type': summary.summary_type,
                'generated_at': summary.generated_at.isoformat(),
                'metadata': summary.metadata,
                'options': options.__dict__
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating scene summary: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while generating scene summary'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@search_summary_bp.route('/summaries/scenes/<scene_id>/catchup', methods=['POST'])
@require_auth
def generate_catchup_brief(scene_id):
    """Generate a catch-up brief for recent activity in a scene.
    
    Request body:
    {
        "since_timestamp": "2024-01-01T00:00:00Z",  // Optional, defaults to 24 hours ago
        "max_length": 300,  // Optional, default: 300 words
        "include_details": true,  // Optional, default: true
        "highlight_key_events": true  // Optional, default: true
    }
    
    Returns:
        200 OK: Generated catch-up brief
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 8.3 - Catch-up brief generation
    """
    init_services()
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    # Parse since_timestamp
    since_timestamp = None
    if 'since_timestamp' in data:
        try:
            since_timestamp = datetime.fromisoformat(data['since_timestamp'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid since_timestamp format. Use ISO format.'
            }), HTTPStatus.BAD_REQUEST
    else:
        # Default to 24 hours ago
        since_timestamp = datetime.utcnow() - timedelta(hours=24)
    
    # Build summary options
    options = SummaryOptions(
        focus='comprehensive',
        max_length=data.get('max_length', 300),
        include_details=data.get('include_details', True),
        highlight_key_events=data.get('highlight_key_events', True)
    )
    
    try:
        # Generate catchup brief
        summary = summary_service.generate_catchup_brief(
            scene_id=scene_id,
            user_id=current_user,
            since_timestamp=since_timestamp,
            options=options
        )
        
        if not summary:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Build response
        return jsonify({
            'success': True,
            'data': {
                'scene_id': summary.scene_id,
                'summary_text': summary.summary_text,
                'summary_type': summary.summary_type,
                'generated_at': summary.generated_at.isoformat(),
                'metadata': summary.metadata,
                'since_timestamp': since_timestamp.isoformat(),
                'options': options.__dict__
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating catchup brief: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while generating catchup brief'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@search_summary_bp.route('/summaries/scenes/<scene_id>/character/<character_id>', methods=['POST'])
@require_auth
def generate_character_summary(scene_id, character_id):
    """Generate a character-focused summary for a scene.
    
    Request body:
    {
        "max_length": 400,  // Optional, default: 400 words
        "include_details": true,  // Optional, default: true
        "chronological": true,  // Optional, default: true
        "highlight_key_events": true  // Optional, default: true
    }
    
    Returns:
        200 OK: Generated character-focused summary
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 8.2 - Character-focused summaries
    """
    init_services()
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    # Build summary options
    options = SummaryOptions(
        focus='character',
        character_id=character_id,
        max_length=data.get('max_length', 400),
        include_details=data.get('include_details', True),
        chronological=data.get('chronological', True),
        highlight_key_events=data.get('highlight_key_events', True)
    )
    
    try:
        # Generate character-focused summary
        summary = summary_service.generate_character_focused_summary(
            scene_id=scene_id,
            user_id=current_user,
            character_id=character_id,
            options=options
        )
        
        if not summary:
            return jsonify({
                'success': False,
                'message': 'Scene or character not found, or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Build response
        return jsonify({
            'success': True,
            'data': {
                'scene_id': summary.scene_id,
                'summary_text': summary.summary_text,
                'summary_type': summary.summary_type,
                'generated_at': summary.generated_at.isoformat(),
                'metadata': summary.metadata,
                'character_id': character_id,
                'options': options.__dict__
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating character summary: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while generating character summary'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@search_summary_bp.route('/summaries/scenes/<scene_id>/plot', methods=['POST'])
@require_auth
def generate_plot_summary(scene_id):
    """Generate a plot-focused summary for a scene.
    
    Request body:
    {
        "max_length": 400,  // Optional, default: 400 words
        "include_details": true,  // Optional, default: true
        "chronological": true,  // Optional, default: true
        "highlight_key_events": true  // Optional, default: true
    }
    
    Returns:
        200 OK: Generated plot-focused summary
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 8.2 - Plot-focused summaries
    """
    init_services()
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        data = {}
    
    # Build summary options
    options = SummaryOptions(
        focus='plot',
        max_length=data.get('max_length', 400),
        include_details=data.get('include_details', True),
        chronological=data.get('chronological', True),
        highlight_key_events=data.get('highlight_key_events', True)
    )
    
    try:
        # Generate plot-focused summary
        summary = summary_service.generate_summary(
            scene_id=scene_id,
            user_id=current_user,
            options=options
        )
        
        if not summary:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Build response
        return jsonify({
            'success': True,
            'data': {
                'scene_id': summary.scene_id,
                'summary_text': summary.summary_text,
                'summary_type': summary.summary_type,
                'generated_at': summary.generated_at.isoformat(),
                'metadata': summary.metadata,
                'options': options.__dict__
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating plot summary: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while generating plot summary'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Export Functionality Endpoints

@search_summary_bp.route('/export/scenes/<scene_id>', methods=['GET'])
@require_auth
def export_scene_data(scene_id):
    """Export scene data in various formats.
    
    Query parameters:
        format (str): Export format - json, csv, txt (default: json)
        include_poses (bool): Include pose data (default: true)
        include_metadata (bool): Include metadata (default: true)
        include_summaries (bool): Include summaries if available (default: false)
        
    Returns:
        200 OK: Scene data in requested format
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        403 Forbidden: If not authorized to access the scene
        404 Not Found: If scene doesn't exist
        
    Requirements: 8.4 - Export functionality for scene data
    """
    init_services()
    current_user = get_current_identity()
    
    # Get query parameters
    export_format = request.args.get('format', 'json').lower()
    include_poses = request.args.get('include_poses', 'true').lower() == 'true'
    include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
    include_summaries = request.args.get('include_summaries', 'false').lower() == 'true'
    
    # Validate format
    valid_formats = ['json', 'csv', 'txt']
    if export_format not in valid_formats:
        return jsonify({
            'success': False,
            'message': f'Invalid format. Must be one of: {", ".join(valid_formats)}'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Get scene data
        scene = SceneService.get_scene(scene_id=scene_id, user_id=current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        # Build export data
        export_data = {
            'scene_id': scene.id,
            'name': scene.name,
            'description': scene.description,
            'created_at': scene.created_at.isoformat(),
            'updated_at': scene.updated_at.isoformat(),
            'is_active': scene.is_active
        }
        
        # Add poses if requested
        if include_poses and hasattr(scene, 'poses'):
            export_data['poses'] = []
            for pose in scene.poses:
                pose_data = {
                    'character_name': pose.character_name,
                    'character_id': getattr(pose, 'character_id', ''),
                    'pose_text': pose.pose_text,
                    'pose_type': pose.pose_type.value if hasattr(pose, 'pose_type') else 'mixed',
                    'timestamp': pose.timestamp.isoformat() if hasattr(pose, 'timestamp') and pose.timestamp else '',
                    'tags': getattr(pose, 'tags', [])
                }
                export_data['poses'].append(pose_data)
        
        # Add metadata if requested
        if include_metadata:
            export_data['metadata'] = {
                'created_by': getattr(scene, 'created_by', ''),
                'participant_count': len(getattr(scene, 'participants', [])),
                'pose_count': len(getattr(scene, 'poses', [])),
                'exported_at': datetime.utcnow().isoformat(),
                'exported_by': current_user
            }
        
        # Add summaries if requested
        if include_summaries:
            export_data['summaries'] = []
            # Note: In a real implementation, you would retrieve stored summaries
            # For now, we'll just include a placeholder
            export_data['summaries'] = []
        
        # Format and return data
        if export_format == 'json':
            return jsonify({
                'success': True,
                'data': export_data
            })
        
        elif export_format == 'csv':
            # Create CSV format for poses
            if include_poses and 'poses' in export_data:
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(['Scene Name', 'Character Name', 'Character ID', 'Pose Text', 'Pose Type', 'Timestamp', 'Tags'])
                
                # Write pose data
                for pose in export_data['poses']:
                    writer.writerow([
                        export_data['name'],
                        pose['character_name'],
                        pose['character_id'],
                        pose['pose_text'],
                        pose['pose_type'],
                        pose['timestamp'],
                        ', '.join(pose['tags'])
                    ])
                
                csv_data = output.getvalue()
                output.close()
                
                return Response(
                    csv_data,
                    mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename=scene_{scene_id}.csv'}
                )
            else:
                return jsonify({
                    'success': False,
                    'message': 'CSV export requires pose data to be included'
                }), HTTPStatus.BAD_REQUEST
        
        elif export_format == 'txt':
            # Create text format
            text_lines = []
            text_lines.append(f"Scene: {export_data['name']}")
            text_lines.append(f"Description: {export_data['description']}")
            text_lines.append(f"Created: {export_data['created_at']}")
            text_lines.append("-" * 50)
            
            if include_poses and 'poses' in export_data:
                text_lines.append("Poses:")
                text_lines.append("")
                
                for i, pose in enumerate(export_data['poses'], 1):
                    text_lines.append(f"{i}. {pose['character_name']} ({pose['pose_type']})")
                    if pose['timestamp']:
                        text_lines.append(f"   Time: {pose['timestamp']}")
                    text_lines.append(f"   {pose['pose_text']}")
                    if pose['tags']:
                        text_lines.append(f"   Tags: {', '.join(pose['tags'])}")
                    text_lines.append("")
            
            text_content = '\n'.join(text_lines)
            
            return Response(
                text_content,
                mimetype='text/plain',
                headers={'Content-Disposition': f'attachment; filename=scene_{scene_id}.txt'}
            )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting scene data: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while exporting scene data'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@search_summary_bp.route('/export/search-results', methods=['POST'])
@require_auth
def export_search_results():
    """Export search results in various formats.
    
    Request body:
    {
        "search_type": "scenes|poses|characters|timeline",  // Required
        "search_params": {  // Search parameters as used in search endpoints
            "q": "search query",
            "scene_id": "scene_id",
            "limit": 100
        },
        "format": "json|csv|txt",  // Optional, default: json
        "include_metadata": true  // Optional, default: true
    }
    
    Returns:
        200 OK: Search results in requested format
        400 Bad Request: If validation fails
        401 Unauthorized: If not authenticated
        
    Requirements: 8.5 - Export functionality for search results
    """
    init_services()
    current_user = get_current_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'Request body is required'
        }), HTTPStatus.BAD_REQUEST
    
    # Get parameters
    search_type = data.get('search_type')
    search_params = data.get('search_params', {})
    export_format = data.get('format', 'json').lower()
    include_metadata = data.get('include_metadata', True)
    
    # Validate search type
    valid_search_types = ['scenes', 'poses', 'characters', 'timeline']
    if search_type not in valid_search_types:
        return jsonify({
            'success': False,
            'message': f'Invalid search_type. Must be one of: {", ".join(valid_search_types)}'
        }), HTTPStatus.BAD_REQUEST
    
    # Validate format
    valid_formats = ['json', 'csv', 'txt']
    if export_format not in valid_formats:
        return jsonify({
            'success': False,
            'message': f'Invalid format. Must be one of: {", ".join(valid_formats)}'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Perform search based on type
        results = []
        
        if search_type == 'scenes':
            results = search_service.search_scenes(
                query=search_params.get('q', ''),
                user_id=current_user,
                filters=search_params.get('filters', {}),
                limit=search_params.get('limit', 100),
                skip=search_params.get('skip', 0)
            )
        
        elif search_type == 'poses':
            results = search_service.search_poses(
                query=search_params.get('q', ''),
                scene_id=search_params.get('scene_id'),
                user_id=current_user,
                character_id=search_params.get('character_id'),
                filters=search_params.get('filters', {}),
                limit=search_params.get('limit', 100),
                skip=search_params.get('skip', 0)
            )
        
        elif search_type == 'characters':
            results = search_service.search_characters(
                query=search_params.get('q', ''),
                scene_id=search_params.get('scene_id'),
                user_id=current_user,
                limit=search_params.get('limit', 100),
                skip=search_params.get('skip', 0)
            )
        
        elif search_type == 'timeline':
            results = search_service.search_timeline(
                query=search_params.get('q', ''),
                scene_id=search_params.get('scene_id'),
                user_id=current_user,
                character_id=search_params.get('character_id'),
                start_date=search_params.get('start_date'),
                end_date=search_params.get('end_date'),
                event_types=search_params.get('event_types'),
                limit=search_params.get('limit', 100),
                skip=search_params.get('skip', 0)
            )
        
        # Build export data
        export_data = {
            'search_type': search_type,
            'search_params': search_params,
            'results': [result.to_dict() if hasattr(result, 'to_dict') else result for result in results],
            'total_results': len(results)
        }
        
        if include_metadata:
            export_data['metadata'] = {
                'exported_at': datetime.utcnow().isoformat(),
                'exported_by': current_user,
                'search_type': search_type
            }
        
        # Format and return data
        if export_format == 'json':
            return jsonify({
                'success': True,
                'data': export_data
            })
        
        elif export_format == 'csv':
            # Create CSV format
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header based on search type
            if search_type == 'scenes':
                writer.writerow(['Scene ID', 'Scene Name', 'Content Preview', 'Relevance Score', 'Timestamp', 'Created By'])
            elif search_type == 'poses':
                writer.writerow(['Scene ID', 'Scene Name', 'Character Name', 'Content Preview', 'Relevance Score', 'Timestamp', 'Pose Type'])
            elif search_type == 'characters':
                writer.writerow(['Character ID', 'Character Name', 'Content Preview', 'Relevance Score', 'Scene Count'])
            elif search_type == 'timeline':
                writer.writerow(['Event ID', 'Event Type', 'Title', 'Content', 'Timestamp', 'Character Name'])
            
            # Write data rows
            for result in export_data['results']:
                if search_type == 'scenes':
                    writer.writerow([
                        result.get('item_id', ''),
                        result.get('metadata', {}).get('name', ''),
                        result.get('content_preview', ''),
                        result.get('relevance_score', 0),
                        result.get('timestamp', ''),
                        result.get('metadata', {}).get('created_by', '')
                    ])
                elif search_type == 'poses':
                    writer.writerow([
                        result.get('metadata', {}).get('scene_id', ''),
                        result.get('metadata', {}).get('scene_name', ''),
                        result.get('metadata', {}).get('character_name', ''),
                        result.get('content_preview', ''),
                        result.get('relevance_score', 0),
                        result.get('timestamp', ''),
                        result.get('metadata', {}).get('pose_type', '')
                    ])
                elif search_type == 'characters':
                    writer.writerow([
                        result.get('item_id', ''),
                        result.get('metadata', {}).get('name', ''),
                        result.get('content_preview', ''),
                        result.get('relevance_score', 0),
                        result.get('metadata', {}).get('scene_count', 0)
                    ])
                elif search_type == 'timeline':
                    writer.writerow([
                        result.get('id', ''),
                        result.get('type', ''),
                        result.get('title', ''),
                        result.get('content', ''),
                        result.get('timestamp', ''),
                        result.get('character_name', '')
                    ])
            
            csv_data = output.getvalue()
            output.close()
            
            return Response(
                csv_data,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={search_type}_search_results.csv'}
            )
        
        elif export_format == 'txt':
            # Create text format
            text_lines = []
            text_lines.append(f"Search Results: {search_type}")
            text_lines.append(f"Total Results: {len(results)}")
            text_lines.append(f"Exported: {datetime.utcnow().isoformat()}")
            text_lines.append("-" * 50)
            
            for i, result in enumerate(export_data['results'], 1):
                text_lines.append(f"{i}. {result.get('item_id', 'N/A')}")
                text_lines.append(f"   Type: {result.get('item_type', 'N/A')}")
                text_lines.append(f"   Preview: {result.get('content_preview', 'N/A')}")
                text_lines.append(f"   Score: {result.get('relevance_score', 0)}")
                text_lines.append(f"   Time: {result.get('timestamp', 'N/A')}")
                text_lines.append("")
            
            text_content = '\n'.join(text_lines)
            
            return Response(
                text_content,
                mimetype='text/plain',
                headers={'Content-Disposition': f'attachment; filename={search_type}_search_results.txt'}
            )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting search results: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while exporting search results'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# Health Check Endpoint

@search_summary_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for search and summary service.
    
    Returns:
        200 OK: Service status and health information
    """
    try:
        # Check service availability
        services_status = {
            'search_service': 'healthy',
            'summary_service': 'healthy',
            'ai_client': 'healthy' if ai_client else 'unavailable'
        }
        
        # Check database connectivity
        from app.models.scene import Scene
        try:
            Scene.get_collection().find_one({})
            services_status['database'] = 'healthy'
        except Exception:
            services_status['database'] = 'unavailable'
        
        overall_status = 'healthy' if all(
            status == 'healthy' for status in services_status.values()
        ) else 'degraded'
        
        return jsonify({
            'success': True,
            'service': 'search_summary_api',
            'status': overall_status,
            'services': services_status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'service': 'search_summary_api',
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), HTTPStatus.INTERNAL_SERVER_ERROR 