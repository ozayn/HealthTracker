from flask import Blueprint, request, jsonify
from models import db, User

user_bp = Blueprint('users', __name__)

@user_bp.route('', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify(existing_user.to_dict()), 200
    
    user = User(email=data['email'])
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('', methods=['GET'])
def get_users():
    """Get all users"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

