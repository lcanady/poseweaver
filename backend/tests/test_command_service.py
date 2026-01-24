"""
Unit tests for the CommandService.

Tests command detection, parsing, and execution through the plugin engine.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.command_service import CommandService


class TestCommandDetection:
    """Test command detection functionality."""
    
    def test_is_command_with_slash(self):
        """Test that messages starting with / are detected as commands."""
        assert CommandService.is_command('/roll 1d20') is True
        assert CommandService.is_command('/help') is True
        assert CommandService.is_command('/kick @user') is True
    
    def test_is_command_without_slash(self):
        """Test that normal messages are not detected as commands."""
        assert CommandService.is_command('This is a normal message') is False
        assert CommandService.is_command('roll 1d20') is False
        assert CommandService.is_command('') is False
        assert CommandService.is_command(None) is False
    
    def test_is_command_with_whitespace(self):
        """Test command detection with leading/trailing whitespace."""
        assert CommandService.is_command('  /roll 1d20  ') is True
        assert CommandService.is_command('\t/help\n') is True


class TestCommandParsing:
    """Test command parsing functionality."""
    
    def test_parse_simple_command(self):
        """Test parsing a simple command without arguments."""
        result = CommandService.parse_command('/help')
        assert result == ('help', [])
    
    def test_parse_command_with_single_arg(self):
        """Test parsing a command with a single argument."""
        result = CommandService.parse_command('/roll 1d20')
        assert result == ('roll', ['1d20'])
    
    def test_parse_command_with_multiple_args(self):
        """Test parsing a command with multiple arguments."""
        result = CommandService.parse_command('/kick @user reason goes here')
        assert result == ('kick', ['@user', 'reason', 'goes', 'here'])
    
    def test_parse_command_case_insensitive(self):
        """Test that command names are lowercased."""
        result = CommandService.parse_command('/ROLL 1d20')
        assert result[0] == 'roll'
        
        result = CommandService.parse_command('/RoLl 1d20')
        assert result[0] == 'roll'
    
    def test_parse_invalid_command(self):
        """Test parsing invalid commands."""
        result = CommandService.parse_command('not a command')
        assert result is None
        
        result = CommandService.parse_command('')
        assert result is None
        
        result = CommandService.parse_command(None)
        assert result is None


class TestCommandExecution:
    """Test command execution through the plugin engine."""
    
    @patch('app.services.command_service.PluginEngine')
    def test_execute_command_success(self, mock_plugin_engine_class):
        """Test successful command execution."""
        # Setup mock
        mock_engine = MagicMock()
        mock_plugin_engine_class.return_value = mock_engine
        mock_engine.trigger_event.return_value = {
            'system_message': 'Rolled 15 (1d20)'
        }
        
        # Execute
        service = CommandService()
        result = service.execute_command(
            text='/roll 1d20',
            user_id='user123',
            scene_id='scene456',
            character_name='TestChar'
        )
        
        # Verify
        assert result['success'] is True
        assert result['command'] == 'roll'
        assert result['args'] == ['1d20']
        assert len(result['system_messages']) > 0
        assert 'Rolled 15' in result['system_messages'][0]
    
    @patch('app.services.command_service.PluginEngine')
    def test_execute_command_with_plugin_context(self, mock_plugin_engine_class):
        """Test that plugin context is loaded during execution."""
        # Setup mock
        mock_engine = MagicMock()
        mock_plugin_engine_class.return_value = mock_engine
        mock_engine.trigger_event.return_value = None
        
        # Execute
        service = CommandService()
        result = service.execute_command(
            text='/roll 1d20',
            user_id='user123',
            scene_id='scene456'
        )
        
        # Verify plugin engine was used correctly
        mock_engine.load_context.assert_called_once_with('user123', 'scene456')
        mock_engine.trigger_event.assert_called_once()
        mock_engine.clear_context.assert_called_once()
    
    @patch('app.services.command_service.PluginEngine')
    def test_execute_command_invalid_format(self, mock_plugin_engine_class):
        """Test execution of invalid command format."""
        service = CommandService()
        result = service.execute_command(
            text='not a command',
            user_id='user123',
            scene_id='scene456'
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    @patch('app.services.command_service.PluginEngine')
    def test_execute_command_no_plugin_response(self, mock_plugin_engine_class):
        """Test execution when no plugin handles the command."""
        # Setup mock
        mock_engine = MagicMock()
        mock_plugin_engine_class.return_value = mock_engine
        mock_engine.trigger_event.return_value = None
        
        # Execute
        service = CommandService()
        result = service.execute_command(
            text='/unknown command',
            user_id='user123',
            scene_id='scene456'
        )
        
        # Should still succeed but with default message
        assert result['success'] is True
        assert result['command'] == 'unknown'
        assert len(result['system_messages']) > 0
        assert 'no plugin response' in result['system_messages'][0].lower()
    
    @patch('app.services.command_service.PluginEngine')
    def test_execute_command_handles_exception(self, mock_plugin_engine_class):
        """Test that exceptions during execution are handled gracefully."""
        # Setup mock to raise exception
        mock_engine = MagicMock()
        mock_plugin_engine_class.return_value = mock_engine
        mock_engine.trigger_event.side_effect = Exception("Plugin error")
        
        # Execute
        service = CommandService()
        result = service.execute_command(
            text='/roll 1d20',
            user_id='user123',
            scene_id='scene456'
        )
        
        # Should return error result
        assert result['success'] is False
        assert 'error' in result
        assert 'Plugin error' in result['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
