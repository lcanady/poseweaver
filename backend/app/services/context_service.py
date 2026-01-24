"""
Pose context analysis service for MUSH Pose Editor.

This service analyzes poses from other players to identify key elements
that should influence character responses.
"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from app.services.ai_client import AIClient, OpenRouterAPIError
from app.services.model_config import ModelConfig


@dataclass
class PoseContext:
    """Structured pose context analysis data."""
    actions: List[str]
    emotions: List[str]
    environmental_details: List[str]
    character_interactions: List[str]
    response_hooks: List[str]
    scene_timing: str
    urgency_level: str
    narrative_tone: str
    poses: List[Dict[str, Any]] = None
    contextText: Optional[str] = None
    setting: Optional[str] = None
    active_characters: Optional[List[str]] = None
    raw_context: Optional[str] = None
    urgency: Optional[str] = None  # Support for both field names
    tone: Optional[str] = None     # Support for both field names
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pose context to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoseContext':
        """Create PoseContext from dictionary, filtering unknown fields."""
        # Define valid field names explicitly
        valid_fields = {
            'actions', 'emotions', 'environmental_details', 
            'character_interactions', 'response_hooks', 'scene_timing', 
            'urgency_level', 'narrative_tone', 'poses', 'contextText', 
            'setting', 'active_characters', 'raw_context', 'urgency', 'tone'
        }
        
        # Filter data to only include valid fields
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Set defaults for required fields if missing
        required_defaults = {
            'actions': [],
            'emotions': [],
            'environmental_details': [],
            'character_interactions': [],
            'response_hooks': [],
            'scene_timing': 'present',
            'urgency_level': 'medium',
            'narrative_tone': 'neutral'
        }
        
        for field, default in required_defaults.items():
            if field not in filtered_data:
                filtered_data[field] = default
        
        return cls(**filtered_data)


class ContextService:
    """Service for analyzing pose context and extracting response elements."""
    
    def __init__(self, ai_client: AIClient):
        """Initialize the context service.
        
        Args:
            ai_client: OpenRouter.ai client for AI processing
        """
        self.ai_client = ai_client
    
    def analyze_pose_context(
        self, 
        pose_text: str,
        character_name: Optional[str] = None
    ) -> PoseContext:
        """Analyze a pose to extract context for response crafting.
        
        Args:
            pose_text: The pose text to analyze
            character_name: Optional character name for perspective
            
        Returns:
            PoseContext: Structured context analysis
            
        Raises:
            OpenRouterAPIError: If AI processing fails
            ValueError: If the AI response is invalid
        """
        try:
            # Extract context information using AI
            context_data = self._extract_pose_context(
                pose_text, character_name
            )
            
            # Validate the extracted data
            self._validate_context_data(context_data)
            
            # Extract poses from the scene text
            poses = self._extract_poses_from_scene(pose_text)
            context_data['poses'] = poses
            
            # Create and return pose context
            return PoseContext.from_dict(context_data)
            
        except OpenRouterAPIError:
            # Re-raise OpenRouter API errors
            raise
        except Exception as e:
            raise ValueError(f"Invalid context data: {str(e)}")
    
    def analyze_poses_context(
        self, 
        poses: List[Dict[str, Any]],
        character_name: Optional[str] = None
    ) -> PoseContext:
        """Analyze poses directly to extract context for response crafting.
        
        Args:
            poses: List of pose dictionaries with character_name and content
            character_name: Optional character name for perspective
            
        Returns:
            PoseContext: Structured context analysis
            
        Raises:
            OpenRouterAPIError: If AI processing fails
            ValueError: If the AI response is invalid
        """
        try:
            # Convert poses to text for analysis
            pose_texts = []
            for pose in poses:
                char_name = pose.get('character_name', 'Unknown')
                content = pose.get('content', 
                                   pose.get('pose_text', ''))
                pose_texts.append(f"{char_name}: {content}")
            
            pose_text = '\n\n'.join(pose_texts)
            
            # Extract context information using AI
            context_data = self._extract_pose_context(
                pose_text, character_name
            )
            
            # Validate the extracted data
            self._validate_context_data(context_data)
            
            # Use the provided poses directly instead of extracting from text
            context_data['poses'] = poses
            
            # Create and return pose context
            return PoseContext.from_dict(context_data)
            
        except OpenRouterAPIError:
            # Re-raise OpenRouter API errors
            raise
        except Exception as e:
            raise ValueError(f"Invalid context data: {str(e)}")
    
    def _extract_poses_from_scene(
        self, scene_text: str
    ) -> List[Dict[str, Any]]:
        """Extract structured pose data from scene text.
        
        Args:
            scene_text: The scene text to analyze
            
        Returns:
            List of pose dictionaries with character_name, content, and preview
        """
        try:
            # Try to use the MushParserService to extract poses
            from app.services.mush_parser_service import MushParserService
            parser = MushParserService()
            parsed_scene = parser.parse_mush_output(scene_text)
            
            # Extract structured pose data
            poses = []
            for pose in parsed_scene.poses:
                # Skip OOC poses
                if pose.is_ooc:
                    continue
                    
                # Generate preview (first ~80 characters)
                preview = pose.content[:80]
                if len(pose.content) > 80:
                    # Try to find a word boundary to end the preview
                    cutoff = preview.rfind(' ')
                    # Only use word boundary if it's reasonably far
                    if cutoff > 60:
                        preview = preview[:cutoff] + '...'
                    else:
                        preview = preview + '...'
                
                poses.append({
                    'character_name': pose.character_name,
                    'content': pose.content,
                    'preview': preview,
                    'timestamp': pose.timestamp
                })
                
            return poses
            
        except Exception as e:
            print(f"Error extracting poses: {str(e)}")
            # Return empty list if pose extraction fails
            return []
    
    def _extract_pose_context(
        self, 
        pose_text: str,
        character_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured context information from pose text.
        
        Args:
            pose_text: The pose to analyze
            character_name: Optional character name for perspective
            
        Returns:
            Dict containing structured context information
        """
        # Prepare system message for context analysis
        system_message = ModelConfig.get_system_message_for_use_case(
            "pose_context"
        )
        
        # Prepare user message with pose analysis request
        user_message = f"""
        Analyze the following roleplay pose and extract structured context information:

        {pose_text}
        
        {f"Analyzing from the perspective of character: {character_name}" 
         if character_name else ""}

        Please respond with a valid JSON object containing:
        - actions: List of physical actions and movements
        - emotions: List of emotional states and feelings expressed
        - environmental_details: List of setting and environmental elements
        - character_interactions: List of character interaction types
        - response_hooks: List of elements that invite responses
        - scene_timing: Overall timing context (immediate, ongoing, delayed)
        - urgency_level: How urgent the situation feels (low, medium, high, 
          critical)
        - narrative_tone: The overall tone (serious, playful, tense, etc.)
        """
        
        # Generate completion using OpenRouter.ai
        response = self.ai_client.generate_completion(
            model="qwen/qwen-plus",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        # Parse JSON response if needed
        if isinstance(response, str):
            try:
                # Try to extract JSON from the response if it's wrapped in text
                response = response.strip()
                if response.startswith('```json'):
                    # Extract JSON from code block
                    start = response.find('{')
                    end = response.rfind('}') + 1
                    if start != -1 and end != 0:
                        response = response[start:end]
                elif response.startswith('```'):
                    # Extract JSON from generic code block
                    lines = response.split('\n')
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.strip().startswith('{') or in_json:
                            in_json = True
                            json_lines.append(line)
                            if line.strip().endswith('}'):
                                break
                    response = '\n'.join(json_lines)
                
                context_data = json.loads(response)
            except json.JSONDecodeError as e:
                print(f"DEBUG: Raw response: {response[:200]}...")
                raise ValueError(f"Invalid JSON response from AI: {str(e)}")
        else:
            # Response is already a dict (from mocked tests)
            context_data = response
        
        return context_data
    
    def _validate_context_data(self, data: Dict[str, Any]) -> None:
        """Validate extracted context data structure.
        
        Args:
            data: Context data dictionary to validate
            
        Raises:
            ValueError: If data structure is invalid
        """
        required_fields = [
            "actions", "emotions", "environmental_details", 
            "character_interactions", "response_hooks",
            "scene_timing", "urgency_level", "narrative_tone"
        ]
        
        # Check for required fields
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate field types
        list_fields = [
            "actions", "emotions", "environmental_details",
            "character_interactions", "response_hooks"
        ]
        for field in list_fields:
            if not isinstance(data[field], list):
                raise ValueError(f"Field '{field}' should be a list")
        
        string_fields = ["scene_timing", "urgency_level", "narrative_tone"]
        for field in string_fields:
            if not isinstance(data[field], str):
                raise ValueError(f"Field '{field}' should be a string")
        
        # Filter out unexpected fields to match PoseContext dataclass
        expected_fields = set(required_fields + [
            'poses', 'contextText', 'setting', 'active_characters', 
            'raw_context', 'urgency', 'tone'
        ])
        keys_to_remove = set(data.keys()) - expected_fields
        for key in keys_to_remove:
            data.pop(key, None)
    
    def get_response_suggestions(
        self, 
        context: PoseContext,
        character_name: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Generate response suggestions based on pose context.
        
        Args:
            context: Analyzed pose context
            character_name: Optional character name for perspective
            
        Returns:
            List of response suggestion objects with text and type
        """
        suggestions = []
        
        # Suggest responses based on actions
        if context.actions:
            action_text = f"React to: {', '.join(context.actions[:2])}"
            suggestions.append({
                "text": action_text,
                "type": "action"
            })
        
        # Suggest responses based on emotions
        if context.emotions:
            emotion_text = f"Respond to emotional tone: {context.emotions[0]}"
            suggestions.append({
                "text": emotion_text,
                "type": "emotion"
            })
        
        # Suggest responses based on hooks
        if context.response_hooks:
            for hook in context.response_hooks[:2]:
                suggestions.append({
                    "text": f"Address: {hook}",
                    "type": "hook"
                })
        
        # Suggest based on urgency
        if context.urgency_level in ["high", "critical"]:
            suggestions.append({
                "text": "Consider immediate action or response",
                "type": "urgency"
            })
        elif context.urgency_level == "low":
            suggestions.append({
                "text": "Take time for thoughtful response",
                "type": "timing"
            })
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def analyze_multiple_poses(
        self, 
        poses: List[str],
        character_name: Optional[str] = None
    ) -> Dict[str, PoseContext]:
        """Analyze multiple poses and return context for each.
        
        Args:
            poses: List of pose texts to analyze
            character_name: Optional character name for perspective
            
        Returns:
            Dictionary mapping pose index to context analysis
        """
        results = {}
        
        for i, pose in enumerate(poses):
            try:
                context = self.analyze_pose_context(pose, character_name)
                results[f"pose_{i}"] = context
            except (OpenRouterAPIError, ValueError) as e:
                # Log error but continue with other poses
                preview_text = pose[:100] + "..." if len(pose) > 100 else pose
                results[f"pose_{i}"] = {
                    "error": str(e),
                    "pose_text": preview_text
                }
        
        return results

    def generate_narrative_log_entry(
        self,
        before_context: Dict[str, Any],
        after_context: Dict[str, Any],
        character_name: Optional[str] = None
    ) -> str:
        """Generate a narrative milestone entry based on context changes.
        
        Args:
            before_context: Context data before the change
            after_context: Context data after the change
            character_name: Optional name of the character who initiated the change
            
        Returns:
            str: A narrative description of the event
        """
        # Prepare system message for narrative logging
        system_message = "You are a narrative chronicler for a roleplay scene. Your task is to summarize changes in scene context into a concise, engaging narrative milestone."
        
        # Prepare user message with context comparison
        user_message = f"""
        Analyze the following changes in scene context and summarize them into a single, concise narrative sentence (max 25 words).
        
        BEFORE CONTEXT:
        - Setting: {before_context.get('setting', 'Unknown')}
        - Mood: {before_context.get('mood', before_context.get('narrative_tone', 'Unknown'))}
        - Active Characters: {', '.join(before_context.get('active_characters', []))}
        - Recent Events: {', '.join(before_context.get('recent_events', []))}
        
        AFTER CONTEXT:
        - Setting: {after_context.get('setting', 'Unknown')}
        - Mood: {after_context.get('mood', after_context.get('narrative_tone', 'Unknown'))}
        - Active Characters: {', '.join(after_context.get('active_characters', []))}
        - Recent Events: {', '.join(after_context.get('recent_events', []))}
        
        Initiated by: {character_name or 'the environment'}
        
        Narrative milestone:
        """
        
        try:
            # Generate completion using OpenRouter.ai
            response = self.ai_client.generate_completion(
                model="qwen/qwen-plus",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            # Extract and clean response
            if isinstance(response, str):
                narrative = response.strip()
                # Remove any surrounding quotes or markdown
                narrative = narrative.replace('"', '').replace("'", "").replace("*", "")
                return narrative
            else:
                return "The scene context shifted, marking a new chapter in the story."
                
        except Exception as e:
            print(f"Error generating narrative log: {str(e)}")
            return "A significant change occurred in the scene's atmosphere and details."
 