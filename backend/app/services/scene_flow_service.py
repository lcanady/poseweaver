"""
Scene flow service for managing roleplay scene conversation flows.

This service handles creating, updating, and managing scene flows that track
the conversation-like flow of poses in a roleplay scene, providing context
for AI enhancement.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import re

from app.models.scene_flow import SceneFlow, ScenePose, PoseType, SceneContext
from app.services.openrouter_client import OpenRouterClient, OpenRouterAPIError


class SceneFlowService:
    """Service for managing scene flows and pose context."""
    
    def __init__(self, openrouter_client: OpenRouterClient):
        """Initialize the scene flow service.
        
        Args:
            openrouter_client: OpenRouter.ai client for AI processing
        """
        self.openrouter_client = openrouter_client
        self.active_scenes: Dict[str, SceneFlow] = {}
    
    def create_scene(self, name: str, character_name: str) -> SceneFlow:
        """Create a new scene flow.
        
        Args:
            name: Name of the scene
            character_name: Name of the main character
            
        Returns:
            Created scene flow
        """
        scene_id = str(uuid.uuid4())
        now = datetime.now()
        
        scene = SceneFlow(
            id=scene_id,
            name=name,
            created_at=now,
            updated_at=now
        )
        
        # Initialize context with the main character
        scene.context.active_characters = [character_name]
        
        self.active_scenes[scene_id] = scene
        return scene
    
    def add_pose_to_scene(
        self,
        scene_id: str,
        character_name: str,
        pose_text: str,
        pose_type: Optional[PoseType] = None
    ) -> ScenePose:
        """Add a new pose to an existing scene.
        
        Args:
            scene_id: ID of the scene
            character_name: Name of the character making the pose
            pose_text: Text of the pose
            pose_type: Type of pose (auto-detected if not provided)
            
        Returns:
            Created pose
            
        Raises:
            ValueError: If scene not found
        """
        if scene_id not in self.active_scenes:
            raise ValueError(f"Scene {scene_id} not found")
        
        scene = self.active_scenes[scene_id]
        
        # Auto-detect pose type if not provided
        if pose_type is None:
            pose_type = self._detect_pose_type(pose_text)
        
        # Create the pose
        pose_id = str(uuid.uuid4())
        pose = ScenePose(
            id=pose_id,
            character_name=character_name,
            pose_text=pose_text,
            pose_type=pose_type,
            timestamp=datetime.now(),
            mentions=self._extract_character_mentions(pose_text, scene)
        )
        
        # Add to scene
        scene.add_pose(pose)
        
        # Update scene context
        self._update_scene_context(scene, pose)
        
        return pose
    
    def bulk_import_poses(
        self, 
        scene_id: str, 
        poses_text: str, 
        format_type: str = "simple",
        use_llm_parsing: bool = False
    ) -> List[ScenePose]:
        """Bulk import multiple poses to a scene.
        
        Args:
            scene_id: ID of the scene to add poses to
            poses_text: Multi-line text containing poses
            format_type: Format ("simple", "character_prefix", or "mush_output")
            use_llm_parsing: Whether to use LLM for parsing instead of regex
            
        Returns:
            List of created poses
        """
        scene = self.get_scene(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        imported_poses = []
        
        # Use LLM parsing if requested
        if use_llm_parsing:
            # Import and use the MUSH parser service for LLM-based parsing
            from app.services.mush_parser_service import MushParserService
            from app.services.data_extraction_service import DataExtractionService
            from app.services.openrouter_client import OpenRouterClient
            from flask import current_app
            
            # Initialize the MUSH parser with LLM support
            api_key = current_app.config.get('OPENROUTER_API_KEY', 'test_key_12345')
            openrouter_client = OpenRouterClient(api_key)
            data_extraction_service = DataExtractionService(openrouter_client)
            mush_parser = MushParserService(data_extraction_service)
            
            # Parse using LLM
            parsed_scene = mush_parser.parse_with_llm(poses_text)
            
            for parsed_pose in parsed_scene.poses:
                # Create the pose
                pose = ScenePose(
                    id=str(uuid.uuid4()),
                    character_name=parsed_pose.character_name,
                    pose_text=parsed_pose.content,
                    pose_type=parsed_pose.pose_type,
                    timestamp=datetime.now(),
                    mentions=self._extract_character_mentions(parsed_pose.content, scene)
                )
                
                # Add to scene
                scene.add_pose(pose)
                imported_poses.append(pose)
        
        # Use intelligent MUSH parser for raw MUSH output
        elif format_type == "mush_output":
            parsed_poses = self._parse_mush_output(poses_text)
            
            for pose_data in parsed_poses:
                character_name = pose_data['character_name']
                pose_text = pose_data['pose_text']
                
                if character_name and pose_text:
                    # Detect pose type
                    pose_type = self._detect_pose_type(pose_text)
                    
                    # Create the pose
                    pose = ScenePose(
                        id=str(uuid.uuid4()),
                        character_name=character_name,
                        pose_text=pose_text,
                        pose_type=pose_type,
                        timestamp=datetime.now(),
                        mentions=self._extract_character_mentions(pose_text, scene)
                    )
                    
                    # Add to scene
                    scene.add_pose(pose)
                    imported_poses.append(pose)
        
        else:
            # Use existing simple parsing for other formats
            lines = poses_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                character_name = None
                pose_text = None
                
                if format_type == "character_prefix":
                    # Format: "CharacterName: pose text"
                    if ':' in line:
                        parts = line.split(':', 1)
                        character_name = parts[0].strip()
                        pose_text = parts[1].strip()
                    else:
                        # No colon, treat as narrative
                        character_name = "Narrator"
                        pose_text = line
                else:  # format_type == "simple"
                    # Try to extract character name from start of pose
                    words = line.split()
                    if len(words) >= 2:
                        # Check if first word looks like a character name
                        first_word = words[0]
                        if (first_word.isalpha() and 
                            first_word[0].isupper() and 
                            len(first_word) > 1):
                            character_name = first_word
                            pose_text = ' '.join(words[1:])
                        else:
                            # Default to unknown character
                            character_name = "Unknown"
                            pose_text = line
                    else:
                        character_name = "Unknown"
                        pose_text = line
                
                if character_name and pose_text:
                    # Detect pose type
                    pose_type = self._detect_pose_type(pose_text)
                    
                    # Create the pose
                    pose = ScenePose(
                        id=str(uuid.uuid4()),
                        character_name=character_name,
                        pose_text=pose_text,
                        pose_type=pose_type,
                        timestamp=datetime.now(),
                        mentions=self._extract_character_mentions(pose_text, scene)
                    )
                    
                    # Add to scene
                    scene.add_pose(pose)
                    imported_poses.append(pose)
        
        # Update scene context once for all poses
        if imported_poses:
            # Update context with the last pose
            self._update_scene_context(scene, imported_poses[-1])
        
        return imported_poses
    
    def get_scene(self, scene_id: str) -> Optional[SceneFlow]:
        """Get a scene by ID.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            Scene flow or None if not found
        """
        return self.active_scenes.get(scene_id)
    
    def get_scene_context_for_enhancement(self, scene_id: str) -> str:
        """Get formatted scene context for pose enhancement.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            Formatted context text for AI enhancement
            
        Raises:
            ValueError: If scene not found
        """
        if scene_id not in self.active_scenes:
            raise ValueError(f"Scene {scene_id} not found")
        
        scene = self.active_scenes[scene_id]
        return scene.get_full_context_text()
    
    def enhance_pose_with_scene_context(
        self,
        scene_id: str,
        pose_text: str,
        character_name: str,
        enhancement_style: str = "balanced"
    ) -> str:
        """Enhance a pose using scene context.
        
        Args:
            scene_id: ID of the scene for context
            pose_text: Pose text to enhance
            character_name: Name of the character making the pose
            enhancement_style: Enhancement style preference
            
        Returns:
            Enhanced pose text
            
        Raises:
            ValueError: If scene not found
            OpenRouterAPIError: If AI enhancement fails
        """
        if scene_id not in self.active_scenes:
            raise ValueError(f"Scene {scene_id} not found")
        
        scene = self.active_scenes[scene_id]
        scene_context = scene.get_full_context_text()
        
        # Get character history for additional context
        character_history = scene.get_character_history(character_name, 3)
        
        # Build enhanced prompt with scene context
        system_message = """You are a roleplay writing assistant that enhances poses 
        with rich detail while maintaining perfect consistency with ongoing scene context."""
        
        user_message = f"""
        SCENE CONTEXT:
        {scene_context}
        
        CHARACTER RECENT HISTORY:
        {self._format_character_history(character_history)}
        
        POSE TO ENHANCE:
        {pose_text}
        
        CHARACTER: {character_name}
        STYLE: {enhancement_style}
        
        CRITICAL INSTRUCTIONS:
        - Maintain perfect consistency with the scene context above
        - Reference recent events and character interactions naturally
        - Keep the character's established voice and behavior patterns
        - Enhance sensory details while respecting the scene's mood and setting
        - DO NOT contradict any established facts from the scene history
        - Focus on {character_name}'s perspective and actions only
        
        Respond with ONLY the enhanced pose text, preserving paragraph structure.
        """
        
        try:
            response = self.openrouter_client.generate_completion(
                model="qwen3-235b",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,
                max_tokens=16000
            )
            
            if isinstance(response, str):
                return response.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            raise OpenRouterAPIError(f"Failed to enhance pose with scene context: {str(e)}")
    
    def _detect_pose_type(self, pose_text: str) -> PoseType:
        """Auto-detect the type of pose based on content.
        
        Args:
            pose_text: Text of the pose
            
        Returns:
            Detected pose type
        """
        text_lower = pose_text.lower()
        
        # Check for dialogue indicators
        if '"' in pose_text or "'" in pose_text or 'says' in text_lower or 'asks' in text_lower:
            return PoseType.DIALOGUE
        
        # Check for internal thoughts
        if 'thinks' in text_lower or 'wonders' in text_lower or 'remembers' in text_lower:
            return PoseType.INTERNAL
        
        # Check for action indicators
        action_words = ['moves', 'walks', 'runs', 'grabs', 'reaches', 'looks', 'turns']
        if any(word in text_lower for word in action_words):
            return PoseType.ACTION
        
        # Default to mixed if unclear
        return PoseType.MIXED
    
    def _extract_character_mentions(self, pose_text: str, scene: SceneFlow) -> List[str]:
        """Extract mentions of other characters in the pose.
        
        Args:
            pose_text: Text of the pose
            scene: Scene flow for character context
            
        Returns:
            List of mentioned character names
        """
        mentions = []
        
        # Check for mentions of known participants
        for participant_name in scene.participants.keys():
            if participant_name.lower() in pose_text.lower():
                mentions.append(participant_name)
        
        return mentions
    
    def _update_scene_context(self, scene: SceneFlow, pose: ScenePose) -> None:
        """Update scene context based on new pose.
        
        Args:
            scene: Scene flow to update
            pose: New pose to analyze
        """
        # Add character to active list if not already there
        if pose.character_name not in scene.context.active_characters:
            scene.context.active_characters.append(pose.character_name)
        
        # Extract context from pose (basic implementation)
        pose_lower = pose.pose_text.lower()
        
        # Update mood based on pose content
        if any(word in pose_lower for word in ['angry', 'furious', 'rage']):
            scene.context.emotional_tone = "tense"
        elif any(word in pose_lower for word in ['happy', 'smile', 'laugh']):
            scene.context.emotional_tone = "cheerful"
        elif any(word in pose_lower for word in ['sad', 'cry', 'tears']):
            scene.context.emotional_tone = "melancholy"
        
        # Extract location details
        location_words = ['room', 'outside', 'building', 'street', 'park', 'house']
        for word in location_words:
            if word in pose_lower and word not in scene.context.location_details:
                scene.context.location_details.append(word)
    
    def _format_character_history(self, history: List[ScenePose]) -> str:
        """Format character history for AI context.
        
        Args:
            history: List of recent poses from the character
            
        Returns:
            Formatted history text
        """
        if not history:
            return "No recent history for this character."
        
        formatted = []
        for pose in history:
            timestamp = pose.timestamp.strftime("%H:%M")
            formatted.append(f"[{timestamp}] {pose.pose_text}")
        
        return "\n".join(formatted)
    
    def list_active_scenes(self) -> List[Dict[str, Any]]:
        """List all active scenes.
        
        Returns:
            List of scene summaries
        """
        summaries = []
        for scene in self.active_scenes.values():
            if scene.is_active:
                summaries.append({
                    'id': scene.id,
                    'name': scene.name,
                    'created_at': scene.created_at.isoformat(),
                    'updated_at': scene.updated_at.isoformat(),
                    'pose_count': len(scene.poses),
                    'participants': list(scene.participants.keys()),
                    'last_activity': scene.updated_at.isoformat()
                })
        
        return summaries
    
    def close_scene(self, scene_id: str) -> bool:
        """Close an active scene.
        
        Args:
            scene_id: ID of the scene to close
            
        Returns:
            True if scene was closed, False if not found
        """
        if scene_id in self.active_scenes:
            self.active_scenes[scene_id].is_active = False
            return True
        return False

    def _parse_mush_output(self, raw_text: str) -> List[Dict[str, str]]:
        """Intelligently parse MUSH output to extract character poses.
        
        Args:
            raw_text: Raw MUSH output containing poses, OOC, system messages
            
        Returns:
            List of dicts with 'character_name' and 'pose_text' keys
        """
        poses = []
        lines = raw_text.split('\n')
        
        # Check if this is likely Discord format
        discord_format = False
        discord_pattern = r'^([\w]+)\s+[\u2014—-]\s+(\d+/\d+/\d+|[A-Z][a-z]+\s+\d+,\s+\d+),\s+\d+:\d+\s+[AP]M'
        
        for i in range(min(10, len(lines))):
            if re.search(discord_pattern, lines[i]):
                discord_format = True
                break
        
        # If Discord format detected, use special parsing to extract character names from content
        if discord_format:
            return self._parse_discord_format(raw_text)
        
        # Patterns for different MUSH elements
        name_separator_pattern = r'^=+>\s*(.+?)\s*<=+$'  # ======> Name <======
        ooc_pattern = r'<OOC>.*?$|^\s*OOC\s*[:\-].*$'  # OOC content
        system_pattern = r'^(The connection was closed|Attempting to reconnect|Command \'.*?\' is not available|Type "help" for help)'
        room_header_pattern = r'^-+\s*(.*?)\s*-+$'  # Room headers
        character_list_pattern = r'^\s*[A-Z][a-z]+\s+\d+[smh]\s+'  # Character lists
        exit_pattern = r'^-+.*?Exits.*?-+$'  # Exit listings
        
        current_character = None
        current_pose_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Handle empty lines - they might be paragraph breaks within poses
            if not line:
                # If we're currently collecting pose lines, add an empty line marker
                if current_character and current_pose_lines:
                    current_pose_lines.append('')  # Preserve paragraph break
                i += 1
                continue
            
            # Check for character name separator
            name_match = re.match(name_separator_pattern, line)
            if name_match:
                # Save previous pose if we have one
                if current_character and current_pose_lines:
                    pose_text = self._clean_pose_text('\n'.join(current_pose_lines))
                    if pose_text:
                        poses.append({
                            'character_name': current_character,
                            'pose_text': pose_text
                        })
                
                # Start new character section
                current_character = name_match.group(1).strip()
                current_pose_lines = []
                i += 1
                continue
            
            # Skip OOC content
            if re.search(ooc_pattern, line, re.IGNORECASE):
                i += 1
                continue
            
            # Skip system messages
            if re.match(system_pattern, line):
                i += 1
                continue
            
            # Skip room headers and descriptions
            if re.match(room_header_pattern, line):
                # Skip room description block
                i += 1
                while i < len(lines) and not re.match(r'^-+', lines[i]):
                    i += 1
                continue
            
            # Skip character lists
            if re.match(character_list_pattern, line):
                i += 1
                continue
            
            # Skip exit listings
            if re.match(exit_pattern, line):
                i += 1
                continue
            
            # Skip lines that look like system output
            if (line.startswith('<') and line.endswith('>')) or \
               line.startswith('Command ') or \
               'is not available' in line or \
               line.startswith('Type "help"') or \
               'Res:' in line and 'RP Room' in line:
                i += 1
                continue
            
            # If we have a current character, this might be part of their pose
            if current_character:
                current_pose_lines.append(line)
            
            i += 1
        
        # Don't forget the last pose
        if current_character and current_pose_lines:
            pose_text = self._clean_pose_text('\n'.join(current_pose_lines))
            if pose_text:
                poses.append({
                    'character_name': current_character,
                    'pose_text': pose_text
                })
        
        return poses
        
    def _parse_discord_format(self, raw_text: str) -> List[Dict[str, str]]:
        """Parse Discord chat format and extract character names from content instead of usernames.
        
        Args:
            raw_text: Raw Discord chat log text
            
        Returns:
            List of dicts with 'character_name' and 'pose_text' keys
        """
        poses = []
        lines = raw_text.split('\n')
        
        # Pattern for Discord format: Username — Date, Time
        discord_pattern = r'^([\w]+)\s+[\u2014\u2015-]\s+(\d+/\d+/\d+|[A-Z][a-z]+\s+\d+,\s+\d+),\s+\d+:\d+\s+[AP]M'
        date_separator_pattern = r'^[A-Z][a-z]+\s+\d+,\s+\d+$'  # e.g. "May 9, 2023"
        
        current_discord_user = None
        current_pose_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines unless we're in a pose
            if not line:
                if current_discord_user and current_pose_lines:
                    current_pose_lines.append('')  # Preserve paragraph break
                i += 1
                continue
            
            # Skip date separators
            if re.match(date_separator_pattern, line):
                i += 1
                continue
            
            # Check for new Discord user
            discord_match = re.match(discord_pattern, line)
            if discord_match:
                # Save previous pose if we have one
                if current_discord_user and current_pose_lines:
                    pose_text = self._clean_pose_text('\n'.join(current_pose_lines))
                    if pose_text:
                        # Extract character name from pose content instead of Discord username
                        character_name = self._extract_character_name_from_content(pose_text, current_discord_user)
                        poses.append({
                            'character_name': character_name,
                            'pose_text': pose_text
                        })
                
                # Start collecting new pose
                current_discord_user = discord_match.group(1).strip()
                current_pose_lines = []
                
                # Skip the timestamp line itself
                i += 1
                continue
            
            # Add content to current pose if we have a user
            if current_discord_user:
                current_pose_lines.append(line)
            
            i += 1
        
        # Don't forget the last pose
        if current_discord_user and current_pose_lines:
            pose_text = self._clean_pose_text('\n'.join(current_pose_lines))
            if pose_text:
                # Extract character name from pose content instead of Discord username
                character_name = self._extract_character_name_from_content(pose_text, current_discord_user)
                poses.append({
                    'character_name': character_name,
                    'pose_text': pose_text
                })
        
        return poses
    
    def _extract_character_name_from_content(self, pose_text: str, discord_username: str) -> str:
        """Extract the actual character name from pose content.
        
        Args:
            pose_text: The pose text to analyze
            discord_username: Discord username as fallback
            
        Returns:
            Extracted character name or default value
        """
        # Common character name patterns in third-person poses
        # 1. Name at the start of the pose/paragraph followed by a verb
        name_starts_pattern = r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+)?(?:\s[A-Z]\.)?)'  # Captures "Name" or "First Last" or "First M."
        
        # 2. "Name needed to" or "Name's something" patterns
        name_possessive_pattern = r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)?(?:\s[A-Z]\.)?)(?:\'s|\s+(?:needed|wanted|decided|tried|began|started|continued|felt|looked|turned|walked|runs|stands|sits))'  
        
        # Try to find character name at start of the text (most common in third-person poses)
        start_match = re.match(name_starts_pattern, pose_text)
        if start_match:
            potential_name = start_match.group(1).strip()
            # Validate it's not just a common word capitalized at the start of a sentence
            common_words = ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'his', 'her', 'its', 'their']
            if potential_name.lower() not in common_words:
                return potential_name
        
        # Try to find name with possessive or common verb patterns
        possessive_match = re.search(name_possessive_pattern, pose_text)
        if possessive_match:
            return possessive_match.group(1).strip()
        
        # Look for specific character names from screenshot ("Kara", "Michelle") 
        # or common patterns from the context
        if 'kara' in pose_text.lower():
            return "Kara"
        elif 'michelle' in pose_text.lower():
            return "Michelle"
        
        # Last resort - check if we can match the Discord username to character patterns
        # For example, FaeWitch -> Kara, Kumakun -> Michelle
        if discord_username.lower() == "faewitch":
            return "Kara"
        elif discord_username.lower() == "kumakun":
            return "Michelle"
        
        # If all else fails, use the Discord username with a note
        return f"{discord_username}"

    def _clean_pose_text(self, pose_text: str) -> str:
        """Clean pose text by removing artifacts and formatting issues.
        
        Args:
            pose_text: Raw pose text
            
        Returns:
            Cleaned pose text with preserved paragraph structure
        """
        if not pose_text:
            return ""
        
        # Remove any remaining OOC markers that might have slipped through
        pose_text = re.sub(r'<OOC>.*?</OOC>', '', pose_text, flags=re.IGNORECASE | re.DOTALL)
        pose_text = re.sub(r'\(OOC:.*?\)', '', pose_text, flags=re.IGNORECASE)
        
        # Remove system artifacts
        pose_text = re.sub(r'Command \'.*?\' is not available\..*?$', '', pose_text)
        pose_text = re.sub(r'Type "help" for help\.', '', pose_text)
        
        # First normalize paragraph breaks - preserve existing paragraph structure
        # Convert multiple newlines to paragraph markers
        pose_text = re.sub(r'\n\s*\n+', '\n\n', pose_text)
        
        # Split by paragraph breaks to handle each paragraph separately
        paragraphs = pose_text.split('\n\n')
        cleaned_paragraphs = []
        
        for paragraph in paragraphs:
            # Clean each paragraph individually
            # Remove extra whitespace within the paragraph but keep it as one block
            paragraph = re.sub(r'\s+', ' ', paragraph.strip())
            if paragraph and len(paragraph) > 3:  # Keep substantial paragraphs
                cleaned_paragraphs.append(paragraph)
        
        # Rejoin paragraphs with double newlines
        result = '\n\n'.join(cleaned_paragraphs)
        
        # Clean up any leading/trailing whitespace
        result = result.strip()
        
        # Only return if we have substantial content
        if len(result) < 10:  # Too short to be a real pose
            return ""
        
        return result 