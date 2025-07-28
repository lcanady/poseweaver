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
from app.services.usage_tracking_service import require_pose_generation_limit, get_usage_info

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
@require_pose_generation_limit
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
        
        # Map 'subtle' to 'minimal' for compatibility
        if enhancement_style == 'subtle':
            enhancement_style = 'minimal'
        
        if enhancement_style not in ['minimal', 'balanced', 'elaborate']:
            return jsonify({
                'success': False,
                'error': 'enhancement_style must be minimal, balanced, elaborate, or subtle'
            }), 400
        
        # Get enhancement options
        enhancement_options = data.get('enhancement_options', {})
        
        # Get character settings
        character_settings = data.get('character_settings', {})
        
        # Enhance the pose
        service = get_pose_service()
        enhancement = service.enhance_pose(
            original_pose, character, context, enhancement_style, enhancement_options, character_settings
        )
        
        # Get usage info from request context (added by decorator)
        usage_info = getattr(request, 'usage_info', {})
        
        # Return enhanced pose with validation warnings and usage info
        response_data = {
            'success': True,
            'enhanced_pose': enhancement['enhanced_pose'],
            'usage_info': {
                'available_generations': usage_info.get('available_generations', 0),
                'monthly_limit': usage_info.get('monthly_limit', 0),
                'current_usage': usage_info.get('current_usage', 0),
                'extra_generations': usage_info.get('extra_generations', 0),
                'subscription_status': usage_info.get('subscription_status', 'free')
            }
        }
        
        # Include validation warnings if present
        if enhancement.get('validation_warnings'):
            response_data['validation_warnings'] = enhancement['validation_warnings']
            
        return jsonify(response_data)
        
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


@pose_bp.route('/refine', methods=['POST'])
@require_pose_generation_limit
def refine_pose():
    """Refine an enhanced pose based on user suggestions.
    
    Expected JSON payload:
    {
        "current_pose": "The current enhanced pose text",
        "edit_suggestion": "User's suggestion for improvement",
        "original_pose": "The original pose (optional)",
        "character": CharacterProfile (optional),
        "context": PoseContext (optional),
        "enhancement_style": "balanced|creative|detailed|concise",
        "enhancement_options": {...}
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        # Extract required fields
        current_pose = data.get('current_pose')
        edit_suggestion = data.get('edit_suggestion')
        
        if not current_pose or not edit_suggestion:
            return jsonify({
                'error': 'Both current_pose and edit_suggestion are required'
            }), 400
            
        # Extract optional fields
        original_pose = data.get('original_pose')
        character_data = data.get('character')
        context_data = data.get('context')
        enhancement_style = data.get('enhancement_style', 'balanced')
        enhancement_options = data.get('enhancement_options', {})
        
        # Parse character and context if provided
        character = None
        context = None
        
        if character_data:
            try:
                character = CharacterProfile(**character_data)
            except TypeError as e:
                return jsonify({
                    'error': f'Invalid character data: {str(e)}'
                }), 400
                
        if context_data:
            try:
                context = PoseContext(**context_data)
            except TypeError as e:
                return jsonify({
                    'error': f'Invalid context data: {str(e)}'
                }), 400
        
        # Get pose service instance
        service = get_pose_service()
        
        # Refine the pose
        result = service.refine_pose(
            current_pose=current_pose,
            edit_suggestion=edit_suggestion,
            original_pose=original_pose,
            character=character,
            context=context,
            enhancement_style=enhancement_style,
            enhancement_options=enhancement_options
        )
        
        return jsonify(result)
        
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
@require_pose_generation_limit
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
        
        # Get usage info from request context (added by decorator)
        usage_info = getattr(request, 'usage_info', {})
        
        return jsonify({
            'success': True,
            'enhanced_pose': enhancement.enhanced_pose,
            'scene_context_used': scene_context_used,
            'usage_info': {
                'available_generations': usage_info.get('available_generations', 0),
                'monthly_limit': usage_info.get('monthly_limit', 0),
                'current_usage': usage_info.get('current_usage', 0),
                'extra_generations': usage_info.get('extra_generations', 0),
                'subscription_status': usage_info.get('subscription_status', 'free')
            }
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
@require_pose_generation_limit
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
@get_usage_info
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


@pose_bp.route('/enhance-with-continuity', methods=['POST'])
def enhance_pose_with_continuity():
    """Enhance a pose with integrated continuity analysis.
    
    Request body:
    {
        "original_pose": "Basic pose text...",
        "scene_id": "scene-uuid-here",  // Required for continuity analysis
        "character_name": "Character Name",  // Required
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
        "enhancement_style": "balanced",  // minimal, balanced, elaborate
        "analyze_continuity": true  // Optional, default: true
    }
    
    Returns:
    {
        "success": true,
        "enhanced_pose": "Enhanced pose text...",
        "continuity_analysis": {
            "character_consistency_score": 0.85,
            "environment_consistency_score": 0.90,
            "plot_consistency_score": 0.78,
            "timeline_consistency_score": 0.95,
            "overall_confidence": 0.87,
            "flags_count": 1,
            "issues": [...],
            "suggestions": [...]
        },
        "character_state_changes": [...],
        "environment_changes": [...]
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
        
        # Validate required fields for continuity analysis
        original_pose = data.get('original_pose')
        if not original_pose or not original_pose.strip():
            return jsonify({
                'success': False,
                'error': 'original_pose is required and cannot be empty'
            }), 400
        
        scene_id = data.get('scene_id')
        if not scene_id or not scene_id.strip():
            return jsonify({
                'success': False,
                'error': 'scene_id is required for continuity analysis'
            }), 400
        
        character_name = data.get('character_name')
        if not character_name or not character_name.strip():
            return jsonify({
                'success': False,
                'error': 'character_name is required'
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
        
        # Get enhancement options
        enhancement_style = data.get('enhancement_style', 'balanced')
        if enhancement_style not in ['minimal', 'balanced', 'elaborate']:
            return jsonify({
                'success': False,
                'error': 'enhancement_style must be minimal, balanced, or '
                         'elaborate'
            }), 400
        
        analyze_continuity = data.get('analyze_continuity', True)
        
        # Enhance the pose with continuity analysis
        service = get_pose_service()
        enhancement = service.enhance_pose_with_continuity(
            original_pose=original_pose,
            scene_id=scene_id,
            character_name=character_name,
            character=character,
            context=context,
            enhancement_style=enhancement_style,
            analyze_continuity=analyze_continuity
        )
        
        # Build response data
        response_data = {
            'success': True,
            'enhanced_pose': enhancement.enhanced_pose,
            'enhancement_notes': enhancement.enhancement_notes,
            'sensory_details': enhancement.sensory_details,
            'character_voice_elements': enhancement.character_voice_elements,
            'narrative_techniques': enhancement.narrative_techniques
        }
        
        # Add continuity analysis if present
        if enhancement.continuity_analysis:
            response_data['continuity_analysis'] = {
                'character_consistency_score': enhancement.continuity_analysis.character_consistency_score,
                'environment_consistency_score': enhancement.continuity_analysis.environment_consistency_score,
                'plot_consistency_score': enhancement.continuity_analysis.plot_consistency_score,
                'timeline_consistency_score': enhancement.continuity_analysis.timeline_consistency_score,
                'overall_confidence': enhancement.continuity_analysis.overall_confidence,
                'flags_count': len(enhancement.continuity_analysis.flags),
                'analysis_notes': enhancement.continuity_analysis.analysis_notes
            }
        
        if enhancement.character_state_changes:
            response_data['character_state_changes'] = enhancement.character_state_changes
        
        if enhancement.environment_changes:
            response_data['environment_changes'] = enhancement.environment_changes
        
        return jsonify(response_data)
        
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


@pose_bp.route('/enhance-with-precheck', methods=['POST'])
def enhance_pose_with_precheck():
    """Enhance a pose with pre-enhancement continuity checking.
    
    This endpoint performs continuity analysis BEFORE enhancement and provides
    warnings about potential issues. Users can review these warnings and
    decide whether to proceed or modify their pose.
    
    Request body:
    {
        "original_pose": "Basic pose text...",
        "scene_id": "scene-uuid-here",  // Required for continuity analysis
        "character_name": "Character Name",  // Required
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
        "enhancement_style": "balanced",  // minimal, balanced, elaborate
        "continuity_threshold": 0.6  // Optional, minimum score for warnings
    }
    
    Returns:
    {
        "success": true,
        "enhanced_pose": "Enhanced pose text...",
        "warnings": [
            "Character consistency concern (score: 0.55). This pose may not match established character behavior.",
            "Environment consistency concern (score: 0.48). This pose may contradict established environmental details."
        ],
        "continuity_scores": {
            "character_consistency_score": 0.55,
            "environment_consistency_score": 0.48,
            "plot_consistency_score": 0.75,
            "timeline_consistency_score": 0.90,
            "overall_confidence": 0.67
        },
        "enhancement_details": {
            "enhancement_notes": [...],
            "sensory_details": [...],
            "character_voice_elements": [...],
            "narrative_techniques": [...]
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
        original_pose = data.get('original_pose')
        if not original_pose or not original_pose.strip():
            return jsonify({
                'success': False,
                'error': 'original_pose is required and cannot be empty'
            }), 400
        
        scene_id = data.get('scene_id')
        if not scene_id or not scene_id.strip():
            return jsonify({
                'success': False,
                'error': 'scene_id is required for continuity analysis'
            }), 400
        
        character_name = data.get('character_name')
        if not character_name or not character_name.strip():
            return jsonify({
                'success': False,
                'error': 'character_name is required'
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
        
        # Get enhancement options
        enhancement_style = data.get('enhancement_style', 'balanced')
        if enhancement_style not in ['minimal', 'balanced', 'elaborate']:
            return jsonify({
                'success': False,
                'error': 'enhancement_style must be minimal, balanced, or '
                         'elaborate'
            }), 400
        
        continuity_threshold = data.get('continuity_threshold', 0.6)
        if not isinstance(continuity_threshold, (int, float)) or continuity_threshold < 0 or continuity_threshold > 1:
            return jsonify({
                'success': False,
                'error': 'continuity_threshold must be a number between 0 and 1'
            }), 400
        
        # Enhance the pose with pre-check continuity analysis
        service = get_pose_service()
        enhancement, warnings = service.enhance_pose_with_pre_check(
            original_pose=original_pose,
            scene_id=scene_id,
            character_name=character_name,
            character=character,
            context=context,
            enhancement_style=enhancement_style,
            continuity_threshold=continuity_threshold
        )
        
        # Build response data
        response_data = {
            'success': True,
            'enhanced_pose': enhancement.enhanced_pose,
            'warnings': warnings,
            'enhancement_details': {
                'enhancement_notes': enhancement.enhancement_notes,
                'sensory_details': enhancement.sensory_details,
                'character_voice_elements': enhancement.character_voice_elements,
                'narrative_techniques': enhancement.narrative_techniques
            }
        }
        
        # Add continuity scores if available
        if enhancement.continuity_analysis:
            response_data['continuity_scores'] = {
                'character_consistency_score': enhancement.continuity_analysis.character_consistency_score,
                'environment_consistency_score': enhancement.continuity_analysis.environment_consistency_score,
                'plot_consistency_score': enhancement.continuity_analysis.plot_consistency_score,
                'timeline_consistency_score': enhancement.continuity_analysis.timeline_consistency_score,
                'overall_confidence': enhancement.continuity_analysis.overall_confidence
            }
        
        if enhancement.character_state_changes:
            response_data['character_state_changes'] = enhancement.character_state_changes
        
        if enhancement.environment_changes:
            response_data['environment_changes'] = enhancement.environment_changes
        
        return jsonify(response_data)
        
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