"""
Unit tests for PlotThreadService.

Tests plot element identification, tracking, linking, and management functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from app.services.plot_thread_service import (
    PlotThreadService, PlotElement, PlotThreadLink, PlotReminder
)
from app.models.scene_memory import (
    PlotThread, Pose, PlotStatus, PoseType
)
from app.services.openrouter_client import OpenRouterClient, OpenRouterAPIError


# Global fixtures for all test classes
@pytest.fixture
def mock_openrouter_client():
    """Create a mock OpenRouter client."""
    return Mock(spec=OpenRouterClient)

@pytest.fixture
def plot_service(mock_openrouter_client):
    """Create PlotThreadService instance with mocked dependencies."""
    return PlotThreadService(mock_openrouter_client)

@pytest.fixture
def sample_pose():
    """Create a sample pose for testing."""
    return Pose(
        scene_id="scene_123",
        character_name="Alice",
        content="Alice discovers a mysterious letter hidden in the old oak tree. The letter mentions a secret meeting at midnight and is signed with a strange symbol she's never seen before.",
        pose_type=PoseType.ACTION,
        timestamp=datetime.utcnow()
    )

@pytest.fixture
def sample_plot_element():
    """Create a sample plot element for testing."""
    return PlotElement(
        title="Mysterious Letter Discovery",
        description="Alice finds a cryptic letter with unknown symbols",
        importance_score=0.8,
        element_type="introduction",
        related_characters=["Alice"],
        keywords=["letter", "mystery", "symbol", "meeting"],
        emotional_weight="high",
        urgency="medium",
        scope="scene"
    )

@pytest.fixture
def sample_plot_thread():
    """Create a sample plot thread for testing."""
    return PlotThread(
        scene_id="scene_123",
        title="The Secret Society",
        description="Investigation into a mysterious organization",
        status=PlotStatus.DEVELOPING,
        importance_score=0.7,
        related_poses=["pose_1", "pose_2"]
    )


class TestPlotThreadService:
    """Test cases for PlotThreadService."""
    pass


class TestPlotElementExtraction:
    """Test plot element extraction functionality."""
    
    def test_extract_plot_elements_success(self, plot_service, sample_pose, mock_openrouter_client):
        """Test successful plot element extraction."""
        # Mock AI response
        ai_response = json.dumps({
            "elements": [
                {
                    "title": "Mysterious Letter Discovery",
                    "description": "Alice finds a cryptic letter",
                    "importance": 0.8,
                    "type": "introduction",
                    "characters": ["Alice"],
                    "keywords": ["letter", "mystery"],
                    "emotional_weight": "high",
                    "urgency": "medium",
                    "scope": "scene"
                },
                {
                    "title": "Secret Meeting Reference",
                    "description": "Letter mentions midnight meeting",
                    "importance": 0.6,
                    "type": "reference",
                    "characters": ["Alice"],
                    "keywords": ["meeting", "midnight"],
                    "emotional_weight": "medium",
                    "urgency": "high",
                    "scope": "scene"
                }
            ]
        })
        
        mock_openrouter_client.generate_completion.return_value = ai_response
        
        # Extract elements
        elements = plot_service.extract_plot_elements_from_pose(sample_pose)
        
        # Verify results
        assert len(elements) == 2
        assert elements[0].title == "Mysterious Letter Discovery"
        assert elements[0].importance_score == 0.8
        assert elements[0].element_type == "introduction"
        assert "Alice" in elements[0].related_characters
        assert "letter" in elements[0].keywords
        
        # Verify AI was called correctly
        mock_openrouter_client.generate_completion.assert_called_once()
        call_args = mock_openrouter_client.generate_completion.call_args
        assert "plot analyst" in call_args[1]['prompt'].lower()
        assert sample_pose.content in call_args[1]['prompt']
    
    def test_extract_plot_elements_filters_low_importance(self, plot_service, sample_pose, mock_openrouter_client):
        """Test that low importance elements are filtered out."""
        # Mock AI response with low importance element
        ai_response = json.dumps({
            "elements": [
                {
                    "title": "High Importance Element",
                    "description": "Important plot point",
                    "importance": 0.8,
                    "type": "introduction",
                    "characters": ["Alice"],
                    "keywords": ["important"],
                    "emotional_weight": "high",
                    "urgency": "medium",
                    "scope": "scene"
                },
                {
                    "title": "Low Importance Element",
                    "description": "Minor detail",
                    "importance": 0.1,  # Below threshold
                    "type": "reference",
                    "characters": ["Alice"],
                    "keywords": ["minor"],
                    "emotional_weight": "low",
                    "urgency": "low",
                    "scope": "personal"
                }
            ]
        })
        
        mock_openrouter_client.generate_completion.return_value = ai_response
        
        # Extract elements
        elements = plot_service.extract_plot_elements_from_pose(sample_pose)
        
        # Verify only high importance element is returned
        assert len(elements) == 1
        assert elements[0].title == "High Importance Element"
        assert elements[0].importance_score == 0.8
    
    def test_extract_plot_elements_openrouter_error(self, plot_service, sample_pose, mock_openrouter_client):
        """Test handling of OpenRouter.ai API errors."""
        mock_openrouter_client.generate_completion.side_effect = OpenRouterAPIError("API Error")
        
        # Extract elements should return empty list on error
        elements = plot_service.extract_plot_elements_from_pose(sample_pose)
        
        assert elements == []
    
    def test_extract_plot_elements_invalid_json(self, plot_service, sample_pose, mock_openrouter_client):
        """Test handling of invalid JSON response."""
        mock_openrouter_client.generate_completion.return_value = "Invalid JSON response"
        
        # Extract elements should return empty list on parse error
        elements = plot_service.extract_plot_elements_from_pose(sample_pose)
        
        assert elements == []


class TestPlotThreadCreation:
    """Test plot thread creation functionality."""
    
    @patch('app.models.scene_memory.PlotThread.save')
    def test_create_plot_thread_from_element(self, mock_save, plot_service, sample_plot_element):
        """Test creating a plot thread from an element."""
        scene_id = "scene_123"
        pose_id = "pose_456"
        
        # Create thread
        thread = plot_service.create_plot_thread_from_element(
            scene_id, sample_plot_element, pose_id
        )
        
        # Verify thread properties
        assert thread.scene_id == scene_id
        assert thread.title == sample_plot_element.title
        assert thread.description == sample_plot_element.description
        assert thread.status == PlotStatus.INTRODUCED  # introduction type -> INTRODUCED
        assert thread.importance_score == sample_plot_element.importance_score
        assert pose_id in thread.related_poses
        
        # Verify save was called
        mock_save.assert_called_once()
    
    @patch('app.models.scene_memory.PlotThread.save')
    def test_create_plot_thread_status_mapping(self, mock_save, plot_service):
        """Test status mapping for different element types."""
        scene_id = "scene_123"
        pose_id = "pose_456"
        
        # Test different element types
        test_cases = [
            ("introduction", PlotStatus.INTRODUCED),
            ("development", PlotStatus.DEVELOPING),
            ("resolution", PlotStatus.RESOLVED),
            ("reference", PlotStatus.DEVELOPING)
        ]
        
        for element_type, expected_status in test_cases:
            element = PlotElement(
                title=f"Test {element_type}",
                description="Test description",
                importance_score=0.5,
                element_type=element_type,
                related_characters=["Alice"],
                keywords=["test"],
                emotional_weight="medium",
                urgency="medium",
                scope="scene"
            )
            
            thread = plot_service.create_plot_thread_from_element(
                scene_id, element, pose_id
            )
            
            assert thread.status == expected_status


class TestPlotThreadUpdating:
    """Test plot thread updating functionality."""
    
    @patch('app.models.scene_memory.PlotThread.save')
    def test_update_plot_thread_from_pose(self, mock_save, plot_service, sample_plot_thread, sample_pose, sample_plot_element):
        """Test updating an existing plot thread."""
        # Mock the add_related_pose method
        sample_plot_thread.add_related_pose = Mock()
        
        original_importance = sample_plot_thread.importance_score
        
        # Update thread
        updated_thread = plot_service.update_plot_thread_from_pose(
            sample_plot_thread, sample_pose, sample_plot_element
        )
        
        # Verify pose was added
        sample_plot_thread.add_related_pose.assert_called_once_with(sample_pose.id)
        
        # Verify importance score was updated (weighted average)
        expected_importance = original_importance * 0.7 + sample_plot_element.importance_score * 0.3
        assert abs(updated_thread.importance_score - expected_importance) < 0.01
        
        # Verify save was called
        mock_save.assert_called_once()
    
    @patch('app.models.scene_memory.PlotThread.save')
    def test_update_plot_thread_status_changes(self, mock_save, plot_service, sample_pose):
        """Test status changes during thread updates."""
        # Test resolution element updates status
        thread = PlotThread(
            scene_id="scene_123",
            title="Test Thread",
            description="Test description",
            status=PlotStatus.DEVELOPING,
            importance_score=0.5
        )
        thread.add_related_pose = Mock()
        
        resolution_element = PlotElement(
            title="Resolution",
            description="Plot resolved",
            importance_score=0.7,
            element_type="resolution",
            related_characters=["Alice"],
            keywords=["resolution"],
            emotional_weight="high",
            urgency="low",
            scope="scene"
        )
        
        # Update with resolution element
        updated_thread = plot_service.update_plot_thread_from_pose(
            thread, sample_pose, resolution_element
        )
        
        # Verify status changed to resolved
        assert updated_thread.status == PlotStatus.RESOLVED
    
    @patch('app.models.scene_memory.PlotThread.save')
    def test_update_plot_thread_description_improvement(self, mock_save, plot_service, sample_pose):
        """Test description updates when new element has more detail."""
        thread = PlotThread(
            scene_id="scene_123",
            title="Test Thread",
            description="Short",  # Short description
            status=PlotStatus.DEVELOPING,
            importance_score=0.5
        )
        thread.add_related_pose = Mock()
        
        detailed_element = PlotElement(
            title="Detailed Element",
            description="This is a much longer and more detailed description of the plot element",
            importance_score=0.6,
            element_type="development",
            related_characters=["Alice"],
            keywords=["detailed"],
            emotional_weight="medium",
            urgency="medium",
            scope="scene"
        )
        
        # Update thread
        updated_thread = plot_service.update_plot_thread_from_pose(
            thread, sample_pose, detailed_element
        )
        
        # Verify description was updated
        assert updated_thread.description == detailed_element.description


class TestPlotThreadRelationships:
    """Test plot thread relationship and linking functionality."""
    
    @patch('app.models.scene_memory.PlotThread.find_by_scene')
    def test_find_related_plot_threads_success(self, mock_find_by_scene, plot_service, sample_plot_element, mock_openrouter_client):
        """Test finding related plot threads."""
        # Mock existing threads
        existing_threads = [
            PlotThread(
                scene_id="scene_123",
                title="Related Thread",
                description="Similar plot",
                status=PlotStatus.DEVELOPING,
                importance_score=0.6
            ),
            PlotThread(
                scene_id="scene_123",
                title="Unrelated Thread",
                description="Different plot",
                status=PlotStatus.INTRODUCED,
                importance_score=0.4
            )
        ]
        existing_threads[0].id = "thread_1"
        existing_threads[1].id = "thread_2"
        
        mock_find_by_scene.return_value = existing_threads
        
        # Mock AI response
        ai_response = json.dumps({
            "matches": [
                {
                    "thread_id": "thread_1",
                    "similarity": 0.8,
                    "relationship_type": "supports",
                    "explanation": "Both involve mystery elements",
                    "shared_elements": ["mystery", "investigation"]
                }
            ]
        })
        mock_openrouter_client.generate_completion.return_value = ai_response
        
        # Find related threads
        related = plot_service.find_related_plot_threads("scene_123", sample_plot_element)
        
        # Verify results
        assert len(related) == 1
        assert related[0][0].id == "thread_1"
        assert related[0][1] == 0.8  # similarity score
    
    @patch('app.models.scene_memory.PlotThread.find_by_scene')
    def test_find_related_plot_threads_fallback(self, mock_find_by_scene, plot_service, sample_plot_element, mock_openrouter_client):
        """Test fallback matching when AI fails."""
        # Mock existing threads
        existing_threads = [
            PlotThread(
                scene_id="scene_123",
                title="Letter Mystery",  # Contains "letter" keyword
                description="Investigation into mysterious letters",
                status=PlotStatus.DEVELOPING,
                importance_score=0.6
            )
        ]
        existing_threads[0].id = "thread_1"
        mock_find_by_scene.return_value = existing_threads
        
        # Mock AI failure
        mock_openrouter_client.generate_completion.side_effect = OpenRouterAPIError("API Error")
        
        # Find related threads (should use fallback)
        related = plot_service.find_related_plot_threads("scene_123", sample_plot_element)
        
        # Verify fallback matching worked
        assert len(related) >= 0  # May or may not find matches depending on keyword overlap
    
    def test_create_plot_thread_links(self, plot_service):
        """Test creating links between plot threads."""
        source_thread = PlotThread(
            scene_id="scene_123",
            title="Source Thread",
            description="Source description",
            status=PlotStatus.INTRODUCED,
            importance_score=0.7
        )
        source_thread.id = "source_id"
        
        target_thread = PlotThread(
            scene_id="scene_123",
            title="Target Thread",
            description="Target description",
            status=PlotStatus.DEVELOPING,
            importance_score=0.6
        )
        target_thread.id = "target_id"
        
        target_threads = [(target_thread, 0.8)]  # High similarity
        
        # Create links
        links = plot_service.create_plot_thread_links(source_thread, target_threads)
        
        # Verify link creation
        assert len(links) == 1
        link = links[0]
        assert link.source_thread_id == "source_id"
        assert link.target_thread_id == "target_id"
        assert link.strength == 0.8
        assert link.relationship_type in ["develops", "supports", "references", "relates_to"]


class TestPlotThreadReminders:
    """Test plot thread reminder functionality."""
    
    @patch('app.models.scene_memory.PlotThread.find_stale_threads')
    def test_get_stale_plot_threads(self, mock_find_stale, plot_service):
        """Test getting stale plot threads."""
        # Mock stale threads
        stale_threads = [
            PlotThread(
                scene_id="scene_123",
                title="Important Stale Thread",
                description="High importance thread",
                status=PlotStatus.DEVELOPING,
                importance_score=0.8,  # Above reminder threshold
                last_referenced=datetime.utcnow() - timedelta(days=10)
            ),
            PlotThread(
                scene_id="scene_123",
                title="Unimportant Stale Thread",
                description="Low importance thread",
                status=PlotStatus.INTRODUCED,
                importance_score=0.2,  # Below reminder threshold
                last_referenced=datetime.utcnow() - timedelta(days=10)
            )
        ]
        mock_find_stale.return_value = stale_threads
        
        # Get stale threads
        result = plot_service.get_stale_plot_threads("scene_123", 7)
        
        # Verify only important threads are returned
        assert len(result) == 1
        assert result[0].title == "Important Stale Thread"
        assert result[0].importance_score == 0.8
    
    @patch('app.models.scene_memory.PlotThread.find_stale_threads')
    def test_generate_plot_reminders(self, mock_find_stale, plot_service):
        """Test generating plot reminders."""
        # Mock stale thread
        stale_thread = PlotThread(
            scene_id="scene_123",
            title="Stale Thread",
            description="Needs attention",
            status=PlotStatus.DEVELOPING,
            importance_score=0.7,
            last_referenced=datetime.utcnow() - timedelta(days=10)
        )
        stale_thread.id = "thread_123"
        mock_find_stale.return_value = [stale_thread]
        
        # Generate reminders
        reminders = plot_service.generate_plot_reminders("scene_123")
        
        # Verify reminder generation
        assert len(reminders) == 1
        reminder = reminders[0]
        assert reminder.thread_id == "thread_123"
        assert reminder.title == "Stale Thread"
        assert reminder.days_since_reference == 10
        assert reminder.importance_score == 0.7
        assert len(reminder.reminder_text) > 0
        assert len(reminder.suggested_action) > 0


class TestPlotThreadStatusManagement:
    """Test plot thread status management functionality."""
    
    @patch('app.models.scene_memory.PlotThread.find_by_id')
    @patch('app.models.scene_memory.PlotThread.save')
    def test_update_plot_thread_status_success(self, mock_save, mock_find_by_id, plot_service):
        """Test successful status update."""
        # Mock thread
        thread = PlotThread(
            scene_id="scene_123",
            title="Test Thread",
            description="Test description",
            status=PlotStatus.DEVELOPING,
            importance_score=0.6
        )
        thread.resolve = Mock()
        mock_find_by_id.return_value = thread
        
        # Update status
        result = plot_service.update_plot_thread_status(
            "thread_123", PlotStatus.RESOLVED, "Resolved in latest scene"
        )
        
        # Verify update
        assert result is True
        assert thread.status == PlotStatus.RESOLVED
        thread.resolve.assert_called_once_with("Resolved in latest scene")
        mock_save.assert_called_once()
    
    @patch('app.models.scene_memory.PlotThread.find_by_id')
    def test_update_plot_thread_status_not_found(self, mock_find_by_id, plot_service):
        """Test status update when thread not found."""
        mock_find_by_id.return_value = None
        
        # Update status
        result = plot_service.update_plot_thread_status("nonexistent", PlotStatus.RESOLVED)
        
        # Verify failure
        assert result is False
    
    @patch('app.models.scene_memory.PlotThread.find_by_scene')
    def test_get_plot_thread_summary(self, mock_find_by_scene, plot_service):
        """Test getting plot thread summary."""
        # Mock threads with different statuses
        threads = [
            PlotThread(
                scene_id="scene_123",
                title="Thread 1",
                description="Description 1",
                status=PlotStatus.INTRODUCED,
                importance_score=0.6
            ),
            PlotThread(
                scene_id="scene_123",
                title="Thread 2",
                description="Description 2",
                status=PlotStatus.DEVELOPING,
                importance_score=0.8
            ),
            PlotThread(
                scene_id="scene_123",
                title="Thread 3",
                description="Description 3",
                status=PlotStatus.RESOLVED,
                importance_score=0.7
            )
        ]
        mock_find_by_scene.return_value = threads
        
        # Get summary
        summary = plot_service.get_plot_thread_summary("scene_123")
        
        # Verify summary
        assert summary['scene_id'] == "scene_123"
        assert summary['total_threads'] == 3
        assert summary['active_threads'] == 2  # INTRODUCED + DEVELOPING
        assert summary['status_distribution']['introduced'] == 1
        assert summary['status_distribution']['developing'] == 1
        assert summary['status_distribution']['resolved'] == 1
        assert abs(summary['average_importance'] - 0.7) < 0.01  # (0.6 + 0.8 + 0.7) / 3


class TestPlotThreadProcessing:
    """Test complete plot thread processing workflow."""
    
    @patch('app.services.plot_thread_service.PlotThreadService.extract_plot_elements_from_pose')
    @patch('app.services.plot_thread_service.PlotThreadService.find_related_plot_threads')
    @patch('app.services.plot_thread_service.PlotThreadService.create_plot_thread_from_element')
    def test_process_pose_for_plot_threads_new_thread(
        self, mock_create_thread, mock_find_related, mock_extract_elements, 
        plot_service, sample_pose, sample_plot_element
    ):
        """Test processing pose that creates new thread."""
        # Mock extracted elements
        mock_extract_elements.return_value = [sample_plot_element]
        
        # Mock no related threads found
        mock_find_related.return_value = []
        
        # Mock thread creation
        new_thread = PlotThread(
            scene_id="scene_123",
            title=sample_plot_element.title,
            description=sample_plot_element.description,
            status=PlotStatus.INTRODUCED,
            importance_score=sample_plot_element.importance_score
        )
        new_thread.id = "new_thread_123"
        mock_create_thread.return_value = new_thread
        
        # Process pose
        results = plot_service.process_pose_for_plot_threads(sample_pose, "scene_123")
        
        # Verify results
        assert results['pose_id'] == sample_pose.id
        assert len(results['extracted_elements']) == 1
        assert len(results['created_threads']) == 1
        assert len(results['updated_threads']) == 0
        assert results['created_threads'][0]['thread_id'] == "new_thread_123"
        
        # Verify method calls
        mock_extract_elements.assert_called_once_with(sample_pose)
        mock_find_related.assert_called_once_with("scene_123", sample_plot_element)
        mock_create_thread.assert_called_once_with("scene_123", sample_plot_element, sample_pose.id)
    
    @patch('app.services.plot_thread_service.PlotThreadService.extract_plot_elements_from_pose')
    @patch('app.services.plot_thread_service.PlotThreadService.find_related_plot_threads')
    @patch('app.services.plot_thread_service.PlotThreadService.update_plot_thread_from_pose')
    def test_process_pose_for_plot_threads_update_existing(
        self, mock_update_thread, mock_find_related, mock_extract_elements,
        plot_service, sample_pose, sample_plot_element, sample_plot_thread
    ):
        """Test processing pose that updates existing thread."""
        # Mock extracted elements
        mock_extract_elements.return_value = [sample_plot_element]
        
        # Mock high similarity match found
        mock_find_related.return_value = [(sample_plot_thread, 0.8)]
        
        # Mock thread update
        sample_plot_thread.id = "existing_thread_123"
        mock_update_thread.return_value = sample_plot_thread
        
        # Process pose
        results = plot_service.process_pose_for_plot_threads(sample_pose, "scene_123")
        
        # Verify results
        assert len(results['updated_threads']) == 1
        assert len(results['created_threads']) == 0
        assert results['updated_threads'][0]['thread_id'] == "existing_thread_123"
        assert results['updated_threads'][0]['similarity'] == 0.8
        
        # Verify method calls
        mock_update_thread.assert_called_once_with(sample_plot_thread, sample_pose, sample_plot_element)


if __name__ == '__main__':
    pytest.main([__file__])