"""
WebSocket service for real-time communication with frontend.
Handles long-running operations like description generation without HTTP timeouts.
"""

import base64
import traceback
from typing import Dict, Any, Optional
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
