import pytest
from unittest.mock import patch
from unittest.mock import MagicMock
from app import app
from bson.objectid import ObjectId

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

### Test get feature flags
@patch('app.feature_flags_collection.find') 
def test_get_flags_unit(mock_find, client):
    mock_find.return_value = [
        {
            "_id": "123", 
            "name": "test-flag", 
            "environments": {"staging": True}
        }
    ]

    response = client.get('/flags?environment=staging')

    assert response.status_code == 200
    assert response.json[0]['name'] == "test-flag"
    assert response.json[0]['enabled'] is True

### Test create feature flag
@patch('app.feature_flags_collection.insert_one')
def test_create_flag_unit(mock_insert, client):
    # Mock the return object of MongoDB's insert_one
    mock_result = MagicMock()
    mock_result.inserted_id = "mocked_guid_123"
    mock_insert.return_value = mock_result

    # Send a POST request with JSON data
    new_flag = {
        "name": "new-feature",
        "description": "A test feature",
        "environments": {"production": True}
    }
    response = client.post('/flags', json=new_flag)

    assert response.status_code == 201
    assert response.json['name'] == "new-feature"
    assert response.json['_id'] == "mocked_guid_123"
    
    # Verify the database was actually called once
    mock_insert.assert_called_once()

### Toggle Logic Test
@patch('app.storage.mongo_available', False)
@patch('app.feature_flags_collection.find_one')
@patch('app.feature_flags_collection.update_one')
def test_toggle_flag_unit(mock_update, mock_find, client):
    # Mock finding an existing 'enabled' flag
    mock_find.return_value = {
        "_id": "123", 
        "environments": {"staging": True}
    }
    mock_update.return_value = MagicMock(modified_count=1)

    response = client.post('/flags/123/toggle', json={"environment": "staging"})

    assert response.status_code == 200
    mock_update.assert_called_once_with(
        {"_id": "123"}, 
        {"$set": {"environments.staging": False}} # Verifies the flip logic
    )

###  Test deletion when MongoDB is available 
@patch('app.storage.mongo_available', True) # Force the production path
@patch('app.feature_flags_collection.delete_one')
def test_delete_flag_unit_mongo(mock_delete, client):
    # Mock a successful deletion 
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_delete.return_value = mock_result
    
    test_id = "507f1f77bcf86cd799439011" # A valid-looking MongoDB ID

    response = client.delete(f'/flags/{test_id}')
    
    assert response.status_code == 204
    mock_delete.assert_called_once_with({"_id": ObjectId(test_id)})


###  Test deletion when MongoDB is unavailable
@patch('app.storage.mongo_available', False) # Force the fallback path
@patch('app.feature_flags_collection.delete_one')
def test_delete_flag_unit_fallback(mock_delete, client):
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_delete.return_value = mock_result
    
    test_id = "12345"

    response = client.delete(f'/flags/{test_id}')
    
    assert response.status_code == 204
    mock_delete.assert_called_once_with({"_id": test_id})
