import unittest
from unittest.mock import patch
from app import app

class TestFeatureFlagsAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    @patch('routes.storage.get_all')
    def test_get_flags_success(self, mock_get_all):
        """Verify GET /flags returns 200 and data."""
        mock_get_all.return_value = [{"name": "test", "enabled": True}]
        
        response = self.client.get('/flags?environment=staging')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]['name'], "test")

    def test_create_flag_missing_name(self):
        """Verify POST /flags returns 400 if name is missing."""
        response = self.client.post('/flags', json={"description": "no name"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)

    @patch('routes.storage.delete_one')
    def test_delete_flag_not_found(self, mock_delete):
        """Verify DELETE /flags/<id> returns 404 for non-existent IDs."""
        mock_delete.return_value = type('Result', (), {'deleted_count': 0})()
        
        response = self.client.delete('/flags/nonexistent-id')
        self.assertEqual(response.status_code, 404)