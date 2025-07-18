import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from app.models.scene_flow import PoseType
from app.services.data_extraction_service import DataExtractionService


@dataclass
class ParsedPose:
    """Represents a parsed pose from MUSH output"""
    character_name: str
    content: str
    pose_type: PoseType
    is_ooc: bool = False
    timestamp: Optional[str] = None


@dataclass
class ParsedScene:
    """Represents a parsed scene from MUSH output"""
    poses: List[ParsedPose]
    room_description: Optional[str] = None
    characters_present: List[str] = None
    your_character: Optional[str] = None


class MushParserService:
    """Service for parsing MUSH game output into structured data"""
    
    def __init__(self, data_extraction_service: Optional[DataExtractionService] = None):
        # Regex patterns for different MUSH output formats
        self.patterns = {
            # Character name separator: "======> Name <======"
            'name_separator': re.compile(r'^=+>\s*(.+?)\s*<=+$'),
            
            # Standard pose: "CharacterName does something"
            'pose': re.compile(r'^([A-Za-z][A-Za-z0-9_\-\']*)\s+(.+)$'),
            
            # Say pattern: "CharacterName says, "dialogue""
            'say': re.compile(r'^([A-Za-z][A-Za-z0-9_\-\']*)\s+says?,?\s*["\'](.+?)["\']\.?$'),
            
            # OOC pattern: "<OOC> CharacterName says, "comment""
            'ooc_say': re.compile(r'^<OOC>\s*([A-Za-z][A-Za-z0-9_\-\']*)\s+says?,?\s*["\'](.+?)["\']\.?$'),
            
            # OOC pose: "<OOC> CharacterName does something"
            'ooc_pose': re.compile(r'^<OOC>\s*([A-Za-z][A-Za-z0-9_\-\']*)\s+(.+)$'),
            
            # Room description: "---- Room Name ----"
            'room_header': re.compile(r'^-+\s*(.+?)\s*-+$'),
            
            # Contents/Who list: "Contents:" or "Players:"
            'contents_header': re.compile(r'^(Contents|Players?):\s*$'),
            
            # Character list line
            'character_list': re.compile(r'^([A-Za-z][A-Za-z0-9_\-\']*(?:\s+[A-Za-z][A-Za-z0-9_\-\']*)*)\s*$'),
            
            # Exits: "<N> North" or "[N] North"
            'exits': re.compile(r'^[<\[]([A-Za-z0-9]+)[>\]]\s*(.+)$'),
            
            # Timestamp patterns (various formats)
            'timestamp': re.compile(r'^\[?(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\]?\s*(.*)$'),
            
            # You say/pose patterns
            'you_say': re.compile(r'^You\s+say,?\s*["\'](.+?)["\']\.?$'),
            'you_pose': re.compile(r'^You\s+(.+)$'),
        }
    
    def parse_mush_output(self, output: str, your_character_hint: Optional[str] = None) -> ParsedScene:
        """
        Parse MUSH game output into structured scene data
        
        Args:
            output: Raw MUSH output text
            your_character_hint: Optional hint about which character is yours
            
        Returns:
            ParsedScene with extracted poses and metadata
        """
        lines = output.strip().split('\n')
        poses = []
        room_description = None
        characters_present = []
        your_character = your_character_hint
        
        # State tracking
        in_room_desc = False
        in_contents = False
        room_desc_lines = []
        current_character = None
        current_pose_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Empty lines can be paragraph breaks in poses
                if current_character and current_pose_lines:
                    current_pose_lines.append('')
                continue
            
            # Check for character name separator first
            name_match = self.patterns['name_separator'].match(line)
            if name_match:
                # Save previous pose if we have one
                if current_character and current_pose_lines:
                    pose_text = '\n'.join(current_pose_lines).strip()
                    if pose_text:
                        pose_type = self._determine_pose_type(pose_text)
                        parsed_pose = ParsedPose(
                            character_name=current_character,
                            content=pose_text,
                            pose_type=pose_type,
                            is_ooc=False
                        )
                        poses.append(parsed_pose)
                        characters_present.append(current_character)
                
                # Start new character section
                current_character = name_match.group(1).strip()
                current_pose_lines = []
                continue
            
            # Check for timestamp and extract it
            timestamp = None
            timestamp_match = self.patterns['timestamp'].match(line)
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                line = timestamp_match.group(2).strip()
                if not line:
                    continue
            
            # If we have a current character, this is part of their pose
            if current_character:
                current_pose_lines.append(line)
                continue
            
            # Legacy parsing for other formats
            # Check for room description header
            room_match = self.patterns['room_header'].match(line)
            if room_match:
                in_room_desc = True
                in_contents = False
                room_desc_lines = [room_match.group(1)]
                continue
            
            # Check for contents header
            contents_match = self.patterns['contents_header'].match(line)
            if contents_match:
                in_room_desc = False
                in_contents = True
                continue
            
            # Check for exits (ends room description)
            exit_match = self.patterns['exits'].match(line)
            if exit_match:
                in_room_desc = False
                in_contents = False
                continue
            
            # Handle room description continuation
            if in_room_desc:
                room_desc_lines.append(line)
                continue
            
            # Handle character list
            if in_contents:
                char_match = self.patterns['character_list'].match(line)
                if char_match:
                    # Split character names (they might be on one line)
                    chars = [name.strip() 
                             for name in char_match.group(1).split() 
                             if name.strip()]
                    characters_present.extend(chars)
                continue
            
            # Parse poses and dialogue (legacy format)
            parsed_pose = self._parse_pose_line(line, timestamp)
            if parsed_pose:
                poses.append(parsed_pose)
                
                # Try to detect your character
                if not your_character and self._is_likely_your_character(line):
                    your_character = "You"
        
        # Don't forget the last pose
        if current_character and current_pose_lines:
            pose_text = '\n'.join(current_pose_lines).strip()
            if pose_text:
                pose_type = self._determine_pose_type(pose_text)
                parsed_pose = ParsedPose(
                    character_name=current_character,
                    content=pose_text,
                    pose_type=pose_type,
                    is_ooc=False
                )
                poses.append(parsed_pose)
                characters_present.append(current_character)
        
        # Finalize room description
        if room_desc_lines:
            room_description = '\n'.join(room_desc_lines)
        
        # Try to infer your character from "You" patterns
        if not your_character:
            your_character = self._infer_your_character(poses, characters_present)
        
        # Only use fallback if NO poses were found at all
        # Don't use fallback if we successfully parsed character poses
        if your_character_hint and output.strip() and not poses:
            # Only if no poses found at all, treat entire input as one pose
            pose_type = self._determine_pose_type(output.strip())
            single_pose = ParsedPose(
                character_name=your_character_hint,
                content=output.strip(),
                pose_type=pose_type,
                is_ooc=False
            )
            poses.append(single_pose)
            characters_present.append(your_character_hint)
            your_character = your_character_hint
        
        return ParsedScene(
            poses=poses,
            room_description=room_description,
            characters_present=list(set(characters_present)) if characters_present else None,
            your_character=your_character
        )
    
    def _parse_pose_line(self, line: str, timestamp: Optional[str] = None) -> Optional[ParsedPose]:
        """Parse a single line that might contain a pose"""
        
        # Check for "You" patterns first
        you_say_match = self.patterns['you_say'].match(line)
        if you_say_match:
            return ParsedPose(
                character_name="You",
                content=f'says, "{you_say_match.group(1)}"',
                pose_type=PoseType.DIALOGUE,
                timestamp=timestamp
            )
        
        you_pose_match = self.patterns['you_pose'].match(line)
        if you_pose_match:
            content = you_pose_match.group(1)
            return ParsedPose(
                character_name="You",
                content=content,
                pose_type=self._determine_pose_type(content),
                timestamp=timestamp
            )
        
        # Check for OOC patterns
        ooc_say_match = self.patterns['ooc_say'].match(line)
        if ooc_say_match:
            return ParsedPose(
                character_name=ooc_say_match.group(1),
                content=f'says, "{ooc_say_match.group(2)}"',
                pose_type=PoseType.DIALOGUE,
                is_ooc=True,
                timestamp=timestamp
            )
        
        ooc_pose_match = self.patterns['ooc_pose'].match(line)
        if ooc_pose_match:
            return ParsedPose(
                character_name=ooc_pose_match.group(1),
                content=ooc_pose_match.group(2),
                pose_type=self._determine_pose_type(ooc_pose_match.group(2)),
                is_ooc=True,
                timestamp=timestamp
            )
        
        # Check for regular say
        say_match = self.patterns['say'].match(line)
        if say_match:
            return ParsedPose(
                character_name=say_match.group(1),
                content=f'says, "{say_match.group(2)}"',
                pose_type=PoseType.DIALOGUE,
                timestamp=timestamp
            )
        
        # Check for regular pose
        pose_match = self.patterns['pose'].match(line)
        if pose_match:
            character_name = pose_match.group(1)
            content = pose_match.group(2)
            
            # Skip common non-pose patterns
            if self._is_system_message(character_name, content):
                return None
            
            return ParsedPose(
                character_name=character_name,
                content=content,
                pose_type=self._determine_pose_type(content),
                timestamp=timestamp
            )
        
        return None
    
    def _is_system_message(self, character_name: str, content: str) -> bool:
        """Check if this looks like a system message rather than a character pose"""
        system_indicators = [
            'connects', 'disconnects', 'has connected', 'has disconnected',
            'goes home', 'has left', 'arrives', 'enters', 'exits',
            'is now known as', 'changes', 'sets'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in system_indicators)
    
    def _is_likely_your_character(self, line: str) -> bool:
        """Check if this line suggests it's from your character's perspective"""
        return line.startswith('You ') or 'you say' in line.lower()
    
    def _infer_your_character(self, poses: List[ParsedPose], characters_present: List[str]) -> Optional[str]:
        """Try to infer which character is yours from the poses"""
        # Look for "You" poses and try to match with character names
        you_poses = [p for p in poses if p.character_name == "You"]
        if not you_poses or not characters_present:
            return None
        
        # For now, return the first character in the list as a guess
        # In a real implementation, we might use more sophisticated heuristics
        return characters_present[0] if characters_present else None
    
    def _determine_pose_type(self, content: str) -> PoseType:
        """Determine the type of pose based on content"""
        content_lower = content.lower()
        
        # Check for dialogue indicators
        if any(word in content_lower for word in ['says', 'asks', 'whispers', 'shouts', 'calls', 'replies']):
            return PoseType.DIALOGUE
        
        # Check for internal thought indicators
        if any(word in content_lower for word in ['thinks', 'wonders', 'realizes', 'remembers', 'considers']):
            return PoseType.INTERNAL
        
        # Check for mixed content (action + dialogue)
        if '"' in content or "'" in content:
            return PoseType.MIXED
        
        # Default to action
        return PoseType.ACTION
    
    def extract_your_character_poses(self, parsed_scene: ParsedScene, your_character_name: str) -> List[ParsedPose]:
        """Extract only the poses from your character"""
        if not your_character_name:
            return []
        
        your_poses = []
        for pose in parsed_scene.poses:
            # Check for exact match first
            if pose.character_name == your_character_name:
                your_poses.append(pose)
            # Check for "You" patterns
            elif pose.character_name == "You" and your_character_name:
                your_poses.append(pose)
            # Check for partial matches (e.g., "Eli" matches "Eli Navarro")
            elif self._is_character_name_match(pose.character_name, your_character_name):
                your_poses.append(pose)
        
        return your_poses

    def _is_character_name_match(self, pose_name: str, your_name: str) -> bool:
        """Check if pose character name matches your character name (including partial matches)"""
        if not pose_name or not your_name:
            return False
        
        pose_name_lower = pose_name.lower().strip()
        your_name_lower = your_name.lower().strip()
        
        # Split names into words
        pose_words = pose_name_lower.split()
        your_words = your_name_lower.split()
        
        # Common nickname mappings
        nickname_map = {
            'elias': ['eli'],
            'eli': ['elias'],
            'elizabeth': ['liz', 'beth', 'betty'],
            'liz': ['elizabeth'],
            'beth': ['elizabeth'],
            'betty': ['elizabeth'],
            'william': ['will', 'bill'],
            'will': ['william'],
            'bill': ['william'],
            'robert': ['rob', 'bob'],
            'rob': ['robert'],
            'bob': ['robert'],
            'richard': ['rick', 'dick'],
            'rick': ['richard'],
            'dick': ['richard'],
            'michael': ['mike'],
            'mike': ['michael'],
            'christopher': ['chris'],
            'chris': ['christopher'],
            'alexander': ['alex'],
            'alex': ['alexander'],
            'jonathan': ['jon'],
            'jon': ['jonathan'],
            'benjamin': ['ben'],
            'ben': ['benjamin']
        }
        
        # Check if any word from the pose name matches any word from your name
        # This handles cases like "Eli" matching "Eli Navarro" or vice versa
        for pose_word in pose_words:
            for your_word in your_words:
                # Direct match
                if pose_word == your_word and len(pose_word) > 2:
                    return True
                # Nickname match
                if pose_word in nickname_map:
                    if your_word in nickname_map[pose_word]:
                        return True
                if your_word in nickname_map:
                    if pose_word in nickname_map[your_word]:
                        return True
        
        return False
    
    def build_scene_context_from_parsed(self, parsed_scene: ParsedScene, max_poses: int = 20, 
                                        use_llm: bool = False, 
                                        data_extraction_service: Optional[DataExtractionService] = None) -> Dict[str, Any]:
        """Build scene context from parsed scene data
        
        Args:
            parsed_scene: The parsed scene data
            max_poses: Maximum number of poses to include
            use_llm: Whether to use the LLM for enhanced context extraction
            data_extraction_service: Optional data extraction service for LLM-based context
            
        Returns:
            Either a dictionary of structured scene context (if use_llm is True)
            or a string representation of the scene context (if use_llm is False)
        """
        # Build the basic scene context string
        context_parts = []
        
        # Add room description if available
        if parsed_scene.room_description:
            context_parts.append(f"Location: {parsed_scene.room_description}")
        
        # Add characters present
        if parsed_scene.characters_present:
            chars = ", ".join(parsed_scene.characters_present)
            context_parts.append(f"Characters present: {chars}")
        
        # Add recent poses (limit to max_poses)
        if parsed_scene.poses:
            context_parts.append("\nRecent scene activity:")
            recent_poses = parsed_scene.poses[-max_poses:] if len(parsed_scene.poses) > max_poses else parsed_scene.poses
            
            for pose in recent_poses:
                ooc_marker = "<OOC> " if pose.is_ooc else ""
                timestamp_marker = f"[{pose.timestamp}] " if pose.timestamp else ""
                context_parts.append(f"{timestamp_marker}{ooc_marker}{pose.character_name} {pose.content}")
        
        context_str = "\n".join(context_parts)
        
        # If LLM extraction is requested and we have a data extraction service
        if use_llm and data_extraction_service:
            try:
                # Extract structured context using LLM with pose extraction
                structured_context = data_extraction_service.extract_scene_context(
                    text=context_str,
                    character_names=parsed_scene.characters_present if parsed_scene.characters_present else [],
                    include_poses=True  # Enable pose extraction
                )
                
                # If LLM didn't extract poses or failed to do so properly, create structured poses manually
                if not structured_context.get("poses") or len(structured_context["poses"]) == 0:
                    structured_poses = []
                    if parsed_scene.poses:
                        recent_poses = parsed_scene.poses[-max_poses:] if len(parsed_scene.poses) > max_poses else parsed_scene.poses
                        for pose in recent_poses:
                            # Create preview by taking first ~10-15 words (roughly 80 characters)
                            content = pose.content
                            preview = content[:80] + "..." if len(content) > 80 else content
                            
                            structured_poses.append({
                                "character_name": pose.character_name,
                                "content": content,
                                "preview": preview,
                                "is_ooc": pose.is_ooc,
                                "timestamp": pose.timestamp
                            })
                        
                    # Add structured poses to the context
                    structured_context["poses"] = structured_poses
                    
                # Make sure all poses have preview field
                for pose in structured_context["poses"]:
                    if "preview" not in pose or not pose["preview"]:
                        content = pose["content"]
                        pose["preview"] = content[:80] + "..." if len(content) > 80 else content
                    
                return structured_context
            except Exception as e:
                print(f"Error extracting structured context: {str(e)}")
                # Fall back to structured representation with manual pose extraction
                structured_poses = []
                if parsed_scene.poses:
                    recent_poses = parsed_scene.poses[-max_poses:] if len(parsed_scene.poses) > max_poses else parsed_scene.poses
                    for pose in recent_poses:
                        content = pose.content
                        preview = content[:80] + "..." if len(content) > 80 else content
                        
                        structured_poses.append({
                            "character_name": pose.character_name,
                            "content": content,
                            "preview": preview,
                            "is_ooc": pose.is_ooc,
                            "timestamp": pose.timestamp
                        })
                
                return {
                    "setting": parsed_scene.room_description or "",
                    "active_characters": parsed_scene.characters_present or [],
                    "raw_context": context_str,
                    "poses": structured_poses,
                    "error": str(e)
                }
        
        # For non-LLM mode, return structured data with manual pose extraction
        if parsed_scene.poses:
            structured_poses = []
            recent_poses = parsed_scene.poses[-max_poses:] if len(parsed_scene.poses) > max_poses else parsed_scene.poses
            
            for pose in recent_poses:
                content = pose.content
                preview = content[:80] + "..." if len(content) > 80 else content
                
                structured_poses.append({
                    "character_name": pose.character_name,
                    "content": content,
                    "preview": preview,
                    "is_ooc": pose.is_ooc,
                    "timestamp": pose.timestamp
                })
                
            return {
                "setting": parsed_scene.room_description or "",
                "active_characters": parsed_scene.characters_present or [],
                "raw_context": context_str,
                "poses": structured_poses
            }
        
        # If no poses, return simpler structure
        return {
            "setting": parsed_scene.room_description or "",
            "active_characters": parsed_scene.characters_present or [],
            "raw_context": context_str,
            "poses": []
        }