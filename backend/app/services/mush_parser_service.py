import re
from typing import List, Optional
from dataclasses import dataclass
from app.models.scene_flow import PoseType


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
    
    def __init__(self):
        # Regex patterns for different MUSH output formats
        self.patterns = {
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
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for timestamp and extract it
            timestamp = None
            timestamp_match = self.patterns['timestamp'].match(line)
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                line = timestamp_match.group(2).strip()
                if not line:
                    continue
            
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
                    chars = [name.strip() for name in char_match.group(1).split() if name.strip()]
                    characters_present.extend(chars)
                continue
            
            # Parse poses and dialogue
            parsed_pose = self._parse_pose_line(line, timestamp)
            if parsed_pose:
                poses.append(parsed_pose)
                
                # Try to detect your character
                if not your_character and self._is_likely_your_character(line):
                    your_character = "You"  # Will be replaced by actual name if detected
        
        # Finalize room description
        if room_desc_lines:
            room_description = '\n'.join(room_desc_lines)
        
        # Try to infer your character from "You" patterns
        if not your_character:
            your_character = self._infer_your_character(poses, characters_present)
        
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
            if (pose.character_name == your_character_name or 
                (pose.character_name == "You" and your_character_name)):
                your_poses.append(pose)
        
        return your_poses
    
    def build_scene_context_from_parsed(self, parsed_scene: ParsedScene, max_poses: int = 20) -> str:
        """Build scene context string from parsed scene data"""
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
        
        return "\n".join(context_parts) 