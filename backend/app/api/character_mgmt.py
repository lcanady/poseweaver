"""
Character Management API endpoints.

Provides CRUD operations for character management using MongoDB.
"""
from flask import Blueprint, request, jsonify, session, current_app
from flask_jwt_extended import verify_jwt_in_request
from bson import ObjectId
from http import HTTPStatus

from app.services.character_mgmt_service import CharacterManagementService
from app.models.character import Character
from app.models.user_mongo import User
from app.middleware.auth_middleware import require_auth, get_current_identity

# Create blueprint
character_mgmt_bp = Blueprint('character_mgmt', __name__)


def get_user_id_from_session_or_jwt():
    """Helper function to get user ID from session or JWT.
    
    Returns:
        str: User ID if found, None otherwise
    """
    # Check if user was set by require_auth middleware
    if hasattr(request, 'current_user') and request.current_user:
        return str(request.current_user.id)

    # First check if user is authenticated via session
    user_id = session.get('user_id')
    
    # If not in session, try JWT
    if not user_id:
        try:
            verify_jwt_in_request(optional=True)
            current_user = get_current_identity()
            if current_user:
                # Extract user_id from identity (handle both string and dict formats)
                user_id = current_user if isinstance(current_user, str) else current_user.get('id')
        except Exception as e:
            current_app.logger.error(f"JWT verification error: {str(e)}")
    
    return user_id

@character_mgmt_bp.route('', methods=['POST'])
@require_auth
def create_character():
    """Create a new character.
    
    Request body:
    {
        "name": "Character Name",
        "description": "Character description",
        "profile_image": "https://example.com/image.jpg",  // Optional
        "tags": ["tag1", "tag2"],  // Optional
        "metadata": {}  // Optional additional data
    }
    
    Returns:
        201 Created: The created character
        400 Bad Request: If validation fails or name already exists
        401 Unauthorized: If not authenticated
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or 'name' not in data:
        return jsonify({
            'success': False,
            'message': 'Character name is required'
        }), HTTPStatus.BAD_REQUEST
    
    # Get user ID from session or JWT
    user_id = get_user_id_from_session_or_jwt()
    
    if not user_id:
        current_app.logger.error("No user ID found in session or JWT identity")
        return jsonify({
            'success': False,
            'message': 'Authentication error: invalid user identity'
        }), HTTPStatus.UNAUTHORIZED

    try:
        # Get user to check subscription status and character limits
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), HTTPStatus.UNAUTHORIZED
        
        # Get current character count for the user
        current_characters = CharacterManagementService.list_characters(
            user_id=user_id,
            include_inactive=False
        )
        current_count = len(current_characters)
        
        # Check if user can create another character
        if not user.can_create_character(current_count):
            character_limit = user.get_character_limit()
            effective_status = user.get_effective_subscription_status()
            
            # Provide different messages based on subscription status
            if effective_status == 'expired':
                message = f"Your premium subscription has expired. You can only access your first {character_limit} characters. Please upgrade to create more characters."
            else:
                message = f"You've reached the character limit ({character_limit} characters). Upgrade to premium for unlimited characters."
            
            return jsonify({
                'success': False,
                'message': message,
                'character_limit': character_limit,
                'current_count': current_count,
                'needs_upgrade': user.needs_upgrade_for_characters(),
                'subscription_status': effective_status
            }), HTTPStatus.FORBIDDEN
        
        # Create the character
        character = CharacterManagementService.create_character(
            user_id=user_id,
            name=data['name'],
            description=data.get('description', ''),
            profile_image=data.get('profile_image'),
            tags=data.get('tags'),
            metadata=data.get('metadata', {})
        )
        
        return jsonify({
            'success': True,
            'data': character.to_dict()
        }), HTTPStatus.CREATED
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        current_app.logger.error(f"Error creating character: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while creating the character'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@character_mgmt_bp.route('/<character_id>', methods=['GET'])
@require_auth
def get_character(character_id):
    """Get a character by ID.
    
    Returns:
        200 OK: The character data
        403 Forbidden: If not the owner of the character
        404 Not Found: If character doesn't exist
    """
    # Get user ID from session or JWT
    user_id = get_user_id_from_session_or_jwt()
    
    if not user_id:
        current_app.logger.error("No user ID found in session or JWT identity")
        return jsonify({
            'success': False,
            'message': 'Authentication error: invalid user identity'
        }), HTTPStatus.UNAUTHORIZED
    
    try:
        character = CharacterManagementService.get_character(
            character_id=character_id,
            user_id=user_id
        )
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found or access denied'
            }), HTTPStatus.NOT_FOUND
            
        return jsonify({
            'success': True,
            'data': character.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting character: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving the character'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@character_mgmt_bp.route('', methods=['GET'])
@require_auth
def list_characters():
    """List all characters for the current user.
    
    Query parameters:
        include_inactive (bool): Include inactive characters (default: false)
        limit (int): Maximum number of characters to return (default: 100)
        skip (int): Number of characters to skip (for pagination, default: 0)
        sort (str): Field to sort by (default: name)
        order (str): Sort order (asc or desc, default: asc)
    
    Returns:
        200 OK: List of characters
    """
    # Get user ID from session or JWT
    user_id = get_user_id_from_session_or_jwt()
    
    # Get query parameters
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 for safety
    skip = max(0, int(request.args.get('skip', 0)))
    sort_field = request.args.get('sort', 'name')
    sort_direction = -1 if request.args.get('order', 'asc').lower() == 'desc' else 1
    
    if not user_id:
        current_app.logger.error("No user ID found in session or JWT identity")
        return jsonify({
            'success': False,
            'message': 'Authentication error: invalid user identity'
        }), HTTPStatus.UNAUTHORIZED
    
    try:
        # Get user to check subscription status
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), HTTPStatus.UNAUTHORIZED
        
        characters = CharacterManagementService.list_characters(
            user_id=user_id,
            include_inactive=include_inactive,
            limit=limit,
            skip=skip,
            sort_field=sort_field,
            sort_direction=sort_direction
        )
        
        # Apply character access limits based on subscription
        effective_status = user.get_effective_subscription_status()
        character_limit = user.get_character_limit()
        
        # For non-premium users (free/expired), limit access to first 3 characters
        if character_limit != -1:  # Not unlimited
            characters = characters[:character_limit]
        
        return jsonify({
            'success': True,
            'data': [char.to_dict() for char in characters],
            'meta': {
                'total': len(characters),
                'limit': limit,
                'skip': skip,
                'sort': sort_field,
                'order': 'desc' if sort_direction == -1 else 'asc',
                'character_limit': character_limit,
                'subscription_status': effective_status,
                'needs_upgrade': user.needs_upgrade_for_characters()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing characters: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while listing characters'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@character_mgmt_bp.route('/<character_id>', methods=['PUT'])
@require_auth
def update_character(character_id):
    """Update a character.
    
    Request body can include any fields to update.
    
    Returns:
        200 OK: The updated character
        400 Bad Request: If validation fails
        403 Forbidden: If not the owner of the character
        404 Not Found: If character doesn't exist
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided for update'
        }), HTTPStatus.BAD_REQUEST
    
    # Get user ID from session or JWT
    user_id = get_user_id_from_session_or_jwt()
    
    if not user_id:
        current_app.logger.error("No user ID found in session or JWT identity")
        return jsonify({
            'success': False,
            'message': 'Authentication error: invalid user identity'
        }), HTTPStatus.UNAUTHORIZED
    
    try:
        # Don't allow updating these fields directly
        for field in ['id', '_id', 'user_id', 'created_at']:
            data.pop(field, None)
        
        # Update the character
        character = CharacterManagementService.update_character(
            character_id=character_id,
            user_id=user_id,
            **data
        )
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found or access denied'
            }), HTTPStatus.NOT_FOUND
            
        return jsonify({
            'success': True,
            'data': character.to_dict()
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        current_app.logger.error(f"Error updating character: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the character'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@character_mgmt_bp.route('/<character_id>', methods=['DELETE'])
@require_auth
def delete_character(character_id):
    """Delete a character (soft delete).
    
    Returns:
        204 No Content: If deletion was successful
        403 Forbidden: If not the owner of the character
        404 Not Found: If character doesn't exist
    """
    # Get user ID from session or JWT
    user_id = get_user_id_from_session_or_jwt()
    
    if not user_id:
        current_app.logger.error("No user ID found in session or JWT identity")
        return jsonify({
            'success': False,
            'message': 'Authentication error: invalid user identity'
        }), HTTPStatus.UNAUTHORIZED
    
    try:
        success = CharacterManagementService.delete_character(
            character_id=character_id,
            user_id=user_id
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Character not found or access denied'
            }), HTTPStatus.NOT_FOUND
            
        return '', HTTPStatus.NO_CONTENT
        
    except Exception as e:
        current_app.logger.error(f"Error deleting character: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the character'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@character_mgmt_bp.route('/featured', methods=['GET'])
def get_featured_characters():
    """Get featured characters for the homepage carousel.
    
    Returns characters that have profile images and complete descriptions.
    No authentication required for public display.
    
    Query parameters:
        limit (int): Maximum number of characters to return (default: 6, max: 12)
    
    Returns:
        200 OK: List of featured characters
    """
    limit = min(int(request.args.get('limit', 6)), 12)  # Max 12 for performance
    
    try:
        # Find characters with profile images and descriptions
        from app.models.character import Character
        from app.services.mongodb_service import get_mongodb_service
        
        mongodb = get_mongodb_service()
        
        # Query for characters with profile images and descriptions
        # Only include active characters with both profile_image and description
        query = {
            'is_active': True,
            'profile_image': {'$exists': True, '$ne': None, '$ne': ''},
            'description': {'$exists': True, '$ne': None, '$ne': ''}
        }
        
        # Get characters from database with random sampling
        pipeline = [
            {'$match': query},
            {'$sample': {'size': limit * 3}},  # Get more than needed for better randomization
            {'$limit': limit}
        ]
        
        results = list(mongodb.db[Character.COLLECTION_NAME].aggregate(pipeline))
        
        # Convert to Character objects and then to dicts
        featured_characters = []
        for doc in results:
            try:
                # Convert ObjectId to string for user_id if needed
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
                if 'user_id' in doc and hasattr(doc['user_id'], 'binary'):
                    doc['user_id'] = str(doc['user_id'])
                
                character = Character.from_dict(doc)
                if character:
                    char_dict = character.to_dict()
                    # Remove sensitive user information for public display
                    char_dict.pop('user_id', None)
                    featured_characters.append(char_dict)
            except Exception as e:
                current_app.logger.warning(f"Error processing featured character: {str(e)}")
                continue
        
        return jsonify({
            'success': True,
            'data': featured_characters,
            'meta': {
                'total': len(featured_characters),
                'limit': limit
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching featured characters: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching featured characters'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@character_mgmt_bp.route('/search', methods=['GET'])
@require_auth
def search_characters():
    """Search for characters by name or tags.
    
    Query parameters:
        q (str): Search query (required)
        include_inactive (bool): Include inactive characters (default: false)
        limit (int): Maximum number of results (default: 20, max: 100)
    
    Returns:
        200 OK: List of matching characters
    """
    query = request.args.get('q')
    
    if not query:
        return jsonify({
            'success': False,
            'message': 'Search query is required'
        }), HTTPStatus.BAD_REQUEST
    
    # Get user ID from session or JWT
    user_id = get_user_id_from_session_or_jwt()
    
    if not user_id:
        current_app.logger.error("No user ID found in session or JWT identity")
        return jsonify({
            'success': False,
            'message': 'Authentication error: invalid user identity'
        }), HTTPStatus.UNAUTHORIZED
    
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    limit = min(int(request.args.get('limit', 20)), 100)  # Max 100 for safety
    
    try:
        results = CharacterManagementService.search_characters(
            user_id=user_id,
            query=query,
            limit=limit,
            include_inactive=include_inactive
        )
        
        return jsonify({
            'success': True,
            'data': [char.to_dict() for char in results],
            'meta': {
                'query': query,
                'total': len(results),
                'limit': limit
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error searching characters: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while searching characters'
        }), HTTPStatus.INTERNAL_SERVER_ERROR
