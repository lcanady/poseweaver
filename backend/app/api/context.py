"""
Context analysis API endpoints for MUSH Pose Editor.

Provides endpoints for pose context analysis and response suggestions.
"""
from flask import Blueprint, request, jsonify
from app.services.context_service import ContextService
from app.services.openrouter_client import OpenRouterClient, OpenRouterAPIError

# Create blueprint
context_bp = Blueprint('context', __name__)

# Global service instance for testing compatibility
context_service = None


@context_bp.route('/', methods=['GET'])
def get_context():
    """Get context API information.
    
    Returns:
    {
        "success": true,
        "info": "Context API information",
        "endpoints": [list of available endpoints]
    }
    """
    endpoints = [
        {
            "path": "/analyze",
            "method": "POST",
            "description": "Analyze a pose to extract context for response crafting"
        },
        {
            "path": "/analyze-multiple", 
            "method": "POST",
            "description": "Analyze multiple poses and return context for each"
        }
    ]
    
    return jsonify({
        'success': True,
        'info': 'Context analysis API for MUSH Pose Editor',
        'endpoints': endpoints
    })


def get_context_service():
    """Get context service instance."""
    global context_service
    if context_service is None:
        import os
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        openrouter_client = OpenRouterClient(api_key=api_key)
        context_service = ContextService(openrouter_client)
    return context_service


@context_bp.route('/analyze', methods=['POST'])
def analyze_pose_context():
    """Analyze a pose to extract context for response crafting.
    
    Request body:
    {
        "poses": [
            {
                "character_name": "Character Name",
                "content": "The pose content..."
            }
        ],
        "character_name": "Optional character name for perspective"
    }
    OR (legacy support):
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
        
        character_name = data.get('character_name')
        service = get_context_service()
        
        # Check if poses are provided (new format)
        poses = data.get('poses')
        if poses and isinstance(poses, list):
            # Validate poses structure
            for pose in poses:
                if not isinstance(pose, dict):
                    return jsonify({
                        'success': False,
                        'error': 'Each pose must be a dictionary'
                    }), 400
                if not pose.get('character_name') or not pose.get('content'):
                    return jsonify({
                        'success': False,
                        'error': 'Each pose must have character_name and content'
                    }), 400
            
            # Analyze poses using the new method
            context = service.analyze_poses_context(poses, character_name)
        else:
            # Legacy support: analyze pose_text
            pose_text = data.get('pose_text')
            if not pose_text or not pose_text.strip():
                return jsonify({
                    'success': False,
                    'error': 'poses array or pose_text is required'
                }), 400
            
            # Analyze using the old method
            context = service.analyze_pose_context(pose_text, character_name)
        
        # Get response suggestions
        suggestions = service.get_response_suggestions(context, character_name)
        
        return jsonify({
            'success': True,
            'context': context.to_dict(),
            'suggestions': suggestions
        })
        
    except OpenRouterAPIError as e:
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
            'error': f'An unexpected error occurred: {str(e)}'
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
        
    except OpenRouterAPIError as e:
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