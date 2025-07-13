"""
Context analysis API endpoints for MUSH Pose Editor.

Provides endpoints for pose context analysis and response suggestions.
"""
from flask import Blueprint, request, jsonify
from app.services.context_service import ContextService
from app.services.venice_client import VeniceClient, VeniceAPIError

# Create blueprint
context_bp = Blueprint('context', __name__)

# Global service instance for testing compatibility
context_service = None


def get_context_service():
    """Get context service instance."""
    global context_service
    if context_service is None:
        import os
        api_key = os.getenv('VENICE_API_KEY')
        if not api_key:
            raise ValueError("VENICE_API_KEY environment variable is required")
        venice_client = VeniceClient(api_key=api_key)
        context_service = ContextService(venice_client)
    return context_service


@context_bp.route('/analyze', methods=['POST'])
def analyze_pose_context():
    """Analyze a pose to extract context for response crafting.
    
    Request body:
    {
        "pose_text": "The pose text to analyze...",
        "character_name": "Optional character name for perspective"
    }
    
    Returns:
    {
        "success": true,
        "context": {
            "actions": [...],
            "emotions": [...],
            "environmental_details": [...],
            "character_interactions": [...],
            "response_hooks": [...],
            "scene_timing": "...",
            "urgency_level": "...",
            "narrative_tone": "..."
        },
        "suggestions": [...]
    }
    """
    try:
        # Get request data
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        pose_text = data.get('pose_text')
        if not pose_text or not pose_text.strip():
            return jsonify({
                'success': False,
                'error': 'pose_text is required and cannot be empty'
            }), 400
        
        character_name = data.get('character_name')
        
        # Analyze the pose context
        service = get_context_service()
        context = service.analyze_pose_context(pose_text, character_name)
        
        # Get response suggestions
        suggestions = service.get_response_suggestions(context, character_name)
        
        return jsonify({
            'success': True,
            'context': context.to_dict(),
            'suggestions': suggestions
        })
        
    except VeniceAPIError as e:
        return jsonify({
            'success': False,
            'error': f'AI processing failed: {str(e)}'
        }), 503
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid data: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@context_bp.route('/analyze-multiple', methods=['POST'])
def analyze_multiple_poses():
    """Analyze multiple poses and return context for each.
    
    Request body:
    {
        "poses": ["pose1", "pose2", ...],
        "character_name": "Optional character name for perspective"
    }
    
    Returns:
    {
        "success": true,
        "results": {
            "pose_0": {...},
            "pose_1": {...},
            ...
        }
    }
    """
    try:
        # Get request data
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        poses = data.get('poses')
        if not poses or not isinstance(poses, list):
            return jsonify({
                'success': False,
                'error': 'poses must be a non-empty list'
            }), 400
        
        if len(poses) > 10:  # Limit to prevent abuse
            return jsonify({
                'success': False,
                'error': 'Maximum 10 poses allowed per request'
            }), 400
        
        character_name = data.get('character_name')
        
        # Analyze multiple poses
        service = get_context_service()
        results = service.analyze_multiple_poses(poses, character_name)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except VeniceAPIError as e:
        return jsonify({
            'success': False,
            'error': f'AI processing failed: {str(e)}'
        }), 503
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid data: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@context_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@context_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405 