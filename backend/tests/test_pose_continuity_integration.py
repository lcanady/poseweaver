"""
Integration tests for pose editor workflow with continuity features.

Tests the integration between:
- Pose enhancement
- Scene memory storage
- Continuity analysis
- Character state tracking
- Character profile integration

Requirements covered: 1.2, 2.1, 2.2, 6.1, 6.2 - Pose editor workflow integration
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.pose_service import PoseService, PoseEnhancement
from app.services.character_service import CharacterProfile
from app.services.context_service import PoseContext
from app.services.venice_client import VeniceClient
from app.services.scene_management_service import SceneManagementService
from app.services.continuity_service import ContinuityService, ContinuityAnalysis
from app.services.character_state_service import CharacterStateService
from app.models.scene_memory import SceneMemory, CharacterState, PoseType


class TestPoseEditorContinuityIntegration:
    """Test suite for pose editor continuity integration."""

    @pytest.fixture
    def mock_venice_client(self):
        """Create mock Venice client."""
        mock_client = Mock(spec=VeniceClient)
        
        # Mock character analysis response
        mock_client.extract_structured_data.return_value = {
            "name": "Test Character",
            "physical_description": "Tall warrior with dark hair",
            "personality_traits": ["brave", "loyal", "determined"],
            "background": "Former soldier turned adventurer",
            "goals": ["protect the innocent", "find redemption"],
            "relationships": {"Mentor": "respected teacher"},
            "skills": ["swordsmanship", "leadership", "tactics"],
            "speaking_style": "direct and confident"
        }
        
        # Mock continuity analysis response
        mock_client.generate_completion.return_value = json.dumps({
            "character_consistency": 0.85,
            "environment_consistency": 0.90,
            "plot_consistency": 0.78,
            "timeline_consistency": 0.95,
            "confidence": 0.87,
            "issues": [],
            "plot_elements": [
                {
                    "title": "Training session",
                    "description": "Character practices combat skills",
                    "importance": 0.6,
                    "type": "development",
                    "characters": ["Test Character"],
                    "keywords": ["training", "combat", "practice"]
                }
            ],
            "state_changes": [
                {
                    "character": "Test Character",
                    "type": "physical",
                    "description": "Became slightly fatigued from training",
                    "confidence": 0.7
                }
            ],
            "environment_changes": [],
            "notes": "Character behavior consistent with established personality"
        })
        
        return mock_client

    @pytest.fixture
    def character_profile(self):
        """Create test character profile."""
        return CharacterProfile(
            name="Test Character",
            background="A brave warrior with a troubled past who seeks redemption through heroic deeds.",
            personality=["brave", "loyal", "determined", "sometimes reckless"],
            skills=["swordsmanship", "leadership", "tactics", "survival"],
            goals=["protect the innocent", "find redemption", "defeat ancient evil"],
            relationships={"Mentor": "respected teacher", "Ally": "trusted companion"},
            voice_notes="Speaks with confidence and authority, uses military terminology"
        )

    @pytest.fixture
    def pose_context(self):
        """Create test pose context."""
        return PoseContext(
            actions=["combat training", "weapon practice"],
            emotions=["focused", "determined"],
            environmental_details=["training yard", "wooden practice dummies", "afternoon sun"],
            character_interactions=["solo training"],
            response_hooks=["completion of training session"],
            scene_timing="afternoon training period",
            urgency_level="low",
            narrative_tone="focused and determined"
        )

    @pytest.fixture
    def mock_scene_data(self):
        """Create mock scene data."""
        return {
            'scene_id': 'test-scene-123',
            'name': 'Training Ground Scene',
            'description': 'A scene in the castle training grounds',
            'owner_id': 'user-123'
        }

    def test_pose_enhancement_with_continuity_analysis(self, mock_venice_client, character_profile, pose_context):
        """Test basic pose enhancement with continuity analysis integration."""
        
        # Setup
        original_pose = "*practices sword forms in the training yard*"
        scene_id = "test-scene-123"
        character_name = "Test Character"
        
        with patch('app.services.scene_management_service.SceneManagementService'), \
             patch('app.services.continuity_service.ContinuityService'), \
             patch('app.services.character_state_service.CharacterStateService'), \
             patch('app.services.environment_state_service.EnvironmentStateService'):
            
            # Create pose service
            pose_service = PoseService(mock_venice_client)
            
            # Mock the basic enhancement
            basic_enhancement = PoseEnhancement(
                original_pose=original_pose,
                enhanced_pose="The warrior moved through the ancient sword forms with practiced precision, each movement flowing into the next as steel cut through the afternoon air in the training yard.",
                enhancement_notes=["Added sensory details", "Expanded on technique"],
                sensory_details=["steel cutting through air", "afternoon light"],
                character_voice_elements=["practiced precision", "warrior terminology"],
                narrative_techniques=["flowing description", "sensory engagement"]
            )
            
            pose_service.enhance_pose = Mock(return_value=basic_enhancement)
            
            # Mock continuity analysis
            mock_analysis = ContinuityAnalysis(
                pose_id="temp_analysis",
                character_consistency_score=0.85,
                environment_consistency_score=0.90,
                plot_consistency_score=0.78,
                timeline_consistency_score=0.95,
                overall_confidence=0.87,
                flags=[],
                extracted_plot_elements=[],
                character_state_changes=[{"character": "Test Character", "type": "physical", "description": "fatigue from training"}],
                environment_changes=[],
                analysis_notes="Character behavior consistent"
            )
            
            pose_service._perform_continuity_analysis = Mock(return_value=mock_analysis)
            
            # Execute
            result = pose_service.enhance_pose_with_continuity(
                original_pose=original_pose,
                scene_id=scene_id,
                character_name=character_name,
                character=character_profile,
                context=pose_context,
                enhancement_style="balanced",
                analyze_continuity=True
            )
            
            # Verify
            assert isinstance(result, PoseEnhancement)
            assert result.enhanced_pose == basic_enhancement.enhanced_pose
            assert result.continuity_analysis == mock_analysis
            assert result.continuity_flags_count == 0
            assert result.character_state_changes == [{"character": "Test Character", "type": "physical", "description": "fatigue from training"}]

    def test_pose_enhancement_with_continuity_warnings(self, mock_venice_client, character_profile):
        """Test pose enhancement with continuity warnings generation."""
        
        # Setup - pose that should trigger warnings
        original_pose = "*suddenly becomes a master wizard and casts powerful spells*"
        scene_id = "test-scene-123"
        character_name = "Test Character"
        
        with patch('app.services.scene_management_service.SceneManagementService'), \
             patch('app.services.continuity_service.ContinuityService'), \
             patch('app.services.character_state_service.CharacterStateService'), \
             patch('app.services.environment_state_service.EnvironmentStateService'):
            
            # Create pose service
            pose_service = PoseService(mock_venice_client)
            
            # Mock continuity analysis with low scores
            mock_analysis = ContinuityAnalysis(
                pose_id="temp_analysis",
                character_consistency_score=0.35,  # Low score should trigger warning
                environment_consistency_score=0.80,
                plot_consistency_score=0.40,  # Low score should trigger warning
                timeline_consistency_score=0.95,
                overall_confidence=0.60,
                flags=[],
                extracted_plot_elements=[],
                character_state_changes=[],
                environment_changes=[],
                analysis_notes="Character behavior inconsistent with established profile"
            )
            
            pose_service._perform_continuity_analysis = Mock(return_value=mock_analysis)
            
            # Mock the continuity-enabled enhancement
            basic_enhancement = PoseEnhancement(
                original_pose=original_pose,
                enhanced_pose="Enhanced pose with magic",
                enhancement_notes=["Added magical elements"],
                sensory_details=["magical energy"],
                character_voice_elements=["mystical terminology"],
                narrative_techniques=["magical description"]
            )
            
            pose_service.enhance_pose_with_continuity = Mock(return_value=basic_enhancement)
            
            # Execute
            result, warnings = pose_service.enhance_pose_with_pre_check(
                original_pose=original_pose,
                scene_id=scene_id,
                character_name=character_name,
                character=character_profile,
                enhancement_style="balanced",
                continuity_threshold=0.6
            )
            
            # Verify warnings were generated
            assert len(warnings) >= 2  # Should have character and plot consistency warnings
            assert any("Character consistency concern" in warning for warning in warnings)
            assert any("Plot consistency concern" in warning for warning in warnings)
            assert isinstance(result, PoseEnhancement)

    def test_character_profile_integration_with_scene_states(self, mock_venice_client, character_profile):
        """Test integration of character profiles with scene character states."""
        
        # Setup
        scene_id = "test-scene-123"
        character_name = "Test Character"
        
        with patch('app.models.scene_memory.SceneMemory') as mock_scene_memory, \
             patch('app.models.scene_memory.CharacterState') as mock_character_state:
            
            # Mock scene exists
            mock_scene = Mock()
            mock_scene_memory.find_by_id.return_value = mock_scene
            
            # Mock no existing character state
            mock_character_state.find_by_character.return_value = None
            
            # Mock character state creation
            mock_new_state = Mock()
            mock_new_state.save.return_value = "state-123"
            mock_character_state.return_value = mock_new_state
            
            # Create character state service
            char_state_service = CharacterStateService(mock_venice_client)
            
            # Execute
            result = char_state_service.initialize_character_state_from_profile(
                scene_id=scene_id,
                character_name=character_name,
                character_profile=character_profile
            )
            
            # Verify
            assert result == mock_new_state
            mock_character_state.assert_called_once()
            
            # Verify character state was created with data derived from profile
            call_args = mock_character_state.call_args
            assert call_args[1]['scene_id'] == scene_id
            assert call_args[1]['character_name'] == character_name
            assert 'physical_state' in call_args[1]
            assert 'emotional_state' in call_args[1]
            assert 'equipment' in call_args[1]
            assert 'conditions' in call_args[1]

    def test_scene_data_storage_integration(self, mock_venice_client, mock_scene_data):
        """Test automatic scene data storage during pose processing."""
        
        # Setup
        mush_output = """
        Training Yard
        You see practice dummies here.
        Test Character is here.
        
        Test Character practices sword forms with focused determination.
        """
        character_name = "Test Character"
        user_id = "user-123"
        
        with patch('app.services.scene_management_service.SceneManagementService') as mock_scene_service, \
             patch('app.services.data_extraction_service.DataExtractionService'), \
             patch('app.services.mush_parser_service.MushParserService'):
            
            # Create pose service
            pose_service = PoseService(mock_venice_client)
            
            # Mock scene creation
            mock_scene = Mock()
            mock_scene.id = mock_scene_data['scene_id']
            mock_scene_service_instance = Mock()
            mock_scene_service_instance.create_scene.return_value = mock_scene
            mock_scene_service.return_value = mock_scene_service_instance
            
            # Mock MUSH parsing result
            mock_parse_result = {
                'parsed_scene': {
                    'room_description': 'Training Yard with practice dummies',
                    'characters_present': ['Test Character'],
                    'poses': [
                        {
                            'character_name': 'Test Character',
                            'content': 'practices sword forms with focused determination',
                            'pose_type': 'action',
                            'is_ooc': False
                        }
                    ]
                },
                'your_poses': ['practices sword forms with focused determination'],
                'enhanced_poses': ['The warrior moved through ancient sword forms...'],
                'scene_context': 'Training session context'
            }
            
            pose_service.enhance_from_mush_output = Mock(return_value=mock_parse_result)
            
            # Execute (this would be called from the MUSH parser endpoint)
            # Simulating the scene storage workflow
            scene_management_service = SceneManagementService()
            
            # Create scene
            scene = scene_management_service.create_scene(
                name=mock_scene_data['name'],
                description=mock_scene_data['description'],
                owner_id=mock_scene_data['owner_id']
            )
            
            # Verify scene management service interaction
            mock_scene_service_instance.create_scene.assert_called_once_with(
                name=mock_scene_data['name'],
                description=mock_scene_data['description'],
                owner_id=mock_scene_data['owner_id']
            )

    def test_end_to_end_pose_workflow(self, mock_venice_client, character_profile, pose_context):
        """Test complete end-to-end pose enhancement workflow with continuity."""
        
        # Setup
        original_pose = "*trains with sword in the afternoon sun*"
        scene_id = "test-scene-123"
        character_name = "Test Character"
        
        with patch('app.services.scene_management_service.SceneManagementService') as mock_scene_mgmt, \
             patch('app.services.continuity_service.ContinuityService') as mock_continuity, \
             patch('app.services.character_state_service.CharacterStateService') as mock_char_state, \
             patch('app.services.environment_state_service.EnvironmentStateService') as mock_env_state:
            
            # Create pose service
            pose_service = PoseService(mock_venice_client)
            
            # Mock all service responses
            mock_scene_mgmt_instance = Mock()
            mock_scene_mgmt.return_value = mock_scene_mgmt_instance
            
            mock_continuity_instance = Mock()
            mock_continuity.return_value = mock_continuity_instance
            
            mock_char_state_instance = Mock()
            mock_char_state.return_value = mock_char_state_instance
            
            mock_env_state_instance = Mock()
            mock_env_state.return_value = mock_env_state_instance
            
            # Mock enhance_pose method to return realistic data
            enhanced_pose_text = ("The seasoned warrior moved through the time-honored sword forms with practiced "
                                 "grace, each movement flowing seamlessly into the next as sunlight gleamed off the "
                                 "polished steel blade in the castle's training yard.")
            
            basic_enhancement = PoseEnhancement(
                original_pose=original_pose,
                enhanced_pose=enhanced_pose_text,
                enhancement_notes=["Expanded basic action", "Added sensory details", "Enhanced flow"],
                sensory_details=["sunlight on steel", "flowing movements", "practiced grace"],
                character_voice_elements=["seasoned warrior", "time-honored forms"],
                narrative_techniques=["sensory description", "flowing narrative"]
            )
            
            pose_service.enhance_pose = Mock(return_value=basic_enhancement)
            
            # Mock continuity analysis
            continuity_result = ContinuityAnalysis(
                pose_id="temp_analysis",
                character_consistency_score=0.90,
                environment_consistency_score=0.85,
                plot_consistency_score=0.88,
                timeline_consistency_score=0.95,
                overall_confidence=0.89,
                flags=[],
                extracted_plot_elements=[],
                character_state_changes=[
                    {"character": "Test Character", "type": "physical", "description": "slight fatigue from training"}
                ],
                environment_changes=[],
                analysis_notes="Excellent consistency with established character and environment"
            )
            
            pose_service._perform_continuity_analysis = Mock(return_value=continuity_result)
            
            # Execute complete workflow
            result = pose_service.enhance_pose_with_continuity(
                original_pose=original_pose,
                scene_id=scene_id,
                character_name=character_name,
                character=character_profile,
                context=pose_context,
                enhancement_style="balanced",
                analyze_continuity=True
            )
            
            # Verify complete integration
            assert isinstance(result, PoseEnhancement)
            assert result.enhanced_pose == enhanced_pose_text
            assert result.continuity_analysis == continuity_result
            assert len(result.character_state_changes) == 1
            assert result.continuity_flags_count == 0
            assert result.continuity_analysis.overall_confidence > 0.8

    def test_error_handling_in_integrated_workflow(self, mock_venice_client, character_profile):
        """Test error handling when continuity services fail."""
        
        # Setup
        original_pose = "*attempts some action*"
        scene_id = "test-scene-123"
        character_name = "Test Character"
        
        with patch('app.services.scene_management_service.SceneManagementService'), \
             patch('app.services.continuity_service.ContinuityService'), \
             patch('app.services.character_state_service.CharacterStateService'), \
             patch('app.services.environment_state_service.EnvironmentStateService'):
            
            # Create pose service
            pose_service = PoseService(mock_venice_client)
            
            # Mock basic enhancement to work
            basic_enhancement = PoseEnhancement(
                original_pose=original_pose,
                enhanced_pose="Enhanced pose text",
                enhancement_notes=["Enhanced action"],
                sensory_details=["action details"],
                character_voice_elements=["character voice"],
                narrative_techniques=["narrative flow"]
            )
            
            pose_service.enhance_pose = Mock(return_value=basic_enhancement)
            
            # Mock continuity analysis to fail
            pose_service._perform_continuity_analysis = Mock(side_effect=Exception("Continuity service error"))
            
            # Execute - should handle error gracefully
            result = pose_service.enhance_pose_with_continuity(
                original_pose=original_pose,
                scene_id=scene_id,
                character_name=character_name,
                character=character_profile,
                enhancement_style="balanced",
                analyze_continuity=True
            )
            
            # Verify graceful degradation
            assert isinstance(result, PoseEnhancement)
            assert result.enhanced_pose == basic_enhancement.enhanced_pose
            assert result.continuity_analysis is None  # Should be None when analysis fails
            assert result.continuity_flags_count == 0

    def test_character_state_derivation_from_profile(self, mock_venice_client):
        """Test deriving character state from character profile data."""
        
        # Setup - warrior character
        warrior_profile = CharacterProfile(
            name="Warrior Test",
            background="A battle-hardened veteran of many wars, trained in martial combat.",
            personality=["brave", "disciplined", "loyal"],
            skills=["swordsmanship", "tactics", "leadership", "survival"],
            goals=["protect allies", "defeat enemies"],
            relationships={"Commander": "respected superior"},
            voice_notes="Speaks with military precision"
        )
        
        # Setup - mage character
        mage_profile = CharacterProfile(
            name="Mage Test",
            background="A scholar of arcane arts who studied magic at the great academy.",
            personality=["intelligent", "curious", "cautious"],
            skills=["spellcasting", "research", "alchemy", "ancient languages"],
            goals=["master magic", "discover secrets"],
            relationships={"Mentor": "wise teacher"},
            voice_notes="Speaks with scholarly precision"
        )
        
        with patch('app.models.scene_memory.SceneMemory') as mock_scene_memory, \
             patch('app.models.scene_memory.CharacterState') as mock_character_state:
            
            # Mock scene exists
            mock_scene = Mock()
            mock_scene_memory.find_by_id.return_value = mock_scene
            
            # Mock no existing character state
            mock_character_state.find_by_character.return_value = None
            
            # Create character state service
            char_state_service = CharacterStateService(mock_venice_client)
            
            # Test warrior state derivation
            warrior_state = char_state_service._derive_state_from_profile(warrior_profile)
            
            # Verify warrior gets combat-ready condition
            assert warrior_state['physical_state']['condition'] == 'combat-ready'
            assert 'combat weapon' in warrior_state['equipment']['weapons']
            assert 'protective gear' in warrior_state['equipment']['armor']
            
            # Test mage state derivation
            mage_state = char_state_service._derive_state_from_profile(mage_profile)
            
            # Verify mage gets magical equipment and condition
            assert 'magically attuned' in mage_state['conditions']['status_conditions']
            assert 'magical focus' in mage_state['equipment']['items']
            assert 'spell components' in mage_state['equipment']['items'] 