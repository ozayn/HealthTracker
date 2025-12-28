from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, User, BloodTest, BloodMarker
from datetime import datetime
from werkzeug.utils import secure_filename
import os

blood_test_bp = Blueprint('blood_tests', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blood_test_bp.route('', methods=['POST'])
@login_required
def create_blood_test():
    """Create a new blood test record"""
    user = current_user
    
    data = request.form
    test_date = datetime.fromisoformat(data.get('test_date')).date() if data.get('test_date') else datetime.utcnow().date()
    
    blood_test = BloodTest(
        user_id=user_id,
        test_date=test_date,
        lab_name=data.get('lab_name'),
        notes=data.get('notes')
    )
    
    # Handle file upload
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{datetime.utcnow().timestamp()}_{file.filename}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            blood_test.file_path = filepath
    
    db.session.add(blood_test)
    db.session.commit()
    
    return jsonify(blood_test.to_dict()), 201

@blood_test_bp.route('', methods=['GET'])
@login_required
def get_blood_tests():
    """Get all blood tests for current user"""
    user = current_user
    
    blood_tests = BloodTest.query.filter_by(user_id=user.id).order_by(BloodTest.test_date.desc()).all()
    
    return jsonify([test.to_dict() for test in blood_tests])

@blood_test_bp.route('/test/<int:test_id>', methods=['GET'])
@login_required
def get_blood_test(test_id):
    """Get a specific blood test"""
    blood_test = BloodTest.query.filter_by(
        id=test_id,
        user_id=current_user.id
    ).first_or_404()
    return jsonify(blood_test.to_dict())

@blood_test_bp.route('/test/<int:test_id>', methods=['PUT'])
@login_required
def update_blood_test(test_id):
    """Update a blood test"""
    blood_test = BloodTest.query.filter_by(
        id=test_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    
    if 'test_date' in data:
        blood_test.test_date = datetime.fromisoformat(data['test_date']).date()
    if 'lab_name' in data:
        blood_test.lab_name = data['lab_name']
    if 'notes' in data:
        blood_test.notes = data['notes']
    
    db.session.commit()
    
    return jsonify(blood_test.to_dict())

@blood_test_bp.route('/test/<int:test_id>', methods=['DELETE'])
@login_required
def delete_blood_test(test_id):
    """Delete a blood test"""
    blood_test = BloodTest.query.filter_by(
        id=test_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Delete associated file if exists
    if blood_test.file_path and os.path.exists(blood_test.file_path):
        os.remove(blood_test.file_path)
    
    db.session.delete(blood_test)
    db.session.commit()
    
    return jsonify({'message': 'Blood test deleted successfully'})

@blood_test_bp.route('/test/<int:test_id>/markers', methods=['POST'])
@login_required
def add_blood_marker(test_id):
    """Add a blood marker to a test"""
    blood_test = BloodTest.query.filter_by(
        id=test_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    
    marker = BloodMarker(
        blood_test_id=test_id,
        marker_name=data['marker_name'],
        value=float(data['value']),
        unit=data.get('unit'),
        reference_range_low=float(data['reference_range_low']) if data.get('reference_range_low') else None,
        reference_range_high=float(data['reference_range_high']) if data.get('reference_range_high') else None,
        is_abnormal=data.get('is_abnormal', False),
        notes=data.get('notes')
    )
    
    db.session.add(marker)
    db.session.commit()
    
    return jsonify(marker.to_dict()), 201

@blood_test_bp.route('/marker/<int:marker_id>', methods=['PUT'])
@login_required
def update_blood_marker(marker_id):
    """Update a blood marker"""
    # Find marker and ensure it belongs to current user via blood test
    marker = BloodMarker.query.join(BloodTest).filter(
        BloodMarker.id == marker_id,
        BloodTest.user_id == current_user.id
    ).first_or_404()
    
    data = request.get_json()
    
    if 'marker_name' in data:
        marker.marker_name = data['marker_name']
    if 'value' in data:
        marker.value = float(data['value'])
    if 'unit' in data:
        marker.unit = data['unit']
    if 'reference_range_low' in data:
        marker.reference_range_low = float(data['reference_range_low']) if data['reference_range_low'] else None
    if 'reference_range_high' in data:
        marker.reference_range_high = float(data['reference_range_high']) if data['reference_range_high'] else None
    if 'is_abnormal' in data:
        marker.is_abnormal = data['is_abnormal']
    if 'notes' in data:
        marker.notes = data['notes']
    
    db.session.commit()
    
    return jsonify(marker.to_dict())

@blood_test_bp.route('/marker/<int:marker_id>', methods=['DELETE'])
@login_required
def delete_blood_marker(marker_id):
    """Delete a blood marker"""
    # Find marker and ensure it belongs to current user via blood test
    marker = BloodMarker.query.join(BloodTest).filter(
        BloodMarker.id == marker_id,
        BloodTest.user_id == current_user.id
    ).first_or_404()
    db.session.delete(marker)
    db.session.commit()
    
    return jsonify({'message': 'Blood marker deleted successfully'})

@blood_test_bp.route('/markers/trends', methods=['GET'])
@login_required
def get_marker_trends():
    """Get trends for a specific marker over time"""
    user = current_user
    marker_name = request.args.get('marker_name')
    
    if not marker_name:
        return jsonify({'error': 'marker_name is required'}), 400
    
    # Get all blood tests for the user
    blood_tests = BloodTest.query.filter_by(user_id=user_id).order_by(BloodTest.test_date).all()
    
    trends = []
    for test in blood_tests:
        for marker in test.markers:
            if marker.marker_name.lower() == marker_name.lower():
                trends.append({
                    'date': test.test_date.isoformat(),
                    'value': marker.value,
                    'unit': marker.unit,
                    'is_abnormal': marker.is_abnormal,
                    'reference_range_low': marker.reference_range_low,
                    'reference_range_high': marker.reference_range_high
                })
    
    return jsonify(trends)

