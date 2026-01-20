"""
Tests for character API endpoints.
"""
import json
import pytest
from unittest.mock import Mock, patch
from app import create_app
from app.services.character_service import CharacterProfile
from app.services.openrouter_client import OpenRouterAPIError


class TestCharacterAPI:
    """Test character API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application."""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def sample_character_data(self):
        """Sample character data for testing."""
        return {
            "name": "Lyra Nightwhisper",
            "background": "A half-elf bard from Waterdeep",
            "personality": ["charismatic", "street-smart"],
            "skills": ["performance", "persuasion"],
            "goals": ["Become a renowned performer"],
            "relationships": {"Old Tom": "mentor figure"},
            "voice_notes": "Uses colorful street slang"
        }
    
    @patch('app.api.characters.character_service')
    def test_process_brain_dump_success(self, mock_service, client, 
                                       sample_character_data):
        """Test successful brain dump processing."""
        # Mock service response
        mock_profile = CharacterProfile(**sample_character_data)
        mock_service.process_brain_dump.return_value = mock_profile
        
        # Make request
        response = client.post('/api/characters/process',
                             json={'brain_dump': 'Test character description'})
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'character' in data
        assert data['character']['name'] == 'Lyra Nightwhisper'
        
        # Verify service was called
        mock_service.process_brain_dump.assert_called_once()
    
    @patch('app.api.characters.character_service')
    def test_process_brain_dump_with_existing_character(self, mock_service, 
                                                       client, 
                                                       sample_character_data):
        """Test brain dump processing with existing character."""
        # Mock service response
        mock_profile = CharacterProfile(**sample_character_data)
        mock_service.process_brain_dump.return_value = mock_profile
        
        # Prepare request with existing character
        request_data = {
            'brain_dump': 'Additional character info',
            'existing_character': sample_character_data
        }
        
        # Make request
        response = client.post('/api/characters/process', json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'character' in data
        
        # Verify service was called with existing character
        mock_service.process_brain_dump.assert_called_once()
        args = mock_service.process_brain_dump.call_args
        assert args[0][0] == 'Additional character info'
        assert args[0][1] is not None  # existing_character parameter
    
    @patch('app.api.characters.get_character_service')
    def test_process_brain_dump_missing_data(self, mock_get_service, client):
        """Test brain dump processing with missing data."""
        response = client.post('/api/characters/process')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'No JSON data provided' in data['error']
        # Service shouldn't be called for missing data
        mock_get_service.assert_not_called()
    
    def test_process_brain_dump_empty_brain_dump(self, client):
        """Test brain dump processing with empty brain dump."""
        response = client.post('/api/characters/process',
                             json={'brain_dump': ''})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'brain_dump is required' in data['error']
    
    def test_process_brain_dump_invalid_existing_character(self, client):
        """Test brain dump processing with invalid existing character."""
        request_data = {
            'brain_dump': 'Test description',
            'existing_character': {'invalid': 'data'}
        }
        
        response = client.post('/api/characters/process', json=request_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid existing character data' in data['error']
    
    @patch('app.api.characters.character_service')
    def test_process_brain_dump_openrouter_api_error(self, mock_service, client):
        """Test handling of OpenRouter API errors."""
        mock_service.process_brain_dump.side_effect = OpenRouterAPIError(
            "API Error", 500
        )
        
        response = client.post('/api/characters/process',
                             json={'brain_dump': 'Test description'})
        
        assert response.status_code == 503
        data = response.get_json()
        assert data['success'] is False
        assert 'AI processing failed' in data['error']
    
    @patch('app.api.characters.character_service')
    def test_process_brain_dump_value_error(self, mock_service, client):
        """Test handling of value errors."""
        mock_service.process_brain_dump.side_effect = ValueError(
            "Invalid data"
        )
        
        response = client.post('/api/characters/process',
                             json={'brain_dump': 'Test description'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid data' in data['error']
    
    @patch('app.api.characters.character_service')
    def test_validate_character_valid(self, mock_service, client, 
                                     sample_character_data):
        """Test character validation with valid data."""
        # Mock service validation (no exception = valid)
        mock_service._validate_character_data.return_value = None
        
        response = client.post('/api/characters/validate',
                             json={'character': sample_character_data})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['valid'] is True
        assert data['errors'] == []
    
    @patch('app.api.characters.character_service')
    def test_validate_character_invalid(self, mock_service, client):
        """Test character validation with invalid data."""
        # Mock service validation error
        mock_service._validate_character_data.side_effect = ValueError(
            "Missing required field: name"
        )
        
        response = client.post('/api/characters/validate',
                             json={'character': {'invalid': 'data'}})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['valid'] is False
        assert len(data['errors']) == 1
        assert 'Missing required field: name' in data['errors'][0]
    
    @patch('app.api.characters.get_character_service')
    def test_validate_character_missing_data(self, mock_get_service, client):
        """Test character validation with missing data."""
        response = client.post('/api/characters/validate')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'No JSON data provided' in data['error']
        # Service shouldn't be called for missing data
        mock_get_service.assert_not_called()
    
    def test_validate_character_missing_character_field(self, client):
        """Test character validation with missing character field."""
        response = client.post('/api/characters/validate',
                             json={'other': 'data'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'character data is required' in data['error']
    
    def test_get_character_schema(self, client):
        """Test getting character schema."""
        response = client.get('/api/characters/schema')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'schema' in data
        assert 'fields' in data['schema']
        
        # Check required fields are present
        fields = data['schema']['fields']
        required_fields = [
            'name', 'background', 'personality', 'skills',
            'goals', 'relationships', 'voice_notes'
        ]
        for field in required_fields:
            assert field in fields
            assert fields[field]['required'] is True
    
    def test_not_found_error(self, client):
        """Test 404 error handling."""
        response = client.get('/api/characters/nonexistent')
        
        assert response.status_code == 404
        # Flask may return HTML for 404, so check if we get JSON or HTML
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = response.get_json()
            assert data['success'] is False
        # If HTML response, that's also acceptable for 404

    def test_method_not_allowed_error(self, client):
        """Test 405 error handling."""
        response = client.put('/api/characters/process')
        
        assert response.status_code == 405
        # Flask may return HTML for 405, so check if we get JSON or HTML
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = response.get_json()
            assert data['success'] is False
        # If HTML response, that's also acceptable for 405 