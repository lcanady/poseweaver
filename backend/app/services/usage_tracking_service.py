"""
Usage tracking service for pose generation limits and paywall enforcement.
"""
from typing import Dict, Any, Optional
from flask import request, jsonify
from functools import wraps
from ..models.user_mongo import User


class UsageTrackingService:
    """Service for tracking and enforcing usage limits."""
    
    @staticmethod
    def get_user_from_request() -> Optional[User]:
        """Extract user from request. This should be updated based on your auth system."""
        # TODO: Replace this with your actual authentication system
        # For now, we'll look for a user_id in headers or request data
        
        user_id = None
        
        # Try to get user_id from Authorization header (if using JWT)
        auth_header = request.headers.get('Authorization')
        if auth_header:
            # This is a placeholder - implement based on your JWT/auth system
            # user_id = extract_user_id_from_jwt(auth_header)
            pass
        
        # Try to get user_id from request data as fallback
        if not user_id:
            data = request.get_json(silent=True) or {}
            user_id = data.get('user_id')
        
        # Try to get from query params
        if not user_id:
            user_id = request.args.get('user_id')
        
        print(f"[DEBUG] Extracted user_id from request: '{user_id}'")
        print(f"[DEBUG] Request data: {data}")
        print(f"[DEBUG] Request args: {dict(request.args)}")
        
        if user_id:
            try:
                return User.find_by_id(user_id)
            except Exception as e:
                # Handle invalid ObjectId or other errors
                print(f"Error finding user by ID '{user_id}': {e}")
                return None
        
        return None
    
    @staticmethod
    def check_pose_generation_limit(user) -> Dict[str, Any]:
        """Check if user can generate a pose and return status info."""
        if not user:
            return {
                'can_generate': False,
                'error': 'User not found',
                'error_code': 'USER_NOT_FOUND'
            }
        
        # Handle demo user (SimpleNamespace object)
        if hasattr(user, '__dict__') and not hasattr(user, 'get_effective_subscription_status'):
            # This is likely a demo user, return demo data
            return {
                'can_generate': True,
                'available_generations': 15,
                'monthly_limit': 20,
                'current_usage': 5,
                'extra_generations': 0,
                'subscription_status': 'free'
            }
        
        # Check if user can generate pose
        if not user.can_generate_pose():
            effective_status = user.get_effective_subscription_status()
            limit = user.get_pose_generation_limit()
            used = user.pose_generations_used
            extra = user.extra_pose_generations
            
            if effective_status in ['free', 'expired']:
                return {
                    'can_generate': False,
                    'error': f'Monthly limit of {limit} pose generations reached. Upgrade to premium for {user.get_pose_generation_limit() if effective_status == "premium" else 500} generations per month.',
                    'error_code': 'LIMIT_REACHED_UPGRADE_NEEDED',
                    'current_usage': used,
                    'monthly_limit': limit,
                    'extra_generations': extra,
                    'subscription_status': effective_status,
                    'can_upgrade': True,
                    'can_purchase_extra': False
                }
            elif effective_status == 'premium':
                return {
                    'can_generate': False,
                    'error': f'Monthly limit of {limit + extra} pose generations reached. Purchase additional generations to continue.',
                    'error_code': 'LIMIT_REACHED_PURCHASE_AVAILABLE',
                    'current_usage': used,
                    'monthly_limit': limit,
                    'extra_generations': extra,
                    'subscription_status': effective_status,
                    'can_upgrade': False,
                    'can_purchase_extra': True
                }
        
        # User can generate pose
        available = user.get_available_pose_generations()
        limit = user.get_pose_generation_limit()
        
        return {
            'can_generate': True,
            'available_generations': available,
            'monthly_limit': limit,
            'current_usage': user.pose_generations_used,
            'extra_generations': user.extra_pose_generations,
            'subscription_status': user.get_effective_subscription_status()
        }
    
    @staticmethod
    def use_generation(user) -> bool:
        """Use one pose generation for the user."""
        # Handle demo user
        if hasattr(user, '__dict__') and not hasattr(user, 'use_pose_generation'):
            # Demo user always allows generation
            print("Demo user used one generation (simulated)")
            return True
        
        return user.use_pose_generation()
    
    @staticmethod
    def _check_and_send_usage_alerts(user):
        """Check if user should receive usage alerts and send them."""
        try:
            # Import here to avoid circular imports
            from app.services.notification_service import NotificationService
            
            # Skip alerts for demo users
            if hasattr(user, '__dict__') and not hasattr(user, 'get_effective_subscription_status'):
                return
            
            # Get current usage info
            current_usage = user.pose_generations_used
            limit = user.get_pose_generation_limit()
            
            if limit > 0:
                percentage = int((current_usage / limit) * 100)
                
                # Send alerts at 80%, 90%, and 100% thresholds
                if percentage in [80, 90, 100]:
                    NotificationService.create_pose_generation_alert(
                        user.id, current_usage, limit
                    )
                    
        except Exception as e:
            print(f"Error checking usage alerts: {e}")


def require_pose_generation_limit(f):
    """Decorator to enforce pose generation limits on API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user from request
        user = UsageTrackingService.get_user_from_request()
        
        if not user:
            # For testing purposes, create a demo user object
            from types import SimpleNamespace
            user = SimpleNamespace(
                id='demo-user',
                subscription_status='free',
                pose_generations_used=5,
                pose_generations_reset_date=None,
                extra_pose_generations=0,
                can_generate_pose=lambda: True,  # Allow generation for demo
                use_pose_generation=lambda: True,
                get_effective_subscription_status=lambda: 'free',
                get_pose_generation_limit=lambda: 20,
                get_available_pose_generations=lambda: 15
            )
            print("Using demo user for testing purposes")
        
        # Check usage limits
        usage_status = UsageTrackingService.check_pose_generation_limit(user)
        
        if not usage_status['can_generate']:
            return jsonify({
                'success': False,
                'error': usage_status['error'],
                'error_code': usage_status['error_code'],
                'usage_info': {
                    'current_usage': usage_status.get('current_usage', 0),
                    'monthly_limit': usage_status.get('monthly_limit', 0),
                    'extra_generations': usage_status.get('extra_generations', 0),
                    'subscription_status': usage_status.get('subscription_status', 'free'),
                    'can_upgrade': usage_status.get('can_upgrade', False),
                    'can_purchase_extra': usage_status.get('can_purchase_extra', False)
                }
            }), 402  # Payment Required
        
        # Use one generation
        if not UsageTrackingService.use_generation(user):
            return jsonify({
                'success': False,
                'error': 'Failed to process generation usage',
                'error_code': 'USAGE_PROCESSING_ERROR'
            }), 500
        
        # Check if we should send usage alerts after using generation
        UsageTrackingService._check_and_send_usage_alerts(user)
        
        # Add user and usage info to request context for the endpoint
        request.current_user = user
        request.usage_info = usage_status
        
        # Call the original function
        return f(*args, **kwargs)
    
    return decorated_function


def get_usage_info(f):
    """Decorator to add usage info to API responses without enforcing limits."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user from request
        user = UsageTrackingService.get_user_from_request()
        
        # Call the original function
        response = f(*args, **kwargs)
        
        # Add usage info to response if user exists and response is successful
        if user and hasattr(response, 'get_json'):
            response_data = response.get_json()
            if response_data and response_data.get('success'):
                usage_status = UsageTrackingService.check_pose_generation_limit(user)
                response_data['usage_info'] = {
                    'available_generations': usage_status.get('available_generations', 0),
                    'monthly_limit': usage_status.get('monthly_limit', 0),
                    'current_usage': usage_status.get('current_usage', 0),
                    'extra_generations': usage_status.get('extra_generations', 0),
                    'subscription_status': usage_status.get('subscription_status', 'free')
                }
                response.data = jsonify(response_data).data
        
        return response
    
    return decorated_function
