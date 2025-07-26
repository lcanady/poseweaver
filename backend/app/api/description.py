"""
Description writing API endpoints for generating detailed physical descriptions from images.

Provides endpoints for image-based description generation with usage tracking and paywall integration.
"""
import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.services.description_service import DescriptionService
from app.services.venice_client import VeniceClient, VeniceAPIError
from app.services.usage_tracking_service import require_pose_generation_limit, get_usage_info

description_bp = Blueprint('description', __name__)

# Global service instance
description_service = None


def get_description_service():
    """Get description service instance."""
    global description_service
    if description_service is None:
        api_key = os.getenv('VENICE_API_KEY')
        if not api_key:
            raise ValueError("VENICE_API_KEY environment variable is required")
        venice_client = VeniceClient(api_key=api_key)
        description_service = DescriptionService(venice_client)
    return description_service


@description_bp.route('/generate', methods=['POST'])
@require_pose_generation_limit  # Reuse existing usage tracking
def generate_description():
    """Generate a detailed physical description from an image.
    
    Request form data:
    - image: Image file (required)
    - prompt: User prompt describing what to focus on (required)
    - style: Description style - minimal, balanced, elaborate (optional, default: balanced)
    - focus_areas: Comma-separated list of areas to focus on (optional)
    - detail_level: Detail level 0-100 (optional, default: 70)
    - creativity_level: Creativity level 0-100 (optional, default: 50)
    - formality_level: Formality level 0-100 (optional, default: 60)
    - include_emotional_context: Include emotional context true/false (optional, default: false)
    - include_sensory_details: Include sensory details true/false (optional, default: false)
    
    Returns:
    {
        "success": true,
        "description": "Generated description text...",
        "metadata": {
            "style": "balanced",
            "prompt_used": "...",
            "model_used": "...",
            "word_count": 150,
            "processing_time_ms": 2500
        },
        "usage_info": {
            "generations_used": 15,
            "generations_limit": 20,
            "subscription_status": "free"
        }
    }
    """
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No image file selected'
            }), 400
        
        # Get prompt from form data
        prompt = request.form.get('prompt', '').strip()
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt is required'
            }), 400
        
        # Get optional parameters
        style = request.form.get('style', 'balanced').lower()
        if style not in ['minimal', 'balanced', 'elaborate']:
            return jsonify({
                'success': False,
                'error': 'Style must be minimal, balanced, or elaborate'
            }), 400
        
        # Parse focus areas if provided
        focus_areas = None
        focus_areas_str = request.form.get('focus_areas', '').strip()
        if focus_areas_str:
            focus_areas = [area.strip() for area in focus_areas_str.split(',') if area.strip()]
        
        # Parse advanced settings with validation
        try:
            detail_level = int(request.form.get('detail_level', 70))
            if not 0 <= detail_level <= 100:
                raise ValueError("Detail level must be between 0 and 100")
        except (ValueError, TypeError):
            detail_level = 70
            
        try:
            creativity_level = int(request.form.get('creativity_level', 50))
            if not 0 <= creativity_level <= 100:
                raise ValueError("Creativity level must be between 0 and 100")
        except (ValueError, TypeError):
            creativity_level = 50
            
        try:
            formality_level = int(request.form.get('formality_level', 60))
            if not 0 <= formality_level <= 100:
                raise ValueError("Formality level must be between 0 and 100")
        except (ValueError, TypeError):
            formality_level = 60
            
        # Parse boolean settings
        include_emotional_context = request.form.get('include_emotional_context', 'false').lower() == 'true'
        include_sensory_details = request.form.get('include_sensory_details', 'false').lower() == 'true'
        
        # Validate image file
        filename = secure_filename(image_file.filename)
        if not filename:
            return jsonify({
                'success': False,
                'error': 'Invalid filename'
            }), 400
        
        # Get file extension
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # Get service instance
        service = get_description_service()
        
        # Validate image format
        if not service.validate_image_format(file_ext):
            return jsonify({
                'success': False,
                'error': f'Unsupported image format: {file_ext}. Supported formats: jpg, jpeg, png, webp, gif'
            }), 400
        
        # Read image data
        image_data = image_file.read()
        
        # Check file size
        if len(image_data) > service.get_max_image_size():
            return jsonify({
                'success': False,
                'error': f'Image file too large. Maximum size: {service.get_max_image_size() // (1024*1024)}MB'
            }), 400
        
        # Generate description with all settings
        result = service.generate_description(
            image_data=image_data,
            image_format=file_ext,
            user_prompt=prompt,
            description_style=style,
            focus_areas=focus_areas,
            detail_level=detail_level,
            creativity_level=creativity_level,
            formality_level=formality_level,
            include_emotional_context=include_emotional_context,
            include_sensory_details=include_sensory_details
        )
        
        # Get usage information for response
        user_id = request.user_id if hasattr(request, 'user_id') else None
        usage_info = get_usage_info(user_id) if user_id else None
        
        # Build response
        response_data = {
            'success': True,
            'description': result.description,
            'metadata': {
                'style': result.style,
                'prompt_used': result.prompt_used,
                'model_used': result.model_used,
                'word_count': result.word_count,
                'processing_time_ms': result.processing_time_ms,
                'timestamp': result.timestamp
            }
        }
        
        # Add usage info if available
        if usage_info:
            response_data['usage_info'] = usage_info
        
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


@description_bp.route('/supported-formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported image formats.
    
    Returns:
    {
        "success": true,
        "formats": ["jpg", "jpeg", "png", "webp", "gif"],
        "max_size_mb": 10
    }
    """
    try:
        service = get_description_service()
        
        return jsonify({
            'success': True,
            'formats': ['jpg', 'jpeg', 'png', 'webp', 'gif'],
            'max_size_mb': service.get_max_image_size() // (1024 * 1024)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@description_bp.route('/styles', methods=['GET'])
def get_description_styles():
    """Get available description styles and their descriptions.
    
    Returns:
    {
        "success": true,
        "styles": {
            "minimal": {
                "name": "Minimal",
                "description": "Concise but vivid descriptions focusing on key elements"
            },
            "balanced": {
                "name": "Balanced", 
                "description": "Comprehensive detail balancing features, clothing, and posture"
            },
            "elaborate": {
                "name": "Elaborate",
                "description": "Rich, detailed descriptions with extensive visual information"
            }
        }
    }
    """
    return jsonify({
        'success': True,
        'styles': {
            'minimal': {
                'name': 'Minimal',
                'description': 'Concise but vivid descriptions focusing on key elements',
                'typical_length': '2-4 sentences'
            },
            'balanced': {
                'name': 'Balanced',
                'description': 'Comprehensive detail balancing features, clothing, and posture',
                'typical_length': '4-8 sentences'
            },
            'elaborate': {
                'name': 'Elaborate', 
                'description': 'Rich, detailed descriptions with extensive visual information',
                'typical_length': '8-15+ sentences'
            }
        }
    })


@description_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@description_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405


@description_bp.errorhandler(413)
def request_entity_too_large(error):
    """Handle 413 errors (file too large)."""
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size: 10MB'
    }), 413
