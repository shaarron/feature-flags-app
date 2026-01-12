import os
import uuid
import logging
from pymongo import MongoClient
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

class FeatureFlagStorage:
    def __init__(self):
        self.mongo_available = False
        self.client = None
        self.db = None
        self.collection = None
        self.fallback_storage = []
        self._initialize_mongo()
        if self.mongo_available:
            self._seed_database()

    def _initialize_mongo(self):
        try:
            user = os.environ.get('MONGO_INITDB_ROOT_USERNAME')
            pw = os.environ.get('MONGO_INITDB_ROOT_PASSWORD')
            host = os.environ.get('MONGO_HOST', 'localhost')
            
            uri = f"mongodb://{user}:{pw}@{host}:27017/?authSource=admin" if user and pw else 'mongodb://localhost:27017/'
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client.feature_flags_db
            self.collection = self.db.flags
            self.mongo_available = True
        except Exception as e:
            logger.error(f"MongoDB failed: {e}. Using in-memory fallback.")

    def _seed_database(self):
        if self.collection.count_documents({}) == 0:
            logger.info("Seeding database with environment-based feature flags...")
            flag_configs = [
                {
                    "name": "new-dashboard",
                    "description": "Ship the redesigned dashboard.",
                    "environments": {
                        "development": True,   
                        "staging": True,       
                        "production": False    
                    }
                },
                {
                    "name": "beta-checkout",
                    "description": "New checkout flow for selected users.",
                    "environments": {
                        "development": True,   
                        "staging": True,       
                        "production": True     
                    }
                },
                {
                    "name": "recommendations",
                    "description": "Product recommendations widget.",
                    "environments": {
                        "development": True,   
                        "staging": False,      
                        "production": False    
                    }
                },
                {
                    "name": "ab-test-home-hero",
                    "description": "A/B test variant of the home hero section.",
                    "environments": {
                        "development": True,   
                        "staging": True,       
                        "production": True     
                    }
                },
                {
                    "name": "dark-mode",
                    "description": "Enable dark theme toggle for all users.",
                    "environments": {
                        "development": True,  
                        "staging": True,       
                        "production": True     
                    }
                },
                {
                    "name": "limit-rate-api",
                    "description": "Enable request rate limiting on APIs.",
                    "environments": {
                        "development": False,  
                        "staging": True,       
                        "production": True     
                    }
                }
            ]
            
            try:
                for flag_config in flag_configs:
                    self.collection.insert_one(flag_config)
                logger.info("Database seeding completed successfully!")
            except Exception as e:
                logger.error(f"Error during seeding: {e}") 

    def get_all(self, environment='staging'):
        flags = []
        cursor = self.collection.find() if self.mongo_available else self.fallback_storage
        for flag in cursor:
            flag['_id'] = str(flag['_id'])
            flag['enabled'] = flag.get('environments', {}).get(environment, False)
            flags.append(flag)
        return flags

    def insert_one(self, document):
        if self.mongo_available:
            try:
                result = self.collection.insert_one(document)
                document['_id'] = str(result.inserted_id)
                return result
            except Exception as e:
                logger.info(f"MongoDB insert failed, using fallback: {e}")
                self.mongo_available = False
        
        document['_id'] = str(uuid.uuid4())
        self.fallback_storage.append(document)
        return type('Result', (), {'inserted_id': document['_id']})()

    def find_one(self, query):
        if self.mongo_available:
            try:
                return self.collection.find_one(query)
            except Exception as e:
                logger.info(f"MongoDB find_one failed, using fallback: {e}")
                self.mongo_available = False
        
        for doc in self.fallback_storage:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def update_one(self, query, update):
        if self.mongo_available:
            try:
                return self.collection.update_one(query, update)
            except Exception as e:
                logger.info(f"MongoDB update failed, using fallback: {e}")
                self.mongo_available = False
        
        for i, doc in enumerate(self.fallback_storage):
            if all(doc.get(k) == v for k, v in query.items()):
                if '$set' in update:
                    doc.update(update['$set'])
                    self.fallback_storage[i] = doc
                return type('Result', (), {'matched_count': 1, 'modified_count': 1})()
        return type('Result', (), {'matched_count': 0, 'modified_count': 0})()

    def delete_one(self, query):
        if self.mongo_available:
            try:
                return self.collection.delete_one(query)
            except Exception as e:
                logger.info(f"MongoDB delete failed, using fallback: {e}")
                self.mongo_available = False
        
        for i, doc in enumerate(self.fallback_storage):
            if all(doc.get(k) == v for k, v in query.items()):
                del self.fallback_storage[i]
                return type('Result', (), {'deleted_count': 1})()
        return type('Result', (), {'deleted_count': 0})()