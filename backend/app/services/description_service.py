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

from app.services.openrouter_client import OpenRouterClient, OpenRouterAPIError
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
    
    def __init__(self, openrouter_client: OpenRouterClient):
        """Initialize the description service with a OpenRouter client."""
        self.openrouter_client = openrouter_client
        
    def generate_description(
        self,
        image_data: bytes,
        image_format: str,
        user_prompt: str,
        description_style: str = "balanced",
        focus_areas: Optional[List[str]] = None
    ) -> DescriptionResult:
        """Generate a detailed physical description from an image.
        
        Args:
            image_data: Raw image bytes
            image_format: Image format (jpg, png, webp, etc.)
            user_prompt: User's specific prompt for what to describe
            description_style: Style of description (minimal, balanced, elaborate)
            focus_areas: Optional list of specific areas to focus on
            
        Returns:
            DescriptionResult with the generated description and metadata
            
        Raises:
            OpenRouterAPIError: If AI processing fails
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
        
        # Build system message with quality standards
        system_message = self._create_system_message(description_style, focus_areas)
        
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
            # Generate description using OpenRouter AI
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Generating description with model={model}")
            
            response = self.openrouter_client.generate_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    user_message
                ],
                model=model,
                temperature=self._get_temperature_for_style(description_style),
                max_tokens=1000  # Reduced from 2000 to prevent timeouts
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
            
        except OpenRouterAPIError:
            raise
        except Exception as e:
            raise OpenRouterAPIError(f"Failed to generate description: {str(e)}")
    
    def _create_system_message(self, style: str, focus_areas: Optional[List[str]] = None) -> str:
        """Create system message with quality standards and style guidelines."""
        
        # Base quality requirements (same as pose enhancer)
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

        # Style-specific guidelines
        style_guidelines = {
            "minimal": """
MINIMAL STYLE:
- Keep descriptions concise but vivid
- Focus on the most striking visual elements
- Use 2-4 sentences maximum
- Emphasize key details that define the subject""",
            
            "balanced": """
BALANCED STYLE:
- Provide comprehensive but not overwhelming detail
- Balance physical features with clothing and posture
- Use 4-8 sentences typically
- Include both obvious and subtle visual elements""",
            
            "elaborate": """
ELABORATE STYLE:
- Provide rich, detailed descriptions with extensive visual information
- Include fine details about textures, colors, lighting, and composition
- Use 8-15 sentences or more as needed
- Layer multiple levels of visual information"""
        }
        
        # Focus areas if specified
        focus_section = ""
        if focus_areas:
            focus_list = ", ".join(focus_areas)
            focus_section = f"""
SPECIFIC FOCUS AREAS:
Pay particular attention to: {focus_list}
Ensure these areas receive detailed coverage in your description."""
        
        return f"{base_requirements}\n{style_guidelines[style]}{focus_section}"
    
    def _get_vision_model(self) -> str:
        """Get a vision-capable model from OpenRouter AI."""
        # Use Gemini 2.0 Flash which is fast, reliable and has excellent vision support
        return "google/gemini-2.0-flash-001"
    
    def _get_temperature_for_style(self, style: str) -> float:
        """Get appropriate temperature setting for description style."""
        temperature_map = {
            "minimal": 0.6,    # More focused and precise
            "balanced": 0.7,   # Balanced creativity
            "elaborate": 0.8   # More creative and varied
        }
        return temperature_map.get(style, 0.7)
    
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
