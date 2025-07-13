"""
Pose context analysis service for MUSH Pose Editor.

This service analyzes poses from other players to identify key elements
that should influence character responses.
"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from app.services.venice_client import VeniceClient, VeniceAPIError
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pose context to dictionary."""
        return asdict(self)


class ContextService:
    """Service for analyzing pose context and extracting response elements."""
    
    def __init__(self, venice_client: VeniceClient):
        """Initialize the context service.
        
        Args:
            venice_client: Venice.ai client for AI processing
        """
        self.venice_client = venice_client
    
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
            VeniceAPIError: If AI processing fails
            ValueError: If the AI response is invalid
        """
        try:
            # Extract context information using AI
            context_data = self._extract_pose_context(pose_text, character_name)
            
            # Validate the extracted data
            self._validate_context_data(context_data)
            
            # Create and return pose context
            return PoseContext(**context_data)
            
        except VeniceAPIError:
            # Re-raise Venice API errors
            raise
        except Exception as e:
            raise ValueError(f"Invalid context data: {str(e)}")
    
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
        system_message = ModelConfig.get_system_message_for_use_case("pose_context")
        
        # Prepare user message with pose analysis request
        user_message = f"""
        Analyze the following roleplay pose and extract structured context information:

        {pose_text}
        
        {f"Analyzing from the perspective of character: {character_name}" if character_name else ""}

        Please respond with a valid JSON object containing:
        - actions: List of physical actions and movements
        - emotions: List of emotional states and feelings expressed
        - environmental_details: List of setting and environmental elements
        - character_interactions: List of character interaction types
        - response_hooks: List of elements that invite responses
        - scene_timing: Overall timing context (immediate, ongoing, delayed)
        - urgency_level: How urgent the situation feels (low, medium, high, critical)
        - narrative_tone: The overall tone (serious, playful, tense, etc.)
        """
        
        # Generate completion using Venice.ai
        response = self.venice_client.generate_completion(
            model="venice-uncensored",
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
    
    def get_response_suggestions(
        self, 
        context: PoseContext,
        character_name: Optional[str] = None
    ) -> List[str]:
        """Generate response suggestions based on pose context.
        
        Args:
            context: Analyzed pose context
            character_name: Optional character name for perspective
            
        Returns:
            List of response suggestions
        """
        suggestions = []
        
        # Suggest responses based on actions
        if context.actions:
            suggestions.append(f"React to: {', '.join(context.actions[:2])}")
        
        # Suggest responses based on emotions
        if context.emotions:
            suggestions.append(f"Respond to emotional tone: {context.emotions[0]}")
        
        # Suggest responses based on hooks
        if context.response_hooks:
            suggestions.extend([f"Address: {hook}" for hook in context.response_hooks[:2]])
        
        # Suggest based on urgency
        if context.urgency_level in ["high", "critical"]:
            suggestions.append("Consider immediate action or response")
        elif context.urgency_level == "low":
            suggestions.append("Take time for thoughtful response")
        
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
            except (VeniceAPIError, ValueError) as e:
                # Log error but continue with other poses
                results[f"pose_{i}"] = {
                    "error": str(e),
                    "pose_text": pose[:100] + "..." if len(pose) > 100 else pose
                }
        
        return results 