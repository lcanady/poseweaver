"""
Dynamic plugin execution engine for PoseWeaver.

This engine loads and executes plugins based on user installations,
enabling extensible gameplay through event-driven hooks.
"""
import importlib
import logging
from typing import Dict, Any, List, Optional, Type
from ..models.marketplace import PluginManifest, UserPluginInstall
from ..plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class PluginEngine:
    """
    Core plugin execution engine.
    
    Responsibilities:
    - Load active plugins for a user/scene context
    - Trigger events and execute plugin hooks
    - Manage plugin pipeline (modification/blocking)
    - Handle errors gracefully
    """
    
    def __init__(self):
        """Initialize the plugin engine."""
        self._loaded_plugins: List[BasePlugin] = []
        self._context: Dict[str, Any] = {}
    
    def load_context(self, user_id: str, scene_id: Optional[str] = None) -> None:
        """
        Load active plugins for a specific user and scene context.
        
        This method:
        1. Fetches active UserPluginInstall records for the user
        2. Retrieves corresponding PluginManifest definitions
        3. Dynamically imports and instantiates plugin classes
        4. Stores loaded plugins for event triggering
        
        Args:
            user_id: ID of the user whose plugins to load
            scene_id: Optional scene ID for scene-specific context
        
        Raises:
            ValueError: If user_id is invalid
        """
        if not user_id:
            raise ValueError("user_id is required for loading plugin context")
        
        logger.info(f"Loading plugin context for user {user_id}, scene {scene_id}")
        
        # Store context
        self._context = {
            'user_id': user_id,
            'scene_id': scene_id
        }
        
        # Clear previously loaded plugins
        self._loaded_plugins = []
        
        try:
            # Fetch active plugin installations for this user
            installs = UserPluginInstall.find_active_by_user(user_id)
            
            if not installs:
                logger.info(f"No active plugins found for user {user_id}")
                return
            
            logger.info(f"Found {len(installs)} active plugin(s) for user {user_id}")
            
            # Load each plugin
            for install in installs:
                try:
                    # Get the plugin manifest
                    manifest = PluginManifest.find_by_id(install.plugin_id)
                    if not manifest:
                        logger.warning(f"Plugin manifest {install.plugin_id} not found, skipping")
                        continue
                    
                    # Import and instantiate the plugin class
                    plugin_instance = self._import_plugin_class(
                        code_ref=manifest.code_ref,
                        config=install.settings
                    )
                    
                    if plugin_instance:
                        self._loaded_plugins.append(plugin_instance)
                        logger.info(f"Loaded plugin: {manifest.name} ({manifest.code_ref})")
                    
                except Exception as e:
                    logger.error(f"Failed to load plugin {install.plugin_id}: {e}", exc_info=True)
                    # Continue loading other plugins even if one fails
                    continue
            
            logger.info(f"Successfully loaded {len(self._loaded_plugins)} plugin(s)")
            
        except Exception as e:
            logger.error(f"Error loading plugin context for user {user_id}: {e}", exc_info=True)
            # Don't raise - gracefully degrade to no plugins
    
    def trigger_event(
        self,
        event_name: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger an event and execute all relevant plugin hooks.
        
        This implements a pipeline pattern where:
        - Each plugin receives the payload (potentially modified by previous plugins)
        - Plugins can modify the payload and pass it to the next plugin
        - Any plugin can return "BLOCK" to stop the pipeline and prevent the event
        - If all plugins pass, the final (potentially modified) payload is returned
        
        Args:
            event_name: Name of the event (e.g., "ON_POSE_CREATE")
            payload: Event data to process
            context: Optional additional context for the event
        
        Returns:
            Modified payload dict, or "BLOCK" if any plugin blocks the event
            Returns None if no plugins are loaded
        """
        if not self._loaded_plugins:
            logger.debug(f"No plugins loaded, event {event_name} passes through")
            return payload
        
        logger.info(f"Triggering event {event_name} with {len(self._loaded_plugins)} plugin(s)")
        
        # Merge context
        full_context = {**self._context, **(context or {})}
        
        # Start with the original payload
        current_payload = payload.copy()
        
        # Execute each plugin in sequence
        for plugin in self._loaded_plugins:
            try:
                # Check if this plugin handles this event
                if event_name not in plugin.get_hooks():
                    logger.debug(f"Plugin {plugin.get_name()} does not handle {event_name}, skipping")
                    continue
                
                logger.debug(f"Executing {plugin.get_name()}.{self._get_hook_method_name(event_name)}")
                
                # Call the appropriate hook method
                result = self._call_plugin_hook(plugin, event_name, current_payload, full_context)
                
                # Handle the result
                if result == "BLOCK":
                    logger.warning(f"Plugin {plugin.get_name()} blocked event {event_name}")
                    return "BLOCK"
                elif result is None:
                    # None means no modification, continue with current payload
                    logger.debug(f"Plugin {plugin.get_name()} passed through without modification")
                    continue
                elif isinstance(result, dict):
                    # Plugin modified the payload
                    logger.debug(f"Plugin {plugin.get_name()} modified the payload")
                    current_payload = result
                else:
                    logger.warning(f"Plugin {plugin.get_name()} returned invalid type: {type(result)}, skipping")
                    continue
                
            except Exception as e:
                # Log error but continue with other plugins
                logger.error(f"Error executing plugin {plugin.get_name()} for event {event_name}: {e}", exc_info=True)
                continue
        
        logger.info(f"Event {event_name} completed successfully")
        return current_payload
    
    def _import_plugin_class(
        self,
        code_ref: str,
        config: Dict[str, Any]
    ) -> Optional[BasePlugin]:
        """
        Dynamically import and instantiate a plugin class.
        
        Args:
            code_ref: Python import path (e.g., "app.plugins.examples.dice_roller.DiceRollerPlugin")
            config: User settings to pass to plugin constructor
        
        Returns:
            Instantiated plugin instance, or None if import fails
        """
        try:
            # Split module path and class name
            if '.' not in code_ref:
                logger.error(f"Invalid code_ref format: {code_ref}")
                return None
            
            module_path, class_name = code_ref.rsplit('.', 1)
            
            # Dynamically import the module
            logger.debug(f"Importing module: {module_path}")
            module = importlib.import_module(module_path)
            
            # Get the class from the module
            plugin_class = getattr(module, class_name, None)
            if not plugin_class:
                logger.error(f"Class {class_name} not found in module {module_path}")
                return None
            
            # Verify it's a BasePlugin subclass
            if not issubclass(plugin_class, BasePlugin):
                logger.error(f"Class {class_name} is not a subclass of BasePlugin")
                return None
            
            # Instantiate the plugin with config
            logger.debug(f"Instantiating {class_name} with config: {config}")
            plugin_instance = plugin_class(config=config)
            
            return plugin_instance
            
        except Exception as e:
            logger.error(f"Failed to import plugin from {code_ref}: {e}", exc_info=True)
            return None
    
    def _call_plugin_hook(
        self,
        plugin: BasePlugin,
        event_name: str,
        payload: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """
        Call the appropriate hook method on a plugin.
        
        Args:
            plugin: Plugin instance to call
            event_name: Event name (maps to method name)
            payload: Event payload
            context: Event context
        
        Returns:
            Result from the plugin hook method
        """
        method_name = self._get_hook_method_name(event_name)
        method = getattr(plugin, method_name, None)
        
        if not method:
            logger.warning(f"Plugin {plugin.get_name()} declared hook {event_name} but has no {method_name} method")
            return None
        
        # Call the method with payload (context available via plugin.config if needed)
        return method(payload)
    
    def _get_hook_method_name(self, event_name: str) -> str:
        """
        Convert event name to method name.
        
        Args:
            event_name: Event name (e.g., "ON_POSE_CREATE")
        
        Returns:
            Method name (e.g., "on_pose_create")
        """
        return event_name.lower()
    
    def get_loaded_plugins(self) -> List[str]:
        """
        Get list of currently loaded plugin names.
        
        Returns:
            List of plugin names
        """
        return [plugin.get_name() for plugin in self._loaded_plugins]
    
    def clear_context(self) -> None:
        """Clear the current context and unload all plugins."""
        self._loaded_plugins = []
        self._context = {}
        logger.info("Plugin context cleared")
