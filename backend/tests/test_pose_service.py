"""
Tests for pose service.
"""
import pytest
import json
from unittest.mock import Mock
from app.services.pose_service import PoseService, PoseEnhancement
from app.services.character_service import CharacterProfile
from app.services.context_service import PoseContext
from app.services.venice_client import VeniceClient, VeniceAPIError


class TestPoseService:
    """Test cases for PoseService."""
    
    @pytest.fixture
    def mock_venice_client(self):
        """Create a mock Venice client."""
        return Mock(spec=VeniceClient)
    
    @pytest.fixture
    def pose_service(self, mock_venice_client):
        """Create a pose service instance."""
        return PoseService(mock_venice_client)
    
    @pytest.fixture
    def sample_enhancement_data(self):
        """Sample enhancement data for testing."""
        return {
            'original_pose': 'Alice examines the artifact.',
            'enhanced_pose': 'Alice carefully examines the ancient artifact, her fingers tracing the intricate symbols.',
            'enhancement_notes': ['Added sensory details', 'Expanded action description'],
            'sensory_details': ['weathered surface', 'intricate symbols'],
            'character_voice_elements': ['careful examination', 'scholarly interest'],
            'narrative_techniques': ['show don\'t tell', 'sensory immersion']
        }
    
    @pytest.fixture
    def sample_pose_enhancement(self, sample_enhancement_data):
        """Sample pose enhancement instance."""
        return PoseEnhancement(**sample_enhancement_data)
    
    @pytest.fixture
    def sample_character_profile(self):
        """Sample character profile for testing."""
        return CharacterProfile(
            name="Alice",
            background="Archaeologist and scholar",
            personality=["curious", "methodical", "cautious"],
            skills=["archaeology", "ancient languages", "research"],
            goals=["uncover ancient secrets", "preserve knowledge"],
            relationships={"Bob": "research partner"},
            voice_notes="Speaks with academic precision"
        )
    
    @pytest.fixture
    def sample_pose_context(self):
        """Sample pose context for testing."""
        return PoseContext(
            actions=["examining", "studying"],
            emotions=["curiosity", "excitement"],
            environmental_details=["ancient chamber", "dim lighting"],
            character_interactions=["with Bob"],
            response_hooks=["artifact's purpose", "Bob's reaction"],
            scene_timing="present",
            urgency_level="low",
            narrative_tone="mysterious"
        )

    def test_init(self, mock_venice_client):
        """Test PoseService initialization."""
        service = PoseService(mock_venice_client)
        assert service.venice_client == mock_venice_client

    def test_enhance_pose_success(self, pose_service, mock_venice_client,
                                 sample_enhancement_data):
        """Test successful pose enhancement."""
        # Mock Venice client response - now returns plain text
        mock_venice_client.generate_completion.return_value = "Alice carefully examines the ancient artifact, running her fingers along its intricate surface."
        
        # Test the enhancement
        result = pose_service.enhance_pose(
            "Alice examines the artifact.",
            enhancement_style="balanced"
        )
        
        # Verify result
        assert isinstance(result, PoseEnhancement)
        assert result.original_pose == "Alice examines the artifact."
        assert "ancient artifact" in result.enhanced_pose
        # Metadata fields are now empty arrays in simplified response
        assert result.enhancement_notes == []
        assert result.sensory_details == []
        assert result.character_voice_elements == []
        assert result.narrative_techniques == []
        
        # Verify Venice client was called twice (enhancement + validation)
        assert mock_venice_client.generate_completion.call_count == 2

    def test_enhance_pose_with_character(self, pose_service, mock_venice_client, 
                                       sample_enhancement_data, 
                                       sample_character_profile):
        """Test pose enhancement with character profile."""
        # Mock Venice client response
        mock_venice_client.generate_completion.return_value = json.dumps(sample_enhancement_data)
        
        # Test the enhancement
        result = pose_service.enhance_pose(
            "Alice examines the artifact.",
            character=sample_character_profile,
            enhancement_style="elaborate"
        )
        
        # Verify result
        assert isinstance(result, PoseEnhancement)
        assert result.original_pose == "Alice examines the artifact."
        
        # Verify Venice client was called twice (enhancement + validation)
        assert mock_venice_client.generate_completion.call_count == 2

    def test_enhance_pose_with_context(self, pose_service, mock_venice_client, 
                                     sample_enhancement_data, 
                                     sample_pose_context):
        """Test pose enhancement with context."""
        # Mock Venice client response
        mock_venice_client.generate_completion.return_value = json.dumps(sample_enhancement_data)
        
        # Test the enhancement
        result = pose_service.enhance_pose(
            "Alice examines the artifact.",
            context=sample_pose_context,
            enhancement_style="minimal"
        )
        
        # Verify result
        assert isinstance(result, PoseEnhancement)
        assert result.original_pose == "Alice examines the artifact."
        
        # Verify Venice client was called twice (enhancement + validation)
        assert mock_venice_client.generate_completion.call_count == 2

    def test_enhance_pose_with_character_and_context(self, pose_service, mock_venice_client, 
                                                   sample_enhancement_data, 
                                                   sample_character_profile,
                                                   sample_pose_context):
        """Test pose enhancement with both character and context."""
        # Mock Venice client response
        mock_venice_client.generate_completion.return_value = json.dumps(sample_enhancement_data)
        
        # Test the enhancement
        result = pose_service.enhance_pose(
            "Alice examines the artifact.",
            character=sample_character_profile,
            context=sample_pose_context,
            enhancement_style="balanced"
        )
        
        # Verify result
        assert isinstance(result, PoseEnhancement)
        assert result.original_pose == "Alice examines the artifact."
        
        # Verify Venice client was called twice (enhancement + validation)
        assert mock_venice_client.generate_completion.call_count == 2

    def test_enhance_pose_venice_api_error(self, pose_service, mock_venice_client):
        """Test pose enhancement with Venice API error."""
        # Mock Venice client to raise error
        mock_venice_client.generate_completion.side_effect = VeniceAPIError("API error")
        
        # Test that the error is re-raised
        with pytest.raises(VeniceAPIError, match="API error"):
            pose_service.enhance_pose("Alice examines the artifact.")

    def test_enhance_pose_invalid_response(self, pose_service, mock_venice_client):
        """Test pose enhancement with invalid AI response."""
        # Mock Venice client with invalid response
        mock_venice_client.generate_completion.return_value = "invalid json"
        
        # Test that the service handles it gracefully by using the raw response
        result = pose_service.enhance_pose(
            "Alice examines the artifact.",
            enhancement_style="balanced"
        )
        
        # Verify result - should use the raw response as enhanced_pose
        assert isinstance(result, PoseEnhancement)
        assert result.original_pose == "Alice examines the artifact."
        assert result.enhanced_pose == "invalid json"
        assert result.enhancement_notes == []
        assert result.sensory_details == []
        assert result.character_voice_elements == []
        assert result.narrative_techniques == []

    def test_generate_pose_enhancement_minimal_style(self, pose_service, mock_venice_client):
        """Test _generate_pose_enhancement with minimal style."""
        # Mock Venice client response
        mock_venice_client.generate_completion.return_value = '{"original_pose": "test"}'
        
        # Test enhancement generation
        result = pose_service._generate_pose_enhancement(
            "Alice examines the artifact.",
            enhancement_style="minimal"
        )
        
        # Verify result
        assert isinstance(result, dict)
        
        # Verify the prompt includes minimal style guidance (check first call)
        first_call_args = mock_venice_client.generate_completion.call_args_list[0]
        messages = first_call_args[1]['messages']
        user_message = messages[1]['content']
        assert "minimal" in user_message.lower()

    def test_generate_pose_enhancement_elaborate_style(self, pose_service, mock_venice_client):
        """Test _generate_pose_enhancement with elaborate style."""
        # Mock Venice client response
        mock_venice_client.generate_completion.return_value = '{"original_pose": "test"}'
        
        # Test enhancement generation
        result = pose_service._generate_pose_enhancement(
            "Alice examines the artifact.",
            enhancement_style="elaborate"
        )
        
        # Verify result
        assert isinstance(result, dict)
        
        # Verify the prompt includes elaborate style guidance (check first call)
        first_call_args = mock_venice_client.generate_completion.call_args_list[0]
        messages = first_call_args[1]['messages']
        user_message = messages[1]['content']
        assert "elaborate" in user_message.lower()

    def test_get_style_guidance_minimal(self, pose_service):
        """Test _get_style_guidance for minimal style."""
        guidance = pose_service._get_style_guidance("minimal")
        
        assert isinstance(guidance, str)
        assert "subtle" in guidance.lower()
        assert "concise" in guidance.lower()

    def test_get_style_guidance_balanced(self, pose_service):
        """Test _get_style_guidance for balanced style."""
        guidance = pose_service._get_style_guidance("balanced")
        
        assert isinstance(guidance, str)
        assert "rich" in guidance.lower()
        assert "balance" in guidance.lower()

    def test_get_style_guidance_elaborate(self, pose_service):
        """Test _get_style_guidance for elaborate style."""
        guidance = pose_service._get_style_guidance("elaborate")
        
        assert isinstance(guidance, str)
        assert "immersive" in guidance.lower()
        assert "detailed" in guidance.lower()

    def test_get_style_guidance_invalid(self, pose_service):
        """Test _get_style_guidance with invalid style."""
        guidance = pose_service._get_style_guidance("invalid")
        
        assert isinstance(guidance, str)
        assert "balance" in guidance.lower()  # Should default to balanced

    def test_validate_enhancement_data_valid(self, pose_service, sample_enhancement_data):
        """Test _validate_enhancement_data with valid data."""
        # Should not raise any exception
        pose_service._validate_enhancement_data(sample_enhancement_data)

    def test_validate_enhancement_data_missing_field(self, pose_service):
        """Test _validate_enhancement_data with missing required field."""
        invalid_data = {
            'original_pose': 'Alice examines the artifact.',
            'enhanced_pose': 'Enhanced version.',
            # Missing other required fields
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            pose_service._validate_enhancement_data(invalid_data)

    def test_validate_enhancement_data_invalid_type(self, pose_service):
        """Test _validate_enhancement_data with invalid field type."""
        invalid_data = {
            'original_pose': 'Alice examines the artifact.',
            'enhanced_pose': 'Enhanced version.',
            'enhancement_notes': 'not a list',  # Should be a list
            'sensory_details': [],
            'character_voice_elements': [],
            'narrative_techniques': []
        }
        
        with pytest.raises(ValueError, match="should be a list"):
            pose_service._validate_enhancement_data(invalid_data)

    def test_generate_pose_variations_success(self, pose_service, mock_venice_client, 
                                            sample_enhancement_data):
        """Test successful pose variation generation."""
        # Mock Venice client response
        mock_venice_client.generate_completion.return_value = json.dumps(sample_enhancement_data)
        
        # Test variation generation
        result = pose_service.generate_pose_variations(
            "Alice examines the artifact.",
            count=3
        )
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(enhancement, PoseEnhancement) for enhancement in result)
        
        # Verify Venice client was called for each variation (enhancement + validation)
        assert mock_venice_client.generate_completion.call_count == 6

    def test_generate_pose_variations_with_character(self, pose_service, mock_venice_client, 
                                                   sample_enhancement_data,
                                                   sample_character_profile):
        """Test pose variation generation with character profile."""
        # Mock Venice client response
        mock_venice_client.generate_completion.return_value = json.dumps(sample_enhancement_data)
        
        # Test variation generation
        result = pose_service.generate_pose_variations(
            "Alice examines the artifact.",
            character=sample_character_profile,
            count=2
        )
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(enhancement, PoseEnhancement) for enhancement in result)

    def test_generate_pose_variations_venice_api_error(self, pose_service, mock_venice_client):
        """Test pose variation generation with Venice API error."""
        # Mock Venice client to raise error
        mock_venice_client.generate_completion.side_effect = VeniceAPIError("API error")
        
        # Test that errors are caught and error enhancements are returned
        result = pose_service.generate_pose_variations("Alice examines the artifact.", count=1)
        
        # Verify result contains error enhancement
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], PoseEnhancement)
        assert "Error generating variation" in result[0].enhanced_pose
        assert "Error: API error" in result[0].enhancement_notes[0]

    def test_analyze_pose_quality_success(self, pose_service, mock_venice_client):
        """Test successful pose quality analysis."""
        # This method doesn't use Venice client - it does local analysis
        
        # Test analysis
        result = pose_service.analyze_pose_quality(
            "Alice looks at the ancient artifact carefully."
        )
        
        # Verify result
        assert isinstance(result, dict)
        assert 'word_count' in result
        assert 'sentence_count' in result
        assert 'has_dialogue' in result
        assert 'has_action' in result
        assert 'has_emotion' in result
        assert 'complexity_score' in result
        assert result['word_count'] == 7  # "Alice looks at the ancient artifact carefully."
        assert result['has_action'] is True  # Contains "looks"

    def test_analyze_pose_quality_with_character(self, pose_service, mock_venice_client,
                                               sample_character_profile):
        """Test pose quality analysis with character profile."""
        # This method doesn't use Venice client - it does local analysis
        
        # Test analysis
        result = pose_service.analyze_pose_quality(
            "Alice examines the ancient artifact carefully.",
            character=sample_character_profile
        )
        
        # Verify result includes character consistency check
        assert isinstance(result, dict)
        assert 'character_consistency' in result
        assert isinstance(result['character_consistency'], bool)

    def test_analyze_pose_quality_with_dialogue(self, pose_service):
        """Test pose quality analysis with dialogue."""
        result = pose_service.analyze_pose_quality(
            'Alice says "This is fascinating!" as she examines the artifact.'
        )
        
        assert result['has_dialogue'] is True

    def test_analyze_pose_quality_with_emotion(self, pose_service):
        """Test pose quality analysis with emotion."""
        result = pose_service.analyze_pose_quality(
            "Alice smiles as she examines the artifact."
        )
        
        assert result['has_emotion'] is True

    def test_analyze_pose_quality_venice_api_error(self, pose_service, mock_venice_client):
        """Test analyze_pose_quality - this method doesn't use Venice client."""
        # This method doesn't use Venice client, so no error should occur
        result = pose_service.analyze_pose_quality("Alice examines the artifact.")
        
        assert isinstance(result, dict)
        assert 'word_count' in result

    def test_analyze_pose_quality_invalid_response(self, pose_service, mock_venice_client):
        """Test analyze_pose_quality - this method doesn't use Venice client."""
        # This method doesn't use Venice client, so no error should occur
        result = pose_service.analyze_pose_quality("Alice examines the artifact.")
        
        assert isinstance(result, dict)
        assert 'word_count' in result


class TestPoseEnhancement:
    """Test cases for PoseEnhancement dataclass."""
    
    def test_pose_enhancement_creation(self):
        """Test PoseEnhancement creation with all fields."""
        enhancement = PoseEnhancement(
            original_pose="Alice examines the artifact.",
            enhanced_pose="Alice carefully examines the ancient artifact.",
            enhancement_notes=["Added sensory details"],
            sensory_details=["weathered surface"],
            character_voice_elements=["careful examination"],
            narrative_techniques=["show don't tell"]
        )
        
        assert enhancement.original_pose == "Alice examines the artifact."
        assert enhancement.enhanced_pose == "Alice carefully examines the ancient artifact."
        assert enhancement.enhancement_notes == ["Added sensory details"]
        assert enhancement.sensory_details == ["weathered surface"]
        assert enhancement.character_voice_elements == ["careful examination"]
        assert enhancement.narrative_techniques == ["show don't tell"]

    def test_pose_enhancement_to_dict(self):
        """Test PoseEnhancement to_dict method."""
        enhancement = PoseEnhancement(
            original_pose="Alice examines the artifact.",
            enhanced_pose="Alice carefully examines the ancient artifact.",
            enhancement_notes=["Added sensory details"],
            sensory_details=["weathered surface"],
            character_voice_elements=["careful examination"],
            narrative_techniques=["show don't tell"]
        )
        
        result = enhancement.to_dict()
        
        assert isinstance(result, dict)
        assert result['original_pose'] == "Alice examines the artifact."
        assert result['enhanced_pose'] == "Alice carefully examines the ancient artifact."
        assert result['enhancement_notes'] == ["Added sensory details"]
        assert result['sensory_details'] == ["weathered surface"]
        assert result['character_voice_elements'] == ["careful examination"]
        assert result['narrative_techniques'] == ["show don't tell"]

    def test_pose_enhancement_equality(self):
        """Test PoseEnhancement equality comparison."""
        enhancement1 = PoseEnhancement(
            original_pose="Alice examines the artifact.",
            enhanced_pose="Alice carefully examines the ancient artifact.",
            enhancement_notes=["Added sensory details"],
            sensory_details=["weathered surface"],
            character_voice_elements=["careful examination"],
            narrative_techniques=["show don't tell"]
        )
        
        enhancement2 = PoseEnhancement(
            original_pose="Alice examines the artifact.",
            enhanced_pose="Alice carefully examines the ancient artifact.",
            enhancement_notes=["Added sensory details"],
            sensory_details=["weathered surface"],
            character_voice_elements=["careful examination"],
            narrative_techniques=["show don't tell"]
        )
        
        assert enhancement1 == enhancement2

    def test_pose_enhancement_inequality(self):
        """Test PoseEnhancement inequality comparison."""
        enhancement1 = PoseEnhancement(
            original_pose="Alice examines the artifact.",
            enhanced_pose="Alice carefully examines the ancient artifact.",
            enhancement_notes=["Added sensory details"],
            sensory_details=["weathered surface"],
            character_voice_elements=["careful examination"],
            narrative_techniques=["show don't tell"]
        )
        
        enhancement2 = PoseEnhancement(
            original_pose="Bob looks around.",
            enhanced_pose="Bob carefully looks around the chamber.",
            enhancement_notes=["Added sensory details"],
            sensory_details=["weathered surface"],
            character_voice_elements=["careful examination"],
            narrative_techniques=["show don't tell"]
        )
        
        assert enhancement1 != enhancement2 