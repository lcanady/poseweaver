import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, UTC
from app.models.scene import Scene, SceneHistoryLogEntry
from app.services.scene_service import SceneService
from app.services.context_service import ContextService

@pytest.fixture
def mock_ai_client():
    client = MagicMock()
    client.generate_completion.return_value = "The cold air of the forest began to bite as a sense of dread settled over the company."
    return client

@pytest.fixture
def sample_scene():
    return Scene(
        name="Test Scene",
        created_by="user123",
        description="A test scene",
        context={
            "setting": "A sunny meadow",
            "mood": "Peaceful",
            "active_characters": ["Alice", "Bob"],
            "recent_events": ["They arrived at the meadow"]
        }
    )

def test_generate_narrative_log_entry(mock_ai_client):
    service = ContextService(mock_ai_client)
    before = {"setting": "Meadow", "mood": "Peaceful"}
    after = {"setting": "Dark Forest", "mood": "Tense"}
    
    narrative = service.generate_narrative_log_entry(before, after, "Alice")
    
    assert narrative == "The cold air of the forest began to bite as a sense of dread settled over the company."
    mock_ai_client.generate_completion.assert_called_once()

@patch('app.models.scene.Scene.find_by_id')
@patch('app.models.scene.Scene.save')
@patch('app.services.ai_client.AIClient')
@patch('app.services.context_service.ContextService.generate_narrative_log_entry')
def test_scene_service_logging(mock_gen, mock_ai, mock_save, mock_find, sample_scene):
    # Setup mocks
    mock_find.return_value = sample_scene
    mock_gen.return_value = "The meadow's peace was shattered as shadows lengthened and the air grew cold."
    
    # Run the service method
    # Note: SceneService methods are static and use os.getenv and internal imports
    with patch('os.getenv', return_value='fake_key'):
        updated_scene = SceneService.update_scene_context(
            scene_id="scene123",
            user_id="user123",
            setting="A dark forest",
            mood="Tense"
        )
    
    assert updated_scene is not None
    assert len(updated_scene.history_log) == 1
    assert updated_scene.history_log[0].event_description == "The meadow's peace was shattered as shadows lengthened and the air grew cold."
    assert mock_save.called

def test_scene_history_log_entry_to_dict():
    entry = SceneHistoryLogEntry(
        event_description="Test event",
        character_name="Alice",
        timestamp=datetime(2023, 1, 1, 12, 0, 0)
    )
    
    data = entry.to_dict()
    assert data['event_description'] == "Test event"
    assert data['character_name'] == "Alice"
    assert data['timestamp'] == "2023-01-01T12:00:00"

def test_scene_history_log_entry_from_dict():
    data = {
        'event_description': "Test event",
        'character_name': "Alice",
        'timestamp': "2023-01-01T12:00:00"
    }
    
    entry = SceneHistoryLogEntry.from_dict(data)
    assert entry.event_description == "Test event"
    assert entry.character_name == "Alice"
    assert entry.timestamp == datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)

def test_scene_service_create_with_history():
    # Setup some initial history
    initial_history = [
        {"event_description": "Initial event 1", "timestamp": "2023-01-01T10:00:00Z"},
        {"event_description": "Initial event 2", "timestamp": "2023-01-01T11:00:00Z"}
    ]
    
    with patch('app.models.scene.Scene.save') as mock_save:
        with patch('app.models.character.Character.find_by_id', return_value=None):
            scene = SceneService.create_scene(
                name="New Scene with History",
                created_by="user123",
                initial_history_log=initial_history
            )
            
            assert len(scene.history_log) == 2
            assert scene.history_log[0].event_description == "Initial event 1"
            assert scene.history_log[1].event_description == "Initial event 2"
            # Verify the timestamps are parsed (UTC)
            assert scene.history_log[0].timestamp.hour == 10
