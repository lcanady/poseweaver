"""
Notification model for in-app notifications.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId
from app.services.mongodb_service import MongoDBService

class Notification:
    """Notification model for in-app notifications."""
    
    # Notification types
    POSE_GENERATION_ALERT = 'pose_generation_alert'
    SUBSCRIPTION_REMINDER = 'subscription_reminder'
    FEATURE_ANNOUNCEMENT = 'feature_announcement'
    SYSTEM_NOTIFICATION = 'system_notification'
    
    VALID_TYPES = [
        POSE_GENERATION_ALERT,
        SUBSCRIPTION_REMINDER,
        FEATURE_ANNOUNCEMENT,
        SYSTEM_NOTIFICATION
    ]
    
    def __init__(self, user_id: str, notification_type: str, title: str, message: str,
                 data: Optional[Dict[str, Any]] = None, is_read: bool = False,
                 created_at: Optional[datetime] = None, _id: Optional[str] = None):
        """Initialize a Notification instance."""
        if notification_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid notification type: {notification_type}")
            
        self.id = _id
        self.user_id = user_id
        self.type = notification_type
        self.title = title
        self.message = message
        self.data = data or {}
        self.is_read = is_read
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            '_id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create notification from dictionary."""
        return cls(
            user_id=data['user_id'],
            notification_type=data['type'],
            title=data['title'],
            message=data['message'],
            data=data.get('data', {}),
            is_read=data.get('is_read', False),
            created_at=data.get('created_at'),
            _id=str(data.get('_id')) if data.get('_id') else None
        )
    
    def save(self) -> bool:
        """Save notification to database."""
        try:
            mongodb = MongoDBService()
            collection = mongodb.get_collection('notifications')
            
            notification_data = self.to_dict()
            
            if self.id:
                # Update existing notification
                result = collection.update_one(
                    {'_id': ObjectId(self.id)},
                    {'$set': notification_data}
                )
                return result.modified_count > 0
            else:
                # Create new notification
                del notification_data['_id']  # Remove None _id
                result = collection.insert_one(notification_data)
                self.id = str(result.inserted_id)
                return True
                
        except Exception as e:
            print(f"Error saving notification: {e}")
            return False
    
    def mark_as_read(self) -> bool:
        """Mark notification as read."""
        self.is_read = True
        return self.save()
    
    def delete(self) -> bool:
        """Delete notification from database."""
        if not self.id:
            return False
            
        try:
            mongodb = MongoDBService()
            collection = mongodb.get_collection('notifications')
            result = collection.delete_one({'_id': ObjectId(self.id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting notification: {e}")
            return False
    
    @classmethod
    def find_by_user(cls, user_id: str, limit: int = 50, skip: int = 0, 
                     unread_only: bool = False) -> List['Notification']:
        """Find notifications for a user."""
        try:
            mongodb = MongoDBService()
            collection = mongodb.get_collection('notifications')
            
            query = {'user_id': user_id}
            if unread_only:
                query['is_read'] = False
            
            cursor = collection.find(query).sort('created_at', -1).skip(skip).limit(limit)
            notifications = []
            
            for doc in cursor:
                notifications.append(cls.from_dict(doc))
            
            return notifications
            
        except Exception as e:
            print(f"Error finding notifications: {e}")
            return []
    
    @classmethod
    def count_unread_by_user(cls, user_id: str) -> int:
        """Count unread notifications for a user."""
        try:
            mongodb = MongoDBService()
            collection = mongodb.get_collection('notifications')
            return collection.count_documents({'user_id': user_id, 'is_read': False})
        except Exception as e:
            print(f"Error counting unread notifications: {e}")
            return 0
    
    @classmethod
    def mark_all_read_by_user(cls, user_id: str) -> bool:
        """Mark all notifications as read for a user."""
        try:
            mongodb = MongoDBService()
            collection = mongodb.get_collection('notifications')
            result = collection.update_many(
                {'user_id': user_id, 'is_read': False},
                {'$set': {'is_read': True}}
            )
            return True
        except Exception as e:
            print(f"Error marking all notifications as read: {e}")
            return False
    
    @classmethod
    def delete_all_by_user(cls, user_id: str) -> bool:
        """Delete all notifications for a user."""
        try:
            mongodb = MongoDBService()
            collection = mongodb.get_collection('notifications')
            collection.delete_many({'user_id': user_id})
            return True
        except Exception as e:
            print(f"Error deleting all notifications: {e}")
            return False
    
    @classmethod
    def create_pose_generation_alert(cls, user_id: str, current_usage: int, 
                                   limit: int, percentage: int) -> 'Notification':
        """Create a pose generation limit alert."""
        if percentage >= 100:
            title = "Pose Generation Limit Reached"
            message = f"You've used all {limit} of your monthly pose generations. Upgrade your plan or purchase additional generations to continue."
        elif percentage >= 90:
            title = "Pose Generation Limit Almost Reached"
            message = f"You've used {current_usage} of {limit} monthly pose generations ({percentage}%). Consider upgrading your plan."
        else:
            title = "Pose Generation Limit Warning"
            message = f"You've used {current_usage} of {limit} monthly pose generations ({percentage}%)."
        
        return cls(
            user_id=user_id,
            notification_type=cls.POSE_GENERATION_ALERT,
            title=title,
            message=message,
            data={
                'current_usage': current_usage,
                'limit': limit,
                'percentage': percentage
            }
        )
    
    @classmethod
    def create_subscription_reminder(cls, user_id: str, subscription_status: str, 
                                   expires_at: Optional[datetime] = None) -> 'Notification':
        """Create a subscription reminder notification."""
        if subscription_status == 'expired':
            title = "Subscription Expired"
            message = "Your subscription has expired. Renew now to continue accessing premium features."
        elif expires_at:
            days_left = (expires_at - datetime.utcnow()).days
            if days_left <= 3:
                title = "Subscription Expiring Soon"
                message = f"Your subscription expires in {days_left} days. Renew now to avoid interruption."
            else:
                title = "Subscription Renewal Reminder"
                message = f"Your subscription expires in {days_left} days."
        else:
            title = "Subscription Update"
            message = "There's an update regarding your subscription."
        
        return cls(
            user_id=user_id,
            notification_type=cls.SUBSCRIPTION_REMINDER,
            title=title,
            message=message,
            data={
                'subscription_status': subscription_status,
                'expires_at': expires_at.isoformat() if expires_at else None
            }
        )
    
    @classmethod
    def create_feature_announcement(cls, user_id: str, feature_name: str, 
                                  description: str) -> 'Notification':
        """Create a feature announcement notification."""
        return cls(
            user_id=user_id,
            notification_type=cls.FEATURE_ANNOUNCEMENT,
            title=f"New Feature: {feature_name}",
            message=description,
            data={'feature_name': feature_name}
        )
    
    @classmethod
    def create_system_notification(cls, user_id: str, title: str, message: str,
                                 data: Optional[Dict[str, Any]] = None) -> 'Notification':
        """Create a system notification."""
        return cls(
            user_id=user_id,
            notification_type=cls.SYSTEM_NOTIFICATION,
            title=title,
            message=message,
            data=data
        )
