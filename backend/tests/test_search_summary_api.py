"""
Integration tests for Search and Summary API endpoints.

Tests all endpoints for scene search, pose search, character search, timeline search,
summary generation, and export functionality.
"""
import pytest
import json
import csv
import io
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import create_app
from app.models.scene import Scene
from app.models.character import Character
from app.services.search_service import SearchResult
from app.services.summary_service import SceneSummary, SummaryOptions


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
    scene.participants = []
    scene.to_dict.return_value = {
        'id': 'test-scene-id',
        'name': 'Test Scene',
        'description': 'A test scene',
        'created_by': 'test-user',
        'created_at': scene.created_at.isoformat(),
        'updated_at': scene.updated_at.isoformat(),
        'is_active': True,
        'poses': [],
        'participants': []
    }
    return scene


@pytest.fixture
def mock_search_result():
    """Create a mock search result for testing."""
    result = SearchResult(
        item_id='test-item-id',
        item_type='scene',
        content_preview='Test content preview',
        relevance_score=0.85,
        timestamp=datetime.utcnow(),
        metadata={
            'name': 'Test Scene',
            'description': 'A test scene',
            'created_by': 'test-user'
        }
    )
    return result


@pytest.fixture
def mock_scene_summary():
    """Create a mock scene summary for testing."""
    summary = SceneSummary(
        scene_id='test-scene-id',
        summary_text='This is a test scene summary',
        summary_type='comprehensive',
        metadata={
            'scene_name': 'Test Scene',
            'pose_count': 5,
            'character_count': 2
        }
    )
    return summary


class TestSceneSearchAPI:
    """Test scene search API endpoints."""

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.SearchService.search_scenes')
    def test_search_scenes_success(self, mock_search_scenes, mock_jwt, client, auth_headers, mock_search_result):
        """Test successful scene search."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_scenes.return_value = [mock_search_result]
        
        # Make request
        response = client.get('/api/search-summary/search/scenes?q=test+scene&limit=10', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['item_id'] == 'test-item-id'
        assert data['meta']['query'] == 'test scene'
        assert data['meta']['limit'] == 10
        
        # Verify service calls
        mock_search_scenes.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_scenes')
    def test_search_scenes_with_filters(self, mock_search_scenes, mock_jwt, client, auth_headers, mock_search_result):
        """Test scene search with filters."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_scenes.return_value = [mock_search_result]
        
        # Make request with filters
        response = client.get('/api/search-summary/search/scenes?q=test&active=true&start_date=2024-01-01T00:00:00Z&participants=char1,char2', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'filters' in data['meta']
        assert data['meta']['filters']['is_active'] is True
        
        # Verify service calls
        mock_search_scenes.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    def test_search_scenes_invalid_sort_field(self, mock_jwt, client, auth_headers):
        """Test scene search with invalid sort field."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with invalid sort field
        response = client.get('/api/search-summary/search/scenes?sort=invalid_field', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid sort field' in data['message'].lower()

    @patch('app.api.search_summary.get_jwt_identity')
    def test_search_scenes_invalid_date_format(self, mock_jwt, client, auth_headers):
        """Test scene search with invalid date format."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with invalid date format
        response = client.get('/api/search-summary/search/scenes?start_date=invalid-date', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid start_date format' in data['message'].lower()


class TestPoseSearchAPI:
    """Test pose search API endpoints."""

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_poses')
    def test_search_poses_success(self, mock_search_poses, mock_jwt, client, auth_headers, mock_search_result):
        """Test successful pose search."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_poses.return_value = [mock_search_result]
        
        # Make request
        response = client.get('/api/search-summary/search/poses?q=test+pose&scene_id=test-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['meta']['query'] == 'test pose'
        assert data['meta']['scene_id'] == 'test-scene-id'
        
        # Verify service calls
        mock_search_poses.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_poses')
    def test_search_poses_with_filters(self, mock_search_poses, mock_jwt, client, auth_headers, mock_search_result):
        """Test pose search with filters."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_poses.return_value = [mock_search_result]
        
        # Make request with filters
        response = client.get('/api/search-summary/search/poses?q=test&character_id=char1&pose_type=action&tags=combat,magic', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['meta']['character_id'] == 'char1'
        assert 'filters' in data['meta']
        
        # Verify service calls
        mock_search_poses.assert_called_once()


class TestCharacterSearchAPI:
    """Test character search API endpoints."""

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_characters')
    def test_search_characters_success(self, mock_search_characters, mock_jwt, client, auth_headers, mock_search_result):
        """Test successful character search."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_characters.return_value = [mock_search_result]
        
        # Make request
        response = client.get('/api/search-summary/search/characters?q=test+character', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['meta']['query'] == 'test character'
        
        # Verify service calls
        mock_search_characters.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_characters')
    def test_search_characters_with_scene_filter(self, mock_search_characters, mock_jwt, client, auth_headers, mock_search_result):
        """Test character search with scene filter."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_characters.return_value = [mock_search_result]
        
        # Make request with scene filter
        response = client.get('/api/search-summary/search/characters?q=test&scene_id=test-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['meta']['scene_id'] == 'test-scene-id'
        
        # Verify service calls
        mock_search_characters.assert_called_once()


class TestPlotElementSearchAPI:
    """Test plot element search API endpoints."""

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_plot_elements')
    def test_search_plot_elements_success(self, mock_search_plot_elements, mock_jwt, client, auth_headers, mock_search_result):
        """Test successful plot element search."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_plot_elements.return_value = [mock_search_result]
        
        # Make request
        response = client.get('/api/search-summary/search/plot-elements?q=test+plot&scene_id=test-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['meta']['query'] == 'test plot'
        assert data['meta']['scene_id'] == 'test-scene-id'
        
        # Verify service calls
        mock_search_plot_elements.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    def test_search_plot_elements_missing_query(self, mock_jwt, client, auth_headers):
        """Test plot element search with missing query."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request without query
        response = client.get('/api/search-summary/search/plot-elements?scene_id=test-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'query parameter q is required' in data['message']

    @patch('app.api.search_summary.get_jwt_identity')
    def test_search_plot_elements_missing_scene_id(self, mock_jwt, client, auth_headers):
        """Test plot element search with missing scene_id."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request without scene_id
        response = client.get('/api/search-summary/search/plot-elements?q=test', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'query parameter scene_id is required' in data['message']


class TestTimelineSearchAPI:
    """Test timeline search API endpoints."""

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_timeline')
    def test_search_timeline_success(self, mock_search_timeline, mock_jwt, client, auth_headers):
        """Test successful timeline search."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_timeline.return_value = [
            {
                'id': 'test-event-id',
                'type': 'pose',
                'timestamp': '2024-01-01T12:00:00Z',
                'title': 'Test Event',
                'content': 'Test event content',
                'character_name': 'Test Character'
            }
        ]
        
        # Make request
        response = client.get('/api/search-summary/search/timeline?q=test+event&scene_id=test-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == 'test-event-id'
        assert data['meta']['query'] == 'test event'
        assert data['meta']['scene_id'] == 'test-scene-id'
        
        # Verify service calls
        mock_search_timeline.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_timeline')
    def test_search_timeline_with_date_filters(self, mock_search_timeline, mock_jwt, client, auth_headers):
        """Test timeline search with date filters."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_timeline.return_value = []
        
        # Make request with date filters
        response = client.get('/api/search-summary/search/timeline?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['meta']['date_range']['start'] == '2024-01-01T00:00:00Z'
        assert data['meta']['date_range']['end'] == '2024-01-31T23:59:59Z'
        
        # Verify service calls
        mock_search_timeline.assert_called_once()


class TestSummaryGenerationAPI:
    """Test scene summary generation API endpoints."""

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.summary_service.generate_summary')
    def test_generate_scene_summary_success(self, mock_generate_summary, mock_jwt, client, auth_headers, mock_scene_summary):
        """Test successful scene summary generation."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_generate_summary.return_value = mock_scene_summary
        
        # Make request
        response = client.post('/api/search-summary/summaries/scenes/test-scene-id', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'focus': 'comprehensive',
                                  'max_length': 500,
                                  'include_details': True
                              }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['scene_id'] == 'test-scene-id'
        assert data['data']['summary_text'] == 'This is a test scene summary'
        assert data['data']['summary_type'] == 'comprehensive'
        
        # Verify service calls
        mock_generate_summary.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.summary_service.generate_summary')
    def test_generate_scene_summary_character_focus_missing_id(self, mock_generate_summary, mock_jwt, client, auth_headers):
        """Test scene summary generation with character focus but missing character_id."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with character focus but no character_id
        response = client.post('/api/search-summary/summaries/scenes/test-scene-id', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'focus': 'character',
                                  'max_length': 500
                              }))
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'character_id is required' in data['message']

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.summary_service.generate_summary')
    def test_generate_scene_summary_invalid_focus(self, mock_generate_summary, mock_jwt, client, auth_headers):
        """Test scene summary generation with invalid focus."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with invalid focus
        response = client.post('/api/search-summary/summaries/scenes/test-scene-id', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'focus': 'invalid_focus'
                              }))
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid focus value' in data['message'].lower()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.summary_service.generate_summary')
    def test_generate_scene_summary_not_found(self, mock_generate_summary, mock_jwt, client, auth_headers):
        """Test scene summary generation when scene not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_generate_summary.return_value = None
        
        # Make request
        response = client.post('/api/search-summary/summaries/scenes/nonexistent-scene-id', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'focus': 'comprehensive'
                              }))
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.summary_service.generate_catchup_brief')
    def test_generate_catchup_brief_success(self, mock_generate_catchup, mock_jwt, client, auth_headers, mock_scene_summary):
        """Test successful catchup brief generation."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_scene_summary.summary_type = 'catchup'
        mock_generate_catchup.return_value = mock_scene_summary
        
        # Make request
        response = client.post('/api/search-summary/summaries/scenes/test-scene-id/catchup', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'since_timestamp': '2024-01-01T00:00:00Z',
                                  'max_length': 300
                              }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['scene_id'] == 'test-scene-id'
        assert data['data']['summary_type'] == 'catchup'
        
        # Verify service calls
        mock_generate_catchup.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.summary_service.generate_character_focused_summary')
    def test_generate_character_summary_success(self, mock_generate_character, mock_jwt, client, auth_headers, mock_scene_summary):
        """Test successful character-focused summary generation."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_scene_summary.summary_type = 'character'
        mock_generate_character.return_value = mock_scene_summary
        
        # Make request
        response = client.post('/api/search-summary/summaries/scenes/test-scene-id/character/test-character-id', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'max_length': 400,
                                  'include_details': True
                              }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['scene_id'] == 'test-scene-id'
        assert data['data']['summary_type'] == 'character'
        assert data['data']['character_id'] == 'test-character-id'
        
        # Verify service calls
        mock_generate_character.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.summary_service.generate_summary')
    def test_generate_plot_summary_success(self, mock_generate_summary, mock_jwt, client, auth_headers, mock_scene_summary):
        """Test successful plot-focused summary generation."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_scene_summary.summary_type = 'plot'
        mock_generate_summary.return_value = mock_scene_summary
        
        # Make request
        response = client.post('/api/search-summary/summaries/scenes/test-scene-id/plot', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'max_length': 400,
                                  'chronological': True
                              }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['scene_id'] == 'test-scene-id'
        assert data['data']['summary_type'] == 'plot'
        
        # Verify service calls
        mock_generate_summary.assert_called_once()


class TestExportFunctionalityAPI:
    """Test export functionality API endpoints."""

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.SceneService.get_scene')
    def test_export_scene_data_json_success(self, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful scene data export in JSON format."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = mock_scene
        
        # Make request
        response = client.get('/api/search-summary/export/scenes/test-scene-id?format=json&include_poses=true', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['scene_id'] == 'test-scene-id'
        assert data['data']['name'] == 'Test Scene'
        
        # Verify service calls
        mock_get_scene.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.SceneService.get_scene')
    def test_export_scene_data_csv_success(self, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful scene data export in CSV format."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_scene.poses = [
            MagicMock(
                character_name='Test Character',
                character_id='test-char-id',
                pose_text='Test pose content',
                pose_type=MagicMock(value='action'),
                timestamp=datetime.utcnow(),
                tags=['test', 'action']
            )
        ]
        mock_get_scene.return_value = mock_scene
        
        # Make request
        response = client.get('/api/search-summary/export/scenes/test-scene-id?format=csv&include_poses=true', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        assert 'attachment; filename=scene_test-scene-id.csv' in response.headers['Content-Disposition']
        
        # Verify CSV content
        csv_content = response.data.decode('utf-8')
        assert 'Scene Name,Character Name,Character ID,Pose Text,Pose Type,Timestamp,Tags' in csv_content
        assert 'Test Scene,Test Character,test-char-id,Test pose content,action' in csv_content

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.SceneService.get_scene')
    def test_export_scene_data_txt_success(self, mock_get_scene, mock_jwt, client, auth_headers, mock_scene):
        """Test successful scene data export in TXT format."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_scene.poses = [
            MagicMock(
                character_name='Test Character',
                character_id='test-char-id',
                pose_text='Test pose content',
                pose_type=MagicMock(value='action'),
                timestamp=datetime.utcnow(),
                tags=['test', 'action']
            )
        ]
        mock_get_scene.return_value = mock_scene
        
        # Make request
        response = client.get('/api/search-summary/export/scenes/test-scene-id?format=txt&include_poses=true', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        assert response.mimetype == 'text/plain'
        assert 'attachment; filename=scene_test-scene-id.txt' in response.headers['Content-Disposition']
        
        # Verify TXT content
        txt_content = response.data.decode('utf-8')
        assert 'Scene: Test Scene' in txt_content
        assert 'Test Character (action)' in txt_content
        assert 'Test pose content' in txt_content

    @patch('app.api.search_summary.get_jwt_identity')
    def test_export_scene_data_invalid_format(self, mock_jwt, client, auth_headers):
        """Test scene data export with invalid format."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with invalid format
        response = client.get('/api/search-summary/export/scenes/test-scene-id?format=invalid', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid format' in data['message'].lower()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.SceneService.get_scene')
    def test_export_scene_data_not_found(self, mock_get_scene, mock_jwt, client, auth_headers):
        """Test scene data export when scene not found."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_get_scene.return_value = None
        
        # Make request
        response = client.get('/api/search-summary/export/scenes/nonexistent-scene-id', headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['message'].lower()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_scenes')
    def test_export_search_results_json_success(self, mock_search_scenes, mock_jwt, client, auth_headers, mock_search_result):
        """Test successful search results export in JSON format."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_scenes.return_value = [mock_search_result]
        
        # Make request
        response = client.post('/api/search-summary/export/search-results', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'search_type': 'scenes',
                                  'search_params': {
                                      'q': 'test scene',
                                      'limit': 10
                                  },
                                  'format': 'json'
                              }))
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['search_type'] == 'scenes'
        assert data['data']['total_results'] == 1
        assert len(data['data']['results']) == 1
        
        # Verify service calls
        mock_search_scenes.assert_called_once()

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_scenes')
    def test_export_search_results_csv_success(self, mock_search_scenes, mock_jwt, client, auth_headers, mock_search_result):
        """Test successful search results export in CSV format."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_scenes.return_value = [mock_search_result]
        
        # Make request
        response = client.post('/api/search-summary/export/search-results', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'search_type': 'scenes',
                                  'search_params': {
                                      'q': 'test scene',
                                      'limit': 10
                                  },
                                  'format': 'csv'
                              }))
        
        # Verify response
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        assert 'attachment; filename=scenes_search_results.csv' in response.headers['Content-Disposition']
        
        # Verify CSV content
        csv_content = response.data.decode('utf-8')
        assert 'Scene ID,Scene Name,Content Preview,Relevance Score,Timestamp,Created By' in csv_content

    @patch('app.api.search_summary.get_jwt_identity')
    def test_export_search_results_missing_search_type(self, mock_jwt, client, auth_headers):
        """Test search results export with missing search type."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request without search_type
        response = client.post('/api/search-summary/export/search-results', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'search_params': {
                                      'q': 'test'
                                  }
                              }))
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid search_type' in data['message'].lower()

    @patch('app.api.search_summary.get_jwt_identity')
    def test_export_search_results_invalid_format(self, mock_jwt, client, auth_headers):
        """Test search results export with invalid format."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        
        # Make request with invalid format
        response = client.post('/api/search-summary/export/search-results', 
                              headers=auth_headers,
                              data=json.dumps({
                                  'search_type': 'scenes',
                                  'search_params': {
                                      'q': 'test'
                                  },
                                  'format': 'invalid'
                              }))
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid format' in data['message'].lower()


class TestSearchSummaryAPIIntegration:
    """Integration tests for the complete search and summary API workflow."""

    @patch('app.api.search_summary.get_jwt_identity')
    @patch('app.api.search_summary.search_service.search_scenes')
    @patch('app.api.search_summary.summary_service.generate_summary')
    @patch('app.api.search_summary.SceneService.get_scene')
    def test_complete_workflow(self, mock_get_scene, mock_generate_summary, mock_search_scenes, mock_jwt, client, auth_headers, mock_scene, mock_search_result, mock_scene_summary):
        """Test complete workflow: search scenes, generate summary, export data."""
        # Setup mocks
        mock_jwt.return_value = 'test-user'
        mock_search_scenes.return_value = [mock_search_result]
        mock_generate_summary.return_value = mock_scene_summary
        mock_get_scene.return_value = mock_scene
        
        # 1. Search scenes
        search_response = client.get('/api/search-summary/search/scenes?q=test+scene', headers=auth_headers)
        assert search_response.status_code == 200
        
        # 2. Generate summary
        summary_response = client.post('/api/search-summary/summaries/scenes/test-scene-id', 
                                      headers=auth_headers,
                                      data=json.dumps({'focus': 'comprehensive'}))
        assert summary_response.status_code == 200
        
        # 3. Export scene data
        export_response = client.get('/api/search-summary/export/scenes/test-scene-id?format=json', headers=auth_headers)
        assert export_response.status_code == 200
        
        # Verify all services were called
        mock_search_scenes.assert_called_once()
        mock_generate_summary.assert_called_once()
        mock_get_scene.assert_called_once()
        
        # Verify data consistency across responses
        search_data = json.loads(search_response.data)
        summary_data = json.loads(summary_response.data)
        export_data = json.loads(export_response.data)
        
        assert search_data['success'] is True
        assert summary_data['success'] is True
        assert export_data['success'] is True
        assert summary_data['data']['scene_id'] == 'test-scene-id'
        assert export_data['data']['scene_id'] == 'test-scene-id'

    def test_health_check_success(self, client):
        """Test successful health check."""
        # Make request
        response = client.get('/api/search-summary/health')
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['service'] == 'search_summary_api'
        assert 'services' in data
        assert 'timestamp' in data 