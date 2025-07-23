"""
MongoDB Migration Manager for Scene Memory & Continuity Tracking.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
from ..services.mongodb_service import get_mongodb_service

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages MongoDB migrations for scene memory models."""
    
    MIGRATION_COLLECTION = 'migrations'
    
    def __init__(self):
        self.mongodb = get_mongodb_service()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names."""
        try:
            migrations = self.mongodb.find_many(
                self.MIGRATION_COLLECTION,
                sort=[('applied_at', 1)]
            )
            return [m['name'] for m in migrations]
        except Exception as e:
            logger.warning(f"Could not retrieve applied migrations: {e}")
            return []
    
    def mark_migration_applied(self, migration_name: str) -> None:
        """Mark a migration as applied."""
        migration_record = {
            'name': migration_name,
            'applied_at': datetime.utcnow(),
            'version': '1.0.0'
        }
        self.mongodb.insert_one(self.MIGRATION_COLLECTION, migration_record)
        logger.info(f"Marked migration '{migration_name}' as applied")
    
    def run_migration(self, migration_name: str, migration_func) -> bool:
        """Run a single migration if not already applied."""
        applied_migrations = self.get_applied_migrations()
        
        if migration_name in applied_migrations:
            logger.info(f"Migration '{migration_name}' already applied, skipping")
            return True
        
        try:
            logger.info(f"Running migration: {migration_name}")
            migration_func()
            self.mark_migration_applied(migration_name)
            logger.info(f"Successfully applied migration: {migration_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply migration '{migration_name}': {e}")
            return False
    
    def run_all_migrations(self) -> bool:
        """Run all pending migrations."""
        migrations = [
            ('001_create_scene_memory_indexes', self._create_scene_memory_indexes),
            ('002_create_pose_indexes', self._create_pose_indexes),
            ('003_create_character_state_indexes', self._create_character_state_indexes),
            ('004_create_environment_state_indexes', self._create_environment_state_indexes),
            ('005_create_plot_thread_indexes', self._create_plot_thread_indexes),
            ('006_create_continuity_flag_indexes', self._create_continuity_flag_indexes),
        ]
        
        success = True
        for migration_name, migration_func in migrations:
            if not self.run_migration(migration_name, migration_func):
                success = False
                break
        
        return success
    
    def _create_scene_memory_indexes(self) -> None:
        """Create indexes for scene_memory collection."""
        collection_name = 'scene_memory'
        
        # Single field indexes
        self.mongodb.create_index(collection_name, 'owner_id')
        self.mongodb.create_index(collection_name, 'status')
        self.mongodb.create_index(collection_name, 'last_activity')
        self.mongodb.create_index(collection_name, 'created_at')
        self.mongodb.create_index(collection_name, 'updated_at')
        
        # Compound indexes for common queries
        self.mongodb.get_collection(collection_name).create_index([
            ('owner_id', 1), ('status', 1)
        ])
        self.mongodb.get_collection(collection_name).create_index([
            ('owner_id', 1), ('last_activity', -1)
        ])
        self.mongodb.get_collection(collection_name).create_index([
            ('status', 1), ('last_activity', -1)
        ])
        
        logger.info("Created indexes for scene_memory collection")
    
    def _create_pose_indexes(self) -> None:
        """Create indexes for poses collection."""
        collection_name = 'poses'
        
        # Single field indexes
        self.mongodb.create_index(collection_name, 'scene_id')
        self.mongodb.create_index(collection_name, 'character_name')
        self.mongodb.create_index(collection_name, 'timestamp')
        self.mongodb.create_index(collection_name, 'pose_type')
        self.mongodb.create_index(collection_name, 'is_ooc')
        self.mongodb.create_index(collection_name, 'created_at')
        
        # Compound indexes for common queries
        self.mongodb.get_collection(collection_name).create_index([
            ('scene_id', 1), ('timestamp', 1)
        ])
        self.mongodb.get_collection(collection_name).create_index([
            ('scene_id', 1), ('character_name', 1)
        ])
        self.mongodb.get_collection(collection_name).create_index([
            ('character_name', 1), ('timestamp', 1)
        ])
        self.mongodb.get_collection(collection_name).create_index([
            ('scene_id', 1), ('pose_type', 1)
        ])
        
        # Text index for content search
        self.mongodb.get_collection(collection_name).create_index([
            ('content', 'text')
        ])
        
        logger.info("Created indexes for poses collection")
    
    def _create_character_state_indexes(self) -> None:
        """Create indexes for character_states collection."""
        collection_name = 'character_states'
        
        # Single field indexes
        self.mongodb.create_index(collection_name, 'scene_id')
        self.mongodb.create_index(collection_name, 'character_name')
        self.mongodb.create_index(collection_name, 'updated_at')
        
        # Compound indexes
        self.mongodb.get_collection(collection_name).create_index([
            ('scene_id', 1), ('character_name', 1)
        ], unique=True)
        
        logger.info("Created indexes for character_states collection")
    
    def _create_environment_state_indexes(self) -> None:
        """Create indexes for environment_states collection."""
        collection_name = 'environment_states'
        
        # Single field indexes
        self.mongodb.create_index(collection_name, 'scene_id')
        self.mongodb.create_index(collection_name, 'location_name')
        self.mongodb.create_index(collection_name, 'established_at')
        
        # Compound indexes
        self.mongodb.get_collection(collection_name).create_index([
            ('scene_id', 1), ('established_at', 1)
        ])
        self.mongodb.get_collection(collection_name).create_index([
            ('scene_id', 1), ('location_name', 1)
        ])
        
        logger.info("Created indexes for environment_states collection")
    
    def _create_plot_thread_indexes(self) -> None:
        """Create indexes for plot_threads collection."""
        collection_name = 'plot_threads'
        
        # Single field indexes
        self.mongodb.create_index(collection_name, 'scene_id')
        self.mongodb.create_index(collection_name, 'status')
        self.mongodb.create_index(collection_name, 'last_referenced')
        self.mongodb.create_index(collection_name, 'introduced_at')
        
        # Compound indexes
        self.mongodb.get_collection(collection_name).create_index([
            ('scene_id', 1), ('status', 1)
        ])
        self.mongodb.get_collection(collection_name).create_index([
            ('scene_id', 1), ('last_referenced', -1)
        ])
        
        # Text index for title and description search
        self.mongodb.get_collection(collection_name).create_index([
            ('title', 'text'), ('description', 'text')
        ])
        
        logger.info("Created indexes for plot_threads collection")
    
    def _create_continuity_flag_indexes(self) -> None:
        """Create indexes for continuity_flags collection."""
        collection_name = 'continuity_flags'
        
        # Single field indexes
        self.mongodb.create_index(collection_name, 'pose_id')
        self.mongodb.create_index(collection_name, 'flag_type')
        self.mongodb.create_index(collection_name, 'severity')
        self.mongodb.create_index(collection_name, 'resolved')
        self.mongodb.create_index(collection_name, 'created_at')
        
        # Compound indexes
        self.mongodb.get_collection(collection_name).create_index([
            ('pose_id', 1), ('resolved', 1)
        ])
        self.mongodb.get_collection(collection_name).create_index([
            ('resolved', 1), ('severity', 1)
        ])
        self.mongodb.get_collection(collection_name).create_index([
            ('flag_type', 1), ('resolved', 1)
        ])
        
        logger.info("Created indexes for continuity_flags collection")


def run_migrations() -> bool:
    """Run all pending migrations."""
    manager = MigrationManager()
    return manager.run_all_migrations()