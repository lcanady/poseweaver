"""
Tests for authentication API endpoints.
"""
import json
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture
def app():
    """Create app instance for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User.create_user(
            email='test@example.com',
            password='testpass123',
            display_name='Test User'
        )
        return user


class TestAuthAPI:
    """Test cases for authentication API."""
    
    def test_signup_success(self, client):
        """Test successful user registration."""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'display_name': 'New User'
        }
        
        response = client.post('/api/auth/signup', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'user' in response_data
        assert 'access_token' in response_data
        assert 'refresh_token' in response_data
        assert response_data['user']['email'] == 'newuser@example.com'
        assert response_data['user']['display_name'] == 'New User'
    
    def test_signup_duplicate_email(self, client, test_user):
        """Test signup with duplicate email."""
        data = {
            'email': 'test@example.com',
            'password': 'newpass123',
            'display_name': 'Another User'
        }
        
        response = client.post('/api/auth/signup',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'already exists' in response_data['error']
    
    def test_signup_missing_fields(self, client):
        """Test signup with missing required fields."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
            # Missing display_name
        }
        
        response = client.post('/api/auth/signup',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'user' in response_data
        assert 'access_token' in response_data
        assert 'refresh_token' in response_data
        assert response_data['user']['email'] == 'test@example.com'
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'Invalid credentials' in response_data['error']
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        data = {
            'email': 'test@example.com'
            # Missing password
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
    
    def test_get_current_user_success(self, client, test_user):
        """Test getting current user with valid token."""
        # First login to get token
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        login_response_data = json.loads(login_response.data)
        access_token = login_response_data['access_token']
        
        # Get current user
        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.get('/api/auth/me', headers=headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'user' in response_data
        assert response_data['user']['email'] == 'test@example.com'
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_logout_success(self, client, test_user):
        """Test successful logout."""
        # First login to get token
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        login_response_data = json.loads(login_response.data)
        access_token = login_response_data['access_token']
        
        # Logout
        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.post('/api/auth/logout', headers=headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'Successfully logged out' in response_data['message'] 