"""
Pose enhancement service for MUSH Pose Editor.

This service transforms basic actions into rich, detailed narratives
while maintaining character voice consistency and context integration.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from app.services.venice_client import VeniceClient, VeniceAPIError
from app.services.model_config import ModelConfig
from app.services.character_service import CharacterProfile
from app.services.context_service import PoseContext


@dataclass
class PoseEnhancement:
    """Enhanced pose with metadata."""
    original_pose: str
    enhanced_pose: str
    enhancement_notes: List[str]
    sensory_details: List[str]
    character_voice_elements: List[str]
    narrative_techniques: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pose enhancement to dictionary."""
        return asdict(self)


class PoseService:
    """Service for enhancing poses with AI-powered narrative improvement."""
    
    def __init__(self, venice_client: VeniceClient):
        """Initialize the pose service.
        
        Args:
            venice_client: Venice.ai client for AI processing
        """
        self.venice_client = venice_client
    
    def enhance_pose(
        self,
        original_pose: str,
        character: Optional[CharacterProfile] = None,
        context: Optional[PoseContext] = None,
        enhancement_style: str = "balanced"
    ) -> PoseEnhancement:
        """Enhance a basic pose into rich narrative.
        
        Args:
            original_pose: The original pose text to enhance
            character: Optional character profile for voice consistency
            context: Optional scene context for integration
            enhancement_style: Style of enhancement (minimal, balanced, elaborate)
            
        Returns:
            PoseEnhancement: Enhanced pose with metadata
            
        Raises:
            VeniceAPIError: If AI processing fails
            ValueError: If the AI response is invalid
        """
        try:
            # Generate enhanced pose using AI
            enhancement_data = self._generate_pose_enhancement(
                original_pose, character, context, enhancement_style
            )
            
            # Validate the enhancement data
            self._validate_enhancement_data(enhancement_data)
            
            # Create and return pose enhancement
            return PoseEnhancement(**enhancement_data)
            
        except VeniceAPIError:
            # Re-raise Venice API errors
            raise
        except Exception as e:
            raise ValueError(f"Invalid enhancement data: {str(e)}")
    
    def _generate_pose_enhancement(
        self,
        original_pose: str,
        character: Optional[CharacterProfile] = None,
        context: Optional[PoseContext] = None,
        enhancement_style: str = "balanced"
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
        Transform the following roleplay pose into vivid, immersive prose focused purely on action and experience:

        ORIGINAL POSE:
        {original_pose}

        {character_context}
        {scene_context}
        
        ENHANCEMENT STYLE: {enhancement_style}
        {style_guidance}

        CRITICAL ROLEPLAY RULES:
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
        - NO excessive alliteration, flowery language, or overly poetic descriptions
        - Keep the tone and style consistent with the original pose
        - Enhancement should feel like a natural expansion, not a complete rewrite

        ADVANCED WRITING TECHNIQUES TO APPLY:

        1. DIRECT PHYSICAL EXPERIENCE:
        - Focus on immediate sensations and physical reactions
        - Describe what the character's body feels and experiences
        - Include involuntary physical responses and instincts
        - Show direct cause-and-effect of physical actions

        2. SENSORY IMMERSION:
        - Engage ALL five senses with specific, concrete details
        - Use textures, temperatures, sounds, scents, tastes
        - Include physical sensations and bodily reactions
        - Show how emotions manifest physically in the body

        3. NATURAL VOICE ENHANCEMENT:
        - Vary sentence structure naturally (avoid forced dramatic changes)
        - Use fitting word choices that match the original tone
        - Enhance existing language patterns, don't completely change them
        - Maintain the original character's voice and style
        - Avoid overly elaborate or flowery language

        4. IMMEDIATE EMOTIONAL REALITY:
        - Show emotions through physical manifestations
        - Include visceral descriptions of feeling states
        - Focus on involuntary reactions and instinctive responses
        - Demonstrate immediate emotional responses to events

        5. ENVIRONMENTAL INTERACTION:
        - Show how the character directly interacts with surroundings
        - Use environmental details the character actually perceives
        - Include weather, lighting, sounds the character experiences
        - Focus on setting elements that affect the character

        6. STREAM OF CONSCIOUSNESS:
        - Include internal monologue and immediate thoughts
        - Show the character's mental reactions to events
        - Use natural thought patterns and mental responses
        - Focus on what the character is thinking, not what it means

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
        No explanations, metadata, or JSON formatting. Multiple paragraphs are mandatory.
        """
        
        # Generate completion using Venice.ai
        response = self.venice_client.generate_completion(
            model="venice-uncensored",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8,  # Higher temperature for more creativity and human-like variation
            max_tokens=1500   # Increased tokens for more detailed prose
        )
        
        # Handle response - if it's a string, use it directly as enhanced pose
        if isinstance(response, str):
            enhanced_pose = response.strip()
        else:
            # Response is a dict (from mocked tests)
            enhanced_pose = response.get('enhanced_pose', str(response))
        
        # Validate the enhanced pose for logical consistency
        validated_pose = self._validate_pose_consistency(original_pose, enhanced_pose)
        
        # Ensure proper paragraph formatting (use original as reference)
        formatted_pose = self._ensure_paragraph_formatting(validated_pose, original_pose)
        
        # Create simple response structure
        enhancement_data = {
            'original_pose': original_pose,
            'enhanced_pose': formatted_pose,
            'enhancement_notes': [],
            'sensory_details': [],
            'character_voice_elements': [],
            'narrative_techniques': []
        }
        
        return enhancement_data
    
    def _get_style_guidance(self, style: str) -> str:
        """Get style-specific guidance for enhancement.
        
        Args:
            style: Enhancement style preference
            
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
    
    def _validate_pose_consistency(self, original_pose: str, enhanced_pose: str) -> str:
        """Validate enhanced pose for logical consistency with original.
        
        Args:
            original_pose: The original pose text
            enhanced_pose: The AI-generated enhanced pose
            
        Returns:
            Validated and potentially corrected pose
        """
        # Create validation prompt
        validation_prompt = f"""
        You are a logical consistency checker for roleplay pose enhancement.
        
        ORIGINAL POSE:
        {original_pose}
        
        ENHANCED POSE:
        {enhanced_pose}
        
        TASK: Check if the enhanced pose has any logical inconsistencies with the original.
        
        CRITICAL ISSUES TO CHECK FOR AND FIX:
        
        1. PHYSICAL POSITIONING ERRORS:
        - If original says "Serena's back connects with the wall" → enhanced CANNOT say "his back meets the wall"
        - If original says "Character A moves toward Character B" → enhanced CANNOT flip who moves toward whom
        - WHO is positioned WHERE must remain exactly the same
        - Physical contact points must match (if A touches B's arm, enhanced can't have B touching A's arm)
        
        2. SPATIAL RELATIONSHIP VIOLATIONS:
        - Maintain exact relative positions (who is against what, who is where)
        - Don't swap character positions or orientations
        - Keep consistent directions (left/right, forward/back, up/down)
        - Preserve environmental interactions (who is against the wall, door, etc.)
        
        3. CHARACTER ACTION CONTRADICTIONS:
        - Don't add new actions the original character didn't perform
        - Don't change the sequence or nature of existing actions
        - Keep the same character as the active agent for each action
        
        4. CAUSE AND EFFECT LOGIC:
        - Enhanced details must logically follow from what actually happened in original
        - Don't contradict established physics or timeline
        - Maintain realistic consequences of described actions
        
        VALIDATION PROCESS:
        1. Read the original pose carefully - note WHO does WHAT and WHERE
        2. Check each sentence in enhanced pose against the original facts
        3. Look specifically for position swaps, action attribution errors, spatial contradictions
        4. If you find inconsistencies, fix ONLY those specific errors
        5. Preserve ALL good enhancements and original text formatting/capitalization
        6. Do NOT rewrite the entire pose - just fix the specific logical errors
        7. If no issues, return the enhanced pose unchanged exactly as provided
        
        CRITICAL OUTPUT FORMAT:
        - Respond with ONLY the corrected enhanced pose text as plain text
        - NO JSON, NO metadata, NO explanations, NO structure
        - Just the raw pose text exactly as it should appear
        - Do NOT include any formatting like quotes, brackets, or JSON structure
        - Example: "Eli moves closer to the wall. His breath catches..."
        """
        
        try:
            # Get validation response
            validation_response = self.venice_client.generate_completion(
                model="venice-uncensored",
                messages=[
                    {"role": "system", "content": "You are a logical consistency validator for roleplay text."},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent validation
                max_tokens=1500
            )
            
            if isinstance(validation_response, str):
                # Clean response - sometimes AI returns JSON despite instructions
                cleaned_response = validation_response.strip()
                
                # If it looks like JSON, try to extract the enhanced_pose
                if cleaned_response.startswith('{') and 'enhanced_pose' in cleaned_response:
                    try:
                        import json
                        json_data = json.loads(cleaned_response)
                        if 'enhanced_pose' in json_data:
                            return json_data['enhanced_pose']
                    except:
                        pass  # Fall through to return original response
                
                return cleaned_response
            else:
                # Fallback to original enhanced pose if validation fails
                return enhanced_pose
                
        except Exception:
            # If validation fails, return the original enhanced pose
            return enhanced_pose
    
    def _ensure_paragraph_formatting(self, pose_text: str, original_pose: str = None) -> str:
        """Ensure proper paragraph formatting for enhanced poses.
        
        Args:
            pose_text: The pose text to format
            original_pose: Optional original pose to use as structure reference
            
        Returns:
            Properly formatted pose text with paragraph breaks
        """
        # Clean up the text
        text = pose_text.strip()
        
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
            except (VeniceAPIError, ValueError) as e:
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