"""
Dice Roller Plugin - Example plugin for PoseWeaver

This plugin demonstrates the plugin system by adding dice rolling capabilities
to poses. When users include /roll commands in their poses, the plugin
automatically rolls the dice and appends the results.

Example usage in a pose:
"John reaches for his sword. /roll 2d6+3"

Result:
"John reaches for his sword. 🎲 Rolled 2d6+3: 7 (dice: 3, 4)"
"""
import re
import random
from typing import Dict, Any, List, Optional
from ..base import BasePlugin


class DiceRollerPlugin(BasePlugin):
    """
    Plugin that parses and executes dice roll commands in poses.
    
    Configuration options (via install settings):
    - die_type: Default die type if not specified (e.g., "d20")
    - auto_roll: Whether to automatically roll on ambiguous syntax
    - show_details: Whether to show individual die results
    - emoji: Emoji to use for roll results (default: 🎲)
    """
    
    def get_hooks(self) -> List[str]:
        """This plugin hooks into pose creation and commands."""
        return ["ON_POSE_CREATE", "ON_COMMAND"]
    
    def on_pose_create(self, pose_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process dice roll commands in pose content.
        
        Args:
            pose_data: Pose data dictionary with 'content' field
        
        Returns:
            Modified pose_data with dice results, or original if no rolls found
        """
        content = pose_data.get('content', '')
        
        if not content:
            return pose_data
        
        # Find all /roll commands in the pose
        # Pattern: /roll NdX+Y or /roll NdX or /roll dX
        roll_pattern = r'/roll\s+(\d*d\d+(?:[+\-]\d+)?)'
        matches = re.finditer(roll_pattern, content, re.IGNORECASE)
        
        # Process each roll command
        modified_content = content
        rolls_performed = []
        
        for match in matches:
            roll_expr = match.group(1)
            roll_result = self._execute_roll(roll_expr)
            
            if roll_result:
                rolls_performed.append(roll_result)
                
                # Replace the /roll command with the result
                emoji = self.config.get('emoji', '🎲')
                show_details = self.config.get('show_details', True)
                
                if show_details and roll_result['dice']:
                    result_text = f"{emoji} Rolled {roll_expr}: **{roll_result['total']}** (dice: {', '.join(map(str, roll_result['dice']))})"
                else:
                    result_text = f"{emoji} Rolled {roll_expr}: **{roll_result['total']}**"
                
                modified_content = modified_content.replace(
                    match.group(0),
                    result_text,
                    1  # Replace only first occurrence
                )
        
        # If we performed any rolls, update the pose content
        if rolls_performed:
            pose_data['content'] = modified_content
            
            # Add roll metadata to analysis_data
            if 'analysis_data' not in pose_data:
                pose_data['analysis_data'] = {}
            
            pose_data['analysis_data']['dice_rolls'] = rolls_performed
        
        return pose_data
    
    def on_command(self, command_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle /roll command execution.
        
        Args:
            command_data: Dictionary containing command information:
                - command: str (command name)
                - args: List[str] (command arguments)
                - user_id: str
                - scene_id: str
        
        Returns:
            Dictionary with system_message key containing the roll result,
            or None if not a roll command
        """
        command = command_data.get('command', '')
        
        # Only handle 'roll' commands
        if command.lower() != 'roll':
            return None
        
        args = command_data.get('args', [])
        
        # If no args, use default die type from config
        if not args:
            default_die = self.config.get('dice_type', 'd20')
            roll_expr = default_die
        else:
            # Join args to form roll expression (e.g., "1d20" or "2d6+3")
            roll_expr = ''.join(args)
        
        # Execute the roll
        roll_result = self._execute_roll(roll_expr)
        
        if not roll_result:
            return {
                'system_message': f"❌ Invalid dice expression: {roll_expr}"
            }
        
        # Format the result message
        emoji = self.config.get('emoji', '🎲')
        show_details = self.config.get('show_details', True)
        
        if show_details and roll_result['dice']:
            message = f"{emoji} Rolled {roll_expr}: **{roll_result['total']}** (dice: {', '.join(map(str, roll_result['dice']))})"
        else:
            message = f"{emoji} Rolled {roll_expr}: **{roll_result['total']}**"
        
        return {
            'system_message': message,
            'roll_data': roll_result
        }
    
    def _execute_roll(self, roll_expr: str) -> Optional[Dict[str, Any]]:
        """
        Execute a dice roll expression.
        
        Args:
            roll_expr: Dice expression (e.g., "2d6+3", "d20", "3d8-2")
        
        Returns:
            Dictionary with roll results:
                - expression: Original expression
                - dice: List of individual die results
                - modifier: Modifier applied
                - total: Final result
        """
        try:
            # Parse the expression: NdX+Y or NdX or dX
            pattern = r'(\d*)d(\d+)([+\-]\d+)?'
            match = re.match(pattern, roll_expr, re.IGNORECASE)
            
            if not match:
                return None
            
            num_dice_str, die_size_str, modifier_str = match.groups()
            
            # Number of dice (default 1 if not specified)
            num_dice = int(num_dice_str) if num_dice_str else 1
            die_size = int(die_size_str)
            modifier = int(modifier_str) if modifier_str else 0
            
            # Validate reasonable limits
            if num_dice < 1 or num_dice > 100:
                return None
            if die_size < 2 or die_size > 1000:
                return None
            
            # Roll the dice
            dice_results = [random.randint(1, die_size) for _ in range(num_dice)]
            dice_sum = sum(dice_results)
            total = dice_sum + modifier
            
            return {
                'expression': roll_expr,
                'dice': dice_results,
                'modifier': modifier,
                'dice_sum': dice_sum,
                'total': total
            }
            
        except Exception as e:
            # If parsing or rolling fails, return None
            return None
    
    def get_name(self) -> str:
        """Plugin name."""
        return "Dice Roller"
    
    def get_version(self) -> str:
        """Plugin version."""
        return "1.0.0"
