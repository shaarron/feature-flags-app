from flask import Flask, request, jsonify, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from flask import render_template
from flask_cors import CORS
import json
import uuid
from datetime import datetime

app = Flask(__name__)

# Database connection and fallback storage
class FeatureFlagStorage:
    def __init__(self):
        self.mongo_available = False
        self.client = None
        self.db = None
        self.collection = None
        self.fallback_storage = []
        self._initialize_mongo()
        self._seed_fallback_data()
    
    def _initialize_mongo(self):
        """Initialize MongoDB connection with error handling"""
        try:
            mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client.feature_flags_db
            self.collection = self.db.flags
            self.mongo_available = True
            print("MongoDB connection established successfully!")
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            print("Falling back to in-memory storage")
            self.mongo_available = False
    
    def _seed_fallback_data(self):
        """Initialize fallback storage as empty list"""
        if not self.mongo_available:
            self.fallback_storage = []
            print("Fallback storage initialized (empty - no default flags)")
    
    def insert_one(self, document):
        """Insert a document into storage"""
        if self.mongo_available:
            try:
                result = self.collection.insert_one(document)
                document['_id'] = str(result.inserted_id)
                return result
            except Exception as e:
                print(f"MongoDB insert failed, using fallback: {e}")
                self.mongo_available = False
        
        # Fallback to in-memory storage
        document['_id'] = str(uuid.uuid4())
        self.fallback_storage.append(document)
        return type('Result', (), {'inserted_id': document['_id']})()
    
    def find(self, query=None):
        """Find documents in storage"""
        if self.mongo_available:
            try:
                return self.collection.find(query or {})
            except Exception as e:
                print(f"MongoDB find failed, using fallback: {e}")
                self.mongo_available = False
        
        # Fallback to in-memory storage
        if query is None:
            return self.fallback_storage.copy()
        # Simple query matching (for basic use cases)
        results = []
        for doc in self.fallback_storage:
            if all(doc.get(k) == v for k, v in query.items()):
                results.append(doc)
        return results
    
    def find_one(self, query):
        """Find one document in storage"""
        if self.mongo_available:
            try:
                return self.collection.find_one(query)
            except Exception as e:
                print(f"MongoDB find_one failed, using fallback: {e}")
                self.mongo_available = False
        
        # Fallback to in-memory storage
        for doc in self.fallback_storage:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None
    
    def update_one(self, query, update):
        """Update one document in storage"""
        if self.mongo_available:
            try:
                return self.collection.update_one(query, update)
            except Exception as e:
                print(f"MongoDB update failed, using fallback: {e}")
                self.mongo_available = False
        
        # Fallback to in-memory storage
        for i, doc in enumerate(self.fallback_storage):
            if all(doc.get(k) == v for k, v in query.items()):
                if '$set' in update:
                    doc.update(update['$set'])
                    self.fallback_storage[i] = doc
                return type('Result', (), {'matched_count': 1, 'modified_count': 1})()
        return type('Result', (), {'matched_count': 0, 'modified_count': 0})()
    
    def delete_one(self, query):
        """Delete one document from storage"""
        if self.mongo_available:
            try:
                return self.collection.delete_one(query)
            except Exception as e:
                print(f"MongoDB delete failed, using fallback: {e}")
                self.mongo_available = False
        
        # Fallback to in-memory storage
        for i, doc in enumerate(self.fallback_storage):
            if all(doc.get(k) == v for k, v in query.items()):
                del self.fallback_storage[i]
                return type('Result', (), {'deleted_count': 1})()
        return type('Result', (), {'deleted_count': 0})()

# Initialize storage
storage = FeatureFlagStorage()
feature_flags_collection = storage

# Seed database if MongoDB is available and collection is empty
if storage.mongo_available:
    try:
        # Check if collection already has data
        existing_flags = list(feature_flags_collection.find())
        if existing_flags:
            print(f"Database already contains {len(existing_flags)} feature flags. Skipping seeding.")
        else:
            print("Seeding database with environment-based feature flags...")
            # Insert flags with predefined environment-specific values
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
                feature_flags_collection.insert_one(flag_config)
            
            print("Database seeding completed successfully!")
    except Exception as e:
        print(f"Error during seeding: {e}")
        # Ignore seeding errors at startup
        pass

# Routes
@app.route('/flags', methods=['POST'])
def create_flag():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    environments = data.get('environments', {
        "development": True,   
        "staging": False,      
        "production": False    
    })

    if not name:
        return jsonify({"error": "Feature flag name is required"}), 400

    flag = {
        "name": name,
        "description": description,
        "environments": environments
    }
    result = feature_flags_collection.insert_one(flag)
    flag['_id'] = str(result.inserted_id)
    return jsonify(flag), 201



@app.route('/flags', methods=['GET'])
def get_flags():
    environment = request.args.get('environment', 'staging')
    flags = []
    for flag in feature_flags_collection.find():
        flag['_id'] = str(flag['_id'])
        # Add enabled status based on environment
        flag['enabled'] = flag.get('environments', {}).get(environment, False)
        flags.append(flag)
    return jsonify(flags), 200

@app.route('/flags/<id>', methods=['GET'])
def get_flag(id):
    # Handle both MongoDB ObjectId and fallback string IDs
    if storage.mongo_available:
        try:
            flag = feature_flags_collection.find_one({"_id": ObjectId(id)})
        except:
            flag = feature_flags_collection.find_one({"_id": id})
    else:
        flag = feature_flags_collection.find_one({"_id": id})
    
    if flag:
        flag['_id'] = str(flag['_id'])
        return jsonify(flag), 200
    return jsonify({"error": "Feature flag not found"}), 404

@app.route('/flags/<id>', methods=['PUT'])
def update_flag(id):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    environments = data.get('environments')

    update_fields = {}
    if name is not None:
        update_fields['name'] = name
    if description is not None:
        update_fields['description'] = description
    if environments is not None:
        update_fields['environments'] = environments
    
    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    # Handle both MongoDB ObjectId and fallback string IDs
    if storage.mongo_available:
        try:
            query = {"_id": ObjectId(id)}
        except:
            query = {"_id": id}
    else:
        query = {"_id": id}

    result = feature_flags_collection.update_one(query, {"$set": update_fields})
    if result.matched_count:
        flag = feature_flags_collection.find_one(query)
        flag['_id'] = str(flag['_id'])
        return jsonify(flag), 200
    return jsonify({"error": "Feature flag not found"}), 404

@app.route('/flags/<id>', methods=['DELETE'])
def delete_flag(id):
    # Handle both MongoDB ObjectId and fallback string IDs
    if storage.mongo_available:
        try:
            query = {"_id": ObjectId(id)}
        except:
            query = {"_id": id}
    else:
        query = {"_id": id}
    
    result = feature_flags_collection.delete_one(query)
    if result.deleted_count:
        return jsonify({"message": "Feature flag deleted"}), 204
    return jsonify({"error": "Feature flag not found"}), 404

@app.route('/flags/<id>/toggle', methods=['POST'])
def toggle_flag(id):
    data = request.get_json()
    environment = data.get('environment', 'staging')
    
    # Handle both MongoDB ObjectId and fallback string IDs
    if storage.mongo_available:
        try:
            query = {"_id": ObjectId(id)}
        except:
            query = {"_id": id}
    else:
        query = {"_id": id}
    
    flag = feature_flags_collection.find_one(query)
    if flag:
        current_status = flag.get('environments', {}).get(environment, False)
        new_status = not current_status
        
        # Update the specific environment
        update_result = feature_flags_collection.update_one(
            query, 
            {"$set": {f"environments.{environment}": new_status}}
        )
        
        if update_result.modified_count:
            # Return updated flag
            updated_flag = feature_flags_collection.find_one(query)
            updated_flag['_id'] = str(updated_flag['_id'])
            updated_flag['enabled'] = new_status
            return jsonify(updated_flag), 200
        
    return jsonify({"error": "Feature flag not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')