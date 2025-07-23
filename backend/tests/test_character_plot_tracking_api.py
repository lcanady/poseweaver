"""
Integration tests for Character and Plot Tracking API endpoints.

Tests all endpoints for plot thread management, character consistency checking,
and relationship tracking functionality.
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import create_app
from app.models.scene_memory import PlotThread, PlotStatus, CharacterState
from app.models.character import Character
from app.models.scene import Scene, PoseType
from app.services.plot_thread_service import PlotElement, PlotReminder
from app.services.character_state_service import StateChange


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
def mock_plot_thread():
    """Create a mock plot thread for testing."""
    thread = MagicMock()
    thread.id = 'test-thread-id'
    thread.scene_id = 'test-scene-id'
    thread.title = 'Test Plot Thread'
    thread.description = 'A test plot thread'
    thread.status = PlotStatus.DEVELOPING
    thread.importance_score = 0.8
    thread.created_at = datetime.utcnow()
    thread.last_referenced = datetime.utcnow()
    thread.to_dict.return_value = {
        'id': 'test-thread-id',
        'scene_id': 'test-scene-id',
        'title': 'Test Plot Thread',
        'description': 'A test plot thread',
        'status': 'developing',
        'importance_score': 0.8,
        'created_at': thread.created_at.isoformat(),
        'last_referenced': thread.last_referenced.isoformat()
    }
    return thread


@pytest.fixture
def mock_character_state():
    """Create a mock character state for testing."""
    state = MagicMock()
    state.id = 'test-state-id'
    state.scene_id = 'test-scene-id'
    state.character_name = 'Test Character'
    state.physical_state = {'health': 'healthy'}
    state.emotional_state = {'mood': 'neutral'}
    state.equipment = {'weapons': [], 'armor': []}
    state.conditions = {'magical_effects': []}
    state.location = 'Forest Clearing'
    state.to_dict.return_value = {
        'id': 'test-state-id',
        'scene_id': 'test-scene-id',
        'character_name': 'Test Character',
        'physical_state': state.physical_state,
        'emotional_state': state.emotional_state,
        'equipment': state.equipment,
        'conditions': state.conditions,
        'location': state.location
    }
    return state


class TestPlotThreadAPI:
    """Test plot thread management API endpoints."""

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.PlotThread.find_by_scene')
    @patch('app.api.character_plot_tracking.plot_thread_service.get_stale_plot_threads')
    def test_get_plot_threads_success(self, mock_get_stale, mock_find_by_scene, mock_get_scene, mock_jwt, client, auth_headers, mock_scene, mock_plot_thread):
        """Test successful plot threads retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_find_by_scene.return_value = [mock_plot_thread]
        mock_get_stale.return_value = []
        
        # Make request
        response = client.get('/api/character-plot/plot-threads/test-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == 'test-thread-id'
        assert data['meta']['scene_id'] == 'test-scene-id'
        assert data['meta']['total_threads'] == 1
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', user_id='test-user')
        mock_find_by_scene.assert_called_once_with('test-scene-id')

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.PlotThread.find_by_scene')
    def test_get_plot_threads_with_filters(self, mock_find_by_scene, mock_get_scene, mock_jwt, client, auth_headers, mock_scene, mock_plot_thread):
        """Test plot threads retrieval with filters."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_find_by_scene.return_value = [mock_plot_thread]
        
        # Make request with filters
        response = client.get('/api/character-plot/plot-threads/test-scene-id?status=developing&importance_min=0.5', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'filters' in data['meta']
        assert data['meta']['filters']['status'] == 'developing'
        assert data['meta']['filters']['importance_min'] == 0.5

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.PlotThread.find_by_id')
    def test_get_plot_thread_success(self, mock_find_by_id, mock_get_scene, mock_jwt, client, auth_headers, mock_scene, mock_plot_thread):
        """Test successful individual plot thread retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_find_by_id.return_value = mock_plot_thread
        
        # Make request
        response = client.get('/api/character-plot/plot-threads/test-scene-id/test-thread-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'test-thread-id'
        assert data['data']['title'] == 'Test Plot Thread'
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', user_id='test-user')
        mock_find_by_id.assert_called_once_with('test-thread-id')

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.PlotThread.find_by_id')
    def test_get_plot_thread_not_found(self, mock_find_by_id, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test plot thread retrieval when thread not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_find_by_id.return_value = None
        
        # Make request
        response = client.get('/api/character-plot/plot-threads/test-scene-id/nonexistent-thread-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.PlotThread.find_by_id')
    @patch('app.api.character_plot_tracking.plot_thread_service.update_plot_thread_status')
    def test_update_plot_thread_success(self, mock_update_status, mock_find_by_id, mock_get_scene, mock_jwt, client, auth_headers, mock_scene, mock_plot_thread):
        """Test successful plot thread update."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_find_by_id.return_value = mock_plot_thread
        mock_update_status.return_value = True
        
        # Make request
        response = client.put('/api/character-plot/plot-threads/test-scene-id/test-thread-id', 
                             headers=auth_headers,
                             data=json.dumps({
                                 'status': 'resolved',
                                 'resolution_notes': 'Thread resolved successfully',
                                 'importance_score': 0.9
                             }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'updated successfully' in data['message']
        
        # Verify service calls
        mock_update_status.assert_called_once()

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.PlotThread.find_by_id')
    @patch('app.api.character_plot_tracking.plot_thread_service.analyze_plot_thread')
    def test_analyze_plot_thread_success(self, mock_analyze, mock_find_by_id, mock_get_scene, mock_jwt, client, auth_headers, mock_scene, mock_plot_thread):
        """Test successful plot thread analysis."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_find_by_id.return_value = mock_plot_thread
        mock_analyze.return_value = {
            'thread_id': 'test-thread-id',
            'analysis_type': 'all',
            'connections': [],
            'development_opportunities': [],
            'resolution_suggestions': []
        }
        
        # Make request
        response = client.post('/api/character-plot/plot-threads/test-scene-id/test-thread-id/analyze', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'analysis_type': 'all',
                                  'include_suggestions': True
                              }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'thread_id' in data['data']
        
        # Verify service calls
        mock_analyze.assert_called_once()

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.plot_thread_service.generate_plot_reminders')
    def test_get_plot_reminders_success(self, mock_generate_reminders, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful plot reminders retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_reminder = MagicMock()
        mock_reminder.thread_id = 'test-thread-id'
        mock_reminder.title = 'Stale Thread'
        mock_reminder.days_since_reference = 10
        mock_reminder.importance_score = 0.8
        mock_reminder.suggested_action = 'Follow up on thread'
        mock_reminder.reminder_text = 'This thread needs attention'
        mock_generate_reminders.return_value = [mock_reminder]
        
        # Make request
        response = client.get('/api/character-plot/plot-threads/test-scene-id/reminders', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['thread_id'] == 'test-thread-id'
        assert data['meta']['scene_id'] == 'test-scene-id'
        
        # Verify service calls
        mock_generate_reminders.assert_called_once()

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.plot_thread_service.get_plot_thread_summary')
    def test_get_plot_thread_summary_success(self, mock_get_summary, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful plot thread summary retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_summary.return_value = {
            'scene_id': 'test-scene-id',
            'total_threads': 5,
            'active_threads': 3,
            'status_distribution': {'developing': 3, 'resolved': 2},
            'average_importance': 0.7,
            'stale_threads': 1,
            'needs_attention': 1
        }
        
        # Make request
        response = client.get('/api/character-plot/plot-threads/test-scene-id/summary', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['scene_id'] == 'test-scene-id'
        assert data['data']['total_threads'] == 5
        assert data['data']['active_threads'] == 3
        
        # Verify service calls
        mock_get_summary.assert_called_once_with('test-scene-id')


class TestCharacterConsistencyAPI:
    """Test character consistency checking API endpoints."""

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.character_state_service.check_character_consistency')
    def test_check_character_consistency_success(self, mock_check_consistency, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful character consistency check."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_check_consistency.return_value = {
            'character_name': 'Test Character',
            'consistency_score': 0.85,
            'voice_consistency': 0.9,
            'behavior_consistency': 0.8,
            'relationship_consistency': 0.85,
            'issues': [],
            'suggestions': ['Good consistency overall']
        }
        
        # Make request
        response = client.post('/api/character-plot/character-consistency/test-scene-id/Test Character/check', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'pose_text': 'Test pose content',
                                  'analysis_depth': 10,
                                  'consistency_types': ['voice', 'behavior'],
                                  'include_suggestions': True
                              }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['character_name'] == 'Test Character'
        assert data['data']['consistency_score'] == 0.85
        
        # Verify service calls
        mock_check_consistency.assert_called_once()

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    def test_check_character_consistency_missing_pose_text(self, mock_jwt, client, auth_headers):
        """Test character consistency check with missing pose text."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request without pose_text
        response = client.post('/api/character-plot/character-consistency/test-scene-id/Test Character/check', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'analysis_depth': 10
                              }))
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'pose_text is required' in data['message']

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.character_state_service.get_character_consistency_history')
    def test_get_character_consistency_history_success(self, mock_get_history, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful character consistency history retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_history.return_value = {
            'character_name': 'Test Character',
            'scene_id': 'test-scene-id',
            'consistency_checks': [],
            'trends': {
                'overall_trend': 'stable',
                'voice_trend': 'improving',
                'behavior_trend': 'stable'
            },
            'averages': {
                'overall': 0.8,
                'voice': 0.85,
                'behavior': 0.75
            }
        }
        
        # Make request
        response = client.get('/api/character-plot/character-consistency/test-scene-id/Test Character/history', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['character_name'] == 'Test Character'
        assert 'trends' in data['data']
        
        # Verify service calls
        mock_get_history.assert_called_once()


class TestCharacterRelationshipAPI:
    """Test character relationship tracking API endpoints."""

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.character_state_service.get_scene_relationships')
    def test_get_character_relationships_success(self, mock_get_relationships, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful character relationships retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_relationships.return_value = [
            {
                'character1': 'Character A',
                'character2': 'Character B',
                'relationship_type': 'friendly',
                'interaction_count': 5,
                'last_interaction': datetime.utcnow().isoformat()
            }
        ]
        
        # Make request
        response = client.get('/api/character-plot/relationships/test-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['character1'] == 'Character A'
        assert data['meta']['scene_id'] == 'test-scene-id'
        
        # Verify service calls
        mock_get_relationships.assert_called_once()

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.character_state_service.get_character_relationship')
    def test_get_character_relationship_success(self, mock_get_relationship, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful individual character relationship retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_relationship.return_value = {
            'character1': 'Character A',
            'character2': 'Character B',
            'relationship_type': 'friendly',
            'interaction_count': 5,
            'last_interaction': datetime.utcnow().isoformat(),
            'relationship_history': []
        }
        
        # Make request
        response = client.get('/api/character-plot/relationships/test-scene-id/Character A/Character B', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['character1'] == 'Character A'
        assert data['data']['character2'] == 'Character B'
        
        # Verify service calls
        mock_get_relationship.assert_called_once()

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.character_state_service.get_character_relationship')
    def test_get_character_relationship_not_found(self, mock_get_relationship, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test character relationship retrieval when relationship not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_relationship.return_value = None
        
        # Make request
        response = client.get('/api/character-plot/relationships/test-scene-id/Character A/Character B', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.character_state_service.analyze_character_relationship')
    def test_analyze_character_relationship_success(self, mock_analyze_relationship, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful character relationship analysis."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_analyze_relationship.return_value = {
            'character1': 'Character A',
            'character2': 'Character B',
            'analysis_type': 'all',
            'compatibility_score': 0.8,
            'conflict_potential': 0.2,
            'development_opportunities': ['More dialogue scenes'],
            'relationship_arc': 'developing_friendship'
        }
        
        # Make request
        response = client.post('/api/character-plot/relationships/test-scene-id/Character A/Character B/analyze', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'analysis_type': 'all',
                                  'context_depth': 10,
                                  'include_suggestions': True
                              }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['character1'] == 'Character A'
        assert data['data']['compatibility_score'] == 0.8
        
        # Verify service calls
        mock_analyze_relationship.assert_called_once()

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.character_state_service.detect_relationship_inconsistencies')
    def test_detect_relationship_inconsistencies_success(self, mock_detect_inconsistencies, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful relationship inconsistency detection."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_detect_inconsistencies.return_value = [
            {
                'character_pair': ['Character A', 'Character B'],
                'inconsistency_type': 'relationship_portrayal',
                'severity': 'medium',
                'description': 'Conflicting relationship dynamics',
                'suggested_resolution': 'Clarify relationship status'
            }
        ]
        
        # Make request
        response = client.post('/api/character-plot/relationships/test-scene-id/detect-inconsistencies', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'analysis_depth': 20,
                                  'severity_threshold': 'medium'
                              }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['character_pair'] == ['Character A', 'Character B']
        assert data['meta']['total_inconsistencies'] == 1
        
        # Verify service calls
        mock_detect_inconsistencies.assert_called_once()


class TestCharacterStateManagementAPI:
    """Test enhanced character state management API endpoints."""

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.character_state_service.get_character_profile')
    def test_get_character_profile_success(self, mock_get_profile, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful character profile retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_profile.return_value = {
            'character_name': 'Test Character',
            'scene_id': 'test-scene-id',
            'current_state': {
                'physical_state': {'health': 'healthy'},
                'emotional_state': {'mood': 'neutral'},
                'equipment': {'weapons': [], 'armor': []},
                'conditions': {'magical_effects': []},
                'location': 'Forest Clearing'
            },
            'relationships': [],
            'consistency_metrics': {
                'overall_score': 0.85,
                'voice_score': 0.9,
                'behavior_score': 0.8
            },
            'development_tracking': {
                'character_growth': 'steady',
                'arc_progression': 'developing'
            }
        }
        
        # Make request
        response = client.get('/api/character-plot/character-states/test-scene-id/Test Character/profile', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['character_name'] == 'Test Character'
        assert 'current_state' in data['data']
        assert 'relationships' in data['data']
        assert 'consistency_metrics' in data['data']
        
        # Verify service calls
        mock_get_profile.assert_called_once()

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.character_state_service.get_character_profile')
    def test_get_character_profile_not_found(self, mock_get_profile, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test character profile retrieval when profile not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_profile.return_value = None
        
        # Make request
        response = client.get('/api/character-plot/character-states/test-scene-id/Nonexistent Character/profile', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()


class TestCharacterPlotTrackingAPIIntegration:
    """Integration tests for the complete character and plot tracking API workflow."""

    @patch('app.api.character_plot_tracking.get_jwt_identity')
    @patch('app.api.character_plot_tracking.SceneService.get_scene')
    @patch('app.api.character_plot_tracking.PlotThread.find_by_scene')
    @patch('app.api.character_plot_tracking.character_state_service.get_scene_relationships')
    @patch('app.api.character_plot_tracking.character_state_service.check_character_consistency')
    def test_complete_workflow(self, mock_check_consistency, mock_get_relationships, mock_find_by_scene, mock_get_scene, mock_jwt, client, auth_headers, mock_scene, mock_plot_thread):
        """Test complete workflow: get plot threads, check consistency, analyze relationships."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_find_by_scene.return_value = [mock_plot_thread]
        mock_get_relationships.return_value = []
        mock_check_consistency.return_value = {
            'character_name': 'Test Character',
            'consistency_score': 0.85,
            'issues': []
        }
        
        # 1. Get plot threads
        threads_response = client.get('/api/character-plot/plot-threads/test-scene-id', headers=auth_headers)
        assert threads_response.status_code == 200
        
        # 2. Check character consistency
        consistency_response = client.post('/api/character-plot/character-consistency/test-scene-id/Test Character/check', 
                                          headers=auth_headers,
                                          data=json.dumps({'pose_text': 'Test pose'}))
        assert consistency_response.status_code == 200
        
        # 3. Get relationships
        relationships_response = client.get('/api/character-plot/relationships/test-scene-id', headers=auth_headers)
        assert relationships_response.status_code == 200
        
        # Verify all services were called
        mock_find_by_scene.assert_called_once()
        mock_check_consistency.assert_called_once()
        mock_get_relationships.assert_called_once()
        
        # Verify data consistency across responses
        threads_data = json.loads(threads_response.data)
        consistency_data = json.loads(consistency_response.data)
        relationships_data = json.loads(relationships_response.data)
        
        assert threads_data['success'] is True
        assert consistency_data['success'] is True
        assert relationships_data['success'] is True
        assert all(data['data'] for data in [threads_data, consistency_data, relationships_data])

    def test_health_check_success(self, client):
        """Test successful health check."""
        # Make request
        response = client.get('/api/character-plot/health')
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['service'] == 'character_plot_tracking_api'
        assert 'services' in data
        assert 'timestamp' in data 