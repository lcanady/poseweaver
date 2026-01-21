"""
Notification API endpoints for in-app notifications.
"""
from flask import Blueprint, request, jsonify
from app.middleware.auth_middleware import require_auth, get_current_identity
from app.services.notification_service import NotificationService

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications', methods=['GET'])
@require_auth
def get_notifications():
    """Get notifications for the current user."""
    try:
        current_user = request.current_user
        
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 notifications
        skip = int(request.args.get('skip', 0))
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Get notifications
        notifications = NotificationService.get_user_notifications(
            current_user.id, limit, skip, unread_only
        )
        
        # Get unread count
        unread_count = NotificationService.get_unread_count(current_user.id)
        
        # Convert notifications to dict format
        notifications_data = []
        for notification in notifications:
            notification_dict = notification.to_dict()
            # Convert ObjectId to string and format datetime
            notification_dict['id'] = notification_dict.pop('_id')
            notification_dict['created_at'] = notification.created_at.isoformat()
            notifications_data.append(notification_dict)
        
        return jsonify({
            'success': True,
            'notifications': notifications_data,
            'unread_count': unread_count,
            'has_more': len(notifications) == limit  # Indicates if there are more notifications
        })
        
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get notifications'
        }), 500

@notifications_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@require_auth
def mark_notification_read(notification_id):
    """Mark a specific notification as read."""
    try:
        current_user = request.current_user
        
        success = NotificationService.mark_notification_read(notification_id, current_user.id)
        
        if success:
            # Get updated unread count
            unread_count = NotificationService.get_unread_count(current_user.id)
            
            return jsonify({
                'success': True,
                'message': 'Notification marked as read',
                'unread_count': unread_count
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Notification not found or access denied'
            }), 404
            
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to mark notification as read'
        }), 500

@notifications_bp.route('/notifications/read-all', methods=['POST'])
@require_auth
def mark_all_notifications_read():
    """Mark all notifications as read for the current user."""
    try:
        current_user = request.current_user
        
        success = NotificationService.mark_all_read(current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'All notifications marked as read',
                'unread_count': 0
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to mark all notifications as read'
            }), 500
            
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to mark all notifications as read'
        }), 500

@notifications_bp.route('/notifications/<notification_id>', methods=['DELETE'])
@require_auth
def delete_notification(notification_id):
    """Delete a specific notification."""
    try:
        current_user = request.current_user
        
        success = NotificationService.delete_notification(notification_id, current_user.id)
        
        if success:
            # Get updated unread count
            unread_count = NotificationService.get_unread_count(current_user.id)
            
            return jsonify({
                'success': True,
                'message': 'Notification deleted',
                'unread_count': unread_count
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Notification not found or access denied'
            }), 404
            
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete notification'
        }), 500

@notifications_bp.route('/notifications/clear-all', methods=['DELETE'])
@require_auth
def clear_all_notifications():
    """Clear all notifications for the current user."""
    try:
        current_user = request.current_user
        
        success = NotificationService.clear_all_notifications(current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'All notifications cleared',
                'unread_count': 0
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to clear notifications'
            }), 500
            
    except Exception as e:
        print(f"Error clearing all notifications: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear notifications'
        }), 500

@notifications_bp.route('/notifications/unread-count', methods=['GET'])
@require_auth
def get_unread_count():
    """Get the count of unread notifications for the current user."""
    try:
        current_user = request.current_user
        
        unread_count = NotificationService.get_unread_count(current_user.id)
        
        return jsonify({
            'success': True,
            'unread_count': unread_count
        })
        
    except Exception as e:
        print(f"Error getting unread count: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get unread count'
        }), 500

# Admin endpoints for creating notifications
@notifications_bp.route('/notifications/broadcast', methods=['POST'])
@require_auth
def broadcast_notification():
    """Broadcast a feature announcement to all users (admin only)."""
    try:
        current_user = request.current_user
        
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body required'
            }), 400
        
        feature_name = data.get('feature_name')
        description = data.get('description')
        target_tiers = data.get('target_subscription_tiers')  # Optional
        
        if not feature_name or not description:
            return jsonify({
                'success': False,
                'error': 'feature_name and description are required'
            }), 400
        
        count = NotificationService.broadcast_feature_announcement(
            feature_name, description, target_tiers
        )
        
        return jsonify({
            'success': True,
            'message': f'Feature announcement sent to {count} users',
            'users_notified': count
        })
        
    except Exception as e:
        print(f"Error broadcasting notification: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to broadcast notification'
        }), 500

@notifications_bp.route('/notifications/test', methods=['POST'])
@require_auth
def create_test_notification():
    """Create a test notification (admin only, for development)."""
    try:
        current_user = request.current_user
        
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body required'
            }), 400
        
        notification_type = data.get('type', 'system_notification')
        title = data.get('title', 'Test Notification')
        message = data.get('message', 'This is a test notification.')
        notification_data = data.get('data', {})
        
        notification = NotificationService.create_notification(
            current_user.id, notification_type, title, message, notification_data
        )
        
        if notification:
            return jsonify({
                'success': True,
                'message': 'Test notification created',
                'notification_id': notification.id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create test notification'
            }), 500
            
    except Exception as e:
        print(f"Error creating test notification: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create test notification'
        }), 500
