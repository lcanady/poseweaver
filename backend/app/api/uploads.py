"""
File Upload API endpoints.

Provides endpoints for uploading and retrieving files.
"""
import os
import uuid
from flask import Blueprint, request, jsonify, current_app, send_from_directory, session
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from app.middleware.auth_middleware import get_current_identity
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps

# Create blueprint
uploads_bp = Blueprint('uploads', __name__)

# Configure upload settings
# Use absolute paths to avoid working directory issues
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.abspath(os.path.join(os.path.dirname(__file__), '../../uploads')))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure upload directory exists
def ensure_upload_dir():
    """Ensure the upload directory exists."""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    # Create subdirectories for different upload types
    avatars_dir = os.path.join(UPLOAD_FOLDER, 'avatars')
    if not os.path.exists(avatars_dir):
        os.makedirs(avatars_dir)


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def auth_required():
    """Custom decorator to support both session and JWT authentication."""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # First check if user is authenticated via session
            if session.get('user'):
                return fn(*args, **kwargs)
            
            # If not in session, try JWT
            try:
                verify_jwt_in_request(optional=True)
                current_identity = get_current_identity()
                if current_identity:
                    return fn(*args, **kwargs)
            except Exception as e:
                current_app.logger.error(f"JWT verification error: {str(e)}")
            
            # If neither authentication method worked
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
            
        return decorator
    return wrapper

@uploads_bp.route('/avatar', methods=['POST'])
@auth_required()
def upload_avatar():
    """Upload a character avatar image.
    
    Returns:
        200 OK: The URL of the uploaded file
        400 Bad Request: If no file is provided or file type is not allowed
        500 Internal Server Error: If there was an error saving the file
    """
    # Get user identity from session or JWT
    current_user = None
    
    if session.get('user'):
        current_user = session.get('user')
    else:
        try:
            current_user = get_current_identity()
        except Exception as e:
            current_app.logger.error(f"Error getting JWT identity: {str(e)}")
    
    if not current_user:
        return jsonify({
            'success': False,
            'message': 'Authentication required'
        }), 401
    
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No file part in the request'
        }), 400
        
    file = request.files['file']
    
    # If the user does not select a file, the browser submits an
    # empty file without a filename
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No file selected'
        }), 400
        
    if file and allowed_file(file.filename):
        # Create a unique filename to prevent collisions
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Ensure upload directory exists
        ensure_upload_dir()
        
        # Save to avatars subdirectory
        avatar_path = os.path.join(UPLOAD_FOLDER, 'avatars', unique_filename)
        
        try:
            file.save(avatar_path)
            
            # Generate the URL for the uploaded file
            base_url = request.host_url.rstrip('/')
            file_url = f"{base_url}/api/uploads/avatars/{unique_filename}"
            
            return jsonify({
                'success': True,
                'file_url': file_url,
                'filename': unique_filename
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Error saving file: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error saving file'
            }), 500
    
    return jsonify({
        'success': False,
        'message': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
    }), 400


@uploads_bp.route('/avatars/<filename>', methods=['GET'])
def get_avatar(filename):
    """Retrieve an avatar image by filename.
    
    Returns:
        200 OK: The image file
        404 Not Found: If the file does not exist
    """
    try:
        # Use absolute paths for file serving
        avatar_dir = os.path.join(UPLOAD_FOLDER, 'avatars')
        current_app.logger.info(f"Serving avatar from: {avatar_dir}, filename: {filename}")
        return send_from_directory(avatar_dir, filename)
    except Exception as e:
        current_app.logger.error(f"Error retrieving avatar: {str(e)}, from path: {os.path.join(avatar_dir, filename)}")
        return jsonify({
            'success': False,
            'message': 'Avatar not found'
        }), 404
