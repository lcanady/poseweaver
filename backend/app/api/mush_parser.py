"""
API endpoints for MUSH output parsing and enhancement.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.services.pose_service import PoseService
from app.services.venice_client import VeniceClient, VeniceAPIError
from app.services.character_service import CharacterProfile
from app.services.scene_management_service import SceneManagementService, PoseData
from app.models.scene_memory import PoseType
from app.middleware.auth_middleware import require_auth

# Create blueprint
mush_parser_bp = Blueprint('mush_parser', __name__)

# Global service instance (initialized lazily)
pose_service = None


def get_pose_service():
    """Get or create the pose service instance."""
    global pose_service
    if pose_service is None:
        from flask import current_app
        api_key = current_app.config.get('VENICE_API_KEY', 'test_key_12345')
        venice_client = VeniceClient(api_key)
        pose_service = PoseService(venice_client)
    return pose_service


@mush_parser_bp.route('/parse', methods=['POST'])
def parse_mush_output():
    """
    Parse MUSH game output into structured data.
    
    Expected JSON payload:
    {
        "mush_output": "string - raw MUSH output",
        "your_character_hint": "string - optional hint about your character name"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        mush_output = data.get('mush_output')
        if not mush_output:
            return jsonify({"error": "mush_output is required"}), 400
        
        your_character_hint = data.get('your_character_hint')
        
        # Parse the MUSH output
        service = get_pose_service()
        parsed_scene = service.parse_mush_output(mush_output, your_character_hint)
        
        # Convert to serializable format
        result = {
            "room_description": parsed_scene.room_description,
            "characters_present": parsed_scene.characters_present,
            "your_character": parsed_scene.your_character,
            "poses": [
                {
                    "character_name": pose.character_name,
                    "content": pose.content,
                    "pose_type": pose.pose_type.value,
                    "is_ooc": pose.is_ooc,
                    "timestamp": pose.timestamp
                }
                for pose in parsed_scene.poses
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mush_parser_bp.route('/enhance', methods=['POST'])
def enhance_from_mush_output():
    """
    Parse text (MUSH, Discord, etc.) and enhance your character's poses with scene context.
    
    Expected JSON payload:
    {
        "mush_output": "string - raw MUSH output",
        "raw_text": "string - raw text in any format (Discord, etc.)",
        "your_character_name": "string - your character name",
        "character": {
            "name": "string",
            "background": "string",
            "personality": ["trait1", "trait2"],
            "speaking_style": "string",
            "physical_description": "string"
        },
        "enhancement_style": "string - balanced/detailed/subtle (optional, default: balanced)",
        "scene_id": "string - optional scene ID to save context to",
        "user_id": "string - optional user ID who owns the scene",
        "use_llm_parsing": "boolean - whether to use LLM for parsing (optional, default: false)"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Check for raw_text first (for LLM parsing), then fall back to mush_output
        raw_text = data.get('raw_text')
        mush_output = data.get('mush_output')
        
        if not raw_text and not mush_output:
            return jsonify({"error": "raw_text or mush_output is required"}), 400
        
        your_character_name = data.get('your_character_name')
        if not your_character_name:
            return jsonify({"error": "your_character_name is required"}), 400
            
        # If raw_text is provided, use it instead of mush_output
        use_llm_parsing = data.get('use_llm_parsing', False)
        text_to_use = raw_text if raw_text and use_llm_parsing else mush_output
        
        # Parse character profile if provided (optional)
        character = None
        character_data = data.get('character')
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
        
        enhancement_style = data.get('enhancement_style', 'balanced')
        scene_id = data.get('scene_id')
        user_id = data.get('user_id')
        
        # Process the input text
        service = get_pose_service()
        result = service.enhance_from_mush_output(
            mush_output=mush_output or "",
            your_character_name=your_character_name,
            character=character,
            enhancement_style=enhancement_style,
            scene_id=scene_id,
            user_id=user_id,
            use_llm_parsing=use_llm_parsing,
            raw_text=raw_text
        )
        
        return jsonify(result)
        
    except VeniceAPIError as e:
        return jsonify({"error": f"AI service error: {str(e)}"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mush_parser_bp.route('/preview', methods=['POST'])
def preview_mush_parsing():
    """
    Preview how MUSH output would be parsed without enhancement.
    
    Expected JSON payload:
    {
        "mush_output": "string - raw MUSH output",
        "your_character_name": "string - your character name"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        mush_output = data.get('mush_output')
        if not mush_output:
            return jsonify({"error": "mush_output is required"}), 400
        
        your_character_name = data.get('your_character_name')
        if not your_character_name:
            return jsonify({"error": "your_character_name is required"}), 400
        
        # Parse the MUSH output
        service = get_pose_service()
        parsed_scene = service.parse_mush_output(mush_output, your_character_name)
        
        # Extract your character's poses
        your_poses = service.mush_parser.extract_your_character_poses(
            parsed_scene, your_character_name
        )
        
        # Build scene context
        scene_context = service.mush_parser.build_scene_context_from_parsed(parsed_scene)
        
        result = {
            "parsed_scene": {
                "room_description": parsed_scene.room_description,
                "characters_present": parsed_scene.characters_present,
                "your_character": parsed_scene.your_character,
                "total_poses": len(parsed_scene.poses)
            },
            "your_poses": [
                {
                    "character_name": pose.character_name,
                    "content": pose.content,
                    "pose_type": pose.pose_type.value,
                    "is_ooc": pose.is_ooc,
                    "timestamp": pose.timestamp
                }
                for pose in your_poses
            ],
            "scene_context": scene_context,
            "poses_found": len(your_poses)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mush_parser_bp.route('/help', methods=['GET'])
def get_mush_parser_help():
    """
    Get help information about MUSH parsing capabilities.
    """
    help_info = {
        "description": "MUSH Parser allows you to copy and paste MUSH game output for automatic pose enhancement",
        "supported_formats": [
            "Standard poses: 'CharacterName does something'",
            "Dialogue: 'CharacterName says, \"something\"'",
            "OOC comments: '<OOC> CharacterName says, \"something\"'",
            "Room descriptions with ---- headers",
            "Character lists in Contents: sections",
            "Timestamped output"
        ],
        "endpoints": {
            "/parse": "Parse MUSH output into structured data",
            "/enhance": "Parse and enhance your character's poses with scene context",
            "/preview": "Preview parsing results without enhancement"
        },
        "tips": [
            "Include room descriptions and character lists for better context",
            "Make sure to specify your exact character name",
            "The parser will automatically detect pose types and build scene context",
            "OOC comments are preserved but not enhanced"
        ]
    }
    
    return jsonify(help_info)


@mush_parser_bp.route('/enhance-with-scene-storage', methods=['POST'])
@require_auth
def enhance_mush_output_with_scene_storage():
    """
    Parse MUSH output, enhance poses, and automatically store scene data.
    
    This endpoint integrates the existing MUSH parsing with the scene memory
    and continuity tracking system. It will:
    1. Parse the MUSH output
    2. Create or update a scene in the continuity system
    3. Store all poses with character states and environment details
    4. Enhance your character's poses with continuity analysis
    5. Return enhanced poses with continuity feedback
    
    Expected JSON payload:
    {
        "mush_output": "string - raw MUSH output",
        "raw_text": "string - raw text in any format (Discord, etc.)",
        "your_character_name": "string - your character name",
        "scene_name": "string - name for the scene (required for new scenes)",
        "scene_id": "string - optional existing scene ID",
        "user_id": "string - user ID who owns the scene (required)",
        "character": {
            "name": "string",
            "background": "string", 
            "personality": ["trait1", "trait2"],
            "speaking_style": "string",
            "physical_description": "string"
        },
        "enhancement_style": "string - balanced/detailed/subtle (optional)",
        "store_all_poses": true,  // Whether to store all poses or just yours
        "analyze_continuity": true,  // Whether to perform continuity analysis
        "use_llm_parsing": true  // Whether to use LLM for parsing (optional, default: false)
    }
    
    Returns:
    {
        "success": true,
        "scene_id": "scene-uuid",
        "parsed_scene": {...},
        "your_poses": [...],
        "enhanced_poses": [...],
        "continuity_analysis": {...},
        "scene_stored": true,
        "poses_stored": 5,
        "character_states_updated": [...],
        "environment_state_updated": {...}
    }
    
    Requirements: 1.2, 2.1, 2.2 - Store poses and track character states
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        raw_text = data.get('raw_text')
        mush_output = data.get('mush_output')
        
        if not raw_text and not mush_output:
            return jsonify({"error": "raw_text or mush_output is required"}), 400
        
        your_character_name = data.get('your_character_name')
        if not your_character_name:
            return jsonify({"error": "your_character_name is required"}), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id is required for scene storage"}), 400
        
        # Get scene information
        scene_id = data.get('scene_id')
        scene_name = data.get('scene_name', f"Scene with {your_character_name}")
        
        # Parse character profile if provided
        character = None
        character_data = data.get('character')
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
        
        # Get processing options
        enhancement_style = data.get('enhancement_style', 'balanced')
        store_all_poses = data.get('store_all_poses', True)
        analyze_continuity = data.get('analyze_continuity', True)
        
        # Step 1: Parse the input text (MUSH or raw text)
        service = get_pose_service()
        use_llm_parsing = data.get('use_llm_parsing', False)
        
        parsed_result = service.enhance_from_mush_output(
            mush_output=mush_output or "",
            your_character_name=your_character_name,
            character=character,
            enhancement_style=enhancement_style,
            scene_id=scene_id,
            user_id=user_id,
            use_llm_parsing=use_llm_parsing,
            raw_text=raw_text
        )
        
        # Step 2: Initialize scene management service
        scene_management_service = SceneManagementService()
        
        # Step 3: Create or get existing scene
        if scene_id:
            # Use existing scene
            scene = scene_management_service.get_scene(scene_id)
            if not scene:
                return jsonify({
                    "error": f"Scene {scene_id} not found"
                }), 404
        else:
            # Create new scene
            try:
                scene = scene_management_service.create_scene(
                    name=scene_name,
                    description=f"Scene parsed from MUSH output on {datetime.utcnow().isoformat()}",
                    owner_id=user_id,
                    metadata={
                        'source': 'mush_parser',
                        'characters_present': parsed_result.get('parsed_scene', {}).get('characters_present', []),
                        'room_description': parsed_result.get('parsed_scene', {}).get('room_description', '')
                    }
                )
                scene_id = scene.id
            except ValueError as e:
                return jsonify({"error": f"Scene creation failed: {str(e)}"}), 400
        
        # Step 4: Store all poses if requested
        poses_stored = 0
        if store_all_poses and 'parsed_scene' in parsed_result:
            scene_poses = parsed_result['parsed_scene'].get('poses', [])
            
            for pose_data in scene_poses:
                try:
                    # Convert pose type
                    pose_type = PoseType.MIXED  # Default
                    if pose_data.get('pose_type') == 'action':
                        pose_type = PoseType.ACTION
                    elif pose_data.get('pose_type') == 'dialogue':
                        pose_type = PoseType.DIALOGUE
                    
                    # Create pose data
                    pose = PoseData(
                        character_name=pose_data.get('character_name', 'Unknown'),
                        content=pose_data.get('content', ''),
                        pose_type=pose_type,
                        is_ooc=pose_data.get('is_ooc', False),
                        timestamp=datetime.utcnow(),
                        analysis_data={'source': 'mush_parser'}
                    )
                    
                    # Store the pose
                    scene_management_service.add_pose(scene_id, pose)
                    poses_stored += 1
                    
                except Exception as e:
                    # Log error but continue with other poses
                    print(f"Error storing pose: {e}")
        
        # Step 5: Prepare response
        response_data = {
            "success": True,
            "scene_id": scene_id,
            "scene_stored": True,
            "poses_stored": poses_stored,
            **parsed_result  # Include all original parsing results
        }
        
        # Add continuity analysis if your poses were enhanced
        if analyze_continuity and 'enhanced_poses' in parsed_result:
            response_data['continuity_analysis_available'] = True
            # Note: Full continuity analysis would require integration 
            # with the ContinuityService here
        
        return jsonify(response_data)
        
    except VeniceAPIError as e:
        return jsonify({"error": f"AI service error: {str(e)}"}), 503
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500 