"""
Tests for context API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.services.context_service import PoseContext
from app.services.venice_client import VeniceAPIError


class TestContextAPI:
    """Test cases for context API endpoints."""
    
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
    def sample_pose_context(self):
        """Sample pose context for testing."""
        return PoseContext(
            actions=["examines the artifact", "steps closer"],
            emotions=["curiosity", "caution"],
            environmental_details=["ancient ruins", "dim lighting"],
            character_interactions=["looking at Bob"],
            response_hooks=["artifact's purpose", "Bob's reaction"],
            scene_timing="present",
            urgency_level="low",
            narrative_tone="mysterious"
        )
    
    @pytest.fixture
    def sample_response_suggestions(self):
        """Sample response suggestions for testing."""
        return [
            "You could have Bob react to the artifact examination",
            "Consider describing the artifact's mysterious properties",
            "Perhaps show Bob's own curiosity or concern"
        ]

    # Test analyze_pose_context endpoint
    @patch('app.api.context.get_context_service')
    def test_analyze_pose_context_success(self, mock_get_service, client, 
                                        sample_pose_context, 
                                        sample_response_suggestions):
        """Test successful pose context analysis."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.analyze_pose_context.return_value = sample_pose_context
        mock_service.get_response_suggestions.return_value = sample_response_suggestions
        mock_get_service.return_value = mock_service
        
        # Test data
        data = {
            'pose_text': 'Alice examines the ancient artifact carefully, her eyes narrowing as she studies the strange symbols.',
            'character_name': 'Bob'
        }
        
        response = client.post('/api/context/analyze', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'context' in result
        assert 'suggestions' in result
        
        # Verify context structure
        context = result['context']
        assert context['actions'] == ["examines the artifact", "steps closer"]
        assert context['emotions'] == ["curiosity", "caution"]
        assert context['environmental_details'] == ["ancient ruins", "dim lighting"]
        assert context['character_interactions'] == ["looking at Bob"]
        assert context['response_hooks'] == ["artifact's purpose", "Bob's reaction"]
        assert context['scene_timing'] == "present"
        assert context['urgency_level'] == "low"
        assert context['narrative_tone'] == "mysterious"
        
        # Verify suggestions
        assert result['suggestions'] == sample_response_suggestions
        
        # Verify service calls
        mock_service.analyze_pose_context.assert_called_once_with(data['pose_text'], data['character_name'])
        mock_service.get_response_suggestions.assert_called_once_with(
            sample_pose_context, data['character_name']
        )

    @patch('app.api.context.get_context_service')
    def test_analyze_pose_context_without_character_name(self, mock_get_service, client, 
                                                       sample_pose_context):
        """Test pose context analysis without character name."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.analyze_pose_context.return_value = sample_pose_context
        mock_service.get_response_suggestions.return_value = []
        mock_get_service.return_value = mock_service
        
        # Test data without character_name
        data = {
            'pose_text': 'Alice examines the ancient artifact carefully.'
        }
        
        response = client.post('/api/context/analyze', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        
        # Verify service calls
        mock_service.analyze_pose_context.assert_called_once_with(data['pose_text'], None)
        mock_service.get_response_suggestions.assert_called_once_with(
            sample_pose_context, None
        )

    def test_analyze_pose_context_missing_data(self, client):
        """Test pose context analysis with missing data."""
        response = client.post('/api/context/analyze')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'No JSON data provided' in data['error']

    def test_analyze_pose_context_empty_pose_text(self, client):
        """Test pose context analysis with empty pose text."""
        data = {'pose_text': ''}
        
        response = client.post('/api/context/analyze', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'pose_text is required and cannot be empty' in result['error']

    def test_analyze_pose_context_whitespace_only_pose_text(self, client):
        """Test pose context analysis with whitespace-only pose text."""
        data = {'pose_text': '   \n\t  '}
        
        response = client.post('/api/context/analyze', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'pose_text is required and cannot be empty' in result['error']

    def test_analyze_pose_context_missing_pose_text(self, client):
        """Test pose context analysis with missing pose_text field."""
        data = {'character_name': 'Bob'}
        
        response = client.post('/api/context/analyze', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'pose_text is required and cannot be empty' in result['error']

    @patch('app.api.context.get_context_service')
    def test_analyze_pose_context_venice_api_error(self, mock_get_service, client):
        """Test pose context analysis with Venice API error."""
        # Mock the service to raise VeniceAPIError
        mock_service = MagicMock()
        mock_service.analyze_pose_context.side_effect = VeniceAPIError("API quota exceeded")
        mock_get_service.return_value = mock_service
        
        data = {'pose_text': 'Alice examines the artifact.'}
        
        response = client.post('/api/context/analyze', json=data)
        
        assert response.status_code == 503
        result = response.get_json()
        assert result['success'] is False
        assert 'AI processing failed' in result['error']
        assert 'API quota exceeded' in result['error']

    @patch('app.api.context.get_context_service')
    def test_analyze_pose_context_value_error(self, mock_get_service, client):
        """Test pose context analysis with value error."""
        # Mock the service to raise ValueError
        mock_service = MagicMock()
        mock_service.analyze_pose_context.side_effect = ValueError("Invalid pose format")
        mock_get_service.return_value = mock_service
        
        data = {'pose_text': 'Alice examines the artifact.'}
        
        response = client.post('/api/context/analyze', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'Invalid data' in result['error']
        assert 'Invalid pose format' in result['error']

    @patch('app.api.context.get_context_service')
    def test_analyze_pose_context_generic_error(self, mock_get_service, client):
        """Test pose context analysis with generic error."""
        # Mock the service to raise generic exception
        mock_service = MagicMock()
        mock_service.analyze_pose_context.side_effect = Exception("Unexpected error")
        mock_get_service.return_value = mock_service
        
        data = {'pose_text': 'Alice examines the artifact.'}
        
        response = client.post('/api/context/analyze', json=data)
        
        assert response.status_code == 500
        result = response.get_json()
        assert result['success'] is False
        assert 'Internal server error' in result['error']
        assert 'Unexpected error' in result['error']

    # Test analyze_multiple_poses endpoint
    @patch('app.api.context.get_context_service')
    def test_analyze_multiple_poses_success(self, mock_get_service, client, 
                                          sample_pose_context):
        """Test successful multiple pose analysis."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.analyze_multiple_poses.return_value = [sample_pose_context]
        mock_get_service.return_value = mock_service
        
        # Test data
        data = {
            'poses': [
                'Alice examines the artifact carefully.',
                'Bob steps closer to get a better look.'
            ]
        }
        
        response = client.post('/api/context/analyze-multiple', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'results' in result
        assert len(result['results']) == 1
        
        # Verify context structure
        context = result['results'][0]
        assert context['actions'] == ["examines the artifact", "steps closer"]
        assert context['emotions'] == ["curiosity", "caution"]
        
        # Verify service call
        mock_service.analyze_multiple_poses.assert_called_once_with(data['poses'], None)

    def test_analyze_multiple_poses_missing_data(self, client):
        """Test multiple pose analysis with missing data."""
        response = client.post('/api/context/analyze-multiple')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'No JSON data provided' in data['error']

    def test_analyze_multiple_poses_empty_poses(self, client):
        """Test multiple pose analysis with empty poses list."""
        data = {'poses': []}
        
        response = client.post('/api/context/analyze-multiple', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'poses must be a non-empty list' in result['error']

    def test_analyze_multiple_poses_missing_poses(self, client):
        """Test multiple pose analysis with missing poses field."""
        data = {'other_field': 'value'}
        
        response = client.post('/api/context/analyze-multiple', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'poses must be a non-empty list' in result['error']

    @patch('app.api.context.get_context_service')
    def test_analyze_multiple_poses_venice_api_error(self, mock_get_service, client):
        """Test multiple pose analysis with Venice API error."""
        # Mock the service to raise VeniceAPIError
        mock_service = MagicMock()
        mock_service.analyze_multiple_poses.side_effect = VeniceAPIError("API quota exceeded")
        mock_get_service.return_value = mock_service
        
        data = {'poses': ['Alice examines the artifact.']}
        
        response = client.post('/api/context/analyze-multiple', json=data)
        
        assert response.status_code == 503
        result = response.get_json()
        assert result['success'] is False
        assert 'AI processing failed' in result['error']
        assert 'API quota exceeded' in result['error']

    @patch('app.api.context.get_context_service')
    def test_analyze_multiple_poses_value_error(self, mock_get_service, client):
        """Test multiple pose analysis with value error."""
        # Mock the service to raise ValueError
        mock_service = MagicMock()
        mock_service.analyze_multiple_poses.side_effect = ValueError("Invalid poses format")
        mock_get_service.return_value = mock_service
        
        data = {'poses': ['Alice examines the artifact.']}
        
        response = client.post('/api/context/analyze-multiple', json=data)
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'Invalid data' in result['error']
        assert 'Invalid poses format' in result['error']

    @patch('app.api.context.get_context_service')
    def test_analyze_multiple_poses_generic_error(self, mock_get_service, client):
        """Test multiple pose analysis with generic error."""
        # Mock the service to raise generic exception
        mock_service = MagicMock()
        mock_service.analyze_multiple_poses.side_effect = Exception("Unexpected error")
        mock_get_service.return_value = mock_service
        
        data = {'poses': ['Alice examines the artifact.']}
        
        response = client.post('/api/context/analyze-multiple', json=data)
        
        assert response.status_code == 500
        result = response.get_json()
        assert result['success'] is False
        assert 'Internal server error' in result['error']
        assert 'Unexpected error' in result['error']

    # Test error handlers
    def test_not_found_error(self, client):
        """Test 404 error handling."""
        response = client.get('/api/context/nonexistent')
        
        assert response.status_code == 404
        # Flask may return HTML for 404, so check if we get JSON or HTML
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = response.get_json()
            assert data['success'] is False
        # If HTML response, that's also acceptable for 404

    def test_method_not_allowed_error(self, client):
        """Test 405 error handling."""
        response = client.put('/api/context/analyze')
        
        assert response.status_code == 405
        # Flask may return HTML for 405, so check if we get JSON or HTML
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = response.get_json()
            assert data['success'] is False
        # If HTML response, that's also acceptable for 405

    # Test service initialization
    @patch('app.api.context.VeniceClient')
    @patch('app.api.context.ContextService')
    @patch.dict('os.environ', {'VENICE_API_KEY': 'test_key_12345'})
    def test_get_context_service_initialization(self, mock_context_service, 
                                              mock_venice_client):
        """Test context service initialization."""
        from app.api.context import get_context_service
        
        # Reset global service
        import app.api.context
        app.api.context.context_service = None
        
        # Call get_context_service
        service = get_context_service()
        
        # Verify initialization
        mock_venice_client.assert_called_once_with(api_key="test_key_12345")
        mock_context_service.assert_called_once_with(mock_venice_client.return_value)
        
        # Verify service is returned
        assert service == mock_context_service.return_value
        
        # Verify singleton behavior
        service2 = get_context_service()
        assert service2 == service
        
        # Venice client should only be called once
        assert mock_venice_client.call_count == 1
        assert mock_context_service.call_count == 1 