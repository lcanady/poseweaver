"""
Integration tests for Continuity API endpoints.

Tests all endpoints for real-time continuity analysis, flag management,
character state tracking, and environment state management.
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import create_app
from app.models.scene_memory import ContinuityFlag, FlagType, Severity
from app.models.character import Character
from app.models.scene import Scene, PoseType
from app.services.continuity_service import ContinuityAnalysis
from app.services.character_state_service import StateChange
from app.services.environment_state_service import EnvironmentUpdate


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Create authentication headers."""
    return {
        'Authorization': 'Bearer mock-jwt-token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def mock_scene():
    """Create a mock scene for testing."""
    scene = MagicMock()
    scene.id = 'test-scene-id'
    scene.name = 'Test Scene'
    scene.description = 'A test scene'
    scene.created_by = 'test-user'
    scene.created_at = datetime.utcnow()
    scene.updated_at = datetime.utcnow()
    scene.is_active = True
    scene.poses = []
    scene.to_dict.return_value = {
        'id': 'test-scene-id',
        'name': 'Test Scene',
        'description': 'A test scene',
        'created_by': 'test-user',
        'created_at': scene.created_at.isoformat(),
        'updated_at': scene.updated_at.isoformat(),
        'is_active': True,
        'poses': []
    }
    return scene


@pytest.fixture
def mock_continuity_flag():
    """Create a mock continuity flag for testing."""
    flag = MagicMock()
    flag.id = 'test-flag-id'
    flag.scene_id = 'test-scene-id'
    flag.pose_id = 'test-pose-id'
    flag.flag_type = FlagType.CHARACTER_INCONSISTENCY
    flag.severity = Severity.MEDIUM
    flag.description = 'Test continuity issue'
    flag.resolved = False
    flag.created_at = datetime.utcnow()
    flag.to_dict.return_value = {
        'id': 'test-flag-id',
        'scene_id': 'test-scene-id',
        'pose_id': 'test-pose-id',
        'flag_type': 'character_inconsistency',
        'severity': 'medium',
        'description': 'Test continuity issue',
        'resolved': False,
        'created_at': flag.created_at.isoformat()
    }
    return flag


class TestContinuityAnalysisAPI:
    """Test real-time continuity analysis API endpoints."""

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.services.continuity_service.ContinuityService.'
           'analyze_pose_continuity')
    def test_analyze_continuity_success(self, mock_analyze, mock_get_scene, 
                                        mock_jwt, client, auth_headers, 
                                        mock_scene):
        """Test successful continuity analysis."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_analyze.return_value = {
            'continuity_score': 0.8,
            'character_consistency': 0.9,
            'environment_consistency': 0.8,
            'plot_consistency': 0.7,
            'issues': [],
            'suggestions': ['Good consistency overall']
        }
        
        # Make request
        response = client.post('/api/continuity/analyze', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'pose_text': 'Test pose text',
                                 'character_id': 'test-character-id',
                                 'character_name': 'Test Character',
                                 'scene_id': 'test-scene-id',
                                 'analysis_type': 'full'
                             }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'continuity_analysis' in data['data']
        assert 'analysis_id' in data['data']
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', 
                                               user_id='test-user')
        mock_analyze.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    def test_analyze_continuity_missing_fields(self, mock_jwt, client, auth_headers):
        """Test continuity analysis with missing required fields."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request without required fields
        response = client.post('/api/continuity/analyze', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'pose_text': 'Test pose text',
                                 'character_id': 'test-character-id'
                                 # Missing character_name and scene_id
                             }))
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'missing required fields' in data['message'].lower()

    @patch('app.api.continuity.get_jwt_identity')
    def test_analyze_continuity_invalid_analysis_type(self, mock_jwt, client, auth_headers):
        """Test continuity analysis with invalid analysis type."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with invalid analysis type
        response = client.post('/api/continuity/analyze', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'pose_text': 'Test pose text',
                                 'character_id': 'test-character-id',
                                 'character_name': 'Test Character',
                                 'scene_id': 'test-scene-id',
                                 'analysis_type': 'invalid'
                             }))
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid analysis_type' in data['message'].lower()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    def test_analyze_continuity_scene_not_found(self, mock_get_scene, mock_jwt, client, auth_headers):
        """Test continuity analysis when scene not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = None
        
        # Make request
        response = client.post('/api/continuity/analyze', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'pose_text': 'Test pose text',
                                 'character_id': 'test-character-id',
                                 'character_name': 'Test Character',
                                 'scene_id': 'nonexistent-scene-id',
                                 'analysis_type': 'full'
                             }))
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.services.continuity_service.ContinuityService.analyze_pose_continuity')
    def test_analyze_batch_continuity_success(self, mock_analyze, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful batch continuity analysis."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_analyze.return_value = {
            'continuity_score': 0.8,
            'issues': [],
            'suggestions': []
        }
        
        # Make request
        response = client.post('/api/continuity/analyze/batch', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'poses': [
                                     {
                                         'pose_text': 'First pose',
                                         'character_id': 'char1',
                                         'character_name': 'Character1',
                                         'scene_id': 'test-scene-id'
                                     },
                                     {
                                         'pose_text': 'Second pose',
                                         'character_id': 'char2',
                                         'character_name': 'Character2',
                                         'scene_id': 'test-scene-id'
                                     }
                                 ],
                                 'include_cross_analysis': True
                             }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['total_poses'] == 2
        assert data['data']['successful_analyses'] == 2
        assert len(data['data']['results']) == 2
        
        # Verify service calls
        assert mock_analyze.call_count == 2


class TestContinuityFlagAPI:
    """Test continuity flag management API endpoints."""

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.continuity_service.get_continuity_flags')
    def test_get_continuity_flags_success(self, mock_get_flags, mock_jwt, client, auth_headers, mock_continuity_flag):
        """Test successful continuity flags retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_flags.return_value = [mock_continuity_flag]
        
        # Make request
        response = client.get('/api/continuity/flags', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == 'test-flag-id'
        assert data['meta']['total_flags'] == 1
        
        # Verify service calls
        mock_get_flags.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.continuity_service.get_continuity_flags')
    def test_get_continuity_flags_with_filters(self, mock_get_flags, mock_jwt, client, auth_headers, mock_continuity_flag):
        """Test continuity flags retrieval with filters."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_flags.return_value = [mock_continuity_flag]
        
        # Make request with filters
        response = client.get('/api/continuity/flags?scene_id=test-scene-id&flag_type=character_inconsistency&resolved=false', 
                             headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        
        # Verify service calls
        mock_get_flags.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.ContinuityFlag.find_by_id')
    @patch('app.api.continuity.SceneService.get_scene')
    def test_get_continuity_flag_success(self, mock_get_scene, mock_find_flag, mock_jwt, client, auth_headers, mock_continuity_flag, mock_scene):
        """Test successful individual continuity flag retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_find_flag.return_value = mock_continuity_flag
        mock_get_scene.return_value = mock_scene
        
        # Make request
        response = client.get('/api/continuity/flags/test-flag-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'test-flag-id'
        assert data['data']['scene_name'] == 'Test Scene'
        
        # Verify service calls
        mock_find_flag.assert_called_once_with('test-flag-id')
        mock_get_scene.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.ContinuityFlag.find_by_id')
    def test_get_continuity_flag_not_found(self, mock_find_flag, mock_jwt, client, auth_headers):
        """Test continuity flag retrieval when flag not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_find_flag.return_value = None
        
        # Make request
        response = client.get('/api/continuity/flags/nonexistent-flag-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.ContinuityFlag.find_by_id')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.continuity_service.resolve_continuity_flag')
    def test_resolve_continuity_flag_success(self, mock_resolve, mock_get_scene, mock_find_flag, mock_jwt, client, auth_headers, mock_continuity_flag, mock_scene):
        """Test successful continuity flag resolution."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_find_flag.return_value = mock_continuity_flag
        mock_get_scene.return_value = mock_scene
        mock_resolve.return_value = True
        
        # Make request
        response = client.post('/api/continuity/flags/test-flag-id/resolve', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'resolution_notes': 'Issue resolved',
                                 'resolution_type': 'accepted'
                             }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'resolved successfully' in data['message']
        
        # Verify service calls
        mock_resolve.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.ContinuityFlag.find_by_id')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.continuity_service.dismiss_continuity_flag')
    def test_dismiss_continuity_flag_success(self, mock_dismiss, mock_get_scene, mock_find_flag, mock_jwt, client, auth_headers, mock_continuity_flag, mock_scene):
        """Test successful continuity flag dismissal."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_find_flag.return_value = mock_continuity_flag
        mock_get_scene.return_value = mock_scene
        mock_dismiss.return_value = True
        
        # Make request
        response = client.post('/api/continuity/flags/test-flag-id/dismiss', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'dismiss_reason': 'False positive',
                                 'permanent': False
                             }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'dismissed successfully' in data['message']
        
        # Verify service calls
        mock_dismiss.assert_called_once()


class TestCharacterStateAPI:
    """Test character state tracking API endpoints."""

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.character_state_service.get_scene_character_states')
    def test_get_character_states_success(self, mock_get_states, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful character states retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_state = MagicMock()
        mock_state.to_dict.return_value = {
            'id': 'test-state-id',
            'character_name': 'Test Character',
            'scene_id': 'test-scene-id',
            'physical_state': {'health': 'healthy'},
            'emotional_state': {'mood': 'neutral'}
        }
        mock_get_states.return_value = [mock_state]
        
        # Make request
        response = client.get('/api/continuity/character-states/test-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == 'test-state-id'
        assert data['meta']['scene_id'] == 'test-scene-id'
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', user_id='test-user')
        mock_get_states.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.character_state_service.get_character_current_state')
    def test_get_character_state_success(self, mock_get_state, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful individual character state retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_state = MagicMock()
        mock_state.to_dict.return_value = {
            'id': 'test-state-id',
            'character_name': 'Test Character',
            'scene_id': 'test-scene-id',
            'physical_state': {'health': 'healthy'},
            'emotional_state': {'mood': 'neutral'}
        }
        mock_get_state.return_value = mock_state
        
        # Make request
        response = client.get('/api/continuity/character-states/test-scene-id/Test Character', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'test-state-id'
        assert data['data']['character_name'] == 'Test Character'
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', user_id='test-user')
        mock_get_state.assert_called_once_with(scene_id='test-scene-id', character_name='Test Character')

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.character_state_service.get_character_current_state')
    def test_get_character_state_not_found(self, mock_get_state, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test character state retrieval when state not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_state.return_value = None
        
        # Make request
        response = client.get('/api/continuity/character-states/test-scene-id/Nonexistent Character', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.character_state_service.get_character_current_state')
    @patch('app.api.continuity.character_state_service.initialize_character_state')
    def test_initialize_character_state_success(self, mock_initialize, mock_get_state, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful character state initialization."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_state.return_value = None  # No existing state
        mock_state = MagicMock()
        mock_state.to_dict.return_value = {
            'id': 'test-state-id',
            'character_name': 'Test Character',
            'scene_id': 'test-scene-id',
            'physical_state': {'health': 'healthy'},
            'emotional_state': {'mood': 'neutral'}
        }
        mock_initialize.return_value = mock_state
        
        # Make request
        response = client.post('/api/continuity/character-states/test-scene-id/Test Character', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'initial_state': {
                                     'physical_state': {'health': 'healthy'},
                                     'emotional_state': {'mood': 'neutral'}
                                 }
                             }))
        
        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'test-state-id'
        assert 'initialized successfully' in data['message']
        
        # Verify service calls
        mock_initialize.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.character_state_service.update_character_state')
    def test_update_character_state_success(self, mock_update, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful character state update."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_state = MagicMock()
        mock_state.to_dict.return_value = {
            'id': 'test-state-id',
            'character_name': 'Test Character',
            'scene_id': 'test-scene-id',
            'physical_state': {'health': 'injured'},
            'emotional_state': {'mood': 'anxious'}
        }
        mock_update.return_value = mock_state
        
        # Make request
        response = client.put('/api/continuity/character-states/test-scene-id/Test Character', 
                            headers=auth_headers,
                            data=json.dumps({
                                'updates': {
                                    'physical_state': {'health': 'injured'},
                                    'emotional_state': {'mood': 'anxious'}
                                },
                                'change_reason': 'Updated from pose analysis'
                            }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'test-state-id'
        assert 'updated successfully' in data['message']
        
        # Verify service calls
        mock_update.assert_called_once()


class TestEnvironmentStateAPI:
    """Test environment state management API endpoints."""

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.environment_state_service.get_scene_environments')
    def test_get_environment_states_success(self, mock_get_environments, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful environment states retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_env = MagicMock()
        mock_env.to_dict.return_value = {
            'id': 'test-env-id',
            'scene_id': 'test-scene-id',
            'location_name': 'Forest Clearing',
            'description': 'A peaceful clearing',
            'weather': {'condition': 'clear'},
            'time_context': {'time_of_day': 'afternoon'}
        }
        mock_get_environments.return_value = [mock_env]
        
        # Make request
        response = client.get('/api/continuity/environment-states/test-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == 'test-env-id'
        assert data['meta']['scene_id'] == 'test-scene-id'
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', user_id='test-user')
        mock_get_environments.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.environment_state_service.get_current_environment')
    def test_get_current_environment_state_success(self, mock_get_current, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful current environment state retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_env = MagicMock()
        mock_env.to_dict.return_value = {
            'id': 'test-env-id',
            'scene_id': 'test-scene-id',
            'location_name': 'Forest Clearing',
            'description': 'A peaceful clearing',
            'weather': {'condition': 'clear'},
            'time_context': {'time_of_day': 'afternoon'}
        }
        mock_get_current.return_value = mock_env
        
        # Make request
        response = client.get('/api/continuity/environment-states/test-scene-id/current', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'test-env-id'
        assert data['data']['location_name'] == 'Forest Clearing'
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', user_id='test-user')
        mock_get_current.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.environment_state_service.get_current_environment')
    def test_get_current_environment_state_not_found(self, mock_get_current, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test current environment state retrieval when not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_current.return_value = None
        
        # Make request
        response = client.get('/api/continuity/environment-states/test-scene-id/current', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.environment_state_service.initialize_environment_state')
    def test_initialize_environment_state_success(self, mock_initialize, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful environment state initialization."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_env = MagicMock()
        mock_env.to_dict.return_value = {
            'id': 'test-env-id',
            'scene_id': 'test-scene-id',
            'location_name': 'Forest Clearing',
            'description': 'A peaceful clearing',
            'weather': {'condition': 'clear'},
            'time_context': {'time_of_day': 'afternoon'}
        }
        mock_initialize.return_value = mock_env
        
        # Make request
        response = client.post('/api/continuity/environment-states/test-scene-id', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'location_name': 'Forest Clearing',
                                 'description': 'A peaceful clearing',
                                 'weather': {'condition': 'clear'},
                                 'time_context': {'time_of_day': 'afternoon'}
                             }))
        
        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'test-env-id'
        assert 'initialized successfully' in data['message']
        
        # Verify service calls
        mock_initialize.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.environment_state_service.get_current_environment')
    @patch('app.api.continuity.environment_state_service.check_environment_consistency')
    def test_check_environment_consistency_success(self, mock_check, mock_get_current, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful environment consistency check."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_env = MagicMock()
        mock_get_current.return_value = mock_env
        mock_check.return_value = {
            'is_consistent': True,
            'conflicts': [],
            'confidence_score': 0.9,
            'suggestions': []
        }
        
        # Make request
        response = client.post('/api/continuity/environment-states/test-scene-id/check-consistency', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'content': 'The sun shines brightly overhead',
                                 'character_name': 'Test Character',
                                 'include_suggestions': True
                             }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['is_consistent'] is True
        assert data['data']['confidence_score'] == 0.9
        
        # Verify service calls
        mock_check.assert_called_once()


class TestContinuitySummaryAPI:
    """Test continuity summary and dashboard API endpoints."""

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.continuity_service.get_scene_continuity_summary')
    def test_get_continuity_summary_success(self, mock_get_summary, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful continuity summary retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_summary.return_value = {
            'scene_id': 'test-scene-id',
            'total_flags': 5,
            'unresolved_flags': 2,
            'resolved_flags': 3,
            'flag_types': {'character_inconsistency': 3, 'environment_contradiction': 2},
            'severity_distribution': {'low': 2, 'medium': 2, 'high': 1},
            'overall_health': 'good'
        }
        
        # Make request
        response = client.get('/api/continuity/summary/test-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['scene_id'] == 'test-scene-id'
        assert data['data']['total_flags'] == 5
        assert data['data']['overall_health'] == 'good'
        assert 'scene_info' in data['data']
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', user_id='test-user')
        mock_get_summary.assert_called_once()

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    def test_get_continuity_summary_scene_not_found(self, mock_get_scene, mock_jwt, client, auth_headers):
        """Test continuity summary retrieval when scene not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = None
        
        # Make request
        response = client.get('/api/continuity/summary/nonexistent-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    def test_health_check_success(self, client):
        """Test successful health check."""
        # Make request
        response = client.get('/api/continuity/health')
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['service'] == 'continuity_api'
        assert 'services' in data
        assert 'timestamp' in data


class TestContinuityAPIIntegration:
    """Integration tests for the complete continuity API workflow."""

    @patch('app.api.continuity.get_jwt_identity')
    @patch('app.api.continuity.SceneService.get_scene')
    @patch('app.api.continuity.continuity_service.analyze_pose_continuity')
    @patch('app.api.continuity.continuity_service.get_continuity_flags')
    @patch('app.api.continuity.continuity_service.get_scene_continuity_summary')
    def test_complete_workflow(self, mock_get_summary, mock_get_flags, mock_analyze, mock_get_scene, mock_jwt, client, auth_headers, mock_scene, mock_continuity_flag):
        """Test complete workflow: analyze continuity, get flags, get summary."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_analyze.return_value = {
            'continuity_score': 0.7,
            'issues': [{'type': 'character', 'severity': 'medium'}],
            'suggestions': ['Check character consistency']
        }
        mock_get_flags.return_value = [mock_continuity_flag]
        mock_get_summary.return_value = {
            'scene_id': 'test-scene-id',
            'total_flags': 1,
            'unresolved_flags': 1,
            'overall_health': 'needs_attention'
        }
        
        # 1. Analyze continuity
        analyze_response = client.post('/api/continuity/analyze', 
                                     headers=auth_headers,
                                     data=json.dumps({
                                         'pose_text': 'Test pose',
                                         'character_id': 'test-char',
                                         'character_name': 'Test Character',
                                         'scene_id': 'test-scene-id'
                                     }))
        assert analyze_response.status_code == 200
        
        # 2. Get continuity flags
        flags_response = client.get('/api/continuity/flags?scene_id=test-scene-id', 
                                   headers=auth_headers)
        assert flags_response.status_code == 200
        
        # 3. Get continuity summary
        summary_response = client.get('/api/continuity/summary/test-scene-id', 
                                    headers=auth_headers)
        assert summary_response.status_code == 200
        
        # Verify all services were called
        mock_analyze.assert_called_once()
        mock_get_flags.assert_called_once()
        mock_get_summary.assert_called_once()
        
        # Verify data consistency across responses
        analyze_data = json.loads(analyze_response.data)
        flags_data = json.loads(flags_response.data)
        summary_data = json.loads(summary_response.data)
        
        assert analyze_data['success'] is True
        assert flags_data['success'] is True
        assert summary_data['success'] is True
        assert summary_data['data']['scene_id'] == 'test-scene-id' 