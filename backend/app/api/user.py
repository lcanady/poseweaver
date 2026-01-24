"""
User API endpoints for settings and data management.
"""
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import json
import tempfile
import os
from ..middleware.auth_middleware import require_auth
from ..models.user_mongo import User
from ..services.mongodb_service import get_mongodb_service

user_bp = Blueprint('user', __name__)

@user_bp.route('/settings', methods=['GET'])
@require_auth
def get_user_settings():
    """Get user settings."""
    try:
        print(f"[DEBUG] get_user_settings called")
        current_user = request.current_user
        print(f"[DEBUG] current_user: {current_user}")
        
        if not current_user:
            print(f"[DEBUG] No current user found")
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        print(f"[DEBUG] About to call get_settings()")
        settings = current_user.get_settings()
        print(f"[DEBUG] Settings retrieved: {settings}")
        
        return jsonify({
            'success': True,
            'settings': settings
        })
        
    except Exception as e:
        print(f"[DEBUG] Exception in get_user_settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_bp.route('/settings', methods=['POST'])
@require_auth
def update_user_settings():
    """Update user settings."""
    try:
        print(f"[DEBUG] update_user_settings called")
        current_user = request.current_user
        print(f"[DEBUG] current_user: {current_user}")
        
        if not current_user:
            print(f"[DEBUG] No current user found")
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        data = request.get_json()
        print(f"[DEBUG] Request data: {data}")
        if not data:
            return jsonify({
                'success': False,
                'error': 'No settings data provided'
            }), 400
        
        # Validate settings structure
        valid_keys = ['theme', 'notifications', 'privacy', 'preferences']
        settings_to_update = {}
        
        for key, value in data.items():
            if key in valid_keys:
                settings_to_update[key] = value
        
        print(f"[DEBUG] Settings to update: {settings_to_update}")
        if not settings_to_update:
            return jsonify({
                'success': False,
                'error': 'No valid settings provided'
            }), 400
        
        # Update user settings
        print(f"[DEBUG] About to call update_settings")
        current_user.update_settings(settings_to_update)
        print(f"[DEBUG] Settings updated successfully")
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': current_user.get_settings()
        })
        
    except Exception as e:
        print(f"[DEBUG] Exception in update_user_settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_bp.route('/export-data', methods=['GET'])
@require_auth
def export_user_data():
    """Export all user data."""
    try:
        current_user = request.current_user
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        mongodb_service = get_mongodb_service()
        
        # Gather all user data
        user_data = {
            'user_profile': {
                'email': current_user.email,
                'display_name': current_user.display_name,
                'bio': current_user.bio,
                'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
                'subscription_status': current_user.subscription_status,
                'settings': current_user.settings
            },
            'characters': [],
            'pose_history': [],
            'usage_stats': {
                'pose_generations_used': current_user.pose_generations_used,
                'extra_pose_generations': current_user.extra_pose_generations,
                'credits': current_user.credits,
                'subscription_status': current_user.subscription_status
            }
        }
        
        # Get user's characters
        try:
            characters = mongodb_service.find_many(
                'characters',
                {'user_id': current_user.id},
                sort=[('created_at', -1)]
            )
            
            for char in characters:
                # Remove sensitive data and convert ObjectId to string
                char_data = {
                    'name': char.get('name'),
                    'background': char.get('background'),
                    'personality': char.get('personality'),
                    'created_at': char.get('created_at').isoformat() if char.get('created_at') else None,
                    'updated_at': char.get('updated_at').isoformat() if char.get('updated_at') else None
                }
                user_data['characters'].append(char_data)
        except Exception as e:
            print(f"Error fetching characters: {e}")
        
        # Get user's pose history (if exists)
        try:
            pose_history = mongodb_service.find_many(
                'pose_history',
                {'user_id': current_user.id},
                sort=[('created_at', -1)],
                limit=100  # Limit to last 100 poses
            )
            
            for pose in pose_history:
                pose_data = {
                    'original_pose': pose.get('original_pose'),
                    'enhanced_pose': pose.get('enhanced_pose'),
                    'enhancement_style': pose.get('enhancement_style'),
                    'created_at': pose.get('created_at').isoformat() if pose.get('created_at') else None
                }
                user_data['pose_history'].append(pose_data)
        except Exception as e:
            print(f"Error fetching pose history: {e}")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(user_data, temp_file, indent=2, default=str)
            temp_filename = temp_file.name
        
        # Send file and clean up
        def remove_file(response):
            try:
                os.unlink(temp_filename)
            except Exception:
                pass
            return response
        
        return send_file(
            temp_filename,
            as_attachment=True,
            download_name=f'poseweaver-data-{datetime.now().strftime("%Y-%m-%d")}.json',
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_bp.route('/delete-account', methods=['POST'])
@require_auth
def delete_user_account():
    """Delete user account and all associated data."""
    try:
        current_user = request.current_user
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        data = request.get_json()
        confirmation = data.get('confirmation') if data else None
        
        # Require explicit confirmation
        if confirmation != 'DELETE_MY_ACCOUNT':
            return jsonify({
                'success': False,
                'error': 'Account deletion requires explicit confirmation'
            }), 400
        
        mongodb_service = get_mongodb_service()
        user_id = current_user.id
        
        # Delete associated data
        try:
            # Delete user's characters
            mongodb_service.delete_many('characters', {'user_id': user_id})
            
            # Delete user's pose history
            mongodb_service.delete_many('pose_history', {'user_id': user_id})
            
            # Delete user's scenes (if any)
            mongodb_service.delete_many('scenes', {'user_id': user_id})
            
            # Finally delete the user account
            current_user.delete()
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to delete account data: {str(e)}'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Account and all associated data have been permanently deleted'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_bp.route('/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """Get user profile information."""
    try:
        current_user = request.current_user
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        profile_data = {
            'id': current_user.id,
            'email': current_user.email,
            'display_name': current_user.display_name,
            'bio': current_user.bio,
            'avatar_url': current_user.avatar_url,
            'subscription_status': current_user.get_effective_subscription_status(),
            'credits': current_user.credits,
            'is_admin': current_user.is_admin,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'settings': current_user.get_settings()
        }
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
