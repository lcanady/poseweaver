"""
Plot Thread Tracking Service for Scene Memory & Continuity Tracking.

This service provides plot element identification, tracking, linking, and management
for maintaining narrative coherence in MUSH roleplay sessions.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging
from dataclasses import dataclass
from ..models.scene_memory import (
    PlotThread, Pose, PlotStatus
)
from ..services.ai_client import AIClient, OpenRouterAPIError

logger = logging.getLogger(__name__)


@dataclass
class PlotElement:
    """Extracted plot element from pose analysis."""
    title: str
    description: str
    importance_score: float
    element_type: str  # "introduction", "development", "resolution", "reference"
    related_characters: List[str]
    keywords: List[str]
    emotional_weight: str  # "low", "medium", "high"
    urgency: str  # "low", "medium", "high"
    scope: str  # "personal", "interpersonal", "scene", "campaign"


@dataclass
class PlotThreadLink:
    """Link between plot threads."""
    source_thread_id: str
    target_thread_id: str
    relationship_type: str  # "causes", "conflicts_with", "supports", "references"
    strength: float  # 0.0-1.0
    description: str


@dataclass
class PlotReminder:
    """Reminder for stale plot threads."""
    thread_id: str
    title: str
    days_since_reference: int
    importance_score: float
    suggested_action: str
    reminder_text: str


class PlotThreadService:
    """
    Service for plot thread identification, tracking, and management.
    
    This service provides:
    - AI-powered plot element extraction from poses
    - Plot thread creation and lifecycle management
    - Plot thread linking and relationship tracking
    - Stale plot thread detection and reminders
    - Plot thread status tracking and updates
    """
    
    def __init__(self, ai_client: AIClient):
        """
        Initialize the plot thread service.
        
        Args:
            ai_client: OpenRouter.ai client for AI analysis
        """
        self.ai_client = ai_client
        self.logger = logging.getLogger(__name__)
        
        # Configuration for plot analysis
        self.config = {
            'model': 'qwen3-235b',
            'temperature': 0.4,  # Balanced creativity and consistency
            'max_tokens': 2000,
            'importance_threshold': 0.3,  # Minimum importance to create thread
            'stale_days_threshold': 7,  # Days before thread is considered stale
            'reminder_importance_threshold': 0.4  # Minimum importance for reminders
        }
    
    def extract_plot_elements_from_pose(self, pose: Pose) -> List[PlotElement]:
        """
        Extract plot elements from a pose using AI analysis.
        
        Args:
            pose: The pose to analyze for plot elements
            
        Returns:
            List of extracted PlotElement instances
            
        Requirements: 4.1 - Identify and tag potential plot threads using AI analysis
        """
        self.logger.debug(f"Extracting plot elements from pose {pose.id}")
        
        try:
            # Build plot extraction prompt
            plot_prompt = self._build_plot_extraction_prompt(pose)
            
            # Call OpenRouter.ai for analysis
            response = self.ai_client.generate_completion(
                prompt=plot_prompt,
                model=self.config['model'],
                temperature=self.config['temperature'],
                max_tokens=self.config['max_tokens']
            )
            
            # Parse response and create plot elements
            plot_data = self._parse_plot_extraction_response(response)
            plot_elements = []
            
            for element_data in plot_data.get('elements', []):
                # Only create elements above importance threshold
                importance = element_data.get('importance', 0.0)
                if importance >= self.config['importance_threshold']:
                    element = PlotElement(
                        title=element_data.get('title', 'Untitled Plot Element'),
                        description=element_data.get('description', ''),
                        importance_score=importance,
                        element_type=element_data.get('type', 'reference'),
                        related_characters=element_data.get('characters', []),
                        keywords=element_data.get('keywords', []),
                        emotional_weight=element_data.get('emotional_weight', 'medium'),
                        urgency=element_data.get('urgency', 'medium'),
                        scope=element_data.get('scope', 'scene')
                    )
                    plot_elements.append(element)
            
            self.logger.debug(f"Extracted {len(plot_elements)} plot elements")
            return plot_elements
            
        except OpenRouterAPIError as e:
            self.logger.error(f"OpenRouter.ai API error during plot extraction: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error during plot extraction: {e}")
            return []
    
    def create_plot_thread_from_element(
        self, 
        scene_id: str, 
        element: PlotElement, 
        pose_id: str
    ) -> PlotThread:
        """
        Create a new plot thread from an extracted plot element.
        
        Args:
            scene_id: ID of the scene
            element: PlotElement to create thread from
            pose_id: ID of the pose that introduced this element
            
        Returns:
            Created PlotThread instance
            
        Requirements: 4.1 - Create plot thread records for identified elements
        """
        self.logger.info(f"Creating plot thread from element: {element.title}")
        
        # Determine initial status based on element type
        status_map = {
            'introduction': PlotStatus.INTRODUCED,
            'development': PlotStatus.DEVELOPING,
            'resolution': PlotStatus.RESOLVED,
            'reference': PlotStatus.DEVELOPING
        }
        
        initial_status = status_map.get(element.element_type, PlotStatus.INTRODUCED)
        
        # Create plot thread
        thread = PlotThread(
            scene_id=scene_id,
            title=element.title,
            description=element.description,
            status=initial_status,
            importance_score=element.importance_score,
            related_poses=[pose_id]
        )
        
        # Save to database
        thread.save()
        
        self.logger.info(f"Created plot thread {thread.id}: {thread.title}")
        return thread
    
    def update_plot_thread_from_pose(
        self, 
        thread: PlotThread, 
        pose: Pose, 
        element: PlotElement
    ) -> PlotThread:
        """
        Update an existing plot thread based on a new pose and element.
        
        Args:
            thread: Existing PlotThread to update
            pose: New pose referencing the thread
            element: PlotElement extracted from the pose
            
        Returns:
            Updated PlotThread instance
            
        Requirements: 4.2 - Link plot threads to subsequent references
        """
        self.logger.debug(f"Updating plot thread {thread.id} from pose {pose.id}")
        
        # Add pose to related poses
        thread.add_related_pose(pose.id)
        
        # Update importance score (weighted average)
        weight = 0.3  # Weight for new information
        thread.importance_score = (
            thread.importance_score * (1 - weight) + 
            element.importance_score * weight
        )
        
        # Update status based on element type
        if element.element_type == 'resolution' and thread.status != PlotStatus.RESOLVED:
            thread.status = PlotStatus.RESOLVED
            self.logger.info(f"Plot thread {thread.id} marked as resolved")
        elif element.element_type == 'development' and thread.status == PlotStatus.INTRODUCED:
            thread.status = PlotStatus.DEVELOPING
            self.logger.info(f"Plot thread {thread.id} marked as developing")
        
        # Update description if new element provides more detail
        if len(element.description) > len(thread.description):
            thread.description = element.description
        
        # Save changes
        thread.save()
        
        return thread
    
    def find_related_plot_threads(
        self, 
        scene_id: str, 
        element: PlotElement
    ) -> List[Tuple[PlotThread, float]]:
        """
        Find existing plot threads related to a new plot element.
        
        Args:
            scene_id: ID of the scene
            element: PlotElement to find relations for
            
        Returns:
            List of tuples (PlotThread, similarity_score)
            
        Requirements: 4.2 - Link plot threads to original introduction
        """
        self.logger.debug(f"Finding related threads for element: {element.title}")
        
        # Get all active plot threads in the scene
        existing_threads = PlotThread.find_by_scene(
            scene_id, 
            status=None  # Get all statuses except abandoned
        )
        existing_threads = [t for t in existing_threads if t.status != PlotStatus.ABANDONED]
        
        if not existing_threads:
            return []
        
        try:
            # Use AI to find semantic relationships
            similarity_prompt = self._build_thread_similarity_prompt(element, existing_threads)
            
            response = self.ai_client.generate_completion(
                prompt=similarity_prompt,
                model=self.config['model'],
                temperature=0.2,  # Lower temperature for consistent matching
                max_tokens=1500
            )
            
            # Parse similarity results
            similarity_data = self._parse_similarity_response(response)
            
            # Create result tuples
            related_threads = []
            for match in similarity_data.get('matches', []):
                thread_id = match.get('thread_id')
                similarity = match.get('similarity', 0.0)
                
                # Find the thread object
                thread = next((t for t in existing_threads if t.id == thread_id), None)
                if thread and similarity > 0.3:  # Minimum similarity threshold
                    related_threads.append((thread, similarity))
            
            # Sort by similarity score
            related_threads.sort(key=lambda x: x[1], reverse=True)
            
            self.logger.debug(f"Found {len(related_threads)} related threads")
            return related_threads
            
        except OpenRouterAPIError as e:
            self.logger.error(f"OpenRouter.ai API error during thread matching: {e}")
            return self._fallback_thread_matching(element, existing_threads)
        except Exception as e:
            self.logger.error(f"Error during thread matching: {e}")
            return self._fallback_thread_matching(element, existing_threads)
    
    def create_plot_thread_links(
        self, 
        source_thread: PlotThread, 
        target_threads: List[Tuple[PlotThread, float]]
    ) -> List[PlotThreadLink]:
        """
        Create links between related plot threads.
        
        Args:
            source_thread: The source plot thread
            target_threads: List of (target_thread, similarity_score) tuples
            
        Returns:
            List of created PlotThreadLink instances
            
        Requirements: 4.3 - Add plot thread linking and relationship management
        """
        self.logger.debug(f"Creating links for thread {source_thread.id}")
        
        links = []
        for target_thread, similarity in target_threads:
            if similarity > 0.5:  # Strong relationship threshold
                # Determine relationship type based on similarity and context
                relationship_type = self._determine_relationship_type(
                    source_thread, target_thread, similarity
                )
                
                link = PlotThreadLink(
                    source_thread_id=source_thread.id,
                    target_thread_id=target_thread.id,
                    relationship_type=relationship_type,
                    strength=similarity,
                    description=f"Related through {relationship_type} (strength: {similarity:.2f})"
                )
                links.append(link)
        
        self.logger.debug(f"Created {len(links)} thread links")
        return links
    
    def get_stale_plot_threads(
        self, 
        scene_id: str, 
        days_threshold: Optional[int] = None
    ) -> List[PlotThread]:
        """
        Find plot threads that haven't been referenced recently.
        
        Args:
            scene_id: ID of the scene
            days_threshold: Days since last reference (uses config default if None)
            
        Returns:
            List of stale PlotThread instances
            
        Requirements: 4.3 - Remind users of pending story elements
        """
        threshold = days_threshold or self.config['stale_days_threshold']
        
        stale_threads = PlotThread.find_stale_threads(scene_id, threshold)
        
        # Filter by importance for reminders
        important_stale = [
            t for t in stale_threads 
            if t.importance_score >= self.config['reminder_importance_threshold']
        ]
        
        self.logger.info(f"Found {len(important_stale)} important stale threads")
        return important_stale
    
    def generate_plot_reminders(
        self, 
        scene_id: str, 
        days_threshold: Optional[int] = None
    ) -> List[PlotReminder]:
        """
        Generate reminders for stale plot threads.
        
        Args:
            scene_id: ID of the scene
            days_threshold: Days since last reference
            
        Returns:
            List of PlotReminder instances
            
        Requirements: 4.4 - Implement plot thread status tracking and reminder system
        """
        stale_threads = self.get_stale_plot_threads(scene_id, days_threshold)
        
        reminders = []
        for thread in stale_threads:
            days_stale = (datetime.utcnow() - thread.last_referenced).days
            
            # Generate contextual reminder text
            reminder_text = self._generate_reminder_text(thread, days_stale)
            suggested_action = self._suggest_plot_action(thread)
            
            reminder = PlotReminder(
                thread_id=thread.id,
                title=thread.title,
                days_since_reference=days_stale,
                importance_score=thread.importance_score,
                suggested_action=suggested_action,
                reminder_text=reminder_text
            )
            reminders.append(reminder)
        
        # Sort by importance and staleness
        reminders.sort(
            key=lambda r: (r.importance_score, r.days_since_reference), 
            reverse=True
        )
        
        self.logger.info(f"Generated {len(reminders)} plot reminders")
        return reminders
    
    def update_plot_thread_status(
        self, 
        thread_id: str, 
        new_status: PlotStatus, 
        resolution_notes: Optional[str] = None
    ) -> bool:
        """
        Update the status of a plot thread.
        
        Args:
            thread_id: ID of the thread to update
            new_status: New status for the thread
            resolution_notes: Optional notes for resolution
            
        Returns:
            True if successful, False if thread not found
            
        Requirements: 4.4 - Plot thread status tracking
        """
        thread = PlotThread.find_by_id(thread_id)
        if not thread:
            self.logger.warning(f"Plot thread {thread_id} not found")
            return False
        
        old_status = thread.status
        thread.status = new_status
        
        if new_status == PlotStatus.RESOLVED:
            thread.resolve(resolution_notes)
        
        thread.save()
        
        self.logger.info(f"Updated thread {thread_id} status: {old_status} -> {new_status}")
        return True
    
    def get_plot_thread_summary(self, scene_id: str) -> Dict[str, Any]:
        """
        Get a summary of plot threads for a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            Dictionary with plot thread summary information
        """
        all_threads = PlotThread.find_by_scene(scene_id)
        
        # Count by status
        status_counts = {}
        for thread in all_threads:
            status = thread.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Get active threads (not resolved or abandoned)
        active_threads = [
            t for t in all_threads 
            if t.status in [PlotStatus.INTRODUCED, PlotStatus.DEVELOPING]
        ]
        
        # Calculate average importance
        avg_importance = (
            sum(t.importance_score for t in all_threads) / len(all_threads)
            if all_threads else 0.0
        )
        
        # Get stale threads
        stale_threads = self.get_stale_plot_threads(scene_id)
        
        return {
            'scene_id': scene_id,
            'total_threads': len(all_threads),
            'active_threads': len(active_threads),
            'status_distribution': status_counts,
            'average_importance': avg_importance,
            'stale_threads': len(stale_threads),
            'needs_attention': len([t for t in stale_threads if t.importance_score > 0.6])
        }
    
    def process_pose_for_plot_threads(
        self, 
        pose: Pose, 
        scene_id: str
    ) -> Dict[str, Any]:
        """
        Process a pose for plot thread creation and updates.
        
        This is the main entry point for plot thread processing.
        
        Args:
            pose: The pose to process
            scene_id: ID of the scene
            
        Returns:
            Dictionary with processing results
            
        Requirements: 4.1, 4.2 - Complete plot thread processing workflow
        """
        self.logger.info(f"Processing pose {pose.id} for plot threads")
        
        results = {
            'pose_id': pose.id,
            'extracted_elements': [],
            'created_threads': [],
            'updated_threads': [],
            'thread_links': []
        }
        
        try:
            # Extract plot elements from the pose
            elements = self.extract_plot_elements_from_pose(pose)
            results['extracted_elements'] = [
                {
                    'title': e.title,
                    'importance': e.importance_score,
                    'type': e.element_type
                }
                for e in elements
            ]
            
            # Process each extracted element
            for element in elements:
                # Find related existing threads
                related_threads = self.find_related_plot_threads(scene_id, element)
                
                if related_threads:
                    # Update the most similar existing thread
                    best_match, similarity = related_threads[0]
                    if similarity > 0.7:  # High similarity threshold for updates
                        updated_thread = self.update_plot_thread_from_pose(
                            best_match, pose, element
                        )
                        results['updated_threads'].append({
                            'thread_id': updated_thread.id,
                            'title': updated_thread.title,
                            'similarity': similarity
                        })
                        continue
                
                # Create new thread if no good match found
                new_thread = self.create_plot_thread_from_element(
                    scene_id, element, pose.id
                )
                results['created_threads'].append({
                    'thread_id': new_thread.id,
                    'title': new_thread.title,
                    'importance': new_thread.importance_score
                })
                
                # Create links to related threads
                if related_threads:
                    links = self.create_plot_thread_links(new_thread, related_threads)
                    results['thread_links'].extend([
                        {
                            'source': link.source_thread_id,
                            'target': link.target_thread_id,
                            'type': link.relationship_type,
                            'strength': link.strength
                        }
                        for link in links
                    ])
            
            self.logger.info(f"Plot thread processing complete for pose {pose.id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing pose for plot threads: {e}")
            results['error'] = str(e)
            return results    
 
   # Private helper methods
    
    def _build_plot_extraction_prompt(self, pose: Pose) -> str:
        """Build the AI prompt for plot element extraction."""
        
        prompt = f"""You are a plot analyst for roleplay scenes. Extract and identify plot elements from the following pose.

CHARACTER: {pose.character_name}
POSE CONTENT:
{pose.content}

ANALYSIS INSTRUCTIONS:
Identify plot-relevant elements in this pose. Look for:
- New plot introductions or story hooks
- Plot developments, progressions, or complications
- Plot resolutions, conclusions, or revelations
- References to existing plot threads or ongoing stories
- Character motivations, goals, and conflicts
- Important discoveries, revelations, or turning points
- Relationship dynamics that drive story forward

Provide your analysis as JSON:

{{
    "elements": [
        {{
            "title": "Brief, descriptive title for the plot element",
            "description": "Detailed description of the plot element and its significance",
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
        "Character development opportunities or moments identified"
    ]
}}

IMPORTANT: Only identify genuine plot elements that advance story or character development. 
Avoid over-analyzing mundane actions or simple interactions that don't contribute to narrative progression.
Focus on elements that create story momentum, conflict, or meaningful character growth."""
        
        return prompt
    
    def _build_thread_similarity_prompt(
        self, 
        element: PlotElement, 
        existing_threads: List[PlotThread]
    ) -> str:
        """Build prompt for finding thread similarities."""
        
        threads_text = "\n".join([
            f"ID: {t.id}\nTitle: {t.title}\nDescription: {t.description}\nStatus: {t.status.value}\n"
            for t in existing_threads
        ])
        
        prompt = f"""You are analyzing plot thread relationships. Determine which existing plot threads are related to a new plot element.

NEW PLOT ELEMENT:
Title: {element.title}
Description: {element.description}
Type: {element.element_type}
Characters: {', '.join(element.related_characters)}
Keywords: {', '.join(element.keywords)}

EXISTING PLOT THREADS:
{threads_text}

ANALYSIS INSTRUCTIONS:
Analyze semantic similarity and thematic connections between the new element and existing threads.
Consider:
- Shared characters or relationships
- Similar themes, conflicts, or goals
- Causal relationships (one leads to another)
- Complementary or opposing elements
- Shared keywords or concepts

Provide analysis as JSON:

{{
    "matches": [
        {{
            "thread_id": "exact_thread_id_from_above",
            "similarity": 0.0-1.0,
            "relationship_type": "causes|conflicts_with|supports|references|develops",
            "explanation": "Why these elements are related",
            "shared_elements": ["list", "of", "shared", "elements"]
        }}
    ],
    "analysis_notes": "Overall analysis of relationships found"
}}

Only include matches with similarity > 0.3. Be conservative - it's better to miss weak connections than create false ones."""
        
        return prompt
    
    def _parse_plot_extraction_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response for plot extraction."""
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse plot extraction response as JSON")
            return {
                'elements': [],
                'overall_plot_significance': 0.3,
                'narrative_hooks': [],
                'character_development': []
            }
    
    def _parse_similarity_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response for thread similarity analysis."""
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse similarity response as JSON")
            return {
                'matches': [],
                'analysis_notes': 'Parsing failed'
            }
    
    def _fallback_thread_matching(
        self, 
        element: PlotElement, 
        existing_threads: List[PlotThread]
    ) -> List[Tuple[PlotThread, float]]:
        """Fallback method for thread matching when AI fails."""
        matches = []
        
        # Simple keyword-based matching
        element_keywords = set(element.keywords + [element.title.lower()])
        
        for thread in existing_threads:
            thread_keywords = set([thread.title.lower()] + thread.description.lower().split())
            
            # Calculate simple overlap score
            overlap = len(element_keywords.intersection(thread_keywords))
            total_keywords = len(element_keywords.union(thread_keywords))
            
            if total_keywords > 0:
                similarity = overlap / total_keywords
                if similarity > 0.2:  # Minimum threshold
                    matches.append((thread, similarity))
        
        return sorted(matches, key=lambda x: x[1], reverse=True)
    
    def _determine_relationship_type(
        self, 
        source_thread: PlotThread, 
        target_thread: PlotThread, 
        similarity: float
    ) -> str:
        """Determine the type of relationship between two threads."""
        
        # Simple heuristics based on status and similarity
        if source_thread.status == PlotStatus.INTRODUCED and target_thread.status == PlotStatus.DEVELOPING:
            return "develops"
        elif source_thread.status == PlotStatus.DEVELOPING and target_thread.status == PlotStatus.RESOLVED:
            return "causes"
        elif similarity > 0.8:
            return "supports"
        elif similarity > 0.6:
            return "references"
        else:
            return "relates_to"
    
    def _generate_reminder_text(self, thread: PlotThread, days_stale: int) -> str:
        """Generate contextual reminder text for a stale thread."""
        
        urgency_text = ""
        if days_stale > 14:
            urgency_text = "This plot thread has been inactive for over two weeks. "
        elif days_stale > 7:
            urgency_text = "This plot thread hasn't been referenced in over a week. "
        
        importance_text = ""
        if thread.importance_score > 0.8:
            importance_text = "This is a high-importance plot thread that may need attention. "
        elif thread.importance_score > 0.6:
            importance_text = "This plot thread has moderate importance. "
        
        status_text = ""
        if thread.status == PlotStatus.INTRODUCED:
            status_text = "Consider developing this plot thread further or having characters react to it."
        elif thread.status == PlotStatus.DEVELOPING:
            status_text = "This ongoing plot thread may need progression or resolution."
        
        return f"{urgency_text}{importance_text}{status_text}".strip()
    
    def _suggest_plot_action(self, thread: PlotThread) -> str:
        """Suggest an action for a stale plot thread."""
        
        if thread.status == PlotStatus.INTRODUCED:
            return "Have characters discuss or react to this development"
        elif thread.status == PlotStatus.DEVELOPING:
            if thread.importance_score > 0.7:
                return "Consider advancing this important plot thread"
            else:
                return "Reference this thread or move toward resolution"
        else:
            return "Review thread status and consider if it needs attention"