"""
Service for extracting structured data from unstructured text using OpenRouter LLM.
"""
from typing import Dict, Any, Optional, List

from app.services.ai_client import AIClient


class DataExtractionService:
    """Service for extracting structured data from unstructured text."""

    def __init__(self, ai_client: AIClient):
        """
        Initialize the data extraction service.
        
        Args:
            ai_client: AIClient instance for making LLM API calls
        """
        self.ai_client = ai_client

    def extract_scene_context(self, text: str, character_names: Optional[List[str]] = None, include_poses: bool = False) -> Dict[str, Any]:
        """
        Extract structured scene context data from unstructured text.
        
        Args:
            text: Unstructured text describing a scene
            character_names: Optional list of character names to focus on
            include_poses: Whether to extract structured pose data for collapsible display
        
        Returns:
            Dictionary of structured scene context
        """
        # Define the schema for scene context extraction
        schema = {
            "setting": "string - detailed description of the physical location and environment",
            "mood": "string - the overall emotional atmosphere of the scene",
            "active_characters": "list of strings - names of characters who are actively present in the scene",
            "time_of_day": "string - the time of day or temporal setting",
            "location_details": "list of strings - notable objects, features, or details about the location",
            "emotional_tone": "string - the dominant emotional tone or theme",
            "recent_events": "list of strings - key events or actions that have just happened or are happening",
            "relationship_dynamics": "object - key-value pairs where keys are relationships between characters and values describe their dynamic"
        }
        
        # Add pose extraction to schema if requested
        if include_poses:
            schema["poses"] = ("list of objects - each object should have: " +
                             "'character_name': string - name of character who posed, " +
                             "'content': string - full content of the pose, " + 
                             "'preview': string - first 10-15 words of the pose, enough to give context without full details")
        
        # Add character context if specific characters are provided
        if character_names and len(character_names) > 0:
            character_context = ", ".join([f"'{name}'" for name in character_names])
            schema_intro = f"Pay special attention to these characters: {character_context}. "
        else:
            schema_intro = ""
            
        # Extract structured data using the OpenRouter LLM
        try:
            return self.ai_client.extract_structured_data(
                unstructured_text=text,
                schema=schema,
                temperature=0.3  # Lower temperature for more deterministic outputs
            )
        except Exception as e:
            # Return partial data if extraction fails
            result = {
                "setting": "",
                "mood": "",
                "active_characters": [],
                "time_of_day": "",
                "location_details": [],
                "emotional_tone": "",
                "recent_events": [],
                "relationship_dynamics": {},
                "error": str(e)
            }
            
            if include_poses:
                result["poses"] = []
                
            return result
            
    def extract_character_details(self, text: str) -> Dict[str, Any]:
        """
        Extract structured character details from unstructured text.
        
        Args:
            text: Unstructured text describing a character
            
        Returns:
            Dictionary of structured character details
        """
        # Define the schema for character details extraction
        schema = {
            "name": "string - the character's full name",
            "physical_description": "string - detailed description of the character's physical appearance",
            "personality_traits": "list of strings - key personality traits",
            "background": "string - summary of the character's background or history",
            "goals": "list of strings - the character's current motivations or objectives",
            "relationships": "object - key-value pairs where keys are names of other characters and values describe their relationship",
            "skills": "list of strings - notable abilities or talents",
            "speaking_style": "string - description of how the character typically speaks"
        }
        
        # Extract structured data using the OpenRouter LLM
        try:
            return self.ai_client.extract_structured_data(
                unstructured_text=text,
                schema=schema,
                temperature=0.3
            )
        except Exception as e:
            # Return partial data if extraction fails
            return {
                "name": "",
                "physical_description": "",
                "personality_traits": [],
                "background": "",
                "goals": [],
                "relationships": {},
                "skills": [],
                "speaking_style": "",
                "error": str(e)
            }
            
    def extract_narrative_elements(self, text: str) -> Dict[str, Any]:
        """
        Extract structured narrative elements from unstructured story text.
        
        Args:
            text: Unstructured narrative or story text
            
        Returns:
            Dictionary of structured narrative elements
        """
        # Define the schema for narrative elements extraction
        schema = {
            "plot_points": "list of strings - key events or developments in the narrative",
            "themes": "list of strings - central themes or motifs",
            "conflicts": "list of strings - main sources of tension or conflict",
            "settings": "list of strings - locations where the narrative takes place",
            "characters": "list of objects - each containing 'name' and 'role' fields",
            "timeline": "list of strings - sequence of events in chronological order",
            "narrative_voice": "string - perspective from which the story is told (first person, third person, etc.)",
            "emotional_arcs": "list of strings - emotional journeys or developments"
        }
        
        # Extract structured data using the OpenRouter LLM
        try:
            return self.ai_client.extract_structured_data(
                unstructured_text=text,
                schema=schema,
                temperature=0.4,
                max_tokens=2000  # More tokens for complex narrative analysis
            )
        except Exception as e:
            # Return partial data if extraction fails
            return {
                "plot_points": [],
                "themes": [],
                "conflicts": [],
                "settings": [],
                "characters": [],
                "timeline": [],
                "narrative_voice": "",
                "emotional_arcs": [],
                "error": str(e)
            }
