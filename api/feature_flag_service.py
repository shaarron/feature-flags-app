from storage import FeatureFlagStorage
from bson.objectid import ObjectId

class FeatureFlagService:
    def __init__(self):
        self.storage = FeatureFlagStorage()

    def get_all_flags(self, environment='staging'):
        return self.storage.get_all(environment)

    def create_flag(self, data):
        # Validation can go here if needed, but for now just proxy
        self.storage.insert_one(data)
        return data

    def get_flag(self, flag_id):
        query = self._build_id_query(flag_id)
        flag = self.storage.find_one(query)
        if flag:
            flag['_id'] = str(flag['_id'])
        return flag

    def update_flag(self, flag_id, updates):
        if not updates:
            return None, "No fields to update"
            
        query = self._build_id_query(flag_id)
        result = self.storage.update_one(query, {"$set": updates})
        
        if result.matched_count:
            flag = self.storage.find_one(query)
            if flag:
                flag['_id'] = str(flag['_id'])
            return flag, None
        return None, "Feature flag not found"

    def delete_flag(self, flag_id):
        query = self._build_id_query(flag_id)
        result = self.storage.delete_one(query)
        return result.deleted_count > 0

    def toggle_flag(self, flag_id, environment):
        query = self._build_id_query(flag_id)
        flag = self.storage.find_one(query)
        
        if flag:
            current_status = flag.get('environments', {}).get(environment, False)
            new_status = not current_status
            
            update_result = self.storage.update_one(
                query, 
                {"$set": {f"environments.{environment}": new_status}}
            )
            
            if update_result.modified_count:
                updated_flag = self.storage.find_one(query)
                updated_flag['_id'] = str(updated_flag['_id'])
                updated_flag['enabled'] = new_status
                return updated_flag
        return None

    def _build_id_query(self, flag_id):
        """Build a query for finding a flag by ID, handling both ObjectId and string formats."""
        if ObjectId.is_valid(flag_id):
            return {"_id": ObjectId(flag_id)}
        return {"_id": flag_id}
