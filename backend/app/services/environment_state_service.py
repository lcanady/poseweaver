"""
Environment State Management Service for Scene Memory & Continuity Tracking.

This service provides environmental state tracking, detail extraction from poses,
and consistency checking for MUSH roleplay scenes according to the Scene Memory
& Continuity spec requirements 3.1-3.5.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import logging
import json
from ..models.scene_memory import EnvironmentState, Pose
from .ai_client import AIClient, OpenRouterAPIError

logger = logging.getLogger(__name__)


class EnvironmentUpdate:
    """Data structure for environment state updates."""
    
    def __init__(
        self,
        location_name: Optional[str] = None,
        description: Optional[str] = None,
        weather: Optional[Dict[str, Any]] = None,
        time_context: Optional[Dict[str, Any]] = None,
        physical_details: Optional[Dict[str, Any]] = None,
        changes_detected: Optional[List[str]] = None
    ):
        self.location_name = location_name
        self.description = description
        self.weather = weather or {}
        self.time_context = time_context or {}
        self.physical_details = physical_details or {}
        self.changes_detected = changes_detected or []


class EnvironmentConsistencyCheck:
    """Result of environment consistency checking."""
    
    def __init__(
        self,
        is_consistent: bool,
        conflicts: List[Dict[str, Any]] = None,
        confidence_score: float = 0.0,
        details: Optional[str] = None
    ):
        self.is_consistent = is_consistent
        self.conflicts = conflicts or []
        self.confidence_score = confidence_score
        self.details = details


class EnvironmentStateService:
    """
    Service for managing environmental state tracking within scenes.
    
    This service handles:
    - Environmental detail extraction from pose content using AI analysis
    - Environmental state initialization and updates
    - Environmental consistency checking against established details
    - Location and setting management within scenes
    """
    
    def __init__(self, ai_client: Optional[AIClient] = None):
        """
        Initialize the environment state service.
        
        Args:
            ai_client: Optional OpenRouter.ai client for AI analysis
        """
        self.logger = logging.getLogger(__name__)
        self.ai_client = ai_client
    
    def initialize_environment_state(
        self,
        scene_id: str,
        location_name: str,
        description: str = "",
        weather: Optional[Dict[str, Any]] = None,
        time_context: Optional[Dict[str, Any]] = None,
        physical_details: Optional[Dict[str, Any]] = None
    ) -> EnvironmentState:
        """
        Initialize environment state for a scene.
        
        Args:
            scene_id: ID of the scene
            location_name: Name of the location
            description: Description of the environment
            weather: Weather conditions dictionary
            time_context: Time-related context (time of day, season, etc.)
            physical_details: Physical environmental details
            
        Returns:
            The created EnvironmentState instance
            
        Requirements: 3.1 - Extract and store location information, weather, time of day, and physical descriptions
        """
        self.logger.info(f"Initializing environment state for scene {scene_id}: {location_name}")
        
        environment_state = EnvironmentState(
            scene_id=scene_id,
            location_name=location_name,
            description=description,
            weather=weather or {},
            time_context=time_context or {},
            physical_details=physical_details or {}
        )
        
        # Save to database
        env_id = environment_state.save()
        self.logger.info(f"Created environment state {env_id} for scene {scene_id}")
        
        return environment_state
    
    def extract_environmental_details(self, pose: Pose) -> Dict[str, Any]:
        """
        Extract environmental details from pose content using AI analysis.
        
        Args:
            pose: Pose to analyze for environmental details
            
        Returns:
            Dictionary containing extracted environmental information
            
        Requirements: 3.1 - Extract and store environmental details from poses
        """
        self.logger.debug(f"Extracting environmental details from pose {pose.id}")
        
        if not self.ai_client:
            self.logger.warning("No OpenRouter client available, using basic extraction")
            return self._extract_basic_environmental_details(pose)
        
        try:
            # Create system prompt for environmental detail extraction
            system_prompt = """You are an environmental detail extraction assistant for MUSH roleplay scenes. 
            Analyze the provided pose text and extract environmental information.
            
            Extract the following environmental details if present:
            - location_name: The name or type of location mentioned
            - weather: Weather conditions (temperature, precipitation, wind, etc.)
            - time_context: Time of day, season, or temporal references
            - lighting: Lighting conditions and sources
            - sounds: Ambient sounds or audio details
            - smells: Scents or odors mentioned
            - temperature: Temperature or thermal conditions
            - atmosphere: General mood or feeling of the environment
            - physical_features: Physical characteristics of the location
            - objects: Environmental objects or features mentioned
            
            Output ONLY valid JSON without explanation. Use null for missing information."""
            
            # Prepare the pose content for analysis
            user_content = f"Pose by {pose.character_name}:\n{pose.content}"
            
            # Call OpenRouter.ai for analysis
            response = self.ai_client.generate_completion(
                prompt=user_content,
                system_message=system_prompt,
                model="qwen3-235b",
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=800
            )
            
            # Parse the response
            try:
                environmental_data = json.loads(response)
                self.logger.debug(f"Extracted environmental data: {environmental_data}")
                return environmental_data
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse AI response as JSON: {response}")
                return self._extract_basic_environmental_details(pose)
                
        except OpenRouterAPIError as e:
            self.logger.error(f"OpenRouter API error during environmental extraction: {e}")
            return self._extract_basic_environmental_details(pose)
        except Exception as e:
            self.logger.error(f"Unexpected error during environmental extraction: {e}")
            return self._extract_basic_environmental_details(pose)
    
    def _extract_basic_environmental_details(self, pose: Pose) -> Dict[str, Any]:
        """
        Basic environmental detail extraction without AI.
        
        Args:
            pose: Pose to analyze
            
        Returns:
            Dictionary with basic environmental information
        """
        content_lower = pose.content.lower()
        
        # Basic keyword-based extraction
        environmental_data = {
            "location_name": None,
            "weather": {},
            "time_context": {},
            "lighting": None,
            "sounds": None,
            "smells": None,
            "temperature": None,
            "atmosphere": None,
            "physical_features": [],
            "objects": []
        }
        
        # Simple weather detection
        weather_keywords = {
            "rain": "rainy",
            "snow": "snowy",
            "sun": "sunny",
            "cloud": "cloudy",
            "wind": "windy",
            "storm": "stormy"
        }
        
        for keyword, condition in weather_keywords.items():
            if keyword in content_lower:
                environmental_data["weather"]["condition"] = condition
                break
        
        # Simple time detection
        time_keywords = {
            "morning": "morning",
            "afternoon": "afternoon",
            "evening": "evening",
            "night": "night",
            "dawn": "dawn",
            "dusk": "dusk",
            "midnight": "midnight",
            "noon": "noon"
        }
        
        for keyword, time_period in time_keywords.items():
            if keyword in content_lower:
                environmental_data["time_context"]["time_of_day"] = time_period
                break
        
        # Simple lighting detection
        lighting_keywords = ["bright", "dim", "dark", "shadowy", "illuminated", "lit"]
        for keyword in lighting_keywords:
            if keyword in content_lower:
                environmental_data["lighting"] = keyword
                break
        
        return environmental_data
    
    def detect_environment_changes(
        self,
        pose: Pose,
        current_environment: EnvironmentState
    ) -> EnvironmentUpdate:
        """
        Detect environmental changes from a pose compared to current state.
        
        Args:
            pose: Pose to analyze for environmental changes
            current_environment: Current environment state
            
        Returns:
            EnvironmentUpdate with detected changes
            
        Requirements: 3.4 - Create new environmental context when scene moves to new location
        """
        self.logger.debug(f"Detecting environment changes from pose {pose.id}")
        
        # Extract environmental details from the pose
        extracted_details = self.extract_environmental_details(pose)
        
        # Compare with current environment state
        changes_detected = []
        update = EnvironmentUpdate()
        
        # Check for location changes
        if extracted_details.get("location_name") and extracted_details["location_name"] != current_environment.location_name:
            update.location_name = extracted_details["location_name"]
            changes_detected.append(f"Location changed to: {extracted_details['location_name']}")
        
        # Check for weather changes
        current_weather = current_environment.weather or {}
        new_weather = extracted_details.get("weather", {})
        if new_weather and new_weather != current_weather:
            update.weather = {**current_weather, **new_weather}
            changes_detected.append("Weather conditions updated")
        
        # Check for time context changes
        current_time = current_environment.time_context or {}
        new_time = extracted_details.get("time_context", {})
        if new_time and new_time != current_time:
            update.time_context = {**current_time, **new_time}
            changes_detected.append("Time context updated")
        
        # Check for physical detail changes
        current_physical = current_environment.physical_details or {}
        new_physical = {}
        
        # Consolidate physical details from extracted data
        for key in ["lighting", "sounds", "smells", "temperature", "atmosphere", "physical_features", "objects"]:
            if extracted_details.get(key):
                new_physical[key] = extracted_details[key]
        
        # Also check for nested physical_details object
        if extracted_details.get("physical_details") and isinstance(extracted_details["physical_details"], dict):
            new_physical.update(extracted_details["physical_details"])
        
        if new_physical:
            update.physical_details = {**current_physical, **new_physical}
            changes_detected.append("Physical environment details updated")
        
        update.changes_detected = changes_detected
        
        if changes_detected:
            self.logger.info(f"Detected environment changes: {changes_detected}")
        
        return update
    
    def update_environment_state(
        self,
        scene_id: str,
        environment_update: EnvironmentUpdate
    ) -> Optional[EnvironmentState]:
        """
        Update environment state with detected changes.
        
        Args:
            scene_id: ID of the scene
            environment_update: EnvironmentUpdate with changes to apply
            
        Returns:
            Updated EnvironmentState or None if no current state found
            
        Requirements: 3.4 - Create new environmental context when scene moves to new location
        """
        self.logger.debug(f"Updating environment state for scene {scene_id}")
        
        # Get current environment states for the scene
        current_environments = EnvironmentState.find_by_scene(scene_id)
        
        # If location changed, create new environment state
        if environment_update.location_name:
            self.logger.info(f"Creating new environment state for location: {environment_update.location_name}")
            return self.initialize_environment_state(
                scene_id=scene_id,
                location_name=environment_update.location_name,
                description=environment_update.description or "",
                weather=environment_update.weather,
                time_context=environment_update.time_context,
                physical_details=environment_update.physical_details
            )
        
        # Otherwise, update the most recent environment state
        if current_environments:
            current_env = current_environments[-1]  # Most recent
            
            # Update fields that have changes
            if environment_update.weather:
                current_env.weather.update(environment_update.weather)
            if environment_update.time_context:
                current_env.time_context.update(environment_update.time_context)
            if environment_update.physical_details:
                current_env.physical_details.update(environment_update.physical_details)
            if environment_update.description:
                current_env.description = environment_update.description
            
            # Save the updated state
            current_env.updated_at = datetime.utcnow()
            current_env.save()
            
            self.logger.debug(f"Updated environment state {current_env.id}")
            return current_env
        
        return None
    
    def check_environmental_consistency(
        self,
        pose: Pose,
        current_environment: EnvironmentState
    ) -> EnvironmentConsistencyCheck:
        """
        Check environmental consistency between pose and established environment.
        
        Args:
            pose: Pose to check for consistency
            current_environment: Current established environment state
            
        Returns:
            EnvironmentConsistencyCheck with consistency results
            
        Requirements: 3.2, 3.3 - Check for consistency with established details and flag contradictions
        """
        self.logger.debug(f"Checking environmental consistency for pose {pose.id}")
        
        if not self.ai_client:
            self.logger.warning("No OpenRouter client available, using basic consistency check")
            return self._check_basic_environmental_consistency(pose, current_environment)
        
        try:
            # Prepare context for AI analysis
            established_context = {
                "location": current_environment.location_name,
                "description": current_environment.description,
                "weather": current_environment.weather,
                "time_context": current_environment.time_context,
                "physical_details": current_environment.physical_details
            }
            
            system_prompt = """You are an environmental consistency checker for MUSH roleplay scenes.
            Compare the environmental details mentioned in the new pose against the established environment.
            
            Look for contradictions in:
            - Location/setting details
            - Weather conditions
            - Time of day/temporal context
            - Lighting conditions
            - Physical features of the environment
            - Atmospheric conditions
            
            Output ONLY valid JSON with this structure:
            {
                "is_consistent": boolean,
                "conflicts": [
                    {
                        "type": "weather|time|location|lighting|physical",
                        "description": "description of the conflict",
                        "established": "what was previously established",
                        "conflicting": "what the new pose suggests",
                        "severity": "low|medium|high"
                    }
                ],
                "confidence_score": float between 0.0 and 1.0,
                "details": "explanation of the analysis"
            }"""
            
            user_content = f"""Established Environment:
{json.dumps(established_context, indent=2)}

New Pose by {pose.character_name}:
{pose.content}

Check for environmental consistency."""
            
            # Call OpenRouter.ai for analysis
            response = self.ai_client.generate_completion(
                prompt=user_content,
                system_message=system_prompt,
                model="qwen3-235b",
                temperature=0.2,  # Very low temperature for consistent analysis
                max_tokens=4000
            )
            
            # Parse the response
            try:
                consistency_data = json.loads(response)
                return EnvironmentConsistencyCheck(
                    is_consistent=consistency_data.get("is_consistent", True),
                    conflicts=consistency_data.get("conflicts", []),
                    confidence_score=consistency_data.get("confidence_score", 0.5),
                    details=consistency_data.get("details", "")
                )
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse AI consistency response: {response}")
                return self._check_basic_environmental_consistency(pose, current_environment)
                
        except OpenRouterAPIError as e:
            self.logger.error(f"OpenRouter API error during consistency check: {e}")
            return self._check_basic_environmental_consistency(pose, current_environment)
        except Exception as e:
            self.logger.error(f"Unexpected error during consistency check: {e}")
            return self._check_basic_environmental_consistency(pose, current_environment)
    
    def _check_basic_environmental_consistency(
        self,
        pose: Pose,
        current_environment: EnvironmentState
    ) -> EnvironmentConsistencyCheck:
        """
        Basic environmental consistency check without AI.
        
        Args:
            pose: Pose to check
            current_environment: Current environment state
            
        Returns:
            EnvironmentConsistencyCheck with basic analysis
        """
        # Extract basic details from pose
        extracted_details = self._extract_basic_environmental_details(pose)
        
        conflicts = []
        
        # Check weather consistency
        if (extracted_details.get("weather", {}).get("condition") and
            current_environment.weather.get("condition") and
            extracted_details["weather"]["condition"] != current_environment.weather["condition"]):
            conflicts.append({
                "type": "weather",
                "description": "Weather condition mismatch",
                "established": current_environment.weather["condition"],
                "conflicting": extracted_details["weather"]["condition"],
                "severity": "medium"
            })
        
        # Check time consistency (basic)
        if (extracted_details.get("time_context", {}).get("time_of_day") and
            current_environment.time_context.get("time_of_day") and
            extracted_details["time_context"]["time_of_day"] != current_environment.time_context["time_of_day"]):
            conflicts.append({
                "type": "time",
                "description": "Time of day mismatch",
                "established": current_environment.time_context["time_of_day"],
                "conflicting": extracted_details["time_context"]["time_of_day"],
                "severity": "low"
            })
        
        return EnvironmentConsistencyCheck(
            is_consistent=len(conflicts) == 0,
            conflicts=conflicts,
            confidence_score=0.6,  # Moderate confidence for basic check
            details="Basic keyword-based consistency check performed"
        )
    
    def get_scene_environments(self, scene_id: str) -> List[EnvironmentState]:
        """
        Get all environment states for a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            List of EnvironmentState instances ordered by establishment time
            
        Requirements: 3.5 - Provide quick access to established scene elements
        """
        return EnvironmentState.find_by_scene(scene_id)
    
    def get_current_environment(self, scene_id: str) -> Optional[EnvironmentState]:
        """
        Get the current (most recent) environment state for a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            Most recent EnvironmentState or None if no environments exist
            
        Requirements: 3.5 - Provide quick access to established scene elements
        """
        environments = self.get_scene_environments(scene_id)
        return environments[-1] if environments else None
    
    def process_pose_for_environment(
        self,
        pose: Pose,
        scene_id: str
    ) -> Optional[EnvironmentState]:
        """
        Process a pose for environmental tracking and consistency.
        
        This is the main entry point that combines environmental detail extraction,
        change detection, consistency checking, and flag creation.
        
        Args:
            pose: Pose to process
            scene_id: ID of the scene
            
        Returns:
            Updated or created EnvironmentState
            
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5 - Complete environmental processing workflow
        """
        self.logger.info(f"Processing pose {pose.id} for environmental tracking")
        
        # Get current environment state
        current_environment = self.get_current_environment(scene_id)
        
        # If no environment exists, create initial one from pose
        if not current_environment:
            extracted_details = self.extract_environmental_details(pose)
            location_name = extracted_details.get("location_name") or "Unknown Location"
            
            current_environment = self.initialize_environment_state(
                scene_id=scene_id,
                location_name=location_name,
                weather=extracted_details.get("weather", {}),
                time_context=extracted_details.get("time_context", {}),
                physical_details={
                    k: v for k, v in extracted_details.items()
                    if k not in ["location_name", "weather", "time_context"] and v
                }
            )
            
            return current_environment
        
        # Check for environmental consistency
        consistency_check = self.check_environmental_consistency(pose, current_environment)
        
        # Detect and apply environmental changes
        environment_update = self.detect_environment_changes(pose, current_environment)
        
        if environment_update.changes_detected:
            updated_environment = self.update_environment_state(scene_id, environment_update)
            return updated_environment or current_environment
        
        return current_environment