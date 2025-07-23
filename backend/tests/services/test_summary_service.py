"""
Unit tests for the Summary Service.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.services.summary_service import SummaryService, SummaryOptions, SceneSummary
from app.models.scene import Scene, ScenePose, PoseType
from app.models.character import Character


class TestSummaryService(unittest.TestCase):
    """Test cases for the Summary Service."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock Scene
        self.mock_scene = MagicMock(spec=Scene)
        self.mock_scene.id = "scene123"
        self.mock_scene.name = "Test Scene"
        self.mock_scene.description = "A test scene for unit testing"
        self.mock_scene.created_by = "user123"
        self.mock_scene.created_at = datetime.utcnow() - timedelta(days=1)
        self.mock_scene.updated_at = datetime.utcnow()
        
        # Set up participants
        self.mock_scene.participants = {
            "char1": MagicMock(character_id="char1", character_name="Character One"),
            "char2": MagicMock(character_id="char2", character_name="Character Two")
        }
        
        # Create some poses
        self.mock_poses = [
            MagicMock(
                character_id="char1", 
                character_name="Character One",
                pose_text="Character One enters the scene and looks around.",
                pose_type=PoseType.ACTION,
                enhanced_text="Character One cautiously enters the dimly lit room, their eyes scanning the environment with evident curiosity.",
                timestamp=datetime.utcnow() - timedelta(hours=2),
                tags=["entry"]
            ),
            MagicMock(
                character_id="char2", 
                character_name="Character Two",
                pose_text="Hello there! Welcome to the scene.",
                pose_type=PoseType.SPEECH,
                enhanced_text="Hello there! Welcome to the scene. Character Two's voice echoes warmly through the space.",
                timestamp=datetime.utcnow() - timedelta(hours=1, minutes=45),
                tags=["greeting"]
            ),
            MagicMock(
                character_id="char1", 
                character_name="Character One",
                pose_text="Thank you. What's happening here?",
                pose_type=PoseType.SPEECH,
                enhanced_text="Thank you. What's happening here? Character One asks with a hint of uncertainty.",
                timestamp=datetime.utcnow() - timedelta(hours=1, minutes=30),
                tags=["question"]
            )
        ]
        self.mock_scene.poses = self.mock_poses
        
        # Mock scene context
        self.mock_scene.context = {
            "environment_details": [
                {
                    "name": "Room",
                    "description": "A dimly lit room with minimal furniture.",
                    "tags": ["indoor", "dark"]
                }
            ],
            "plot_elements": [
                {
                    "title": "Mysterious Meeting",
                    "description": "Characters meeting for unknown purposes.",
                    "tags": ["mystery", "meeting"]
                }
            ]
        }
        
        # Mock Character
        self.mock_character = MagicMock(spec=Character)
        self.mock_character.id = "char1"
        self.mock_character.name = "Character One"
        self.mock_character.user_id = "user123"
        self.mock_character.description = "A test character"
        
        # Patch the find_by_id methods
        self.scene_find_patcher = patch('app.models.scene.Scene.find_by_id')
        self.mock_scene_find = self.scene_find_patcher.start()
        self.mock_scene_find.return_value = self.mock_scene
        
        self.character_find_patcher = patch('app.models.character.Character.find_by_id')
        self.mock_character_find = self.character_find_patcher.start()
        self.mock_character_find.return_value = self.mock_character
        
        # Patch the AI text generation
        self.ai_text_patcher = patch('app.services.summary_service.generate_ai_text')
        self.mock_ai_text = self.ai_text_patcher.start()
        self.mock_ai_text.return_value = "This is a test summary of the scene."

    def tearDown(self):
        """Tear down test fixtures."""
        self.scene_find_patcher.stop()
        self.character_find_patcher.stop()
        self.ai_text_patcher.stop()

    def test_generate_summary_basic(self):
        """Test basic summary generation."""
        summary = SummaryService.generate_summary(
            scene_id="scene123",
            user_id="user123"
        )
        
        # Assert the summary was created correctly
        self.assertIsNotNone(summary)
        self.assertEqual(summary.scene_id, "scene123")
        self.assertEqual(summary.summary_type, "comprehensive")
        self.assertEqual(summary.summary_text, "This is a test summary of the scene.")
        
        # Verify AI was called with appropriate context
        self.mock_ai_text.assert_called_once()
        context_arg = self.mock_ai_text.call_args[0][0]
        self.assertIn("Test Scene", context_arg)
        self.assertIn("comprehensive", context_arg)

    def test_generate_summary_access_denied(self):
        """Test summary generation fails with invalid user."""
        summary = SummaryService.generate_summary(
            scene_id="scene123",
            user_id="wrong_user"
        )
        
        # Assert no summary was created
        self.assertIsNone(summary)
        # Verify AI was not called
        self.mock_ai_text.assert_not_called()

    def test_generate_summary_scene_not_found(self):
        """Test summary generation fails with invalid scene."""
        self.mock_scene_find.return_value = None
        
        summary = SummaryService.generate_summary(
            scene_id="invalid_scene",
            user_id="user123"
        )
        
        # Assert no summary was created
        self.assertIsNone(summary)
        # Verify AI was not called
        self.mock_ai_text.assert_not_called()

    def test_generate_character_focused_summary(self):
        """Test character-focused summary generation."""
        summary = SummaryService.generate_character_focused_summary(
            scene_id="scene123",
            user_id="user123",
            character_id="char1"
        )
        
        # Assert the summary was created correctly
        self.assertIsNotNone(summary)
        self.assertEqual(summary.scene_id, "scene123")
        self.assertEqual(summary.summary_type, "character")
        self.assertEqual(summary.focus_character_id, "char1")
        
        # Verify AI was called with appropriate context
        self.mock_ai_text.assert_called_once()
        context_arg = self.mock_ai_text.call_args[0][0]
        self.assertIn("Character One", context_arg)
        self.assertIn("character", context_arg)

    def test_generate_plot_focused_summary(self):
        """Test plot-focused summary generation."""
        summary = SummaryService.generate_plot_focused_summary(
            scene_id="scene123",
            user_id="user123"
        )
        
        # Assert the summary was created correctly
        self.assertIsNotNone(summary)
        self.assertEqual(summary.scene_id, "scene123")
        self.assertEqual(summary.summary_type, "plot")
        
        # Verify AI was called with appropriate context
        self.mock_ai_text.assert_called_once()
        context_arg = self.mock_ai_text.call_args[0][0]
        self.assertIn("plot", context_arg)

    def test_generate_environment_focused_summary(self):
        """Test environment-focused summary generation."""
        summary = SummaryService.generate_environment_focused_summary(
            scene_id="scene123",
            user_id="user123"
        )
        
        # Assert the summary was created correctly
        self.assertIsNotNone(summary)
        self.assertEqual(summary.scene_id, "scene123")
        self.assertEqual(summary.summary_type, "environment")
        
        # Verify AI was called with appropriate context
        self.mock_ai_text.assert_called_once()
        context_arg = self.mock_ai_text.call_args[0][0]
        self.assertIn("environment", context_arg)

    def test_generate_catchup_brief(self):
        """Test catch-up brief generation."""
        since_time = datetime.utcnow() - timedelta(hours=2)
        
        summary = SummaryService.generate_catchup_brief(
            scene_id="scene123",
            user_id="user123",
            since_timestamp=since_time
        )
        
        # Assert the summary was created correctly
        self.assertIsNotNone(summary)
        self.assertEqual(summary.scene_id, "scene123")
        self.assertEqual(summary.summary_type, "catchup")
        
        # Check metadata
        self.assertIn("since_timestamp", summary.metadata)
        
        # Verify AI was called with appropriate context
        self.mock_ai_text.assert_called_once()
        context_arg = self.mock_ai_text.call_args[0][0]
        self.assertIn("catch-up", context_arg.lower())

    def test_generate_catchup_brief_no_activity(self):
        """Test catch-up brief when there's no new activity."""
        # Set all poses to be older than the since timestamp
        for pose in self.mock_poses:
            pose.timestamp = datetime.utcnow() - timedelta(days=10)
            
        since_time = datetime.utcnow() - timedelta(hours=2)
        
        summary = SummaryService.generate_catchup_brief(
            scene_id="scene123",
            user_id="user123",
            since_timestamp=since_time
        )
        
        # Assert a summary was created with a "no activity" message
        self.assertIsNotNone(summary)
        self.assertEqual(summary.scene_id, "scene123")
        self.assertEqual(summary.summary_type, "catchup")
        self.assertIn("No activity", summary.summary_text)
        
        # Verify AI was NOT called since there's no activity to summarize
        self.mock_ai_text.assert_not_called()

    def test_edit_summary(self):
        """Test editing a summary."""
        edited_text = "This is an edited summary with user modifications."
        
        summary = SummaryService.edit_summary(
            scene_id="scene123",
            user_id="user123",
            edited_text=edited_text,
            original_summary_type="comprehensive"
        )
        
        # Assert the edited summary was created correctly
        self.assertIsNotNone(summary)
        self.assertEqual(summary.scene_id, "scene123")
        self.assertEqual(summary.summary_text, edited_text)
        self.assertEqual(summary.summary_type, "comprehensive_edited")
        
        # Check that the metadata indicates it's edited
        self.assertIn("is_edited", summary.metadata)
        self.assertTrue(summary.metadata["is_edited"])

    def test_export_summary_markdown(self):
        """Test exporting summary in markdown format."""
        result = SummaryService.export_summary(
            scene_id="scene123",
            user_id="user123",
            format_type="markdown"
        )
        
        # Assert the export was created correctly
        self.assertIsNotNone(result)
        self.assertEqual(result["scene_id"], "scene123")
        self.assertEqual(result["scene_name"], "Test Scene")
        
        # Check that the content is markdown formatted
        self.assertIn("# Test Scene", result["content"])
        self.assertIn("---", result["content"])

    def test_export_summary_html(self):
        """Test exporting summary in HTML format."""
        result = SummaryService.export_summary(
            scene_id="scene123",
            user_id="user123",
            format_type="html"
        )
        
        # Assert the export was created correctly
        self.assertIsNotNone(result)
        self.assertEqual(result["scene_id"], "scene123")
        
        # Check that the content is HTML formatted
        self.assertIn("<h1>", result["content"])
        self.assertIn("</div>", result["content"])

    def test_summary_options(self):
        """Test that summary options affect the generated content."""
        options = SummaryOptions(
            focus="comprehensive",
            max_length=300,
            formal_style=True,
            highlight_key_events=True
        )
        
        summary = SummaryService.generate_summary(
            scene_id="scene123",
            user_id="user123",
            options=options
        )
        
        # Assert options were passed to the AI context
        self.mock_ai_text.assert_called_once()
        context_arg = self.mock_ai_text.call_args[0][0]
        self.assertIn("formal", context_arg)
        self.assertIn("300 words", context_arg)
        self.assertIn("key events", context_arg)

    def test_scene_summary_to_dict(self):
        """Test conversion of SceneSummary to dictionary."""
        summary = SceneSummary(
            scene_id="scene123",
            summary_text="Test summary text",
            summary_type="comprehensive",
            focus_character_id="char1",
            metadata={"key": "value"}
        )
        
        summary_dict = summary.to_dict()
        
        # Assert conversion is correct
        self.assertEqual(summary_dict["scene_id"], "scene123")
        self.assertEqual(summary_dict["summary_text"], "Test summary text")
        self.assertEqual(summary_dict["summary_type"], "comprehensive")
        self.assertEqual(summary_dict["focus_character_id"], "char1")
        self.assertIn("created_at", summary_dict)
        self.assertIn("key", summary_dict["metadata"])


if __name__ == '__main__':
    unittest.main()
