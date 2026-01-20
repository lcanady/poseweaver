"""
Integration tests for Environment State Service.

Tests the complete workflow of environmental tracking and consistency checking
in realistic scenarios.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json

from app.services.environment_state_service import EnvironmentStateService
from app.models.scene_memory import EnvironmentState, Pose, PoseType, ContinuityFlag, FlagType
from app.services.openrouter_client import OpenRouterClient


class TestEnvironmentStateIntegration:
    """Integration tests for complete environment state workflows."""
    
    @pytest.fixture
    def mock_openrouter_client(self):
        """Create a mock OpenRouter client with realistic responses."""
        client = Mock(spec=OpenRouterClient)
        return client
    
    @pytest.fixture
    def environment_service(self, mock_openrouter_client):
        """Create EnvironmentStateService with mock OpenRouter client."""
        return EnvironmentStateService(openrouter_client=mock_openrouter_client)
    
    def test_complete_environment_tracking_workflow(self, environment_service):
        """Test complete workflow from pose to environment tracking."""
        scene_id = "test_scene_123"
        
        # First pose establishes the environment
        first_pose = Pose(
            scene_id=scene_id,
            character_name="Aria",
            content="Aria steps into the dimly lit tavern, rain pattering against the windows as the evening settles in.",
            pose_type=PoseType.NARRATIVE,
            timestamp=datetime.utcnow()
        )
        
        # Mock AI response for first pose (establishing environment)
        environment_service.openrouter_client.generate_completion.return_value = json.dumps({
            "location_name": "tavern",
            "weather": {"condition": "rainy", "intensity": "light"},
            "time_context": {"time_of_day": "evening"},
            "lighting": "dim",
            "sounds": "rain pattering",
            "atmosphere": "cozy"
        })
        
        # Mock database operations
        with patch.object(EnvironmentState, 'save', return_value="env_123"):
            with patch.object(ContinuityFlag, 'save', return_value="flag_123"):
                # Process first pose - should create initial environment
                env, flags = environment_service.process_pose_for_environment(first_pose, scene_id)
                
                assert env is not None
                assert env.location_name == "tavern"
                assert env.weather["condition"] == "rainy"
                assert env.time_context["time_of_day"] == "evening"
                assert len(flags) == 0  # No inconsistencies in first pose
        
        # Second pose with consistent environment
        second_pose = Pose(
            scene_id=scene_id,
            character_name="Bran",
            content="Bran shakes the rain from his cloak as he enters the warm tavern, grateful to escape the evening drizzle.",
            pose_type=PoseType.NARRATIVE,
            timestamp=datetime.utcnow()
        )
        
        # Mock AI responses for consistency check and extraction
        def mock_ai_response(prompt=None, system_message=None, **kwargs):
            if "consistency" in system_message.lower():
                return json.dumps({
                    "is_consistent": True,
                    "conflicts": [],
                    "confidence_score": 0.9,
                    "details": "Environment is consistent with established setting"
                })
            else:
                return json.dumps({
                    "location_name": "tavern",
                    "weather": {"condition": "rainy"},
                    "atmosphere": "warm"
                })
        
        environment_service.openrouter_client.generate_completion.side_effect = mock_ai_response
        
        # Mock getting current environment
        with patch.object(environment_service, 'get_current_environment', return_value=env):
            # Process second pose - should be consistent
            env2, flags2 = environment_service.process_pose_for_environment(second_pose, scene_id)
            
            assert env2 == env  # Same environment
            assert len(flags2) == 0  # No inconsistencies
    
    def test_environment_inconsistency_detection(self, environment_service):
        """Test detection and flagging of environmental inconsistencies."""
        scene_id = "test_scene_123"
        
        # Established environment (rainy evening tavern)
        established_env = EnvironmentState(
            scene_id=scene_id,
            location_name="The Rusty Anchor Tavern",
            description="A cozy tavern with wooden tables",
            weather={"condition": "rainy", "intensity": "heavy"},
            time_context={"time_of_day": "evening"},
            physical_details={"lighting": "dim", "atmosphere": "cozy"}
        )
        
        # Inconsistent pose (mentions sunny weather)
        inconsistent_pose = Pose(
            scene_id=scene_id,
            character_name="Clara",
            content="Clara squints against the bright sunlight streaming through the tavern windows, enjoying the warm afternoon.",
            pose_type=PoseType.NARRATIVE,
            timestamp=datetime.utcnow()
        )
        
        # Mock AI response indicating inconsistency
        def mock_ai_response(prompt=None, system_message=None, **kwargs):
            if "consistency" in system_message.lower():
                return json.dumps({
                    "is_consistent": False,
                    "conflicts": [
                        {
                            "type": "weather",
                            "description": "Weather condition contradiction",
                            "established": "rainy",
                            "conflicting": "sunny",
                            "severity": "high"
                        },
                        {
                            "type": "time",
                            "description": "Time of day mismatch",
                            "established": "evening",
                            "conflicting": "afternoon",
                            "severity": "medium"
                        }
                    ],
                    "confidence_score": 0.85,
                    "details": "Multiple environmental inconsistencies detected"
                })
            else:
                return json.dumps({
                    "weather": {"condition": "sunny"},
                    "time_context": {"time_of_day": "afternoon"},
                    "lighting": "bright"
                })
        
        environment_service.openrouter_client.generate_completion.side_effect = mock_ai_response
        
        # Mock database operations
        with patch.object(environment_service, 'get_current_environment', return_value=established_env):
            with patch.object(ContinuityFlag, 'save', return_value="flag_123"):
                # Process inconsistent pose
                env, flags = environment_service.process_pose_for_environment(inconsistent_pose, scene_id)
                
                assert env == established_env  # Environment unchanged
                assert len(flags) == 2  # Two inconsistency flags created
                
                # Check flag details
                weather_flag = flags[0]
                assert weather_flag.flag_type == FlagType.ENVIRONMENT_CONTRADICTION
                assert "Weather condition contradiction" in weather_flag.description
                assert weather_flag.confidence_score == 0.85
                
                time_flag = flags[1]
                assert time_flag.flag_type == FlagType.ENVIRONMENT_CONTRADICTION
                assert "Time of day mismatch" in time_flag.description
    
    def test_location_change_workflow(self, environment_service):
        """Test workflow when characters move to a new location."""
        scene_id = "test_scene_123"
        
        # Established environment (tavern)
        tavern_env = EnvironmentState(
            scene_id=scene_id,
            location_name="The Rusty Anchor Tavern",
            weather={"condition": "rainy"},
            time_context={"time_of_day": "evening"}
        )
        
        # Pose indicating location change
        location_change_pose = Pose(
            scene_id=scene_id,
            character_name="Derek",
            content="Derek pushes through the tavern door and steps out into the cobblestone marketplace, the rain having stopped and stars beginning to appear in the night sky.",
            pose_type=PoseType.NARRATIVE,
            timestamp=datetime.utcnow()
        )
        
        # Mock AI response for location change
        environment_service.openrouter_client.generate_completion.return_value = json.dumps({
            "location_name": "marketplace",
            "weather": {"condition": "clear"},
            "time_context": {"time_of_day": "night"},
            "physical_features": ["cobblestone", "open space"],
            "lighting": "starlight"
        })
        
        # Mock database operations
        with patch.object(environment_service, 'get_current_environment', return_value=tavern_env):
            with patch.object(EnvironmentState, 'save', return_value="env_456"):
                # Process location change pose
                new_env, flags = environment_service.process_pose_for_environment(location_change_pose, scene_id)
                
                assert new_env is not None
                assert new_env.location_name == "marketplace"
                assert new_env.weather["condition"] == "clear"
                assert new_env.time_context["time_of_day"] == "night"
                assert "cobblestone" in new_env.physical_details.get("physical_features", [])
                assert len(flags) == 0  # No inconsistencies for location change
    
    def test_gradual_environment_evolution(self, environment_service):
        """Test gradual evolution of environment through multiple poses."""
        scene_id = "test_scene_123"
        
        # Initial environment
        initial_env = EnvironmentState(
            scene_id=scene_id,
            location_name="forest clearing",
            weather={"condition": "overcast"},
            time_context={"time_of_day": "morning"},
            physical_details={"lighting": "dim"}
        )
        
        # Pose that adds weather details
        weather_pose = Pose(
            scene_id=scene_id,
            character_name="Elena",
            content="Elena notices the first drops of rain beginning to fall, darkening the forest floor around the clearing.",
            pose_type=PoseType.NARRATIVE
        )
        
        # Mock AI response for weather update
        def mock_weather_response(prompt=None, system_message=None, **kwargs):
            if "consistency" in system_message.lower():
                return json.dumps({
                    "is_consistent": True,
                    "conflicts": [],
                    "confidence_score": 0.9
                })
            else:
                return json.dumps({
                    "weather": {"condition": "light rain", "intensity": "beginning"},
                    "physical_details": {"ground": "darkening"}
                })
        
        environment_service.openrouter_client.generate_completion.side_effect = mock_weather_response
        
        # Mock database operations
        with patch.object(environment_service, 'get_current_environment', return_value=initial_env):
            with patch.object(EnvironmentState, 'find_by_scene', return_value=[initial_env]):
                with patch.object(initial_env, 'save'):
                    # Process weather evolution pose
                    updated_env, flags = environment_service.process_pose_for_environment(weather_pose, scene_id)
                    
                    assert updated_env == initial_env  # Same environment object, updated
                    assert updated_env.weather["condition"] == "light rain"
                    assert updated_env.weather["intensity"] == "beginning"
                    # Physical details should be merged
                    assert "ground" in updated_env.physical_details
                    assert len(flags) == 0  # No inconsistencies
    
    def test_fallback_without_ai(self):
        """Test that the service works without AI client (fallback mode)."""
        # Create service without AI client
        service = EnvironmentStateService(openrouter_client=None)
        scene_id = "test_scene_123"
        
        # Test pose with clear environmental keywords
        pose = Pose(
            scene_id=scene_id,
            character_name="Test",
            content="The character walks through the rainy evening, the dim lighting making it hard to see.",
            pose_type=PoseType.NARRATIVE
        )
        
        # Mock database operations
        with patch.object(EnvironmentState, 'save', return_value="env_123"):
            # Process pose without AI
            env, flags = service.process_pose_for_environment(pose, scene_id)
            
            assert env is not None
            # Without AI, location_name comes from basic extraction (None in this case)
            # The service should still create an environment with extracted basic details
            # Basic extraction should still work
            extracted = service.extract_environmental_details(pose)
            assert extracted["weather"].get("condition") == "rainy"
            assert extracted["time_context"].get("time_of_day") == "evening"
            assert extracted["lighting"] == "dim"