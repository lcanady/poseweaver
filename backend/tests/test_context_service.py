"""
Tests for context service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.context_service import ContextService, PoseContext
from app.services.openrouter_client import OpenRouterClient, OpenRouterAPIError
import json


class TestContextService:
    """Test cases for ContextService."""
    
    @pytest.fixture
    def mock_openrouter_client(self):
        """Create a mock OpenRouter client."""
        return Mock(spec=OpenRouterClient)
    
    @pytest.fixture
    def context_service(self, mock_openrouter_client):
        """Create a context service instance."""
        return ContextService(mock_openrouter_client)
    
    @pytest.fixture
    def sample_context_data(self):
        """Sample context data for testing."""
        return {
            'actions': ['examining', 'studying'],
            'emotions': ['curiosity', 'excitement'],
            'environmental_details': ['ancient chamber', 'dim lighting'],
            'character_interactions': ['with Bob'],
            'response_hooks': ['artifact\'s purpose', 'Bob\'s reaction'],
            'scene_timing': 'present',
            'urgency_level': 'low',
            'narrative_tone': 'mysterious'
        }
    
    @pytest.fixture
    def sample_pose_context(self, sample_context_data):
        """Sample pose context instance."""
        return PoseContext(**sample_context_data)

    def test_init(self, mock_openrouter_client):
        """Test ContextService initialization."""
        service = ContextService(mock_openrouter_client)
        assert service.openrouter_client == mock_openrouter_client

    def test_analyze_pose_context_success(self, context_service, mock_openrouter_client, 
                                        sample_context_data):
        """Test successful pose context analysis."""
        # Mock OpenRouter client response - returns JSON string
        mock_openrouter_client.generate_completion.return_value = json.dumps(sample_context_data)
        
        # Test the analysis
        result = context_service.analyze_pose_context(
            "Alice examines the ancient artifact carefully.",
            "Bob"
        )
        
        # Verify result
        assert isinstance(result, PoseContext)
        assert result.actions == ['examining', 'studying']
        assert result.emotions == ['curiosity', 'excitement']
        assert result.environmental_details == ['ancient chamber', 'dim lighting']
        assert result.character_interactions == ['with Bob']
        assert result.response_hooks == ['artifact\'s purpose', 'Bob\'s reaction']
        assert result.scene_timing == 'present'
        assert result.urgency_level == 'low'
        assert result.narrative_tone == 'mysterious'
        
        # Verify OpenRouter client was called
        mock_openrouter_client.generate_completion.assert_called_once()

    def test_analyze_pose_context_without_character(self, context_service, 
                                                  mock_openrouter_client, 
                                                  sample_context_data):
        """Test pose context analysis without character name."""
        # Mock OpenRouter client response - returns JSON string
        mock_openrouter_client.generate_completion.return_value = json.dumps(sample_context_data)
        
        # Test the analysis
        result = context_service.analyze_pose_context(
            "Alice examines the ancient artifact carefully."
        )
        
        # Verify result
        assert isinstance(result, PoseContext)
        assert result.actions == ['examining', 'studying']
        
        # Verify OpenRouter client was called
        mock_openrouter_client.generate_completion.assert_called_once()

    def test_analyze_pose_context_openrouter_api_error(self, context_service, 
                                                 mock_openrouter_client):
        """Test pose context analysis with OpenRouter API error."""
        # Mock OpenRouter client to raise error
        mock_openrouter_client.generate_completion.side_effect = OpenRouterAPIError("API error")
        
        # Test that the error is re-raised
        with pytest.raises(OpenRouterAPIError, match="API error"):
            context_service.analyze_pose_context("Alice examines the artifact.")

    def test_analyze_pose_context_invalid_response(self, context_service, 
                                                 mock_openrouter_client):
        """Test pose context analysis with invalid AI response."""
        # Mock OpenRouter client with invalid response
        mock_openrouter_client.generate_completion.return_value = {
            'choices': [{'message': {'content': 'invalid json'}}]
        }
        
        # Test that ValueError is raised
        with pytest.raises(ValueError, match="Invalid context data"):
            context_service.analyze_pose_context("Alice examines the artifact.")

    def test_extract_pose_context_with_character(self, context_service, 
                                               mock_openrouter_client):
        """Test _extract_pose_context with character name."""
        # Mock OpenRouter client response - returns JSON string
        mock_openrouter_client.generate_completion.return_value = '{"actions": ["test"]}'
        
        # Test extraction
        result = context_service._extract_pose_context(
            "Alice examines the artifact.", "Bob"
        )
        
        # Verify result
        assert isinstance(result, dict)
        assert result == {"actions": ["test"]}
        
        # Verify the prompt includes character name and pose text
        call_args = mock_openrouter_client.generate_completion.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']
        assert "Bob" in user_message
        assert "Alice examines the artifact." in user_message

    def test_extract_pose_context_without_character(self, context_service, 
                                                  mock_openrouter_client):
        """Test _extract_pose_context without character name."""
        # Mock OpenRouter client response - returns JSON string
        mock_openrouter_client.generate_completion.return_value = '{"actions": ["test"]}'
        
        # Test extraction
        result = context_service._extract_pose_context(
            "Alice examines the artifact."
        )
        
        # Verify result
        assert isinstance(result, dict)
        assert result == {"actions": ["test"]}
        
        # Verify the prompt includes pose text
        call_args = mock_openrouter_client.generate_completion.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']
        assert "Alice examines the artifact." in user_message

    def test_validate_context_data_valid(self, context_service, sample_context_data):
        """Test _validate_context_data with valid data."""
        # Should not raise any exception
        context_service._validate_context_data(sample_context_data)

    def test_validate_context_data_missing_field(self, context_service):
        """Test _validate_context_data with missing required field."""
        invalid_data = {
            'actions': ['examining'],
            'emotions': ['curiosity'],
            # Missing other required fields
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            context_service._validate_context_data(invalid_data)

    def test_validate_context_data_invalid_type(self, context_service):
        """Test _validate_context_data with invalid field type."""
        invalid_data = {
            'actions': 'not a list',  # Should be a list
            'emotions': ['curiosity'],
            'environmental_details': ['chamber'],
            'character_interactions': ['with Bob'],
            'response_hooks': ['hook'],
            'scene_timing': 'present',
            'urgency_level': 'low',
            'narrative_tone': 'mysterious'
        }
        
        with pytest.raises(ValueError, match="Field 'actions' should be a list"):
            context_service._validate_context_data(invalid_data)

    def test_get_response_suggestions_with_character(self, context_service, 
                                                   mock_openrouter_client, 
                                                   sample_pose_context):
        """Test get_response_suggestions with character name."""
        # This method doesn't use OpenRouter client - it generates suggestions from context
        
        # Test suggestions
        result = context_service.get_response_suggestions(
            sample_pose_context, "Bob"
        )
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) == 5  # Limited to 5 suggestions
        
        # Check suggestion texts
        suggestion_texts = [s["text"] for s in result]
        assert "React to: examining, studying" in suggestion_texts
        assert "Respond to emotional tone: curiosity" in suggestion_texts
        assert "Address: artifact's purpose" in suggestion_texts
        assert "Address: Bob's reaction" in suggestion_texts
        assert "Take time for thoughtful response" in suggestion_texts
        
        # Check suggestion types
        assert all("type" in s for s in result)
        assert all("text" in s for s in result)

    def test_get_response_suggestions_without_character(self, context_service, 
                                                      mock_openrouter_client, 
                                                      sample_pose_context):
        """Test get_response_suggestions without character name."""
        # This method doesn't use OpenRouter client - it generates suggestions from context
        
        # Test suggestions
        result = context_service.get_response_suggestions(sample_pose_context)
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) == 5  # Limited to 5 suggestions
        
        # Check suggestion texts
        suggestion_texts = [s["text"] for s in result]
        assert "React to: examining, studying" in suggestion_texts
        assert "Respond to emotional tone: curiosity" in suggestion_texts
        assert "Address: artifact's purpose" in suggestion_texts
        assert "Address: Bob's reaction" in suggestion_texts
        assert "Take time for thoughtful response" in suggestion_texts
        
        # Check suggestion types
        assert all("type" in s for s in result)
        assert all("text" in s for s in result)

    def test_get_response_suggestions_high_urgency(self, context_service):
        """Test get_response_suggestions with high urgency context."""
        high_urgency_context = PoseContext(
            actions=['attacking', 'charging'],
            emotions=['anger', 'rage'],
            environmental_details=['battlefield'],
            character_interactions=['targeting Bob'],
            response_hooks=['defend yourself'],
            scene_timing='immediate',
            urgency_level='high',
            narrative_tone='intense'
        )
        
        result = context_service.get_response_suggestions(high_urgency_context)
        
        assert isinstance(result, list)
        suggestion_texts = [s["text"] for s in result]
        assert "Consider immediate action or response" in suggestion_texts

    def test_get_response_suggestions_empty_context(self, context_service):
        """Test get_response_suggestions with empty context."""
        empty_context = PoseContext(
            actions=[],
            emotions=[],
            environmental_details=[],
            character_interactions=[],
            response_hooks=[],
            scene_timing='present',
            urgency_level='medium',
            narrative_tone='neutral'
        )
        
        result = context_service.get_response_suggestions(empty_context)
        
        assert isinstance(result, list)
        # Should have no suggestions since no actions, emotions, or hooks
        assert len(result) == 0

    def test_get_response_suggestions_openrouter_api_error(self, context_service, 
                                                     mock_openrouter_client, 
                                                     sample_pose_context):
        """Test get_response_suggestions - this method doesn't use OpenRouter client."""
        # This method doesn't use OpenRouter client, so no error should occur
        result = context_service.get_response_suggestions(sample_pose_context, "Bob")
        
        assert isinstance(result, list)
        assert len(result) == 5

    def test_get_response_suggestions_invalid_response(self, context_service, 
                                                     mock_openrouter_client, 
                                                     sample_pose_context):
        """Test get_response_suggestions - this method doesn't use OpenRouter client."""
        # This method doesn't use OpenRouter client, so no error should occur
        result = context_service.get_response_suggestions(sample_pose_context, "Bob")
        
        assert isinstance(result, list)
        assert len(result) == 5

    def test_analyze_multiple_poses_success(self, context_service, 
                                          mock_openrouter_client, 
                                          sample_context_data):
        """Test successful multiple pose analysis."""
        # Mock OpenRouter client response - returns JSON string
        mock_openrouter_client.generate_completion.return_value = json.dumps(sample_context_data)
        
        # Test multiple pose analysis
        poses = [
            "Alice examines the artifact.",
            "Bob steps closer to look."
        ]
        
        result = context_service.analyze_multiple_poses(poses, "Charlie")
        
        # Verify result
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "pose_0" in result
        assert "pose_1" in result
        assert isinstance(result["pose_0"], PoseContext)
        assert isinstance(result["pose_1"], PoseContext)
        
        # Verify OpenRouter client was called for each pose
        assert mock_openrouter_client.generate_completion.call_count == 2

    def test_analyze_multiple_poses_without_character(self, context_service, 
                                                    mock_openrouter_client, 
                                                    sample_context_data):
        """Test multiple pose analysis without character name."""
        # Mock OpenRouter client response - returns JSON string
        mock_openrouter_client.generate_completion.return_value = json.dumps(sample_context_data)
        
        # Test multiple pose analysis
        poses = ["Alice examines the artifact."]
        
        result = context_service.analyze_multiple_poses(poses)
        
        # Verify result
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "pose_0" in result
        assert isinstance(result["pose_0"], PoseContext)

    def test_analyze_multiple_poses_empty_list(self, context_service):
        """Test multiple pose analysis with empty list."""
        result = context_service.analyze_multiple_poses([])
        
        # Verify result
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_analyze_multiple_poses_openrouter_api_error(self, context_service, 
                                                   mock_openrouter_client):
        """Test multiple pose analysis with OpenRouter API error."""
        # Mock OpenRouter client to raise error
        mock_openrouter_client.generate_completion.side_effect = OpenRouterAPIError("API error")
        
        # Test that errors are caught and returned in results
        result = context_service.analyze_multiple_poses(["Alice examines the artifact."])
        
        # Verify result
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "pose_0" in result
        assert "error" in result["pose_0"]
        assert "API error" in result["pose_0"]["error"]

    def test_analyze_multiple_poses_partial_failure(self, context_service, 
                                                   mock_openrouter_client, 
                                                   sample_context_data):
        """Test multiple pose analysis with partial failure."""
        # Mock OpenRouter client to succeed first, then fail
        mock_openrouter_client.generate_completion.side_effect = [
            json.dumps(sample_context_data),
            OpenRouterAPIError("API error")
        ]
        
        poses = [
            "Alice examines the artifact.",
            "Bob steps closer to look."
        ]
        
        # Test that partial failure is handled
        result = context_service.analyze_multiple_poses(poses)
        
        # Verify result
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "pose_0" in result
        assert "pose_1" in result
        assert isinstance(result["pose_0"], PoseContext)
        assert "error" in result["pose_1"]
        assert "API error" in result["pose_1"]["error"]


class TestPoseContext:
    """Test cases for PoseContext dataclass."""
    
    def test_pose_context_creation(self):
        """Test PoseContext creation with all fields."""
        context = PoseContext(
            actions=['examining', 'studying'],
            emotions=['curiosity', 'excitement'],
            environmental_details=['ancient chamber', 'dim lighting'],
            character_interactions=['with Bob'],
            response_hooks=['artifact\'s purpose', 'Bob\'s reaction'],
            scene_timing='present',
            urgency_level='low',
            narrative_tone='mysterious'
        )
        
        assert context.actions == ['examining', 'studying']
        assert context.emotions == ['curiosity', 'excitement']
        assert context.environmental_details == ['ancient chamber', 'dim lighting']
        assert context.character_interactions == ['with Bob']
        assert context.response_hooks == ['artifact\'s purpose', 'Bob\'s reaction']
        assert context.scene_timing == 'present'
        assert context.urgency_level == 'low'
        assert context.narrative_tone == 'mysterious'

    def test_pose_context_to_dict(self):
        """Test PoseContext to_dict method."""
        context = PoseContext(
            actions=['examining'],
            emotions=['curiosity'],
            environmental_details=['chamber'],
            character_interactions=['with Bob'],
            response_hooks=['hook'],
            scene_timing='present',
            urgency_level='low',
            narrative_tone='mysterious'
        )
        
        result = context.to_dict()
        
        assert isinstance(result, dict)
        assert result['actions'] == ['examining']
        assert result['emotions'] == ['curiosity']
        assert result['environmental_details'] == ['chamber']
        assert result['character_interactions'] == ['with Bob']
        assert result['response_hooks'] == ['hook']
        assert result['scene_timing'] == 'present'
        assert result['urgency_level'] == 'low'
        assert result['narrative_tone'] == 'mysterious'

    def test_pose_context_equality(self):
        """Test PoseContext equality comparison."""
        context1 = PoseContext(
            actions=['examining'],
            emotions=['curiosity'],
            environmental_details=['chamber'],
            character_interactions=['with Bob'],
            response_hooks=['hook'],
            scene_timing='present',
            urgency_level='low',
            narrative_tone='mysterious'
        )
        
        context2 = PoseContext(
            actions=['examining'],
            emotions=['curiosity'],
            environmental_details=['chamber'],
            character_interactions=['with Bob'],
            response_hooks=['hook'],
            scene_timing='present',
            urgency_level='low',
            narrative_tone='mysterious'
        )
        
        assert context1 == context2

    def test_pose_context_inequality(self):
        """Test PoseContext inequality comparison."""
        context1 = PoseContext(
            actions=['examining'],
            emotions=['curiosity'],
            environmental_details=['chamber'],
            character_interactions=['with Bob'],
            response_hooks=['hook'],
            scene_timing='present',
            urgency_level='low',
            narrative_tone='mysterious'
        )
        
        context2 = PoseContext(
            actions=['different'],
            emotions=['curiosity'],
            environmental_details=['chamber'],
            character_interactions=['with Bob'],
            response_hooks=['hook'],
            scene_timing='present',
            urgency_level='low',
            narrative_tone='mysterious'
        )
        
        assert context1 != context2 