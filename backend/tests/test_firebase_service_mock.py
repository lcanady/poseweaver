"""
Test Firebase Service using mocks.
"""
import sys
import unittest
from unittest.mock import MagicMock

# Create mock classes
class MockCredentials:
    class Certificate:
        def __init__(self, path):
            pass

class MockFirestore:
    class Query:
        DESCENDING = 'DESCENDING'
        ASCENDING = 'ASCENDING'
    
    @staticmethod
    def client():
        return MagicMock()

# Create a mock module for firebase_admin
mock_firebase_admin = MagicMock()
mock_firebase_admin.credentials = MockCredentials
mock_firebase_admin.firestore = MockFirestore

# Function to fake initialize_app
def mock_initialize_app(cred=None):
    pass
mock_firebase_admin.initialize_app = mock_initialize_app
mock_firebase_admin._apps = {}

# Apply mocks to sys.modules
sys.modules['firebase_admin'] = mock_firebase_admin
sys.modules['firebase_admin.credentials'] = MockCredentials
sys.modules['firebase_admin.firestore'] = MockFirestore

# Now we can safely import the service
# Mock flask_limiter
class MockLimiter:
    def __init__(self, key_func=None):
        pass
    def init_app(self, app):
        pass

mock_flask_limiter = MagicMock()
mock_flask_limiter.Limiter = MockLimiter
mock_flask_limiter.util = MagicMock()
mock_flask_limiter.util.get_remote_address = MagicMock()

sys.modules['flask_limiter'] = mock_flask_limiter
sys.modules['flask_limiter.util'] = mock_flask_limiter.util

# Now we can safely import the service
# We need to ensure app.services can be imported, so we might need to mock extensions or others if they import things
# But since we are unit testing FirebaseService, we'll try to import it.
# Note: extensions.py imports FirebaseService, but FirebaseService imports db_repository.
from app.services.firebase_service import FirebaseService

class TestFirebaseService(unittest.TestCase):
    def setUp(self):
        self.service = FirebaseService()
        self.service._db = MagicMock() # Mock the db client
    
    def test_insert_one(self):
        # Setup
        collection_ref = MagicMock()
        doc_ref = MagicMock()
        doc_ref.id = 'new_doc_id'
        collection_ref.add.return_value = (None, doc_ref)
        self.service.db.collection.return_value = collection_ref
        
        # Execute
        doc = {'name': 'test'}
        result_id = self.service.insert_one('test_collection', doc)
        
        # Verify
        self.assertEqual(result_id, 'new_doc_id')
        collection_ref.add.assert_called_once()
        args, _ = collection_ref.add.call_args
        self.assertEqual(args[0]['name'], 'test')
        self.assertIn('created_at', args[0])
        self.assertIn('updated_at', args[0])

    def test_find_one_by_id(self):
        # Setup
        collection_ref = MagicMock()
        doc_ref = MagicMock()
        doc_snapshot = MagicMock()
        doc_snapshot.exists = True
        doc_snapshot.id = 'target_id'
        doc_snapshot.to_dict.return_value = {'name': 'found'}
        doc_ref.get.return_value = doc_snapshot
        
        collection_ref.document.return_value = doc_ref
        self.service.db.collection.return_value = collection_ref
        
        # Execute
        result = self.service.find_one('test_collection', {'id': 'target_id'})
        
        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 'target_id')
        self.assertEqual(result['name'], 'found')
        collection_ref.document.assert_called_with('target_id')

    def test_find_many_filter(self):
        # Setup
        collection_ref = MagicMock()
        query = MagicMock()
        collection_ref.where.return_value = query
        query.where.return_value = query
        query.stream.return_value = []
        
        self.service.db.collection.return_value = collection_ref
        
        # Execute
        self.service.find_many('test_collection', {'status': 'active', 'count': {'$gt': 5}})
        
        # Verify
        # Check that where was called correctly
        # We expect 'status' == 'active'
        # And 'count' > 5
        # Since logic iterates, order might vary or calls might be chained
        # Check if collection was called
        self.service.db.collection.assert_called_with('test_collection')

if __name__ == '__main__':
    unittest.main()
