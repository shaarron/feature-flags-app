import unittest
from unittest.mock import MagicMock, patch
from storage import FeatureFlagStorage

class TestFeatureFlagStorage(unittest.TestCase):
    @patch('storage.MongoClient')
    def setUp(self, mock_client):
        # Force fallback to in-memory storage for consistent unit tests
        mock_client.side_effect = Exception("Conn failed")
        self.storage = FeatureFlagStorage()

    def test_insert_and_find_fallback(self):
        """Verify that data is correctly stored and retrieved in fallback mode."""
        flag = {"name": "test-flag", "environments": {"dev": True}}
        result = self.storage.insert_one(flag)
        
        # Check if ID was generated
        self.assertIsNotNone(flag.get('_id'))
        
        # Retrieve and verify
        found = self.storage.get_all(environment='dev')
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0]['enabled'])

    def test_toggle_logic(self):
        """Ensure get_all correctly calculates the 'enabled' field based on environment."""
        flag = {
            "name": "toggle-me",
            "environments": {"dev": True, "prod": False}
        }
        self.storage.insert_one(flag)
        
        dev_flags = self.storage.get_all(environment='dev')
        prod_flags = self.storage.get_all(environment='prod')
        
        self.assertTrue(dev_flags[0]['enabled'])
        self.assertFalse(prod_flags[0]['enabled'])