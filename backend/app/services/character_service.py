"""
Character brain dump processing service for MUSH Pose Editor.

This service handles free-form character descriptions and converts them
into structured character profiles using AI analysis.
"""
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from flask import current_app
from app.services.ai_client import AIClient, OpenRouterAPIError


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
    
    def __init__(self, ai_client: AIClient):
        """Initialize the character service.
        
        Args:
            ai_client: OpenRouter.ai client for AI processing
        """
        self.ai_client = ai_client
    
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
            OpenRouterAPIError: If AI processing fails
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
            
        except OpenRouterAPIError:
            # Re-raise OpenRouter API errors
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
        
        # Generate completion using OpenRouter.ai
        response = self.ai_client.generate_completion(
            model="qwen3-235b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=16000  # Much higher token limit for detailed character analysis
        )
        
        # Parse JSON response if needed
        if isinstance(response, str):
            try:
                # Try to extract JSON from the response if it's wrapped in text
                response = response.strip()
                print(f"DEBUG: Raw character response: {response[:500]}...")
                
                # More robust JSON extraction logic
                if '```json' in response or '```' in response:
                    # First try to find json code block
                    json_start = response.find('```json')
                    if json_start == -1:
                        json_start = response.find('```')
                    
                    if json_start != -1:
                        # Skip past the code block markers
                        content_start = response.find('\n', json_start) + 1
                        json_end = response.find('```', content_start)
                        
                        if json_end != -1:
                            # Extract content between code block markers
                            extracted_json = response[content_start:json_end].strip()
                            print(f"DEBUG: Extracted JSON from code block: {extracted_json[:100]}...")
                            response = extracted_json
                
                # Fallback approach: find the first { and last }
                if not response.startswith('{'):
                    start = response.find('{')
                    if start != -1:
                        response = response[start:]
                
                if not response.rstrip().endswith('}'):
                    end = response.rfind('}')
                    if end != -1:
                        response = response[:end+1]
                
                print(f"DEBUG: Cleaned JSON for parsing: {response[:100]}...")
                character_data = json.loads(response)
                print("DEBUG: JSON successfully parsed!")
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

        Extract the following information from character descriptions and adhere to these format requirements:
        - name: Character's full name (MUST BE A STRING)
        - background: Character's history, origin, and life story (MUST BE A STRING)
        - personality: List of personality traits and characteristics (MUST BE AN ARRAY)
        - skills: List of abilities, talents, and competencies (MUST BE AN ARRAY)
        - goals: List of character motivations and objectives (MUST BE AN ARRAY)
        - relationships: Dictionary of important relationships (name: relationship type) (MUST BE AN OBJECT)
        - voice_notes: Notes about how the character speaks and communicates (MUST BE A STRING)

        IMPORTANT FORMAT REQUIREMENTS:
        1. Respond ONLY with a valid JSON object containing these fields.
        2. String fields (name, background, voice_notes) MUST be returned as strings, not arrays/lists.
        3. List fields (personality, skills, goals) MUST be arrays.
        4. The relationships field MUST be an object (dictionary).
        
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
        
        # Define expected field types
        list_fields = ["personality", "skills", "goals"]
        string_fields = ["name", "background", "voice_notes"]
        
        # Validate list fields
        for field in list_fields:
            if field in data and not isinstance(data[field], list):
                raise ValueError(f"Field '{field}' should be a list")
        
        # Convert list fields to strings if necessary
        for field in string_fields:
            if field in data:
                if isinstance(data[field], list):
                    # If it's a list, convert to string for consistency
                    current_app.logger.info(f"Converting {field} from list to string")
                    data[field] = "\n\n".join(str(item) for item in data[field])
                elif not isinstance(data[field], str):
                    raise ValueError(f"Field '{field}' should be a string or list of strings")
        
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