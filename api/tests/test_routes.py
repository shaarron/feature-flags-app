"""
Unit tests for Flask routes.
Uses module-level patching to prevent FeatureFlagStorage from attempting MongoDB connections.
"""
import sys
import unittest
from unittest.mock import patch, MagicMock

mock_storage_instance = MagicMock()

storage_patcher = patch('storage.FeatureFlagStorage', return_value=mock_storage_instance)
storage_patcher.start()

from api.app import app
from api import routes


class TestFeatureFlagsAPI(unittest.TestCase):
    """Test the Flask routes with mocked storage layer."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        app.config['TESTING'] = True

    def setUp(self):
        """Set up test client and reset mock before each test."""
        self.client = app.test_client()
        # Reset the mock storage state before each test
        mock_storage_instance.reset_mock()
        # Reset side_effect if set by previous tests
        mock_storage_instance.find_one.side_effect = None

    def test_get_flags_success(self):
        """Verify GET /flags returns 200 and data."""
        mock_storage_instance.get_all.return_value = [{"_id": "1", "name": "test", "enabled": True}]
        
        response = self.client.get('/flags?environment=staging')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]['name'], "test")

    def test_get_flags_default_environment(self):
        """Verify GET /flags uses 'staging' as default environment."""
        mock_storage_instance.get_all.return_value = []
        
        response = self.client.get('/flags')
        
        self.assertEqual(response.status_code, 200)
        mock_storage_instance.get_all.assert_called_with('staging')

    def test_create_flag_success(self):
        """Verify POST /flags creates a flag and returns 201."""
        flag_data = {"name": "new-flag", "description": "Test flag"}
        
        response = self.client.post('/flags', json=flag_data)
        
        self.assertEqual(response.status_code, 201)
        mock_storage_instance.insert_one.assert_called_once()

    def test_create_flag_missing_name(self):
        """Verify POST /flags returns 400 if name is missing."""
        response = self.client.post('/flags', json={"description": "no name"})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)

    def test_get_single_flag_success(self):
        """Verify GET /flags/<id> returns flag data."""
        mock_storage_instance.find_one.return_value = {"_id": "123", "name": "test-flag"}
        
        response = self.client.get('/flags/123')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "test-flag")

    def test_get_single_flag_not_found(self):
        """Verify GET /flags/<id> returns 404 for non-existent flags."""
        mock_storage_instance.find_one.return_value = None
        
        response = self.client.get('/flags/nonexistent')
        
        self.assertEqual(response.status_code, 404)

    def test_update_flag_success(self):
        """Verify PUT /flags/<id> updates and returns the flag."""
        mock_storage_instance.update_one.return_value = MagicMock(matched_count=1)
        mock_storage_instance.find_one.return_value = {"_id": "123", "name": "updated"}
        
        response = self.client.put('/flags/123', json={"name": "updated"})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "updated")

    def test_update_flag_no_fields(self):
        """Verify PUT /flags/<id> returns 400 if no fields provided."""
        response = self.client.put('/flags/123', json={})
        
        self.assertEqual(response.status_code, 400)

    def test_update_flag_not_found(self):
        """Verify PUT /flags/<id> returns 404 for non-existent flags."""
        mock_storage_instance.update_one.return_value = MagicMock(matched_count=0)
        
        response = self.client.put('/flags/nonexistent', json={"name": "test"})
        
        self.assertEqual(response.status_code, 404)

    def test_delete_flag_success(self):
        """Verify DELETE /flags/<id> returns 204 on success."""
        mock_storage_instance.delete_one.return_value = MagicMock(deleted_count=1)
        
        response = self.client.delete('/flags/123')
        
        self.assertEqual(response.status_code, 204)

    def test_delete_flag_not_found(self):
        """Verify DELETE /flags/<id> returns 404 for non-existent IDs."""
        mock_storage_instance.delete_one.return_value = MagicMock(deleted_count=0)
        
        response = self.client.delete('/flags/nonexistent-id')
        
        self.assertEqual(response.status_code, 404)

    def test_toggle_flag_success(self):
        """Verify POST /flags/<id>/toggle toggles the flag."""
        mock_storage_instance.find_one.side_effect = [
            {"_id": "123", "environments": {"production": False}},  # Initial state
            {"_id": "123", "environments": {"production": True}}     # After toggle
        ]
        mock_storage_instance.update_one.return_value = MagicMock(modified_count=1)
        
        response = self.client.post('/flags/123/toggle', json={"environment": "production"})
        
        self.assertEqual(response.status_code, 200)

    def test_toggle_flag_not_found(self):
        """Verify POST /flags/<id>/toggle returns 404 for non-existent flags."""
        mock_storage_instance.find_one.return_value = None
        
        response = self.client.post('/flags/nonexistent/toggle', json={"environment": "staging"})
        
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()