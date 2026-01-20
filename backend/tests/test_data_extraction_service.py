import pytest
from unittest.mock import Mock, patch

from app.services.data_extraction_service import DataExtractionService
from app.services.openrouter_client import OpenRouterClient, OpenRouterAPIError


class TestDataExtractionService:
    """Test suite for DataExtractionService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_openrouter_client = Mock(spec=OpenRouterClient)
        self.service = DataExtractionService(self.mock_openrouter_client)
        
    def test_initialization(self):
        """Test that DataExtractionService initializes correctly."""
        assert self.service.openrouter_client is self.mock_openrouter_client
        
    def test_extract_scene_context_success(self):
        """Test successful scene context extraction with structured response."""
        # Mock successful response
        mock_response = {
            "setting": "A dimly lit tavern with wooden tables and a roaring fireplace",
            "mood": "Tense but jovial",
            "active_characters": ["Galen", "Thorne", "Barkeeper"],
            "time_of_day": "Late evening",
            "location_details": ["Wooden tables", "Fireplace", "Bar counter"],
            "emotional_tone": "Anticipation",
            "recent_events": ["A heated argument", "A toast to fallen comrades"],
            "relationship_dynamics": {"Galen-Thorne": "Cautious allies"}
        }
        self.mock_openrouter_client.extract_structured_data.return_value = mock_response
        
        # Call the method
        result = self.service.extract_scene_context(
            text="Scene description text",
            character_names=["Galen", "Thorne"]
        )
        
        # Verify the result
        assert result == mock_response
        assert result["setting"] == "A dimly lit tavern with wooden tables and a roaring fireplace"
        assert len(result["active_characters"]) == 3
        assert "Galen" in result["active_characters"]
        
        # Verify the correct schema was passed to OpenRouter client
        _, kwargs = self.mock_openrouter_client.extract_structured_data.call_args
        schema = kwargs.get("schema", {})
        assert "setting" in schema
        assert "active_characters" in schema
        assert "mood" in schema
        assert kwargs.get("temperature") == 0.3  # Lower temperature for deterministic output
        
    def test_extract_scene_context_with_poses(self):
        """Test scene context extraction with poses included."""
        # Mock response with poses
        mock_response = {
            "setting": "Castle courtyard",
            "mood": "Celebratory",
            "active_characters": ["Queen", "Knight", "Jester"],
            "time_of_day": "Midday",
            "location_details": ["Fountain", "Banners", "Stone walls"],
            "emotional_tone": "Joy",
            "recent_events": ["Knighting ceremony", "Royal announcement"],
            "relationship_dynamics": {"Queen-Knight": "Proud mentor"},
            "poses": [
                {
                    "character_name": "Queen",
                    "content": "The queen stands tall, addressing the gathered crowd with authority.",
                    "preview": "The queen stands tall, addressing..."
                },
                {
                    "character_name": "Knight",
                    "content": "The knight kneels, accepting the honor bestowed upon him.",
                    "preview": "The knight kneels, accepting..."
                }
            ]
        }
        self.mock_openrouter_client.extract_structured_data.return_value = mock_response
        
        # Call the method
        result = self.service.extract_scene_context(
            text="Scene with poses description",
            include_poses=True
        )
        
        # Verify the result includes poses
        assert "poses" in result
        assert len(result["poses"]) == 2
        assert result["poses"][0]["character_name"] == "Queen"
        
        # Verify the correct schema was passed to OpenRouter client
        _, kwargs = self.mock_openrouter_client.extract_structured_data.call_args
        schema = kwargs.get("schema", {})
        assert "poses" in schema
        
    def test_extract_scene_context_error_handling(self):
        """Test error handling during scene context extraction."""
        # Mock error during extraction
        self.mock_openrouter_client.extract_structured_data.side_effect = OpenRouterAPIError("API error")
        
        # Call the method (should not raise exception)
        result = self.service.extract_scene_context("Scene text")
        
        # Verify graceful error handling
        assert "error" in result
        assert "API error" in result["error"]
        assert "setting" in result
        assert "active_characters" in result
        assert result["active_characters"] == []
        
    def test_extract_character_details_success(self):
        """Test successful character details extraction with structured response."""
        # Mock successful response
        mock_response = {
            "name": "Eldrin Stormweaver",
            "physical_description": "Tall elf with silver hair and emerald eyes",
            "personality_traits": ["Wise", "Cautious", "Determined"],
            "background": "Ancient sage from the eastern forests",
            "goals": ["Find the lost artifacts", "Restore balance"],
            "relationships": {"Thorne": "Former apprentice", "Council": "Advisor"},
            "skills": ["Arcane magic", "Herbalism", "Diplomacy"],
            "speaking_style": "Formal and measured, with occasional ancient proverbs"
        }
        self.mock_openrouter_client.extract_structured_data.return_value = mock_response
        
        # Call the method
        result = self.service.extract_character_details("Character description text")
        
        # Verify the result
        assert result == mock_response
        assert result["name"] == "Eldrin Stormweaver"
        assert "Wise" in result["personality_traits"]
        assert "Arcane magic" in result["skills"]
        
        # Verify the correct schema was passed to OpenRouter client
        _, kwargs = self.mock_openrouter_client.extract_structured_data.call_args
        schema = kwargs.get("schema", {})
        assert "name" in schema
        assert "physical_description" in schema
        assert "personality_traits" in schema
        assert kwargs.get("temperature") == 0.3
        
    def test_extract_character_details_error_handling(self):
        """Test error handling during character details extraction."""
        # Mock error during extraction
        self.mock_openrouter_client.extract_structured_data.side_effect = Exception("Generic error")
        
        # Call the method (should not raise exception)
        result = self.service.extract_character_details("Character text")
        
        # Verify graceful error handling
        assert "error" in result
        assert "Generic error" in result["error"]
        assert "name" in result
        assert "personality_traits" in result
        assert result["personality_traits"] == []
        
    def test_extract_narrative_elements_success(self):
        """Test successful narrative elements extraction with structured response."""
        # Mock successful response
        mock_response = {
            "plot_points": ["Discovery of ancient map", "Betrayal by trusted ally"],
            "themes": ["Redemption", "Sacrifice", "Power corruption"],
            "conflicts": ["Internal struggle with dark magic", "External threat from invading forces"],
            "settings": ["Mountain fortress", "Enchanted forest", "Ancient ruins"],
            "characters": [
                {"name": "Lyra", "role": "Protagonist"}, 
                {"name": "Morden", "role": "Antagonist"}
            ],
            "timeline": ["Discovery", "Journey begins", "First confrontation", "Final battle"],
            "narrative_voice": "Third person limited",
            "emotional_arcs": ["Hope to despair", "Fear to courage"]
        }
        self.mock_openrouter_client.extract_structured_data.return_value = mock_response
        
        # Call the method
        result = self.service.extract_narrative_elements("Narrative text")
        
        # Verify the result
        assert result == mock_response
        assert "Redemption" in result["themes"]
        assert len(result["characters"]) == 2
        assert result["characters"][0]["name"] == "Lyra"
        
        # Verify the correct schema was passed to OpenRouter client
        _, kwargs = self.mock_openrouter_client.extract_structured_data.call_args
        schema = kwargs.get("schema", {})
        assert "plot_points" in schema
        assert "characters" in schema
        assert "timeline" in schema
        assert kwargs.get("temperature") == 0.4
        assert kwargs.get("max_tokens") == 2000  # Larger limit for complex narrative analysis
        
    def test_extract_narrative_elements_error_handling(self):
        """Test error handling during narrative elements extraction."""
        # Mock error during extraction
        self.mock_openrouter_client.extract_structured_data.side_effect = OpenRouterAPIError("Schema error")
        
        # Call the method (should not raise exception)
        result = self.service.extract_narrative_elements("Narrative text")
        
        # Verify graceful error handling
        assert "error" in result
        assert "Schema error" in result["error"]
        assert "plot_points" in result
        assert "themes" in result
        assert result["themes"] == []
