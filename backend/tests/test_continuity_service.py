"""
Unit tests for ContinuityService with mocked AI responses.

Tests the AI-powered continuity analysis functionality including character consistency
checking, plot element extraction, and continuity flag generation.
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.continuity_service import (
    ContinuityService, ContinuityAnalysis, ConsistencyCheck,
    StateChange, EnvironmentUpdate, SceneContext, create_continuity_service
)
from app.services.plot_thread_service import PlotElement
from app.services.venice_client import VeniceClient, VeniceAPIError
from app.models.scene_memory import (
    Pose, CharacterState, EnvironmentState, PlotThread, ContinuityFlag,
    SceneMemory, PoseType, FlagType, Severity, PlotStatus
)


class TestContinuityService:
    """Test suite for ContinuityService."""
    
    @pytest.fixture
    def mock_venice_client(self):
        """Create a mock Venice.ai client."""
        client = Mock(spec=VeniceClient)
        return client
    
    @pytest.fixture
    def continuity_service(self, mock_venice_client):
        """Create a ContinuityService instance with mocked Venice client."""
        with patch('app.services.continuity_service.PlotThreadService') as mock_plot_service_class:
            # Create a mock plot service instance
            mock_plot_service = Mock()
            # Import PlotElement from plot_thread_service for proper mocking
            from app.services.plot_thread_service import PlotElement
            mock_plot_service.extract_plot_elements_from_pose.return_value = [
                PlotElement(
                    title="Ancient Artifact Investigation",
                    description="Character begins detailed examination of mysterious artifact",
                    importance_score=0.8,
                    element_type="development",
                    related_characters=["TestCharacter"],
                    keywords=["artifact", "investigation", "ancient"],
                    emotional_weight="medium",
                    urgency="medium",
                    scope="scene"
                )
            ]
            mock_plot_service.process_pose_for_plot_threads.return_value = {
                'pose_id': 'test_pose',
                'extracted_elements': [],
                'created_threads': [],
                'updated_threads': [],
                'thread_links': []
            }
            mock_plot_service_class.return_value = mock_plot_service
            
            return ContinuityService(mock_venice_client)
    
    @pytest.fixture
    def sample_pose(self):
        """Create a sample pose for testing."""
        return Pose(
            scene_id="test_scene_123",
            character_name="TestCharacter",
            content="TestCharacter examines the ancient artifact carefully, noting the strange symbols carved into its surface.",
            pose_type=PoseType.ACTION,
            timestamp=datetime.utcnow(),
            is_ooc=False
        )
    
    @pytest.fixture
    def sample_scene_context(self):
        """Create a sample scene context for testing."""
        recent_poses = [
            Pose(
                scene_id="test_scene_123",
                character_name="OtherCharacter",
                content="OtherCharacter points to the artifact on the table.",
                pose_type=PoseType.ACTION,
                timestamp=datetime.utcnow() - timedelta(minutes=5)
            ),
            Pose(
                scene_id="test_scene_123",
                character_name="TestCharacter",
                content="TestCharacter enters the room and looks around curiously.",
                pose_type=PoseType.ACTION,
                timestamp=datetime.utcnow() - timedelta(minutes=3)
            )
        ]
        
        character_states = [
            CharacterState(
                scene_id="test_scene_123",
                character_name="TestCharacter",
                physical_state={"health": "good", "fatigue": "low"},
                emotional_state={"mood": "curious", "stress": "low"},
                location="ancient_library"
            )
        ]
        
        environment_states = [
            EnvironmentState(
                scene_id="test_scene_123",
                location_name="ancient_library",
                description="A dusty library filled with ancient tomes and artifacts",
                weather={"indoor": True},
                time_context={"time_of_day": "afternoon"},
                physical_details={"lighting": "dim", "atmosphere": "mysterious"}
            )
        ]
        
        plot_threads = [
            PlotThread(
                scene_id="test_scene_123",
                title="The Mysterious Artifact",
                description="An ancient artifact with unknown powers",
                status=PlotStatus.DEVELOPING,
                importance_score=0.8
            )
        ]
        
        return SceneContext(
            scene_id="test_scene_123",
            recent_poses=recent_poses,
            character_states=character_states,
            environment_states=environment_states,
            plot_threads=plot_threads,
            scene_metadata={"theme": "mystery", "setting": "fantasy"}
        )
    
    @pytest.fixture
    def mock_continuity_analysis_response(self):
        """Mock AI response for continuity analysis."""
        return json.dumps({
            "character_consistency": 0.9,
            "environment_consistency": 0.8,
            "plot_consistency": 0.85,
            "timeline_consistency": 0.9,
            "confidence": 0.8,
            "issues": [
                {
                    "type": "environment",
                    "severity": "low",
                    "description": "Minor lighting inconsistency",
                    "suggestion": "Consider the established dim lighting"
                }
            ],
            "plot_elements": [
                {
                    "title": "Artifact Examination",
                    "description": "Character studying the mysterious artifact",
                    "importance": 0.7,
                    "type": "development",
                    "characters": ["TestCharacter"],
                    "keywords": ["artifact", "symbols", "examination"]
                }
            ],
            "state_changes": [
                {
                    "character": "TestCharacter",
                    "type": "emotional",
                    "description": "Increased focus and concentration",
                    "confidence": 0.8
                }
            ],
            "environment_changes": [],
            "notes": "Good continuity overall with minor environmental note"
        })
    
    @pytest.fixture
    def mock_character_consistency_response(self):
        """Mock AI response for character consistency checking."""
        return json.dumps({
            "overall_score": 0.85,
            "voice_score": 0.9,
            "behavior_score": 0.8,
            "relationship_score": 0.85,
            "confidence": 0.8,
            "issues": [],
            "strengths": [
                "Consistent curious personality",
                "Appropriate action for character"
            ],
            "suggestions": [
                "Consider adding more character-specific mannerisms"
            ],
            "voice_analysis": "Character voice remains consistent with established patterns",
            "behavior_analysis": "Behavior aligns well with character's curious nature",
            "relationship_analysis": "No relationship inconsistencies detected"
        })
    
    @pytest.fixture
    def mock_plot_extraction_response(self):
        """Mock AI response for plot element extraction."""
        return json.dumps({
            "elements": [
                {
                    "title": "Ancient Artifact Investigation",
                    "description": "Character begins detailed examination of mysterious artifact",
                    "importance": 0.8,
                    "type": "development",
                    "characters": ["TestCharacter"],
                    "keywords": ["artifact", "ancient", "symbols", "investigation"],
                    "emotional_weight": "medium",
                    "urgency": "medium",
                    "scope": "scene"
                }
            ],
            "overall_plot_significance": 0.7,
            "narrative_hooks": [
                "What do the symbols mean?",
                "What powers does the artifact possess?"
            ],
            "character_development": [
                "Character's investigative nature is highlighted"
            ]
        })
    
    @pytest.fixture
    def mock_environment_analysis_response(self):
        """Mock AI response for environment analysis."""
        return json.dumps({
            "location": "ancient_library",
            "change_type": "none",
            "description": "No significant environmental changes",
            "confidence": 0.8,
            "details": {
                "weather_changes": {},
                "time_changes": {},
                "physical_changes": {},
                "new_elements": {}
            },
            "consistency_issues": [],
            "environmental_mood": "mysterious and scholarly",
            "sensory_details": [
                "visual examination of symbols",
                "tactile interaction with artifact surface"
            ]
        })
    
    def test_analyze_pose_continuity_success(
        self, 
        continuity_service, 
        mock_venice_client,
        sample_pose, 
        sample_scene_context,
        mock_continuity_analysis_response
    ):
        """Test successful pose continuity analysis."""
        # Setup mock response
        mock_venice_client.generate_completion.return_value = mock_continuity_analysis_response
        
        # Perform analysis
        result = continuity_service.analyze_pose_continuity(sample_pose, sample_scene_context)
        
        # Verify results
        assert isinstance(result, ContinuityAnalysis)
        assert result.pose_id == sample_pose.id
        assert result.character_consistency_score == 0.9
        assert result.environment_consistency_score == 0.8
        assert result.plot_consistency_score == 0.85
        assert result.timeline_consistency_score == 0.9
        assert result.overall_confidence == 0.8
        assert len(result.extracted_plot_elements) == 1
        assert len(result.character_state_changes) == 1
        assert len(result.environment_changes) == 0
        
        # Verify Venice client was called
        mock_venice_client.generate_completion.assert_called_once()
        call_args = mock_venice_client.generate_completion.call_args
        assert 'prompt' in call_args.kwargs
        assert 'TestCharacter' in call_args.kwargs['prompt']
        assert 'ancient artifact' in call_args.kwargs['prompt']
    
    def test_analyze_pose_continuity_api_error(
        self, 
        continuity_service, 
        mock_venice_client,
        sample_pose, 
        sample_scene_context
    ):
        """Test pose continuity analysis with API error."""
        # Setup mock to raise API error
        mock_venice_client.generate_completion.side_effect = VeniceAPIError("API Error")
        
        # Perform analysis
        result = continuity_service.analyze_pose_continuity(sample_pose, sample_scene_context)
        
        # Verify fallback analysis is returned
        assert isinstance(result, ContinuityAnalysis)
        assert result.pose_id == sample_pose.id
        assert result.overall_confidence == 0.3  # Low confidence for fallback
        assert "Analysis unavailable" in result.analysis_notes
    
    def test_check_character_consistency_success(
        self, 
        continuity_service, 
        mock_venice_client,
        sample_pose,
        mock_character_consistency_response
    ):
        """Test successful character consistency checking."""
        # Setup mock response
        mock_venice_client.generate_completion.return_value = mock_character_consistency_response
        
        # Create character history
        character_history = [
            Pose(
                scene_id="test_scene_123",
                character_name="TestCharacter",
                content="TestCharacter looks around with curiosity.",
                pose_type=PoseType.ACTION,
                timestamp=datetime.utcnow() - timedelta(hours=1)
            ),
            Pose(
                scene_id="test_scene_123",
                character_name="TestCharacter",
                content="TestCharacter asks thoughtful questions about the surroundings.",
                pose_type=PoseType.DIALOGUE,
                timestamp=datetime.utcnow() - timedelta(minutes=30)
            )
        ]
        
        # Perform consistency check
        result = continuity_service.check_character_consistency(sample_pose, character_history)
        
        # Verify results
        assert isinstance(result, ConsistencyCheck)
        assert result.character_name == "TestCharacter"
        assert result.consistency_score == 0.85
        assert result.voice_consistency == 0.9
        assert result.behavior_consistency == 0.8
        assert result.relationship_consistency == 0.85
        assert result.confidence == 0.8
        assert len(result.issues) == 0
        
        # Verify Venice client was called
        mock_venice_client.generate_completion.assert_called_once()
    
    def test_check_character_consistency_api_error(
        self, 
        continuity_service, 
        mock_venice_client,
        sample_pose
    ):
        """Test character consistency checking with API error."""
        # Setup mock to raise API error
        mock_venice_client.generate_completion.side_effect = VeniceAPIError("API Error")
        
        # Perform consistency check
        result = continuity_service.check_character_consistency(sample_pose, [])
        
        # Verify fallback consistency check is returned
        assert isinstance(result, ConsistencyCheck)
        assert result.character_name == "TestCharacter"
        assert result.confidence == 0.3  # Low confidence for fallback
    
    def test_extract_plot_elements_success(
        self, 
        continuity_service, 
        mock_venice_client,
        sample_pose,
        mock_plot_extraction_response
    ):
        """Test successful plot element extraction."""
        # Setup mock response
        mock_venice_client.generate_completion.return_value = mock_plot_extraction_response
        
        # Extract plot elements
        result = continuity_service.extract_plot_elements(sample_pose)
        
        # Verify results
        assert isinstance(result, list)
        assert len(result) == 1
        
        element = result[0]
        assert isinstance(element, PlotElement)
        assert element.title == "Ancient Artifact Investigation"
        assert element.importance_score == 0.8
        assert element.element_type == "development"
        assert "TestCharacter" in element.related_characters
        assert "artifact" in element.keywords
        
        # Note: Venice client is called by PlotThreadService, not directly by ContinuityService
    
    def test_extract_plot_elements_api_error(
        self, 
        mock_venice_client,
        sample_pose
    ):
        """Test plot element extraction with API error."""
        # Create a continuity service with a plot service that returns empty list on error
        with patch('app.services.continuity_service.PlotThreadService') as mock_plot_service_class:
            mock_plot_service = Mock()
            mock_plot_service.extract_plot_elements_from_pose.return_value = []
            mock_plot_service_class.return_value = mock_plot_service
            
            continuity_service = ContinuityService(mock_venice_client)
            
            # Extract plot elements
            result = continuity_service.extract_plot_elements(sample_pose)
            
            # Verify empty list is returned
            assert isinstance(result, list)
            assert len(result) == 0
    
    def test_detect_environment_changes_success(
        self, 
        continuity_service, 
        mock_venice_client,
        sample_pose,
        mock_environment_analysis_response
    ):
        """Test successful environment change detection."""
        # Setup mock response
        mock_venice_client.generate_completion.return_value = mock_environment_analysis_response
        
        # Create current environment
        current_environment = EnvironmentState(
            scene_id="test_scene_123",
            location_name="ancient_library",
            description="A dusty library",
            weather={"indoor": True},
            time_context={"time_of_day": "afternoon"}
        )
        
        # Detect environment changes
        result = continuity_service.detect_environment_changes(sample_pose, current_environment)
        
        # Verify results
        assert isinstance(result, EnvironmentUpdate)
        assert result.location_name == "ancient_library"
        assert result.change_type == "none"
        assert result.confidence == 0.8
        
        # Verify Venice client was called
        mock_venice_client.generate_completion.assert_called_once()
    
    def test_detect_environment_changes_api_error(
        self, 
        continuity_service, 
        mock_venice_client,
        sample_pose
    ):
        """Test environment change detection with API error."""
        # Setup mock to raise API error
        mock_venice_client.generate_completion.side_effect = VeniceAPIError("API Error")
        
        # Create current environment
        current_environment = EnvironmentState(
            scene_id="test_scene_123",
            location_name="ancient_library",
            description="A dusty library"
        )
        
        # Detect environment changes
        result = continuity_service.detect_environment_changes(sample_pose, current_environment)
        
        # Verify fallback environment update is returned
        assert isinstance(result, EnvironmentUpdate)
        assert result.location_name == "ancient_library"
        assert result.confidence == 0.3  # Low confidence for fallback
    
    @patch('app.models.scene_memory.ContinuityFlag.save')
    def test_flag_continuity_issues(
        self, 
        mock_save,
        continuity_service
    ):
        """Test continuity flag generation."""
        # Create analysis with issues
        analysis = ContinuityAnalysis(
            pose_id="test_pose_123",
            character_consistency_score=0.6,  # Below threshold
            environment_consistency_score=0.5,  # Below threshold
            plot_consistency_score=0.8,  # Above threshold
            timeline_consistency_score=0.9,  # Above threshold
            overall_confidence=0.8,
            flags=[],
            extracted_plot_elements=[],
            character_state_changes=[],
            environment_changes=[],
            analysis_notes="Test analysis"
        )
        
        # Generate flags
        flags = continuity_service.flag_continuity_issues(analysis)
        
        # Verify flags were generated
        assert len(flags) == 2  # Character and environment issues
        
        character_flag = next((f for f in flags if f.flag_type == FlagType.CHARACTER_INCONSISTENCY), None)
        assert character_flag is not None
        assert character_flag.pose_id == "test_pose_123"
        assert character_flag.severity in [Severity.MEDIUM, Severity.HIGH]
        
        environment_flag = next((f for f in flags if f.flag_type == FlagType.ENVIRONMENT_CONTRADICTION), None)
        assert environment_flag is not None
        assert environment_flag.pose_id == "test_pose_123"
        
        # Verify save was called for each flag
        assert mock_save.call_count == 2
    
    @patch('app.models.scene_memory.ContinuityFlag.find_by_scene')
    def test_get_continuity_flags(
        self, 
        mock_find_by_scene,
        continuity_service
    ):
        """Test getting continuity flags for a scene."""
        # Setup mock return value
        mock_flags = [
            ContinuityFlag(
                pose_id="pose1",
                flag_type=FlagType.CHARACTER_INCONSISTENCY,
                description="Test flag",
                severity=Severity.MEDIUM
            )
        ]
        mock_find_by_scene.return_value = mock_flags
        
        # Get flags
        result = continuity_service.get_continuity_flags("test_scene_123")
        
        # Verify results
        assert result == mock_flags
        mock_find_by_scene.assert_called_once_with("test_scene_123", None)
        
        # Test with resolved filter
        continuity_service.get_continuity_flags("test_scene_123", resolved=False)
        mock_find_by_scene.assert_called_with("test_scene_123", False)
    
    @patch('app.models.scene_memory.ContinuityFlag.find_by_id')
    @patch('app.models.scene_memory.ContinuityFlag.save')
    def test_resolve_continuity_flag_success(
        self, 
        mock_save,
        mock_find_by_id,
        continuity_service
    ):
        """Test successful continuity flag resolution."""
        # Setup mock flag
        mock_flag = Mock()
        mock_flag.resolve = Mock()
        mock_find_by_id.return_value = mock_flag
        
        # Resolve flag
        result = continuity_service.resolve_continuity_flag("flag_123", "Resolved by user")
        
        # Verify results
        assert result is True
        mock_find_by_id.assert_called_once_with("flag_123")
        mock_flag.resolve.assert_called_once_with("Resolved by user")
        mock_flag.save.assert_called_once()
    
    @patch('app.models.scene_memory.ContinuityFlag.find_by_id')
    def test_resolve_continuity_flag_not_found(
        self, 
        mock_find_by_id,
        continuity_service
    ):
        """Test continuity flag resolution when flag not found."""
        # Setup mock to return None
        mock_find_by_id.return_value = None
        
        # Attempt to resolve flag
        result = continuity_service.resolve_continuity_flag("nonexistent_flag")
        
        # Verify results
        assert result is False
        mock_find_by_id.assert_called_once_with("nonexistent_flag")
    
    @patch('app.models.scene_memory.ContinuityFlag.find_by_scene')
    def test_get_scene_continuity_summary(
        self, 
        mock_find_by_scene,
        continuity_service
    ):
        """Test scene continuity summary generation."""
        # Setup mock flags
        mock_flags = [
            Mock(resolved=False, flag_type=Mock(value='character_inconsistency'), severity=Mock(value='high')),
            Mock(resolved=False, flag_type=Mock(value='environment_contradiction'), severity=Mock(value='medium')),
            Mock(resolved=True, flag_type=Mock(value='plot_contradiction'), severity=Mock(value='low')),
        ]
        
        mock_find_by_scene.return_value = mock_flags
        
        # Get summary
        result = continuity_service.get_scene_continuity_summary("test_scene_123")
        
        # Verify results
        assert result['scene_id'] == "test_scene_123"
        assert result['total_flags'] == 3
        assert result['unresolved_flags'] == 2
        assert result['resolved_flags'] == 1
        assert 'flag_types' in result
        assert 'severity_distribution' in result
        assert 'overall_health' in result
        
        mock_find_by_scene.assert_called_once_with("test_scene_123", None)
    
    def test_create_continuity_service_factory(self, mock_venice_client):
        """Test the factory function for creating continuity service."""
        service = create_continuity_service(mock_venice_client)
        
        assert isinstance(service, ContinuityService)
        assert service.venice_client == mock_venice_client
    
    def test_determine_severity_levels(self, continuity_service):
        """Test severity determination based on scores."""
        assert continuity_service._determine_severity(0.2) == Severity.CRITICAL
        assert continuity_service._determine_severity(0.4) == Severity.HIGH
        assert continuity_service._determine_severity(0.6) == Severity.MEDIUM
        assert continuity_service._determine_severity(0.8) == Severity.LOW
    
    def test_calculate_scene_health_levels(self, continuity_service):
        """Test scene health calculation."""
        # No flags - excellent
        assert continuity_service._calculate_scene_health([]) == "excellent"
        
        # Critical flags - critical
        critical_flag = Mock(severity=Severity.CRITICAL)
        assert continuity_service._calculate_scene_health([critical_flag]) == "critical"
        
        # Multiple high flags - poor
        high_flags = [Mock(severity=Severity.HIGH) for _ in range(3)]
        assert continuity_service._calculate_scene_health(high_flags) == "poor"
        
        # Many medium flags - fair
        medium_flags = [Mock(severity=Severity.MEDIUM) for _ in range(6)]
        assert continuity_service._calculate_scene_health(medium_flags) == "fair"
        
        # Few low flags - good
        low_flags = [Mock(severity=Severity.LOW) for _ in range(2)]
        assert continuity_service._calculate_scene_health(low_flags) == "good"
    
    def test_json_parsing_error_handling(self, continuity_service):
        """Test handling of JSON parsing errors in AI responses."""
        # Test continuity analysis parsing error
        invalid_json = "This is not valid JSON"
        result = continuity_service._parse_continuity_response(invalid_json)
        
        assert isinstance(result, dict)
        assert result['confidence'] == 0.5
        assert 'Analysis parsing failed' in result['notes']
        
        # Test character consistency parsing error
        result = continuity_service._parse_character_consistency_response(invalid_json)
        
        assert isinstance(result, dict)
        assert result['confidence'] == 0.5
        assert result['overall_score'] == 0.8
        
        # Test plot extraction parsing error
        result = continuity_service._parse_plot_extraction_response(invalid_json)
        
        assert isinstance(result, dict)
        assert result['elements'] == []
        assert result['overall_plot_significance'] == 0.3
        
        # Test environment analysis parsing error
        result = continuity_service._parse_environment_response(invalid_json)
        
        assert isinstance(result, dict)
        assert result['location'] == 'Unknown'
        assert result['change_type'] == 'none'


class TestContinuityServiceIntegration:
    """Integration tests for ContinuityService with real-like scenarios."""
    
    @pytest.fixture
    def real_venice_client(self):
        """Create a Venice client with test API key for integration testing."""
        return VeniceClient("test_key_for_integration")
    
    @pytest.fixture
    def integration_continuity_service(self, real_venice_client):
        """Create a ContinuityService for integration testing."""
        return ContinuityService(real_venice_client)
    
    @pytest.fixture
    def sample_pose(self):
        """Create a sample pose for testing."""
        return Pose(
            scene_id="test_scene_123",
            character_name="TestCharacter",
            content="TestCharacter examines the ancient artifact carefully, noting the strange symbols carved into its surface.",
            pose_type=PoseType.ACTION,
            timestamp=datetime.utcnow(),
            is_ooc=False
        )
    
    @pytest.fixture
    def sample_scene_context(self):
        """Create a sample scene context for testing."""
        recent_poses = [
            Pose(
                scene_id="test_scene_123",
                character_name="OtherCharacter",
                content="OtherCharacter points to the artifact on the table.",
                pose_type=PoseType.ACTION,
                timestamp=datetime.utcnow() - timedelta(minutes=5)
            ),
            Pose(
                scene_id="test_scene_123",
                character_name="TestCharacter",
                content="TestCharacter enters the room and looks around curiously.",
                pose_type=PoseType.ACTION,
                timestamp=datetime.utcnow() - timedelta(minutes=3)
            )
        ]
        
        character_states = [
            CharacterState(
                scene_id="test_scene_123",
                character_name="TestCharacter",
                physical_state={"health": "good", "fatigue": "low"},
                emotional_state={"mood": "curious", "stress": "low"},
                location="ancient_library"
            )
        ]
        
        environment_states = [
            EnvironmentState(
                scene_id="test_scene_123",
                location_name="ancient_library",
                description="A dusty library filled with ancient tomes and artifacts",
                weather={"indoor": True},
                time_context={"time_of_day": "afternoon"},
                physical_details={"lighting": "dim", "atmosphere": "mysterious"}
            )
        ]
        
        plot_threads = [
            PlotThread(
                scene_id="test_scene_123",
                title="The Mysterious Artifact",
                description="An ancient artifact with unknown powers",
                status=PlotStatus.DEVELOPING,
                importance_score=0.8
            )
        ]
        
        return SceneContext(
            scene_id="test_scene_123",
            recent_poses=recent_poses,
            character_states=character_states,
            environment_states=environment_states,
            plot_threads=plot_threads,
            scene_metadata={"theme": "mystery", "setting": "fantasy"}
        )
    
    def test_full_continuity_analysis_workflow(
        self, 
        integration_continuity_service,
        sample_pose,
        sample_scene_context
    ):
        """Test the complete continuity analysis workflow with mocked Venice responses."""
        # This test uses the mock responses built into the Venice client
        # when using a test API key
        
        # Perform full analysis
        result = integration_continuity_service.analyze_pose_continuity(
            sample_pose, 
            sample_scene_context
        )
        
        # Verify we get a valid analysis result
        assert isinstance(result, ContinuityAnalysis)
        assert result.pose_id == sample_pose.id
        assert 0.0 <= result.character_consistency_score <= 1.0
        assert 0.0 <= result.environment_consistency_score <= 1.0
        assert 0.0 <= result.plot_consistency_score <= 1.0
        assert 0.0 <= result.timeline_consistency_score <= 1.0
        assert 0.0 <= result.overall_confidence <= 1.0
    
    def test_character_consistency_workflow(
        self, 
        integration_continuity_service,
        sample_pose
    ):
        """Test character consistency checking workflow."""
        # Create character history
        character_history = [
            Pose(
                scene_id="test_scene_123",
                character_name="TestCharacter",
                content="TestCharacter speaks thoughtfully about the mysteries of the world.",
                pose_type=PoseType.DIALOGUE,
                timestamp=datetime.utcnow() - timedelta(hours=1)
            )
        ]
        
        # Perform consistency check
        result = integration_continuity_service.check_character_consistency(
            sample_pose, 
            character_history
        )
        
        # Verify we get a valid consistency check
        assert isinstance(result, ConsistencyCheck)
        assert result.character_name == "TestCharacter"
        assert 0.0 <= result.consistency_score <= 1.0
        assert 0.0 <= result.voice_consistency <= 1.0
        assert 0.0 <= result.behavior_consistency <= 1.0
        assert 0.0 <= result.relationship_consistency <= 1.0
        assert 0.0 <= result.confidence <= 1.0
    
    def test_plot_extraction_workflow(
        self, 
        integration_continuity_service,
        sample_pose
    ):
        """Test plot element extraction workflow."""
        # Extract plot elements
        result = integration_continuity_service.extract_plot_elements(sample_pose)
        
        # Verify we get a valid result
        assert isinstance(result, list)
        # The mock should return at least some plot elements for our test pose
        # which mentions examining an artifact
        if result:  # If elements were extracted
            for element in result:
                assert isinstance(element, PlotElement)
                assert element.title
                assert element.description
                assert 0.0 <= element.importance_score <= 1.0
                assert element.element_type in ["introduction", "development", "resolution", "reference"]


if __name__ == "__main__":
    pytest.main([__file__])