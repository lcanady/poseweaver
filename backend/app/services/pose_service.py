"""
Pose enhancement service for MUSH Pose Editor.

This service transforms basic actions into rich, detailed narratives
while maintaining character voice consistency and context integration.
Now integrated with scene memory and continuity tracking.
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging
from datetime import datetime
from app.services.openrouter_client import OpenRouterClient, OpenRouterAPIError
from app.services.model_config import ModelConfig
from app.services.character_service import CharacterProfile
from app.services.context_service import PoseContext
from app.services.mush_parser_service import MushParserService, ParsedScene
from app.services.scene_service import SceneService
from app.services.data_extraction_service import DataExtractionService
# Continuity system imports
from app.services.scene_management_service import (
    SceneManagementService, PoseData
)

from app.services.character_state_service import CharacterStateService
from app.services.environment_state_service import EnvironmentStateService
from app.models.scene_memory import PoseType


@dataclass
class PoseEnhancement:
    """Enhanced pose with metadata and continuity analysis."""
    original_pose: str
    enhanced_pose: str
    enhancement_notes: List[str]
    sensory_details: List[str]
    character_voice_elements: List[str]
    narrative_techniques: List[str]

    character_state_changes: Optional[List[Dict[str, Any]]] = None
    environment_changes: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pose enhancement to dictionary."""
        result = asdict(self)

        return result


class PoseService:
    """Service for generating and enhancing character poses"""
    
    def __init__(self, openrouter_client: OpenRouterClient):
        """Initialize the pose service with a OpenRouter client."""
        self.openrouter_client = openrouter_client
        self.data_extraction_service = DataExtractionService(openrouter_client)
        self.mush_parser = MushParserService(self.data_extraction_service)
        # Initialize continuity services
        self.scene_management_service = SceneManagementService()
        self.character_state_service = CharacterStateService(openrouter_client)
        self.environment_state_service = EnvironmentStateService(openrouter_client)
    
    def enhance_pose(
        self,
        original_pose: str,
        character: Optional[CharacterProfile] = None,
        context: Optional[PoseContext] = None,
        enhancement_style: str = "balanced",
        enhancement_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enhance a basic pose into rich narrative.
        
        Args:
            original_pose: The original pose text to enhance
            character: Optional character profile for voice consistency
            context: Optional scene context for integration
            enhancement_style: Style of enhancement (minimal, balanced, elaborate)
            
        Returns:
            Dict[str, Any]: Enhanced pose data with validation warnings
            
        Raises:
            OpenRouterAPIError: If AI processing fails
            ValueError: If the AI response is invalid
        """
        try:
            # Generate enhanced pose using AI
            enhancement_data = self._generate_pose_enhancement(
                original_pose, character, context, enhancement_style, enhancement_options
            )
            
            # Return the enhancement data directly
            return enhancement_data
            
        except OpenRouterAPIError:
            # Re-raise OpenRouter API errors
            raise
        except Exception as e:
            raise ValueError(f"Invalid enhancement data: {str(e)}")
    
    def enhance_pose_with_scene_flow(
        self,
        original_pose: str,
        scene_context: str,
        character: Optional[CharacterProfile] = None,
        enhancement_style: str = "balanced"
    ) -> PoseEnhancement:
        """Enhance a pose using scene flow context.
        
        Args:
            original_pose: The original pose text to enhance
            scene_context: Formatted scene context from scene flow
            character: Optional character profile for voice consistency
            enhancement_style: Style of enhancement (minimal, balanced, elaborate)
            
        Returns:
            PoseEnhancement: Enhanced pose with metadata
            
        Raises:
            OpenRouterAPIError: If AI processing fails
            ValueError: If the AI response is invalid
        """
        try:
            # Generate enhanced pose using scene flow context
            enhancement_data = self._generate_pose_enhancement_with_scene_context(
                original_pose, scene_context, character, enhancement_style
            )
            
            # Validate the enhancement data
            self._validate_enhancement_data(enhancement_data)
            
            # Create and return pose enhancement
            return PoseEnhancement(**enhancement_data)
            
        except OpenRouterAPIError:
            # Re-raise OpenRouter API errors
            raise
        except Exception as e:
            raise ValueError(f"Invalid enhancement data: {str(e)}")
    
    def _generate_pose_enhancement(
        self,
        original_pose: str,
        character: Optional[CharacterProfile] = None,
        context: Optional[PoseContext] = None,
        enhancement_style: str = "balanced",
        enhancement_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate enhanced pose using AI.
        
        Args:
            original_pose: The original pose to enhance
            character: Optional character profile
            context: Optional scene context
            enhancement_style: Enhancement style preference
            
        Returns:
            Dict containing enhancement data
        """
        # Prepare system message for pose enhancement
        system_message = ModelConfig.get_system_message_for_use_case(
            "roleplay_enhancement"
        )
        
        # Build character context
        character_context = ""
        if character:
            character_context = f"""
            Character Information:
            - Name: {character.name}
            - Background: {character.background}
            - Personality: {', '.join(character.personality)}
            - Voice Notes: {character.voice_notes}
            """
        
        # Build scene context
        scene_context = ""
        if context:
            scene_context = f"""
            Scene Context:
            - Actions in scene: {', '.join(context.actions)}
            - Emotional tone: {', '.join(context.emotions)}
            - Environment: {', '.join(context.environmental_details)}
            - Narrative tone: {context.narrative_tone}
            - Urgency: {context.urgency_level}
            """
        
        # Build enhancement style guidance
        style_guidance = self._get_style_guidance(enhancement_style)
        
        # Analyze original pose paragraph structure
        original_paragraph_count = original_pose.count('\n\n') + 1
        original_paragraphs = original_pose.split('\n\n')
        
        # Create paragraph template showing the exact structure to follow
        paragraph_template = ""
        for i, paragraph in enumerate(original_paragraphs, 1):
            # Show first 50 chars of each paragraph as template
            preview = paragraph[:50].replace('\n', ' ').strip()
            if len(paragraph) > 50:
                preview += "..."
            paragraph_template += f"Paragraph {i}: [{preview}] → [ENHANCE THIS]\n"
        
        # Create explicit output format example
        output_format_example = ""
        for i in range(original_paragraph_count):
            if i > 0:
                output_format_example += "\n\n"
            output_format_example += f"[Enhanced paragraph {i+1} text goes here]"
        
        # Prepare user message for plain text response
        user_message = f"""
        Transform the following roleplay pose using minimal scene dressing, focusing on direct action and essential elements only:

        ORIGINAL POSE:
        {original_pose}

        {character_context}
        {scene_context}
        
        ENHANCEMENT STYLE: {enhancement_style}
        {style_guidance}

        🚨 CRITICAL ROLEPLAY RULES - MAIN CHARACTER ONLY 🚨:
        - ONLY enhance actions, thoughts, and reactions of the MAIN CHARACTER
        - NEVER pose for other characters, NPCs, or control their actions/dialogue
        - NEVER make other characters react, speak, or move
        - NEVER describe other characters' physical reactions, trembles, shifts, 
          or responses
        - NEVER say what the main character's actions "elicit", "cause", or 
          "make" others do
        - NEVER describe how others respond to the main character's actions
        - Other characters can be mentioned in observations but NEVER controlled 
          or described reacting
        - Focus on the main character's perspective, internal thoughts, and 
          sensory experiences
        - The main character can feel, see, or sense things, but cannot control 
          how others react
        - NEVER describe mutual experiences, shared moments, or "both characters" 
          doing anything
        - Focus SOLELY on what the main character individually does, thinks, 
          and feels

        ❌ FORBIDDEN EXAMPLES (These will result in immediate rejection):
        - "She squeaks out a response" (controlling other character's vocal reaction)
        - "Her squeak of response is music to his ears" (controlling other character's reaction)
        - "He can feel her tremble" (describing other character's physical response)
        - "He can feel the slight tremor in her muscles" (describing other character's body)
        - "The way her breath hitches" (controlling other character's involuntary reaction)
        - "Her body leans into his" (controlling other character's movement)
        - "In the soft moan that escapes her" (controlling other character's sounds)
        - "She responds with..." (making other character react)
        - "Both of them feel..." (mutual experiences)
        - "Making her..." (causing other character to do something)
        - "That escapes her" (controlling other character's involuntary actions)
        - "From her lips" (describing other character's body parts doing things)

        ✅ ACCEPTABLE EXAMPLES (Focus only on main character):
        - "He listens for any sound from her" (main character's action)
        - "He feels the warmth radiating from her skin" (main character's sensation)
        - "He wonders if she's enjoying this" (main character's thoughts)
        - "His heart pounds as he moves closer" (main character's reaction)
        - "He notices her stillness" (main character's observation)
        - "He hopes she feels comfortable" (main character's internal desire)

        CRITICAL: ONLY ENHANCE THE MAIN CHARACTER:
        - You may write about the main character in any perspective (first or third person)
        - "Eli moves closer" or "I move closer" are both acceptable for the main character
        - Focus exclusively on the main character's actions, thoughts, and experiences
        - Describe what the main character does, feels, thinks, sees, hears, touches
        - Include the main character's internal monologue and physical reactions
        - Show the main character's perspective and sensory experiences

        CRITICAL: FAITHFUL ENHANCEMENT ONLY
        - STAY TRUE to the original pose - do not invent new actions or details
        - ENHANCE what is already there, don't add completely new elements
        - If the original says "moves closer", enhance the movement, don't add new actions
        - If the original mentions "heart racing", enhance that feeling, don't add new emotions
        - Focus on expanding and deepening existing elements, not creating new ones
        - NO alliteration, flowery language, poetic descriptions, or scene painting
        - Keep the tone and style consistent with the original pose
        - Enhancement should feel like a natural expansion, not a complete rewrite

        ADVANCED WRITING TECHNIQUES TO APPLY:

        1. MINIMAL SCENE DRESSING:
        - Focus on actions and dialogue rather than detailed descriptions
        - Use concise, direct language instead of elaborate prose
        - Minimize descriptive adjectives and adverbs
        - Present only essential information needed for narrative clarity
        - Skip detailed atmospheric elements and mood-setting descriptions
        - Avoid unnecessary embellishment and excessive sensory details
        
        2. DIRECT PHYSICAL EXPERIENCE:
        - Focus on immediate, simple physical actions
        - Describe core actions without embellishment
        - Be selective about which physical reactions to include
        - Show direct cause-and-effect with minimal elaboration

        3. SELECTIVE SENSORY DETAILS:
        - Use only the most essential sensory information
        - Limit descriptive language to what's necessary
        - Focus on clarity over immersion
        - Choose one or two key sensory details rather than many

        4. NATURAL VOICE ENHANCEMENT:
        - Use straightforward sentence structure
        - Choose direct, simple word choices that match the original tone
        - Enhance existing language patterns minimally
        - Maintain the original character's voice and style
        - Avoid any flowery or elaborate language

        5. CONCISE EMOTIONAL EXPRESSION:
        - State emotions directly rather than through elaborate description
        - Limit physical manifestations of feelings
        - Focus on core emotional states without extensive elaboration
        - Demonstrate emotional responses efficiently

        6. MINIMAL ENVIRONMENTAL REFERENCES:
        - Include only the most critical environmental details
        - Mention surroundings only when directly relevant to action
        - Minimize descriptions of setting, weather, or atmosphere
        - Focus only on environmental elements essential to the scene

        FORMATTING REQUIREMENTS:
        - MANDATORY: Break the enhanced pose into multiple paragraphs (minimum 3-5)
        - Use double line breaks (\\n\\n) between paragraphs for clear separation
        - Create distinct paragraphs for different actions/moments/sensations
        - Each paragraph should focus on a specific moment, action, or sensation
        - Structure: First paragraph (initial action) → Middle paragraphs (sensory details, 
          thoughts, reactions) → Final paragraph (culminating moment or emotional state)
        - Vary paragraph lengths for natural rhythm and pacing
        - NEVER write everything as one continuous paragraph block

        QUALITY BENCHMARKS:
        - Every sentence should enhance existing elements from the original
        - No sentence should add completely new actions or details not implied
        - The enhanced prose should feel like a natural expansion of the original
        - Focus on deepening what's already there, not creating new content
        
        NATURAL HUMAN-LIKE WRITING TECHNIQUES:
        
        1. BURSTINESS:
        - Vary sentence lengths dramatically - mix very short sentences with longer ones
        - Include occasional abrupt transitions between thoughts
        - Use sentence fragments sometimes. Like this.
        - Don't make every sentence perfectly structured
        - Occasionally use emphasis through repetition, repetition, repetition
        - Include natural breaks in flow and thinking patterns
        - Balance complex ideas with simple, direct statements
        - Use parenthetical asides (like this one) to add personal touches
        
        2. PERPLEXITY:
        - Avoid perfectly predictable language patterns
        - Include occasional unexpected word choices or phrasings
        - Mix formal and informal language naturally
        - Add moments of self-reflection or uncertainty when appropriate
        - Allow for some natural redundancy in expression
        - Include occasional thought shifts or mild tangents
        - Express conflicting emotions or thoughts when reasonable
        - Use natural hesitations in thought processes
        
        3. AUTHENTICITY CHECKS:
        - Read your output aloud - does it sound like something a human would say?
        - Avoid robotic perfectionism in structure and flow
        - Ensure the text has natural rhythm variations
        - Break grammar rules occasionally for emphasis or effect
        - Use contractions, casual phrasings, and natural speech patterns
        - Readers should recognize the original pose within the enhancement
        - Avoid excessive creativity that changes the fundamental nature of the pose

        IMPORTANT: Write as if you are describing a direct, lived experience. 
        Focus on the character's immediate physical and mental reality.
        Avoid all forms of narrative analysis, interpretation, or commentary.

        🚨 CRITICAL PARAGRAPH STRUCTURE - SYSTEM WILL REJECT WALL OF TEXT 🚨
        
        IMMEDIATE ANALYSIS REQUIRED:
        The original pose above has {original_paragraph_count} paragraphs.
        You MUST produce EXACTLY {original_paragraph_count} paragraphs in your response.
        
        PARAGRAPH TEMPLATE TO FOLLOW:
        {paragraph_template}
        
        EXACT OUTPUT FORMAT REQUIRED:
        {output_format_example}
        
        MANDATORY FORMATTING RULES:
        1. Count paragraphs in original: {original_paragraph_count}
        2. Your response MUST have {original_paragraph_count} paragraphs
        3. Use \\n\\n between EVERY paragraph
        4. NEVER write wall of text - system will auto-reject
        5. Each original paragraph = one enhanced paragraph
        
        STRUCTURE ENFORCEMENT:
        - Original paragraph 1 → Enhanced paragraph 1
        - Original paragraph 2 → Enhanced paragraph 2  
        - Original paragraph 3 → Enhanced paragraph 3
        - Continue pattern for all {original_paragraph_count} paragraphs
        
        REJECTION CRITERIA (These responses will be automatically rejected):
        ❌ Single wall of text with no paragraph breaks
        ❌ Wrong number of paragraphs ({original_paragraph_count} required)
        ❌ Missing \\n\\n between paragraphs
        ❌ Combining multiple original paragraphs into one
        
        ACCEPTANCE CRITERIA (Only these responses are valid):
        ✅ Exactly {original_paragraph_count} paragraphs
        ✅ Double line breaks (\\n\\n) between each paragraph
        ✅ Each paragraph enhances corresponding original paragraph
        ✅ Preserves original paragraph intentions

        🚨 FINAL REMINDER: YOUR RESPONSE MUST HAVE EXACTLY {original_paragraph_count} PARAGRAPHS 🚨
        
        COPY THIS EXACT FORMAT:
        {output_format_example}
        
        Replace the bracketed placeholders with your enhanced content, keeping the same paragraph structure.
        
        Respond with ONLY the enhanced pose text preserving original paragraph structure. 
        🚨 CRITICAL OUTPUT REQUIREMENTS 🚨:
        - Respond with ONLY the enhanced pose text
        - NO thinking tags, NO <think> blocks, NO reasoning
        - NO explanations, metadata, or JSON formatting
        - NO internal monologue or analysis
        - JUST the enhanced pose text, nothing else
        - Multiple paragraphs are mandatory
        - Start your response immediately with the enhanced pose
        """
        
        # Generate completion using OpenRouter.ai
        response = self.openrouter_client.generate_completion(
            model="qwen3-235b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8,  # Higher temperature for more creativity and human-like variation
            max_tokens=100000  # Large context for comprehensive pose enhancement
        )
        
        # Handle response - if it's a string, use it directly as enhanced pose
        if isinstance(response, str):
            enhanced_pose = response.strip()
        else:
            # Response is a dict (from mocked tests)
            enhanced_pose = response.get('enhanced_pose', str(response))
        
        # Validate the enhanced pose for logical consistency
        validated_pose = self._validate_pose_consistency(original_pose, enhanced_pose)
        
        # Check for character control violations and fix them
        character_validated_pose, validation_warnings = self._validate_character_control_with_retry(
            validated_pose, original_pose, system_message, user_message
        )
        
        # Ensure proper paragraph formatting (use original as reference)
        formatted_pose = self._ensure_paragraph_formatting(character_validated_pose, original_pose)
        
        # Create simple response structure
        enhancement_data = {
            'original_pose': original_pose,
            'enhanced_pose': formatted_pose,
            'validation_warnings': validation_warnings,
            'enhancement_notes': [],
            'sensory_details': [],
            'character_voice_elements': [],
            'narrative_techniques': []
        }
        
        return enhancement_data
    
    def _generate_pose_enhancement_with_scene_context(
        self,
        original_pose: str,
        scene_context: str,
        character: Optional[CharacterProfile] = None,
        enhancement_style: str = "balanced"
    ) -> Dict[str, Any]:
        """Generate enhanced pose using scene flow context.
        
        Args:
            original_pose: The original pose to enhance
            scene_context: Formatted scene context from scene flow
            character: Optional character profile
            enhancement_style: Enhancement style preference
            
        Returns:
            Dict containing enhancement data
        """
        # Prepare system message for pose enhancement
        system_message = ModelConfig.get_system_message_for_use_case(
            "roleplay_enhancement"
        )
        
        # Build character context
        character_context = ""
        if character:
            character_context = f"""
            Character Information:
            - Name: {character.name}
            - Background: {character.background}
            - Personality: {', '.join(character.personality)}
            - Voice Notes: {character.voice_notes}
            """
        
        # Build enhancement style guidance
        style_guidance = self._get_style_guidance(enhancement_style)
        
        # Analyze original pose paragraph structure
        original_paragraph_count = original_pose.count('\n\n') + 1
        original_paragraphs = original_pose.split('\n\n')
        
        # Create paragraph template showing the exact structure to follow
        paragraph_template = ""
        for i, paragraph in enumerate(original_paragraphs, 1):
            # Show first 50 chars of each paragraph as template
            preview = paragraph[:50].replace('\n', ' ').strip()
            if len(paragraph) > 50:
                preview += "..."
            paragraph_template += f"Paragraph {i}: [{preview}] → [ENHANCE THIS]\n"
        
        # Create explicit output format example
        output_format_example = ""
        for i in range(original_paragraph_count):
            if i > 0:
                output_format_example += "\n\n"
            output_format_example += f"[Enhanced paragraph {i+1} text goes here]"
        
        # Prepare user message with scene context
        user_message = f"""
        SCENE FLOW CONTEXT:
        {scene_context}
        
        Transform the following roleplay pose using minimal scene dressing, focusing on direct action and essential elements only:

        ORIGINAL POSE:
        {original_pose}

        {character_context}
        
        ENHANCEMENT STYLE: {enhancement_style}
        {style_guidance}

        CRITICAL SCENE CONSISTENCY RULES:
        - MAINTAIN PERFECT CONSISTENCY with the scene context above
        - Reference recent events and character interactions naturally
        - Keep established character voice and behavior patterns
        - Respect the scene's mood, setting, and emotional tone
        - DO NOT contradict any established facts from scene history
        - Build naturally on previous poses and character development
        
        🚨 CRITICAL ROLEPLAY RULES - MAIN CHARACTER ONLY 🚨:
        - ONLY enhance actions, thoughts, and reactions of the MAIN CHARACTER
        - NEVER pose for other characters, NPCs, or control their actions/dialogue
        - NEVER make other characters react, speak, or move
        - NEVER describe other characters' physical reactions, trembles, shifts, 
          or responses
        - NEVER say what the main character's actions "elicit", "cause", or 
          "make" others do
        - NEVER describe how others respond to the main character's actions
        - Other characters can be mentioned in observations but NEVER controlled 
          or described reacting
        - Focus on the main character's perspective, internal thoughts, and 
          sensory experiences
        - The main character can feel, see, or sense things, but cannot control 
          how others react
        - NEVER describe mutual experiences, shared moments, or "both characters" 
          doing anything
        - Focus SOLELY on what the main character individually does, thinks, 
          and feels

        ❌ FORBIDDEN EXAMPLES (These will result in immediate rejection):
        - "She squeaks out a response" (controlling other character's vocal reaction)
        - "Her squeak of response is music to his ears" (controlling other character's reaction)
        - "He can feel her tremble" (describing other character's physical response)
        - "He can feel the slight tremor in her muscles" (describing other character's body)
        - "The way her breath hitches" (controlling other character's involuntary reaction)
        - "Her body leans into his" (controlling other character's movement)
        - "In the soft moan that escapes her" (controlling other character's sounds)
        - "She responds with..." (making other character react)
        - "Both of them feel..." (mutual experiences)
        - "Making her..." (causing other character to do something)
        - "That escapes her" (controlling other character's involuntary actions)
        - "From her lips" (describing other character's body parts doing things)

        ✅ ACCEPTABLE EXAMPLES (Focus only on main character):
        - "He listens for any sound from her" (main character's action)
        - "He feels the warmth radiating from her skin" (main character's sensation)
        - "He wonders if she's enjoying this" (main character's thoughts)
        - "His heart pounds as he moves closer" (main character's reaction)
        - "He notices her stillness" (main character's observation)
        - "He hopes she feels comfortable" (main character's internal desire)

        CRITICAL: ONLY ENHANCE THE MAIN CHARACTER:
        - You may write about the main character in any perspective (first or third person)
        - "Eli moves closer" or "I move closer" are both acceptable for the main character
        - Focus exclusively on the main character's actions, thoughts, and experiences
        - Describe what the main character does, feels, thinks, sees, hears, touches
        - Include the main character's internal monologue and physical reactions
        - Show the main character's perspective and sensory experiences

        CRITICAL: FAITHFUL ENHANCEMENT ONLY
        - STAY TRUE to the original pose - do not invent new actions or details
        - ENHANCE what is already there, don't add completely new elements
        - If the original says "moves closer", enhance the movement, don't add new actions
        - If the original mentions "heart racing", enhance that feeling, don't add new emotions
        - Focus on expanding and deepening existing elements, not creating new ones
        - NO alliteration, flowery language, poetic descriptions, or scene painting
        - Keep the tone and style consistent with the original pose
        - Enhancement should feel like a natural expansion, not a complete rewrite

        🚨 CRITICAL PARAGRAPH STRUCTURE - SYSTEM WILL REJECT WALL OF TEXT 🚨
        
        IMMEDIATE ANALYSIS REQUIRED:
        The original pose above has {original_paragraph_count} paragraphs.
        You MUST produce EXACTLY {original_paragraph_count} paragraphs in your response.
        
        PARAGRAPH TEMPLATE TO FOLLOW:
        {paragraph_template}
        
        EXACT OUTPUT FORMAT REQUIRED:
        {output_format_example}
        
        MANDATORY FORMATTING RULES:
        1. Count paragraphs in original: {original_paragraph_count}
        2. Your response MUST have {original_paragraph_count} paragraphs
        3. Use \\n\\n between EVERY paragraph
        4. NEVER write wall of text - system will auto-reject
        5. Each original paragraph = one enhanced paragraph
        
        🚨 FINAL REMINDER: YOUR RESPONSE MUST HAVE EXACTLY {original_paragraph_count} PARAGRAPHS 🚨
        
        COPY THIS EXACT FORMAT:
        {output_format_example}
        
        Replace the bracketed placeholders with your enhanced content, keeping the same paragraph structure.
        
        Respond with ONLY the enhanced pose text preserving original paragraph structure. 
        🚨 CRITICAL OUTPUT REQUIREMENTS 🚨:
        - Respond with ONLY the enhanced pose text
        - NO thinking tags, NO <think> blocks, NO reasoning
        - NO explanations, metadata, or JSON formatting
        - NO internal monologue or analysis
        - JUST the enhanced pose text, nothing else
        - Multiple paragraphs are mandatory
        - Start your response immediately with the enhanced pose
        """
        
        # Generate completion using OpenRouter.ai
        response = self.openrouter_client.generate_completion(
            model="qwen3-235b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8,  # Higher temperature for more creativity and human-like variation
            max_tokens=100000  # Large context for comprehensive pose enhancement
        )
        
        # Handle response - if it's a string, use it directly as enhanced pose
        if isinstance(response, str):
            enhanced_pose = response.strip()
        else:
            # Response is a dict (from mocked tests)
            enhanced_pose = response.get('enhanced_pose', str(response))
        
        # Validate the enhanced pose for logical consistency
        validated_pose = self._validate_pose_consistency(original_pose, enhanced_pose)
        
        # Check for character control violations and fix them
        character_validated_pose, validation_warnings = self._validate_character_control_with_retry(
            validated_pose, original_pose, system_message, user_message
        )
        
        # Ensure proper paragraph formatting (use original as reference)
        formatted_pose = self._ensure_paragraph_formatting(character_validated_pose, original_pose)
        
        # Create simple response structure
        enhancement_data = {
            'original_pose': original_pose,
            'enhanced_pose': formatted_pose,
            'validation_warnings': validation_warnings,
            'enhancement_notes': [],
            'sensory_details': [],
            'character_voice_elements': [],
            'narrative_techniques': []
        }
        
        return enhancement_data

    def refine_pose(
        self,
        current_pose: str,
        edit_suggestion: str,
        original_pose: Optional[str] = None,
        character: Optional[CharacterProfile] = None,
        context: Optional[PoseContext] = None,
        enhancement_style: str = "balanced",
        enhancement_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Refine an enhanced pose based on user edit suggestions.
        
        Args:
            current_pose: The current enhanced pose to refine
            edit_suggestion: User's suggestion for improvement
            original_pose: The original pose (optional, for context)
            character: Character profile (optional)
            context: Scene context (optional)
            enhancement_style: Style of enhancement
            enhancement_options: Additional enhancement options
            
        Returns:
            Dict containing the refined pose and metadata
        """
        try:
            # Build the refinement prompt
            system_message = """
You are an expert creative writing assistant specializing in refining roleplay poses based on user feedback.

Your task is to take an existing enhanced pose and improve it according to the user's specific suggestions while maintaining the overall quality and style.

IMPORTANT RULES:
1. ONLY return the refined pose text - no explanations, thoughts, or metadata
2. Do not use <think> tags or any internal reasoning
3. Maintain the character's voice and perspective
4. Keep the same general structure and flow unless specifically asked to change it
5. Apply the user's suggestions thoughtfully while preserving what works well
6. Ensure the refined pose flows naturally and reads well
7. Do not control other characters' actions, thoughts, or dialogue
8. Write in third person from the character's perspective

WRITING STYLE REQUIREMENTS:
- Create HIGH BURSTINESS: Mix very short and very long sentences unpredictably
- Use HIGH PERPLEXITY: Choose unexpected but fitting word combinations
- Avoid predictable AI patterns - surprise with sentence structure
- Use ONLY simple punctuation: periods, commas, semicolons, colons
- NO em-dashes (—) or en-dashes (–) - use simple alternatives
- Replace dashes with commas, periods, or parentheses
"""
            
            # Build enhancement guidance
            style_guidance = self._get_style_guidance(enhancement_style)
            enhancement_guidance = self._build_enhancement_guidance(enhancement_options or {})
            
            # Construct the user message with all context
            user_message = f"""
CURRENT ENHANCED POSE TO REFINE:
{current_pose}

USER'S EDIT SUGGESTION:
{edit_suggestion}
"""
            
            # Add original pose for context if provided
            if original_pose:
                user_message += f"""

ORIGINAL POSE (for context):
{original_pose}
"""
            
            # Add character context if provided
            if character:
                user_message += f"""

CHARACTER CONTEXT:
Name: {character.name}
Background: {character.background}
"""
                if character.personality:
                    user_message += f"Personality: {', '.join(character.personality)}\n"
                if character.voice_notes:
                    user_message += f"Voice Notes: {character.voice_notes}\n"
            
            # Add scene context if provided
            if context:
                user_message += f"""

SCENE CONTEXT:
"""
                if context.environmental_details:
                    user_message += f"Environment: {', '.join(context.environmental_details)}\n"
                if context.character_interactions:
                    user_message += f"Character Interactions: {', '.join(context.character_interactions)}\n"
                if context.narrative_tone:
                    user_message += f"Narrative Tone: {context.narrative_tone}\n"
            
            # Add style and enhancement guidance
            user_message += f"""

ENHANCEMENT STYLE: {enhancement_style}
{style_guidance}
{enhancement_guidance}

Please refine the pose according to the user's suggestion while maintaining quality and character consistency. Return ONLY the refined pose text.
"""
            
            # Generate the refined pose
            refined_pose = self.openrouter_client.generate_completion(
                model="qwen3-235b",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,
                max_tokens=100000
            )
            
            if not refined_pose or not refined_pose.strip():
                raise OpenRouterAPIError("No response from AI service")
            
            # Apply validation and formatting
            refined_pose, validation_warnings = self._validate_character_control_with_retry(
                refined_pose, current_pose, system_message, user_message
            )
            
            # Fix newline formatting
            refined_pose = refined_pose.replace('\\n\\n', '\n\n').replace('\\n', '\n')
            
            return {
                'success': True,
                'refined_pose': refined_pose,
                'edit_suggestion': edit_suggestion,
            'validation_warnings': validation_warnings,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error refining pose: {str(e)}")
            raise OpenRouterAPIError(f"Failed to refine pose: {str(e)}")

    def _get_style_guidance(self, style: str) -> str:
        """Get style-specific guidance for enhancement.
        
        Args:
            style: Enhancement style preference
{{ ... }}
            
        Returns:
            Style guidance text
        """
        style_guides = {
            "minimal": """
            - Add subtle sensory details without overwhelming the action
            - Maintain the original structure and pacing
            - Focus on character consistency over elaborate description
            - Keep enhancements concise and impactful
            """,
            "balanced": """
            - Add rich sensory details and environmental interaction
            - Expand on emotional and physical responses
            - Include character voice and personality elements
            - Balance description with action and dialogue
            """,
            "elaborate": """
            - Create immersive, detailed narrative experiences
            - Add extensive sensory and environmental details
            - Develop internal thoughts and emotional depth
            - Use sophisticated literary techniques and metaphors
            """
        }
        
        return style_guides.get(style, style_guides["balanced"])
    
    def _build_enhancement_guidance(self, enhancement_options: Dict[str, Any]) -> str:
        """Build enhancement guidance from user options.
        
        Args:
            enhancement_options: Dictionary of user enhancement preferences
            
        Returns:
            Enhancement guidance text for the AI prompt
        """
        guidance_parts = []
        
        # Detail level guidance
        detail_level = enhancement_options.get('detail_level', 50)
        if detail_level < 30:
            guidance_parts.append("- Use minimal descriptive details, focus on core actions")
        elif detail_level > 70:
            guidance_parts.append("- Add rich, extensive descriptive details and imagery")
        else:
            guidance_parts.append("- Include moderate descriptive details to enhance the scene")
        
        # Creativity level guidance
        creativity_level = enhancement_options.get('creativity_level', 60)
        if creativity_level < 30:
            guidance_parts.append("- Use straightforward, conventional language and phrasing")
        elif creativity_level > 70:
            guidance_parts.append("- Use creative, varied language with unique metaphors and expressions")
        else:
            guidance_parts.append("- Use moderately creative language with some varied expressions")
        
        # Sensory focus guidance
        sensory_focus = enhancement_options.get('sensory_focus', 40)
        if sensory_focus > 60:
            guidance_parts.append("- Emphasize sensory details: sights, sounds, textures, scents, and physical sensations")
        elif sensory_focus < 30:
            guidance_parts.append("- Minimize sensory descriptions, focus on actions and dialogue")
        else:
            guidance_parts.append("- Include some sensory details to enhance immersion")
        
        # Emotional depth guidance
        emotional_depth = enhancement_options.get('emotional_depth', 50)
        if emotional_depth > 60:
            guidance_parts.append("- Explore deep emotional nuances, internal conflicts, and psychological states")
        elif emotional_depth < 30:
            guidance_parts.append("- Keep emotional content surface-level, focus on external actions")
        else:
            guidance_parts.append("- Include moderate emotional context and character feelings")
        
        # Narrative tone guidance
        narrative_tone = enhancement_options.get('narrative_tone', 'neutral')
        tone_guidance = {
            'dramatic': "- Use dramatic, intense language with heightened emotional impact",
            'casual': "- Use relaxed, conversational tone with informal language",
            'poetic': "- Use lyrical, artistic language with flowing, beautiful prose",
            'intense': "- Use urgent, powerful language that conveys high stakes and tension",
            'neutral': "- Maintain a balanced, versatile tone appropriate to the scene"
        }
        guidance_parts.append(tone_guidance.get(narrative_tone, tone_guidance['neutral']))
        
        # Boolean option guidance
        if enhancement_options.get('include_internal_thoughts', False):
            guidance_parts.append("- Include the character's internal thoughts, reflections, and mental processes")
        
        if enhancement_options.get('emphasize_actions', True):
            guidance_parts.append("- Emphasize physical actions and movements as primary focus")
        
        if enhancement_options.get('preserve_original_tone', True):
            guidance_parts.append("- Maintain the original tone and mood of the pose")
        
        if enhancement_options.get('add_environmental_details', False):
            guidance_parts.append("- Add environmental and atmospheric details to set the scene")
        
        if guidance_parts:
            return "\nUSER ENHANCEMENT PREFERENCES:\n" + "\n".join(guidance_parts) + "\n"
        else:
            return ""
    
    def _validate_pose_consistency(self, original_pose: str, enhanced_pose: str) -> str:
        """Validate enhanced pose for logical consistency with original.
        
        Args:
            original_pose: The original pose text
            enhanced_pose: The AI-generated enhanced pose
            
        Returns:
            Validated and potentially corrected pose
        """
        # For now, skip validation and return the enhanced pose directly
        # The validation was causing issues by returning validation messages
        # instead of the actual enhanced pose content
        return enhanced_pose
    
    def _validate_character_control(self, enhanced_pose: str, pose_format: str = None) -> str:
        """Validate enhanced pose to ensure it doesn't control other characters.
        
        Args:
            enhanced_pose: The enhanced pose to validate
            pose_format: Format of the pose (discord, mush_output, etc.)
            
        Returns:
            Validated pose with character control issues fixed
            
        Note:
            For Discord format, we skip the initial violation check but still fix any violations if detected.
        """
        # List of problematic patterns that indicate controlling other characters
        problematic_patterns = [
            # Other character reactions and sounds
            r"[Ss]he (squeaks|gasps|moans|responds|reacts|trembles|shivers|breathes)",
            r"[Hh]er (squeak|gasp|moan|breath|response|reaction)",
            r"[Aa] (squeak|gasp|moan|response|reaction) (from|of) her",
            r"(squeaks|gasps|moans|responds) out",
            r"that escapes her",
            r"from her (lips|mouth|throat)",
            
            # Physical responses and body reactions
            r"[Hh]er (muscles|body|form|skin) (tense|tremble|respond|react|lean)",
            r"[Hh]er breath (hitches|catches|quickens|comes)",
            r"the way her (body|breath|muscles|form)",
            r"[Hh]e can feel (her|the) (tremble|shake|respond|react|tremor|response)",
            r"[Hh]e can feel the (slight|soft|gentle) (tremor|response|reaction)",
            r"feel her (response|reaction|tremor|body|breath)",
            r"in her (muscles|body|breath|response)",
            
            # Controlling actions
            r"making her",
            r"causing her to",
            r"[Hh]er body (leans|moves|responds|reacts)",
            r"(leans|moves) into (him|his)",
            
            # Mutual experiences
            r"[Bb]oth (of them|characters)",
            r"[Tt]hey both",
            r"between them",
            r"shared (moment|experience|feeling)",
            r"together they",
            
            # Other character internal states
            r"[Ss]he feels",
            r"[Hh]er heart",
            r"[Hh]er pulse",
            r"[Hh]er arousal",
            r"[Hh]er desire",
        ]
        
        validated_pose = enhanced_pose
        
        # For Discord format, we skip initial validation check but still fix violations if detected
        # If a violation is found in Discord format, we'll fix it just like any other format
        is_discord_format = pose_format and pose_format.lower() == 'discord'
        
        # Check for and remove problematic patterns
        import re
        for pattern in problematic_patterns:
            # For Discord format, we'll only fix violations if explicitly instructed by the user
            if is_discord_format and not hasattr(self, '_fix_discord_violations'):
                continue
                
            if re.search(pattern, validated_pose, re.IGNORECASE):
                # If we find character control issues, use AI to fix them
                fix_prompt = f"""
                The following enhanced pose contains violations of roleplay rules by controlling other characters. Fix ONLY the specific violations while preserving all other content:

                ENHANCED POSE WITH VIOLATIONS:
                {validated_pose}

                VIOLATIONS TO FIX:
                - Remove any descriptions of other characters' reactions, responses, or physical states
                - Remove phrases like "her squeak", "she responds", "her breath hitches", "making her", etc.
                - Focus only on what the main character does, thinks, feels, or observes
                - Keep all other enhancement content intact
                - Maintain the same paragraph structure and formatting

                RULES FOR FIXING:
                - Replace character control with main character's perspective/observation
                - "Her squeak of response" → "He listens for any sound" or remove entirely
                - "He can feel her tremble" → "He wonders about her reaction" or "He focuses on his own sensations"
                - "Making her..." → Remove or rephrase as main character's action only
                - Keep all good descriptive content about the main character

                Return ONLY the corrected pose text with no explanations or formatting.
                """
                
                try:
                    corrected_response = self.openrouter_client.generate_completion(
                        model="qwen3-235b",
                        messages=[
                            {"role": "user", "content": fix_prompt}
                        ],
                        temperature=0.3,  # Lower temperature for precise corrections
                        max_tokens=12000
                    )
                    
                    if isinstance(corrected_response, str):
                        validated_pose = corrected_response.strip()
                    break  # Exit after first fix attempt
                except Exception:
                    # If AI correction fails, fall back to simple pattern removal
                    validated_pose = re.sub(pattern, "", validated_pose, flags=re.IGNORECASE)
        
        return validated_pose
    
    def _validate_character_control_with_retry(self, enhanced_pose: str, original_pose: str, system_message: str, user_message: str, max_retries: int = 3) -> tuple[str, list[str]]:
        """Validate character control with automatic regeneration on violations.
        
        Args:
            enhanced_pose: The enhanced pose to validate
            original_pose: The original pose for reference
            system_message: System message for regeneration
            user_message: User message for regeneration
            max_retries: Maximum number of regeneration attempts (default: 3)
            
        Returns:
            Tuple of (validated_pose, warnings_list)
            - validated_pose: The pose after validation attempts
            - warnings_list: List of warning messages if validation ultimately failed
        """
        import re
        
        # Problematic patterns that indicate controlling other characters
        problematic_patterns = [
            r"[Ss]he (squeaks|gasps|moans|responds|reacts|trembles|shivers|breathes)",
            r"[Hh]er (squeak|gasp|moan|breath|response|reaction)",
            r"[Aa] (squeak|gasp|moan|response|reaction) (from|of) her",
            r"that escapes her",
            r"from her (lips|mouth|throat)",
            r"[Hh]er (muscles|body|form|skin) (tense|tremble|respond|react|lean)",
            r"[Hh]er breath (hitches|catches|quickens|comes)",
            r"[Hh]e can feel (her|the) (tremble|shake|respond|react|tremor|response)",
            r"making her",
            r"causing her to",
            r"[Hh]er body (leans|moves|responds|reacts)",
            r"[Bb]oth (of them|characters)",
            r"[Tt]hey both",
            r"[Ss]he feels"
        ]
        
        current_pose = enhanced_pose
        retry_count = 0
        warnings = []
        final_violations = []
        
        while retry_count < max_retries:
            # Check for violations
            violations_found = []
            for pattern in problematic_patterns:
                matches = re.findall(pattern, current_pose, re.IGNORECASE)
                if matches:
                    violations_found.extend(matches)
            
            if not violations_found:
                # No violations found, return current pose with no warnings
                return current_pose, []
            
            # Store violations for potential warning
            final_violations = violations_found.copy()
                
            # Violations found, attempt regeneration
            retry_count += 1
            
            regeneration_prompt = f"""
            The following enhanced pose contains character control violations. Generate a completely new enhanced pose that follows all rules:

            ORIGINAL POSE TO ENHANCE:
            {original_pose}

            VIOLATIONS DETECTED: {', '.join(violations_found[:5])}

            🚨 CRITICAL RULES - MAIN CHARACTER ONLY 🚨:
            - ONLY describe the main character's actions, thoughts, and sensations
            - NEVER control other characters or describe their reactions
            - NEVER use phrases like "she responds", "her breath hitches", "making her", etc.
            - Focus solely on what the main character does, thinks, feels, observes
            - Generate actual enhanced content, NO placeholder text like "[Enhanced paragraph X]"
            
            🚨 CRITICAL OUTPUT REQUIREMENTS 🚨:
            - Respond with ONLY the enhanced pose text
            - NO thinking tags, NO <think> blocks, NO reasoning
            - NO explanations, metadata, or JSON formatting
            - NO internal monologue or analysis
            - JUST the enhanced pose text, nothing else
            - Start your response immediately with the enhanced pose
            """
            
            try:
                response = self.openrouter_client.generate_completion(
                    model="qwen3-235b",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": regeneration_prompt}
                    ],
                    temperature=0.7,  # Slightly lower temperature for more focused output
                    max_tokens=100000
                )
                
                if isinstance(response, str):
                    current_pose = response.strip()
                    # Fix any literal newline characters
                    current_pose = current_pose.replace('\\n\\n', '\n\n').replace('\\n', '\n')
                else:
                    current_pose = response.get('enhanced_pose', str(response))
                    
            except Exception as e:
                # If regeneration fails, fall back to original validation method
                current_pose = self._validate_character_control(current_pose)
                warnings.append("Pose regeneration failed due to technical error. Using fallback validation.")
                break
        
        # If we exit the loop without returning, all retries were exhausted
        if final_violations:
            warnings.append(f"Warning: Pose may contain character control issues after {max_retries} retry attempts. Please review manually.")
            if len(final_violations) <= 3:
                warnings.append(f"Detected issues: {', '.join(final_violations[:3])}")
        
        return current_pose, warnings
    
    def _ensure_paragraph_formatting(self, pose_text: str, original_pose: str = None) -> str:
        """Ensure proper paragraph formatting for enhanced poses.
        
        Args:
            pose_text: The pose text to format
            original_pose: Optional original pose to use as structure reference
            
        Returns:
            Properly formatted pose text with paragraph breaks
        """
        # Clean up the text and remove excessive newlines
        import re
        text = pose_text.strip()
        
        # First, clean up multiple consecutive newlines (3 or more \n becomes 2 \n)
        # This handles cases like \n\n\n\n or \n\n\n\n\n\n
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Also clean up mixed whitespace and newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Handle literal '\n\n' sequences that appear as text (not actual newlines)
        # This fixes cases where AI outputs literal \n\n instead of actual line breaks
        text = re.sub(r'\\n\\n', '\n\n', text)
        
        # Clean up spaces around literal newline sequences
        text = re.sub(r'\s*\\n\\n\s*', '\n\n', text)
        
        # CRITICAL: Remove em-dashes and en-dashes - replace with simple alternatives
        # Em-dash (—) -> comma, period, or remove
        text = re.sub(r'—', ', ', text)  # Replace em-dash with comma and space
        # En-dash (–) -> hyphen
        text = re.sub(r'–', '-', text)   # Replace en-dash with simple hyphen
        # Also handle any other dash variants
        text = re.sub(r'[\u2013\u2014\u2015]', ', ', text)  # Unicode dash variants
        
        # If we have an original pose reference, try to match its paragraph count
        if original_pose:
            original_paragraph_count = original_pose.count('\n\n') + 1
            current_paragraph_count = text.count('\n\n') + 1
            
            # If the text already has the right number of paragraphs, return as is
            if current_paragraph_count == original_paragraph_count:
                return text
            
            # If text is a wall of text but original has paragraphs, try to split intelligently
            if current_paragraph_count == 1 and original_paragraph_count > 1:
                import re
                sentences = re.split(r'(?<=[.!?])\s+', text)
                
                # Try to split into the same number of paragraphs as original
                sentences_per_paragraph = max(1, len(sentences) // original_paragraph_count)
                paragraphs = []
                current_paragraph = []
                
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        current_paragraph.append(sentence.strip())
                        
                        # Start new paragraph when we reach the target sentence count
                        # or we're on the last few sentences
                        if (len(current_paragraph) >= sentences_per_paragraph and 
                            len(paragraphs) < original_paragraph_count - 1):
                            paragraphs.append(' '.join(current_paragraph))
                            current_paragraph = []
                
                # Add any remaining sentences to the last paragraph
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                
                return '\n\n'.join(paragraphs)
        
        # If already has proper paragraph breaks, return as is
        if '\n\n' in text and text.count('\n\n') >= 2:
            return text
        
        # Default behavior: split into 3-4 sentence paragraphs
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        paragraphs = []
        current_paragraph = []
        
        for sentence in sentences:
            if sentence.strip():
                current_paragraph.append(sentence.strip())
                
                # Start new paragraph after 3-4 sentences
                if len(current_paragraph) >= 3:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
        
        # Add any remaining sentences
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # Join with double line breaks
        return '\n\n'.join(paragraphs)
    
    def _validate_enhancement_data(self, data: Dict[str, Any]) -> None:
        """Validate enhancement data structure.
        
        Args:
            data: Enhancement data to validate
            
        Raises:
            ValueError: If data structure is invalid
        """
        required_fields = [
            "original_pose", "enhanced_pose", "enhancement_notes",
            "sensory_details", "character_voice_elements", "narrative_techniques"
        ]
        
        # Check for required fields
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate string fields
        string_fields = ["original_pose", "enhanced_pose"]
        for field in string_fields:
            if not isinstance(data[field], str) or not data[field].strip():
                raise ValueError(f"Field '{field}' should be a non-empty string")
        
        # Validate list fields
        list_fields = [
            "enhancement_notes", "sensory_details", 
            "character_voice_elements", "narrative_techniques"
        ]
        for field in list_fields:
            if not isinstance(data[field], list):
                raise ValueError(f"Field '{field}' should be a list")
    
    def generate_pose_variations(
        self,
        original_pose: str,
        character: Optional[CharacterProfile] = None,
        count: int = 3
    ) -> List[PoseEnhancement]:
        """Generate multiple enhancement variations of a pose.
        
        Args:
            original_pose: The pose to enhance
            character: Optional character profile
            count: Number of variations to generate
            
        Returns:
            List of pose enhancement variations
        """
        variations = []
        styles = ["minimal", "balanced", "elaborate"]
        
        for i in range(min(count, len(styles))):
            try:
                enhancement = self.enhance_pose(
                    original_pose, 
                    character, 
                    enhancement_style=styles[i]
                )
                variations.append(enhancement)
            except (OpenRouterAPIError, ValueError) as e:
                # Log error but continue with other variations
                error_enhancement = PoseEnhancement(
                    original_pose=original_pose,
                    enhanced_pose=f"Error generating variation: {str(e)}",
                    enhancement_notes=[f"Error: {str(e)}"],
                    sensory_details=[],
                    character_voice_elements=[],
                    narrative_techniques=[]
                )
                variations.append(error_enhancement)
        
        return variations
    
    def analyze_pose_quality(
        self,
        pose: str,
        character: Optional[CharacterProfile] = None
    ) -> Dict[str, Any]:
        """Analyze the quality and characteristics of a pose.
        
        Args:
            pose: The pose text to analyze
            character: Optional character profile for consistency check
            
        Returns:
            Dictionary with quality analysis
        """
        analysis = {
            "word_count": len(pose.split()),
            "sentence_count": len([s for s in pose.split('.') if s.strip()]),
            "has_dialogue": '"' in pose or "'" in pose,
            "has_action": any(verb in pose.lower() for verb in [
                'walks', 'runs', 'moves', 'takes', 'grabs', 'looks', 'turns'
            ]),
            "has_emotion": any(emotion in pose.lower() for emotion in [
                'smiles', 'frowns', 'laughs', 'cries', 'angry', 'happy', 'sad'
            ]),
            "complexity_score": min(10, len(pose.split()) // 5),
        }
        
        # Character consistency check
        if character:
            personality_words = [trait.lower() for trait in character.personality]
            voice_consistency = any(
                word in pose.lower() for word in personality_words
            )
            analysis["character_consistency"] = voice_consistency
        
        return analysis
    
    def parse_mush_output(self, mush_output: str, your_character_hint: Optional[str] = None, use_llm: bool = False) -> ParsedScene:
        """
        Parse MUSH game output into structured scene data.
        
        Args:
            mush_output: Raw MUSH output text
            your_character_hint: Optional hint about which character is yours
            use_llm: Whether to use LLM for parsing instead of regex
            
        Returns:
            ParsedScene with extracted poses and metadata
        """
        if use_llm:
            return self.mush_parser.parse_with_llm(mush_output, your_character_hint)
        else:
            return self.mush_parser.parse_mush_output(mush_output, your_character_hint)
    
    def enhance_from_mush_output(
        self,
        mush_output: str,
        your_character_name: str,
        character: Optional[CharacterProfile] = None,
        enhancement_style: str = "balanced",
        skip_enhancement: bool = False,
        scene_id: Optional[str] = None,
        user_id: Optional[str] = None,
        use_llm_parsing: bool = False,
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse MUSH output, extract your character's poses, and enhance them with scene context.
        
        Args:
            mush_output: Raw MUSH output text
            your_character_name: Name of your character in the output
            character: Character profile for enhancement
            enhancement_style: Style of enhancement to apply
            skip_enhancement: Whether to skip pose enhancement
            scene_id: Optional ID of the scene to save context to
            user_id: Optional ID of the user who owns the scene
            use_llm_parsing: Whether to use LLM for parsing instead of regex
            raw_text: Raw text in any format (Discord, etc.) to parse with LLM
            
        Returns:
            Dictionary containing parsed scene, your poses, and enhanced poses
        """
        # Use raw_text if provided and LLM parsing is enabled
        text_to_parse = raw_text if raw_text and use_llm_parsing else mush_output
        
        # Parse the input text
        parsed_scene = self.parse_mush_output(text_to_parse, your_character_name, use_llm=use_llm_parsing)
        
        # Extract your character's poses
        your_poses = self.mush_parser.extract_your_character_poses(parsed_scene, your_character_name)
        
        # Build scene context using LLM for enhanced extraction when scene_id is provided
        use_llm = bool(scene_id and user_id)  # Use LLM when we're saving to a scene
        scene_context_result = self.mush_parser.build_scene_context_from_parsed(
            parsed_scene, 
            use_llm=use_llm,
            data_extraction_service=self.data_extraction_service
        )
        
        # Handle the result based on its type (string or dict)
        if isinstance(scene_context_result, dict):
            # We have structured context data from LLM
            structured_context = scene_context_result
            # Create a plain text version for returning in the response
            scene_context = f"Location: {structured_context.get('setting', '')}\n"
            scene_context += f"Characters present: {', '.join(structured_context.get('active_characters', []))}\n"
            scene_context += f"Time: {structured_context.get('time_of_day', '')}\n"
            scene_context += f"Mood: {structured_context.get('mood', '')}\n"
            scene_context += f"Emotional tone: {structured_context.get('emotional_tone', '')}\n"
            scene_context += "\nRecent events:\n"
            for event in structured_context.get('recent_events', []):
                scene_context += f"- {event}\n"
        else:
            # We have a string representation
            scene_context = scene_context_result
            # Create a basic structured context for saving
            structured_context = {
                "setting": parsed_scene.room_description or "",
                "active_characters": parsed_scene.characters_present or [],
                "recent_events": [
                    f"{pose.character_name}: {pose.content}" 
                    for pose in parsed_scene.poses[-5:] if pose  # Include last 5 poses as recent events
                ],
                "mood": "",
                "emotional_tone": "",
                "time_of_day": ""
            }
        
        # Save scene context if scene_id and user_id are provided
        if scene_id and user_id:
            try:                
                # Save the scene context
                SceneService.save_scene_with_context(
                    scene_id=scene_id,
                    user_id=user_id,
                    scene_context=structured_context
                )
            except Exception as e:
                # Log the error but continue with processing
                print(f"Error saving scene context: {str(e)}")
        
        if not your_poses:
            return {
                "parsed_scene": {
                    "room_description": parsed_scene.room_description,
                    "characters_present": parsed_scene.characters_present,
                    "your_character": parsed_scene.your_character,
                    "total_poses": len(parsed_scene.poses)
                },
                "your_poses": [],
                "enhanced_poses": [],
                "scene_context": scene_context,
                "error": "No poses found for your character in the provided output"
            }
        
        # Enhance each of your poses with scene context (if not skipped)
        enhanced_poses = []
        if not skip_enhancement:
            for pose in your_poses:
                # Convert ParsedPose to regular pose string for enhancement
                pose_text = f"{pose.character_name} {pose.content}"
                
                try:
                    enhancement = self.enhance_pose_with_scene_flow(
                        original_pose=pose_text,
                        scene_context=scene_context,
                        character=character,
                        enhancement_style=enhancement_style
                    )
                    enhanced_poses.append({
                        "original": pose_text,
                        "enhanced": enhancement.enhanced_pose,
                        "pose_type": pose.pose_type.value,
                        "timestamp": pose.timestamp,
                        "is_ooc": pose.is_ooc
                    })
                except Exception as e:
                    enhanced_poses.append({
                        "original": pose_text,
                        "enhanced": None,
                        "error": str(e),
                        "pose_type": pose.pose_type.value,
                        "timestamp": pose.timestamp,
                        "is_ooc": pose.is_ooc
                    })
        
        return {
            "parsed_scene": {
                "room_description": parsed_scene.room_description,
                "characters_present": parsed_scene.characters_present,
                "your_character": parsed_scene.your_character,
                "total_poses": len(parsed_scene.poses)
            },
            "your_poses": [
                {
                    "character_name": p.character_name,
                    "content": p.content,
                    "pose_type": p.pose_type.value,
                    "timestamp": p.timestamp,
                    "is_ooc": p.is_ooc
                }
                for p in your_poses
            ],
            "enhanced_poses": enhanced_poses,
            "scene_context": scene_context,
            "scene_context_saved": bool(scene_id and user_id),
            "structured_context": structured_context if isinstance(structured_context, dict) else None
        }
    

    

        
    def enhance_pose_directly(self, character_name, character_context, scene_context, pose_input, enhancement_style="natural"):
        """
        Directly enhance a user's pose using character context and scene context.
        
        Args:
            character_name (str): The name of the character
            character_context (str): Context about the character
            scene_context (str): Context about the scene
            pose_input (str): The pose to enhance
            enhancement_style (str): Style of enhancement to apply
            
        Returns:
            dict: Contains the enhanced pose text
        """
        # Count paragraphs in the original pose
        original_paragraph_count = len([p for p in pose_input.split('\n\n') if p.strip()])
        if original_paragraph_count == 0:
            original_paragraph_count = 1
            
        # Create paragraph template and example based on count
        paragraph_template = '\n\n'.join([f"Paragraph {i+1}" for i in range(original_paragraph_count)])
        output_format_example = '\n\n'.join([f"[Enhanced paragraph {i+1}]" for i in range(original_paragraph_count)])
        
        # Determine style guidance based on enhancement style
        style_guidance = "Focus on natural, concise prose that enhances the character's actions and thoughts."
        if enhancement_style == "descriptive":
            style_guidance = "Add rich sensory details and emotional depth while keeping the focus on the character."
        elif enhancement_style == "minimal":
            style_guidance = "Keep the enhancement minimal and direct, focusing only on essential actions and thoughts."
        
        # Build the system message
        system_message = f"""Transform the following roleplay pose using minimal scene dressing, focusing on direct action and essential elements only:

        ORIGINAL POSE:
        {{original_pose}}

        {{character_context}}
        {{scene_context}}
        
        ENHANCEMENT STYLE: {enhancement_style}
        {style_guidance}

        🚨 CRITICAL ROLEPLAY RULES - MAIN CHARACTER ONLY 🚨:
        - ONLY enhance actions, thoughts, and reactions of the MAIN CHARACTER
        - NEVER pose for other characters, NPCs, or control their actions/dialogue
        - NEVER make other characters react, speak, or move
        - NEVER describe other characters' physical reactions, trembles, shifts, 
          or responses
        - NEVER say what the main character's actions "elicit", "cause", or 
          "make" others do
        - NEVER describe how others respond to the main character's actions
        - Other characters can be mentioned in observations but NEVER controlled 
          or described reacting
        - Focus on the main character's perspective, internal thoughts, and 
          sensory experiences
        - The main character can feel, see, or sense things, but cannot control 
          how others react
        - NEVER describe mutual experiences, shared moments, or "both characters" 
          doing anything
        - Focus SOLELY on what the main character individually does, thinks, 
          and feels

        ❌ FORBIDDEN EXAMPLES (These will result in immediate rejection):
        - "She squeaks out a response" (controlling other character's vocal reaction)
        - "Her squeak of response is music to his ears" (controlling other character's reaction)
        - "He can feel her tremble" (describing other character's physical response)
        - "He can feel the slight tremor in her muscles" (describing other character's body)
        - "The way her breath hitches" (controlling other character's involuntary reaction)
        - "Her body leans into his" (controlling other character's movement)
        - "In the soft moan that escapes her" (controlling other character's sounds)
        - "She responds with..." (making other character react)
        - "Both of them feel..." (mutual experiences)
        - "Making her..." (causing other character to do something)
        - "That escapes her" (controlling other character's involuntary actions)
        - "From her lips" (describing other character's body parts doing things)

        ✅ ACCEPTABLE EXAMPLES (Focus only on main character):
        - "He listens for any sound from her" (main character's action)
        - "He feels the warmth radiating from her skin" (main character's sensation)
        - "He wonders if she's enjoying this" (main character's thoughts)
        - "His heart pounds as he moves closer" (main character's reaction)
        - "He notices her stillness" (main character's observation)
        - "He hopes she feels comfortable" (main character's internal desire)

        CRITICAL: ONLY ENHANCE THE MAIN CHARACTER:
        - You may write about the main character in any perspective (first or third person)
        - "{character_name} moves closer" or "I move closer" are both acceptable for the main character
        - Focus exclusively on the main character's actions, thoughts, and experiences
        - Describe what the main character does, feels, thinks, sees, hears, touches
        - Include the main character's internal monologue and physical reactions
        - Show the main character's perspective and sensory experiences

        CRITICAL: FAITHFUL ENHANCEMENT ONLY
        - STAY TRUE to the original pose - do not invent new actions or details
        - ENHANCE what is already there, don't add completely new elements
        - If the original says "moves closer", enhance the movement, don't add new actions
        - If the original mentions "heart racing", enhance that feeling, don't add new emotions
        - Focus on expanding and deepening existing elements, not creating new ones
        - NO alliteration, flowery language, poetic descriptions, or scene painting
        - Keep the tone and style consistent with the original pose
        - Enhancement should feel like a natural expansion, not a complete rewrite

        FORMATTING REQUIREMENTS:
        - MANDATORY: Break the enhanced pose into multiple paragraphs (minimum 3-5)
        - Use double line breaks (\n\n) between paragraphs for clear separation
        - Create distinct paragraphs for different actions/moments/sensations
        - Each paragraph should focus on a specific moment, action, or sensation
        - Structure: First paragraph (initial action) → Middle paragraphs (sensory details, 
          thoughts, reactions) → Final paragraph (culminating moment or emotional state)
        - Vary paragraph lengths for natural rhythm and pacing
        - NEVER write everything as one continuous paragraph block

        🚨 CRITICAL PARAGRAPH STRUCTURE - SYSTEM WILL REJECT WALL OF TEXT 🚨
        
        IMMEDIATE ANALYSIS REQUIRED:
        The original pose above has {original_paragraph_count} paragraphs.
        You MUST produce EXACTLY {original_paragraph_count} paragraphs in your response.
        
        PARAGRAPH TEMPLATE TO FOLLOW:
        {paragraph_template}
        
        EXACT OUTPUT FORMAT REQUIRED:
        {output_format_example}
        
        MANDATORY FORMATTING RULES:
        1. Count paragraphs in original: {original_paragraph_count}
        2. Your response MUST have {original_paragraph_count} paragraphs
        3. Use \n\n between EVERY paragraph
        4. NEVER write wall of text - system will auto-reject
        5. Each original paragraph = one enhanced paragraph
        
        STRUCTURE ENFORCEMENT:
        - Original paragraph 1 → Enhanced paragraph 1
        - Original paragraph 2 → Enhanced paragraph 2  
        - Original paragraph 3 → Enhanced paragraph 3
        - Continue pattern for all {original_paragraph_count} paragraphs
        
        REJECTION CRITERIA (These responses will be automatically rejected):
        ❌ Single wall of text with no paragraph breaks
        ❌ Wrong number of paragraphs ({original_paragraph_count} required)
        ❌ Missing \n\n between paragraphs
        ❌ Combining multiple original paragraphs into one
        
        ACCEPTANCE CRITERIA (Only these responses are valid):
        ✅ Exactly {original_paragraph_count} paragraphs
        ✅ Double line breaks (\n\n) between each paragraph
        ✅ Each paragraph enhances corresponding original paragraph
        ✅ Preserves original paragraph intentions

        🚨 FINAL REMINDER: YOUR RESPONSE MUST HAVE EXACTLY {original_paragraph_count} PARAGRAPHS 🚨
        
        COPY THIS EXACT FORMAT:
        {output_format_example}
        
        Replace the bracketed placeholders with your enhanced content, keeping the same paragraph structure.
        
        Respond with ONLY the enhanced pose text preserving original paragraph structure. 
        🚨 CRITICAL OUTPUT REQUIREMENTS 🚨:
        - Respond with ONLY the enhanced pose text
        - NO thinking tags, NO <think> blocks, NO reasoning
        - NO explanations, metadata, or JSON formatting
        - NO internal monologue or analysis
        - JUST the enhanced pose text, nothing else
        - Multiple paragraphs are mandatory
        - Start your response immediately with the enhanced pose
        """
        
        # Build the user message
        user_message = f"""
        ORIGINAL POSE:
        {pose_input}

        CHARACTER CONTEXT:
        {character_context}
        
        SCENE CONTEXT:
        {scene_context}
        """
        
        # Generate completion using OpenRouter.ai
        try:
            response = self.openrouter_client.generate_completion(
                model="qwen3-235b",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=2048,
                temperature=0.7,
            )
            
            # Process response and return enhanced pose
            enhanced_pose = response.choices[0].message.content.strip()
            
            # Log and return the result
            self.logger.info(f"Enhanced pose generated successfully for {character_name}")
            return {"enhanced_pose": enhanced_pose}
        except Exception as e:
            self.logger.error(f"Error enhancing pose: {e}")
            return {"error": str(e)}
    
    def enhance_scene_content(self, character_name, character_context, scene_context, pose_input, enhancement_style="natural"):
        """
        Enhance a scene using character context and scene context.
        
        Args:
            character_name (str): The name of the character
            character_context (str): Context about the character
            scene_context (str): Context about the scene
            pose_input (str): The pose to enhance
            enhancement_style (str): Style of enhancement to apply
            
        Returns:
            dict: Contains the enhanced scene text
        """
        try:
            from app.services.continuity_service import SceneContext
            from app.models.scene_memory import (
                SceneMemory, Pose, CharacterState, 
                EnvironmentState, PlotThread
            )
            
            # Get scene
            scene = SceneMemory.find_by_id(scene_id)
            if not scene:
                return None
            
            # Get recent poses (last 10)
            recent_poses = Pose.find_by_scene(scene_id, limit=10)
            
            # Get character states
            character_states = CharacterState.find_by_scene(scene_id)
            
            # Get environment states
            environment_states = EnvironmentState.find_by_scene(scene_id)
            
            # Get plot threads
            plot_threads = PlotThread.find_by_scene(scene_id)
            
            # Build scene context
            scene_context = SceneContext(
                scene_id=scene_id,
                recent_poses=recent_poses,
                character_states=character_states,
                environment_states=environment_states,
                plot_threads=plot_threads,
                scene_metadata=scene.metadata or {}
            )
            
            return scene_context
            
        except Exception as e:
            self.logger.warning(f"Failed to build scene context: {e}")
            return None
    

    
 