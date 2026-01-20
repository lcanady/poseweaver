"""
Tests for character brain dump processing service.
"""
import pytest
from unittest.mock import Mock
from app.services.character_service import CharacterService, CharacterProfile
from app.services.openrouter_client import OpenRouterAPIError


class TestCharacterProfile:
    """Test the CharacterProfile data class."""
    
    def test_character_profile_initialization(self):
        """Test CharacterProfile can be initialized with all fields."""
        profile = CharacterProfile(
            name="Aria Shadowmere",
            background="A mysterious elven rogue",
            personality=["cunning", "loyal", "secretive"],
            skills=["stealth", "lockpicking", "archery"],
            goals=["Find her missing brother"],
            relationships={"Marcus": "trusted ally"},
            voice_notes="Speaks in clipped sentences"
        )
        
        assert profile.name == "Aria Shadowmere"
        assert "mysterious elven rogue" in profile.background
        assert "cunning" in profile.personality
        assert "stealth" in profile.skills
        assert "Find her missing brother" in profile.goals
        assert profile.relationships["Marcus"] == "trusted ally"
        assert "clipped sentences" in profile.voice_notes
    
    def test_character_profile_to_dict(self):
        """Test CharacterProfile can be converted to dictionary."""
        profile = CharacterProfile(
            name="Test Character",
            background="Test background",
            personality=["trait1"],
            skills=["skill1"],
            goals=["goal1"],
            relationships={"friend": "ally"},
            voice_notes="Test voice"
        )
        
        result = profile.to_dict()
        
        assert isinstance(result, dict)
        assert result["name"] == "Test Character"
        assert result["background"] == "Test background"
        assert result["personality"] == ["trait1"]
        assert result["skills"] == ["skill1"]
        assert result["goals"] == ["goal1"]
        assert result["relationships"] == {"friend": "ally"}
        assert result["voice_notes"] == "Test voice"


class TestCharacterService:
    """Test the CharacterService class."""
    
    @pytest.fixture
    def mock_openrouter_client(self):
        """Create a mock OpenRouter client."""
        mock_client = Mock()
        return mock_client
    
    @pytest.fixture
    def character_service(self, mock_openrouter_client):
        """Create a CharacterService instance with mocked dependencies."""
        return CharacterService(openrouter_client=mock_openrouter_client)
    
    def test_character_service_initialization(self, mock_openrouter_client):
        """Test CharacterService can be initialized."""
        service = CharacterService(openrouter_client=mock_openrouter_client)
        assert service.openrouter_client == mock_openrouter_client
    
    def test_process_brain_dump_success(self, character_service, 
                                       mock_openrouter_client):
        """Test successful brain dump processing."""
        # Mock AI response
        mock_response = {
            "name": "Lyra Nightwhisper",
            "background": "A half-elf bard from Waterdeep",
            "personality": ["charismatic", "street-smart"],
            "skills": ["performance", "persuasion"],
            "goals": ["Become a renowned performer"],
            "relationships": {"Old Tom": "mentor figure"},
            "voice_notes": "Uses colorful street slang"
        }
        
        mock_openrouter_client.generate_completion.return_value = mock_response
        
        brain_dump = "Lyra is a half-elf bard from Waterdeep"
        
        result = character_service.process_brain_dump(brain_dump)
        
        assert isinstance(result, CharacterProfile)
        assert result.name == "Lyra Nightwhisper"
        assert "half-elf bard" in result.background
        assert "charismatic" in result.personality
        assert "performance" in result.skills
        assert "Become a renowned performer" in result.goals
        assert result.relationships["Old Tom"] == "mentor figure"
        assert "street slang" in result.voice_notes
        
        # Verify the AI was called
        mock_openrouter_client.generate_completion.assert_called_once()
    
    def test_process_brain_dump_with_existing_character(self, character_service,
                                                       mock_openrouter_client):
        """Test brain dump processing with existing character."""
        existing_profile = CharacterProfile(
            name="Lyra Nightwhisper",
            background="A half-elf bard",
            personality=["charismatic"],
            skills=["performance"],
            goals=["Become famous"],
            relationships={},
            voice_notes="Street slang"
        )
        
        mock_response = {
            "name": "Lyra Nightwhisper",
            "background": "A half-elf bard from Waterdeep",
            "personality": ["charismatic", "street-smart"],
            "skills": ["performance", "persuasion"],
            "goals": ["Become famous", "Help street children"],
            "relationships": {"Old Tom": "mentor figure"},
            "voice_notes": "Uses colorful street slang"
        }
        
        mock_openrouter_client.generate_completion.return_value = mock_response
        
        brain_dump = "Lyra learned from Old Tom and wants to help kids."
        
        result = character_service.process_brain_dump(
            brain_dump, existing_character=existing_profile
        )
        
        assert isinstance(result, CharacterProfile)
        assert result.name == "Lyra Nightwhisper"
        assert "Help street children" in result.goals
        assert result.relationships["Old Tom"] == "mentor figure"
    
    def test_process_brain_dump_api_error(self, character_service, 
                                         mock_openrouter_client):
        """Test handling of OpenRouter API errors."""
        mock_openrouter_client.generate_completion.side_effect = OpenRouterAPIError(
            "API Error", 500
        )
        
        brain_dump = "Test character description"
        
        with pytest.raises(OpenRouterAPIError):
            character_service.process_brain_dump(brain_dump)
    
    def test_process_brain_dump_invalid_response(self, character_service,
                                                mock_openrouter_client):
        """Test handling of invalid AI response format."""
        # Mock invalid response (missing required fields)
        mock_openrouter_client.generate_completion.return_value = {
            "invalid": "response"
        }
        
        brain_dump = "Test character description"
        
        with pytest.raises(ValueError, match="Invalid character data"):
            character_service.process_brain_dump(brain_dump)
    
    def test_validate_character_data_valid(self, character_service):
        """Test validation of valid character data."""
        valid_data = {
            "name": "Test Character",
            "background": "Test background",
            "personality": ["trait1", "trait2"],
            "skills": ["skill1", "skill2"],
            "goals": ["goal1"],
            "relationships": {"friend": "ally"},
            "voice_notes": "Test voice"
        }
        
        # Should not raise an exception
        character_service._validate_character_data(valid_data)
    
    def test_validate_character_data_missing_fields(self, character_service):
        """Test validation fails for missing required fields."""
        invalid_data = {
            "name": "Test Character"
            # Missing other required fields
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            character_service._validate_character_data(invalid_data)
    
    def test_validate_character_data_wrong_types(self, character_service):
        """Test validation fails for wrong data types."""
        invalid_data = {
            "name": "Test Character",
            "background": "Test background",
            "personality": "should be list",  # Wrong type
            "skills": ["skill1"],
            "goals": ["goal1"],
            "relationships": {"friend": "ally"},
            "voice_notes": "Test voice"
        }
        
        with pytest.raises(ValueError, match="should be a list"):
            character_service._validate_character_data(invalid_data)
    
    def test_extract_character_info_success(self, character_service,
                                           mock_openrouter_client):
        """Test successful character information extraction."""
        mock_response = {
            "name": "Test Character",
            "background": "Test background",
            "personality": ["trait1"],
            "skills": ["skill1"],
            "goals": ["goal1"],
            "relationships": {"friend": "ally"},
            "voice_notes": "Test voice"
        }
        
        mock_openrouter_client.generate_completion.return_value = mock_response
        
        brain_dump = "Test character description"
        result = character_service._extract_character_info(brain_dump)
        
        assert result == mock_response
        mock_openrouter_client.generate_completion.assert_called_once()
    
    def test_merge_character_data(self, character_service):
        """Test merging existing character data with new information."""
        existing_data = {
            "name": "Test Character",
            "background": "Original background",
            "personality": ["trait1"],
            "skills": ["skill1"],
            "goals": ["goal1"],
            "relationships": {"friend1": "ally"},
            "voice_notes": "Original voice"
        }
        
        new_data = {
            "name": "Test Character",
            "background": "Updated background",
            "personality": ["trait1", "trait2"],
            "skills": ["skill1", "skill2"],
            "goals": ["goal1", "goal2"],
            "relationships": {"friend1": "ally", "friend2": "enemy"},
            "voice_notes": "Updated voice"
        }
        
        result = character_service._merge_character_data(existing_data, 
                                                        new_data)
        
        assert result["background"] == "Updated background"
        assert "trait2" in result["personality"]
        assert "skill2" in result["skills"]
        assert "goal2" in result["goals"]
        assert result["relationships"]["friend2"] == "enemy"
        assert result["voice_notes"] == "Updated voice" 