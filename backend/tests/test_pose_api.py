"""
Tests for pose API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.services.pose_service import PoseEnhancement
from app.services.character_service import CharacterProfile
from app.services.context_service import PoseContext
from app.services.openrouter_client import OpenRouterAPIError


class TestPoseAPI:
    """Test cases for pose API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create test app instance."""
        app = create_app('testing')
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def sample_pose_enhancement(self):
        """Sample pose enhancement for testing."""
        return PoseEnhancement(
            original_pose="Alice examines the artifact.",
            enhanced_pose="Alice carefully examines the ancient artifact, her fingers tracing the intricate symbols carved into its weathered surface.",
            enhancement_notes=["Added sensory details", "Expanded action description"],
            sensory_details=["weathered surface", "intricate symbols"],
            character_voice_elements=["careful examination", "scholarly interest"],
            narrative_techniques=["show don't tell", "sensory immersion"]
        )
    
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

    # Test enhance_pose endpoint
    @patch('app.api.pose.get_pose_service')
    def test_enhance_pose_success(self, mock_get_service, client, 
                                 sample_pose_enhancement):
        """Test successful pose enhancement."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.enhance_pose.return_value = sample_pose_enhancement
        mock_get_service.return_value = mock_service
        
        # Test data
        data = {
            'original_pose': 'Alice examines the artifact.',
            'enhancement_style': 'balanced'
        }
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'enhanced_pose' in result
        
        # Verify enhanced pose content
        enhanced_pose = result['enhanced_pose']
        assert "ancient artifact" in enhanced_pose
        
        # Verify service call
        mock_service.enhance_pose.assert_called_once_with(
            data['original_pose'], None, None, data['enhancement_style']
        )

    @patch('app.api.pose.get_pose_service')
    def test_enhance_pose_with_character(self, mock_get_service, client, 
                                       sample_pose_enhancement, 
                                       sample_character_profile):
        """Test pose enhancement with character profile."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.enhance_pose.return_value = sample_pose_enhancement
        mock_get_service.return_value = mock_service
        
        # Test data with character
        data = {
            'original_pose': 'Alice examines the artifact.',
            'character': {
                'name': 'Alice',
                'background': 'Archaeologist and scholar',
                'personality': ['curious', 'methodical', 'cautious'],
                'skills': ['archaeology', 'ancient languages', 'research'],
                'goals': ['uncover ancient secrets', 'preserve knowledge'],
                'relationships': {'Bob': 'research partner'},
                'voice_notes': 'Speaks with academic precision'
            },
            'enhancement_style': 'elaborate'
        }
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        
        # Verify service call includes character
        args, kwargs = mock_service.enhance_pose.call_args
        assert args[0] == data['original_pose']
        assert args[1] is not None  # Character profile
        assert args[1].name == 'Alice'
        assert args[2] is None  # Context
        assert args[3] == 'elaborate'

    @patch('app.api.pose.get_pose_service')
    def test_enhance_pose_with_context(self, mock_get_service, client, 
                                     sample_pose_enhancement, 
                                     sample_pose_context):
        """Test pose enhancement with context."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.enhance_pose.return_value = sample_pose_enhancement
        mock_get_service.return_value = mock_service
        
        # Test data with context
        data = {
            'original_pose': 'Alice examines the artifact.',
            'context': {
                'actions': ['examining', 'studying'],
                'emotions': ['curiosity', 'excitement'],
                'environmental_details': ['ancient chamber', 'dim lighting'],
                'character_interactions': ['with Bob'],
                'response_hooks': ['artifact\'s purpose', 'Bob\'s reaction'],
                'scene_timing': 'present',
                'urgency_level': 'low',
                'narrative_tone': 'mysterious'
            },
            'enhancement_style': 'minimal'
        }
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        
        # Verify service call includes context
        args, kwargs = mock_service.enhance_pose.call_args
        assert args[0] == data['original_pose']
        assert args[1] is None  # Character
        assert args[2] is not None  # Context
        assert args[2].actions == ['examining', 'studying']
        assert args[3] == 'minimal'

    def test_enhance_pose_missing_data(self, client):
        """Test pose enhancement with missing data."""
        response = client.post('/api/pose/enhance')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'No JSON data provided' in data['error']

    def test_enhance_pose_empty_original_pose(self, client):
        """Test pose enhancement with empty original pose."""
        data = {'original_pose': ''}
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'original_pose is required and cannot be empty' in result['error']

    def test_enhance_pose_whitespace_only_pose(self, client):
        """Test pose enhancement with whitespace-only pose."""
        data = {'original_pose': '   \n\t  '}
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'original_pose is required and cannot be empty' in result['error']

    def test_enhance_pose_missing_original_pose(self, client):
        """Test pose enhancement with missing original_pose field."""
        data = {'enhancement_style': 'balanced'}
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'original_pose is required and cannot be empty' in result['error']

    @patch('app.api.pose.get_pose_service')
    def test_enhance_pose_invalid_character_data(self, mock_get_service, client):
        """Test pose enhancement with invalid character data."""
        # Mock the service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Test data with invalid character
        data = {
            'original_pose': 'Alice examines the artifact.',
            'character': {
                'name': 'Alice',
                # Missing required fields
            }
        }
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'Invalid character data' in result['error']

    @patch('app.api.pose.get_pose_service')
    def test_enhance_pose_invalid_context_data(self, mock_get_service, client):
        """Test pose enhancement with invalid context data."""
        # Mock the service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Test data with invalid context
        data = {
            'original_pose': 'Alice examines the artifact.',
            'context': {
                'actions': ['examining'],
                # Missing required fields
            }
        }
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'Invalid context data' in result['error']

    @patch('app.api.pose.get_pose_service')
    def test_enhance_pose_openrouter_api_error(self, mock_get_service, client):
        """Test pose enhancement with OpenRouter API error."""
        # Mock the service to raise OpenRouterAPIError
        mock_service = MagicMock()
        mock_service.enhance_pose.side_effect = OpenRouterAPIError("API quota exceeded")
        mock_get_service.return_value = mock_service
        
        data = {'original_pose': 'Alice examines the artifact.'}
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 503
        result = response.get_json()
        assert result['success'] is False
        assert 'AI processing failed' in result['error']
        assert 'API quota exceeded' in result['error']

    @patch('app.api.pose.get_pose_service')
    def test_enhance_pose_value_error(self, mock_get_service, client):
        """Test pose enhancement with value error."""
        # Mock the service to raise ValueError
        mock_service = MagicMock()
        mock_service.enhance_pose.side_effect = ValueError("Invalid pose format")
        mock_get_service.return_value = mock_service
        
        data = {'original_pose': 'Alice examines the artifact.'}
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'Invalid data' in result['error']
        assert 'Invalid pose format' in result['error']

    @patch('app.api.pose.get_pose_service')
    def test_enhance_pose_generic_error(self, mock_get_service, client):
        """Test pose enhancement with generic error."""
        # Mock the service to raise generic exception
        mock_service = MagicMock()
        mock_service.enhance_pose.side_effect = Exception("Unexpected error")
        mock_get_service.return_value = mock_service
        
        data = {'original_pose': 'Alice examines the artifact.'}
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 500
        result = response.get_json()
        assert result['success'] is False
        assert 'Internal server error' in result['error']
        assert 'Unexpected error' in result['error']

    # Test generate_pose_variations endpoint
    @patch('app.api.pose.get_pose_service')
    def test_generate_pose_variations_success(self, mock_get_service, client, 
                                            sample_pose_enhancement):
        """Test successful pose variation generation."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.generate_pose_variations.return_value = [sample_pose_enhancement]
        mock_get_service.return_value = mock_service
        
        # Test data
        data = {
            'original_pose': 'Alice examines the artifact.',
            'count': 3
        }
        
        response = client.post('/api/pose/variations', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'variations' in result
        assert len(result['variations']) == 1
        
        # Verify variation structure
        variation = result['variations'][0]
        assert variation['original_pose'] == "Alice examines the artifact."
        assert "ancient artifact" in variation['enhanced_pose']
        
        # Verify service call
        mock_service.generate_pose_variations.assert_called_once_with(
            data['original_pose'], None, data['count']
        )

    def test_generate_pose_variations_missing_data(self, client):
        """Test pose variation generation with missing data."""
        response = client.post('/api/pose/variations')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'No JSON data provided' in data['error']

    def test_generate_pose_variations_empty_pose(self, client):
        """Test pose variation generation with empty pose."""
        data = {'original_pose': ''}
        
        response = client.post('/api/pose/variations', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'original_pose is required and cannot be empty' in result['error']

    # Test analyze_pose_quality endpoint
    @patch('app.api.pose.get_pose_service')
    def test_analyze_pose_quality_success(self, mock_get_service, client):
        """Test successful pose quality analysis."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.analyze_pose_quality.return_value = {
            'overall_score': 85,
            'strengths': ['Good sensory details', 'Clear action'],
            'weaknesses': ['Could use more emotion'],
            'suggestions': ['Add character feelings', 'Expand environment']
        }
        mock_get_service.return_value = mock_service
        
        # Test data
        data = {
            'pose': 'Alice examines the ancient artifact carefully.'
        }
        
        response = client.post('/api/pose/analyze', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'analysis' in result
        
        # Verify analysis structure
        analysis = result['analysis']
        assert analysis['overall_score'] == 85
        assert analysis['strengths'] == ['Good sensory details', 'Clear action']
        assert analysis['weaknesses'] == ['Could use more emotion']
        assert analysis['suggestions'] == ['Add character feelings', 'Expand environment']
        
        # Verify service call
        mock_service.analyze_pose_quality.assert_called_once_with(
            data['pose'], None
        )

    def test_analyze_pose_quality_missing_data(self, client):
        """Test pose quality analysis with missing data."""
        response = client.post('/api/pose/analyze')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'No JSON data provided' in data['error']

    def test_analyze_pose_quality_empty_pose(self, client):
        """Test pose quality analysis with empty pose."""
        data = {'pose': ''}
        
        response = client.post('/api/pose/analyze', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'pose is required and cannot be empty' in result['error']

    # Test error handlers
    def test_not_found_error(self, client):
        """Test 404 error handling."""
        response = client.get('/api/pose/nonexistent')
        
        assert response.status_code == 404
        # Flask may return HTML for 404, so check if we get JSON or HTML
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = response.get_json()
            assert data['success'] is False
        # If HTML response, that's also acceptable for 404

    def test_method_not_allowed_error(self, client):
        """Test 405 error handling."""
        response = client.put('/api/pose/enhance')
        
        assert response.status_code == 405
        # Flask may return HTML for 405, so check if we get JSON or HTML
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = response.get_json()
            assert data['success'] is False
        # If HTML response, that's also acceptable for 405

    # Test service initialization
    @patch('app.api.pose.OpenRouterClient')
    @patch('app.api.pose.PoseService')
    def test_get_pose_service_initialization(self, mock_pose_service, 
                                           mock_openrouter_client):
        """Test pose service initialization."""
        from app.api.pose import get_pose_service
        
        # Reset global service
        import app.api.pose
        app.api.pose.pose_service = None
        
        # Call get_pose_service
        service = get_pose_service()
        
        # Verify initialization
        mock_openrouter_client.assert_called_once_with(api_key="test_key")
        mock_pose_service.assert_called_once_with(mock_openrouter_client.return_value)
        
        # Verify service is returned
        assert service == mock_pose_service.return_value
        
        # Verify singleton behavior
        service2 = get_pose_service()
        assert service2 == service
        
        # OpenRouter client should only be called once
        assert mock_openrouter_client.call_count == 1
        assert mock_pose_service.call_count == 1

    def test_enhance_pose_invalid_enhancement_style(self, client):
        """Test pose enhancement with invalid enhancement style."""
        data = {
            'original_pose': 'Alice examines the artifact.',
            'enhancement_style': 'invalid_style'
        }
        
        response = client.post('/api/pose/enhance', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'enhancement_style must be minimal, balanced, or elaborate' in result['error']

    def test_generate_pose_deprecated_endpoint(self, client):
        """Test deprecated generate pose endpoint."""
        data = {'original_pose': 'Alice examines the artifact.'}
        
        response = client.post('/api/pose/generate', json=data)
        
        assert response.status_code == 410
        result = response.get_json()
        assert result['success'] is False
        assert 'This endpoint has been replaced by /enhance' in result['error']

    @patch('app.api.pose.get_pose_service')
    def test_generate_pose_variations_with_character(self, mock_get_service, client, 
                                                   sample_pose_enhancement,
                                                   sample_character_profile):
        """Test pose variation generation with character profile."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.generate_pose_variations.return_value = [sample_pose_enhancement]
        mock_get_service.return_value = mock_service
        
        # Test data with character
        data = {
            'original_pose': 'Alice examines the artifact.',
            'character': {
                'name': 'Alice',
                'background': 'Archaeologist and scholar',
                'personality': ['curious', 'methodical', 'cautious'],
                'skills': ['archaeology', 'ancient languages', 'research'],
                'goals': ['uncover ancient secrets', 'preserve knowledge'],
                'relationships': {'Bob': 'research partner'},
                'voice_notes': 'Speaks with academic precision'
            },
            'count': 2
        }
        
        response = client.post('/api/pose/variations', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        
        # Verify service call includes character
        args, kwargs = mock_service.generate_pose_variations.call_args
        assert args[0] == data['original_pose']
        assert args[1] is not None  # Character profile
        assert args[1].name == 'Alice'
        assert args[2] == 2  # Count

    @patch('app.api.pose.get_pose_service')
    def test_analyze_pose_quality_with_character(self, mock_get_service, client,
                                               sample_character_profile):
        """Test pose quality analysis with character profile."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.analyze_pose_quality.return_value = {
            'overall_score': 90,
            'strengths': ['Strong character voice', 'Clear action'],
            'weaknesses': ['Could use more environment'],
            'suggestions': ['Add more sensory details']
        }
        mock_get_service.return_value = mock_service
        
        # Test data with character
        data = {
            'pose': 'Alice examines the ancient artifact carefully.',
            'character': {
                'name': 'Alice',
                'background': 'Archaeologist and scholar',
                'personality': ['curious', 'methodical', 'cautious'],
                'skills': ['archaeology', 'ancient languages', 'research'],
                'goals': ['uncover ancient secrets', 'preserve knowledge'],
                'relationships': {'Bob': 'research partner'},
                'voice_notes': 'Speaks with academic precision'
            }
        }
        
        response = client.post('/api/pose/analyze', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        
        # Verify service call includes character
        args, kwargs = mock_service.analyze_pose_quality.call_args
        assert args[0] == data['pose']
        assert args[1] is not None  # Character profile
        assert args[1].name == 'Alice' 