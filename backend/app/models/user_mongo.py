"""
MongoDB User model for authentication.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from flask_bcrypt import Bcrypt
from email_validator import validate_email, EmailNotValidError
from bson import ObjectId
from ..extensions import get_db

bcrypt = Bcrypt()


class User:
    """User model for Database storage."""
    
    COLLECTION_NAME = 'users'
    
    def __init__(self, email: str, password: str = None, display_name: str = None,
                 bio: str = None, avatar_url: str = None, is_active: bool = True, _id: str = None, 
                 created_at: datetime = None, updated_at: datetime = None, subscription_status: str = 'free',
                 is_admin: bool = False, subscription_expires_at: datetime = None,
                 pose_generations_used: int = 0, pose_generations_reset_date: datetime = None,
                 extra_pose_generations: int = 0, credits: int = 0, stripe_customer_id: str = None, settings: Dict[str, Any] = None):
        """Initialize a User instance."""
        self.id = _id
        self.email = email
        self.display_name = display_name or email.split('@')[0]
        self.bio = bio
        self.avatar_url = avatar_url
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
        self.subscription_status = subscription_status  # 'free', 'premium', 'expired'
        self.is_admin = is_admin
        self.subscription_expires_at = subscription_expires_at
        self.pose_generations_used = pose_generations_used
        self.pose_generations_reset_date = pose_generations_reset_date
        self.extra_pose_generations = extra_pose_generations
        self.credits = credits
        self.stripe_customer_id = stripe_customer_id
        
        # User settings with defaults
        self.settings = settings or {
            'theme': 'system',
            'notifications': {
                'email_updates': True,
                'pose_generation_alerts': False,
                'subscription_reminders': True,
                'feature_announcements': True
            },
            'privacy': {
                'profile_visibility': 'private',
                'analytics_tracking': True,
                'data_collection': True
            },
            'preferences': {
                'default_enhancement_style': 'balanced',
                'auto_save_poses': True,
                'show_advanced_settings': False,
                'character_limit_warnings': True
            }
        }
        
        # Hash password if provided
        if password:
            self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        else:
            self.password_hash = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create a User instance from a dictionary."""
        # Standardize id
        user_id = None
        if '_id' in data:
            user_id = str(data['_id'])
        elif 'id' in data:
            user_id = str(data['id'])

        user = cls(
            email=data['email'],
            display_name=data.get('display_name'),
            bio=data.get('bio'),
            avatar_url=data.get('avatar_url'),
            is_active=data.get('is_active', True),
            _id=user_id,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            subscription_status=data.get('subscription_status', 'free'),
            is_admin=data.get('is_admin', False),
            subscription_expires_at=data.get('subscription_expires_at'),
            pose_generations_used=data.get('pose_generations_used', 0),
            pose_generations_reset_date=data.get('pose_generations_reset_date'),
            extra_pose_generations=data.get('extra_pose_generations', 0),
            credits=data.get('credits', 0),
            stripe_customer_id=data.get('stripe_customer_id'),
            settings=data.get('settings')
        )
        user.password_hash = data.get('password_hash')
        return user
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert User instance to dictionary."""
        data = {
            'email': self.email,
            'password_hash': self.password_hash,
            'display_name': self.display_name,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'subscription_status': self.subscription_status,
            'is_admin': self.is_admin,
            'subscription_expires_at': self.subscription_expires_at,
            'pose_generations_used': self.pose_generations_used,
            'pose_generations_reset_date': self.pose_generations_reset_date,
            'extra_pose_generations': self.extra_pose_generations,
            'credits': self.credits,
            'stripe_customer_id': self.stripe_customer_id,
            'settings': self.settings
        }
        if self.id:
            data['id'] = str(self.id)
            # Legacy assumption: callers might expect _id if they are legacy code
            data['_id'] = str(self.id)
        return data
    
    def save(self) -> str:
        """Save user to Database."""
        db = get_db()
        
        if self.id:
            # Update existing user
            user_data = self.to_dict()
            user_data.pop('_id', None)  # Remove _id from update data
            user_data.pop('id', None)
            user_data.pop('created_at', None)  # Don't update created_at
            
            db.update_one(
                self.COLLECTION_NAME,
                {'id': self.id},
                user_data
            )
            return self.id
        else:
            # Create new user
            user_data = self.to_dict()
            user_data.pop('_id', None)
            user_data.pop('id', None)
            
            self.id = db.insert_one(self.COLLECTION_NAME, user_data)
            return self.id
    
    def delete(self) -> bool:
        """Delete user from MongoDB."""
        if not self.id:
            return False
        
        db = get_db()
        return db.delete_one(
            self.COLLECTION_NAME,
            {'id': self.id}
        )
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches the user's password."""
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def set_password(self, password: str) -> None:
        """Set a new password for the user."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def get_effective_subscription_status(self) -> str:
        """Get the effective subscription status, checking for expiration."""
        if self.is_admin:
            return 'admin'
        
        if self.subscription_status == 'premium':
            # Check if subscription has expired
            if self.subscription_expires_at and datetime.utcnow() > self.subscription_expires_at:
                return 'expired'
            return 'premium'
        
        return self.subscription_status
    
    def get_character_limit(self) -> int:
        """Get the character limit based on subscription status."""
        effective_status = self.get_effective_subscription_status()
        
        if effective_status == 'admin':
            return -1  # Unlimited for admins
        elif effective_status == 'premium':  # Legacy premium users
            return -1  # Unlimited for legacy premium users
        elif effective_status == 'pro':
            return -1  # Unlimited for pro tier users
        elif effective_status == 'basic':
            return 20  # 20 characters for basic tier users
        else:  # free, expired, or any other status
            return 5
    
    def can_create_character(self, current_character_count: int) -> bool:
        """Check if user can create another character."""
        limit = self.get_character_limit()
        if limit == -1:  # Unlimited
            return True
        return current_character_count < limit
    
    def needs_upgrade_for_characters(self) -> bool:
        """Check if user needs to upgrade to create more characters."""
        effective_status = self.get_effective_subscription_status()
        return effective_status in ['free', 'expired']
    
    def get_pose_generation_limit(self) -> int:
        """Get the monthly pose generation limit based on subscription status."""
        effective_status = self.get_effective_subscription_status()
        
        if effective_status == 'admin':
            return -1  # Unlimited for admins
        elif effective_status == 'premium':  # Legacy premium users
            return 5000  # Legacy premium limit
        elif effective_status == 'pro':
            return 5000  # Pro tier gets 5000 generations per month
        elif effective_status == 'basic':
            return 1000  # Basic tier gets 1000 generations per month
        else:  # free, expired, or any other status
            return 100  # Free tier gets 100 free generations per month
    
    def get_credits(self) -> int:
        """Get the user's current credit balance."""
        return self.credits
    
    def add_credits(self, amount: int) -> None:
        """Add credits to the user's balance."""
        self.credits += amount
        self.save()
    
    def use_credits(self, amount: int) -> bool:
        """Use credits from the user's balance. Returns True if successful."""
        if self.credits >= amount:
            self.credits -= amount
            self.save()
            return True
        return False

    def get_available_pose_generations(self) -> int:
        """Get the number of pose generations available this month."""
        # Reset monthly usage if needed
        self._reset_monthly_usage_if_needed()
        
        limit = self.get_pose_generation_limit()
        if limit == -1:  # Unlimited
            return -1
        
        # Calculate available generations including extra purchased ones
        total_available = limit + self.extra_pose_generations
        used = self.pose_generations_used
        remaining = max(0, total_available - used)
        
        return remaining
    
    def can_generate_pose(self) -> bool:
        """Check if user can generate another pose."""
        # Use credit system first
        if self.credits > 0:
            return True
            
        # Fallback to monthly limits for legacy users
        available = self.get_available_pose_generations()
        return available == -1 or available > 0
    
    def use_pose_generation(self) -> bool:
        """Use one pose generation and update the counter. Returns True if successful."""
        # Try to use credits first
        if self.use_credits(1):
            return True
            
        if not self.can_generate_pose():
            return False
        
        # Reset monthly usage if needed
        self._reset_monthly_usage_if_needed()
        
        # Increment usage counter
        self.pose_generations_used += 1
        self.save()
        return True
    
    def add_extra_pose_generations(self, count: int) -> None:
        """Add extra pose generations (for purchases). Maps to unified credit system."""
        self.add_credits(count)
    
    def needs_upgrade_for_poses(self) -> bool:
        """Check if user needs to upgrade for more pose generations."""
        effective_status = self.get_effective_subscription_status()
        return effective_status in ['free', 'expired'] and not self.can_generate_pose()
    
    def can_purchase_extra_generations(self) -> bool:
        """Check if user can purchase extra generations (available to all users)."""
        # Recharge packs are available to all user tiers (free, basic, pro, premium, admin)
        return True
    
    def set_stripe_customer_id(self, stripe_customer_id: str) -> None:
        """Set the Stripe customer ID for this user."""
        self.stripe_customer_id = stripe_customer_id
        self.save()
    
    def upgrade_to_subscription(self, tier: str, stripe_subscription_id: str = None) -> None:
        """Upgrade user to a subscription tier."""
        from datetime import datetime, timedelta
        
        if tier in ['basic', 'pro']:
            self.subscription_status = tier
            # Set expiration to 1 month from now
            self.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
            self.reset_monthly_generations()
            self.save()
    
    def reset_monthly_generations(self) -> None:
        """Reset monthly generation count (for subscription renewals)."""
        from datetime import datetime
        self.pose_generations_used = 0
        self.pose_generations_reset_date = datetime(datetime.utcnow().year, datetime.utcnow().month, 1)
        self.save()
    
    def activate_subscription(self) -> None:
        """Activate subscription (from past_due or other status)."""
        from datetime import datetime, timedelta
        
        # Reactivate subscription if it was suspended
        if self.subscription_status in ['basic', 'pro']:
            # Extend expiration if needed
            if not self.subscription_expires_at or self.subscription_expires_at < datetime.utcnow():
                self.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
            self.save()
    
    def set_subscription_grace_period(self) -> None:
        """Set user in grace period for failed payments."""
        # Keep current subscription active but mark for potential downgrade
        # You might want to add a grace_period_expires field
        pass
    
    def suspend_subscription(self) -> None:
        """Suspend subscription due to failed payments."""
        # Keep the subscription tier but mark as expired
        from datetime import datetime
        self.subscription_expires_at = datetime.utcnow()
        self.save()
    
    def cancel_subscription(self) -> None:
        """Cancel subscription and revert to free tier."""
        from datetime import datetime
        self.subscription_status = 'free'
        self.subscription_expires_at = datetime.utcnow()
        self.save()
    
    def revert_to_free_tier(self) -> None:
        """Revert user to free tier while preserving extra generations."""
        from datetime import datetime
        self.subscription_status = 'free'
        self.subscription_expires_at = datetime.utcnow()
        # Keep extra_pose_generations - they don't expire
        self.save()
    
    def update_subscription_tier(self, new_tier: str) -> None:
        """Update subscription tier (for upgrades/downgrades)."""
        from datetime import datetime, timedelta
        
        if new_tier in ['basic', 'pro']:
            self.subscription_status = new_tier
            # Extend expiration for tier changes
            self.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
            self.save()
    
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """Update user settings with new values."""
        from datetime import datetime
        if new_settings:
            # Deep merge settings to preserve existing values not being updated
            for key, value in new_settings.items():
                if key in self.settings and isinstance(self.settings[key], dict) and isinstance(value, dict):
                    self.settings[key].update(value)
                else:
                    self.settings[key] = value
            self.updated_at = datetime.utcnow()
            self.save()
    
    def get_settings(self) -> Dict[str, Any]:
        """Get user settings."""
        return self.settings
    
    def _reset_monthly_usage_if_needed(self) -> None:
        """Reset monthly usage counter if a new month has started."""
        from datetime import datetime
        import calendar
        
        now = datetime.utcnow()
        
        # If no reset date is set, set it to the start of current month
        if not self.pose_generations_reset_date:
            self.pose_generations_reset_date = datetime(now.year, now.month, 1)
            self.pose_generations_used = 0
            return
        
        # Check if we've moved to a new month
        reset_date = self.pose_generations_reset_date
        if now.year > reset_date.year or (now.year == reset_date.year and now.month > reset_date.month):
            # Reset for new month
            self.pose_generations_reset_date = datetime(now.year, now.month, 1)
            self.pose_generations_used = 0
            # Keep extra generations - they don't expire monthly
    
    @classmethod
    def find_by_id(cls, user_id: str) -> Optional['User']:
        """Find user by ID."""
        db = get_db()
        user_data = db.find_one(
            cls.COLLECTION_NAME,
            {'id': user_id}
        )
        
        if not user_data and ObjectId.is_valid(user_id):
            # Fallback for old IDs
            user_data = db.find_one(
                cls.COLLECTION_NAME,
                {'_id': ObjectId(user_id)}
            )

        if user_data:
            return cls.from_dict(user_data)
        return None
    
    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """Find user by email."""
        db = get_db()
        user_data = db.find_one(
            cls.COLLECTION_NAME,
            {'email': email}
        )
        
        if user_data:
            return cls.from_dict(user_data)
        return None
    
    @classmethod
    def find_by_stripe_customer_id(cls, stripe_customer_id: str) -> Optional['User']:
        """Find user by Stripe customer ID."""
        db = get_db()
        user_data = db.find_one(
            cls.COLLECTION_NAME,
            {'stripe_customer_id': stripe_customer_id}
        )
        
        if user_data:
            return cls.from_dict(user_data)
        return None
    
    @classmethod
    def create_user(cls, email: str, password: str, display_name: str = None, avatar_url: str = None) -> 'User':
        """Create a new user with validation."""
        # Validate email
        try:
            # Allow example.com for testing
            if not email.endswith('@example.com'):
                validate_email(email)
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email: {e}")
        
        # Check if user already exists
        if cls.find_by_email(email):
            raise ValueError("User with this email already exists")
        
        # Create and save user
        user = cls(
            email=email,
            password=password,
            display_name=display_name,
            avatar_url=avatar_url
        )
        user.save()
        return user
    
    @classmethod
    def authenticate(cls, email: str, password: str) -> Optional['User']:
        """Authenticate user with email and password."""
        user = cls.find_by_email(email)
        if user and user.check_password(password):
            return user
        return None
    
    @classmethod
    def get_all_users(cls, limit: int = 100) -> list['User']:
        """Get all users (for admin purposes)."""
        db = get_db()
        users_data = db.find_many(
            cls.COLLECTION_NAME,
            limit=limit,
            sort=[('created_at', -1)]
        )
        
        return [cls.from_dict(user_data) for user_data in users_data]
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for the User collection."""
        db = get_db()
        
        # Create unique index on email
        db.create_index(cls.COLLECTION_NAME, 'email', unique=True)
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User {self.email}>" 