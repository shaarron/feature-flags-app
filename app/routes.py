from flask import Blueprint, request, jsonify
from storage import FeatureFlagStorage
from bson.objectid import ObjectId

flags_bp = Blueprint('flags', __name__)
storage = FeatureFlagStorage()

@flags_bp.route('/flags', methods=['GET'])
def get_flags():
    env = request.args.get('environment', 'staging')
    return jsonify(storage.get_all(env)), 200

@flags_bp.route('/flags', methods=['POST'])
def create_flag():
    data = request.get_json()
    if not data.get('name'):
        return jsonify({"error": "Name required"}), 400
    result = storage.insert_one(data)
    return jsonify(data), 201

@flags_bp.route('/flags/<id>', methods=['GET'])
def get_flag(id):
    if storage.mongo_available:
        try:
            flag = storage.find_one({"_id": ObjectId(id)})
        except:
            flag = storage.find_one({"_id": id})
    else:
        flag = storage.find_one({"_id": id})
    
    if flag:
        flag['_id'] = str(flag['_id'])
        return jsonify(flag), 200
    return jsonify({"error": "Feature flag not found"}), 404

@flags_bp.route('/flags/<id>', methods=['PUT'])
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

    if storage.mongo_available:
        try:
            query = {"_id": ObjectId(id)}
        except:
            query = {"_id": id}
    else:
        query = {"_id": id}

    result = storage.update_one(query, {"$set": update_fields})
    if result.matched_count:
        flag = storage.find_one(query)
        flag['_id'] = str(flag['_id'])
        return jsonify(flag), 200
    return jsonify({"error": "Feature flag not found"}), 404

@flags_bp.route('/flags/<id>', methods=['DELETE'])
def delete_flag(id):
    if storage.mongo_available:
        try:
            query = {"_id": ObjectId(id)}
        except:
            query = {"_id": id}
    else:
        query = {"_id": id}
    
    result = storage.delete_one(query)
    if result.deleted_count:
        return jsonify({"message": "Feature flag deleted"}), 204
    return jsonify({"error": "Feature flag not found"}), 404

@flags_bp.route('/flags/<id>/toggle', methods=['POST'])
def toggle_flag(id):
    data = request.get_json()
    environment = data.get('environment', 'staging')
    
    if storage.mongo_available:
        try:
            query = {"_id": ObjectId(id)}
        except:
            query = {"_id": id}
    else:
        query = {"_id": id}
    
    flag = storage.find_one(query)
    if flag:
        current_status = flag.get('environments', {}).get(environment, False)
        new_status = not current_status
        
        # Update the specific environment
        update_result = storage.update_one(
            query, 
            {"$set": {f"environments.{environment}": new_status}}
        )
        
        if update_result.modified_count:
            # Return updated flag
            updated_flag = storage.find_one(query)
            updated_flag['_id'] = str(updated_flag['_id'])
            updated_flag['enabled'] = new_status
            return jsonify(updated_flag), 200
        
    return jsonify({"error": "Feature flag not found"}), 404