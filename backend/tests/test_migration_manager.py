"""
Unit tests for MongoDB Migration Manager.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app.migrations.migration_manager import MigrationManager


class TestMigrationManager:
    """Test cases for MigrationManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MigrationManager()
    
    def test_get_applied_migrations(self):
        """Test getting applied migrations."""
        mock_migrations = [
            {'name': 'migration1', 'applied_at': datetime.utcnow()},
            {'name': 'migration2', 'applied_at': datetime.utcnow()}
        ]
        self.manager.mongodb.find_many = Mock(return_value=mock_migrations)
        
        result = self.manager.get_applied_migrations()
        
        self.manager.mongodb.find_many.assert_called_once_with(
            'migrations',
            sort=[('applied_at', 1)]
        )
        assert result == ['migration1', 'migration2']
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_get_applied_migrations_error(self, mock_get_mongodb):
        """Test getting applied migrations with error."""
        mock_mongodb = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.find_many.side_effect = Exception("Database error")
        
        result = self.manager.get_applied_migrations()
        
        assert result == []
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_mark_migration_applied(self, mock_get_mongodb):
        """Test marking migration as applied."""
        mock_mongodb = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.insert_one.return_value = "migration_id"
        
        self.manager.mark_migration_applied("test_migration")
        
        # Verify insert_one was called with correct structure
        call_args = mock_mongodb.insert_one.call_args
        assert call_args[0][0] == 'migrations'
        migration_record = call_args[0][1]
        assert migration_record['name'] == 'test_migration'
        assert 'applied_at' in migration_record
        assert migration_record['version'] == '1.0.0'
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_run_migration_success(self, mock_get_mongodb):
        """Test running a migration successfully."""
        mock_mongodb = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.find_many.return_value = []  # No applied migrations
        mock_mongodb.insert_one.return_value = "migration_id"
        
        # Mock migration function
        mock_migration_func = Mock()
        
        result = self.manager.run_migration("test_migration", mock_migration_func)
        
        assert result is True
        mock_migration_func.assert_called_once()
        mock_mongodb.insert_one.assert_called_once()
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_run_migration_already_applied(self, mock_get_mongodb):
        """Test running a migration that's already applied."""
        mock_mongodb = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.find_many.return_value = [
            {'name': 'test_migration', 'applied_at': datetime.utcnow()}
        ]
        
        mock_migration_func = Mock()
        
        result = self.manager.run_migration("test_migration", mock_migration_func)
        
        assert result is True
        mock_migration_func.assert_not_called()
        mock_mongodb.insert_one.assert_not_called()
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_run_migration_failure(self, mock_get_mongodb):
        """Test running a migration that fails."""
        mock_mongodb = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.find_many.return_value = []  # No applied migrations
        
        # Mock migration function that raises an exception
        mock_migration_func = Mock(side_effect=Exception("Migration failed"))
        
        result = self.manager.run_migration("test_migration", mock_migration_func)
        
        assert result is False
        mock_migration_func.assert_called_once()
        mock_mongodb.insert_one.assert_not_called()
    
    @patch.object(MigrationManager, 'run_migration')
    def test_run_all_migrations_success(self, mock_run_migration):
        """Test running all migrations successfully."""
        mock_run_migration.return_value = True
        
        result = self.manager.run_all_migrations()
        
        assert result is True
        # Should call run_migration for each migration
        assert mock_run_migration.call_count == 6
    
    @patch.object(MigrationManager, 'run_migration')
    def test_run_all_migrations_failure(self, mock_run_migration):
        """Test running all migrations with one failure."""
        # First migration succeeds, second fails
        mock_run_migration.side_effect = [True, False]
        
        result = self.manager.run_all_migrations()
        
        assert result is False
        # Should stop after first failure
        assert mock_run_migration.call_count == 2
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_create_scene_memory_indexes(self, mock_get_mongodb):
        """Test creating scene memory indexes."""
        mock_mongodb = Mock()
        mock_collection = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.get_collection.return_value = mock_collection
        
        self.manager._create_scene_memory_indexes()
        
        # Verify single field indexes were created
        assert mock_mongodb.create_index.call_count >= 5
        # Verify compound indexes were created
        assert mock_collection.create_index.call_count >= 3
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_create_pose_indexes(self, mock_get_mongodb):
        """Test creating pose indexes."""
        mock_mongodb = Mock()
        mock_collection = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.get_collection.return_value = mock_collection
        
        self.manager._create_pose_indexes()
        
        # Verify indexes were created including text search
        assert mock_mongodb.create_index.call_count >= 6
        assert mock_collection.create_index.call_count >= 5
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_create_character_state_indexes(self, mock_get_mongodb):
        """Test creating character state indexes."""
        mock_mongodb = Mock()
        mock_collection = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.get_collection.return_value = mock_collection
        
        self.manager._create_character_state_indexes()
        
        # Verify indexes were created including unique compound index
        assert mock_mongodb.create_index.call_count >= 3
        assert mock_collection.create_index.call_count >= 1
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_create_environment_state_indexes(self, mock_get_mongodb):
        """Test creating environment state indexes."""
        mock_mongodb = Mock()
        mock_collection = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.get_collection.return_value = mock_collection
        
        self.manager._create_environment_state_indexes()
        
        # Verify indexes were created
        assert mock_mongodb.create_index.call_count >= 3
        assert mock_collection.create_index.call_count >= 2
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_create_plot_thread_indexes(self, mock_get_mongodb):
        """Test creating plot thread indexes."""
        mock_mongodb = Mock()
        mock_collection = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.get_collection.return_value = mock_collection
        
        self.manager._create_plot_thread_indexes()
        
        # Verify indexes were created including text search
        assert mock_mongodb.create_index.call_count >= 4
        assert mock_collection.create_index.call_count >= 3
    
    @patch('app.migrations.migration_manager.get_mongodb_service')
    def test_create_continuity_flag_indexes(self, mock_get_mongodb):
        """Test creating continuity flag indexes."""
        mock_mongodb = Mock()
        mock_collection = Mock()
        mock_get_mongodb.return_value = mock_mongodb
        mock_mongodb.get_collection.return_value = mock_collection
        
        self.manager._create_continuity_flag_indexes()
        
        # Verify indexes were created
        assert mock_mongodb.create_index.call_count >= 5
        assert mock_collection.create_index.call_count >= 3


@patch('app.migrations.migration_manager.MigrationManager')
def test_run_migrations_function(mock_manager_class):
    """Test the run_migrations function."""
    from app.migrations.migration_manager import run_migrations
    
    mock_manager = Mock()
    mock_manager_class.return_value = mock_manager
    mock_manager.run_all_migrations.return_value = True
    
    result = run_migrations()
    
    assert result is True
    mock_manager.run_all_migrations.assert_called_once()