"""
Scene summary generation service.

This service provides AI-powered scene summarization capabilities, including comprehensive, 
character-focused, and plot-focused summaries, as well as catch-up briefs for returning users.
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass
from ..models.scene import Scene
from ..models.character import Character
from ..services.openrouter_client import OpenRouterClient


@dataclass
class SummaryOptions:
    """Options for generating scene summaries."""
    focus: str = "comprehensive"  # Options: comprehensive, character, plot, environment
    character_id: Optional[str] = None  # Required if focus is 'character'
    max_length: int = 500  # Maximum length of the summary in words
    include_details: bool = True  # Whether to include detailed descriptions
    formal_style: bool = False  # Whether to use a formal writing style
    chronological: bool = True  # Whether to organize events chronologically
    highlight_key_events: bool = True  # Whether to highlight key events


@dataclass
class SceneSummary:
    """Represents a generated scene summary."""
    scene_id: str
    summary_text: str
    summary_type: str
    created_at: datetime = datetime.utcnow()
    focus_character_id: Optional[str] = None
    word_count: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Calculate word count if not provided."""
        if not self.word_count:
            self.word_count = len(self.summary_text.split())
        
        if not self.metadata:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary representation."""
        return {
            'scene_id': self.scene_id,
            'summary_text': self.summary_text,
            'summary_type': self.summary_type,
            'created_at': self.created_at.isoformat(),
            'focus_character_id': self.focus_character_id,
            'word_count': self.word_count,
            'metadata': self.metadata
        }


class SummaryService:
    """Service for generating scene summaries."""
    
    @staticmethod
    def generate_summary(
        scene_id: str,
        user_id: str,
        options: Optional[SummaryOptions] = None
    ) -> Optional[SceneSummary]:
        """Generate a summary for the specified scene.
        
        Args:
            scene_id: ID of the scene to summarize
            user_id: ID of the user requesting the summary
            options: Options for generating the summary
            
        Returns:
            A SceneSummary object, or None if scene not found or access denied
        """
        # Get the scene
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return None
            
        # Set default options if not provided
        if not options:
            options = SummaryOptions()
        
        # Check if character focus is specified but no character ID provided
        if options.focus == "character" and not options.character_id:
            return None
            
        # Get character information if needed
        focus_character = None
        if options.character_id:
            focus_character = Character.find_by_id(options.character_id)
            if not focus_character:
                return None
        
        # Build context for summary generation
        summary_context = SummaryService._build_summary_context(scene, options, focus_character)
        
        # Generate the summary using AI
        summary_text = SummaryService._generate_summary_text(summary_context, options)
        
        # Create and return the summary object
        metadata = {
            'scene_name': scene.name,
            'participant_count': len(scene.participants),
            'pose_count': len(scene.poses),
            'summary_options': {
                'focus': options.focus,
                'max_length': options.max_length,
                'include_details': options.include_details,
                'formal_style': options.formal_style,
                'chronological': options.chronological,
                'highlight_key_events': options.highlight_key_events
            }
        }
        
        # Add character info to metadata if character-focused
        if focus_character:
            metadata['focus_character'] = {
                'id': focus_character.id,
                'name': focus_character.name
            }
            
        return SceneSummary(
            scene_id=scene.id,
            summary_text=summary_text,
            summary_type=options.focus,
            focus_character_id=options.character_id,
            metadata=metadata
        )
    
    @staticmethod
    def generate_catchup_brief(
        scene_id: str,
        user_id: str,
        since_timestamp: Optional[datetime] = None,
        options: Optional[SummaryOptions] = None
    ) -> Optional[SceneSummary]:
        """Generate a catch-up brief for a returning user.
        
        This summarizes what happened in a scene since the user was last active.
        
        Args:
            scene_id: ID of the scene
            user_id: ID of the user requesting the brief
            since_timestamp: Optional timestamp to start the summary from
            options: Options for generating the summary
            
        Returns:
            A SceneSummary object, or None if scene not found or access denied
        """
        # Get the scene
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return None
            
        # Set default options if not provided
        if not options:
            options = SummaryOptions(max_length=300)  # Briefer by default
        
        # Default since_timestamp to 7 days ago if not provided
        if not since_timestamp:
            since_timestamp = datetime.utcnow() - datetime.timedelta(days=7)
            
        # Filter poses that occurred after the specified timestamp
        recent_poses = [
            pose for pose in scene.poses 
            if (pose.timestamp and pose.timestamp > since_timestamp)
        ]
        
        # If no recent poses, return a note about that
        if not recent_poses:
            return SceneSummary(
                scene_id=scene.id,
                summary_text="No activity in this scene since your last visit.",
                summary_type="catchup",
                metadata={
                    'scene_name': scene.name,
                    'since_timestamp': since_timestamp.isoformat()
                }
            )
            
        # Build context for summary generation with only recent poses
        temp_scene = Scene.from_dict(scene.to_dict())
        temp_scene.poses = recent_poses
        
        summary_context = SummaryService._build_summary_context(temp_scene, options, None)
        summary_context['is_catchup'] = True
        summary_context['since_timestamp'] = since_timestamp.isoformat()
        
        # Generate the summary using AI
        summary_text = SummaryService._generate_summary_text(summary_context, options)
        
        # Create and return the summary object
        return SceneSummary(
            scene_id=scene.id,
            summary_text=summary_text,
            summary_type="catchup",
            metadata={
                'scene_name': scene.name,
                'since_timestamp': since_timestamp.isoformat(),
                'recent_pose_count': len(recent_poses)
            }
        )
    
    @staticmethod
    def generate_character_focused_summary(
        scene_id: str,
        user_id: str,
        character_id: str,
        options: Optional[SummaryOptions] = None
    ) -> Optional[SceneSummary]:
        """Generate a summary focused on a specific character's activity.
        
        Args:
            scene_id: ID of the scene
            user_id: ID of the user requesting the summary
            character_id: ID of the character to focus on
            options: Options for generating the summary
            
        Returns:
            A SceneSummary object, or None if scene or character not found or access denied
        """
        # Set character focus options
        if not options:
            options = SummaryOptions()
        options.focus = "character"
        options.character_id = character_id
        
        # Use the main generate_summary method
        return SummaryService.generate_summary(scene_id, user_id, options)
    
    @staticmethod
    def generate_plot_focused_summary(
        scene_id: str,
        user_id: str,
        options: Optional[SummaryOptions] = None
    ) -> Optional[SceneSummary]:
        """Generate a summary focused on plot developments.
        
        Args:
            scene_id: ID of the scene
            user_id: ID of the user requesting the summary
            options: Options for generating the summary
            
        Returns:
            A SceneSummary object, or None if scene not found or access denied
        """
        # Set plot focus options
        if not options:
            options = SummaryOptions()
        options.focus = "plot"
        
        # Use the main generate_summary method
        return SummaryService.generate_summary(scene_id, user_id, options)
    
    @staticmethod
    def generate_environment_focused_summary(
        scene_id: str,
        user_id: str,
        options: Optional[SummaryOptions] = None
    ) -> Optional[SceneSummary]:
        """Generate a summary focused on environmental details.
        
        Args:
            scene_id: ID of the scene
            user_id: ID of the user requesting the summary
            options: Options for generating the summary
            
        Returns:
            A SceneSummary object, or None if scene not found or access denied
        """
        # Set environment focus options
        if not options:
            options = SummaryOptions()
        options.focus = "environment"
        
        # Use the main generate_summary method
        return SummaryService.generate_summary(scene_id, user_id, options)
    
    @staticmethod
    def edit_summary(
        scene_id: str,
        user_id: str,
        edited_text: str,
        original_summary_type: str,
        focus_character_id: Optional[str] = None
    ) -> Optional[SceneSummary]:
        """Save a user-edited version of a summary.
        
        Args:
            scene_id: ID of the scene
            user_id: ID of the user editing the summary
            edited_text: The edited summary text
            original_summary_type: The type of the original summary
            focus_character_id: ID of the focus character, if applicable
            
        Returns:
            The updated SceneSummary object, or None if scene not found or access denied
        """
        # Get the scene to verify access
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return None
        
        # Create and return the edited summary
        metadata = {
            'scene_name': scene.name,
            'is_edited': True,
            'edited_at': datetime.utcnow().isoformat()
        }
        
        return SceneSummary(
            scene_id=scene_id,
            summary_text=edited_text,
            summary_type=f"{original_summary_type}_edited",
            focus_character_id=focus_character_id,
            metadata=metadata
        )
    
    @staticmethod
    def export_summary(
        scene_id: str,
        user_id: str,
        format_type: str = "markdown",  # Options: markdown, plain, html
        include_metadata: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Export a summary in the specified format.
        
        Args:
            scene_id: ID of the scene
            user_id: ID of the user requesting the export
            format_type: Format to export in
            include_metadata: Whether to include metadata in the export
            
        Returns:
            A dictionary with the formatted summary, or None if scene not found or access denied
        """
        # Generate a comprehensive summary first
        summary = SummaryService.generate_summary(
            scene_id, 
            user_id, 
            SummaryOptions(focus="comprehensive")
        )
        
        if not summary:
            return None
            
        # Format the summary according to requested format
        result = {"scene_id": scene_id, "scene_name": summary.metadata.get("scene_name")}
        
        if format_type == "markdown":
            result["content"] = SummaryService._format_as_markdown(summary)
        elif format_type == "html":
            result["content"] = SummaryService._format_as_html(summary)
        else:  # plain text
            result["content"] = summary.summary_text
            
        # Include metadata if requested
        if include_metadata:
            result["metadata"] = summary.metadata
            
        return result
    
    @staticmethod
    def _build_summary_context(
        scene: Scene, 
        options: SummaryOptions, 
        focus_character: Optional[Character] = None
    ) -> Dict[str, Any]:
        """Build the context dictionary for summary generation.
        
        Args:
            scene: The scene to summarize
            options: Summary generation options
            focus_character: Optional character to focus on
            
        Returns:
            Dictionary with context for summary generation
        """
        # Extract basic scene information
        context = {
            "scene_name": scene.name,
            "scene_description": scene.description,
            "participant_count": len(scene.participants),
            "pose_count": len(scene.poses),
            "participants": {},
            "poses": [],
            "focus": options.focus,
            "summary_options": options.__dict__
        }
        
        # Add character information
        for char_id, participant in scene.participants.items():
            context["participants"][char_id] = {
                "name": participant.character_name,
                "id": char_id
            }
        
        # Add focus character details if applicable
        if focus_character:
            context["focus_character"] = {
                "id": focus_character.id,
                "name": focus_character.name,
                "description": getattr(focus_character, "description", ""),
                "traits": getattr(focus_character, "traits", {})
            }
        
        # Extract relevant pose information
        for pose in scene.poses:
            pose_data = {
                "character_name": pose.character_name,
                "character_id": pose.character_id,
                "pose_type": pose.pose_type.value,
                "pose_text": pose.pose_text,
                "enhanced_text": pose.enhanced_text,
                "timestamp": pose.timestamp.isoformat() if pose.timestamp else None,
                "tags": pose.tags or []
            }
            context["poses"].append(pose_data)
        
        # Include scene context if available
        if hasattr(scene, "context") and scene.context:
            context["scene_context"] = scene.context
        
        return context
    
    @staticmethod
    def _generate_summary_text(context: Dict[str, Any], options: SummaryOptions) -> str:
        """Generate summary text using AI based on context and options.
        
        Args:
            context: Context dictionary for summary generation
            options: Summary generation options
            
        Returns:
            Generated summary text
        """
        # Get API key from environment variable
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            # Fallback for testing/development
            return f"This is a placeholder summary for scene '{context['scene_name']}'. AI integration requires a valid OPENROUTER_API_KEY."
        
        # Initialize OpenRouter client
        openrouter_client = OpenRouterClient(api_key=api_key)
        
        # Create system message with summary generation instructions
        system_message = SummaryService._create_system_prompt(options)
        
        # Create user message with scene details for summary generation
        user_message = SummaryService._create_user_prompt(context, options)
        
        # Set up message structure for the API call
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        # Call the OpenRouter API
        try:
            # Configure parameters based on summary type
            temperature = 0.7  # Default temperature
            # Adjust temperature based on summary type
            if options.focus == "comprehensive":
                temperature = 0.6  # More factual
            elif options.focus == "character":
                temperature = 0.7  # Moderate creativity for character focus
            elif options.focus == "plot" or options.focus == "catchup":
                temperature = 0.65  # Balance facts and narrative flow
            
            # Estimate tokens based on word count (approximation)
            max_tokens = options.max_length * 2
            
            # Generate the summary using OpenRouter.ai
            summary = openrouter_client.generate_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model="qwen3-235b"  # OpenRouter Large model for high-quality summaries
            )
            
            return summary.strip()
            
        except Exception as e:
            # Log the error (in a real implementation, use a proper logging framework)
            print(f"Error generating summary: {str(e)}")
            return f"Failed to generate summary for scene '{context['scene_name']}'. Error: {str(e)}"
    
    @staticmethod
    def _create_system_prompt(options: SummaryOptions) -> str:
        """Create the system prompt for the AI model.
        
        Args:
            options: Summary generation options
            
        Returns:
            System prompt string
        """
        prompt = """You are a skilled narrative summarizer for roleplaying scenes. Your task is to create a clear, engaging summary that captures the essence of the scene provided.
            
Follow these instructions:
1. Create a coherent summary that maintains the narrative flow and highlights key events.
2. Focus on character interactions, plot developments, and environmental changes.
3. Include relevant dialogue and character actions that moved the scene forward.
4. Organize the information in a reader-friendly format."""

        # Add specific instructions based on summary type
        if options.focus == "comprehensive":
            prompt += """
5. Create a comprehensive overview that balances character actions, plot developments, and environmental details.
6. Ensure all major scene elements and turning points are included."""
        elif options.focus == "character":
            prompt += """
5. Focus primarily on the specified character's actions, dialogue, emotions, and development.
6. Include how other characters interact with this character, but keep the focus character central to the summary."""
        elif options.focus == "plot":
            prompt += """
5. Focus primarily on plot developments, story progression, and narrative arcs.
6. Highlight cause-effect relationships and how events connect or build upon each other."""
        elif options.focus == "environment":
            prompt += """
5. Focus primarily on the environment, setting changes, atmosphere, and world-building elements.
6. Describe how the environment affects characters and influences the scene's mood."""

        # Add style guidance
        if options.formal_style:
            prompt += """

Use a formal, academic writing style with precise language and proper terminology."""
        else:
            prompt += """

Use a casual, engaging writing style that's accessible and enjoyable to read."""
            
        # Add organization guidance
        if options.chronological:
            prompt += """
Organize events in chronological order, following the timeline of the scene."""
        else:
            prompt += """
Organize events by importance, with major developments and turning points highlighted first."""

        # Add length guidance
        prompt += f"""

Keep the summary concise, around {options.max_length} words total.
        
Your response should be in plain text format, ready for presentation to the reader."""

        return prompt
    
    @staticmethod
    def _create_user_prompt(context: Dict[str, Any], options: SummaryOptions) -> str:
        """Create the user prompt with scene details for the AI model.
        
        Args:
            context: Context dictionary with scene information
            options: Summary generation options
            
        Returns:
            User prompt string
        """
        prompt = f"Generate a {options.focus} summary for the following scene:\n\n"
        
        # Add basic scene information
        prompt += f"Scene Name: {context['scene_name']}\n"
        if context.get("scene_description"):
            prompt += f"Scene Description: {context.get('scene_description')}\n"
            
        # Add focus character info if applicable
        if options.focus == "character" and context.get("focus_character"):
            char = context.get("focus_character")
            prompt += f"\nFocus Character: {char['name']}\n"
            if char.get("description"):
                prompt += f"Character Description: {char['description']}\n"
                
        # Add catchup info if applicable
        if context.get("is_catchup"):
            prompt += f"\nThis is a catch-up brief summarizing activity since {context.get('since_timestamp')}\n"
            
        # Add scene context if available
        if context.get("scene_context"):
            # Add plot elements
            if context["scene_context"].get("plot_elements"):
                prompt += "\nPlot Elements:\n"
                for plot in context["scene_context"]["plot_elements"]:
                    prompt += f"- {plot.get('title')}: {plot.get('description')}\n"
            
            # Add environment details
            if context["scene_context"].get("environment_details"):
                prompt += "\nEnvironment Details:\n"
                for env in context["scene_context"]["environment_details"]:
                    prompt += f"- {env.get('name')}: {env.get('description')}\n"
        
        # Add participant information
        if context["participants"]:
            prompt += f"\nParticipants ({len(context['participants'])} characters):\n"
            for char_id, participant in context["participants"].items():
                prompt += f"- {participant['name']} (ID: {char_id})\n"
        
        # Add pose data
        poses = context["poses"]
        prompt += f"\nScene Content ({len(poses)} poses):\n\n"
        
        # Process poses (limit to reasonable number to avoid token limits)
        max_poses = min(len(poses), 30)  # Set a reasonable limit
        
        for i, pose in enumerate(poses[:max_poses]):
            # Use enhanced text if available, otherwise use regular pose text
            pose_content = pose.get("enhanced_text") if pose.get("enhanced_text") else pose.get("pose_text")
            
            # Add timestamp if available
            timestamp = ""
            if pose.get("timestamp"):
                timestamp = f" [{pose.get('timestamp')}]"
                
            prompt += f"{i+1}. {pose['character_name']}{timestamp} ({pose['pose_type']}): {pose_content}\n\n"
            
        # Add note if poses were limited
        if len(poses) > max_poses:
            prompt += f"... and {len(poses) - max_poses} more poses (summarized for brevity)\n\n"
            
        # Add any specific summary instructions
        if options.highlight_key_events:
            prompt += "\nPlease highlight key events and turning points in the summary.\n"
            
        return prompt
    
    @staticmethod
    def _format_as_markdown(summary: SceneSummary) -> str:
        """Format summary as markdown.
        
        Args:
            summary: The summary to format
            
        Returns:
            Markdown formatted summary
        """
        scene_name = summary.metadata.get("scene_name", "Unnamed Scene")
        summary_type = summary.summary_type.title()
        
        markdown = f"# {scene_name} - {summary_type} Summary\n\n"
        
        # Add focus character if applicable
        if summary.focus_character_id and summary.metadata.get("focus_character"):
            char_name = summary.metadata["focus_character"]["name"]
            markdown += f"*Character focus: {char_name}*\n\n"
            
        # Add the summary text
        markdown += summary.summary_text
        
        # Add metadata footer
        markdown += f"\n\n---\n"
        markdown += f"Generated on: {summary.created_at.strftime('%Y-%m-%d %H:%M')}"
        
        return markdown
    
    @staticmethod
    def _format_as_html(summary: SceneSummary) -> str:
        """Format summary as HTML.
        
        Args:
            summary: The summary to format
            
        Returns:
            HTML formatted summary
        """
        scene_name = summary.metadata.get("scene_name", "Unnamed Scene")
        summary_type = summary.summary_type.title()
        
        html = f"""
        <div class="scene-summary">
            <h1>{scene_name} - {summary_type} Summary</h1>
        """
        
        # Add focus character if applicable
        if summary.focus_character_id and summary.metadata.get("focus_character"):
            char_name = summary.metadata["focus_character"]["name"]
            html += f'<p class="focus-character"><em>Character focus: {char_name}</em></p>\n'
            
        # Add the summary text with paragraphs
        paragraphs = summary.summary_text.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                html += f'<p>{paragraph}</p>\n'
        
        # Add metadata footer
        html += f'<hr>\n<p class="meta">Generated on: {summary.created_at.strftime("%Y-%m-%d %H:%M")}</p>\n'
        html += '</div>'
        
        return html
