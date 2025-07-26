"""
Description writing service for generating detailed physical descriptions from images.

This service follows the same quality standards as the pose enhancer:
- High burstiness (mix of short and long sentences)
- High perplexity (unexpected but fitting word combinations)
- Simple punctuation only (no em-dashes or en-dashes)
- Character control validation
- Proper paragraph formatting
"""

import re
import base64
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from app.services.venice_client import VeniceClient, VeniceAPIError
from app.services.model_config import ModelConfig


@dataclass
class DescriptionResult:
    """Result of a description generation request."""
    description: str
    style: str
    prompt_used: str
    model_used: str
    timestamp: str
    word_count: int
    processing_time_ms: int


class DescriptionService:
    """Service for generating detailed physical descriptions from images."""
    
    def __init__(self, venice_client: VeniceClient):
        """Initialize the description service with a Venice client."""
        self.venice_client = venice_client
        
    def generate_description(
        self,
        image_data: bytes,
        image_format: str,
        user_prompt: str,
        description_style: str = "balanced",
        focus_areas: Optional[List[str]] = None,
        detail_level: int = 70,
        creativity_level: int = 50,
        formality_level: int = 60,
        include_emotional_context: bool = False,
        include_sensory_details: bool = False
    ) -> DescriptionResult:
        """Generate a detailed physical description from an image.
        
        Args:
            image_data: Raw image bytes
            image_format: Image format (jpg, png, webp, etc.)
            user_prompt: User's specific prompt for what to describe
            description_style: Style of description (minimal, balanced, elaborate)
            focus_areas: Optional list of specific areas to focus on
            detail_level: Level of detail (0-100, default 70)
            creativity_level: Level of creative language (0-100, default 50)
            formality_level: Level of formality (0-100, default 60)
            include_emotional_context: Whether to include emotional/mood descriptions
            include_sensory_details: Whether to include sensory descriptions (textures, etc.)
            
        Returns:
            DescriptionResult with the generated description and metadata
            
        Raises:
            VeniceAPIError: If AI processing fails
            ValueError: If the input data is invalid
        """
        start_time = datetime.now()
        
        # Validate inputs
        if not image_data:
            raise ValueError("Image data is required")
        if not user_prompt or not user_prompt.strip():
            raise ValueError("User prompt is required")
        if description_style not in ["minimal", "balanced", "elaborate"]:
            raise ValueError("Description style must be minimal, balanced, or elaborate")
            
        # Convert image to base64 for API
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_url = f"data:image/{image_format};base64,{image_base64}"
        
        # Build system message with quality standards and all settings
        system_message = self._create_system_message(
            description_style, 
            focus_areas,
            detail_level,
            creativity_level,
            formality_level,
            include_emotional_context,
            include_sensory_details
        )
        
        # Create user message with image and prompt
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ]
        }
        
        # Select vision-capable model
        model = self._get_vision_model()
        
        try:
            # Generate description using Venice AI
            response = self.venice_client.generate_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    user_message
                ],
                model=model,
                temperature=self._get_temperature_for_settings(description_style, creativity_level),
                max_tokens=self._get_max_tokens_for_detail_level(detail_level)
            )
            
            # Post-process the description
            processed_description = self._post_process_description(response)
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Count words
            word_count = len(processed_description.split())
            
            return DescriptionResult(
                description=processed_description,
                style=description_style,
                prompt_used=user_prompt,
                model_used=model,
                timestamp=start_time.isoformat(),
                word_count=word_count,
                processing_time_ms=processing_time_ms
            )
            
        except VeniceAPIError:
            raise
        except Exception as e:
            raise VeniceAPIError(f"Failed to generate description: {str(e)}")
    
    def _create_system_message(
        self, 
        style: str, 
        focus_areas: Optional[List[str]] = None,
        detail_level: int = 70,
        creativity_level: int = 50,
        formality_level: int = 60,
        include_emotional_context: bool = False,
        include_sensory_details: bool = False
    ) -> str:
        """Create system message with quality standards and style guidelines.
        
        Args:
            style: Description style (minimal, balanced, elaborate)
            focus_areas: Optional list of specific areas to focus on
            detail_level: Level of detail (0-100)
            creativity_level: Level of creative language (0-100)
            formality_level: Level of formality (0-100)
            include_emotional_context: Whether to include emotional/mood descriptions
            include_sensory_details: Whether to include sensory descriptions
        """
        
        # Base quality requirements
        base_requirements = """You are a professional description writer specializing in detailed physical descriptions. Your writing must follow these strict quality standards:

BURSTINESS REQUIREMENTS:
- Mix very short and very long sentences unpredictably
- Alternate between terse fragments and elaborate descriptions
- Avoid predictable AI patterns - vary sentence structure dramatically
- Use sudden shifts from simple to complex phrasing

PERPLEXITY REQUIREMENTS:
- Choose unexpected but fitting word combinations
- Use unconventional but natural phrasing that feels authentically human
- Avoid clichéd or predictable descriptions
- Select vivid, specific details over generic observations

PUNCTUATION RULES:
- Use ONLY simple punctuation: periods, commas, semicolons, colons
- NO em-dashes (—) or en-dashes (–) - replace with commas or simple alternatives
- Keep punctuation clean and straightforward

DESCRIPTION FOCUS:
- Focus on physical appearance, clothing, posture, and visible characteristics
- Include environmental context only as it relates to the subject
- Describe what you can actually see, not assumptions about personality or emotions
- Use precise, concrete language rather than abstract concepts"""

        # Build dynamic style guidelines based on settings
        style_section = self._build_style_guidelines(style, detail_level)
        
        # Build formality guidelines
        formality_section = self._build_formality_guidelines(formality_level)
        
        # Build creativity guidelines
        creativity_section = self._build_creativity_guidelines(creativity_level)
        
        # Build optional content sections
        optional_sections = self._build_optional_content_sections(
            include_emotional_context, include_sensory_details
        )
        
        # Focus areas if specified
        focus_section = ""
        if focus_areas:
            focus_list = ", ".join(focus_areas)
            focus_section = f"""

SPECIFIC FOCUS AREAS:
Pay particular attention to: {focus_list}
Ensure these areas receive detailed coverage in your description."""
        
        # Combine all sections
        return f"{base_requirements}\n{style_section}\n{formality_section}\n{creativity_section}\n{optional_sections}{focus_section}"
    
    def _build_style_guidelines(self, style: str, detail_level: int) -> str:
        """Build style guidelines that incorporate both style and detail level."""
        base_styles = {
            "minimal": {
                "name": "MINIMAL STYLE",
                "base_sentences": "2-4 sentences",
                "focus": "most striking visual elements",
                "approach": "concise but vivid"
            },
            "balanced": {
                "name": "BALANCED STYLE", 
                "base_sentences": "4-8 sentences",
                "focus": "comprehensive balance of features, clothing, and posture",
                "approach": "moderate detail, well-rounded"
            },
            "elaborate": {
                "name": "ELABORATE STYLE",
                "base_sentences": "8-15+ sentences",
                "focus": "rich, extensive visual information with fine details",
                "approach": "comprehensive and layered descriptions"
            }
        }
        
        style_info = base_styles[style]
        
        # Adjust sentence count based on detail level
        if detail_level <= 30:
            length_modifier = "Keep descriptions shorter and more focused."
        elif detail_level <= 70:
            length_modifier = f"Use approximately {style_info['base_sentences']} typically."
        else:
            length_modifier = "Expand beyond typical length with additional layers of detail."
            
        return f"""
{style_info['name']}:
- {style_info['approach'].capitalize()}
- Focus on {style_info['focus']}
- {length_modifier}
- Detail intensity: {detail_level}% - {'minimal' if detail_level <= 30 else 'moderate' if detail_level <= 70 else 'maximum'} visual information"""
    
    def _build_formality_guidelines(self, formality_level: int) -> str:
        """Build formality guidelines based on formality level."""
        if formality_level <= 30:
            tone = "casual and conversational"
            language = "Use everyday language, contractions, and informal phrasing"
            structure = "Write as if describing to a friend"
        elif formality_level <= 70:
            tone = "professional but approachable"
            language = "Use clear, direct language without being overly casual or formal"
            structure = "Maintain professional clarity while being accessible"
        else:
            tone = "formal and sophisticated"
            language = "Use elevated vocabulary, complete sentences, and precise terminology"
            structure = "Write with academic or professional precision"
            
        return f"""
FORMALITY LEVEL ({formality_level}%):
- Tone: {tone}
- Language: {language}
- Structure: {structure}"""
    
    def _build_creativity_guidelines(self, creativity_level: int) -> str:
        """Build creativity guidelines based on creativity level."""
        if creativity_level <= 30:
            approach = "straightforward and literal"
            language = "Use direct, conventional descriptions"
            metaphors = "Avoid metaphors and creative comparisons"
        elif creativity_level <= 70:
            approach = "balanced creativity"
            language = "Mix conventional descriptions with occasional creative phrasing"
            metaphors = "Use subtle creative elements when they enhance clarity"
        else:
            approach = "highly creative and expressive"
            language = "Use vivid, imaginative language and unexpected word combinations"
            metaphors = "Employ creative metaphors, analogies, and artistic descriptions"
            
        return f"""
CREATIVITY LEVEL ({creativity_level}%):
- Approach: {approach}
- Language style: {language}
- Creative elements: {metaphors}"""
    
    def _build_optional_content_sections(self, include_emotional_context: bool, include_sensory_details: bool) -> str:
        """Build optional content sections based on boolean settings."""
        sections = []
        
        if include_emotional_context:
            sections.append("""
EMOTIONAL CONTEXT ENABLED:
- Include descriptions of apparent mood, expression, and emotional atmosphere
- Describe facial expressions, body language, and overall demeanor
- Note the emotional tone conveyed by posture and positioning""")
            
        if include_sensory_details:
            sections.append("""
SENSORY DETAILS ENABLED:
- Include tactile descriptions of textures, materials, and surfaces
- Describe how things might feel, sound, or even smell when relevant
- Add sensory richness to clothing, hair, skin, and environmental elements""")
            
        return "".join(sections)
    
    def _get_vision_model(self) -> str:
        """Get a vision-capable model from Venice AI."""
        # Use qwen-2.5-vl which actually supports vision according to Venice AI API
        return "qwen-2.5-vl"  # Qwen 2.5 VL 72B - specifically designed for vision tasks
    
    def _get_temperature_for_settings(self, style: str, creativity_level: int) -> float:
        """Get appropriate temperature setting based on style and creativity level."""
        # Base temperature from style
        base_temps = {
            "minimal": 0.6,    # More focused and precise
            "balanced": 0.7,   # Balanced creativity
            "elaborate": 0.8   # More creative and varied
        }
        
        base_temp = base_temps.get(style, 0.7)
        
        # Adjust based on creativity level (0-100)
        # Low creativity (0-30): reduce temperature by up to 0.2
        # High creativity (70-100): increase temperature by up to 0.2
        creativity_adjustment = (creativity_level - 50) * 0.004  # Maps 0-100 to -0.2 to +0.2
        
        final_temp = base_temp + creativity_adjustment
        
        # Clamp between 0.3 and 1.0 for safety
        return max(0.3, min(1.0, final_temp))
    
    def _get_max_tokens_for_detail_level(self, detail_level: int) -> int:
        """Get appropriate max tokens based on detail level."""
        # Map detail level (0-100) to token count
        # Low detail: 800-1200 tokens
        # Medium detail: 1200-2000 tokens  
        # High detail: 2000-3000 tokens
        
        if detail_level <= 30:
            return 1200  # Shorter descriptions
        elif detail_level <= 70:
            return 2000  # Standard length
        else:
            return 3000  # Extended descriptions
    
    def _post_process_description(self, description: str) -> str:
        """Post-process description to ensure quality standards."""
        if not description:
            return ""
        
        # Clean up the description
        processed = description.strip()
        
        # Remove any markdown formatting that might have been added
        processed = re.sub(r'\*\*(.*?)\*\*', r'\1', processed)  # Remove bold
        processed = re.sub(r'\*(.*?)\*', r'\1', processed)      # Remove italic
        processed = re.sub(r'`(.*?)`', r'\1', processed)        # Remove code
        
        # Ensure proper paragraph formatting
        processed = self._ensure_paragraph_formatting(processed)
        
        # Replace complex punctuation with simple alternatives
        processed = self._clean_punctuation(processed)
        
        return processed
    
    def _ensure_paragraph_formatting(self, text: str) -> str:
        """Ensure proper paragraph formatting with clean line breaks."""
        if not text:
            return ""
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Clean up excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)  # Replace 3+ newlines with 2
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Clean mixed whitespace/newlines
        
        # Ensure sentences are properly spaced
        text = re.sub(r'\.(\w)', r'. \1', text)  # Add space after periods
        text = re.sub(r'  +', ' ', text)  # Remove multiple spaces
        
        return text.strip()
    
    def _clean_punctuation(self, text: str) -> str:
        """Replace complex punctuation with simple alternatives."""
        if not text:
            return ""
        
        # Replace em-dashes and en-dashes with commas and spaces
        text = re.sub(r'—', ', ', text)  # Em-dash to comma
        text = re.sub(r'–', '-', text)   # En-dash to hyphen
        text = re.sub(r'[\u2013\u2014\u2015]', ', ', text)  # Unicode dashes
        
        # Clean up any double punctuation that might result
        text = re.sub(r', ,', ',', text)
        text = re.sub(r'  +', ' ', text)
        
        return text
    
    def validate_image_format(self, image_format: str) -> bool:
        """Validate that the image format is supported."""
        supported_formats = ['jpg', 'jpeg', 'png', 'webp', 'gif']
        return image_format.lower() in supported_formats
    
    def get_max_image_size(self) -> int:
        """Get maximum allowed image size in bytes."""
        return 10 * 1024 * 1024  # 10MB limit
