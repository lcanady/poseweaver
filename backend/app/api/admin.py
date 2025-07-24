"""
Admin API endpoints for user management and analytics.
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, Any, List
from bson import ObjectId
from ..models.user_mongo import User
from ..models.character import Character
from app.services.mongodb_service import get_mongodb_service
from app.services.logging_service import get_logging_service, log_info, log_warning, log_error
from app.services.admin_init import ensure_admin_initialized
from ..middleware.auth_middleware import require_auth
from ..services.auth_service import AuthService
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

def safe_date_format(date_value):
    """Safely format date values that could be datetime objects or strings"""
    if not date_value:
        return None
    if isinstance(date_value, str):
        return date_value
    if hasattr(date_value, 'isoformat'):
        return date_value.isoformat()
    return str(date_value)

def require_admin_auth(f):
    """Decorator to require admin authentication using JWT."""
    @require_auth
    def decorated_function(*args, **kwargs):
        # Ensure admin system is initialized on first access
        ensure_admin_initialized()
        
        # Get current user from JWT
        current_user = AuthService.get_current_user()
        if not current_user or not current_user.is_admin:
            log_warning('Admin', f'Unauthorized admin access attempt from user: {current_user.email if current_user else "unknown"}')
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/users', methods=['GET'])
@require_admin_auth
def get_users():
    """Get paginated list of users with search and filtering"""
    try:
        log_info('Admin', 'User list requested by admin')
        
        db_service = get_mongodb_service()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        subscription_filter = request.args.get('subscription', 'all')
        status_filter = request.args.get('status', 'all')
        
        # Build filter query
        filter_dict = {}
        
        # Search filter
        if search:
            filter_dict['$or'] = [
                {'email': {'$regex': search, '$options': 'i'}},
                {'display_name': {'$regex': search, '$options': 'i'}}
            ]
        
        # Subscription filter
        if subscription_filter != 'all':
            filter_dict['subscription_status'] = subscription_filter
            
        # Status filter
        if status_filter == 'active':
            filter_dict['is_active'] = True
        elif status_filter == 'inactive':
            filter_dict['is_active'] = False
        
        # Get users with pagination
        skip = (page - 1) * per_page
        users_data = db_service.find_many('users', filter_dict, skip=skip, limit=per_page)
        
        # Get total count for pagination
        total_users = db_service.count_documents('users', filter_dict)
        
        # Format users data
        users = []
        for user_data in users_data:
            user = {
                'id': str(user_data['_id']),
                'email': user_data.get('email', ''),
                'display_name': user_data.get('display_name', ''),
                'is_admin': user_data.get('is_admin', False),
                'is_active': user_data.get('is_active', True),
                'subscription_status': user_data.get('subscription_status', 'free'),
                'pose_generations_used': user_data.get('pose_generations_used', 0),
                'pose_generation_limit': user_data.get('pose_generation_limit', 20),
                'extra_pose_generations': user_data.get('extra_pose_generations', 0),
                'created_at': safe_date_format(user_data.get('created_at')),
                'updated_at': safe_date_format(user_data.get('updated_at')),
                'last_login': safe_date_format(user_data.get('last_login'))
            }
            users.append(user)
        
        log_info('Admin', f'Retrieved {len(users)} users (page {page}, total: {total_users})')
        
        return jsonify({
            'success': True,
            'users': users,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_users,
                'pages': (total_users + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        log_error('Admin', f'Error getting users: {str(e)}')
        return jsonify({'error': 'Failed to fetch users'}), 500

@admin_bp.route('/users/<user_id>', methods=['GET'])
@require_admin_auth
def get_user_details(user_id):
    """Get detailed information about a specific user."""
    try:
        # Get user data directly from MongoDB
        db_service = get_mongodb_service()
        user_data = db_service.find_one('users', {'_id': ObjectId(user_id)})
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's characters
        characters_data = db_service.find_many('characters', {'user_id': user_id})
        
        characters = []
        for char_data in characters_data:
            characters.append({
                'id': char_data['_id'],
                'name': char_data.get('name', ''),
                'created_at': char_data.get('created_at', '')
            })
        
        # Build user details response
        user_details = {
            'id': user_data['_id'],
            'email': user_data.get('email', ''),
            'display_name': user_data.get('display_name', ''),
            'bio': user_data.get('bio', ''),
            'avatar_url': user_data.get('avatar_url', ''),
            'is_active': user_data.get('is_active', True),
            'is_admin': user_data.get('is_admin', False),
            'created_at': safe_date_format(user_data.get('created_at')),
            'updated_at': safe_date_format(user_data.get('updated_at')),
            'subscription_status': user_data.get('subscription_status', 'free'),
            'subscription_tier': user_data.get('subscription_tier', 'free'),
            'subscription_expires_at': safe_date_format(user_data.get('subscription_expires_at')),
            'poses_generated': user_data.get('poses_generated', 0),
            'pose_generation_limit': user_data.get('pose_generation_limit', 10),
            'extra_poses': user_data.get('extra_poses', 0),
            'pose_generations_reset_date': safe_date_format(user_data.get('pose_generations_reset_date')),
            'stripe_customer_id': user_data.get('stripe_customer_id', ''),
            'characters': characters,
            'character_count': len(characters),
            'character_limit': user_data.get('character_limit', 5)
        }
        
        return jsonify({
            'success': True,
            'user': user_details
        })
        
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        return jsonify({'error': 'Failed to fetch user details'}), 500

@admin_bp.route('/users/<user_id>/update', methods=['POST'])
@require_admin_auth
def update_user(user_id):
    """Update user information and settings."""
    try:
        # Get user data directly from MongoDB
        db_service = get_mongodb_service()
        user_data = db_service.find_one('users', {'_id': ObjectId(user_id)})
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        update_fields = {}
        
        # Update allowed fields
        if 'is_active' in data:
            update_fields['is_active'] = bool(data['is_active'])
        
        if 'is_admin' in data:
            update_fields['is_admin'] = bool(data['is_admin'])
        
        if 'subscription_status' in data:
            valid_statuses = ['free', 'basic', 'pro', 'premium', 'expired']
            if data['subscription_status'] in valid_statuses:
                update_fields['subscription_status'] = data['subscription_status']
        
        if 'subscription_tier' in data:
            valid_tiers = ['free', 'basic', 'pro', 'premium']
            if data['subscription_tier'] in valid_tiers:
                update_fields['subscription_tier'] = data['subscription_tier']
        
        if 'extra_pose_generations' in data:
            update_fields['extra_poses'] = max(0, int(data['extra_pose_generations']))
        
        if 'extra_poses' in data:
            update_fields['extra_poses'] = max(0, int(data['extra_poses']))
        
        if 'display_name' in data:
            update_fields['display_name'] = data['display_name']
        
        if 'bio' in data:
            update_fields['bio'] = data['bio']
        
        # Reset usage if requested
        if data.get('reset_usage', False):
            update_fields['poses_generated'] = 0
            update_fields['pose_generations_reset_date'] = datetime.now().isoformat()
        
        # Always update the updated_at timestamp
        update_fields['updated_at'] = datetime.now().isoformat()
        
        # Update the user in MongoDB
        success = db_service.update_one('users', {'_id': ObjectId(user_id)}, update_fields)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'User updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update user'}), 500
        
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({'error': 'Failed to update user'}), 500

@admin_bp.route('/analytics/overview', methods=['GET'])
@require_admin_auth
def get_analytics_overview():
    """Get high-level analytics overview."""
    try:
        db_service = get_mongodb_service()
        
        # Get total user count
        total_users = db_service.count_documents('users')
        
        # Get active users count
        active_users = db_service.count_documents('users', {'is_active': True})
        
        # Get admin users count
        admin_users = db_service.count_documents('users', {'is_admin': True})
        
        # Get subscription status counts
        free_users = db_service.count_documents('users', {'subscription_status': 'free'})
        basic_users = db_service.count_documents('users', {'subscription_status': 'basic'})
        pro_users = db_service.count_documents('users', {'subscription_status': 'pro'})
        premium_users = db_service.count_documents('users', {'subscription_status': 'premium'})
        
        # Get users created in the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users_30d = db_service.count_documents('users', {
            'created_at': {'$gte': thirty_days_ago}
        })
        
        # Get users created in the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        new_users_7d = db_service.count_documents('users', {
            'created_at': {'$gte': seven_days_ago}
        })
        
        # Get total characters count
        total_characters = db_service.count_documents('characters')
        
        # Calculate usage statistics
        all_users = db_service.find_many('users', filter_dict={}, limit=0)  # Get all users
        total_pose_generations = sum(user.get('pose_generations_used', 0) for user in all_users)
        total_extra_generations = sum(user.get('extra_pose_generations', 0) for user in all_users)
        
        # Calculate conversion rate (users with paid subscriptions)
        paid_users = basic_users + pro_users + premium_users
        conversion_rate = (paid_users / total_users * 100) if total_users > 0 else 0
        
        analytics = {
            'users': {
                'total': total_users,
                'active': active_users,
                'recent_signups': new_users_30d
            },
            'subscriptions': {
                'free': free_users,
                'basic': basic_users,
                'pro': pro_users,
                'premium': premium_users
            },
            'content': {
                'total_characters': total_characters
            },
            'usage': {
                'total_pose_generations': total_pose_generations,
                'total_extra_generations': total_extra_generations
            },
            'conversion_rate': round(conversion_rate, 2),
            'admin_users': admin_users,
            'new_users_7d': new_users_7d
        }
        
        return jsonify({'analytics': analytics})
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {str(e)}")
        return jsonify({'error': 'Failed to fetch analytics'}), 500

@admin_bp.route('/analytics/growth', methods=['GET'])
@require_admin_auth
def get_growth_analytics():
    """Get user growth analytics over time."""
    try:
        mongodb_service = get_mongodb_service()
        
        # Get growth data for the last 12 months
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        # Aggregate users by month
        pipeline = [
            {'$match': {'created_at': {'$gte': twelve_months_ago}}},
            {'$group': {
                '_id': {
                    'year': {'$year': '$created_at'},
                    'month': {'$month': '$created_at'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id.year': 1, '_id.month': 1}}
        ]
        
        growth_data = list(mongodb_service.aggregate(User.COLLECTION_NAME, pipeline))
        
        # Format data for frontend
        monthly_growth = []
        for item in growth_data:
            month_str = f"{item['_id']['year']}-{item['_id']['month']:02d}"
            monthly_growth.append({
                'month': month_str,
                'users': item['count']
            })
        
        # Get subscription conversion data
        conversion_pipeline = [
            {'$group': {
                '_id': '$subscription_status',
                'count': {'$sum': 1}
            }}
        ]
        
        subscription_data = list(mongodb_service.aggregate(User.COLLECTION_NAME, conversion_pipeline))
        
        return jsonify({
            'success': True,
            'growth': {
                'monthly_signups': monthly_growth,
                'subscription_distribution': subscription_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting growth analytics: {e}")
        return jsonify({'error': 'Failed to fetch growth analytics'}), 500

@admin_bp.route('/users/<user_id>/delete', methods=['DELETE'])
@require_admin_auth
def delete_user(user_id):
    """Delete a user and all associated data."""
    try:
        # Get user data directly from MongoDB
        db_service = get_mongodb_service()
        user_data = db_service.find_one('users', {'_id': ObjectId(user_id)})
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Delete user's characters first
        characters_deleted = db_service.find_many('characters', {'user_id': user_id})
        for character in characters_deleted:
            db_service.delete_one('characters', {'_id': ObjectId(character['_id'])})
        
        # Delete the user
        success = db_service.delete_one('users', {'_id': ObjectId(user_id)})
        
        if success:
            return jsonify({
                'success': True,
                'message': 'User and associated data deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete user'}), 500
        
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return jsonify({'error': 'Failed to delete user'}), 500

@admin_bp.route('/system/stats', methods=['GET'])
@require_admin_auth
def get_system_stats():
    """Get system-wide statistics and health metrics."""
    try:
        db_service = get_mongodb_service()
        
        # Database collection statistics
        collections_stats = {
            'users': db_service.count_documents('users'),
            'characters': db_service.count_documents('characters'),
        }
        
        # Recent activity (last 24 hours)
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        recent_activity = {
            'users_created_24h': db_service.count_documents('users', {
                'created_at': {'$gte': twenty_four_hours_ago}
            }),
            'users_active_1h': db_service.count_documents('users', {
                'updated_at': {'$gte': one_hour_ago}
            }),
            'characters_created_24h': db_service.count_documents('characters', {
                'created_at': {'$gte': twenty_four_hours_ago}
            })
        }
        
        # System health indicators
        try:
            # Test database connection with timeout
            import time
            start_time = time.time()
            
            # Try to ping the database first
            db_service._client.admin.command('ping')
            
            # Then test a simple query
            db_service.count_documents('users', {})
            
            end_time = time.time()
            response_time_ms = round((end_time - start_time) * 1000, 2)
            
            db_healthy = True
            db_response_time = f"{response_time_ms}ms"
            
            log_info('Admin', f'Database health check passed: {db_response_time}')
            
        except Exception as e:
            db_healthy = False
            db_response_time = "Connection Failed"
            log_error('Admin', f'Database health check failed: {str(e)}')
        
        # Memory and performance metrics (basic)
        import psutil
        import os
        
        system_metrics = {
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent(interval=1),
            'disk_usage': psutil.disk_usage('/').percent,
            'process_id': os.getpid(),
            'uptime': datetime.now().isoformat()  # App start time placeholder
        }
        
        return jsonify({
            'success': True,
            'health': {
                'database_connected': db_healthy,
                'database_response_time': db_response_time,
                'memory_usage_percent': system_metrics['memory_usage'],
                'cpu_usage_percent': system_metrics['cpu_usage'],
                'disk_usage_percent': system_metrics['disk_usage']
            },
            'database': {
                'collections': collections_stats
            },
            'activity': recent_activity,
            'metrics': system_metrics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch system statistics'}), 500

@admin_bp.route('/system/maintenance/cleanup', methods=['POST'])
@require_admin_auth
def system_cleanup():
    """Perform system cleanup - remove inactive users and orphaned data"""
    try:
        log_info('Admin', 'System cleanup initiated by admin')

        db_service = get_mongodb_service()

        # Find inactive users (no activity for 365+ days)
        cutoff_date = datetime.now() - timedelta(days=365)
        inactive_filter = {
            '$or': [
                {'last_login': {'$lt': cutoff_date}},
                {'last_login': {'$exists': False}, 'created_at': {'$lt': cutoff_date}}
            ]
        }

        inactive_users = db_service.find_many('users', inactive_filter)
        inactive_count = len(inactive_users)

        # Find orphaned characters (characters without valid user_id)
        all_user_ids = [str(user['_id']) for user in db_service.find_many('users', {})]
        orphaned_characters = []
        all_characters = db_service.find_many('characters', {})

        for char in all_characters:
            if char.get('user_id') not in all_user_ids:
                orphaned_characters.append(char)

        orphaned_count = len(orphaned_characters)

        # For now, just report what would be cleaned up (don't actually delete)
        cleanup_summary = {
            'inactive_users': inactive_count,
            'orphaned_characters': orphaned_count,
            'total_users': db_service.count_documents('users'),
            'total_characters': db_service.count_documents('characters')
        }

        if inactive_count > 0:
            log_warning('Admin', f'Found {inactive_count} inactive users for potential cleanup')
        if orphaned_count > 0:
            log_warning('Admin', f'Found {orphaned_count} orphaned characters for potential cleanup')

        log_info('Admin', f'System cleanup analysis completed: {cleanup_summary}')

        return jsonify({
            'success': True,
            'message': f'Cleanup analysis completed. Found {inactive_count} inactive users and {orphaned_count} orphaned characters.',
            'details': cleanup_summary
        })

    except Exception as e:
        log_error('Admin', f'Error during system cleanup: {str(e)}')
        return jsonify({'error': 'Failed to perform system cleanup'}), 500

@admin_bp.route('/system/maintenance/reset-usage', methods=['POST'])
@require_admin_auth
def reset_all_usage():
    """Reset usage statistics for all users"""
    try:
        log_info('Admin', 'Usage reset initiated by admin')

        db_service = get_mongodb_service()

        # Reset poses_generated for all users
        update_result = db_service.update_many(
            'users',
            {},  # Empty filter to match all users
            {
                '$set': {
                    'poses_generated': 0,
                    'updated_at': datetime.now()
                }
            }
        )

        affected_users = update_result.modified_count if hasattr(update_result, 'modified_count') else 0

        log_info('Admin', f'Usage statistics reset for {affected_users} users')

        return jsonify({
            'success': True,
            'message': f'Usage statistics reset for {affected_users} users'
        })

    except Exception as e:
        log_error('Admin', f'Error resetting usage statistics: {str(e)}')
        return jsonify({'error': 'Failed to reset usage statistics'}), 500

@admin_bp.route('/system/logs', methods=['GET'])
@require_admin_auth
def get_system_logs():
    """Get recent system logs"""
    try:
        logging_service = get_logging_service()
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        level_filter = request.args.get('level')
        component_filter = request.args.get('component')
        hours = request.args.get('hours', 24, type=int)
        
        # Get logs based on timeframe or recent logs
        if hours:
            logs = logging_service.get_logs_by_timeframe(hours=hours)
        else:
            logs = logging_service.get_recent_logs(
                limit=limit,
                level_filter=level_filter,
                component_filter=component_filter
            )
        
        # Format timestamps for frontend
        for log in logs:
            try:
                # Convert ISO format to more readable format
                dt = datetime.fromisoformat(log['timestamp'])
                log['timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, KeyError):
                pass
        
        log_info('Admin', f'System logs retrieved: {len(logs)} entries')
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': len(logs)
        })
        
    except Exception as e:
        log_error('Admin', f'Error getting system logs: {str(e)}')
        return jsonify({'error': 'Failed to fetch system logs'}), 500
