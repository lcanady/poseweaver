"""
Setup API endpoints for first-time application initialization.
"""
from flask import Blueprint, request, jsonify
from ..models.user_mongo import User
from ..services.mongodb_service import get_mongodb_service
import logging

setup_bp = Blueprint('setup', __name__)
logger = logging.getLogger(__name__)

@setup_bp.route('/check', methods=['GET'])
def check_setup_status():
    """Check if the application needs initial setup (no admin users exist)."""
    try:
        mongodb_service = get_mongodb_service()
        
        # Check if MongoDB is connected
        if mongodb_service.db is None:
            logger.warning("MongoDB not connected - assuming setup is needed")
            return jsonify({
                'success': True,
                'needs_setup': True,
                'admin_count': 0,
                'mongodb_connected': False,
                'message': 'MongoDB not connected - running in development mode'
            })
        
        # Check if any admin users exist
        admin_count = mongodb_service.count_documents(
            User.COLLECTION_NAME,
            {'is_admin': True}
        )
        
        needs_setup = admin_count == 0
        
        return jsonify({
            'success': True,
            'needs_setup': needs_setup,
            'admin_count': admin_count,
            'mongodb_connected': True
        })
        
    except Exception as e:
        logger.error(f"Error checking setup status: {e}")
        # Return a more informative error response
        return jsonify({
            'success': False,
            'error': 'Failed to check setup status',
            'details': str(e),
            'needs_setup': True  # Default to needing setup if we can't check
        }), 200  # Return 200 instead of 500 so frontend can handle it

@setup_bp.route('/create-admin', methods=['POST'])
def create_first_admin():
    """Create the first admin user during initial setup."""
    try:
        # First, verify that no admin users exist
        mongodb_service = get_mongodb_service()
        admin_count = mongodb_service.count_documents(
            User.COLLECTION_NAME,
            {'is_admin': True}
        )
        
        if admin_count > 0:
            return jsonify({
                'error': 'Admin users already exist. Initial setup is not needed.'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        display_name = data.get('display_name', '').strip()
        
        # Validate required fields
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        if not display_name:
            display_name = email.split('@')[0]
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Check if user with this email already exists
        existing_user = User.find_by_email(email)
        if existing_user:
            # If user exists but is not admin, make them admin
            existing_user.is_admin = True
            existing_user.is_active = True
            existing_user.save()
            
            return jsonify({
                'success': True,
                'message': f'User {email} has been granted admin privileges',
                'user': {
                    'id': str(existing_user.id),
                    'email': existing_user.email,
                    'display_name': existing_user.display_name,
                    'is_admin': existing_user.is_admin
                }
            })
        
        # Create new admin user
        try:
            admin_user = User.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            
            # Set admin privileges
            admin_user.is_admin = True
            admin_user.is_active = True
            admin_user.save()
            
            logger.info(f"First admin user created: {email}")
            
            return jsonify({
                'success': True,
                'message': 'First admin user created successfully',
                'user': {
                    'id': str(admin_user.id),
                    'email': admin_user.email,
                    'display_name': admin_user.display_name,
                    'is_admin': admin_user.is_admin
                }
            })
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
    except Exception as e:
        logger.error(f"Error creating first admin: {e}")
        return jsonify({'error': 'Failed to create admin user'}), 500

@setup_bp.route('/skip', methods=['POST'])
def skip_setup():
    """Skip the initial setup process (for development/testing)."""
    try:
        # This endpoint can be used to bypass setup in development
        # In production, you might want to disable this or add additional security
        
        return jsonify({
            'success': True,
            'message': 'Setup skipped'
        })
        
    except Exception as e:
        logger.error(f"Error skipping setup: {e}")
        return jsonify({'error': 'Failed to skip setup'}), 500
