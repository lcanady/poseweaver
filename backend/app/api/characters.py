"""
Character API endpoints for MUSH Pose Editor.

Provides endpoints for character brain dump processing and management.
"""
from flask import Blueprint, request, jsonify
from app.services.character_service import CharacterService, CharacterProfile
from app.services.venice_client import VeniceClient, VeniceAPIError
from app.middleware.auth_middleware import require_auth

# Create blueprint
characters_bp = Blueprint('characters', __name__)


# Global service instance for testing compatibility
character_service = None


def get_character_service():
    """Get character service instance."""
    global character_service
    if character_service is None:
        try:
            import os
            api_key = os.getenv('VENICE_API_KEY')
            if not api_key:
                raise ValueError("VENICE_API_KEY environment variable is required")
            venice_client = VeniceClient(api_key=api_key)
            character_service = CharacterService(venice_client)
        except Exception as e:
            # If service creation fails, raise a more specific error
            raise ValueError(
                f"Failed to initialize character service: {str(e)}"
            )
    return character_service


@characters_bp.route('/process', methods=['POST'])
@require_auth
def process_brain_dump():
    """Process a character brain dump into structured profile.
    
    Request body:
    {
        "brain_dump": "Free-form character description...",
        "existing_character": {  // Optional
            "name": "Character Name",
            "background": "...",
            // ... other character fields
        }
    }
    
    Returns:
    {
        "success": true,
        "character": {
            "name": "Character Name",
            "background": "...",
            "personality": [...],
            "skills": [...],
            "goals": [...],
            "relationships": {...},
            "voice_notes": "..."
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
        brain_dump = data.get('brain_dump')
        if not brain_dump or not brain_dump.strip():
            return jsonify({
                'success': False,
                'error': 'brain_dump is required and cannot be empty'
            }), 400
        
        # Handle existing character data if provided
        existing_character = None
        if 'existing_character' in data and data['existing_character']:
            try:
                existing_data = data['existing_character']
                existing_character = CharacterProfile(**existing_data)
            except (TypeError, ValueError) as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid existing character data: {str(e)}'
                }), 400
        
        # Process the brain dump
        character_service = get_character_service()
        character = character_service.process_brain_dump(
            brain_dump, existing_character
        )
        
        return jsonify({
            'success': True,
            'character': character.to_dict()
        }), 200
        
    except VeniceAPIError as e:
        return jsonify({
            'success': False,
            'error': f'AI processing failed: {str(e)}'
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


@characters_bp.route('/validate', methods=['POST'])
@require_auth
def validate_character():
    """Validate a character profile structure.
    
    Request body:
    {
        "character": {
            "name": "Character Name",
            "background": "...",
            "personality": [...],
            "skills": [...],
            "goals": [...],
            "relationships": {...},
            "voice_notes": "..."
        }
    }
    
    Returns:
    {
        "success": true,
        "valid": true,
        "errors": []
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
        
        # Validate character data
        character_data = data.get('character')
        if not character_data:
            return jsonify({
                'success': False,
                'error': 'character field is required'
            }), 400
        
        # Attempt to create character profile to validate structure
        try:
            character = CharacterProfile(**character_data)
            return jsonify({
                'success': True,
                'valid': True,
                'errors': []
            }), 200
        except (TypeError, ValueError) as e:
            return jsonify({
                'success': True,
                'valid': False,
                'errors': [str(e)]
            }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@characters_bp.route('/', methods=['GET'])
@require_auth
def get_characters():
    """Get list of characters for the authenticated user.
    
    Returns:
    {
        "success": true,
        "data": [character objects],
        "meta": {
            "total": total_count,
            "limit": limit,
            "skip": skip
        }
    }
    """
    try:
        from app.models.character import Character
        from flask import request, current_app
        from flask_jwt_extended import get_jwt_identity
        
        # Get user ID from JWT
        current_user = get_jwt_identity()
        user_id = None
        
        if current_user:
            # Extract user_id from identity (handle both string and dict formats)
            user_id = current_user if isinstance(current_user, str) else current_user.get('id')
        else:
            current_app.logger.error("No JWT identity found")
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        
        # Get all user's characters
        try:
            # Try to get characters with pagination if supported
            skip = request.args.get('skip', default=0, type=int)
            limit = min(request.args.get('limit', default=100, type=int), 100)  # Max 100
            characters = Character.find_by_user(user_id, skip=skip, limit=limit)
        except TypeError:
            # If pagination not supported, get all characters
            characters = Character.find_by_user(user_id)
            
        # Get total count
        try:
            total_count = Character.count_by_user(user_id)
        except (AttributeError, TypeError):
            # If count method doesn't exist, count the results manually
            total_count = len(characters)
        
        return jsonify({
            'success': True,
            'data': [char.to_dict() for char in characters],
            'meta': {
                'total': total_count,
                'limit': limit,
                'skip': skip
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve characters: {str(e)}'
        }), 500

@characters_bp.route('/schema', methods=['GET'])
def get_character_schema():
    """Get the character profile schema definition.
    
    Returns:
    {
        "success": true,
        "schema": {
            "name": "string",
            "background": "string",
            "personality": ["string"],
            "skills": ["string"],
            "goals": ["string"],
            "relationships": {"string": "string"},
            "voice_notes": "string"
        }
    }
    """
    try:
        schema = {
            "name": "string",
            "background": "string",
            "personality": ["string"],
            "skills": ["string"],
            "goals": ["string"],
            "relationships": {"string": "string"},
            "voice_notes": "string"
        }
        
        return jsonify({
            'success': True,
            'schema': schema
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@characters_bp.route('/<character_id>/saved-poses', methods=['POST'])
@require_auth
def save_enhanced_pose(character_id):
    """Save an enhanced pose to a character for training.
    
    Request body:
    {
        "original_pose": "Basic pose text...",
        "enhanced_pose": "Enhanced pose text...",
        "enhancement_settings": {
            "style": "balanced",
            "detail_level": 50,
            "creativity_level": 60,
            // ... other settings
        },
        "tags": ["combat", "dialogue"]  // Optional
    }
    
    Returns:
    {
        "success": true,
        "message": "Pose saved successfully",
        "pose_id": "unique_pose_id"
    }
    """
    try:
        from app.models.character import Character
        from datetime import datetime
        import uuid
        
        # Get request data
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        original_pose = data.get('original_pose')
        enhanced_pose = data.get('enhanced_pose')
        enhancement_settings = data.get('enhancement_settings', {})
        
        if not original_pose or not original_pose.strip():
            return jsonify({
                'success': False,
                'error': 'original_pose is required'
            }), 400
            
        if not enhanced_pose or not enhanced_pose.strip():
            return jsonify({
                'success': False,
                'error': 'enhanced_pose is required'
            }), 400
        
        # Get the character
        character = Character.find_by_id(character_id)
        if not character:
            return jsonify({
                'success': False,
                'error': 'Character not found'
            }), 404
        
        # Check if user owns this character
        current_user = request.current_user
        if str(character.user_id) != str(current_user['_id']):
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Create pose data
        pose_id = str(uuid.uuid4())
        pose_data = {
            'id': pose_id,
            'original_pose': original_pose.strip(),
            'enhanced_pose': enhanced_pose.strip(),
            'enhancement_settings': enhancement_settings,
            'tags': data.get('tags', []),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Initialize metadata if it doesn't exist
        if not character.metadata:
            character.metadata = {}
        
        # Initialize saved_poses if it doesn't exist
        if 'saved_poses' not in character.metadata:
            character.metadata['saved_poses'] = []
        
        # Add the pose
        character.metadata['saved_poses'].append(pose_data)
        
        # Save the character
        character.save()
        
        return jsonify({
            'success': True,
            'message': 'Pose saved successfully',
            'pose_id': pose_id
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to save pose: {str(e)}'
        }), 500


@characters_bp.route('/<character_id>/saved-poses', methods=['GET'])
@require_auth
def get_saved_poses(character_id):
    """Get all saved enhanced poses for a character.
    
    Returns:
    {
        "success": true,
        "poses": [
            {
                "id": "pose_id",
                "original_pose": "...",
                "enhanced_pose": "...",
                "enhancement_settings": {...},
                "tags": [...],
                "timestamp": "2024-01-01T00:00:00"
            }
        ]
    }
    """
    try:
        from app.models.character import Character
        
        # Get the character
        character = Character.find_by_id(character_id)
        if not character:
            return jsonify({
                'success': False,
                'error': 'Character not found'
            }), 404
        
        # Check if user owns this character
        current_user = request.current_user
        if str(character.user_id) != str(current_user['_id']):
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Get saved poses
        saved_poses = []
        if character.metadata and 'saved_poses' in character.metadata:
            saved_poses = character.metadata['saved_poses']
        
        return jsonify({
            'success': True,
            'poses': saved_poses
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve poses: {str(e)}'
        }), 500


@characters_bp.route('/<character_id>/saved-poses/<pose_id>', methods=['DELETE'])
@require_auth
def delete_saved_pose(character_id, pose_id):
    """Delete a saved enhanced pose from a character.
    
    Returns:
    {
        "success": true,
        "message": "Pose deleted successfully"
    }
    """
    try:
        from app.models.character import Character
        
        # Get the character
        character = Character.find_by_id(character_id)
        if not character:
            return jsonify({
                'success': False,
                'error': 'Character not found'
            }), 404
        
        # Check if user owns this character
        current_user = request.current_user
        if str(character.user_id) != str(current_user['_id']):
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Find and remove the pose
        if not character.metadata or 'saved_poses' not in character.metadata:
            return jsonify({
                'success': False,
                'error': 'Pose not found'
            }), 404
        
        saved_poses = character.metadata['saved_poses']
        original_length = len(saved_poses)
        
        # Filter out the pose to delete
        character.metadata['saved_poses'] = [
            pose for pose in saved_poses if pose.get('id') != pose_id
        ]
        
        # Check if pose was found and removed
        if len(character.metadata['saved_poses']) == original_length:
            return jsonify({
                'success': False,
                'error': 'Pose not found'
            }), 404
        
        # Save the character
        character.save()
        
        return jsonify({
            'success': True,
            'message': 'Pose deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to delete pose: {str(e)}'
        }), 500


@characters_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors for character endpoints."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@characters_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors for character endpoints."""
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405 