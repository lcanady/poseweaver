"""
Character brain dump processing service for MUSH Pose Editor.

This service handles free-form character descriptions and converts them
into structured character profiles using AI analysis.
"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from app.services.venice_client import VeniceClient, VeniceAPIError


@dataclass
class CharacterProfile:
    """Structured character profile data."""
    name: str
    background: str
    personality: List[str]
    skills: List[str]
    goals: List[str]
    relationships: Dict[str, str]
    voice_notes: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert character profile to dictionary."""
        return asdict(self)


class CharacterService:
    """Service for processing character brain dumps into structured profiles."""
    
    def __init__(self, venice_client: VeniceClient):
        """Initialize the character service.
        
        Args:
            venice_client: Venice.ai client for AI processing
        """
        self.venice_client = venice_client
    
    def process_brain_dump(
        self, 
        brain_dump: str,
        existing_character: Optional[CharacterProfile] = None
    ) -> CharacterProfile:
        """Process a character brain dump into a structured profile.
        
        Args:
            brain_dump: Free-form character description text
            existing_character: Optional existing character to update
            
        Returns:
            CharacterProfile: Structured character data
            
        Raises:
            VeniceAPIError: If AI processing fails
            ValueError: If the AI response is invalid
        """
        try:
            # Extract character information using AI
            character_data = self._extract_character_info(
                brain_dump, existing_character
            )
            
            # Validate the extracted data
            self._validate_character_data(character_data)
            
            # Create and return character profile
            return CharacterProfile(**character_data)
            
        except VeniceAPIError:
            # Re-raise Venice API errors
            raise
        except Exception as e:
            raise ValueError(f"Invalid character data: {str(e)}")
    
    def _extract_character_info(
        self, 
        brain_dump: str,
        existing_character: Optional[CharacterProfile] = None
    ) -> Dict[str, Any]:
        """Extract structured character information from brain dump text.
        
        Args:
            brain_dump: Free-form character description
            existing_character: Optional existing character data
            
        Returns:
            Dict containing structured character information
        """
        # Prepare system message for character analysis
        system_message = self._build_character_analysis_prompt(
            existing_character
        )
        
        # Prepare user message with brain dump
        user_message = f"""
        Analyze the following character description and extract structured information:

        {brain_dump}

        Please respond with a valid JSON object containing the character data.
        """
        
        # Generate completion using Venice.ai
        response = self.venice_client.generate_completion(
            model="venice-uncensored",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Parse JSON response if needed
        if isinstance(response, str):
            try:
                # Try to extract JSON from the response if it's wrapped in text
                response = response.strip()
                print(f"DEBUG: Raw character response: {response[:500]}...")
                
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
                
                character_data = json.loads(response)
            except json.JSONDecodeError as e:
                print(f"DEBUG: Failed to parse character response: {response[:200]}...")
                raise ValueError(f"Invalid JSON response from AI: {str(e)}")
        else:
            # Response is already a dict (from mocked tests)
            character_data = response
        
        # If we have existing character data, merge with new information
        if existing_character:
            existing_data = existing_character.to_dict()
            merged_data = self._merge_character_data(
                existing_data, character_data
            )
            return merged_data
        
        return character_data
    
    def _build_character_analysis_prompt(self, 
                                       existing_character: Optional[CharacterProfile] = None
                                       ) -> str:
        """Build system prompt for character analysis.
        
        Args:
            existing_character: Optional existing character for updates
            
        Returns:
            System prompt string
        """
        base_prompt = """
        You are an expert character analyst for MUSH (Multi-User Shared Hallucination) roleplay.
        Your task is to analyze character descriptions and extract structured information.

        Extract the following information from character descriptions:
        - name: Character's full name
        - background: Character's history, origin, and life story
        - personality: List of personality traits and characteristics
        - skills: List of abilities, talents, and competencies
        - goals: List of character motivations and objectives
        - relationships: Dictionary of important relationships (name: relationship type)
        - voice_notes: Notes about how the character speaks and communicates

        Respond ONLY with a valid JSON object containing these fields.
        Ensure all list fields are arrays and relationships is an object.
        Be creative but consistent with the provided information.
        """
        
        if existing_character:
            existing_data = json.dumps(existing_character.to_dict(), indent=2)
            base_prompt += f"""
            
            IMPORTANT: You are updating an existing character. Here is their current data:
            {existing_data}
            
            Merge new information with existing data. Expand and enhance existing fields
            rather than replacing them completely. Maintain consistency with established
            character elements.
            """
        
        return base_prompt
    
    def _validate_character_data(self, data: Dict[str, Any]) -> None:
        """Validate extracted character data structure.
        
        Args:
            data: Character data dictionary to validate
            
        Raises:
            ValueError: If data structure is invalid
        """
        required_fields = [
            "name", "background", "personality", "skills", 
            "goals", "relationships", "voice_notes"
        ]
        
        # Check for required fields
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate field types
        list_fields = ["personality", "skills", "goals"]
        for field in list_fields:
            if not isinstance(data[field], list):
                raise ValueError(f"Field '{field}' should be a list")
        
        if not isinstance(data["relationships"], dict):
            raise ValueError("Field 'relationships' should be a dictionary")
        
        if not isinstance(data["name"], str) or not data["name"].strip():
            raise ValueError("Field 'name' should be a non-empty string")
        
        if not isinstance(data["background"], str) or not data["background"].strip():
            raise ValueError("Field 'background' should be a non-empty string")
        
        if not isinstance(data["voice_notes"], str):
            raise ValueError("Field 'voice_notes' should be a string")
    
    def _merge_character_data(self, existing_data: Dict[str, Any], 
                             new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge existing character data with new information.
        
        Args:
            existing_data: Current character data
            new_data: New character information to merge
            
        Returns:
            Merged character data dictionary
        """
        merged = existing_data.copy()
        
        # Merge list fields (personality, skills, goals)
        list_fields = ["personality", "skills", "goals"]
        for field in list_fields:
            if field in new_data and isinstance(new_data[field], list):
                # Combine lists and remove duplicates while preserving order
                existing_items = set(merged.get(field, []))
                new_items = new_data[field]
                
                # Start with existing items, then add new ones
                combined = list(merged.get(field, []))
                for item in new_items:
                    if item not in existing_items:
                        combined.append(item)
                
                merged[field] = combined
        
        # Merge relationships dictionary
        if "relationships" in new_data and isinstance(new_data["relationships"], dict):
            merged["relationships"] = {
                **merged.get("relationships", {}),
                **new_data["relationships"]
            }
        
        # Update string fields with new information if provided
        string_fields = ["name", "background", "voice_notes"]
        for field in string_fields:
            if field in new_data and new_data[field]:
                merged[field] = new_data[field]
        
        return merged 