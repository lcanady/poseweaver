"""
WebSocket service for real-time communication with frontend.
Handles long-running operations like description generation without HTTP timeouts.
"""

import base64
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, UTC
from flask import request, session
from flask_socketio import SocketIO, emit, disconnect
from flask_jwt_extended import decode_token, JWTManager
import logging

from app.services.description_service import DescriptionService
from app.services.ai_client import AIClient, OpenRouterAPIError
from app.services.usage_tracking_service import UsageTrackingService
from app.services.auth_service import AuthService
from app.models.user_mongo import User

logger = logging.getLogger(__name__)


class WebSocketService:
    """Service for handling WebSocket connections and events."""
    
    def __init__(self, socketio: SocketIO):
        """Initialize WebSocket service with SocketIO instance."""
        import os
        self.socketio = socketio
        
        # Get OpenRouter API key from environment
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
            
        self.ai_client = AIClient(openrouter_api_key)
        self.description_service = DescriptionService(self.ai_client)
        self.usage_service = UsageTrackingService()
        self.auth_service = AuthService()
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection with authentication."""
            try:
                # Authenticate user using JWT token
                if not auth or 'token' not in auth:
                    logger.warning("WebSocket connection attempt without token")
                    disconnect()
                    return False
                
                token = auth['token']
                user_id = self._authenticate_token(token)
                
                if not user_id:
                    logger.warning("WebSocket connection attempt with invalid token")
                    disconnect()
                    return False
                
                # Store user_id in session for this connection
                session['user_id'] = user_id
                
                logger.info(f"WebSocket connected: user_id={user_id}, sid={request.sid}")
                emit('connected', {'status': 'success', 'message': 'Connected successfully'})
                
            except Exception as e:
                logger.error(f"WebSocket connection error: {str(e)}")
                disconnect()
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            try:
                user_id = session.get('user_id')
                logger.info(f"WebSocket disconnected: user_id={user_id}, sid={request.sid}")
            except Exception as e:
                logger.error(f"WebSocket disconnect error: {str(e)}")
        
        @self.socketio.on('join_scene')
        def handle_join_scene(data):
            """Handle user joining a scene room."""
            try:
                user_id = self._get_user_from_session()
                if not user_id:
                    emit('error', {'message': 'Authentication required'})
                    return
                
                scene_id = data.get('scene_id')
                character_id = data.get('character_id')
                
                if not scene_id or not character_id:
                    emit('error', {'message': 'scene_id and character_id required'})
                    return
                
                # Validate character ownership
                from app.services.character_mgmt_service import CharacterManagementService
                character = CharacterManagementService.get_character(character_id, user_id)
                
                if not character:
                    emit('error', {'message': 'Character not found or access denied'})
                    return
                
                # Verify scene exists
                from app.services.scene_service import SceneService
                scene = SceneService.get_scene(scene_id, user_id)
                
                if not scene:
                    emit('error', {'message': 'Scene not found or access denied'})
                    return
                
                # Join the scene room
                from flask_socketio import join_room
                join_room(scene_id)
                
                logger.info(f"User {user_id} ({character.name}) joined scene {scene_id}")
                
                # Notify others in the room
                emit('user_joined', {
                    'user_id': user_id,
                    'character_id': character_id,
                    'character_name': character.name,
                    'character_avatar': character.profile_image,
                    'timestamp': datetime.now(UTC).isoformat()
                }, room=scene_id, skip_sid=request.sid)
                
                # Confirm to the joining user
                emit('scene_joined', {
                    'scene_id': scene_id,
                    'character': {
                        'id': character_id,
                        'name': character.name,
                        'avatar': character.profile_image
                    },
                    'message': f'Joined scene as {character.name}'
                })
                
            except Exception as e:
                logger.error(f"Error joining scene: {str(e)}")
                emit('error', {'message': 'Failed to join scene'})
        
        @self.socketio.on('leave_scene')
        def handle_leave_scene(data):
            """Handle user leaving a scene room."""
            try:
                user_id = self._get_user_from_session()
                scene_id = data.get('scene_id')
                character_name = data.get('character_name', 'Unknown')
                
                if scene_id:
                    from flask_socketio import leave_room
                    leave_room(scene_id)
                    
                    logger.info(f"User {user_id} ({character_name}) left scene {scene_id}")
                    
                    # Notify others
                    emit('user_left', {
                        'user_id': user_id,
                        'character_name': character_name,
                        'timestamp': datetime.now(UTC).isoformat()
                    }, room=scene_id)
                    
            except Exception as e:
                logger.error(f"Error leaving scene: {str(e)}")
        
        @self.socketio.on('send_pose')
        def handle_send_pose(data):
            """Handle pose sent by user in a scene."""
            try:
                user_id = self._get_user_from_session()
                if not user_id:
                    emit('error', {'message': 'Authentication required'})
                    return
                
                scene_id = data.get('scene_id')
                character_id = data.get('character_id')
                pose_text = data.get('pose_text')
                
                if not all([scene_id, character_id, pose_text]):
                    emit('error', {'message': 'scene_id, character_id, and pose_text required'})
                    return
                
                # Validate character ownership
                from app.services.character_mgmt_service import CharacterManagementService
                character = CharacterManagementService.get_character(character_id, user_id)
                
                if not character:
                    emit('error', {'message': 'Character not found or access denied'})
                    return
                
                # Check if this is a command
                from app.services.command_service import CommandService
                command_service = CommandService()
                
                if command_service.is_command(pose_text):
                    # Execute command
                    result = command_service.execute_command(
                        text=pose_text,
                        user_id=user_id,
                        scene_id=scene_id,
                        character_name=character.name
                    )
                    
                    # Broadcast system messages to the room
                    if result.get('success'):
                        for message in result.get('system_messages', []):
                            emit('system_message', {
                                'type': 'system_message',
                                'message': message,
                                'scene_id': scene_id,
                                'command': result.get('command'),
                                'character_name': character.name,
                                'timestamp': datetime.now(UTC).isoformat()
                            }, room=scene_id)
                else:
                    # Save pose to database
                    from app.services.scene_service import SceneService
                    from app.models.scene import PoseType
                    
                    try:
                        result = SceneService.add_pose(
                            scene_id=scene_id,
                            character_id=character_id,
                            character_name=character.name,
                            pose_text=pose_text,
                            pose_type=PoseType.MIXED
                        )
                        
                        if result:
                            scene, pose = result
                            logger.info(f"Saved pose to scene {scene_id}: {pose.id}")
                    except Exception as e:
                        logger.error(f"Failed to save pose to database: {str(e)}")
                    
                    # Broadcast normal pose to the room
                    emit('new_pose', {
                        'character_id': character_id,
                        'character_name': character.name,
                        'character_avatar': character.profile_image,
                        'pose_text': pose_text,
                        'user_id': user_id,
                        'timestamp': datetime.now(UTC).isoformat()
                    }, room=scene_id)
                
            except Exception as e:
                logger.error(f"Error sending pose: {str(e)}")
                emit('error', {'message': 'Failed to send pose'})
        
        @self.socketio.on('generate_description')
        def handle_generate_description(data):
            """Handle description generation request via WebSocket."""
            try:
                logger.info(f"Received generate_description request: sid={request.sid}")
                # Get authenticated user
                user_id = self._get_user_from_session()
                if not user_id:
                    logger.warning(f"Unauthorized generate_description request: sid={request.sid}")
                    emit('description_error', {'error': 'Authentication required'})
                    return
                
                # Emit progress update
                emit('description_progress', {
                    'status': 'starting',
                    'message': 'Validating request and checking usage limits...'
                })
                
                # Validate request data
                if not self._validate_description_request(data):
                    emit('description_error', {'error': 'Invalid request data'})
                    return
                
                # Check usage limits
                user = User.find_by_id(user_id)
                usage_check = self.usage_service.check_pose_generation_limit(user)
                logger.info(f"Usage check for user {user_id}: {usage_check}")
                if not usage_check['can_generate']:
                    logger.warning(f"Generation limit reached for user {user_id}")
                    emit('description_error', {
                        'error': 'Generation limit reached',
                        'usage_info': usage_check
                    })
                    return
                
                # Emit progress update
                emit('description_progress', {
                    'status': 'processing',
                    'message': 'Processing image and generating description...'
                })
                
                # Process the description generation
                result = self._process_description_generation(data, user)
                
                # Emit success result
                emit('description_complete', {
                    'status': 'success',
                    'result': result
                })
                
            except OpenRouterAPIError as e:
                logger.error(f"OpenRouter API error in WebSocket: {str(e)}")
                emit('description_error', {
                    'error': f'AI service error: {str(e)}'
                })
            except Exception as e:
                logger.error(f"WebSocket description generation error: {str(e)}")
                logger.error(traceback.format_exc())
                emit('description_error', {
                    'error': 'An unexpected error occurred during description generation'
                })
    
    def broadcast_system_message(self, scene_id: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Broadcast a system message to all clients in a scene.
        
        System messages are displayed differently from normal poses 
        (grey text, bold, no avatar).
        
        Args:
            scene_id: ID of the scene to broadcast to
            message: The system message text
            metadata: Optional additional metadata
        """
        try:
            message_data = {
                'type': 'system_message',
                'message': message,
                'scene_id': scene_id,
                'timestamp': datetime.now(UTC).isoformat()
            }
            
            # Add any additional metadata
            if metadata:
                message_data.update(metadata)
            
            # Broadcast to all clients in the scene's room
            logger.info(f"Broadcasting system message to scene {scene_id}: {message}")
            self.socketio.emit('system_message', message_data, room=scene_id)
            
        except Exception as e:
            logger.error(f"Error broadcasting system message: {str(e)}")
    
    def _authenticate_token(self, token: str) -> Optional[str]:
        """Authenticate JWT token and return user_id."""
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decode JWT token
            decoded_token = decode_token(token)
            user_id = decoded_token.get('sub')
            
            # Verify user exists and is active
            user = self.auth_service.get_user_by_id(user_id)
            if not user or not user.get('is_active', True):
                return None
            
            return user_id
            
        except Exception as e:
            logger.debug(f"JWT authentication failed, trying Firebase: {str(e)}")
            
            # Try Firebase Token
            try:
                from firebase_admin import auth
                decoded_token = auth.verify_id_token(token)
                
                # Handle user login/creation via AuthService
                user = self.auth_service.handle_firebase_login(decoded_token)
                
                if user and user.is_active:
                    return str(user.id)
                    
            except Exception as fe:
                logger.error(f"Firebase token verification failed: {str(fe)}")
            
            return None
    
    def _get_user_from_session(self) -> Optional[str]:
        """Get authenticated user_id from WebSocket session."""
        try:
            return session.get('user_id')
        except Exception:
            return None
    
    def _validate_description_request(self, data: Dict[str, Any]) -> bool:
        """Validate description generation request data."""
        required_fields = ['image_data', 'image_format']
        
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate description style
        style = data.get('description_style', 'balanced')
        if style not in ['minimal', 'balanced', 'elaborate']:
            logger.warning(f"Invalid description style: {style}")
            return False
        
        return True
    
    def _process_description_generation(self, data: Dict[str, Any], user: User) -> Dict[str, Any]:
        """Process description generation and return result."""
        try:
            # Extract request parameters
            image_data_b64 = data['image_data']
            image_format = data['image_format']
            
            # Get prompt or use default
            user_prompt = data.get('user_prompt', '').strip()
            if not user_prompt:
                user_prompt = "Describe the character's physical appearance, focusing on body type, facial features, hair, and visible traits. Keep the description open-ended and suitable for adding an outfit later."
            description_style = data.get('description_style', 'balanced')
            focus_areas = data.get('focus_areas', [])
            
            # Decode base64 image data
            logger.info(f"Decoding image data (length: {len(image_data_b64)})")
            image_data = base64.b64decode(image_data_b64)
            
            # Generate description
            logger.info(f"Calling description_service.generate_description for user {user.id}")
            result = self.description_service.generate_description(
                image_data=image_data,
                image_format=image_format,
                user_prompt=user_prompt,
                description_style=description_style,
                focus_areas=focus_areas if focus_areas else None
            )
            
            # Update usage tracking
            self.usage_service.use_generation(user)
            logger.info(f"Successfully generated and recorded usage for user {user.id}")
            
            # Convert result to dictionary
            return {
                'description': result.description,
                'style': result.style,
                'prompt_used': result.prompt_used,
                'model_used': result.model_used,
                'timestamp': result.timestamp,
                'word_count': result.word_count,
                'processing_time_ms': result.processing_time_ms
            }
            
        except Exception as e:
            logger.error(f"Description generation processing error: {str(e)}")
            raise
