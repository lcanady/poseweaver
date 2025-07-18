"""
Pose enhancement API endpoints for MUSH Pose Editor.

Provides endpoints for pose enhancement and generation.
"""
from flask import Blueprint, request, jsonify
from app.services.pose_service import PoseService
from app.services.character_service import CharacterProfile
from app.services.context_service import PoseContext
from app.services.scene_flow_service import SceneFlowService
from app.services.venice_client import VeniceClient, VeniceAPIError

pose_bp = Blueprint('pose', __name__)

# Global service instances for testing compatibility
pose_service = None
scene_flow_service = None


def get_pose_service():
    """Get pose service instance."""
    global pose_service
    if pose_service is None:
        import os
        api_key = os.getenv('VENICE_API_KEY')
        if not api_key:
            raise ValueError("VENICE_API_KEY environment variable is required")
        venice_client = VeniceClient(api_key=api_key)
        pose_service = PoseService(venice_client)
    return pose_service


def get_scene_flow_service():
    """Get scene flow service instance."""
    global scene_flow_service
    if scene_flow_service is None:
        import os
        api_key = os.getenv('VENICE_API_KEY')
        if not api_key:
            raise ValueError("VENICE_API_KEY environment variable is required")
        venice_client = VeniceClient(api_key=api_key)
        scene_flow_service = SceneFlowService(venice_client)
    return scene_flow_service


@pose_bp.route('/enhance', methods=['POST'])
def enhance_pose():
    """Enhance a basic pose into rich narrative.
    
    Request body:
    {
        "original_pose": "Basic pose text...",
        "character": {  // Optional
            "name": "Character Name",
            "background": "...",
            // ... other character fields
        },
        "context": {  // Optional
            "actions": [...],
            "emotions": [...],
            // ... other context fields
        },
        "enhancement_style": "balanced"  // minimal, balanced, elaborate
    }
    
    Returns:
    {
        "success": true,
        "enhanced_pose": "Enhanced pose text..."
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
        original_pose = data.get('original_pose')
        if not original_pose or not original_pose.strip():
            return jsonify({
                'success': False,
                'error': 'original_pose is required and cannot be empty'
            }), 400
        
        # Handle optional character data
        character = None
        if 'character' in data and data['character']:
            try:
                character_data = data['character']
                character = CharacterProfile(**character_data)
            except (TypeError, ValueError) as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid character data: {str(e)}'
                }), 400
        
        # Handle optional context data
        context = None
        if 'context' in data and data['context']:
            try:
                context_data = data['context']
                context = PoseContext.from_dict(context_data)
            except (TypeError, ValueError) as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid context data: {str(e)}'
                }), 400
        
        # Get enhancement style
        enhancement_style = data.get('enhancement_style', 'balanced')
        if enhancement_style not in ['minimal', 'balanced', 'elaborate']:
            return jsonify({
                'success': False,
                'error': 'enhancement_style must be minimal, balanced, or '
                         'elaborate'
            }), 400
        
        # Enhance the pose
        service = get_pose_service()
        enhancement = service.enhance_pose(
            original_pose, character, context, enhancement_style
        )
        
        # Return just the enhanced pose text
        return jsonify({
            'success': True,
            'enhanced_pose': enhancement.enhanced_pose
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


@pose_bp.route('/enhance-with-scene', methods=['POST'])
def enhance_pose_with_scene():
    """Enhance a pose using scene context from scene flow.
    
    Request body:
    {
        "original_pose": "Basic pose text...",
        "scene_id": "scene-uuid-here",  // Optional - uses scene context
        "character": {  // Optional
            "name": "Character Name",
            "background": "...",
            // ... other character fields
        },
        "enhancement_style": "balanced"  // minimal, balanced, elaborate
    }
    
    Returns:
    {
        "success": true,
        "enhanced_pose": "Enhanced pose text...",
        "scene_context_used": true  // indicates if scene context was available
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
        original_pose = data.get('original_pose')
        if not original_pose or not original_pose.strip():
            return jsonify({
                'success': False,
                'error': 'original_pose is required and cannot be empty'
            }), 400
        
        # Handle optional character data
        character = None
        if 'character' in data and data['character']:
            try:
                character_data = data['character']
                character = CharacterProfile(**character_data)
            except (TypeError, ValueError) as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid character data: {str(e)}'
                }), 400
        
        # Get enhancement style
        enhancement_style = data.get('enhancement_style', 'balanced')
        if enhancement_style not in ['minimal', 'balanced', 'elaborate']:
            return jsonify({
                'success': False,
                'error': 'enhancement_style must be minimal, balanced, or '
                         'elaborate'
            }), 400
        
        # Get scene context if scene_id provided
        scene_context = None
        scene_context_used = False
        scene_id = data.get('scene_id')
        
        if scene_id:
            try:
                scene_service = get_scene_flow_service()
                scene_context = scene_service.get_scene_context_for_enhancement(
                    scene_id
                )
                scene_context_used = True
            except ValueError:
                # Scene not found, continue without scene context
                pass
        
        # Enhance the pose
        service = get_pose_service()
        
        if scene_context:
            # Use scene flow enhancement if we have scene context
            enhancement = service.enhance_pose_with_scene_flow(
                original_pose, scene_context, character, enhancement_style
            )
        else:
            # Fall back to regular enhancement
            enhancement = service.enhance_pose(
                original_pose, character, None, enhancement_style
            )
        
        # Return the enhanced pose
        return jsonify({
            'success': True,
            'enhanced_pose': enhancement.enhanced_pose,
            'scene_context_used': scene_context_used
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


@pose_bp.route('/variations', methods=['POST'])
def generate_pose_variations():
    """Generate multiple enhancement variations of a pose.
    
    Request body:
    {
        "original_pose": "Basic pose text...",
        "character": {  // Optional
            "name": "Character Name",
            // ... other character fields
        },
        "count": 3  // Number of variations (max 3)
    }
    
    Returns:
    {
        "success": true,
        "variations": [
            {
                "original_pose": "...",
                "enhanced_pose": "...",
                // ... enhancement data
            },
            // ... more variations
        ]
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
        original_pose = data.get('original_pose')
        if not original_pose or not original_pose.strip():
            return jsonify({
                'success': False,
                'error': 'original_pose is required and cannot be empty'
            }), 400
        
        # Handle optional character data
        character = None
        if 'character' in data and data['character']:
            try:
                character_data = data['character']
                character = CharacterProfile(**character_data)
            except (TypeError, ValueError) as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid character data: {str(e)}'
                }), 400
        
        # Get count
        count = data.get('count', 3)
        if not isinstance(count, int) or count < 1 or count > 3:
            return jsonify({
                'success': False,
                'error': 'count must be an integer between 1 and 3'
            }), 400
        
        # Generate variations
        service = get_pose_service()
        variations = service.generate_pose_variations(
            original_pose, character, count
        )
        
        return jsonify({
            'success': True,
            'variations': [v.to_dict() for v in variations]
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


@pose_bp.route('/analyze', methods=['POST'])
def analyze_pose_quality():
    """Analyze the quality and characteristics of a pose.
    
    Request body:
    {
        "pose": "Pose text to analyze...",
        "character": {  // Optional
            "name": "Character Name",
            // ... other character fields
        }
    }
    
    Returns:
    {
        "success": true,
        "analysis": {
            "word_count": 25,
            "sentence_count": 2,
            "has_dialogue": true,
            "has_action": true,
            "has_emotion": false,
            "complexity_score": 5,
            "character_consistency": true  // if character provided
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
        pose = data.get('pose')
        if not pose or not pose.strip():
            return jsonify({
                'success': False,
                'error': 'pose is required and cannot be empty'
            }), 400
        
        # Handle optional character data
        character = None
        if 'character' in data and data['character']:
            try:
                character_data = data['character']
                character = CharacterProfile(**character_data)
            except (TypeError, ValueError) as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid character data: {str(e)}'
                }), 400
        
        # Analyze pose quality
        service = get_pose_service()
        analysis = service.analyze_pose_quality(pose, character)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@pose_bp.route('/parse-mush-output', methods=['POST'])
def parse_mush_output():
    """Parse MUSH game output and extract character poses.
    
    Request body:
    {
        "mush_output": "Raw MUSH output text",
        "your_character_name": "Your character's name",
        "character": {...},  // Optional character profile
        "enhancement_style": "balanced"  // Optional enhancement style
    }
    
    Returns:
    {
        "success": true,
        "parsed_scene": {...},
        "your_poses": [...],
        "enhanced_poses": [...],
        "scene_context": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        # Extract required fields
        mush_output = data.get('mush_output', '').strip()
        your_character_name = data.get('your_character_name', '').strip()
        
        if not mush_output:
            return jsonify({
                'success': False,
                'error': 'mush_output is required'
            }), 400
            
        if not your_character_name:
            return jsonify({
                'success': False,
                'error': 'your_character_name is required'
            }), 400
        
        # Extract optional fields
        character_data = data.get('character')
        enhancement_style = data.get('enhancement_style', 'balanced')
        skip_enhancement = data.get('skip_enhancement', False)
        
        # Create character profile if provided
        character = None
        if character_data:
            character = CharacterProfile(
                name=character_data.get('name', ''),
                background=character_data.get('background', ''),
                personality=character_data.get('personality', []),
                skills=character_data.get('skills', []),
                goals=character_data.get('goals', []),
                relationships=character_data.get('relationships', {}),
                voice_notes=character_data.get('voice_notes', '')
            )
        
        # Get pose service and parse MUSH output
        service = get_pose_service()
        results = service.enhance_from_mush_output(
            mush_output=mush_output,
            your_character_name=your_character_name,
            character=character,
            enhancement_style=enhancement_style,
            skip_enhancement=skip_enhancement
        )
        
        return jsonify({
            'success': True,
            **results
        })
        
    except VeniceAPIError as e:
        return jsonify({
            'success': False,
            'error': f'AI service error: {str(e)}'
        }), 503
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@pose_bp.route('/generate', methods=['POST'])
def generate_pose():
    """Generate enhanced pose - legacy endpoint for compatibility."""
    return jsonify({
        'success': False,
        'error': 'This endpoint has been replaced by /enhance'
    }), 410


@pose_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@pose_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405 