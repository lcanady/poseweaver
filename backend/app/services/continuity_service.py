"""
AI-powered Continuity Analysis Service for Scene Memory & Continuity Tracking.

This service provides intelligent analysis of poses for continuity checking,
character consistency validation, plot element extraction, and continuity flag management
using Venice.ai integration.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging
import json
from dataclasses import dataclass
from ..models.scene_memory import (
    Pose, CharacterState, EnvironmentState, PlotThread, ContinuityFlag,
    FlagType, Severity, PlotStatus, PoseType
)
from ..services.venice_client import VeniceClient, VeniceAPIError
from ..services.plot_thread_service import PlotThreadService, PlotElement as PlotThreadElement

logger = logging.getLogger(__name__)


@dataclass
class ContinuityAnalysis:
    """Results of continuity analysis for a pose."""
    pose_id: str
    character_consistency_score: float
    environment_consistency_score: float
    plot_consistency_score: float
    timeline_consistency_score: float
    overall_confidence: float
    flags: List[ContinuityFlag]
    extracted_plot_elements: List[PlotThreadElement]
    character_state_changes: List[Dict[str, Any]]
    environment_changes: List[Dict[str, Any]]
    analysis_notes: str


@dataclass
class ConsistencyCheck:
    """Results of character consistency checking."""
    character_name: str
    consistency_score: float
    voice_consistency: float
    behavior_consistency: float
    relationship_consistency: float
    issues: List[str]
    confidence: float


@dataclass
class PlotElement:
    """Extracted plot element from pose analysis."""
    title: str
    description: str
    importance_score: float
    element_type: str  # "introduction", "development", "resolution", "reference"
    related_characters: List[str]
    keywords: List[str]


@dataclass
class StateChange:
    """Detected character state change."""
    character_name: str
    change_type: str  # "physical", "emotional", "equipment", "condition", "location"
    old_value: Any
    new_value: Any
    confidence: float
    description: str


@dataclass
class EnvironmentUpdate:
    """Detected environment state change."""
    location_name: str
    change_type: str  # "weather", "time", "physical", "new_location"
    description: str
    details: Dict[str, Any]
    confidence: float


@dataclass
class SceneContext:
    """Context information for scene analysis."""
    scene_id: str
    recent_poses: List[Pose]
    character_states: List[CharacterState]
    environment_states: List[EnvironmentState]
    plot_threads: List[PlotThread]
    scene_metadata: Dict[str, Any]


class ContinuityService:
    """
    AI-powered service for continuity analysis and checking.
    
    This service provides:
    - Pose continuity analysis using Venice.ai
    - Character consistency checking
    - Plot element extraction and tracking
    - Continuity flag generation and management
    - Environment and timeline consistency validation
    """
    
    def __init__(self, venice_client: VeniceClient, plot_thread_service: Optional[PlotThreadService] = None):
        """
        Initialize the continuity service.
        
        Args:
            venice_client: Venice.ai client for AI analysis
            plot_thread_service: Optional PlotThreadService for plot analysis
        """
        self.venice_client = venice_client
        self.plot_thread_service = plot_thread_service or PlotThreadService(venice_client)
        self.logger = logging.getLogger(__name__)
        
        # Analysis configuration
        self.analysis_config = {
            'model': 'qwen3-235b',
            'temperature': 0.3,  # Lower temperature for more consistent analysis
            'max_tokens': 2000,
            'confidence_threshold': 0.6,
            'flag_threshold': 0.7
        }
    
    def analyze_pose_continuity(
        self, 
        pose: Pose, 
        scene_context: SceneContext
    ) -> ContinuityAnalysis:
        """
        Analyze a pose for continuity issues using AI.
        
        Args:
            pose: The pose to analyze
            scene_context: Context information about the scene
            
        Returns:
            ContinuityAnalysis with detected issues and scores
            
        Requirements: 6.1 - Analyze poses for potential continuity issues
        """
        self.logger.info(f"Analyzing continuity for pose {pose.id}")
        
        try:
            # Prepare analysis prompt
            analysis_prompt = self._build_continuity_analysis_prompt(pose, scene_context)
            
            # Call Venice.ai for analysis
            response = self.venice_client.generate_completion(
                prompt=analysis_prompt,
                model=self.analysis_config['model'],
                temperature=self.analysis_config['temperature'],
                max_tokens=self.analysis_config['max_tokens']
            )
            
            # Parse the AI response
            analysis_data = self._parse_continuity_response(response)
            
            # Generate continuity flags based on analysis
            flags = self._generate_continuity_flags(pose.id, analysis_data)
            
            # Extract plot elements using PlotThreadService
            plot_elements = self.extract_plot_elements(pose)
            
            # Process plot threads if scene context is available
            if hasattr(scene_context, 'scene_id'):
                plot_thread_results = self.process_plot_threads_for_pose(pose, scene_context.scene_id)
                self.logger.debug(f"Plot thread processing: {plot_thread_results}")
            
            # Detect state changes
            character_changes = self._detect_character_state_changes(pose, analysis_data)
            environment_changes = self._detect_environment_changes(pose, analysis_data)
            
            # Create analysis result
            analysis = ContinuityAnalysis(
                pose_id=pose.id,
                character_consistency_score=analysis_data.get('character_consistency', 0.8),
                environment_consistency_score=analysis_data.get('environment_consistency', 0.8),
                plot_consistency_score=analysis_data.get('plot_consistency', 0.8),
                timeline_consistency_score=analysis_data.get('timeline_consistency', 0.8),
                overall_confidence=analysis_data.get('confidence', 0.7),
                flags=flags,
                extracted_plot_elements=plot_elements,
                character_state_changes=character_changes,
                environment_changes=environment_changes,
                analysis_notes=analysis_data.get('notes', '')
            )
            
            self.logger.info(f"Completed continuity analysis for pose {pose.id}")
            return analysis
            
        except VeniceAPIError as e:
            self.logger.error(f"Venice.ai API error during continuity analysis: {e}")
            # Return fallback analysis
            return self._create_fallback_analysis(pose.id)
        except Exception as e:
            self.logger.error(f"Error during continuity analysis: {e}")
            return self._create_fallback_analysis(pose.id)
    
    def check_character_consistency(
        self, 
        pose: Pose, 
        character_history: List[Pose]
    ) -> ConsistencyCheck:
        """
        Check character consistency against historical poses.
        
        Args:
            pose: The current pose to check
            character_history: List of previous poses by the same character
            
        Returns:
            ConsistencyCheck with detailed consistency scores
            
        Requirements: 6.2 - Character behavior consistency checking
        """
        self.logger.debug(f"Checking character consistency for {pose.character_name}")
        
        try:
            # Build character consistency prompt
            consistency_prompt = self._build_character_consistency_prompt(pose, character_history)
            
            # Call Venice.ai for analysis
            response = self.venice_client.generate_completion(
                prompt=consistency_prompt,
                model=self.analysis_config['model'],
                temperature=self.analysis_config['temperature'],
                max_tokens=1500
            )
            
            # Parse response
            consistency_data = self._parse_character_consistency_response(response)
            
            # Create consistency check result
            check = ConsistencyCheck(
                character_name=pose.character_name,
                consistency_score=consistency_data.get('overall_score', 0.8),
                voice_consistency=consistency_data.get('voice_score', 0.8),
                behavior_consistency=consistency_data.get('behavior_score', 0.8),
                relationship_consistency=consistency_data.get('relationship_score', 0.8),
                issues=consistency_data.get('issues', []),
                confidence=consistency_data.get('confidence', 0.7)
            )
            
            return check
            
        except VeniceAPIError as e:
            self.logger.error(f"Venice.ai API error during character consistency check: {e}")
            return self._create_fallback_consistency_check(pose.character_name)
        except Exception as e:
            self.logger.error(f"Error during character consistency check: {e}")
            return self._create_fallback_consistency_check(pose.character_name)
    
    def extract_plot_elements(self, pose: Pose) -> List['PlotElement']:
        """
        Extract plot elements from a pose using AI analysis.
        
        Delegates to PlotThreadService for comprehensive plot analysis.
        
        Args:
            pose: The pose to analyze for plot elements
            
        Returns:
            List of extracted PlotElement instances
            
        Requirements: 4.1 - Identify and tag potential plot threads
        """
        return self.plot_thread_service.extract_plot_elements_from_pose(pose)
    
    def process_plot_threads_for_pose(self, pose: Pose, scene_id: str) -> Dict[str, Any]:
        """
        Process plot threads for a pose during continuity analysis.
        
        Args:
            pose: The pose to process
            scene_id: ID of the scene
            
        Returns:
            Dictionary with plot thread processing results
            
        Requirements: 4.1, 4.2 - Plot thread processing integration
        """
        return self.plot_thread_service.process_pose_for_plot_threads(pose, scene_id)
    
    def detect_environment_changes(
        self, 
        pose: Pose, 
        current_environment: EnvironmentState
    ) -> EnvironmentUpdate:
        """
        Detect environmental changes from pose content.
        
        Args:
            pose: The pose to analyze
            current_environment: Current environment state
            
        Returns:
            EnvironmentUpdate with detected changes
            
        Requirements: 3.2 - Check for consistency with established details
        """
        self.logger.debug(f"Detecting environment changes in pose {pose.id}")
        
        try:
            # Build environment analysis prompt
            env_prompt = self._build_environment_analysis_prompt(pose, current_environment)
            
            # Call Venice.ai for analysis
            response = self.venice_client.generate_completion(
                prompt=env_prompt,
                model=self.analysis_config['model'],
                temperature=self.analysis_config['temperature'],
                max_tokens=4000
            )
            
            # Parse response
            env_data = self._parse_environment_response(response)
            
            # Create environment update
            update = EnvironmentUpdate(
                location_name=env_data.get('location', current_environment.location_name),
                change_type=env_data.get('change_type', 'none'),
                description=env_data.get('description', ''),
                details=env_data.get('details', {}),
                confidence=env_data.get('confidence', 0.5)
            )
            
            return update
            
        except VeniceAPIError as e:
            self.logger.error(f"Venice.ai API error during environment analysis: {e}")
            return self._create_fallback_environment_update(current_environment.location_name)
        except Exception as e:
            self.logger.error(f"Error during environment analysis: {e}")
            return self._create_fallback_environment_update(current_environment.location_name)
    
    def flag_continuity_issues(self, analysis: ContinuityAnalysis) -> List[ContinuityFlag]:
        """
        Generate continuity flags based on analysis results.
        
        Args:
            analysis: ContinuityAnalysis results
            
        Returns:
            List of ContinuityFlag instances for detected issues
            
        Requirements: 6.3 - Alert users before pose submission
        """
        flags = []
        
        # Check consistency scores and generate flags
        if analysis.character_consistency_score < self.analysis_config['flag_threshold']:
            flag = ContinuityFlag(
                pose_id=analysis.pose_id,
                flag_type=FlagType.CHARACTER_INCONSISTENCY,
                description="Character behavior appears inconsistent with previous portrayals",
                severity=self._determine_severity(analysis.character_consistency_score),
                confidence_score=analysis.overall_confidence
            )
            flags.append(flag)
        
        if analysis.environment_consistency_score < self.analysis_config['flag_threshold']:
            flag = ContinuityFlag(
                pose_id=analysis.pose_id,
                flag_type=FlagType.ENVIRONMENT_CONTRADICTION,
                description="Environmental details may conflict with established scene elements",
                severity=self._determine_severity(analysis.environment_consistency_score),
                confidence_score=analysis.overall_confidence
            )
            flags.append(flag)
        
        if analysis.plot_consistency_score < self.analysis_config['flag_threshold']:
            flag = ContinuityFlag(
                pose_id=analysis.pose_id,
                flag_type=FlagType.PLOT_CONTRADICTION,
                description="Plot elements may contradict established story threads",
                severity=self._determine_severity(analysis.plot_consistency_score),
                confidence_score=analysis.overall_confidence
            )
            flags.append(flag)
        
        if analysis.timeline_consistency_score < self.analysis_config['flag_threshold']:
            flag = ContinuityFlag(
                pose_id=analysis.pose_id,
                flag_type=FlagType.TIMELINE_ISSUE,
                description="Timeline inconsistencies detected in pose content",
                severity=self._determine_severity(analysis.timeline_consistency_score),
                confidence_score=analysis.overall_confidence
            )
            flags.append(flag)
        
        # Save flags to database
        for flag in flags:
            flag.save()
        
        return flags
    
    def get_continuity_flags(
        self, 
        scene_id: str, 
        resolved: Optional[bool] = None
    ) -> List[ContinuityFlag]:
        """
        Get continuity flags for a scene.
        
        Args:
            scene_id: ID of the scene
            resolved: Filter by resolution status (None for all)
            
        Returns:
            List of ContinuityFlag instances
        """
        return ContinuityFlag.find_by_scene(scene_id, resolved)
    
    def resolve_continuity_flag(
        self, 
        flag_id: str, 
        resolution_notes: Optional[str] = None
    ) -> bool:
        """
        Mark a continuity flag as resolved.
        
        Args:
            flag_id: ID of the flag to resolve
            resolution_notes: Optional notes about the resolution
            
        Returns:
            True if successful, False if flag not found
        """
        flag = ContinuityFlag.find_by_id(flag_id)
        if not flag:
            return False
        
        flag.resolve(resolution_notes)
        flag.save()
        
        self.logger.info(f"Resolved continuity flag {flag_id}")
        return True
    
    def get_scene_continuity_summary(self, scene_id: str) -> Dict[str, Any]:
        """
        Get a summary of continuity status for a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            Dictionary with continuity summary information
        """
        flags = self.get_continuity_flags(scene_id)
        unresolved_flags = [f for f in flags if not f.resolved]
        
        # Count flags by type and severity
        flag_counts = {}
        severity_counts = {}
        
        for flag in unresolved_flags:
            flag_counts[flag.flag_type.value] = flag_counts.get(flag.flag_type.value, 0) + 1
            severity_counts[flag.severity.value] = severity_counts.get(flag.severity.value, 0) + 1
        
        return {
            'scene_id': scene_id,
            'total_flags': len(flags),
            'unresolved_flags': len(unresolved_flags),
            'resolved_flags': len(flags) - len(unresolved_flags),
            'flag_types': flag_counts,
            'severity_distribution': severity_counts,
            'overall_health': self._calculate_scene_health(unresolved_flags),
            'overall_score': max(0, 100 - (len(unresolved_flags) * 10)),  # Simple scoring
            'recent_activity': {
                'new_flags_24h': 0,
                'resolved_flags_24h': 0,
                'analysis_count_24h': 0
            },
            'recommendations': [
                "Review any critical flags first",
                "Check character consistency across scenes",
                "Verify environment continuity"
            ]
        } 
   
    # Private helper methods for AI prompt construction
    
    def _build_continuity_analysis_prompt(
        self, 
        pose: Pose, 
        scene_context: SceneContext
    ) -> str:
        """Build the AI prompt for continuity analysis."""
        
        # Gather context information
        recent_poses_text = "\n".join([
            f"[{p.character_name}]: {p.content}" 
            for p in scene_context.recent_poses[-5:]  # Last 5 poses for context
        ])
        
        character_states_text = "\n".join([
            f"{cs.character_name}: {json.dumps(cs.physical_state)} (emotional: {json.dumps(cs.emotional_state)})"
            for cs in scene_context.character_states
        ])
        
        environment_text = "\n".join([
            f"{es.location_name}: {es.description}"
            for es in scene_context.environment_states
        ])
        
        plot_threads_text = "\n".join([
            f"- {pt.title}: {pt.description} (status: {pt.status.value})"
            for pt in scene_context.plot_threads
        ])
        
        prompt = f"""You are a continuity analyst for roleplay scenes. Analyze the following pose for potential continuity issues.

CURRENT POSE TO ANALYZE:
Character: {pose.character_name}
Content: {pose.content}

SCENE CONTEXT:
Recent Poses:
{recent_poses_text}

Character States:
{character_states_text}

Environment:
{environment_text}

Plot Threads:
{plot_threads_text}

ANALYSIS INSTRUCTIONS:
Analyze the current pose for continuity with the established scene context. Provide your analysis as JSON with the following structure:

{{
    "character_consistency": 0.0-1.0,
    "environment_consistency": 0.0-1.0,
    "plot_consistency": 0.0-1.0,
    "timeline_consistency": 0.0-1.0,
    "confidence": 0.0-1.0,
    "issues": [
        {{
            "type": "character|environment|plot|timeline",
            "severity": "low|medium|high|critical",
            "description": "Description of the issue",
            "suggestion": "Suggested resolution"
        }}
    ],
    "plot_elements": [
        {{
            "title": "Plot element title",
            "description": "Description",
            "importance": 0.0-1.0,
            "type": "introduction|development|resolution|reference",
            "characters": ["character1", "character2"],
            "keywords": ["keyword1", "keyword2"]
        }}
    ],
    "state_changes": [
        {{
            "character": "character_name",
            "type": "physical|emotional|equipment|condition|location",
            "description": "Description of change",
            "confidence": 0.0-1.0
        }}
    ],
    "environment_changes": [
        {{
            "type": "weather|time|physical|location",
            "description": "Description of change",
            "confidence": 0.0-1.0
        }}
    ],
    "notes": "Additional analysis notes"
}}

Focus on identifying inconsistencies, contradictions, and potential issues while being constructive and helpful."""
        
        return prompt
    
    def _build_character_consistency_prompt(
        self, 
        pose: Pose, 
        character_history: List[Pose]
    ) -> str:
        """Build the AI prompt for character consistency checking."""
        
        # Get recent character poses for context
        recent_poses = character_history[-10:] if len(character_history) > 10 else character_history
        history_text = "\n".join([
            f"[{p.timestamp.strftime('%Y-%m-%d %H:%M')}]: {p.content}"
            for p in recent_poses
        ])
        
        prompt = f"""You are a character consistency analyst for roleplay. Analyze the following pose for consistency with the character's established personality, voice, and behavior patterns.

CHARACTER: {pose.character_name}

CURRENT POSE:
{pose.content}

CHARACTER HISTORY (Recent poses):
{history_text}

ANALYSIS INSTRUCTIONS:
Analyze the current pose for consistency with the character's established patterns. Provide your analysis as JSON:

{{
    "overall_score": 0.0-1.0,
    "voice_score": 0.0-1.0,
    "behavior_score": 0.0-1.0,
    "relationship_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "issues": [
        "List of specific consistency issues found"
    ],
    "strengths": [
        "List of consistent elements that work well"
    ],
    "suggestions": [
        "Constructive suggestions for improvement"
    ],
    "voice_analysis": "Analysis of character voice consistency",
    "behavior_analysis": "Analysis of behavior consistency",
    "relationship_analysis": "Analysis of relationship consistency"
}}

Consider speaking patterns, personality traits, emotional responses, relationship dynamics, and behavioral consistency."""
        
        return prompt
    
    def _build_plot_extraction_prompt(self, pose: Pose) -> str:
        """Build the AI prompt for plot element extraction."""
        
        prompt = f"""You are a plot analyst for roleplay scenes. Extract and identify plot elements from the following pose.

CHARACTER: {pose.character_name}
POSE CONTENT:
{pose.content}

ANALYSIS INSTRUCTIONS:
Identify plot-relevant elements in this pose. Look for:
- New plot introductions
- Plot developments or progressions
- Plot resolutions or conclusions
- References to existing plot threads
- Character motivations and goals
- Conflicts and tensions
- Important revelations or discoveries

Provide your analysis as JSON:

{{
    "elements": [
        {{
            "title": "Brief title for the plot element",
            "description": "Detailed description of the plot element",
            "importance": 0.0-1.0,
            "type": "introduction|development|resolution|reference",
            "characters": ["list", "of", "involved", "characters"],
            "keywords": ["relevant", "keywords", "for", "searching"],
            "emotional_weight": "low|medium|high",
            "urgency": "low|medium|high",
            "scope": "personal|interpersonal|scene|campaign"
        }}
    ],
    "overall_plot_significance": 0.0-1.0,
    "narrative_hooks": [
        "List of potential story hooks or follow-up opportunities"
    ],
    "character_development": [
        "Character development opportunities or moments"
    ]
}}

Only identify genuine plot elements - avoid over-analyzing mundane actions."""
        
        return prompt
    
    def _build_environment_analysis_prompt(
        self, 
        pose: Pose, 
        current_environment: EnvironmentState
    ) -> str:
        """Build the AI prompt for environment analysis."""
        
        prompt = f"""You are an environment continuity analyst for roleplay scenes. Analyze the following pose for environmental details and changes.

CURRENT ENVIRONMENT STATE:
Location: {current_environment.location_name}
Description: {current_environment.description}
Weather: {json.dumps(current_environment.weather)}
Time Context: {json.dumps(current_environment.time_context)}
Physical Details: {json.dumps(current_environment.physical_details)}

POSE TO ANALYZE:
Character: {pose.character_name}
Content: {pose.content}

ANALYSIS INSTRUCTIONS:
Analyze the pose for environmental references and changes. Provide your analysis as JSON:

{{
    "location": "Current location name",
    "change_type": "none|weather|time|physical|new_location",
    "description": "Description of any environmental changes",
    "confidence": 0.0-1.0,
    "details": {{
        "weather_changes": {{}},
        "time_changes": {{}},
        "physical_changes": {{}},
        "new_elements": {{}}
    }},
    "consistency_issues": [
        "List of any environmental contradictions"
    ],
    "environmental_mood": "Description of environmental atmosphere",
    "sensory_details": [
        "List of sensory details mentioned (sight, sound, smell, etc.)"
    ]
}}

Focus on identifying environmental changes, new details, and potential contradictions with established environment."""
        
        return prompt
    
    # Response parsing methods
    
    def _parse_continuity_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response for continuity analysis."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse continuity analysis response as JSON")
            return {
                'character_consistency': 0.8,
                'environment_consistency': 0.8,
                'plot_consistency': 0.8,
                'timeline_consistency': 0.8,
                'confidence': 0.5,
                'issues': [],
                'plot_elements': [],
                'state_changes': [],
                'environment_changes': [],
                'notes': 'Analysis parsing failed'
            }
    
    def _parse_character_consistency_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response for character consistency checking."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse character consistency response as JSON")
            return {
                'overall_score': 0.8,
                'voice_score': 0.8,
                'behavior_score': 0.8,
                'relationship_score': 0.8,
                'confidence': 0.5,
                'issues': [],
                'strengths': [],
                'suggestions': []
            }
    
    def _parse_plot_extraction_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response for plot extraction."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse plot extraction response as JSON")
            return {
                'elements': [],
                'overall_plot_significance': 0.3,
                'narrative_hooks': [],
                'character_development': []
            }
    
    def _parse_environment_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response for environment analysis."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse environment analysis response as JSON")
            return {
                'location': 'Unknown',
                'change_type': 'none',
                'description': '',
                'confidence': 0.5,
                'details': {},
                'consistency_issues': []
            }
    
    # Helper methods for data processing
    
    def _generate_continuity_flags(
        self, 
        pose_id: str, 
        analysis_data: Dict[str, Any]
    ) -> List[ContinuityFlag]:
        """Generate continuity flags from analysis data."""
        flags = []
        
        for issue in analysis_data.get('issues', []):
            flag_type_map = {
                'character': FlagType.CHARACTER_INCONSISTENCY,
                'environment': FlagType.ENVIRONMENT_CONTRADICTION,
                'plot': FlagType.PLOT_CONTRADICTION,
                'timeline': FlagType.TIMELINE_ISSUE
            }
            
            severity_map = {
                'low': Severity.LOW,
                'medium': Severity.MEDIUM,
                'high': Severity.HIGH,
                'critical': Severity.CRITICAL
            }
            
            flag = ContinuityFlag(
                pose_id=pose_id,
                flag_type=flag_type_map.get(issue.get('type', 'character'), FlagType.CHARACTER_INCONSISTENCY),
                description=issue.get('description', 'Continuity issue detected'),
                severity=severity_map.get(issue.get('severity', 'medium'), Severity.MEDIUM),
                confidence_score=analysis_data.get('confidence', 0.7)
            )
            flags.append(flag)
        
        return flags
    
    def _extract_plot_elements_from_analysis(
        self, 
        analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract plot elements from analysis data."""
        return analysis_data.get('plot_elements', [])
    
    def _detect_character_state_changes(
        self, 
        pose: Pose, 
        analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect character state changes from analysis data."""
        changes = []
        
        for change in analysis_data.get('state_changes', []):
            changes.append({
                'character_name': change.get('character', pose.character_name),
                'change_type': change.get('type', 'unknown'),
                'description': change.get('description', ''),
                'confidence': change.get('confidence', 0.5)
            })
        
        return changes
    
    def _detect_environment_changes(
        self, 
        pose: Pose, 
        analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect environment changes from analysis data."""
        changes = []
        
        for change in analysis_data.get('environment_changes', []):
            changes.append({
                'change_type': change.get('type', 'unknown'),
                'description': change.get('description', ''),
                'confidence': change.get('confidence', 0.5)
            })
        
        return changes
    
    def _determine_severity(self, score: float) -> Severity:
        """Determine severity based on consistency score."""
        if score < 0.3:
            return Severity.CRITICAL
        elif score < 0.5:
            return Severity.HIGH
        elif score < 0.7:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _calculate_scene_health(self, unresolved_flags: List[ContinuityFlag]) -> str:
        """Calculate overall scene continuity health."""
        if not unresolved_flags:
            return "excellent"
        
        critical_count = sum(1 for f in unresolved_flags if f.severity == Severity.CRITICAL)
        high_count = sum(1 for f in unresolved_flags if f.severity == Severity.HIGH)
        
        if critical_count > 0:
            return "critical"
        elif high_count > 2:
            return "poor"
        elif len(unresolved_flags) > 5:
            return "fair"
        else:
            return "good"
    
    # Fallback methods for error handling
    
    def _create_fallback_analysis(self, pose_id: str) -> ContinuityAnalysis:
        """Create a fallback analysis when AI analysis fails."""
        return ContinuityAnalysis(
            pose_id=pose_id,
            character_consistency_score=0.8,
            environment_consistency_score=0.8,
            plot_consistency_score=0.8,
            timeline_consistency_score=0.8,
            overall_confidence=0.3,
            flags=[],
            extracted_plot_elements=[],
            character_state_changes=[],
            environment_changes=[],
            analysis_notes="Analysis unavailable - AI service error"
        )
    
    def _create_fallback_consistency_check(self, character_name: str) -> ConsistencyCheck:
        """Create a fallback consistency check when AI analysis fails."""
        return ConsistencyCheck(
            character_name=character_name,
            consistency_score=0.8,
            voice_consistency=0.8,
            behavior_consistency=0.8,
            relationship_consistency=0.8,
            issues=[],
            confidence=0.3
        )
    
    def _create_fallback_environment_update(self, location_name: str) -> EnvironmentUpdate:
        """Create a fallback environment update when AI analysis fails."""
        return EnvironmentUpdate(
            location_name=location_name,
            change_type="none",
            description="Environment analysis unavailable",
            details={},
            confidence=0.3
        )


# Factory function for creating continuity service
def create_continuity_service(venice_client: VeniceClient) -> ContinuityService:
    """
    Factory function to create a ContinuityService instance.
    
    Args:
        venice_client: Venice.ai client for AI analysis
        
    Returns:
        Configured ContinuityService instance
    """
    return ContinuityService(venice_client)