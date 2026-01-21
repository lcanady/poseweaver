"""
Character State Tracking Service for Scene Memory & Continuity Tracking.

This service provides character state management, change detection, and relationship
tracking functionality according to the Scene Memory & Continuity spec.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import logging
import re
from ..models.scene_memory import CharacterState, Pose, SceneMemory
from ..services.ai_client import AIClient, OpenRouterAPIError
from ..services.character_service import CharacterProfile

logger = logging.getLogger(__name__)


class StateChange:
    """Represents a detected change in character state."""
    
    def __init__(
        self,
        character_name: str,
        change_type: str,
        field: str,
        old_value: Any,
        new_value: Any,
        confidence: float = 0.5,
        description: str = ""
    ):
        self.character_name = character_name
        self.change_type = change_type  # 'physical', 'emotional', 'equipment', 'conditions', 'location'
        self.field = field
        self.old_value = old_value
        self.new_value = new_value
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
        self.description = description
        self.timestamp = datetime.utcnow()


class Interaction:
    """Represents an interaction between characters."""
    
    def __init__(
        self,
        character1: str,
        character2: str,
        interaction_type: str,
        description: str = "",
        timestamp: Optional[datetime] = None
    ):
        self.character1 = character1
        self.character2 = character2
        self.interaction_type = interaction_type  # 'dialogue', 'action', 'conflict', 'cooperation'
        self.description = description
        self.timestamp = timestamp or datetime.utcnow()


class CharacterStateService:
    """
    Service for tracking character states throughout scenes.
    
    This service handles:
    - Character state initialization and updates
    - State change detection from pose content
    - Character relationship tracking
    - State consistency validation
    """
    
    def __init__(self, ai_client: Optional[AIClient] = None):
        """Initialize the character state service.
        
        Args:
            ai_client: Optional OpenRouter.ai client for AI-powered analysis
        """
        self.logger = logging.getLogger(__name__)
        self.ai_client = ai_client
    
    def initialize_character_state(
        self,
        scene_id: str,
        character_name: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> CharacterState:
        """
        Initialize character state for a scene.
        
        Args:
            scene_id: ID of the scene
            character_name: Name of the character
            initial_state: Optional initial state data
            
        Returns:
            The created CharacterState instance
            
        Raises:
            ValueError: If scene not found or character state already exists
            
        Requirements: 2.1 - Record initial character state when entering scene
        """
        self.logger.info(f"Initializing state for character {character_name} in scene {scene_id}")
        
        # Verify scene exists
        scene = SceneMemory.find_by_id(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        # Check if character state already exists
        existing_state = CharacterState.find_by_character(scene_id, character_name)
        if existing_state:
            raise ValueError(f"Character state for {character_name} already exists in scene {scene_id}")
        
        # Create default state structure if not provided
        if initial_state is None:
            initial_state = {}
        
        # Ensure all required state categories exist
        default_state = {
            'physical_state': initial_state.get('physical_state', {
                'health': 'healthy',
                'injuries': [],
                'fatigue': 'rested',
                'condition': 'normal'
            }),
            'emotional_state': initial_state.get('emotional_state', {
                'mood': 'neutral',
                'stress_level': 'low',
                'dominant_emotion': 'calm'
            }),
            'equipment': initial_state.get('equipment', {
                'weapons': [],
                'armor': [],
                'items': [],
                'clothing': []
            }),
            'conditions': initial_state.get('conditions', {
                'magical_effects': [],
                'status_conditions': [],
                'temporary_modifiers': []
            }),
            'location': initial_state.get('location', 'unknown')
        }
        
        # Create character state
        character_state = CharacterState(
            scene_id=scene_id,
            character_name=character_name,
            physical_state=default_state['physical_state'],
            emotional_state=default_state['emotional_state'],
            equipment=default_state['equipment'],
            conditions=default_state['conditions'],
            location=default_state['location']
        )
        
        # Save to database
        state_id = character_state.save()
        self.logger.info(f"Initialized character state {state_id} for {character_name}")
        
        return character_state
    
    def update_character_state(
        self,
        scene_id: str,
        character_name: str,
        updates: Dict[str, Any]
    ) -> CharacterState:
        """
        Update character state with new values.
        
        Args:
            scene_id: ID of the scene
            character_name: Name of the character
            updates: Dictionary of state updates
            
        Returns:
            The updated CharacterState instance
            
        Raises:
            ValueError: If character state not found
            
        Requirements: 2.2 - Update and track character state changes automatically
        """
        self.logger.debug(f"Updating state for character {character_name} in scene {scene_id}")
        
        # Find existing character state
        character_state = CharacterState.find_by_character(scene_id, character_name)
        if not character_state:
            raise ValueError(f"Character state for {character_name} not found in scene {scene_id}")
        
        # Apply updates
        character_state.update_state(**updates)
        
        # Save updated state
        character_state.save()
        
        self.logger.debug(f"Updated character state for {character_name}")
        return character_state
    
    def get_character_current_state(
        self,
        scene_id: str,
        character_name: str
    ) -> Optional[CharacterState]:
        """
        Get current character state for a scene.
        
        Args:
            scene_id: ID of the scene
            character_name: Name of the character
            
        Returns:
            CharacterState instance or None if not found
            
        Requirements: 2.3 - Display character's last known state when resuming
        """
        return CharacterState.find_by_character(scene_id, character_name)
    
    def detect_state_changes(self, pose: Pose) -> List[StateChange]:
        """
        Detect character state changes from pose content.
        
        Args:
            pose: The pose to analyze for state changes
            
        Returns:
            List of detected StateChange instances
            
        Requirements: 2.2 - Update and track character state changes automatically
        """
        self.logger.debug(f"Detecting state changes in pose {pose.id}")
        
        changes = []
        
        # Use AI analysis if available, otherwise use pattern matching
        if self.ai_client:
            try:
                ai_changes = self._detect_changes_with_ai(pose)
                changes.extend(ai_changes)
            except (OpenRouterAPIError, Exception) as e:
                self.logger.warning(f"AI analysis failed for pose {pose.id}: {e}")
                # Fall back to pattern matching
                pattern_changes = self._detect_changes_with_patterns(pose)
                changes.extend(pattern_changes)
        else:
            # Use pattern matching
            pattern_changes = self._detect_changes_with_patterns(pose)
            changes.extend(pattern_changes)
        
        self.logger.debug(f"Detected {len(changes)} state changes in pose {pose.id}")
        return changes
    
    def track_character_relationships(
        self,
        scene_id: str,
        interactions: List[Interaction]
    ) -> None:
        """
        Track character relationships based on interactions.
        
        Args:
            scene_id: ID of the scene
            interactions: List of character interactions to process
            
        Requirements: 2.4, 2.5 - Track character relationships and detect inconsistencies
        """
        self.logger.debug(f"Tracking {len(interactions)} interactions in scene {scene_id}")
        
        # Group interactions by character pairs
        relationship_updates = {}
        
        for interaction in interactions:
            # Create a consistent key for the character pair
            char_pair = tuple(sorted([interaction.character1, interaction.character2]))
            
            if char_pair not in relationship_updates:
                relationship_updates[char_pair] = {
                    'interactions': [],
                    'relationship_type': 'neutral',
                    'interaction_count': 0
                }
            
            relationship_updates[char_pair]['interactions'].append(interaction)
            relationship_updates[char_pair]['interaction_count'] += 1
        
        # Update character states with relationship information
        for char_pair, data in relationship_updates.items():
            char1, char2 = char_pair
            
            # Update both characters' relationship data
            for character_name, other_character in [(char1, char2), (char2, char1)]:
                try:
                    character_state = self.get_character_current_state(scene_id, character_name)
                    if character_state:
                        # Update relationship tracking in emotional state
                        if 'relationships' not in character_state.emotional_state:
                            character_state.emotional_state['relationships'] = {}
                        
                        character_state.emotional_state['relationships'][other_character] = {
                            'relationship_type': data['relationship_type'],
                            'interaction_count': data['interaction_count'],
                            'last_interaction': data['interactions'][-1].timestamp.isoformat()
                        }
                        
                        character_state.save()
                        
                except Exception as e:
                    self.logger.warning(f"Failed to update relationships for {character_name}: {e}")
        
        self.logger.debug(f"Updated relationships for {len(relationship_updates)} character pairs")
    
    def _detect_changes_with_ai(self, pose: Pose) -> List[StateChange]:
        """
        Use AI to detect character state changes from pose content.
        
        Args:
            pose: The pose to analyze
            
        Returns:
            List of detected StateChange instances
        """
        self.logger.debug(f"Starting AI analysis for pose {pose.id}")
        try:
            # Build prompt for state change detection
            system_message = """
            You are an expert at analyzing MUSH roleplay poses to detect character state changes.
            
            Analyze the following pose and identify any changes to the character's:
            - Physical state (health, injuries, fatigue, condition)
            - Emotional state (mood, stress, emotions)
            - Equipment (weapons, armor, items, clothing)
            - Conditions (magical effects, status conditions, modifiers)
            - Location (where the character is)
            
            Respond with a JSON array of state changes. Each change should have:
            - change_type: one of 'physical', 'emotional', 'equipment', 'conditions', 'location'
            - field: specific field that changed
            - new_value: the new value or state
            - confidence: confidence score from 0.0 to 1.0
            - description: brief description of the change
            
            Only include changes that are explicitly mentioned or strongly implied in the pose.
            """
            
            user_message = f"""
            Character: {pose.character_name}
            Pose Content: {pose.content}
            
            Analyze this pose for character state changes.
            """
            
            response = self.ai_client.generate_completion(
                model="qwen3-235b",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # Parse AI response
            if isinstance(response, str):
                import json
                try:
                    # Extract JSON from response
                    response = response.strip()
                    if '```json' in response:
                        start = response.find('```json') + 7
                        end = response.find('```', start)
                        response = response[start:end].strip()
                    elif response.startswith('[') or response.startswith('{'):
                        pass  # Already JSON
                    else:
                        # Try to find JSON array in response
                        start = response.find('[')
                        if start != -1:
                            response = response[start:]
                    
                    changes_data = json.loads(response)
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse AI response for pose {pose.id}")
                    return []
            else:
                changes_data = response
            
            # Convert to StateChange objects
            changes = []
            if isinstance(changes_data, list):
                for change_data in changes_data:
                    if isinstance(change_data, dict):
                        change = StateChange(
                            character_name=pose.character_name,
                            change_type=change_data.get('change_type', 'unknown'),
                            field=change_data.get('field', 'unknown'),
                            old_value=None,  # AI doesn't know old value
                            new_value=change_data.get('new_value', ''),
                            confidence=change_data.get('confidence', 0.5),
                            description=change_data.get('description', '')
                        )
                        changes.append(change)
            
            return changes
            
        except Exception as e:
            self.logger.error(f"AI state change detection failed: {e}")
            # Re-raise the exception so it can be caught by the calling method
            raise
    
    def _detect_changes_with_patterns(self, pose: Pose) -> List[StateChange]:
        """
        Use pattern matching to detect character state changes from pose content.
        
        Args:
            pose: The pose to analyze
            
        Returns:
            List of detected StateChange instances
        """
        changes = []
        content = pose.content.lower()
        
        # Physical state patterns
        injury_patterns = [
            r'(wounded|injured|hurt|bleeding|bruised|cut|stabbed|shot)',
            r'(takes?\s+damage|gets?\s+hurt|is\s+injured)',
            r'(blood|wound|injury|pain|ache)'
        ]
        
        for pattern in injury_patterns:
            if re.search(pattern, content):
                changes.append(StateChange(
                    character_name=pose.character_name,
                    change_type='physical',
                    field='injuries',
                    old_value=None,
                    new_value='injured',
                    confidence=0.7,
                    description=f"Detected injury indicators in pose"
                ))
                break
        
        # Emotional state patterns
        emotion_patterns = {
            'angry': r'(angry|furious|rage|mad|irritated)',
            'sad': r'(sad|depressed|melancholy|sorrowful|grief)',
            'happy': r'(happy|joyful|cheerful|delighted|pleased)',
            'afraid': r'(afraid|scared|terrified|frightened|fearful)',
            'surprised': r'(surprised|shocked|amazed|astonished)'
        }
        
        for emotion, pattern in emotion_patterns.items():
            if re.search(pattern, content):
                changes.append(StateChange(
                    character_name=pose.character_name,
                    change_type='emotional',
                    field='dominant_emotion',
                    old_value=None,
                    new_value=emotion,
                    confidence=0.6,
                    description=f"Detected emotional state: {emotion}"
                ))
                break
        
        # Equipment patterns
        equipment_patterns = [
            r'(draws?|pulls?|unsheathes?|takes?\s+out)\s+(?:a\s+|an\s+|the\s+|her\s+|his\s+)?(\w+)',
            r'(equips?|wields?|holds?)\s+(?:a\s+|an\s+|the\s+|her\s+|his\s+)?(\w+)',
            r'(puts?\s+on|wears?)\s+(?:a\s+|an\s+|the\s+|her\s+|his\s+)?(\w+)'
        ]
        
        for pattern in equipment_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if len(match.groups()) >= 2:
                    item = match.group(2)
                    changes.append(StateChange(
                        character_name=pose.character_name,
                        change_type='equipment',
                        field='items',
                        old_value=None,
                        new_value=item,
                        confidence=0.8,
                        description=f"Detected equipment change: {match.group(1)} {item}"
                    ))
        
        # Location patterns
        location_patterns = [
            r'(moves?\s+to|goes?\s+to|enters?|arrives?\s+at)\s+(?:the\s+)?(\w+)',
            r'(walks?\s+into|steps?\s+into)\s+(?:the\s+)?(\w+)'
        ]
        
        for pattern in location_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if len(match.groups()) >= 2:
                    location = match.group(2)
                    changes.append(StateChange(
                        character_name=pose.character_name,
                        change_type='location',
                        field='location',
                        old_value=None,
                        new_value=location,
                        confidence=0.7,
                        description=f"Detected location change: {match.group(1)} {location}"
                    ))
        
        return changes
    
    def get_character_states_for_scene(self, scene_id: str) -> List[CharacterState]:
        """
        Get all character states for a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            List of CharacterState instances
        """
        return CharacterState.find_by_scene(scene_id)
    
    def apply_state_changes(
        self,
        scene_id: str,
        character_name: str,
        changes: List[StateChange]
    ) -> CharacterState:
        """
        Apply detected state changes to a character's state.
        
        Args:
            scene_id: ID of the scene
            character_name: Name of the character
            changes: List of state changes to apply
            
        Returns:
            Updated CharacterState instance
            
        Raises:
            ValueError: If character state not found
        """
        character_state = self.get_character_current_state(scene_id, character_name)
        if not character_state:
            raise ValueError(f"Character state for {character_name} not found in scene {scene_id}")
        
        updates = {}
        
        for change in changes:
            # Only apply changes with reasonable confidence
            if change.confidence < 0.5:
                continue
            
            # Determine which state category to update
            if change.change_type == 'physical':
                if 'physical_state' not in updates:
                    updates['physical_state'] = character_state.physical_state.copy()
                updates['physical_state'][change.field] = change.new_value
                
            elif change.change_type == 'emotional':
                if 'emotional_state' not in updates:
                    updates['emotional_state'] = character_state.emotional_state.copy()
                updates['emotional_state'][change.field] = change.new_value
                
            elif change.change_type == 'equipment':
                if 'equipment' not in updates:
                    updates['equipment'] = character_state.equipment.copy()
                
                # Handle equipment as lists
                if change.field not in updates['equipment']:
                    updates['equipment'][change.field] = character_state.equipment.get(change.field, []).copy()
                if change.new_value not in updates['equipment'][change.field]:
                    updates['equipment'][change.field].append(change.new_value)
                    
            elif change.change_type == 'conditions':
                if 'conditions' not in updates:
                    updates['conditions'] = character_state.conditions.copy()
                
                # Handle conditions as lists
                if change.field not in updates['conditions']:
                    updates['conditions'][change.field] = character_state.conditions.get(change.field, []).copy()
                if change.new_value not in updates['conditions'][change.field]:
                    updates['conditions'][change.field].append(change.new_value)
                    
            elif change.change_type == 'location':
                updates['location'] = change.new_value
        
        # Apply updates if any were made
        if updates:
            return self.update_character_state(scene_id, character_name, updates)
        
        return character_state
    
    def extract_interactions_from_pose(self, pose: Pose, scene_id: str) -> List[Interaction]:
        """
        Extract character interactions from a pose.
        
        Args:
            pose: The pose to analyze
            scene_id: ID of the scene
            
        Returns:
            List of detected Interaction instances
        """
        interactions = []
        
        # Get all characters in the scene
        character_states = self.get_character_states_for_scene(scene_id)
        character_names = [cs.character_name for cs in character_states]
        
        # Remove the pose author from the list to find interaction targets
        other_characters = [name for name in character_names if name != pose.character_name]
        
        content = pose.content.lower()
        
        # Look for mentions of other characters
        for other_char in other_characters:
            other_char_lower = other_char.lower()
            
            # Check if the character is mentioned in the pose
            if other_char_lower in content:
                # Determine interaction type based on context
                interaction_type = 'dialogue'  # Default
                
                if any(word in content for word in ['says', 'tells', 'asks', 'whispers', 'shouts']):
                    interaction_type = 'dialogue'
                elif any(word in content for word in ['attacks', 'hits', 'strikes', 'fights']):
                    interaction_type = 'conflict'
                elif any(word in content for word in ['helps', 'assists', 'supports', 'works with']):
                    interaction_type = 'cooperation'
                else:
                    interaction_type = 'action'
                
                interaction = Interaction(
                    character1=pose.character_name,
                    character2=other_char,
                    interaction_type=interaction_type,
                    description=f"{pose.character_name} interacted with {other_char}",
                    timestamp=pose.timestamp
                )
                interactions.append(interaction)
        
        return interactions
    
    def initialize_character_state_from_profile(
        self,
        scene_id: str,
        character_name: str,
        character_profile: Optional['CharacterProfile'] = None,
        initial_overrides: Optional[Dict[str, Any]] = None
    ) -> CharacterState:
        """
        Initialize character state for a scene from a character profile.
        
        This method bridges the character profile system with scene character
        states by creating initial scene state from character profile data.
        
        Args:
            scene_id: ID of the scene
            character_name: Name of the character
            character_profile: Character profile to derive state from
            initial_overrides: Optional overrides for specific state values
            
        Returns:
            The created CharacterState instance
            
        Raises:
            ValueError: If scene not found or character state already exists
            
        Requirements: 2.1, 19 - Integrate character profile system with scene states
        """
        self.logger.info(f"Initializing state from profile for character {character_name} in scene {scene_id}")
        
        # Verify scene exists
        scene = SceneMemory.find_by_id(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        # Check if character state already exists
        existing_state = CharacterState.find_by_character(scene_id, character_name)
        if existing_state:
            raise ValueError(f"Character state for {character_name} already exists in scene {scene_id}")
        
        # Build initial state from character profile
        if character_profile:
            initial_state = self._derive_state_from_profile(character_profile)
        else:
            initial_state = self._get_default_character_state()
        
        # Apply any overrides
        if initial_overrides:
            initial_state.update(initial_overrides)
        
        # Create character state using the derived initial state
        character_state = CharacterState(
            scene_id=scene_id,
            character_name=character_name,
            physical_state=initial_state['physical_state'],
            emotional_state=initial_state['emotional_state'],
            equipment=initial_state['equipment'],
            conditions=initial_state['conditions'],
            location=initial_state['location'],
            # Store reference to character profile for consistency checking
            metadata={'character_profile_reference': True}
        )
        
        # Save to database
        state_id = character_state.save()
        self.logger.info(f"Initialized character state {state_id} from profile for {character_name}")
        
        return character_state
    
    def _derive_state_from_profile(self, character_profile: 'CharacterProfile') -> Dict[str, Any]:
        """
        Derive initial character state from character profile data.
        
        Args:
            character_profile: Character profile to derive state from
            
        Returns:
            Dictionary with initial state values derived from profile
        """
        # Extract relevant information from character profile
        background = character_profile.background.lower()
        personality = [trait.lower() for trait in character_profile.personality]
        skills = [skill.lower() for skill in character_profile.skills]
        
        # Derive physical state from background and skills
        physical_state = {
            'health': 'healthy',
            'injuries': [],
            'fatigue': 'rested',
            'condition': 'normal'
        }
        
        # Check for combat-related background/skills for better physical condition
        combat_keywords = ['warrior', 'fighter', 'soldier', 'combat', 'battle', 'martial']
        if any(keyword in background or any(keyword in skill for skill in skills) for keyword in combat_keywords):
            physical_state['condition'] = 'combat-ready'
        
        # Check for magic-related background/skills
        magic_keywords = ['magic', 'spell', 'wizard', 'sorcerer', 'witch', 'mage', 'enchant']
        magical_condition = any(keyword in background or any(keyword in skill for skill in skills) for keyword in magic_keywords)
        
        # Derive emotional state from personality
        emotional_state = {
            'mood': 'neutral',
            'stress_level': 'low',
            'dominant_emotion': 'calm'
        }
        
        # Analyze personality for emotional tendencies
        if any(trait in ['cheerful', 'optimistic', 'happy', 'joyful'] for trait in personality):
            emotional_state['mood'] = 'positive'
            emotional_state['dominant_emotion'] = 'content'
        elif any(trait in ['melancholy', 'sad', 'depressed', 'gloomy'] for trait in personality):
            emotional_state['mood'] = 'somber'
            emotional_state['dominant_emotion'] = 'thoughtful'
        elif any(trait in ['aggressive', 'hot-tempered', 'angry', 'fierce'] for trait in personality):
            emotional_state['dominant_emotion'] = 'intense'
            
        if any(trait in ['anxious', 'nervous', 'worried', 'stressed'] for trait in personality):
            emotional_state['stress_level'] = 'moderate'
        
        # Derive equipment from background and skills
        equipment = {
            'weapons': [],
            'armor': [],
            'items': [],
            'clothing': ['basic clothing']
        }
        
        # Add equipment based on skills and background
        if any(keyword in background or any(keyword in skill for skill in skills) for keyword in combat_keywords):
            equipment['weapons'].append('combat weapon')
            equipment['armor'].append('protective gear')
            
        if magical_condition:
            equipment['items'].append('magical focus')
            equipment['items'].append('spell components')
        
        if any(keyword in background or any(keyword in skill for skill in skills) for keyword in ['noble', 'wealthy', 'aristocrat']):
            equipment['clothing'] = ['fine clothing', 'jewelry']
            equipment['items'].append('money pouch')
            
        # Derive conditions from background
        conditions = {
            'magical_effects': [],
            'status_conditions': [],
            'temporary_modifiers': []
        }
        
        if magical_condition:
            conditions['status_conditions'].append('magically attuned')
        
        return {
            'physical_state': physical_state,
            'emotional_state': emotional_state,
            'equipment': equipment,
            'conditions': conditions,
            'location': 'unknown'
        }
    
    def _get_default_character_state(self) -> Dict[str, Any]:
        """
        Get default character state structure.
        
        Returns:
            Dictionary with default state values
        """
        return {
            'physical_state': {
                'health': 'healthy',
                'injuries': [],
                'fatigue': 'rested',
                'condition': 'normal'
            },
            'emotional_state': {
                'mood': 'neutral',
                'stress_level': 'low',
                'dominant_emotion': 'calm'
            },
            'equipment': {
                'weapons': [],
                'armor': [],
                'items': [],
                'clothing': ['basic clothing']
            },
            'conditions': {
                'magical_effects': [],
                'status_conditions': [],
                'temporary_modifiers': []
            },
            'location': 'unknown'
        }
    
    def update_character_profile_from_scene(
        self,
        character_profile: 'CharacterProfile',
        scene_id: str,
        character_name: str
    ) -> Dict[str, Any]:
        """
        Update character profile based on scene interactions.
        
        This method analyzes scene character state changes and suggests
        updates to the character profile to maintain consistency.
        
        Args:
            character_profile: Current character profile
            scene_id: ID of the scene to analyze
            character_name: Name of the character
            
        Returns:
            Dictionary of suggested profile updates
            
        Requirements: 19 - Integrate character profile system
        """
        self.logger.debug(f"Analyzing scene {scene_id} for profile updates for {character_name}")
        
        # Get current character state
        current_state = self.get_character_current_state(scene_id, character_name)
        if not current_state:
            return {}
        
        # Get scene poses for this character
        poses = Pose.find_by_character(scene_id, character_name)
        
        suggested_updates = {
            'personality_additions': [],
            'skills_additions': [],
            'goals_updates': [],
            'relationship_updates': {},
            'voice_notes_additions': []
        }
        
        # Analyze poses for new personality traits
        if self.ai_client:
            try:
                personality_analysis = self._analyze_poses_for_personality(poses, character_profile)
                if personality_analysis:
                    suggested_updates.update(personality_analysis)
            except Exception as e:
                self.logger.warning(f"Failed to analyze poses for personality updates: {e}")
        
        return suggested_updates
    
    def _analyze_poses_for_personality(
        self, 
        poses: List[Pose], 
        character_profile: 'CharacterProfile'
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze character poses for personality insights using AI.
        
        Args:
            poses: List of poses by the character
            character_profile: Current character profile
            
        Returns:
            Dictionary of suggested updates or None if analysis fails
        """
        if not poses or not self.ai_client:
            return None
        
        # Build analysis prompt
        poses_text = '\n\n'.join([f"[{pose.timestamp}] {pose.content}" for pose in poses[-10:]])  # Last 10 poses
        current_personality = ', '.join(character_profile.personality)
        
        prompt = f"""
        Analyze the following character poses and suggest personality trait additions
        or updates based on observed behavior patterns.
        
        Current personality traits: {current_personality}
        
        Recent poses:
        {poses_text}
        
        Provide suggestions in JSON format:
        {{
            "personality_additions": ["new trait 1", "new trait 2"],
            "voice_notes_additions": ["speaking pattern observation"],
            "relationship_insights": {{"character_name": "relationship_type"}}
        }}
        
        Focus on consistent behavioral patterns that aren't already captured.
        """
        
        try:
            response = self.ai_client.generate_completion(
                prompt=prompt,
                model='qwen3-235b',
                temperature=0.3,
                max_tokens=4000
            )
            
            # Parse response (simplified - would need proper JSON parsing)
            if isinstance(response, dict):
                return response
            elif isinstance(response, str):
                import json
                return json.loads(response)
                
        except Exception as e:
            self.logger.warning(f"Failed to analyze poses: {e}")
            return None