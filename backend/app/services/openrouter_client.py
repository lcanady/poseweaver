import requests
import re
import json
from typing import Optional, Dict, Any, List
from requests.exceptions import ConnectionError, Timeout, RequestException


class OpenRouterAPIError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""
    
    def __init__(self, api_key: str, 
                 base_url: str = "https://openrouter.ai/api/v1"):
        """Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            base_url: Base URL for the API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "PoseWeaver",
            "HTTP-Referer": "https://github.com/lcanady/poseweaver"
        }
        # Make timeout configurable via environment variable
        import os
        self.timeout = int(os.getenv('OPENROUTER_TIMEOUT', '60'))  # seconds
    
    def generate_completion(
        self,
        prompt: str = None,
        model: str = "google/gemini-2.0-flash-001",
        temperature: float = 0.7,
        max_tokens: int = 32000,
        system_message: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a completion using OpenRouter.ai API.
        
        Args:
            prompt: The user prompt
            model: Model to use for generation
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system_message: Optional system message
            messages: Optional list of messages for chat format
            response_format: Optional response format specification for structured outputs
            
        Returns:
            Generated text content
        """
        # Validate API key
        if not self.api_key or self.api_key.strip() == "":
            raise OpenRouterAPIError("API key is required")
        
        if self.api_key == "your_openrouter_api_key_here":
            raise OpenRouterAPIError("Please set your actual OpenRouter API key in the .env file")
        
        # Use mock responses for testing
        if self.api_key.startswith("mock_key"):
            return self._generate_llm_mock_response(messages, model)
        
        # Validate parameters
        if not self.validate_parameters(temperature, max_tokens):
            raise ValueError("Invalid parameters provided")
        
        # Build messages array
        if messages is None:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            if prompt:
                messages.append({"role": "user", "content": prompt})
        
        # Prepare request data
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        
        # Add response_format if provided for structured responses
        if response_format is not None:
            # Ensure proper format according to OpenRouter API requirements
            if "type" in response_format and response_format["type"] == "json_schema":
                # Enforce required settings for OpenRouter structured responses
                if "json_schema" in response_format:
                    if "strict" not in response_format["json_schema"]:
                        response_format["json_schema"]["strict"] = True
                    if "schema" in response_format["json_schema"] and "additionalProperties" not in response_format["json_schema"]["schema"]:
                        response_format["json_schema"]["schema"]["additionalProperties"] = False
            
            data["response_format"] = response_format
        
        # Retry logic for timeout handling
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                
                # Make API request
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"OpenRouter Request: model={model}, temperature={temperature}, max_tokens={max_tokens}")
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    timeout=self.timeout
                )
                
                
                # Process response
                return self._process_response(response)
                
            except requests.exceptions.HTTPError as e:
                # Log the full error response for debugging
                try:
                    error_json = e.response.json()
                    logger.error(f"OpenRouter HTTP Error {e.response.status_code}: {error_json}")
                except:
                    logger.error(f"OpenRouter HTTP Error {e.response.status_code}: {e.response.text}")
                
                raise OpenRouterAPIError(f"HTTP {e.response.status_code}: {str(e)}")
            except Timeout as e:
                retry_count += 1
                if retry_count > max_retries:
                    raise OpenRouterAPIError(f"Request timeout after {max_retries} retries: {str(e)}")
                else:
                    # Wait before retry (exponential backoff)
                    import time
                    wait_time = 2 ** retry_count  # 2, 4, 8 seconds
                    time.sleep(wait_time)
                    continue
                    
            except ConnectionError as e:
                raise OpenRouterAPIError(f"Connection error: {str(e)}")
            except RequestException as e:
                raise OpenRouterAPIError(f"Request failed: {str(e)}")
    
    def _process_response(self, response: requests.Response) -> str:
        """Process API response and extract content.
        
        Args:
            response: HTTP response from OpenRouter API
            
        Returns:
            Generated text content
        """
        try:
            response.raise_for_status()
            response_data = response.json()
            
            # Extract content from response
            if response_data and 'choices' in response_data and response_data['choices']:
                choice = response_data['choices'][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    print(f"[DEBUG] Raw response content: {content[:200]}...")
                    
                    # Remove <think></think> tags and their content
                    import re
                    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
                    content = content.strip()
                    print(f"[DEBUG] Cleaned response content: {content[:200]}...")
                    
                    return content
                elif "text" in choice:
                    return choice["text"]
            
            raise OpenRouterAPIError("No content found in API response")
            
        except requests.exceptions.HTTPError:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg += f": {error_data['error']}"
            except Exception:
                error_msg += f": {response.text}"
            raise OpenRouterAPIError(error_msg)
        except ValueError as e:
            raise OpenRouterAPIError(f"Invalid JSON response: {str(e)}")

    def _generate_llm_mock_response(self, messages: List[Dict[str, str]], 
                                    model: str) -> str:
        """Generate mock responses using LLM-style structured data extraction."""
        # Get the user message content
        user_content = ""
        system_content = ""
        
        if messages:
            for msg in messages:
                if msg.get("role") == "user":
                    user_content = msg.get("content", "")
                elif msg.get("role") == "system":
                    system_content = msg.get("content", "")
        
        # Determine the type of request based on system message and user content
        request_type = self._identify_request_type(system_content, user_content)
        
        if request_type == "data_extraction":
            return self._generate_data_extraction_response(user_content)
        elif request_type == "character_processing":
            return self._generate_character_profile_response(user_content)
        elif request_type == "context_analysis":
            return self._generate_context_analysis_response(user_content)
        elif request_type == "pose_enhancement":
            return self._generate_pose_enhancement_response(user_content)
        elif request_type == "pose_variations":
            return self._generate_pose_variations_response(user_content)
        else:
            # Fallback for unknown requests
            return self._generate_generic_response(user_content)
    
    def _identify_request_type(self, system_content: str, 
                               user_content: str) -> str:
        """Identify the type of request based on system and user messages."""
        combined_content = (system_content + " " + user_content).lower()
        
        # Debug logging
        print(f"DEBUG: System content: {system_content[:100]}...")
        print(f"DEBUG: User content: {user_content[:100]}...")
        print(f"DEBUG: Combined content: {combined_content[:200]}...")
        
        # Check for data extraction requests first (most specific)
        if (("data extraction assistant" in combined_content) or
            ("extract the following structured information" in combined_content) or
            ("output only valid json" in combined_content) or
            ("structured data" in combined_content and "extract" in combined_content)):
            print("DEBUG: Identified as data_extraction")
            return "data_extraction"
        
        # Check for context analysis (pose context analysis) - check first as it's more specific
        elif (("context" in combined_content and "analyze" in combined_content) or
            ("pose" in combined_content and "context" in combined_content) or
            ("scene analyst" in combined_content) or
            ("response opportunities" in combined_content) or
            ("roleplay pose" in combined_content and "extract" in combined_content)):
            print("DEBUG: Identified as context_analysis")
            return "context_analysis"
        
        # Check for character processing (brain dump analysis)
        elif ("character" in combined_content and 
              ("brain dump" in combined_content or 
               ("analyze" in combined_content and "structured" in combined_content and "brain dump" in combined_content))):
            print("DEBUG: Identified as character_processing")
            return "character_processing"
        
        # Check for pose enhancement
        elif ("enhance" in combined_content and "pose" in combined_content):
            print("DEBUG: Identified as pose_enhancement")
            return "pose_enhancement"
        
        # Check for pose variations
        elif ("variations" in combined_content and "pose" in combined_content):
            print("DEBUG: Identified as pose_variations")
            return "pose_variations"
        
        else:
            print("DEBUG: Identified as unknown")
            return "unknown"
    
    def _extract_character_name_llm(self, content: str) -> str:
        """Extract character name using LLM-style intelligent analysis."""
        # Try to parse as JSON first
        try:
            data = json.loads(content)
            if 'character_name' in data and data['character_name']:
                return data['character_name'].strip()
            if 'character' in data and isinstance(data['character'], dict):
                if 'name' in data['character'] and data['character']['name']:
                    return data['character']['name'].strip()
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
        
        # Look for structured patterns first
        patterns = [
            r'"character_name":\s*"([^"]+)"',
            r'"name":\s*"([^"]+)"',
            r'personality breakdown of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'character:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'name:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|was|has|offers|values)',
            r'"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),"?\s+(?:he|she|they)\s+(?:says|thinks|feels)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                if name.lower() not in ['llm', 'ai', 'assistant', 'system', 'user', 'character', 'personality']:
                    return name
        
        # Default fallback
        return "Character"

    def _extract_pose_text_from_content(self, content: str) -> str:
        """Extract pose text from user content for analysis."""
        # Look for pose text patterns in the content
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Skip empty lines and structural text
            if not line or line.startswith('{') or line.startswith('['):
                continue
            # Skip instruction lines
            if any(word in line.lower() for word in [
                'analyze', 'extract', 'respond', 'please', 'json'
            ]):
                continue
            # Look for narrative content that looks like a pose
            if len(line) > 20 and any(word in line.lower() for word in [
                'examines', 'looks', 'moves', 'walks', 'says', 'steps', 
                'turns', 'glances', 'approaches', 'studies'
            ]):
                return line
        
        # Fallback
        return "The character performs an action."
    
    def _extract_original_pose_llm(self, content: str) -> str:
        """Extract original pose using LLM-style intelligent analysis."""
        # Try JSON parsing first
        try:
            data = json.loads(content)
            if 'original_pose' in data:
                return data['original_pose']
            if 'pose' in data:
                return data['pose']
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
        
        # Look for structured pose patterns
        patterns = [
            r'"original_pose":\s*"([^"]+)"',
            r'"pose":\s*"([^"]+)"',
            r'original pose:\s*"([^"]+)"',
            r'pose:\s*"([^"]+)"',
            r'enhance this pose:\s*"([^"]+)"',
            r'original:\s*"([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Look for narrative content that looks like a pose
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('{') and not line.startswith('['):
                # Check if this looks like a pose (contains action words)
                action_words = ['says', 'looks', 'moves', 'walks', 'runs', 'sits', 'stands', 'turns', 'smiles', 'frowns']
                if any(word in line.lower() for word in action_words):
                    return line
        
        # Fallback
        return "The character performs an action."
    
    def _generate_data_extraction_response(self, user_content: str) -> str:
        """Generate data extraction response for Discord roleplay parsing."""
        # Parse Discord format and extract character names from content
        poses = []
        
        # Split by Discord message pattern
        import re
        import json
        discord_pattern = r'([A-Za-z0-9_\-\']+)\s+—\s+(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[AP]M)'
        
        # Split the content by Discord headers
        parts = re.split(discord_pattern, user_content)
        
        current_pose = None
        for i, part in enumerate(parts):
            if i == 0:
                continue  # Skip the first empty part
            
            if i % 4 == 1:  # Username
                discord_username = part
            elif i % 4 == 2:  # Date
                date = part
            elif i % 4 == 3:  # Time
                time = part
            elif i % 4 == 0:  # Content
                content = part.strip()
                if content:
                    # Extract character name from content
                    character_name = self._extract_character_name_from_discord_content(content)
                    if not character_name:
                        character_name = discord_username  # Fallback to Discord username
                    
                    poses.append({
                        "character_name": character_name,
                        "content": content,
                        "pose_type": "mixed",
                        "is_ooc": False
                    })
        
        # Extract all character names mentioned
        all_character_names = list(set([pose["character_name"] for pose in poses]))
        
        response_data = {
            "poses": poses,
            "room_description": "",
            "characters_present": all_character_names,
            "your_character": None
        }
        
        return json.dumps(response_data, indent=2)
    
    def _extract_character_name_from_discord_content(self, content: str) -> str:
        """Extract character name from Discord pose content."""
        if not content:
            return ""
            
        # Look for common patterns that indicate character names
        patterns = [
            # Pattern 1: First sentence often starts with character name
            r'^([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\s+(?:is|was|has|had|seems|looks|moves|walks|sits|stands|takes|needed|followed|drops|grabs|joins|pauses|shifts|narrows|searches|catches)',
            # Pattern 2: Look for possessive forms
            r'(?:^|\.\s+)([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\'s\s+(?:eyes|face|body|hand|hair|voice|gaze|laugh|attitude|progress|sigh|grip)',
            # Pattern 3: Look for character name in middle of sentence
            r'\b([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\s+(?:takes|moves|walks|runs|jumps|looks|glances|stares|smiles|frowns|nods|shakes|pays|drops|grabs|dives|intertwines)',
            # Pattern 4: Look for "As [Character]" patterns
            r'As\s+(?:more\s+of\s+)?([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\s+(?:is|was|has|had)',
            # Pattern 5: Look for character names in dialogue attribution
            r'([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\s+(?:says|asks|whispers|shouts|calls|replies|tests|gazes)',
            # Pattern 6: Look for "Her/His [body part]" followed by character name context
            r'(?:Her|His)\s+(?:eyes|face|body|hand|hair|voice|gaze)\s+.*?([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\s+(?:hasn\'t|has|is|was)',
            # Pattern 7: Look for character names after "If"
            r'If\s+(?:she\'s\s+noticed\s+)?([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\'s',
            # Pattern 8: Look for "Catching [Character]'s" patterns
            r'Catching\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\'s',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1)
                # Filter out common false positives
                if name.lower() not in ['the', 'and', 'but', 'she', 'he', 'they', 'it', 'this', 'that', 'with', 'from', 'into', 'onto', 'her', 'his', 'their']:
                    return name
                    
        return ""
    
    def _generate_character_profile_response(self, user_content: str) -> str:
        """Generate character profile response using extracted data."""
        character_name = self._extract_character_name_llm(user_content)
        
        response_data = {
            "name": character_name,
            "background": f"{character_name} is a complex character with a rich history and deep motivations.",
            "personality": [
                "Thoughtful and introspective",
                "Loyal to friends and allies",
                "Determined in pursuit of goals",
                "Compassionate towards others"
            ],
            "skills": [
                "Skilled in combat and strategy",
                "Knowledgeable about history and lore",
                "Excellent at reading people",
                "Natural leader"
            ],
            "goals": [
                "Protect those who cannot protect themselves",
                "Uncover the truth about their past",
                "Build lasting relationships",
                "Make a positive impact on the world"
            ],
            "relationships": {
                "allies": "Trusted companions who share similar values",
                "enemies": "Those who oppose justice and peace",
                "mentors": "Wise figures who provided guidance",
                "family": "Complex relationships with deep emotional ties"
            },
            "voice_notes": f"{character_name} speaks with confidence and conviction, often using metaphors and references to their experiences. Their tone is warm with friends but can become stern when facing injustice."
        }
        
        return json.dumps(response_data, indent=2)
    
    def _generate_context_analysis_response(self, user_content: str) -> str:
        """Generate context analysis response using extracted data."""
        # Extract pose text from user content for more contextual analysis
        pose_text = self._extract_pose_text_from_content(user_content)
        
        # Generate appropriate mock response based on the expected structure
        response_data = {
            "actions": [
                "examining the artifact",
                "stepping closer",
                "narrowing eyes",
                "studying symbols"
            ],
            "emotions": [
                "curiosity",
                "caution",
                "fascination",
                "concentration"
            ],
            "environmental_details": [
                "ancient artifact",
                "strange symbols",
                "dim lighting",
                "mysterious atmosphere"
            ],
            "character_interactions": [
                "observing others",
                "potential for collaboration",
                "shared discovery moment"
            ],
            "response_hooks": [
                "artifact's purpose",
                "symbol meanings",
                "character's reaction",
                "next discovery step"
            ],
            "scene_timing": "present",
            "urgency_level": "low",
            "narrative_tone": "mysterious"
        }
        
        return json.dumps(response_data, indent=2)
    
    def _generate_pose_enhancement_response(self, user_content: str) -> str:
        """Generate pose enhancement response using extracted data."""
        character_name = self._extract_character_name_llm(user_content)
        original_pose = self._extract_original_pose_llm(user_content)
        
        response_data = {
            "character_name": character_name,
            "original_pose": original_pose,
            "enhanced_pose": f'{character_name} {original_pose.lower() if original_pose else "moves with purpose"}, their eyes reflecting the depth of their experiences as they navigate the complexities of the moment with both grace and determination.',
            "enhancement_notes": [
                "Added emotional depth and character motivation",
                "Incorporated sensory details for immersion",
                "Enhanced the character's unique voice and perspective",
                "Improved flow and narrative structure"
            ],
            "style_applied": "Descriptive and character-focused with emphasis on internal motivation",
            "suggestions": [
                "Consider adding dialogue to reveal character thoughts",
                "Include reactions from other characters if present",
                "Expand on the environmental details",
                "Add physical gestures that reflect emotional state"
            ]
        }
        
        return json.dumps(response_data, indent=2)
    
    def _generate_pose_variations_response(self, user_content: str) -> str:
        """Generate pose variations response using extracted data."""
        character_name = self._extract_character_name_llm(user_content)
        original_pose = self._extract_original_pose_llm(user_content)
        
        response_data = {
            "character_name": character_name,
            "original_pose": original_pose,
            "variations": [
                {
                    "style": "Action-focused",
                    "pose": f"{character_name} springs into action, their movements swift and decisive as they respond to the situation with practiced efficiency."
                },
                {
                    "style": "Emotional",
                    "pose": f"A complex mix of emotions plays across {character_name}'s features as they process the moment, their inner turmoil evident in their hesitant movements."
                },
                {
                    "style": "Descriptive",
                    "pose": f"The soft light catches {character_name}'s profile as they stand quietly, their presence commanding attention despite their stillness."
                },
                {
                    "style": "Dialogue-heavy",
                    "pose": f'"{character_name} speaks with quiet conviction, their words carrying the weight of experience and hard-won wisdom."'
                }
            ]
        }
        
        return json.dumps(response_data, indent=2)
    
    def _generate_generic_response(self, user_content: str) -> str:
        """Generate a generic response for unknown request types."""
        return json.dumps({
            "message": "I understand you're looking for assistance. Could you please provide more specific information about what you'd like me to help you with?",
            "type": "generic_response"
        }, indent=2)
    
    def validate_model_name(self, model: str) -> bool:
        """Validate model name format.
        
        Args:
            model: Model name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not model or not isinstance(model, str):
            return False
        
        # Allow alphanumeric, hyphens, dots, and underscores
        pattern = r'^[a-zA-Z0-9\-\._]+$'
        return bool(re.match(pattern, model))
    
    def validate_parameters(self, temperature: float, max_tokens: int) -> bool:
        """Validate generation parameters.
        
        Args:
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not (0.0 <= temperature <= 1.0):
            raise ValueError("Temperature must be between 0.0 and 1.0")
        
        if not (1 <= max_tokens < 100000):
            raise ValueError("max_tokens must be between 1 and 99999")
        
        return True
    
    def get_available_models(self) -> List[str]:
        """Get list of available models.
        
        Returns:
            List of available model names
        """
        # For now, return a hardcoded list of common models
        # In a real implementation, this might query the API
        return [
            "dolphin-2.9-llama3-70b",
            "gpt-3.5-turbo",
            "gpt-4",
            "claude-3-opus",
            "claude-3-sonnet"
        ]
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model.
        
        Args:
            model: Model name
            
        Returns:
            Dictionary with model information
        """
        model_info = {
            "dolphin-2.9-llama3-70b": {
                "name": "Dolphin 2.9 Llama3 70B",
                "description": "Uncensored model based on Llama3 70B",
                "supports_thinking": True,
                "max_context": 8192,
                "recommended_temperature": 0.7
            }
        }
        
        return model_info.get(model, {
            "name": model,
            "description": "Unknown model",
            "supports_thinking": False,
            "max_context": 4096,
            "recommended_temperature": 0.7
        })
        
    def extract_structured_data(self, 
                               unstructured_text: str, 
                               schema: Dict[str, Any],
                               model: str = "google/gemini-2.0-flash-001",
                               temperature: float = 0.5,
                               max_tokens: int = 8000) -> Dict[str, Any]:
        """Extract structured data from unstructured text using the LLM.
        
        Args:
            unstructured_text: Raw unstructured text to process
            schema: Dictionary describing the structure to extract.
                    For example: {
                      "title": "string - extract the title",
                      "characters": "list of strings - extract character names",
                      "settings": "list of strings - extract setting descriptions",
                      "mood": "string - extract the overall mood",
                      "events": "list of strings - extract key events"
                    }
            model: Model to use for extraction
            temperature: Sampling temperature (lower is more deterministic)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary of extracted structured data matching the schema
        """
        # Validate the schema is a dictionary
        if not isinstance(schema, dict):
            raise ValueError("Schema must be a dictionary")
        
        # Create a OpenRouter structured response format JSON schema
        properties = {}
        required_fields = []
        
        # Convert the description schema to actual JSON schema properties
        for key, description in schema.items():
            required_fields.append(key)
            
            # Parse the type from the description
            if "list of" in description.lower() or "array of" in description.lower():
                properties[key] = {
                    "type": "array",
                    "items": {"type": "string"}
                }
            elif "object" in description.lower() or "dict" in description.lower() or "dictionary" in description.lower():
                properties[key] = {
                    "type": "object",
                    "additionalProperties": {"type": "string"}
                }
            else:
                # Default to string type
                properties[key] = {"type": ["string", "null"]}
                
        # Create the response format structure
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "extracted_data",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required_fields,
                    "additionalProperties": False
                }
            }
        }
        
        # Create system prompt instructing the LLM how to interpret the data
        schema_description = "\n".join([f"{key}: {description}" for key, description in schema.items()])
        system_message = f"""You are a data extraction assistant. Extract the following structured information from the user's text:
        
        {schema_description}
        
        Use only the information explicitly present in the text.
        If information for a field is not found, use null for strings or [] for lists."""
        
        # Setup messages for the API call
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": unstructured_text}
        ]
        
        # Call the LLM API with structured response format
        try:
            response = self.generate_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )
            
            # With proper response_format, the response should already be valid JSON
            structured_data = json.loads(response)
            return structured_data
        except json.JSONDecodeError as e:
            # Fallback to cleaning the response in case the model added any markdown
            try:
                cleaned_response = re.sub(r'^\s*```(?:json)?\s*|\s*```\s*$', '', response, flags=re.MULTILINE)
                structured_data = json.loads(cleaned_response)
                return structured_data
            except json.JSONDecodeError:
                raise OpenRouterAPIError(f"Failed to parse structured data from LLM response: {str(e)}. Response: {response}")
        except Exception as e:
            raise OpenRouterAPIError(f"Error extracting structured data: {str(e)}. Response: {response if 'response' in locals() else 'No response'}")