"""
Base plugin interface for the PoseWeaver plugin system.

All plugins must inherit from BasePlugin and implement the required methods.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BasePlugin(ABC):
    """
    Abstract base class for all PoseWeaver plugins.
    
    Plugins can hook into various events in the MUSH engine to extend functionality.
    All plugins receive configuration from the user's plugin installation settings.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the plugin with user configuration.
        
        Args:
            config: User-specific settings from UserPluginInstall.settings
        """
        self.config = config or {}
    
    @abstractmethod
    def get_hooks(self) -> List[str]:
        """
        Return list of hook names this plugin handles.
        
        Available hooks:
        - ON_POSE_CREATE: Triggered before a pose is created
        - ON_COMMAND: Triggered when a command is executed
        - ON_SCENE_ENTER: Triggered when a user enters a scene
        
        Returns:
            List of hook names (e.g., ["ON_POSE_CREATE", "ON_COMMAND"])
        """
        pass
    
    def on_pose_create(self, pose_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Hook called before a pose is created.
        
        The plugin can:
        1. Return modified pose_data to change the pose
        2. Return None to pass through unchanged
        3. Return "BLOCK" to prevent the pose from being created
        
        Args:
            pose_data: Dictionary containing pose information:
                - character_name: str
                - content: str (pose text)
                - pose_type: str
                - is_ooc: bool
                - timestamp: datetime
                - analysis_data: dict
        
        Returns:
            Modified pose_data dict, None (no change), or "BLOCK" (prevent pose)
        """
        return pose_data
    
    def on_command(self, command_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Hook called when a command is executed.
        
        Args:
            command_data: Dictionary containing command information:
                - command: str (command name)
                - args: List[str] (command arguments)
                - user_id: str
                - scene_id: str
        
        Returns:
            Modified command_data dict, None (no change), or "BLOCK" (prevent command)
        """
        return command_data
    
    def on_scene_enter(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Hook called when a user enters a scene.
        
        Args:
            user_data: Dictionary containing user/scene information:
                - user_id: str
                - scene_id: str
                - character_name: str
        
        Returns:
            Modified user_data dict, None (no change), or "BLOCK" (prevent entry)
        """
        return user_data
    
    def get_name(self) -> str:
        """
        Get the plugin's display name.
        
        Returns:
            Plugin name (defaults to class name)
        """
        return self.__class__.__name__
    
    def get_version(self) -> str:
        """
        Get the plugin's version.
        
        Returns:
            Plugin version string
        """
        return "1.0.0"
