"""
API endpoints for MUSH output parsing and enhancement.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.pose_service import PoseService
from app.services.venice_client import VeniceClient, VeniceAPIError
from app.services.character_service import CharacterProfile

# Create blueprint
mush_parser_bp = Blueprint('mush_parser', __name__, url_prefix='/api/mush')

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
    Parse MUSH output and enhance your character's poses with scene context.
    
    Expected JSON payload:
    {
        "mush_output": "string - raw MUSH output",
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
        "user_id": "string - optional user ID who owns the scene"
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
        
        # Process the MUSH output
        service = get_pose_service()
        result = service.enhance_from_mush_output(
            mush_output=mush_output,
            your_character_name=your_character_name,
            character=character,
            enhancement_style=enhancement_style,
            scene_id=scene_id,
            user_id=user_id
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