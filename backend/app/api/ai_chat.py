from flask import Blueprint, request, jsonify, current_app
from app.services.character_creation_service import CharacterCreationService
from app.services.ai_client import AIClient
from app.middleware.auth_middleware import require_auth, get_current_identity
import os

ai_chat_bp = Blueprint('ai_chat', __name__)

# Global service instance
_creation_service = None

def get_creation_service():
    global _creation_service
    if _creation_service is None:
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        ai_client = AIClient(api_key=api_key)
        _creation_service = CharacterCreationService(ai_client)
    return _creation_service

@ai_chat_bp.route('/start', methods=['POST'])
@require_auth
def start_session():
    try:
        current_user = get_current_identity()
        user_id = current_user if isinstance(current_user, str) else current_user.get('id')
        
        service = get_creation_service()
        session_id = service.start_session(user_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error starting AI chat session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_chat_bp.route('/message', methods=['POST'])
@require_auth
def send_message():
    from app.services.ai_client import OpenRouterAPIError
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id or not message:
            return jsonify({'success': False, 'error': 'session_id and message are required'}), 400
            
        service = get_creation_service()
        response = service.get_ai_response(session_id, message)
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
    except OpenRouterAPIError as e:
        current_app.logger.error(f"AI Provider error: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f"AI Service Error: {str(e)}. Please check your OPENROUTER_API_KEY in the .env file."
        }), 502
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error in AI chat message: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_chat_bp.route('/finalize', methods=['POST'])
@require_auth
def finalize_session():
    from app.services.ai_client import OpenRouterAPIError
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'session_id is required'}), 400
            
        service = get_creation_service()
        character_data = service.finalize_character(session_id)
        
        return jsonify({
            'success': True,
            'character': character_data
        }), 200
    except OpenRouterAPIError as e:
        current_app.logger.error(f"AI Provider error during finalization: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f"AI Service Error during extraction: {str(e)}. Please check your API configuration."
        }), 502
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error finalizing AI chat: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
