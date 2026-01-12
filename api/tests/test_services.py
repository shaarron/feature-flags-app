import unittest
from unittest.mock import patch, MagicMock
from api.feature_flag_service import FeatureFlagService

class TestFeatureFlagService(unittest.TestCase):
    @patch('api.feature_flag_service.FeatureFlagStorage')
    def setUp(self, MockStorage):
        self.mock_storage_instance = MockStorage.return_value
        self.service = FeatureFlagService()
        # Ensure the service uses the mock instance
        self.service.storage = self.mock_storage_instance

    def test_get_all_flags(self):
        self.mock_storage_instance.get_all.return_value = [{'name': 'flag1'}]
        result = self.service.get_all_flags('staging')
        self.assertEqual(result, [{'name': 'flag1'}])
        self.mock_storage_instance.get_all.assert_called_with('staging')

    def test_create_flag(self):
        data = {'name': 'new_flag'}
        self.mock_storage_instance.insert_one.return_value = 'some_result'
        result = self.service.create_flag(data)
        self.assertEqual(result, data)
        self.mock_storage_instance.insert_one.assert_called_with(data)

    def test_get_flag_found(self):
        self.mock_storage_instance.find_one.return_value = {'_id': '123', 'name': 'flag1'}
        result = self.service.get_flag('123')
        self.assertEqual(result['name'], 'flag1')
        self.assertEqual(result['_id'], '123')

    def test_get_flag_not_found(self):
        self.mock_storage_instance.find_one.return_value = None
        result = self.service.get_flag('unknown')
        self.assertIsNone(result)

    def test_update_flag_success(self):
        self.mock_storage_instance.update_one.return_value = MagicMock(matched_count=1)
        self.mock_storage_instance.find_one.return_value = {'_id': '123', 'name': 'updated'}
        
        flag, error = self.service.update_flag('123', {'name': 'updated'})
        self.assertIsNone(error)
        self.assertEqual(flag['name'], 'updated')

    def test_update_flag_no_fields(self):
        flag, error = self.service.update_flag('123', {})
        self.assertEqual(error, "No fields to update")

    def test_delete_flag(self):
        self.mock_storage_instance.delete_one.return_value = MagicMock(deleted_count=1)
        success = self.service.delete_flag('123')
        self.assertTrue(success)

    def test_toggle_flag(self):
        # Setup initial state: enabled=False
        self.mock_storage_instance.find_one.side_effect = [
            {'_id': '123', 'environments': {'staging': False}}, # First find (check existence)
            {'_id': '123', 'enabled': True, 'environments': {'staging': True}} # Second find (return updated)
        ]
        self.mock_storage_instance.update_one.return_value = MagicMock(modified_count=1)

        result = self.service.toggle_flag('123', 'staging')
        self.assertTrue(result['enabled'])
        
        # Verify update was called with negation of current status
        args = self.mock_storage_instance.update_one.call_args
        self.assertEqual(args[0][1]['$set']['environments.staging'], True)
