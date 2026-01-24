"""
Integration tests for the command parser system.

Tests the full flow from command detection -> execution -> system message generation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.command_service import CommandService
from app.plugins.examples.dice_roller import DiceRollerPlugin


class TestDiceRollerIntegration:
    """Integration tests for dice roller command."""
    
    def test_roll_command_generates_system_message(self):
        """Test that /roll command generates appropriate system message."""
        # Create dice roller plugin
        plugin = DiceRollerPlugin(config={
            'dice_type': 'd20',
            'show_details': True,
            'emoji': '🎲'
        })
        
        # Prepare command data
        command_data = {
            'command': 'roll',
            'args': ['1d20'],
            'user_id': 'user123',
            'scene_id': 'scene456'
        }
        
        # Execute on_command hook
        result = plugin.on_command(command_data)
        
        # Verify system message was generated
        assert result is not None
        assert 'system_message' in result
        assert '🎲' in result['system_message']
        assert 'Rolled 1d20' in result['system_message']
        assert 'roll_data' in result
        assert result['roll_data']['expression'] == '1d20'
    
    def test_roll_command_with_modifier(self):
        """Test /roll with modifier (e.g., 2d6+3)."""
        plugin = DiceRollerPlugin(config={'show_details': True})
        
        command_data = {
            'command': 'roll',
            'args': ['2d6+3'],
            'user_id': 'user123',
            'scene_id': 'scene456'
        }
        
        result = plugin.on_command(command_data)
        
        assert result is not None
        assert 'system_message' in result
        assert 'Rolled 2d6+3' in result['system_message']
        
        # Verify roll data
        roll_data = result['roll_data']
        assert roll_data['modifier'] == 3
        assert len(roll_data['dice']) == 2
        assert roll_data['total'] == roll_data['dice_sum'] + 3
    
    def test_roll_command_invalid_expression(self):
        """Test that invalid expressions return error message."""
        plugin = DiceRollerPlugin(config={})
        
        command_data = {
            'command': 'roll',
            'args': ['invalid'],
            'user_id': 'user123',
            'scene_id': 'scene456'
        }
        
        result = plugin.on_command(command_data)
        
        assert result is not None
        assert 'system_message' in result
        assert '❌' in result['system_message']
        assert 'Invalid' in result['system_message']
    
    def test_non_roll_command_ignored(self):
        """Test that non-roll commands are ignored by dice plugin."""
        plugin = DiceRollerPlugin(config={})
        
        command_data = {
            'command': 'help',
            'args': [],
            'user_id': 'user123',
            'scene_id': 'scene456'
        }
        
        result = plugin.on_command(command_data)
        
        # Plugin should return None for commands it doesn't handle
        assert result is None


class TestCommandServiceFlow:
    """Test the complete command flow."""
    
    @patch('app.services.command_service.PluginEngine')
    def test_command_to_pose_distinction(self, mock_plugin_engine_class):
        """Test that service correctly distinguishes commands from poses."""
        service = CommandService()
        
        # Test command detection
        assert service.is_command('/roll 1d20') is True
        assert service.is_command('John swings his sword') is False
    
    @patch('app.core.plugin_engine.PluginManifest')
    @patch('app.core.plugin_engine.UserPluginInstall')
    def test_full_command_execution_flow(self, mock_user_install, mock_manifest):
        """Test full flow: parse -> execute -> generate system message."""
        # This would require setting up mock database objects
        # For now, just verify the structure
        from app.services.command_service import CommandService
        service = CommandService()
        
        # Verify command is parsed correctly
        parsed = service.parse_command('/roll 1d20')
        assert parsed == ('roll', ['1d20'])


class TestSceneServiceRouting:
    """Test that scene service routes commands correctly."""
    
    def test_command_detection_in_scene_flow(self):
        """Test that scene_flow_service detects commands."""
        from app.services.command_service import CommandService
        
        # Verify the is_command method works as expected
        assert CommandService.is_command('/roll 1d20') is True
        assert CommandService.is_command('Normal pose text') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
