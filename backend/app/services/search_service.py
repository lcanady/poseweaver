"""
Search and indexing service for scene content.

This service provides full-text search capabilities and specialized search methods
for characters, plots, and environments within scenes.
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from ..models.scene import Scene, ScenePose, PoseType
from ..models.character import Character


@dataclass
class SearchResult:
    """Represents a search result with relevance information."""
    item_id: str
    item_type: str  # 'scene', 'pose', 'character', 'plot', 'environment'
    content_preview: str
    relevance_score: float
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary."""
        return {
            'item_id': self.item_id,
            'item_type': self.item_type,
            'content_preview': self.content_preview,
            'relevance_score': self.relevance_score,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class SearchService:
    """Service for searching and indexing scene content."""
    
    @staticmethod
    def search_scenes(
        query: str,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        skip: int = 0,
        sort_field: str = "relevance",
        sort_direction: int = -1
    ) -> List[SearchResult]:
        """Search for scenes matching the query.
        
        Args:
            query: Search query text
            user_id: ID of the user making the search
            filters: Optional filters to apply to search results
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            sort_field: Field to sort results by (relevance, timestamp, name)
            sort_direction: Sort direction (1 for ascending, -1 for descending)
            
        Returns:
            List of SearchResult objects
        """
        # Build search query
        search_query = {
            'created_by': user_id,
            'is_active': True
        }
        
        # Text search if query provided
        if query:
            search_query['$text'] = {'$search': query}
        
        # Apply additional filters
        if filters:
            # Handle date range filters
            if 'date_range' in filters:
                date_range = filters.pop('date_range')
                if 'start' in date_range:
                    search_query['created_at'] = {'$gte': date_range['start']}
                if 'end' in date_range:
                    if 'created_at' in search_query:
                        search_query['created_at']['$lte'] = date_range['end']
                    else:
                        search_query['created_at'] = {'$lte': date_range['end']}
            
            # Add remaining filters to query
            for key, value in filters.items():
                if key in ['participants', 'tags']:
                    search_query[key] = {'$in': value if isinstance(value, list) else [value]}
                else:
                    search_query[key] = value
        
        # Determine sort options
        sort_options = {}
        if sort_field == 'relevance' and query:
            sort_options['score'] = {'$meta': 'textScore'}
        elif sort_field in ['created_at', 'updated_at', 'name']:
            sort_options[sort_field] = sort_direction
        else:
            # Default to updated_at if invalid sort field
            sort_options['updated_at'] = sort_direction
        
        # Execute search
        scenes = Scene.find_all(
            query=search_query,
            projection={'score': {'$meta': 'textScore'}} if query else None,
            sort=sort_options,
            skip=skip,
            limit=limit
        )
        
        # Convert to search results
        results = []
        for scene in scenes:
            # Create content preview from scene description or recent poses
            preview = scene.description or ""
            if not preview and scene.poses:
                latest_pose = scene.poses[-1]
                preview = f"{latest_pose.character_name}: {latest_pose.pose_text[:100]}..."
            
            # Extract metadata
            metadata = {
                'name': scene.name,
                'description': scene.description,
                'participant_count': len(scene.participants),
                'pose_count': len(scene.poses),
                'created_by': scene.created_by,
                'created_at': scene.created_at.isoformat(),
                'updated_at': scene.updated_at.isoformat()
            }
            
            # Calculate relevance score
            score = getattr(scene, 'score', 1.0)
            
            results.append(SearchResult(
                item_id=scene.id,
                item_type='scene',
                content_preview=preview,
                relevance_score=score,
                timestamp=scene.updated_at,
                metadata=metadata
            ))
        
        return results
    
    @staticmethod
    def search_poses(
        query: str,
        scene_id: Optional[str] = None,
        user_id: Optional[str] = None,
        character_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        skip: int = 0
    ) -> List[SearchResult]:
        """Search for poses matching the query.
        
        Args:
            query: Search query text
            scene_id: Optional scene ID to limit search scope
            user_id: Optional user ID for access control
            character_id: Optional character ID to filter by character
            filters: Optional filters to apply to search results
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        # Build scene filters
        scene_filters = {}
        if user_id:
            scene_filters['created_by'] = user_id
        scene_filters['is_active'] = True
        
        # Limit to specific scene if requested
        if scene_id:
            scene = Scene.find_by_id(scene_id)
            if not scene or (user_id and scene.created_by != user_id):
                return []
            
            scenes = [scene]
        else:
            scenes = Scene.find_all(query=scene_filters)
        
        # Search poses across scenes
        for scene in scenes:
            for pose_idx, pose in enumerate(scene.poses):
                # Skip if not matching character filter
                if character_id and pose.character_id != character_id:
                    continue
                
                # Skip if doesn't match pose type filter
                if filters and 'pose_type' in filters and pose.pose_type.value != filters['pose_type']:
                    continue
                
                # Skip if doesn't match date range filter
                if filters and 'date_range' in filters:
                    pose_date = pose.timestamp or scene.updated_at
                    date_range = filters['date_range']
                    if 'start' in date_range and pose_date < date_range['start']:
                        continue
                    if 'end' in date_range and pose_date > date_range['end']:
                        continue
                
                # Apply text search
                pose_text = pose.pose_text or ""
                enhanced_text = pose.enhanced_text or ""
                combined_text = f"{pose_text} {enhanced_text}"
                
                if query and query.lower() not in combined_text.lower():
                    continue
                
                # Calculate relevance (simple contains-based score for now)
                score = 1.0
                if query:
                    # More sophisticated scoring could be implemented here
                    # For now, count occurrences for basic relevance
                    score = combined_text.lower().count(query.lower()) / len(combined_text.split())
                
                # Create metadata for this pose
                metadata = {
                    'scene_id': scene.id,
                    'scene_name': scene.name,
                    'pose_index': pose_idx,
                    'character_name': pose.character_name,
                    'character_id': pose.character_id,
                    'pose_type': pose.pose_type.value,
                    'tags': pose.tags or []
                }
                
                # Create preview (truncate if needed)
                preview = pose_text[:150] + "..." if len(pose_text) > 150 else pose_text
                
                results.append(SearchResult(
                    item_id=f"{scene.id}:{pose_idx}",
                    item_type='pose',
                    content_preview=preview,
                    relevance_score=score,
                    timestamp=pose.timestamp or scene.updated_at,
                    metadata=metadata
                ))
        
        # Sort by relevance and apply pagination
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        paginated_results = results[skip:skip+limit]
        
        return paginated_results
    
    @staticmethod
    def search_characters(
        query: str,
        scene_id: Optional[str] = None,
        user_id: str = None,
        limit: int = 10,
        skip: int = 0
    ) -> List[SearchResult]:
        """Search for characters matching the query.
        
        Args:
            query: Search query text
            scene_id: Optional scene ID to limit search to characters in that scene
            user_id: ID of the user making the search
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        # If scene ID is provided, get characters from that scene
        if scene_id:
            scene = Scene.find_by_id(scene_id)
            if not scene or (user_id and scene.created_by != user_id):
                return []
            
            # Get all characters from this scene
            character_ids = [p.character_id for p in scene.participants.values() if p.character_id]
            characters = [Character.find_by_id(char_id) for char_id in character_ids]
            characters = [c for c in characters if c]  # Filter out None values
        else:
            # Get all characters owned by the user
            characters = Character.find_all(query={'user_id': user_id})
        
        # Apply text search
        for character in characters:
            # Search in name, description, and traits
            searchable_text = f"{character.name} {character.description or ''}"
            if hasattr(character, 'traits'):
                for trait_name, trait_value in character.traits.items():
                    searchable_text += f" {trait_name}: {trait_value}"
            
            # Skip if doesn't match query
            if query and query.lower() not in searchable_text.lower():
                continue
            
            # Calculate relevance score
            score = 1.0
            if query:
                # More sophisticated scoring could be implemented here
                score = searchable_text.lower().count(query.lower()) / len(searchable_text.split())
            
            # Create preview
            preview = character.description[:150] + "..." if character.description and len(character.description) > 150 else (character.description or "No description")
            
            # Extract metadata
            metadata = {
                'name': character.name,
                'user_id': character.user_id,
                'is_active': getattr(character, 'is_active', True),
                'traits': getattr(character, 'traits', {})
            }
            
            results.append(SearchResult(
                item_id=character.id,
                item_type='character',
                content_preview=preview,
                relevance_score=score,
                timestamp=character.updated_at if hasattr(character, 'updated_at') else datetime.utcnow(),
                metadata=metadata
            ))
        
        # Sort by relevance and apply pagination
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        paginated_results = results[skip:skip+limit]
        
        return paginated_results
    
    @staticmethod
    def search_plot_elements(
        query: str,
        scene_id: str,
        user_id: str,
        limit: int = 10,
        skip: int = 0
    ) -> List[SearchResult]:
        """Search for plot elements matching the query within a scene.
        
        Args:
            query: Search query text
            scene_id: ID of the scene to search within
            user_id: ID of the user making the search
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        # Get the scene
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return []
        
        # Check if scene has plot elements in its context
        plot_elements = scene.context.get('plot_elements', []) if hasattr(scene, 'context') else []
        
        # Search through plot elements
        for element in plot_elements:
            if not isinstance(element, dict):
                continue
                
            # Extract searchable text from plot element
            element_text = f"{element.get('title', '')} {element.get('description', '')}"
            for tag in element.get('tags', []):
                element_text += f" {tag}"
            
            # Skip if doesn't match query
            if query and query.lower() not in element_text.lower():
                continue
            
            # Calculate relevance score
            score = 1.0
            if query:
                # Basic relevance scoring
                score = element_text.lower().count(query.lower()) / len(element_text.split())
            
            # Create preview
            preview = element.get('description', '')[:150]
            if len(element.get('description', '')) > 150:
                preview += "..."
            
            # Extract metadata
            metadata = {
                'title': element.get('title', 'Untitled Plot Element'),
                'tags': element.get('tags', []),
                'created_at': element.get('created_at', scene.updated_at.isoformat()),
                'scene_id': scene_id,
                'scene_name': scene.name
            }
            
            # Generate a stable ID for this plot element
            element_id = element.get('id', f"plot:{scene_id}:{element.get('title', '')}")
            
            results.append(SearchResult(
                item_id=element_id,
                item_type='plot',
                content_preview=preview,
                relevance_score=score,
                timestamp=datetime.fromisoformat(metadata['created_at']) if isinstance(metadata['created_at'], str) else metadata['created_at'],
                metadata=metadata
            ))
        
        # Sort by relevance and apply pagination
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        paginated_results = results[skip:skip+limit]
        
        return paginated_results
    
    @staticmethod
    def search_environment_details(
        query: str,
        scene_id: str,
        user_id: str,
        limit: int = 10,
        skip: int = 0
    ) -> List[SearchResult]:
        """Search for environment details matching the query within a scene.
        
        Args:
            query: Search query text
            scene_id: ID of the scene to search within
            user_id: ID of the user making the search
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        # Get the scene
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return []
        
        # Check if scene has environment details in its context
        env_details = scene.context.get('environment_details', []) if hasattr(scene, 'context') else []
        
        # Search through environment details
        for detail in env_details:
            if not isinstance(detail, dict):
                continue
                
            # Extract searchable text from environment detail
            detail_text = f"{detail.get('name', '')} {detail.get('description', '')}"
            for tag in detail.get('tags', []):
                detail_text += f" {tag}"
            
            # Skip if doesn't match query
            if query and query.lower() not in detail_text.lower():
                continue
            
            # Calculate relevance score
            score = 1.0
            if query:
                # Basic relevance scoring
                score = detail_text.lower().count(query.lower()) / len(detail_text.split())
            
            # Create preview
            preview = detail.get('description', '')[:150]
            if len(detail.get('description', '')) > 150:
                preview += "..."
            
            # Extract metadata
            metadata = {
                'name': detail.get('name', 'Unnamed Environment Detail'),
                'tags': detail.get('tags', []),
                'created_at': detail.get('created_at', scene.updated_at.isoformat()),
                'scene_id': scene_id,
                'scene_name': scene.name
            }
            
            # Generate a stable ID for this environment detail
            detail_id = detail.get('id', f"env:{scene_id}:{detail.get('name', '')}")
            
            results.append(SearchResult(
                item_id=detail_id,
                item_type='environment',
                content_preview=preview,
                relevance_score=score,
                timestamp=datetime.fromisoformat(metadata['created_at']) if isinstance(metadata['created_at'], str) else metadata['created_at'],
                metadata=metadata
            ))
        
        # Sort by relevance and apply pagination
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        paginated_results = results[skip:skip+limit]
        
        return paginated_results
    
    @staticmethod
    def timeline_search(
        scene_id: str,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        character_id: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for timeline events within a date range.
        
        Args:
            scene_id: ID of the scene to search within
            user_id: ID of the user making the search
            start_date: Optional start date for timeline range
            end_date: Optional end date for timeline range
            character_id: Optional character ID to filter by
            query: Optional text query to filter events
            limit: Maximum number of events to return
            
        Returns:
            List of timeline events with metadata
        """
        # Get the scene
        scene = Scene.find_by_id(scene_id)
        if not scene or scene.created_by != user_id:
            return []
        
        timeline_events = []
        
        # Process poses as timeline events
        for pose_idx, pose in enumerate(scene.poses):
            # Skip if character filter is applied and doesn't match
            if character_id and pose.character_id != character_id:
                continue
            
            # Get timestamp for this pose
            pose_timestamp = pose.timestamp or scene.created_at
            
            # Skip if outside date range
            if start_date and pose_timestamp < start_date:
                continue
            if end_date and pose_timestamp > end_date:
                continue
            
            # Skip if doesn't match text query
            pose_text = pose.pose_text or ""
            enhanced_text = pose.enhanced_text or ""
            if query and query.lower() not in pose_text.lower() and query.lower() not in enhanced_text.lower():
                continue
            
            # Create timeline event
            timeline_events.append({
                'id': f"{scene.id}:pose:{pose_idx}",
                'type': 'pose',
                'timestamp': pose_timestamp.isoformat(),
                'title': f"{pose.character_name}'s {pose.pose_type.value}",
                'content': pose.pose_text,
                'character_id': pose.character_id,
                'character_name': pose.character_name,
                'tags': pose.tags or []
            })
        
        # Add plot events from scene context if available
        if hasattr(scene, 'context') and scene.context.get('plot_events'):
            for event_idx, event in enumerate(scene.context['plot_events']):
                if not isinstance(event, dict):
                    continue
                
                # Get timestamp for this event
                try:
                    event_timestamp = datetime.fromisoformat(event.get('timestamp')) if isinstance(event.get('timestamp'), str) else event.get('timestamp')
                    if not event_timestamp:
                        event_timestamp = scene.created_at
                except (ValueError, TypeError):
                    event_timestamp = scene.created_at
                
                # Skip if outside date range
                if start_date and event_timestamp < start_date:
                    continue
                if end_date and event_timestamp > end_date:
                    continue
                
                # Skip if doesn't match character filter
                event_character_id = event.get('character_id')
                if character_id and event_character_id != character_id:
                    continue
                
                # Skip if doesn't match text query
                event_text = f"{event.get('title', '')} {event.get('description', '')}"
                if query and query.lower() not in event_text.lower():
                    continue
                
                # Create timeline event
                timeline_events.append({
                    'id': event.get('id', f"{scene.id}:plot:{event_idx}"),
                    'type': 'plot_event',
                    'timestamp': event_timestamp.isoformat(),
                    'title': event.get('title', 'Untitled Plot Event'),
                    'content': event.get('description', ''),
                    'character_id': event.get('character_id'),
                    'character_name': event.get('character_name'),
                    'tags': event.get('tags', [])
                })
        
        # Sort by timestamp and limit results
        timeline_events.sort(key=lambda x: x['timestamp'])
        limited_events = timeline_events[:limit] if len(timeline_events) > limit else timeline_events
        
        return limited_events
    
    @staticmethod
    def create_search_index(collection_name: str) -> bool:
        """Create search indexes for the specified collection.
        
        Args:
            collection_name: Name of the collection to index
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if collection_name == 'scenes':
                # Create text index on name, description and pose content
                Scene.create_index([
                    ('name', 'text'),
                    ('description', 'text'),
                    ('poses.pose_text', 'text'),
                    ('poses.enhanced_text', 'text')
                ])
                
                # Create additional indexes for common query patterns
                Scene.create_index('created_by')
                Scene.create_index('participants.character_id')
                Scene.create_index('updated_at')
                Scene.create_index('is_active')
                
            elif collection_name == 'characters':
                # Create text index on character fields
                Character.create_index([
                    ('name', 'text'),
                    ('description', 'text')
                ])
                
                # Create additional indexes
                Character.create_index('user_id')
            
            return True
            
        except Exception as e:
            # Log the error
            print(f"Error creating search index for {collection_name}: {str(e)}")
            return False
