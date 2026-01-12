import os
import uuid
import logging
from pymongo import MongoClient
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

class FeatureFlagStorage:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None

    def _get_collection(self):
        if self.collection is None:
            self._initialize_mongo()
            self._seed_database()
        return self.collection

    def _initialize_mongo(self):
        try:
            user = os.environ.get('MONGO_INITDB_ROOT_USERNAME')
            pw = os.environ.get('MONGO_INITDB_ROOT_PASSWORD')
            host = os.environ.get('MONGO_HOST', 'localhost')
            
            uri = f"mongodb://{user}:{pw}@{host}:27017/?authSource=admin" if user and pw else 'mongodb://localhost:27017/'
            # Reduce timeout for faster failure in tests if not mocked
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            self.db = self.client.feature_flags_db
            self.collection = self.db.flags
            logger.info("MongoDB connection established successfully!")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise e

    def _seed_database(self):
        try:
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
                
                for flag_config in flag_configs:
                    self.collection.insert_one(flag_config)
                logger.info("Database seeding completed successfully!")
        except Exception as e:
            logger.error(f"Error during seeding: {e}")

    def get_all(self, environment='staging'):
        flags = []
        cursor = self._get_collection().find()
        for flag in cursor:
            flag = flag.copy()
            flag['_id'] = str(flag['_id'])
            flag['enabled'] = flag.get('environments', {}).get(environment, False)
            flags.append(flag)
        return flags

    def insert_one(self, document):
        result = self._get_collection().insert_one(document)
        document['_id'] = str(result.inserted_id)
        return result

    def find_one(self, query):
        return self._get_collection().find_one(query)

    def update_one(self, query, update):
        return self._get_collection().update_one(query, update)

    def delete_one(self, query):
        return self._get_collection().delete_one(query)