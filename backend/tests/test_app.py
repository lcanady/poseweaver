from app import create_app


class TestApplication:
    """Test application setup and configuration."""
    
    def test_app_creation(self):
        """Test that the Flask app can be created."""
        app = create_app('testing')
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'mush-pose-editor'
    
    def test_cors_configuration(self, client):
        """Test CORS headers are properly configured."""
        response = client.options('/api/characters/schema')
        
        # CORS headers should be present
        assert 'Access-Control-Allow-Origin' in response.headers
        # Flask-CORS provides different header names
        allow_methods_present = (
            'Allow' in response.headers or 
            'Access-Control-Allow-Methods' in response.headers
        )
        assert allow_methods_present
        assert response.status_code == 200
    
    def test_api_endpoints_registered(self, app):
        """Test that API blueprints are properly registered."""
        with app.app_context():
            # Check that character endpoints are registered
            assert any(
                rule.rule.startswith('/api/characters') 
                for rule in app.url_map.iter_rules()
            )
            
            # Check that pose endpoints are registered
            assert any(
                rule.rule.startswith('/api/pose') 
                for rule in app.url_map.iter_rules()
            )
    
    def test_environment_configuration(self, app):
        """Test environment variables are properly loaded."""
        assert app.config.get('OPENROUTER_API_KEY') is not None
        assert app.config.get('TESTING') is True 