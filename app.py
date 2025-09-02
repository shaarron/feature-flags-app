from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from flask import render_template
from flask_cors import CORS

app = Flask(__name__)

# MongoDB connection
client = MongoClient(os.environ.get('MONGO_URI', 'mongodb://localhost:27017/'))

db = client.feature_flags_db
feature_flags_collection = db.flags

# hardcoded flags for demonstration purposes
try:
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

@app.route('/')
def index():
    return render_template('index.html')

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
    flag = feature_flags_collection.find_one({"_id": ObjectId(id)})
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

    result = feature_flags_collection.update_one({"_id": ObjectId(id)}, {"$set": update_fields})
    if result.matched_count:
        flag = feature_flags_collection.find_one({"_id": ObjectId(id)})
        flag['_id'] = str(flag['_id'])
        return jsonify(flag), 200
    return jsonify({"error": "Feature flag not found"}), 404

@app.route('/flags/<id>', methods=['DELETE'])
def delete_flag(id):
    result = feature_flags_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count:
        return jsonify({"message": "Feature flag deleted"}), 204
    return jsonify({"error": "Feature flag not found"}), 404

@app.route('/flags/<id>/toggle', methods=['POST'])
def toggle_flag(id):
    data = request.get_json()
    environment = data.get('environment', 'staging')
    
    flag = feature_flags_collection.find_one({"_id": ObjectId(id)})
    if flag:
        current_status = flag.get('environments', {}).get(environment, False)
        new_status = not current_status
        
        # Update the specific environment
        update_result = feature_flags_collection.update_one(
            {"_id": ObjectId(id)}, 
            {"$set": {f"environments.{environment}": new_status}}
        )
        
        if update_result.modified_count:
            # Return updated flag
            updated_flag = feature_flags_collection.find_one({"_id": ObjectId(id)})
            updated_flag['_id'] = str(updated_flag['_id'])
            updated_flag['enabled'] = new_status
            return jsonify(updated_flag), 200
        
    return jsonify({"error": "Feature flag not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')