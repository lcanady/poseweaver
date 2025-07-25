"""
Notification service for managing in-app notifications.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.notification import Notification
from app.models.user_mongo import User

class NotificationService:
    """Service for managing notifications."""
    
    @staticmethod
    def create_notification(user_id: str, notification_type: str, title: str, 
                          message: str, data: Optional[Dict[str, Any]] = None) -> Optional[Notification]:
        """Create and save a new notification."""
        try:
            # Check if user has notifications enabled for this type
            user = User.find_by_id(user_id)
            if not user:
                print(f"User not found: {user_id}")
                return None
            
            # Check user notification preferences
            if not NotificationService._should_send_notification(user, notification_type):
                print(f"Notification disabled for user {user_id}, type: {notification_type}")
                return None
            
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data
            )
            
            if notification.save():
                print(f"Created notification for user {user_id}: {title}")
                return notification
            else:
                print(f"Failed to save notification for user {user_id}")
                return None
                
        except Exception as e:
            print(f"Error creating notification: {e}")
            return None
    
    @staticmethod
    def _should_send_notification(user: User, notification_type: str) -> bool:
        """Check if user has enabled notifications for this type."""
        try:
            settings = user.get_settings()
            notifications_settings = settings.get('notifications', {})
            
            # Map notification types to user settings
            type_mapping = {
                Notification.POSE_GENERATION_ALERT: 'pose_generation_alerts',
                Notification.SUBSCRIPTION_REMINDER: 'subscription_reminders',
                Notification.FEATURE_ANNOUNCEMENT: 'feature_announcements',
                Notification.SYSTEM_NOTIFICATION: True  # Always send system notifications
            }
            
            setting_key = type_mapping.get(notification_type)
            if setting_key is True:
                return True
            elif setting_key:
                return notifications_settings.get(setting_key, True)
            else:
                return True  # Default to enabled for unknown types
                
        except Exception as e:
            print(f"Error checking notification preferences: {e}")
            return True  # Default to enabled on error
    
    @staticmethod
    def get_user_notifications(user_id: str, limit: int = 50, skip: int = 0, 
                             unread_only: bool = False) -> List[Notification]:
        """Get notifications for a user."""
        return Notification.find_by_user(user_id, limit, skip, unread_only)
    
    @staticmethod
    def get_unread_count(user_id: str) -> int:
        """Get count of unread notifications for a user."""
        return Notification.count_unread_by_user(user_id)
    
    @staticmethod
    def mark_notification_read(notification_id: str, user_id: str) -> bool:
        """Mark a specific notification as read."""
        try:
            # Find the notification and verify it belongs to the user
            notifications = Notification.find_by_user(user_id, limit=1000)  # Get all to find by ID
            notification = next((n for n in notifications if n.id == notification_id), None)
            
            if not notification:
                print(f"Notification not found or doesn't belong to user: {notification_id}")
                return False
            
            return notification.mark_as_read()
            
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
    
    @staticmethod
    def mark_all_read(user_id: str) -> bool:
        """Mark all notifications as read for a user."""
        return Notification.mark_all_read_by_user(user_id)
    
    @staticmethod
    def delete_notification(notification_id: str, user_id: str) -> bool:
        """Delete a specific notification."""
        try:
            # Find the notification and verify it belongs to the user
            notifications = Notification.find_by_user(user_id, limit=1000)
            notification = next((n for n in notifications if n.id == notification_id), None)
            
            if not notification:
                print(f"Notification not found or doesn't belong to user: {notification_id}")
                return False
            
            return notification.delete()
            
        except Exception as e:
            print(f"Error deleting notification: {e}")
            return False
    
    @staticmethod
    def clear_all_notifications(user_id: str) -> bool:
        """Clear all notifications for a user."""
        return Notification.delete_all_by_user(user_id)
    
    @staticmethod
    def create_pose_generation_alert(user_id: str, current_usage: int, limit: int) -> Optional[Notification]:
        """Create a pose generation limit alert notification."""
        percentage = int((current_usage / limit) * 100) if limit > 0 else 0
        
        # Only create alerts at specific thresholds to avoid spam
        if percentage not in [80, 90, 100]:
            return None
        
        # Check if we already sent this alert recently
        existing_notifications = Notification.find_by_user(user_id, limit=10)
        for notification in existing_notifications:
            if (notification.type == Notification.POSE_GENERATION_ALERT and 
                notification.data.get('percentage') == percentage and
                (datetime.utcnow() - notification.created_at).days < 1):
                # Already sent this alert today
                return None
        
        notification = Notification.create_pose_generation_alert(user_id, current_usage, limit, percentage)
        
        if notification.save():
            return notification
        return None
    
    @staticmethod
    def create_subscription_reminder(user_id: str, subscription_status: str, 
                                   expires_at: Optional[datetime] = None) -> Optional[Notification]:
        """Create a subscription reminder notification."""
        notification = Notification.create_subscription_reminder(user_id, subscription_status, expires_at)
        
        if notification.save():
            return notification
        return None
    
    @staticmethod
    def create_feature_announcement(user_id: str, feature_name: str, description: str) -> Optional[Notification]:
        """Create a feature announcement notification."""
        notification = Notification.create_feature_announcement(user_id, feature_name, description)
        
        if notification.save():
            return notification
        return None
    
    @staticmethod
    def create_system_notification(user_id: str, title: str, message: str,
                                 data: Optional[Dict[str, Any]] = None) -> Optional[Notification]:
        """Create a system notification."""
        notification = Notification.create_system_notification(user_id, title, message, data)
        
        if notification.save():
            return notification
        return None
    
    @staticmethod
    def broadcast_feature_announcement(feature_name: str, description: str, 
                                     target_subscription_tiers: Optional[List[str]] = None) -> int:
        """Broadcast a feature announcement to all users or specific subscription tiers."""
        try:
            from app.services.mongodb_service import MongoDBService
            
            mongodb = MongoDBService()
            users_collection = mongodb.get_collection('users')
            
            # Build query for target users
            query = {'is_active': True}
            if target_subscription_tiers:
                query['subscription_status'] = {'$in': target_subscription_tiers}
            
            users = users_collection.find(query, {'_id': 1})
            count = 0
            
            for user_doc in users:
                user_id = str(user_doc['_id'])
                notification = NotificationService.create_feature_announcement(
                    user_id, feature_name, description
                )
                if notification:
                    count += 1
            
            print(f"Broadcasted feature announcement to {count} users")
            return count
            
        except Exception as e:
            print(f"Error broadcasting feature announcement: {e}")
            return 0
    
    @staticmethod
    def cleanup_old_notifications(days_old: int = 30) -> int:
        """Clean up old notifications to prevent database bloat."""
        try:
            from app.services.mongodb_service import MongoDBService
            
            mongodb = MongoDBService()
            collection = mongodb.get_collection('notifications')
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            result = collection.delete_many({
                'created_at': {'$lt': cutoff_date},
                'is_read': True  # Only delete read notifications
            })
            
            print(f"Cleaned up {result.deleted_count} old notifications")
            return result.deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old notifications: {e}")
            return 0
