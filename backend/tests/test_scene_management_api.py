"""
Integration tests for Scene Management API endpoints.

Tests all endpoints for scene history, search, summary generation,
and continuity analysis integration.
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import create_app
from app.models.scene import Scene, ScenePose, PoseType
from app.models.character import Character
from app.services.search_service import SearchResult
from app.services.summary_service import SceneSummary


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
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
def mock_pose():
    """Create a mock pose for testing."""
    pose = MagicMock()
    pose.id = 'test-pose-id'
    pose.character_id = 'test-character-id'
    pose.character_name = 'Test Character'
    pose.pose_text = 'Test pose text'
    pose.pose_type = PoseType.ACTION
    pose.timestamp = datetime.utcnow()
    pose.to_dict.return_value = {
        'id': 'test-pose-id',
        'character_id': 'test-character-id',
        'character_name': 'Test Character',
        'pose_text': 'Test pose text',
        'pose_type': 'action',
        'timestamp': pose.timestamp.isoformat()
    }
    return pose


class TestSceneHistoryAPI:
    """Test scene history API endpoints."""

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SceneService.get_scene')
    @patch('app.services.scene_management_service.SceneManagementService.get_scene_history')
    def test_get_scene_history_success(self, mock_get_history, mock_get_scene, mock_jwt, client, auth_headers, mock_scene, mock_pose):
        """Test successful scene history retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_history.return_value = [mock_pose]
        
        # Make request
        response = client.get('/api/scenes/test-scene-id/history', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == 'test-pose-id'
        assert data['meta']['scene_id'] == 'test-scene-id'
        assert data['meta']['total_poses'] == 1
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', user_id='test-user')
        mock_get_history.assert_called_once()

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SceneService.get_scene')
    def test_get_scene_history_not_found(self, mock_get_scene, mock_jwt, client, auth_headers):
        """Test scene history retrieval when scene not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = None
        
        # Make request
        response = client.get('/api/scenes/nonexistent-scene/history', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SceneService.get_scene')
    @patch('app.services.scene_management_service.SceneManagementService.get_scene_history')
    def test_get_scene_history_with_filters(self, mock_get_history, mock_get_scene, mock_jwt, client, auth_headers, mock_scene, mock_pose):
        """Test scene history retrieval with filters."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_history.return_value = [mock_pose]
        
        # Make request with filters
        response = client.get(
            '/api/scenes/test-scene-id/history?limit=50&include_ooc=false&character_id=test-character',
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['meta']['filters']['include_ooc'] is False
        assert data['meta']['filters']['character_id'] == 'test-character'
        assert data['meta']['limit'] == 50


class TestSceneSearchAPI:
    """Test scene search API endpoints."""

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SearchService.search_scenes')
    def test_search_scenes_success(self, mock_search, mock_jwt, client, auth_headers):
        """Test successful scene search."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_result = SearchResult(
            item_id='test-scene-id',
            item_type='scene',
            content_preview='Test scene content',
            relevance_score=0.8,
            timestamp=datetime.utcnow(),
            metadata={'name': 'Test Scene'}
        )
        mock_search.return_value = [mock_result]
        
        # Make request
        response = client.get('/api/scenes/search?q=test', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['item_id'] == 'test-scene-id'
        assert data['meta']['query'] == 'test'
        
        # Verify service calls
        mock_search.assert_called_once()

    @patch('app.api.scenes.get_jwt_identity')
    def test_search_scenes_missing_query(self, mock_jwt, client, auth_headers):
        """Test scene search with missing query parameter."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request without query
        response = client.get('/api/scenes/search', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'required' in data['message'].lower()

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SearchService.search_poses')
    def test_search_poses_success(self, mock_search, mock_jwt, client, auth_headers):
        """Test successful pose search within a scene."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_result = SearchResult(
            item_id='test-pose-id',
            item_type='pose',
            content_preview='Test pose content',
            relevance_score=0.9,
            timestamp=datetime.utcnow(),
            metadata={'character_name': 'Test Character'}
        )
        mock_search.return_value = [mock_result]
        
        # Make request
        response = client.get('/api/scenes/test-scene-id/search/poses?q=test', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['item_id'] == 'test-pose-id'
        assert data['meta']['scene_id'] == 'test-scene-id'
        
        # Verify service calls
        mock_search.assert_called_once()

    @patch('app.api.scenes.get_jwt_identity')
    def test_search_poses_missing_query(self, mock_jwt, client, auth_headers):
        """Test pose search with missing query parameter."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request without query
        response = client.get('/api/scenes/test-scene-id/search/poses', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'required' in data['message'].lower()


class TestSceneSummaryAPI:
    """Test scene summary generation API endpoints."""

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SummaryService.generate_summary')
    def test_generate_scene_summary_success(self, mock_generate, mock_jwt, client, auth_headers):
        """Test successful scene summary generation."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_summary = SceneSummary(
            scene_id='test-scene-id',
            summary_text='This is a test summary',
            summary_type='comprehensive',
            word_count=5,
            metadata={'scene_name': 'Test Scene'}
        )
        mock_generate.return_value = mock_summary
        
        # Make request
        response = client.post(
            '/api/scenes/test-scene-id/summary',
            headers=auth_headers,
            data=json.dumps({'summary_type': 'comprehensive'})
        )
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['summary_text'] == 'This is a test summary'
        assert data['data']['summary_type'] == 'comprehensive'
        
        # Verify service calls
        mock_generate.assert_called_once()

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SummaryService.generate_summary')
    def test_generate_scene_summary_not_found(self, mock_generate, mock_jwt, client, auth_headers):
        """Test scene summary generation when scene not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_generate.return_value = None
        
        # Make request
        response = client.post(
            '/api/scenes/nonexistent-scene/summary',
            headers=auth_headers,
            data=json.dumps({'summary_type': 'comprehensive'})
        )
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.scenes.get_jwt_identity')
    def test_generate_scene_summary_invalid_type(self, mock_jwt, client, auth_headers):
        """Test scene summary generation with invalid summary type."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with invalid type
        response = client.post(
            '/api/scenes/test-scene-id/summary',
            headers=auth_headers,
            data=json.dumps({'summary_type': 'invalid'})
        )
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid' in data['message'].lower()

    @patch('app.api.scenes.get_jwt_identity')
    def test_generate_scene_summary_character_missing_id(self, mock_jwt, client, auth_headers):
        """Test character-focused summary without character ID."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request for character summary without character_id
        response = client.post(
            '/api/scenes/test-scene-id/summary',
            headers=auth_headers,
            data=json.dumps({'summary_type': 'character'})
        )
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'character_id' in data['message'].lower()

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SummaryService.generate_catchup_brief')
    def test_generate_catchup_brief_success(self, mock_generate, mock_jwt, client, auth_headers):
        """Test successful catch-up brief generation."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_brief = SceneSummary(
            scene_id='test-scene-id',
            summary_text='This is a test catch-up brief',
            summary_type='catchup',
            word_count=6,
            metadata={'scene_name': 'Test Scene'}
        )
        mock_generate.return_value = mock_brief
        
        # Make request
        response = client.post(
            '/api/scenes/test-scene-id/summary/catchup',
            headers=auth_headers,
            data=json.dumps({'max_length': 300})
        )
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['summary_text'] == 'This is a test catch-up brief'
        assert data['data']['summary_type'] == 'catchup'
        
        # Verify service calls
        mock_generate.assert_called_once()

    @patch('app.api.scenes.get_jwt_identity')
    def test_generate_catchup_brief_invalid_timestamp(self, mock_jwt, client, auth_headers):
        """Test catch-up brief generation with invalid timestamp."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with invalid timestamp
        response = client.post(
            '/api/scenes/test-scene-id/summary/catchup',
            headers=auth_headers,
            data=json.dumps({'since_timestamp': 'invalid-timestamp'})
        )
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid' in data['message'].lower()


class TestContinuityAnalysisAPI:
    """Test continuity analysis API endpoints."""

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SceneService.get_scene')
    @patch('app.services.continuity_service.ContinuityService.analyze_pose_continuity')
    def test_analyze_pose_continuity_success(self, mock_analyze, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful pose continuity analysis."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_analyze.return_value = {
            'continuity_score': 0.8,
            'issues': [],
            'analysis_type': 'full'
        }
        
        # Make request
        response = client.post(
            '/api/scenes/test-scene-id/poses/test-pose-id/continuity',
            headers=auth_headers,
            data=json.dumps({
                'pose_text': 'Test pose',
                'character_id': 'test-character-id',
                'analysis_type': 'full'
            })
        )
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['continuity_score'] == 0.8
        assert data['data']['analysis_type'] == 'full'
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', user_id='test-user')
        mock_analyze.assert_called_once()

    @patch('app.api.scenes.get_jwt_identity')
    def test_analyze_pose_continuity_missing_fields(self, mock_jwt, client, auth_headers):
        """Test pose continuity analysis with missing required fields."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request without required fields
        response = client.post(
            '/api/scenes/test-scene-id/poses/test-pose-id/continuity',
            headers=auth_headers,
            data=json.dumps({'pose_text': 'Test pose'})
        )
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'required' in data['message'].lower()

    @patch('app.api.scenes.get_jwt_identity')
    def test_analyze_pose_continuity_invalid_type(self, mock_jwt, client, auth_headers):
        """Test pose continuity analysis with invalid analysis type."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with invalid analysis type
        response = client.post(
            '/api/scenes/test-scene-id/poses/test-pose-id/continuity',
            headers=auth_headers,
            data=json.dumps({
                'pose_text': 'Test pose',
                'character_id': 'test-character-id',
                'analysis_type': 'invalid'
            })
        )
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid' in data['message'].lower()

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SceneService.get_scene')
    @patch('app.services.continuity_service.ContinuityService.get_continuity_flags')
    def test_get_continuity_flags_success(self, mock_get_flags, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful continuity flags retrieval."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_flag = MagicMock()
        mock_flag.to_dict.return_value = {
            'id': 'test-flag-id',
            'flag_type': 'character_inconsistency',
            'severity': 'medium',
            'resolved': False
        }
        mock_get_flags.return_value = [mock_flag]
        
        # Make request
        response = client.get('/api/scenes/test-scene-id/continuity/flags', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == 'test-flag-id'
        assert data['meta']['scene_id'] == 'test-scene-id'
        
        # Verify service calls
        mock_get_scene.assert_called_once_with(scene_id='test-scene-id', user_id='test-user')
        mock_get_flags.assert_called_once()

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SceneService.get_scene')
    def test_get_continuity_flags_not_found(self, mock_get_scene, mock_jwt, client, auth_headers):
        """Test continuity flags retrieval when scene not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = None
        
        # Make request
        response = client.get('/api/scenes/nonexistent-scene/continuity/flags', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.services.continuity_service.ContinuityService.analyze_pose_continuity')
    @patch('app.api.scenes.SceneService.add_pose')
    def test_add_pose_with_continuity_success(self, mock_add_pose, mock_analyze, mock_jwt, client, auth_headers, mock_scene, mock_pose):
        """Test successful pose addition with continuity analysis."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_analyze.return_value = {
            'continuity_score': 0.9,
            'issues': [],
            'analysis_type': 'full'
        }
        mock_add_pose.return_value = (mock_scene, mock_pose)
        
        # Make request
        response = client.post(
            '/api/scenes/test-scene-id/poses',
            headers=auth_headers,
            data=json.dumps({
                'character_id': 'test-character-id',
                'character_name': 'Test Character',
                'pose_text': 'Test pose',
                'pose_type': 'action',
                'analyze_continuity': True
            })
        )
        
        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'scene' in data['data']
        assert 'pose' in data['data']
        assert 'continuity_analysis' in data['data']
        assert data['data']['continuity_analysis']['continuity_score'] == 0.9
        
        # Verify service calls
        mock_analyze.assert_called_once()
        mock_add_pose.assert_called_once()

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SceneService.add_pose')
    def test_add_pose_with_continuity_disabled(self, mock_add_pose, mock_jwt, client, auth_headers, mock_scene, mock_pose):
        """Test pose addition with continuity analysis disabled."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_add_pose.return_value = (mock_scene, mock_pose)
        
        # Make request
        response = client.post(
            '/api/scenes/test-scene-id/poses',
            headers=auth_headers,
            data=json.dumps({
                'character_id': 'test-character-id',
                'character_name': 'Test Character',
                'pose_text': 'Test pose',
                'pose_type': 'action',
                'analyze_continuity': False
            })
        )
        
        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'scene' in data['data']
        assert 'pose' in data['data']
        assert 'continuity_analysis' not in data['data']
        
        # Verify service calls
        mock_add_pose.assert_called_once()

    @patch('app.api.scenes.get_jwt_identity')
    def test_add_pose_with_continuity_missing_fields(self, mock_jwt, client, auth_headers):
        """Test pose addition with missing required fields."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request without required fields
        response = client.post(
            '/api/scenes/test-scene-id/poses',
            headers=auth_headers,
            data=json.dumps({
                'character_name': 'Test Character',
                'pose_text': 'Test pose'
            })
        )
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'missing' in data['message'].lower()

    @patch('app.api.scenes.get_jwt_identity')
    def test_add_pose_with_continuity_invalid_type(self, mock_jwt, client, auth_headers):
        """Test pose addition with invalid pose type."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with invalid pose type
        response = client.post(
            '/api/scenes/test-scene-id/poses',
            headers=auth_headers,
            data=json.dumps({
                'character_id': 'test-character-id',
                'character_name': 'Test Character',
                'pose_text': 'Test pose',
                'pose_type': 'invalid'
            })
        )
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid' in data['message'].lower()


class TestSceneManagementAPIIntegration:
    """Integration tests for the complete scene management API workflow."""

    @patch('app.api.scenes.get_jwt_identity')
    @patch('app.api.scenes.SceneService.get_scene')
    @patch('app.services.scene_management_service.SceneManagementService.get_scene_history')
    @patch('app.api.scenes.SearchService.search_scenes')
    @patch('app.api.scenes.SummaryService.generate_summary')
    def test_complete_workflow(self, mock_generate_summary, mock_search, mock_get_history, mock_get_scene, mock_jwt, client, auth_headers, mock_scene, mock_pose):
        """Test complete workflow: create scene, add poses, search, generate summary."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        mock_get_history.return_value = [mock_pose]
        
        mock_search_result = SearchResult(
            item_id='test-scene-id',
            item_type='scene',
            content_preview='Test scene content',
            relevance_score=0.8,
            timestamp=datetime.utcnow(),
            metadata={'name': 'Test Scene'}
        )
        mock_search.return_value = [mock_search_result]
        
        mock_summary = SceneSummary(
            scene_id='test-scene-id',
            summary_text='Complete workflow test summary',
            summary_type='comprehensive',
            word_count=4,
            metadata={'scene_name': 'Test Scene'}
        )
        mock_generate_summary.return_value = mock_summary
        
        # 1. Get scene history
        history_response = client.get('/api/scenes/test-scene-id/history', headers=auth_headers)
        assert history_response.status_code == 200
        
        # 2. Search scenes
        search_response = client.get('/api/scenes/search?q=test', headers=auth_headers)
        assert search_response.status_code == 200
        
        # 3. Generate summary
        summary_response = client.post(
            '/api/scenes/test-scene-id/summary',
            headers=auth_headers,
            data=json.dumps({'summary_type': 'comprehensive'})
        )
        assert summary_response.status_code == 200
        
        # Verify all services were called
        mock_get_history.assert_called_once()
        mock_search.assert_called_once()
        mock_generate_summary.assert_called_once() 