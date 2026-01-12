import unittest
from unittest.mock import MagicMock, patch
from api.storage import FeatureFlagStorage

class TestFeatureFlagStorage(unittest.TestCase):
    @patch('api.storage.MongoClient')
    def setUp(self, mock_client):
        # Mock the client -> db -> collection chain
        self.mock_client_instance = MagicMock()
        mock_client.return_value = self.mock_client_instance
        self.mock_db = self.mock_client_instance.feature_flags_db
        self.mock_collection = self.mock_db.flags
        
        # Initialize storage
        self.storage = FeatureFlagStorage()
        # Manually set the collection to bypass lazy loading _initialize_mongo in tests
        self.storage.collection = self.mock_collection

    def test_insert_and_find(self):
        """Verify that insert_one interacts correctly with the mocked collection."""
        flag = {"name": "test-flag", "environments": {"dev": True}}
        
        # Setup mock for insert_one
        mock_result = MagicMock()
        mock_result.inserted_id = 'mock-id-123'
        self.storage.collection.insert_one.return_value = mock_result
        
        # Execute
        result = self.storage.insert_one(flag)
        
        # Verify
        self.storage.collection.insert_one.assert_called_with(flag)
        self.assertEqual(flag['_id'], 'mock-id-123')

    def test_get_all_logic(self):
        """Ensure get_all retrieves from collection and filters by environment."""
        # Setup mock data associated with the cursor
        mock_data = [
            {"_id": "id1", "name": "f1", "environments": {"dev": True}},
            {"_id": "id2", "name": "f2", "environments": {"dev": False}}
        ]
        self.storage.collection.find.return_value = mock_data # find returns iterable
        
        # Execute
        found = self.storage.get_all(environment='dev')
        
        # Verify
        self.assertEqual(len(found), 2)
        self.assertTrue(found[0]['enabled'])
        self.assertFalse(found[1]['enabled'])