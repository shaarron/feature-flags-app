from flask import Blueprint, request, jsonify
from feature_flag_service import FeatureFlagService

flags_bp = Blueprint('flags', __name__)
service = FeatureFlagService()

@flags_bp.route('/flags', methods=['GET'])
def get_flags():
    env = request.args.get('environment', 'staging')
    return jsonify(service.get_all_flags(env)), 200

@flags_bp.route('/flags', methods=['POST'])
def create_flag():
    data = request.get_json()
    if not data.get('name'):
        return jsonify({"error": "Name required"}), 400
    flag = service.create_flag(data)
    return jsonify(flag), 201

@flags_bp.route('/flags/<id>', methods=['GET'])
def get_flag(id):
    flag = service.get_flag(id)
    if flag:
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
    
    flag, error = service.update_flag(id, update_fields)
    if error:
        status_code = 400 if error == "No fields to update" else 404
        return jsonify({"error": error}), status_code
    
    return jsonify(flag), 200

@flags_bp.route('/flags/<id>', methods=['DELETE'])
def delete_flag(id):
    success = service.delete_flag(id)
    if success:
        return jsonify({"message": "Feature flag deleted"}), 204
    return jsonify({"error": "Feature flag not found"}), 404

@flags_bp.route('/flags/<id>/toggle', methods=['POST'])
def toggle_flag(id):
    data = request.get_json()
    environment = data.get('environment', 'staging')
    
    flag = service.toggle_flag(id, environment)
    if flag:
        return jsonify(flag), 200
        
    return jsonify({"error": "Feature flag not found"}), 404