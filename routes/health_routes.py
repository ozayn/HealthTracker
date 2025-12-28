from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Integration, HealthData
from datetime import datetime, timedelta
from services.fitbit_service import FitbitService
from services.oura_service import OuraService
from services.clue_service import ClueService

health_bp = Blueprint('health', __name__)

@health_bp.route('/sync', methods=['POST'])
@login_required
def sync_health_data():
    """Sync health data from all connected providers"""
    user = current_user
    print(f"=== FULL SYNC START ===")
    print(f"Starting full sync for user {user.id}")

    data = request.get_json() or {}
    days = data.get('days', 30)  # Default to last 30 days
    sync_type = data.get('type', 'full')  # 'full' or 'recent'
    print(f"Syncing last {days} days (type: {sync_type})")

    results = {
        'fitbit': None,
        'oura': None,
        'clue': None
    }
    
    # Sync Fitbit
    fitbit_integration = Integration.query.filter_by(
        user_id=user.id,
        provider='fitbit',
        is_active=True
    ).first()

    if fitbit_integration:
        fitbit_service = FitbitService()
        try:
            results['fitbit'] = fitbit_service.sync_data(user.id, fitbit_integration, days)
            fitbit_integration.last_sync = datetime.utcnow()
        except Exception as e:
            results['fitbit'] = {'error': str(e)}
    
    # Sync Oura
    oura_integration = Integration.query.filter_by(
        user_id=user.id,
        provider='oura',
        is_active=True
    ).first()
    print(f"Oura integration found: {oura_integration is not None}")

    if oura_integration:
        print(f"Oura access token exists: {bool(oura_integration.access_token)}")
        oura_service = OuraService()
        try:
            if sync_type == 'recent':
                # Sync only recent data (last 24 hours)
                results['oura'] = oura_service.sync_recent_data(user.id, oura_integration, hours=24)
            else:
                # Full sync (specified number of days)
                results['oura'] = oura_service.sync_data(user.id, oura_integration, days)
            oura_integration.last_sync = datetime.utcnow()
            print(f"Oura {sync_type} sync results: {results['oura']}")
        except Exception as e:
            print(f"Oura sync error: {str(e)}")
            results['oura'] = {'error': str(e)}
    
    # Sync Clue
    clue_integration = Integration.query.filter_by(
        user_id=user.id,
        provider='clue',
        is_active=True
    ).first()

    if clue_integration:
        clue_service = ClueService()
        try:
            results['clue'] = clue_service.sync_data(user.id, clue_integration, days)
            clue_integration.last_sync = datetime.utcnow()
        except Exception as e:
            results['clue'] = {'error': str(e)}
    
    db.session.commit()
    
    return jsonify(results)

@health_bp.route('', methods=['GET'])
@login_required
def get_health_data():
    """Get health data for current user"""
    user = current_user
    
    # Query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    data_type = request.args.get('data_type')
    provider = request.args.get('provider')
    
    query = HealthData.query.filter_by(user_id=user.id)
    
    if start_date:
        query = query.filter(HealthData.date >= datetime.fromisoformat(start_date).date())
    
    if end_date:
        query = query.filter(HealthData.date <= datetime.fromisoformat(end_date).date())
    
    if data_type:
        query = query.filter_by(data_type=data_type)
    
    if provider:
        query = query.filter_by(provider=provider)
    
    health_data = query.order_by(HealthData.date.desc()).all()
    
    return jsonify([data.to_dict() for data in health_data])

@health_bp.route('/summary', methods=['GET'])
@login_required
def get_health_summary():
    """Get aggregated health data summary"""
    user = current_user

    days = int(request.args.get('days', 7))
    start_date = datetime.utcnow().date() - timedelta(days=days)

    # Get all health data for the user in date range
    health_data = HealthData.query.filter(
        HealthData.user_id == user.id,
        HealthData.date >= start_date
    ).order_by(HealthData.date.desc()).all()

    # Aggregate data by data_type
    summary = {}
    for record in health_data:
        data_type = record.data_type
        if data_type not in summary:
            summary[data_type] = {
                'values': [],
                'unit': record.unit or '',
                'latest_value': record.value,
                'latest_date': record.date.isoformat()
            }
        summary[data_type]['values'].append({
            'date': record.date.isoformat(),
            'value': record.value
        })

    return jsonify(summary)

@health_bp.route('/data-summary', methods=['GET'])
@login_required
def get_data_summary():
    """Get comprehensive data summary for current user"""
    user = current_user
    summary = HealthData.get_user_data_summary(user.id)
    return jsonify(summary)

@health_bp.route('/sync-recent', methods=['POST'])
@login_required
def sync_recent_health_data():
    """Sync only recent health data (last 24 hours) - for real-time updates"""
    user = current_user
    print("=== RECENT SYNC START ===")
    print(f"Starting recent sync for user {user.id}")

    data = request.get_json() or {}
    hours = data.get('hours', 24)  # Default to last 24 hours

    results = {
        'fitbit': None,
        'oura': None,
        'clue': None
    }

    # Sync Oura recent data
    oura_integration = Integration.query.filter_by(
        user_id=user.id,
        provider='oura',
        is_active=True
    ).first()

    if oura_integration:
        print(f"Oura integration found, syncing last {hours} hours")
        oura_service = OuraService()
        try:
            results['oura'] = oura_service.sync_recent_data(user.id, oura_integration, hours=hours)
            oura_integration.last_sync = datetime.utcnow()
            db.session.commit()
            print(f"Oura recent sync results: {results['oura']}")
        except Exception as e:
            print(f"Oura recent sync error: {str(e)}")
            results['oura'] = {'error': str(e)}

    return jsonify(results)

@health_bp.route('/export', methods=['GET'])
@login_required
def export_user_data():
    """Export all user health data as JSON"""
    user = current_user

    # Get all health data for user
    health_data = HealthData.query.filter_by(user_id=user.id).order_by(
        HealthData.date.desc(), HealthData.created_at.desc()
    ).all()

    # Get all blood tests for user
    blood_tests = []
    try:
        from models import BloodTest, BloodMarker
        blood_tests_data = BloodTest.query.filter_by(user_id=user.id).order_by(
            BloodTest.test_date.desc()
        ).all()

        for test in blood_tests_data:
            markers = BloodMarker.query.filter_by(blood_test_id=test.id).all()
            blood_tests.append({
                'test': test.to_dict(),
                'markers': [marker.to_dict() for marker in markers]
            })
    except:
        pass  # Blood test tables might not exist yet

    # Get integrations
    integrations = []
    try:
        from models import Integration
        integrations = Integration.query.filter_by(user_id=user.id).all()
        integrations = [i.to_dict() for i in integrations]
    except:
        pass

    export_data = {
        'export_date': datetime.utcnow().isoformat(),
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'created_at': user.created_at.isoformat() if user.created_at else None
        },
        'health_data': [data.to_dict() for data in health_data],
        'blood_tests': blood_tests,
        'integrations': integrations,
        'data_summary': HealthData.get_user_data_summary(user.id)
    }

    return jsonify(export_data)
@login_required
def get_health_summary():
    """Get aggregated health data summary"""
    user = current_user
    
    days = int(request.args.get('days', 7))
    start_date = datetime.utcnow().date() - timedelta(days=days)
    
    health_data = HealthData.query.filter(
        HealthData.user_id == user.id,
        HealthData.date >= start_date
    ).all()
    
    # Aggregate data by type
    summary = {}
    for data in health_data:
        if data.data_type not in summary:
            summary[data.data_type] = {
                'provider': data.provider,
                'unit': data.unit,
                'values': []
            }
        summary[data.data_type]['values'].append({
            'date': data.date.isoformat(),
            'value': data.value
        })
    
    return jsonify(summary)

@health_bp.route('/test-sync', methods=['POST'])
def test_sync_health_data():
    """Test sync health data - temporary endpoint for debugging"""
    print("=== TEST SYNC START ===")

    # For testing, assume user ID 2 (from database check)
    from models import User
    user = User.query.get(2)
    if not user:
        return jsonify({'error': 'Test user not found'}), 404

    print(f"Test sync for user {user.id}")

    data = request.get_json() or {}
    days = data.get('days', 7)  # Default to last 7 days for testing
    sync_type = data.get('type', 'recent')  # Default to recent for testing
    print(f"Syncing last {days} days (type: {sync_type})")

    results = {
        'fitbit': None,
        'oura': None,
        'clue': None
    }

    # Sync Oura only for testing
    oura_integration = Integration.query.filter_by(
        user_id=user.id,
        provider='oura',
        is_active=True
    ).first()

    if oura_integration:
        print("Oura integration found")
        print(f"Oura access token exists: {bool(oura_integration.access_token)}")
        oura_service = OuraService()
        try:
            if sync_type == 'recent':
                # Sync only recent data (last 24 hours)
                results['oura'] = oura_service.sync_recent_data(user.id, oura_integration, hours=24)
            else:
                # Full sync (specified number of days)
                results['oura'] = oura_service.sync_data(user.id, oura_integration, days)
            oura_integration.last_sync = datetime.utcnow()
            db.session.commit()
            print(f"Oura {sync_type} sync results: {results['oura']}")
        except Exception as e:
            print(f"Oura sync error: {str(e)}")
            results['oura'] = {'error': str(e)}

    return jsonify(results)

@health_bp.route('/types', methods=['GET'])
def get_data_types():
    """Get all available data types"""
    data_types = db.session.query(HealthData.data_type).distinct().all()
    return jsonify([dt[0] for dt in data_types])

