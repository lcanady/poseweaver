import pytest
from unittest.mock import Mock, patch
import requests
from app.services.openrouter_client import OpenRouterClient, OpenRouterAPIError


class TestOpenRouterClient:
    """Test suite for OpenRouter.ai API client."""
    
    def test_client_initialization(self):
        """Test that OpenRouterClient initializes correctly."""
        api_key = "test_api_key_12345"
        client = OpenRouterClient(api_key)
        
        assert client.api_key == api_key
        assert client.base_url == "https://openrouter.ai/api/v1"
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == f"Bearer {api_key}"
        assert client.headers["Content-Type"] == "application/json"
    
    def test_client_initialization_with_custom_base_url(self):
        """Test client initialization with custom base URL."""
        api_key = "test_key"
        base_url = "https://custom.api.url/v1"
        client = OpenRouterClient(api_key, base_url=base_url)
        
        assert client.base_url == base_url
    
    @patch('requests.post')
    def test_generate_completion_success(self, mock_post):
        """Test successful completion generation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test AI response."
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Test the client
        client = OpenRouterClient("test_key")
        result = client.generate_completion(
            prompt="Test prompt",
            model="dolphin-2.9-llama3-70b"
        )
        
        # Verify the result
        assert result == "This is a test AI response."
        
        # Verify the API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        expected_url = "https://openrouter.ai/api/v1/chat/completions"
        assert call_args[0][0] == expected_url
        
        # Verify request payload
        payload = call_args[1]['json']
        assert payload['model'] == "dolphin-2.9-llama3-70b"
        expected_messages = [{"role": "user", "content": "Test prompt"}]
        assert payload['messages'] == expected_messages
        assert payload['temperature'] == 0.7  # default value
        assert payload['max_tokens'] == 32000  # default value
    
    @patch('requests.post')
    def test_generate_completion_with_custom_parameters(self, mock_post):
        """Test completion generation with custom parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Custom response"}}]
        }
        mock_post.return_value = mock_response
        
        client = OpenRouterClient("test_key")
        result = client.generate_completion(
            prompt="Custom prompt",
            model="custom-model",
            temperature=0.9,
            max_tokens=500
        )
        
        assert result == "Custom response"
        
        # Verify custom parameters were used
        payload = mock_post.call_args[1]['json']
        assert payload['temperature'] == 0.9
        assert payload['max_tokens'] == 500
        assert payload['model'] == "custom-model"
    
    @patch('requests.post')
    def test_generate_completion_api_error(self, mock_post):
        """Test handling of API errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "error": {
                "message": "Internal server error"
            }
        }
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "HTTP Error", response=mock_response
        )
        mock_post.return_value = mock_response
        
        client = OpenRouterClient("test_key")
        
        with pytest.raises(OpenRouterAPIError) as exc_info:
            client.generate_completion("Test prompt")
        
        assert "HTTP 500" in str(exc_info.value)
        assert "Internal server error" in str(exc_info.value)
    
    @patch('requests.post')
    def test_generate_completion_network_error(self, mock_post):
        """Test handling of network errors."""
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Network error"
        )
        
        client = OpenRouterClient("test_key")
        
        with pytest.raises(OpenRouterAPIError) as exc_info:
            client.generate_completion("Test prompt")
        
        assert "Connection error" in str(exc_info.value)
    
    @patch('requests.post')
    def test_generate_completion_timeout(self, mock_post):
        """Test handling of timeout errors."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        client = OpenRouterClient("test_key")
        
        with pytest.raises(OpenRouterAPIError) as exc_info:
            client.generate_completion("Test prompt")
        
        assert "Request timeout" in str(exc_info.value)
    
    @patch('requests.post')
    def test_generate_completion_invalid_json_response(self, mock_post):
        """Test handling of invalid JSON responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid response text"
        mock_post.return_value = mock_response
        
        client = OpenRouterClient("test_key")
        
        with pytest.raises(OpenRouterAPIError) as exc_info:
            client.generate_completion("Test prompt")
        
        assert "Invalid JSON response" in str(exc_info.value)
    
    @patch('requests.post')
    def test_generate_completion_missing_choices(self, mock_post):
        """Test handling of response missing choices."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "No choices"}
        mock_post.return_value = mock_response
        
        client = OpenRouterClient("test_key")
        
        with pytest.raises(OpenRouterAPIError) as exc_info:
            client.generate_completion("Test prompt")
        
        assert "No content found in API response" in str(exc_info.value)
    
    def test_validate_model_name_valid(self):
        """Test validation of valid model names."""
        client = OpenRouterClient("test_key")
        
        valid_models = [
            "dolphin-2.9-llama3-70b",
            "gpt-3.5-turbo",
            "claude-3-opus"
        ]
        
        for model in valid_models:
            assert client.validate_model_name(model) is True
    
    def test_validate_model_name_invalid(self):
        """Test validation of invalid model names."""
        client = OpenRouterClient("test_key")
        
        invalid_models = [
            "",
            None,
            "invalid/model",
            "model with spaces",
            "model@special"
        ]
        
        for model in invalid_models:
            assert client.validate_model_name(model) is False
    
    def test_validate_parameters(self):
        """Test parameter validation."""
        client = OpenRouterClient("test_key")
        
        # Valid parameters
        assert client.validate_parameters(
            temperature=0.7, max_tokens=4000) is True
        assert client.validate_parameters(
            temperature=0.0, max_tokens=1) is True
        assert client.validate_parameters(
            temperature=1.0, max_tokens=4000) is True
        
        # Invalid parameters
        with pytest.raises(ValueError):
            client.validate_parameters(temperature=-0.1, max_tokens=4000)
        
        with pytest.raises(ValueError):
            client.validate_parameters(temperature=1.1, max_tokens=4000)
        
        with pytest.raises(ValueError):
            client.validate_parameters(temperature=0.7, max_tokens=0)
        
        with pytest.raises(ValueError):
            client.validate_parameters(temperature=0.7, max_tokens=100000)
    
    @patch('requests.post')
    def test_generate_completion_with_system_message(self, mock_post):
        """Test completion generation with system message."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "System guided response"}}]
        }
        mock_post.return_value = mock_response
        
        client = OpenRouterClient("test_key")
        result = client.generate_completion(
            prompt="User prompt",
            system_message="You are a helpful assistant."
        )
        
        assert result == "System guided response"
        
        # Verify system message was included
        payload = mock_post.call_args[1]['json']
        messages = payload['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == "You are a helpful assistant."
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == "User prompt" 
        
    @patch('requests.post')
    def test_generate_completion_with_response_format(self, mock_post):
        """Test completion generation with response_format parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "{\"result\": \"structured data\"}"}}]
        }
        mock_post.return_value = mock_response
        
        client = OpenRouterClient("test_key")
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "test_schema",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {"result": {"type": "string"}},
                    "required": ["result"],
                    "additionalProperties": False
                }
            }
        }
        
        # Need to patch json.loads to return the expected structured data
        with patch('json.loads', return_value={"result": "structured data"}):
            result = client.generate_completion(
                prompt="Test prompt",
                response_format=response_format
            )
            
            assert result == '{"result": "structured data"}'
            
            # Verify response_format was included in the request
            payload = mock_post.call_args[1]['json']
            assert 'response_format' in payload
            assert payload['response_format'] == response_format
    
    @patch('requests.post')
    def test_extract_structured_data(self, mock_post):
        """Test structured data extraction with response_format."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "{\"name\": \"Test Character\", \"traits\": [\"brave\", \"intelligent\"]}"}}]
        }
        mock_post.return_value = mock_response
        
        # Create test data to be returned by json.loads
        test_data = {
            "name": "Test Character",
            "traits": ["brave", "intelligent"]
        }
        
        # Test the client with a patched json.loads
        client = OpenRouterClient("test_key")
        schema = {
            "name": "string - character name",
            "traits": "list of strings - character traits"
        }
        
        # Need to patch json.loads to return the expected structured data
        with patch('json.loads', return_value=test_data):
            result = client.extract_structured_data(
                unstructured_text="Character description text",
                schema=schema
            )
            
            # Verify result
            assert result["name"] == "Test Character"
            assert "brave" in result["traits"]
            assert "intelligent" in result["traits"]
            
            # Verify the API call was made correctly with response_format
            payload = mock_post.call_args[1]['json']
            assert 'response_format' in payload
            assert payload['response_format']['type'] == "json_schema"
            
            # Verify schema conversion
            json_schema = payload['response_format']['json_schema']['schema']
            assert json_schema['properties']['name']['type'][0] == "string"
            assert json_schema['properties']['traits']['type'] == "array"
            assert json_schema['required'] == ["name", "traits"]
            assert json_schema['additionalProperties'] is False