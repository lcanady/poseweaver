"""
Unit tests for Environment State Service.

Tests environmental state tracking, detail extraction, consistency checking,
and integration with AI analysis according to requirements 3.1-3.5.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from app.services.environment_state_service import (
    EnvironmentStateService, EnvironmentUpdate, EnvironmentConsistencyCheck
)
from app.models.scene_memory import (
    EnvironmentState, Pose, ContinuityFlag, PoseType, FlagType, Severity
)
from app.services.openrouter_client import OpenRouterClient, OpenRouterAPIError


class TestEnvironmentStateService:
    """Test cases for EnvironmentStateService."""
    
    @pytest.fixture
    def mock_openrouter_client(self):
        """Create a mock OpenRouter client."""
        return Mock(spec=OpenRouterClient)
    
    @pytest.fixture
    def environment_service(self, mock_openrouter_client):
        """Create EnvironmentStateService with mock OpenRouter client."""
        return EnvironmentStateService(openrouter_client=mock_openrouter_client)
    
    @pytest.fixture
    def environment_service_no_ai(self):
        """Create EnvironmentStateService without AI client."""
        return EnvironmentStateService(openrouter_client=None)
    
    @pytest.fixture
    def sample_pose(self):
        """Create a sample pose for testing."""
        return Pose(
            scene_id="test_scene_123",
            character_name="TestCharacter",
            content="The character steps into the dimly lit tavern, rain pattering against the windows as the evening light fades.",
            pose_type=PoseType.NARRATIVE,
            timestamp=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_environment(self):
        """Create a sample environment state for testing."""
        return EnvironmentState(
            scene_id="test_scene_123",
            location_name="The Rusty Anchor Tavern",
            description="A cozy tavern with wooden tables and a stone fireplace",
            weather={"condition": "rainy", "intensity": "light"},
            time_context={"time_of_day": "evening"},
            physical_details={
                "lighting": "dim",
                "sounds": ["rain", "crackling fire"],
                "atmosphere": "cozy"
            }
        )
    
    def test_initialize_environment_state(self, environment_service):
        """Test environment state initialization - Requirement 3.1."""
        with patch.object(EnvironmentState, 'save', return_value="env_123"):
            result = environment_service.initialize_environment_state(
                scene_id="test_scene_123",
                location_name="Test Location",
                description="A test location",
                weather={"condition": "sunny"},
                time_context={"time_of_day": "morning"},
                physical_details={"lighting": "bright"}
            )
            
            assert result.scene_id == "test_scene_123"
            assert result.location_name == "Test Location"
            assert result.description == "A test location"
            assert result.weather == {"condition": "sunny"}
            assert result.time_context == {"time_of_day": "morning"}
            assert result.physical_details == {"lighting": "bright"}
    
    def test_extract_environmental_details_with_ai(self, environment_service, sample_pose):
        """Test AI-powered environmental detail extraction - Requirement 3.1."""
        # Mock AI response
        ai_response = json.dumps({
            "location_name": "tavern",
            "weather": {"condition": "rainy"},
            "time_context": {"time_of_day": "evening"},
            "lighting": "dim",
            "sounds": "rain pattering",
            "atmosphere": "cozy"
        })
        
        environment_service.openrouter_client.generate_completion.return_value = ai_response
        
        result = environment_service.extract_environmental_details(sample_pose)
        
        assert result["location_name"] == "tavern"
        assert result["weather"]["condition"] == "rainy"
        assert result["time_context"]["time_of_day"] == "evening"
        assert result["lighting"] == "dim"
        assert result["sounds"] == "rain pattering"
        assert result["atmosphere"] == "cozy"
        
        # Verify AI was called with correct parameters
        environment_service.openrouter_client.generate_completion.assert_called_once()
        call_args = environment_service.openrouter_client.generate_completion.call_args
        assert "environmental detail extraction" in call_args[1]["system_message"].lower()
        assert sample_pose.content in call_args[1]["prompt"]
    
    def test_extract_environmental_details_ai_error_fallback(self, environment_service, sample_pose):
        """Test fallback to basic extraction when AI fails."""
        # Mock AI error
        environment_service.openrouter_client.generate_completion.side_effect = OpenRouterAPIError("API Error")
        
        result = environment_service.extract_environmental_details(sample_pose)
        
        # Should fall back to basic extraction
        assert isinstance(result, dict)
        assert "location_name" in result
        assert "weather" in result
        assert "time_context" in result
    
    def test_extract_environmental_details_without_ai(self, environment_service_no_ai, sample_pose):
        """Test basic environmental detail extraction without AI."""
        result = environment_service_no_ai.extract_environmental_details(sample_pose)
        
        # Should extract basic details from keywords
        assert isinstance(result, dict)
        assert result["weather"].get("condition") == "rainy"  # From "rain" in content
        assert result["time_context"].get("time_of_day") == "evening"  # From "evening" in content
        assert result["lighting"] == "dim"  # From "dimly lit" in content
    
    def test_detect_environment_changes_location_change(self, environment_service, sample_environment):
        """Test detection of location changes - Requirement 3.4."""
        # Create pose with different location
        pose = Pose(
            scene_id="test_scene_123",
            character_name="TestCharacter",
            content="The character walks into the bright marketplace, bustling with activity under the noon sun.",
            pose_type=PoseType.NARRATIVE
        )
        
        # Mock AI extraction to return new location
        ai_response = json.dumps({
            "location_name": "marketplace",
            "time_context": {"time_of_day": "noon"},
            "lighting": "bright"
        })
        environment_service.openrouter_client.generate_completion.return_value = ai_response
        
        result = environment_service.detect_environment_changes(pose, sample_environment)
        
        assert result.location_name == "marketplace"
        assert "Location changed to: marketplace" in result.changes_detected
        assert result.time_context["time_of_day"] == "noon"
    
    def test_detect_environment_changes_weather_update(self, environment_service, sample_environment):
        """Test detection of weather changes."""
        pose = Pose(
            scene_id="test_scene_123",
            character_name="TestCharacter",
            content="The rain has stopped and the sun is beginning to shine through the clouds.",
            pose_type=PoseType.NARRATIVE
        )
        
        # Mock AI extraction to return weather change
        ai_response = json.dumps({
            "weather": {"condition": "partly cloudy", "previous": "rainy"}
        })
        environment_service.openrouter_client.generate_completion.return_value = ai_response
        
        result = environment_service.detect_environment_changes(pose, sample_environment)
        
        assert result.weather["condition"] == "partly cloudy"
        assert "Weather conditions updated" in result.changes_detected
    
    def test_update_environment_state_new_location(self, environment_service):
        """Test creating new environment state for location change - Requirement 3.4."""
        with patch.object(EnvironmentState, 'find_by_scene', return_value=[]):
            with patch.object(environment_service, 'initialize_environment_state') as mock_init:
                mock_env = Mock(spec=EnvironmentState)
                mock_init.return_value = mock_env
                
                update = EnvironmentUpdate(
                    location_name="New Location",
                    weather={"condition": "sunny"},
                    time_context={"time_of_day": "morning"}
                )
                
                result = environment_service.update_environment_state("test_scene_123", update)
                
                assert result == mock_env
                mock_init.assert_called_once_with(
                    scene_id="test_scene_123",
                    location_name="New Location",
                    description="",
                    weather={"condition": "sunny"},
                    time_context={"time_of_day": "morning"},
                    physical_details={}
                )
    
    def test_update_environment_state_existing_location(self, environment_service, sample_environment):
        """Test updating existing environment state."""
        with patch.object(EnvironmentState, 'find_by_scene', return_value=[sample_environment]):
            with patch.object(sample_environment, 'save') as mock_save:
                update = EnvironmentUpdate(
                    weather={"condition": "sunny", "temperature": "warm"},
                    physical_details={"lighting": "bright"}
                )
                
                result = environment_service.update_environment_state("test_scene_123", update)
                
                assert result == sample_environment
                assert sample_environment.weather["condition"] == "sunny"
                assert sample_environment.weather["temperature"] == "warm"
                assert sample_environment.physical_details["lighting"] == "bright"
                mock_save.assert_called_once()
    
    def test_check_environmental_consistency_with_ai(self, environment_service, sample_pose, sample_environment):
        """Test AI-powered environmental consistency checking - Requirement 3.2, 3.3."""
        # Mock AI response indicating inconsistency
        ai_response = json.dumps({
            "is_consistent": False,
            "conflicts": [
                {
                    "type": "weather",
                    "description": "Weather condition mismatch",
                    "established": "rainy",
                    "conflicting": "sunny",
                    "severity": "medium"
                }
            ],
            "confidence_score": 0.8,
            "details": "Weather inconsistency detected"
        })
        
        environment_service.openrouter_client.generate_completion.return_value = ai_response
        
        result = environment_service.check_environmental_consistency(sample_pose, sample_environment)
        
        assert not result.is_consistent
        assert len(result.conflicts) == 1
        assert result.conflicts[0]["type"] == "weather"
        assert result.confidence_score == 0.8
        assert result.details == "Weather inconsistency detected"
    
    def test_check_environmental_consistency_consistent(self, environment_service, sample_pose, sample_environment):
        """Test consistency check when environment is consistent."""
        # Mock AI response indicating consistency
        ai_response = json.dumps({
            "is_consistent": True,
            "conflicts": [],
            "confidence_score": 0.9,
            "details": "No environmental inconsistencies detected"
        })
        
        environment_service.openrouter_client.generate_completion.return_value = ai_response
        
        result = environment_service.check_environmental_consistency(sample_pose, sample_environment)
        
        assert result.is_consistent
        assert len(result.conflicts) == 0
        assert result.confidence_score == 0.9
    
    def test_check_environmental_consistency_without_ai(self, environment_service_no_ai, sample_pose, sample_environment):
        """Test basic consistency checking without AI."""
        result = environment_service_no_ai.check_environmental_consistency(sample_pose, sample_environment)
        
        # Should perform basic keyword-based check
        assert isinstance(result, EnvironmentConsistencyCheck)
        assert isinstance(result.is_consistent, bool)
        assert isinstance(result.conflicts, list)
        assert result.confidence_score == 0.6  # Basic check confidence
    
    def test_create_consistency_flags(self, environment_service, sample_pose):
        """Test creation of continuity flags for inconsistencies - Requirement 3.3."""
        consistency_check = EnvironmentConsistencyCheck(
            is_consistent=False,
            conflicts=[
                {
                    "type": "weather",
                    "description": "Weather mismatch",
                    "established": "rainy",
                    "conflicting": "sunny",
                    "severity": "high"
                }
            ],
            confidence_score=0.8
        )
        
        with patch.object(ContinuityFlag, 'save', return_value="flag_123"):
            flags = environment_service.create_consistency_flags(sample_pose, consistency_check)
            
            assert len(flags) == 1
            flag = flags[0]
            assert flag.pose_id == sample_pose.id
            assert flag.flag_type == FlagType.ENVIRONMENT_CONTRADICTION
            assert flag.severity == Severity.HIGH
            assert "Weather mismatch" in flag.description
            assert flag.confidence_score == 0.8
    
    def test_create_consistency_flags_consistent(self, environment_service, sample_pose):
        """Test no flags created when environment is consistent."""
        consistency_check = EnvironmentConsistencyCheck(
            is_consistent=True,
            conflicts=[],
            confidence_score=0.9
        )
        
        flags = environment_service.create_consistency_flags(sample_pose, consistency_check)
        
        assert len(flags) == 0
    
    def test_get_scene_environments(self, environment_service):
        """Test retrieving all environments for a scene - Requirement 3.5."""
        mock_environments = [Mock(spec=EnvironmentState), Mock(spec=EnvironmentState)]
        
        with patch.object(EnvironmentState, 'find_by_scene', return_value=mock_environments):
            result = environment_service.get_scene_environments("test_scene_123")
            
            assert result == mock_environments
            EnvironmentState.find_by_scene.assert_called_once_with("test_scene_123")
    
    def test_get_current_environment(self, environment_service):
        """Test retrieving current environment for a scene - Requirement 3.5."""
        mock_environments = [Mock(spec=EnvironmentState), Mock(spec=EnvironmentState)]
        
        with patch.object(EnvironmentState, 'find_by_scene', return_value=mock_environments):
            result = environment_service.get_current_environment("test_scene_123")
            
            assert result == mock_environments[-1]  # Should return most recent
    
    def test_get_current_environment_none(self, environment_service):
        """Test retrieving current environment when none exists."""
        with patch.object(EnvironmentState, 'find_by_scene', return_value=[]):
            result = environment_service.get_current_environment("test_scene_123")
            
            assert result is None
    
    def test_process_pose_for_environment_new_scene(self, environment_service, sample_pose):
        """Test processing pose for environment when no environment exists."""
        # Mock no existing environment
        with patch.object(environment_service, 'get_current_environment', return_value=None):
            with patch.object(environment_service, 'extract_environmental_details') as mock_extract:
                with patch.object(environment_service, 'initialize_environment_state') as mock_init:
                    mock_extract.return_value = {
                        "location_name": "tavern",
                        "weather": {"condition": "rainy"},
                        "time_context": {"time_of_day": "evening"}
                    }
                    mock_env = Mock(spec=EnvironmentState)
                    mock_init.return_value = mock_env
                    
                    env, flags = environment_service.process_pose_for_environment(
                        sample_pose, "test_scene_123"
                    )
                    
                    assert env == mock_env
                    assert len(flags) == 0
                    mock_init.assert_called_once()
    
    def test_process_pose_for_environment_existing_scene(self, environment_service, sample_pose, sample_environment):
        """Test processing pose for environment with existing environment."""
        with patch.object(environment_service, 'get_current_environment', return_value=sample_environment):
            with patch.object(environment_service, 'check_environmental_consistency') as mock_check:
                with patch.object(environment_service, 'create_consistency_flags') as mock_flags:
                    with patch.object(environment_service, 'detect_environment_changes') as mock_detect:
                        with patch.object(environment_service, 'update_environment_state') as mock_update:
                            # Mock consistent environment
                            mock_check.return_value = EnvironmentConsistencyCheck(
                                is_consistent=True, conflicts=[], confidence_score=0.9
                            )
                            mock_flags.return_value = []
                            mock_detect.return_value = EnvironmentUpdate(changes_detected=[])
                            
                            env, flags = environment_service.process_pose_for_environment(
                                sample_pose, "test_scene_123"
                            )
                            
                            assert env == sample_environment
                            assert len(flags) == 0
                            mock_check.assert_called_once_with(sample_pose, sample_environment)
                            mock_flags.assert_called_once()
                            mock_detect.assert_called_once_with(sample_pose, sample_environment)
    
    def test_process_pose_for_environment_with_changes(self, environment_service, sample_pose, sample_environment):
        """Test processing pose that results in environment changes."""
        with patch.object(environment_service, 'get_current_environment', return_value=sample_environment):
            with patch.object(environment_service, 'check_environmental_consistency') as mock_check:
                with patch.object(environment_service, 'create_consistency_flags') as mock_flags:
                    with patch.object(environment_service, 'detect_environment_changes') as mock_detect:
                        with patch.object(environment_service, 'update_environment_state') as mock_update:
                            # Mock environment changes
                            mock_check.return_value = EnvironmentConsistencyCheck(
                                is_consistent=True, conflicts=[], confidence_score=0.9
                            )
                            mock_flags.return_value = []
                            mock_detect.return_value = EnvironmentUpdate(
                                changes_detected=["Weather updated"],
                                weather={"condition": "sunny"}
                            )
                            updated_env = Mock(spec=EnvironmentState)
                            mock_update.return_value = updated_env
                            
                            env, flags = environment_service.process_pose_for_environment(
                                sample_pose, "test_scene_123"
                            )
                            
                            assert env == updated_env
                            mock_update.assert_called_once()
    
    def test_process_pose_for_environment_with_flags(self, environment_service, sample_pose, sample_environment):
        """Test processing pose that creates consistency flags."""
        with patch.object(environment_service, 'get_current_environment', return_value=sample_environment):
            with patch.object(environment_service, 'check_environmental_consistency') as mock_check:
                with patch.object(environment_service, 'create_consistency_flags') as mock_flags:
                    with patch.object(environment_service, 'detect_environment_changes') as mock_detect:
                        # Mock inconsistent environment
                        mock_check.return_value = EnvironmentConsistencyCheck(
                            is_consistent=False,
                            conflicts=[{"type": "weather", "severity": "medium"}],
                            confidence_score=0.7
                        )
                        mock_flag = Mock(spec=ContinuityFlag)
                        mock_flags.return_value = [mock_flag]
                        mock_detect.return_value = EnvironmentUpdate(changes_detected=[])
                        
                        env, flags = environment_service.process_pose_for_environment(
                            sample_pose, "test_scene_123"
                        )
                        
                        assert env == sample_environment
                        assert len(flags) == 1
                        assert flags[0] == mock_flag


class TestEnvironmentUpdate:
    """Test cases for EnvironmentUpdate data structure."""
    
    def test_environment_update_initialization(self):
        """Test EnvironmentUpdate initialization."""
        update = EnvironmentUpdate(
            location_name="New Location",
            weather={"condition": "sunny"},
            changes_detected=["Location changed"]
        )
        
        assert update.location_name == "New Location"
        assert update.weather == {"condition": "sunny"}
        assert update.changes_detected == ["Location changed"]
        assert update.time_context == {}
        assert update.physical_details == {}
    
    def test_environment_update_defaults(self):
        """Test EnvironmentUpdate default values."""
        update = EnvironmentUpdate()
        
        assert update.location_name is None
        assert update.description is None
        assert update.weather == {}
        assert update.time_context == {}
        assert update.physical_details == {}
        assert update.changes_detected == []


class TestEnvironmentConsistencyCheck:
    """Test cases for EnvironmentConsistencyCheck data structure."""
    
    def test_consistency_check_initialization(self):
        """Test EnvironmentConsistencyCheck initialization."""
        conflicts = [{"type": "weather", "severity": "high"}]
        check = EnvironmentConsistencyCheck(
            is_consistent=False,
            conflicts=conflicts,
            confidence_score=0.8,
            details="Weather mismatch detected"
        )
        
        assert not check.is_consistent
        assert check.conflicts == conflicts
        assert check.confidence_score == 0.8
        assert check.details == "Weather mismatch detected"
    
    def test_consistency_check_defaults(self):
        """Test EnvironmentConsistencyCheck default values."""
        check = EnvironmentConsistencyCheck(is_consistent=True)
        
        assert check.is_consistent
        assert check.conflicts == []
        assert check.confidence_score == 0.0
        assert check.details is None