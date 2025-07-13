"""
Character API endpoints for MUSH Pose Editor.

Provides endpoints for character brain dump processing and management.
"""
from flask import Blueprint, request, jsonify
from app.services.character_service import CharacterService, CharacterProfile
from app.services.venice_client import VeniceClient, VeniceAPIError

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
        character_profile = character_service.process_brain_dump(
            brain_dump, existing_character
        )
        
        return jsonify({
            'success': True,
            'character': character_profile.to_dict()
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


@characters_bp.route('/validate', methods=['POST'])
def validate_character():
    """Validate character profile data structure.
    
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
        
        # Get character data
        character_data = data.get('character')
        if not character_data:
            return jsonify({
                'success': False,
                'error': 'character data is required'
            }), 400
        
        # Validate character data
        try:
            character_service = get_character_service()
            character_service._validate_character_data(character_data)
            return jsonify({
                'success': True,
                'valid': True,
                'errors': []
            })
        except ValueError as e:
            return jsonify({
                'success': True,
                'valid': False,
                'errors': [str(e)]
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@characters_bp.route('/schema', methods=['GET'])
def get_character_schema():
    """Get the character profile data schema.
    
    Returns:
    {
        "success": true,
        "schema": {
            "fields": {
                "name": {"type": "string", "required": true},
                "background": {"type": "string", "required": true},
                // ... other fields
            }
        }
    }
    """
    schema = {
        "fields": {
            "name": {
                "type": "string",
                "required": True,
                "description": "Character's full name"
            },
            "background": {
                "type": "string", 
                "required": True,
                "description": "Character's history, origin, and life story"
            },
            "personality": {
                "type": "array",
                "items": {"type": "string"},
                "required": True,
                "description": "List of personality traits and characteristics"
            },
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "required": True,
                "description": "List of abilities, talents, and competencies"
            },
            "goals": {
                "type": "array",
                "items": {"type": "string"},
                "required": True,
                "description": "List of character motivations and objectives"
            },
            "relationships": {
                "type": "object",
                "required": True,
                "description": "Important relationships (name: type)"
            },
            "voice_notes": {
                "type": "string",
                "required": True,
                "description": "Notes about how the character speaks"
            }
        }
    }
    
    return jsonify({
        'success': True,
        'schema': schema
    })


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