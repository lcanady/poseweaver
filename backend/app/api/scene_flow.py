"""
Scene flow API endpoints for managing roleplay scene conversation flows.

This module provides REST API endpoints for creating, managing, and
interacting with scene flows that track the conversation-like flow of poses
in roleplay scenes.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
import os

from app.services.scene_flow_service import SceneFlowService
from app.services.openrouter_client import OpenRouterClient, OpenRouterAPIError
from app.models.scene_flow import PoseType
from app.middleware.auth_middleware import require_auth

# Create blueprint
scene_flow_bp = Blueprint('scene_flow', __name__, url_prefix='/api/scene-flow')

# Initialize service with proper API key from environment
openrouter_api_key = os.getenv('OPENROUTER_API_KEY', '')
openrouter_client = OpenRouterClient(openrouter_api_key)
scene_flow_service = SceneFlowService(openrouter_client)


@scene_flow_bp.route('/scenes', methods=['POST'])
@require_auth
def create_scene():
    """Create a new scene flow.
    
    Expected JSON body:
    {
        "name": "Scene name",
        "character_name": "Main character name"
    }
    
    Returns:
        JSON response with created scene data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        name = data.get('name')
        character_name = data.get('character_name')
        
        if not name or not character_name:
            return jsonify({
                'error': 'Both name and character_name are required'
            }), 400
        
        # Create the scene
        scene = scene_flow_service.create_scene(name, character_name)
        
        return jsonify({
            'success': True,
            'scene': scene.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scene_flow_bp.route('/scenes', methods=['GET'])
@require_auth
def list_scenes():
    """List all active scenes.
    
    Returns:
        JSON response with list of active scenes
    """
    try:
        scenes = scene_flow_service.list_active_scenes()
        return jsonify({
            'success': True,
            'scenes': scenes
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scene_flow_bp.route('/scenes/<scene_id>', methods=['GET'])
@require_auth
def get_scene(scene_id: str):
    """Get a specific scene by ID.
    
    Args:
        scene_id: ID of the scene to retrieve
        
    Returns:
        JSON response with scene data
    """
    try:
        scene = scene_flow_service.get_scene(scene_id)
        
        if not scene:
            return jsonify({'error': 'Scene not found'}), 404
        
        return jsonify({
            'success': True,
            'scene': scene.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scene_flow_bp.route('/scenes/<scene_id>/poses', methods=['POST'])
def add_pose_to_scene(scene_id: str):
    """Add a new pose to a scene.
    
    Args:
        scene_id: ID of the scene to add pose to
        
    Expected JSON body:
    {
        "character_name": "Character name",
        "pose_text": "Pose text",
        "pose_type": "action|dialogue|narrative|internal|mixed" (optional)
    }
    
    Returns:
        JSON response with created pose data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        character_name = data.get('character_name')
        pose_text = data.get('pose_text')
        pose_type_str = data.get('pose_type')
        
        if not character_name or not pose_text:
            return jsonify({
                'error': 'Both character_name and pose_text are required'
            }), 400
        
        # Convert pose type string to enum if provided
        pose_type = None
        if pose_type_str:
            try:
                pose_type = PoseType(pose_type_str.lower())
            except ValueError:
                return jsonify({
                    'error': f'Invalid pose_type: {pose_type_str}'
                }), 400
        
        # Add the pose
        pose = scene_flow_service.add_pose_to_scene(
            scene_id, character_name, pose_text, pose_type
        )
        
        # Return updated scene data
        scene = scene_flow_service.get_scene(scene_id)
        
        return jsonify({
            'success': True,
            'pose': pose.to_dict(),
            'scene': scene.to_dict() if scene else None
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scene_flow_bp.route('/scenes/<scene_id>/poses/bulk', methods=['POST'])
@require_auth
def bulk_import_poses(scene_id: str):
    """Bulk import multiple poses to a scene.
    
    Args:
        scene_id: ID of the scene to add poses to
        
    Expected JSON body:
    {
        "poses_text": "Multi-line text with poses",
        "raw_text": "Raw text in any format (Discord, etc.)",
        "format": "simple|character_prefix|mush_output" (optional, defaults to "simple"),
        "use_llm_parsing": "boolean - whether to use LLM for parsing (optional, default: false)"
    }
    
    Format options:
    - "simple": Each line is a pose, character name extracted from start
    - "character_prefix": Lines like "CharacterName: pose text"
    - "mush_output": Raw MUSH game output with name separators and OOC
    - When use_llm_parsing is true, the format is ignored and the LLM will parse the text
    
    Returns:
        JSON response with imported poses count and data
    """
    # Get current user for authentication
    current_user = get_jwt_identity()
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        poses_text = data.get('poses_text')
        raw_text = data.get('raw_text')
        format_type = data.get('format', 'simple')
        use_llm_parsing = data.get('use_llm_parsing', False)
        
        # Check if we have either poses_text or raw_text
        if not poses_text and not raw_text:
            return jsonify({
                'error': 'poses_text or raw_text is required'
            }), 400
        
        # If not using LLM parsing, validate the format
        if not use_llm_parsing and format_type not in ['simple', 'character_prefix', 'mush_output']:
            return jsonify({
                'error': 'format must be "simple", "character_prefix", or "mush_output"'
            }), 400
        
        # Use raw_text if provided and LLM parsing is enabled
        text_to_parse = raw_text if raw_text and use_llm_parsing else poses_text
        
        # Parse the poses text into individual poses
        imported_poses = scene_flow_service.bulk_import_poses(
            scene_id, text_to_parse, format_type, use_llm_parsing=use_llm_parsing
        )
        
        return jsonify({
            'success': True,
            'imported_count': len(imported_poses),
            'poses': [pose.to_dict() for pose in imported_poses]
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scene_flow_bp.route('/scenes/<scene_id>/context', methods=['GET'])
@require_auth
def get_scene_context(scene_id: str):
    """Get formatted scene context for enhancement.
    
    Args:
        scene_id: ID of the scene
        
    Returns:
        JSON response with formatted context text
    """
    try:
        context = scene_flow_service.get_scene_context_for_enhancement(scene_id)
        
        return jsonify({
            'success': True,
            'context': context
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scene_flow_bp.route('/scenes/<scene_id>/enhance', methods=['POST'])
def enhance_pose_with_context(scene_id: str):
    """Enhance a pose using scene context.
    
    Args:
        scene_id: ID of the scene for context
        
    Expected JSON body:
    {
        "pose_text": "Pose text to enhance",
        "character_name": "Character name",
        "enhancement_style": "minimal|balanced|elaborate" (optional, default: balanced)
    }
    
    Returns:
        JSON response with enhanced pose
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        pose_text = data.get('pose_text')
        character_name = data.get('character_name')
        enhancement_style = data.get('enhancement_style', 'balanced')
        
        if not pose_text or not character_name:
            return jsonify({
                'error': 'Both pose_text and character_name are required'
            }), 400
        
        # Validate enhancement style
        valid_styles = ['minimal', 'balanced', 'elaborate']
        if enhancement_style not in valid_styles:
            return jsonify({
                'error': f'Invalid enhancement_style. Must be one of: {valid_styles}'
            }), 400
        
        # Enhance the pose
        enhanced_text = scene_flow_service.enhance_pose_with_scene_context(
            scene_id, pose_text, character_name, enhancement_style
        )
        
        return jsonify({
            'success': True,
            'original_pose': pose_text,
            'enhanced_pose': enhanced_text,
            'character_name': character_name,
            'enhancement_style': enhancement_style
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except OpenRouterAPIError as e:
        return jsonify({'error': f'AI enhancement failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scene_flow_bp.route('/scenes/<scene_id>/close', methods=['POST'])
def close_scene(scene_id: str):
    """Close an active scene.
    
    Args:
        scene_id: ID of the scene to close
        
    Returns:
        JSON response confirming closure
    """
    try:
        success = scene_flow_service.close_scene(scene_id)
        
        if not success:
            return jsonify({'error': 'Scene not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Scene closed successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Health check endpoint
@scene_flow_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for scene flow service.
    
    Returns:
        JSON response with service status
    """
    return jsonify({
        'success': True,
        'service': 'scene_flow',
        'status': 'healthy',
        'active_scenes': len(scene_flow_service.active_scenes)
    }) 