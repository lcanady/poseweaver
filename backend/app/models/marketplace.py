"""
Marketplace models for plugin management.
Supports a platform model where users browse, purchase, and configure plugins for their scenes.
"""
from typing import Dict, Any, Optional, List, Type
from datetime import datetime, UTC
import uuid
from .base_model import BaseModel
from ..extensions import get_db


class PluginManifest(BaseModel):
    """
    Plugin Manifest model - defines available plugins in the marketplace.
    
    A plugin is an extension that can be attached to scenes via hooks.
    Plugins have configurable settings defined by a JSON Schema.
    """
    
    COLLECTION_NAME = 'plugin_manifests'
    
    def __init__(
        self,
        name: str,
        description: str = '',
        price: int = 0,
        hooks: Optional[List[str]] = None,
        config_schema: Optional[Dict[str, Any]] = None,
        code_ref: str = '',
        is_official: bool = False,
        author: str = '',
        version: str = '1.0.0',
        **kwargs
    ):
        """
        Initialize a PluginManifest instance.
        
        Args:
            name: Display name of the plugin
            description: Detailed description of plugin functionality
            price: Price in cents (0 for free plugins)
            hooks: List of event hooks (e.g., ["ON_POSE", "ON_SCENE_START"])
            config_schema: JSON Schema defining the plugin's configuration UI
            code_ref: Reference to plugin code (path, URL, or stored script identifier)
            is_official: Whether this is an official plugin
            author: Plugin author name
            version: Semantic version string
        """
        super().__init__(**kwargs)
        
        # Generate UUID if not provided
        if not self.id:
            self.id = str(uuid.uuid4())
        
        self.name = name
        self.description = description
        self.price = price
        self.hooks = hooks or []
        self.config_schema = config_schema or self._get_default_schema()
        self.code_ref = code_ref
        self.is_official = is_official
        self.author = author
        self.version = version
        
        # Additional metadata
        self.download_count = kwargs.get('download_count', 0)
        self.rating = kwargs.get('rating', 0.0)
        self.stripe_price_id = kwargs.get('stripe_price_id', None)
        self.stripe_product_id = kwargs.get('stripe_product_id', None)
    
    @staticmethod
    def _get_default_schema() -> Dict[str, Any]:
        """Return a default empty JSON Schema for plugins without configuration."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": "Plugin Configuration",
            "properties": {},
            "required": []
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PluginManifest to dictionary."""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'hooks': self.hooks,
            'config_schema': self.config_schema,
            'code_ref': self.code_ref,
            'is_official': self.is_official,
            'author': self.author,
            'version': self.version,
            'download_count': self.download_count,
            'rating': self.rating,
            'stripe_price_id': self.stripe_price_id,
            'stripe_product_id': self.stripe_product_id
        })
        return data
    
    @classmethod
    def from_dict(cls: Type['PluginManifest'], data: Dict[str, Any]) -> Optional['PluginManifest']:
        """Create PluginManifest from dictionary."""
        if not data:
            return None
        
        # Standardize id
        if '_id' in data:
            data['id'] = str(data['_id'])
        
        return cls(**data)
    
    @classmethod
    def find_by_hook(cls, hook: str) -> List['PluginManifest']:
        """Find all plugins that support a specific hook."""
        db = get_db()
        results = db.find_many(
            cls.COLLECTION_NAME,
            filter_dict={'hooks': hook},
            limit=100
        )
        return [cls.from_dict(data) for data in results if data]
    
    @classmethod
    def find_official_plugins(cls) -> List['PluginManifest']:
        """Find all official plugins."""
        db = get_db()
        results = db.find_many(
            cls.COLLECTION_NAME,
            filter_dict={'is_official': True},
            limit=100,
            sort=[('name', 1)]
        )
        return [cls.from_dict(data) for data in results if data]
    
    @classmethod
    def find_free_plugins(cls) -> List['PluginManifest']:
        """Find all free plugins."""
        db = get_db()
        results = db.find_many(
            cls.COLLECTION_NAME,
            filter_dict={'price': 0},
            limit=100,
            sort=[('download_count', -1)]
        )
        return [cls.from_dict(data) for data in results if data]
    
    def increment_download_count(self) -> None:
        """Increment the download counter for this plugin."""
        self.download_count += 1
        self.save()
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for PluginManifest collection."""
        db = get_db()
        db.create_index(cls.COLLECTION_NAME, 'name')
        db.create_index(cls.COLLECTION_NAME, 'hooks')
        db.create_index(cls.COLLECTION_NAME, 'is_official')
        db.create_index(cls.COLLECTION_NAME, 'stripe_price_id')


class UserPluginInstall(BaseModel):
    """
    User Plugin Installation model - tracks which plugins users have purchased/installed.
    
    Stores user-specific configuration values for each installed plugin.
    """
    
    COLLECTION_NAME = 'user_plugin_installs'
    
    def __init__(
        self,
        user_id: str,
        plugin_id: str,
        is_active: bool = True,
        settings: Optional[Dict[str, Any]] = None,
        purchased_at: Optional[datetime] = None,
        **kwargs
    ):
        """
        Initialize a UserPluginInstall instance.
        
        Args:
            user_id: Reference to User ID
            plugin_id: Reference to PluginManifest ID
            is_active: Whether the plugin is currently active for this user
            settings: User's configuration values matching the plugin's config_schema
            purchased_at: Timestamp of when the plugin was purchased
        """
        super().__init__(**kwargs)
        
        # Generate UUID if not provided
        if not self.id:
            self.id = str(uuid.uuid4())
        
        self.user_id = user_id
        self.plugin_id = plugin_id
        self.is_active = is_active
        self.settings = settings or {}
        self.purchased_at = purchased_at or datetime.now(UTC)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert UserPluginInstall to dictionary."""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'plugin_id': self.plugin_id,
            'is_active': self.is_active,
            'settings': self.settings,
            'purchased_at': self.purchased_at.isoformat() if isinstance(self.purchased_at, datetime) else self.purchased_at
        })
        return data
    
    @classmethod
    def from_dict(cls: Type['UserPluginInstall'], data: Dict[str, Any]) -> Optional['UserPluginInstall']:
        """Create UserPluginInstall from dictionary."""
        if not data:
            return None
        
        # Standardize id
        if '_id' in data:
            data['id'] = str(data['_id'])
        
        return cls(**data)
    
    @classmethod
    def find_by_user(cls, user_id: str) -> List['UserPluginInstall']:
        """Find all plugin installations for a specific user."""
        db = get_db()
        results = db.find_many(
            cls.COLLECTION_NAME,
            filter_dict={'user_id': user_id},
            limit=100,
            sort=[('purchased_at', -1)]
        )
        return [cls.from_dict(data) for data in results if data]
    
    @classmethod
    def find_active_by_user(cls, user_id: str) -> List['UserPluginInstall']:
        """Find all active plugin installations for a specific user."""
        db = get_db()
        results = db.find_many(
            cls.COLLECTION_NAME,
            filter_dict={'user_id': user_id, 'is_active': True},
            limit=100
        )
        return [cls.from_dict(data) for data in results if data]
    
    @classmethod
    def find_by_user_and_plugin(cls, user_id: str, plugin_id: str) -> Optional['UserPluginInstall']:
        """Find a specific plugin installation for a user."""
        db = get_db()
        data = db.find_one(
            cls.COLLECTION_NAME,
            {'user_id': user_id, 'plugin_id': plugin_id}
        )
        return cls.from_dict(data) if data else None
    
    @classmethod
    def user_has_plugin(cls, user_id: str, plugin_id: str) -> bool:
        """Check if a user has installed a specific plugin."""
        install = cls.find_by_user_and_plugin(user_id, plugin_id)
        return install is not None
    
    def toggle_active(self) -> None:
        """Toggle the active state of this plugin installation."""
        self.is_active = not self.is_active
        self.save()
    
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """Update the user's configuration settings for this plugin."""
        self.settings.update(new_settings)
        self.save()
    
    @classmethod
    def initialize_indexes(cls) -> None:
        """Initialize database indexes for UserPluginInstall collection."""
        db = get_db()
        db.create_index(cls.COLLECTION_NAME, 'user_id')
        db.create_index(cls.COLLECTION_NAME, 'plugin_id')
        # Compound index for finding user's specific plugin
        db.create_index(cls.COLLECTION_NAME, [('user_id', 1), ('plugin_id', 1)], unique=True)
