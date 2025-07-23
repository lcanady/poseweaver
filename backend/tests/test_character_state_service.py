"""
Tests for Character State Tracking Service.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.character_state_service import (
    CharacterStateService, StateChange, Interaction
)
from app.models.scene_memory import CharacterState, Pose, SceneMemory, PoseType
from app.services.venice_client import VeniceAPIError


class TestStateChange:
    """Test the StateChange data class."""
    
    def test_state_change_initialization(self):
        """Test StateChange can be initialized with all fields."""
        change = StateChange(
            character_name="Aria",
            change_type="physical",
            field="health",
            old_value="healthy",
            new_value="injured",
            confidence=0.8,
            description="Character was wounded in combat"
        )
        
        assert change.character_name == "Aria"
        assert change.change_type == "physical"
        assert change.field == "health"
        assert change.old_value == "healthy"
        assert change.new_value == "injured"
        assert change.confidence == 0.8
        assert "wounded in combat" in change.description
        assert isinstance(change.timestamp, datetime)
    
    def test_state_change_confidence_clamping(self):
        """Test confidence values are clamped between 0 and 1."""
        # Test upper bound
        change1 = StateChange("Aria", "physical", "health", None, "injured", confidence=1.5)
        assert change1.confidence == 1.0
        
        # Test lower bound
        change2 = StateChange("Aria", "physical", "health", None, "injured", confidence=-0.5)
        assert change2.confidence == 0.0
        
        # Test normal value
        change3 = StateChange("Aria", "physical", "health", None, "injured", confidence=0.7)
        assert change3.confidence == 0.7


class TestInteraction:
    """Test the Interaction data class."""
    
    def test_interaction_initialization(self):
        """Test Interaction can be initialized with all fields."""
        interaction = Interaction(
            character1="Aria",
            character2="Marcus",
            interaction_type="dialogue",
            description="Aria spoke to Marcus",
            timestamp=datetime.utcnow()
        )
        
        assert interaction.character1 == "Aria"
        assert interaction.character2 == "Marcus"
        assert interaction.interaction_type == "dialogue"
        assert "spoke to" in interaction.description
        assert isinstance(interaction.timestamp, datetime)
    
    def test_interaction_default_timestamp(self):
        """Test Interaction uses current time as default timestamp."""
        before = datetime.utcnow()
        interaction = Interaction("Aria", "Marcus", "dialogue")
        after = datetime.utcnow()
        
        assert before <= interaction.timestamp <= after


class TestCharacterStateService:
    """Test the CharacterStateService class."""
    
    @pytest.fixture
    def mock_venice_client(self):
        """Create a mock Venice client."""
        mock_client = Mock()
        return mock_client
    
    @pytest.fixture
    def character_state_service(self, mock_venice_client):
        """Create a CharacterStateService instance with mocked dependencies."""
        return CharacterStateService(venice_client=mock_venice_client)
    
    @pytest.fixture
    def character_state_service_no_ai(self):
        """Create a CharacterStateService instance without AI client."""
        return CharacterStateService(venice_client=None)
    
    @pytest.fixture
    def mock_scene(self):
        """Create a mock scene."""
        scene = Mock(spec=SceneMemory)
        scene.id = "test_scene_123"
        scene.name = "Test Scene"
        return scene
    
    @pytest.fixture
    def mock_character_state(self):
        """Create a mock character state."""
        state = Mock(spec=CharacterState)
        state.id = "test_state_123"
        state.scene_id = "test_scene_123"
        state.character_name = "Aria"
        state.physical_state = {
            'health': 'healthy',
            'injuries': [],
            'fatigue': 'rested',
            'condition': 'normal'
        }
        state.emotional_state = {
            'mood': 'neutral',
            'stress_level': 'low',
            'dominant_emotion': 'calm'
        }
        state.equipment = {
            'weapons': [],
            'armor': [],
            'items': [],
            'clothing': []
        }
        state.conditions = {
            'magical_effects': [],
            'status_conditions': [],
            'temporary_modifiers': []
        }
        state.location = 'tavern'
        return state
    
    @pytest.fixture
    def mock_pose(self):
        """Create a mock pose."""
        pose = Mock(spec=Pose)
        pose.id = "test_pose_123"
        pose.scene_id = "test_scene_123"
        pose.character_name = "Aria"
        pose.content = "Aria draws her sword and prepares for battle."
        pose.timestamp = datetime.utcnow()
        return pose
    
    def test_character_state_service_initialization(self, mock_venice_client):
        """Test CharacterStateService can be initialized."""
        service = CharacterStateService(venice_client=mock_venice_client)
        assert service.venice_client == mock_venice_client
    
    def test_character_state_service_initialization_no_ai(self):
        """Test CharacterStateService can be initialized without AI client."""
        service = CharacterStateService(venice_client=None)
        assert service.venice_client is None
    
    @patch('app.services.character_state_service.SceneMemory')
    @patch('app.services.character_state_service.CharacterState')
    def test_initialize_character_state_success(self, mock_character_state_class, 
                                               mock_scene_class, character_state_service,
                                               mock_scene):
        """Test successful character state initialization."""
        # Mock scene lookup
        mock_scene_class.find_by_id.return_value = mock_scene
        
        # Mock character state lookup (should return None for new character)
        mock_character_state_class.find_by_character.return_value = None
        
        # Mock character state creation
        mock_state_instance = Mock()
        mock_state_instance.save.return_value = "test_state_123"
        mock_character_state_class.return_value = mock_state_instance
        
        # Test initialization
        result = character_state_service.initialize_character_state(
            scene_id="test_scene_123",
            character_name="Aria"
        )
        
        # Verify scene lookup
        mock_scene_class.find_by_id.assert_called_once_with("test_scene_123")
        
        # Verify character state creation
        mock_character_state_class.assert_called_once()
        call_args = mock_character_state_class.call_args[1]
        assert call_args['scene_id'] == "test_scene_123"
        assert call_args['character_name'] == "Aria"
        assert 'physical_state' in call_args
        assert 'emotional_state' in call_args
        assert 'equipment' in call_args
        assert 'conditions' in call_args
        
        # Verify save was called
        mock_state_instance.save.assert_called_once()
        
        assert result == mock_state_instance
    
    @patch('app.services.character_state_service.SceneMemory')
    def test_initialize_character_state_scene_not_found(self, mock_scene_class,
                                                       character_state_service):
        """Test character state initialization fails when scene not found."""
        mock_scene_class.find_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Scene .* not found"):
            character_state_service.initialize_character_state(
                scene_id="nonexistent_scene",
                character_name="Aria"
            )
    
    @patch('app.services.character_state_service.SceneMemory')
    @patch('app.services.character_state_service.CharacterState')
    def test_initialize_character_state_already_exists(self, mock_character_state_class,
                                                      mock_scene_class, character_state_service,
                                                      mock_scene, mock_character_state):
        """Test character state initialization fails when state already exists."""
        mock_scene_class.find_by_id.return_value = mock_scene
        mock_character_state_class.find_by_character.return_value = mock_character_state
        
        with pytest.raises(ValueError, match="Character state .* already exists"):
            character_state_service.initialize_character_state(
                scene_id="test_scene_123",
                character_name="Aria"
            )
    
    @patch('app.services.character_state_service.CharacterState')
    def test_update_character_state_success(self, mock_character_state_class,
                                           character_state_service, mock_character_state):
        """Test successful character state update."""
        mock_character_state_class.find_by_character.return_value = mock_character_state
        
        updates = {
            'physical_state': {'health': 'injured'},
            'location': 'forest'
        }
        
        result = character_state_service.update_character_state(
            scene_id="test_scene_123",
            character_name="Aria",
            updates=updates
        )
        
        # Verify character state lookup
        mock_character_state_class.find_by_character.assert_called_once_with(
            "test_scene_123", "Aria"
        )
        
        # Verify update_state was called
        mock_character_state.update_state.assert_called_once_with(**updates)
        
        # Verify save was called
        mock_character_state.save.assert_called_once()
        
        assert result == mock_character_state
    
    @patch('app.services.character_state_service.CharacterState')
    def test_update_character_state_not_found(self, mock_character_state_class,
                                             character_state_service):
        """Test character state update fails when state not found."""
        mock_character_state_class.find_by_character.return_value = None
        
        with pytest.raises(ValueError, match="Character state .* not found"):
            character_state_service.update_character_state(
                scene_id="test_scene_123",
                character_name="Aria",
                updates={'location': 'forest'}
            )
    
    @patch('app.services.character_state_service.CharacterState')
    def test_get_character_current_state(self, mock_character_state_class,
                                        character_state_service, mock_character_state):
        """Test getting current character state."""
        mock_character_state_class.find_by_character.return_value = mock_character_state
        
        result = character_state_service.get_character_current_state(
            scene_id="test_scene_123",
            character_name="Aria"
        )
        
        mock_character_state_class.find_by_character.assert_called_once_with(
            "test_scene_123", "Aria"
        )
        assert result == mock_character_state
    
    def test_detect_state_changes_with_ai(self, character_state_service, mock_venice_client,
                                         mock_pose):
        """Test state change detection using AI."""
        # Mock AI response
        mock_ai_response = [
            {
                'change_type': 'equipment',
                'field': 'weapons',
                'new_value': 'sword',
                'confidence': 0.9,
                'description': 'Character drew a sword'
            },
            {
                'change_type': 'emotional',
                'field': 'dominant_emotion',
                'new_value': 'determined',
                'confidence': 0.7,
                'description': 'Character shows determination'
            }
        ]
        
        mock_venice_client.generate_completion.return_value = mock_ai_response
        
        result = character_state_service.detect_state_changes(mock_pose)
        
        # Verify AI was called
        mock_venice_client.generate_completion.assert_called_once()
        
        # Verify results
        assert len(result) == 2
        assert result[0].change_type == 'equipment'
        assert result[0].field == 'weapons'
        assert result[0].new_value == 'sword'
        assert result[0].confidence == 0.9
        assert result[1].change_type == 'emotional'
        assert result[1].field == 'dominant_emotion'
        assert result[1].new_value == 'determined'
        assert result[1].confidence == 0.7
    
    def test_detect_state_changes_ai_failure_fallback(self, character_state_service,
                                                     mock_venice_client, mock_pose):
        """Test state change detection falls back to patterns when AI fails."""
        # Mock AI failure
        mock_venice_client.generate_completion.side_effect = VeniceAPIError("API Error", 500)
        
        result = character_state_service.detect_state_changes(mock_pose)
        
        # Should still return results from pattern matching
        assert isinstance(result, list)
        # Should detect equipment change from "draws her sword"
        equipment_changes = [c for c in result if c.change_type == 'equipment']
        assert len(equipment_changes) > 0
    
    def test_detect_state_changes_pattern_matching(self, character_state_service_no_ai,
                                                  mock_pose):
        """Test state change detection using pattern matching."""
        result = character_state_service_no_ai.detect_state_changes(mock_pose)
        
        assert isinstance(result, list)
        
        # Should detect equipment change from "draws her sword"
        equipment_changes = [c for c in result if c.change_type == 'equipment']
        assert len(equipment_changes) > 0
        assert equipment_changes[0].field == 'items'
        assert 'sword' in equipment_changes[0].new_value
    
    def test_detect_state_changes_injury_patterns(self, character_state_service_no_ai):
        """Test detection of injury patterns."""
        pose = Mock(spec=Pose)
        pose.id = "test_pose"
        pose.character_name = "Aria"
        pose.content = "Aria is wounded and bleeding from the attack."
        
        result = character_state_service_no_ai.detect_state_changes(pose)
        
        # Should detect injury
        injury_changes = [c for c in result if c.change_type == 'physical']
        assert len(injury_changes) > 0
        assert injury_changes[0].field == 'injuries'
        assert injury_changes[0].new_value == 'injured'
    
    def test_detect_state_changes_emotion_patterns(self, character_state_service_no_ai):
        """Test detection of emotional state patterns."""
        pose = Mock(spec=Pose)
        pose.id = "test_pose"
        pose.character_name = "Aria"
        pose.content = "Aria becomes angry and furious at the insult."
        
        result = character_state_service_no_ai.detect_state_changes(pose)
        
        # Should detect emotion change
        emotion_changes = [c for c in result if c.change_type == 'emotional']
        assert len(emotion_changes) > 0
        assert emotion_changes[0].field == 'dominant_emotion'
        assert emotion_changes[0].new_value == 'angry'
    
    def test_detect_state_changes_location_patterns(self, character_state_service_no_ai):
        """Test detection of location change patterns."""
        pose = Mock(spec=Pose)
        pose.id = "test_pose"
        pose.character_name = "Aria"
        pose.content = "Aria moves to the forest and enters the clearing."
        
        result = character_state_service_no_ai.detect_state_changes(pose)
        
        # Should detect location changes
        location_changes = [c for c in result if c.change_type == 'location']
        assert len(location_changes) > 0
        # Should detect at least one location change
        locations = [c.new_value for c in location_changes]
        assert any(loc in ['forest', 'clearing'] for loc in locations)
    
    @patch('app.services.character_state_service.CharacterState')
    def test_track_character_relationships(self, mock_character_state_class,
                                          character_state_service, mock_character_state):
        """Test character relationship tracking."""
        # Mock character state lookup
        mock_character_state_class.find_by_character.return_value = mock_character_state
        
        interactions = [
            Interaction("Aria", "Marcus", "dialogue", "Aria spoke to Marcus"),
            Interaction("Aria", "Marcus", "cooperation", "Aria helped Marcus"),
            Interaction("Marcus", "Elena", "conflict", "Marcus argued with Elena")
        ]
        
        character_state_service.track_character_relationships(
            scene_id="test_scene_123",
            interactions=interactions
        )
        
        # Verify character states were looked up
        assert mock_character_state_class.find_by_character.call_count >= 2
        
        # Verify character state was saved (relationship updates)
        assert mock_character_state.save.call_count >= 2
    
    @patch('app.services.character_state_service.CharacterState')
    def test_get_character_states_for_scene(self, mock_character_state_class,
                                           character_state_service):
        """Test getting all character states for a scene."""
        mock_states = [Mock(), Mock(), Mock()]
        mock_character_state_class.find_by_scene.return_value = mock_states
        
        result = character_state_service.get_character_states_for_scene("test_scene_123")
        
        mock_character_state_class.find_by_scene.assert_called_once_with("test_scene_123")
        assert result == mock_states
    
    def test_apply_state_changes(self, character_state_service, mock_character_state):
        """Test applying state changes to character state."""
        changes = [
            StateChange("Aria", "physical", "health", "healthy", "injured", 0.8),
            StateChange("Aria", "location", "location", "tavern", "forest", 0.9),
            StateChange("Aria", "equipment", "weapons", [], "sword", 0.7)
        ]
        
        # Mock the get_character_current_state method to return our mock
        with patch.object(character_state_service, 'get_character_current_state') as mock_get:
            mock_get.return_value = mock_character_state
            
            # Mock the update method
            with patch.object(character_state_service, 'update_character_state') as mock_update:
                mock_update.return_value = mock_character_state
                
                result = character_state_service.apply_state_changes(
                    scene_id="test_scene_123",
                    character_name="Aria",
                    changes=changes
                )
                
                # Verify update was called with appropriate changes
                mock_update.assert_called_once()
                call_args = mock_update.call_args
                # The third argument (index 2) should be the updates dictionary
                updates_dict = call_args[0][2]  # positional args: scene_id, character_name, updates
                assert 'physical_state' in updates_dict
                assert 'location' in updates_dict
                assert 'equipment' in updates_dict
                
                assert result == mock_character_state
    
    def test_apply_state_changes_low_confidence_filtered(self, character_state_service,
                                                        mock_character_state):
        """Test that low confidence changes are filtered out."""
        with patch.object(character_state_service, 'get_character_current_state') as mock_get:
            mock_get.return_value = mock_character_state
            
            changes = [
                StateChange("Aria", "physical", "health", "healthy", "injured", 0.3),  # Low confidence
                StateChange("Aria", "location", "location", "tavern", "forest", 0.8)   # High confidence
            ]
            
            with patch.object(character_state_service, 'update_character_state') as mock_update:
                mock_update.return_value = mock_character_state
                
                character_state_service.apply_state_changes(
                    scene_id="test_scene_123",
                    character_name="Aria",
                    changes=changes
                )
                
                # Should only update with high confidence change
                mock_update.assert_called_once()
                call_args = mock_update.call_args
                # The third argument (index 2) should be the updates dictionary
                updates_dict = call_args[0][2]  # positional args: scene_id, character_name, updates
                assert 'location' in updates_dict
                assert 'physical_state' not in updates_dict
    
    def test_extract_interactions_from_pose(self, character_state_service):
        """Test extracting character interactions from pose content."""
        pose = Mock(spec=Pose)
        pose.character_name = "Aria"
        pose.content = "Aria says to Marcus, 'We need to help Elena fight the bandits.'"
        pose.timestamp = datetime.utcnow()
        
        # Mock character states in scene
        mock_states = [
            Mock(character_name="Aria"),
            Mock(character_name="Marcus"),
            Mock(character_name="Elena")
        ]
        
        with patch.object(character_state_service, 'get_character_states_for_scene') as mock_get:
            mock_get.return_value = mock_states
            
            result = character_state_service.extract_interactions_from_pose(
                pose, "test_scene_123"
            )
            
            # Should detect interactions with mentioned characters
            assert len(result) >= 1
            
            # Should detect dialogue with Marcus
            marcus_interactions = [i for i in result if i.character2 == "Marcus"]
            assert len(marcus_interactions) > 0
            assert marcus_interactions[0].interaction_type == "dialogue"
            
            # Should detect mention of Elena
            elena_interactions = [i for i in result if i.character2 == "Elena"]
            assert len(elena_interactions) > 0
    
    def test_extract_interactions_conflict_type(self, character_state_service):
        """Test extracting conflict-type interactions."""
        pose = Mock(spec=Pose)
        pose.character_name = "Aria"
        pose.content = "Aria attacks Marcus with her sword, striking at his armor."
        pose.timestamp = datetime.utcnow()
        
        mock_states = [
            Mock(character_name="Aria"),
            Mock(character_name="Marcus")
        ]
        
        with patch.object(character_state_service, 'get_character_states_for_scene') as mock_get:
            mock_get.return_value = mock_states
            
            result = character_state_service.extract_interactions_from_pose(
                pose, "test_scene_123"
            )
            
            # Should detect conflict interaction
            assert len(result) > 0
            assert result[0].interaction_type == "conflict"
            assert result[0].character2 == "Marcus"
    
    def test_extract_interactions_cooperation_type(self, character_state_service):
        """Test extracting cooperation-type interactions."""
        pose = Mock(spec=Pose)
        pose.character_name = "Aria"
        pose.content = "Aria helps Marcus lift the heavy stone, working together."
        pose.timestamp = datetime.utcnow()
        
        mock_states = [
            Mock(character_name="Aria"),
            Mock(character_name="Marcus")
        ]
        
        with patch.object(character_state_service, 'get_character_states_for_scene') as mock_get:
            mock_get.return_value = mock_states
            
            result = character_state_service.extract_interactions_from_pose(
                pose, "test_scene_123"
            )
            
            # Should detect cooperation interaction
            assert len(result) > 0
            assert result[0].interaction_type == "cooperation"
            assert result[0].character2 == "Marcus"