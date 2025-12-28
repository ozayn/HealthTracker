from flask import Blueprint, request, jsonify, redirect, url_for, current_app, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Integration
from datetime import datetime, timedelta
from services.fitbit_service import FitbitService
from services.oura_service import OuraService
from services.clue_service import ClueService

auth_bp = Blueprint('auth', __name__)

# Google OAuth routes
@auth_bp.route('/google/login')
def google_login():
    """Initiate Google OAuth login"""
    try:
        client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')

        if not client_id or not client_secret or client_id.startswith('your-'):
            return jsonify({'error': 'Google OAuth not configured properly. Please check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env file.'}), 500

        # Check if google oauth is registered
        if not hasattr(current_app.oauth, 'google'):
            return jsonify({'error': 'Google OAuth client not registered. Please restart the server.'}), 500

        redirect_uri = url_for('auth.google_authorize', _external=True)
        return current_app.oauth.google.authorize_redirect(redirect_uri)
    except Exception as e:
        return jsonify({'error': f'Google OAuth setup error: {str(e)}. Please check your Google OAuth credentials.'}), 500

@auth_bp.route('/google/callback')
def google_authorize():
    """Handle Google OAuth callback"""
    try:
        # Get the access token
        token = current_app.oauth.google.authorize_access_token()

        # Get user info from Google's userinfo endpoint (more reliable than parsing ID token)
        resp = current_app.oauth.google.get('https://www.googleapis.com/oauth2/v2/userinfo')
        user_info = resp.json()

        # Check if user's email is in allowed list
        allowed_emails = current_app.config.get('ALLOWED_EMAILS', '')
        if allowed_emails:
            allowed_list = [email.strip() for email in allowed_emails.split(',')]
            if user_info.get('email') not in allowed_list:
                return jsonify({
                    'error': 'Access denied. Your email is not authorized to use this application.'
                }), 403

        # Check if user exists
        google_id = user_info.get('id')
        if not google_id:
            return jsonify({'error': 'Could not get Google user ID'}), 400

        user = User.query.filter_by(google_id=google_id).first()

        if not user:
            # Check if email already exists
            email = user_info.get('email')
            if not email:
                return jsonify({'error': 'Could not get user email from Google'}), 400

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                # Link Google account to existing user
                existing_user.google_id = google_id
                existing_user.name = user_info.get('name', '')
                existing_user.profile_pic = user_info.get('picture', '')
                user = existing_user
            else:
                # Create new user
                user = User(
                    email=email,
                    google_id=google_id,
                    name=user_info.get('name', ''),
                    profile_pic=user_info.get('picture', '')
                )
                db.session.add(user)

        db.session.commit()
        login_user(user)

        return redirect('/dashboard')

    except Exception as e:
        return jsonify({'error': f'OAuth error: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'user': current_user.to_dict()}), 200
    return jsonify({'authenticated': False}), 200

# Fitbit OAuth
@auth_bp.route('/fitbit/authorize', methods=['GET'])
@login_required
def fitbit_authorize():
    """Initiate Fitbit OAuth flow"""
    user_id = current_user.id
    
    fitbit_service = FitbitService()
    auth_url = fitbit_service.get_authorization_url(user_id)
    
    return jsonify({'authorization_url': auth_url})

@auth_bp.route('/fitbit/callback', methods=['GET'])
@login_required
def fitbit_callback():
    """Handle Fitbit OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        return jsonify({'error': 'Authorization code not provided'}), 400

    user = current_user
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    fitbit_service = FitbitService()
    tokens = fitbit_service.exchange_code_for_token(code)
    
    # Store or update integration
    integration = Integration.query.filter_by(user_id=user.id, provider='fitbit').first()
    if integration:
        integration.access_token = tokens['access_token']
        integration.refresh_token = tokens['refresh_token']
        integration.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
        integration.is_active = True
    else:
        integration = Integration(
            user_id=user.id,
            provider='fitbit',
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            token_expires_at=datetime.utcnow() + timedelta(seconds=tokens['expires_in']),
            is_active=True
        )
        db.session.add(integration)
    
    db.session.commit()
    
    return redirect('/dashboard?integration=fitbit&status=success')

# Oura OAuth
@auth_bp.route('/oura/authorize', methods=['GET'])
@login_required
def oura_authorize():
    """Initiate Oura OAuth flow"""
    user_id = current_user.id
    
    oura_service = OuraService()
    auth_url = oura_service.get_authorization_url(user_id)
    
    return jsonify({'authorization_url': auth_url})

@auth_bp.route('/oura/callback', methods=['GET'])
@login_required
def oura_callback():
    """Handle Oura OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        return jsonify({'error': 'Authorization code not provided'}), 400

    user = current_user
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    oura_service = OuraService()
    tokens = oura_service.exchange_code_for_token(code)
    
    integration = Integration.query.filter_by(user_id=user.id, provider='oura').first()
    if integration:
        integration.access_token = tokens['access_token']
        integration.refresh_token = tokens.get('refresh_token')
        integration.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 86400))
        integration.is_active = True
    else:
        integration = Integration(
            user_id=user.id,
            provider='oura',
            access_token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token'),
            token_expires_at=datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 86400)),
            is_active=True
        )
        db.session.add(integration)
    
    db.session.commit()
    
    return redirect('/dashboard?integration=oura&status=success')

# Clue OAuth
@auth_bp.route('/clue/authorize', methods=['GET'])
@login_required
def clue_authorize():
    """Initiate Clue OAuth flow"""
    user_id = current_user.id
    
    clue_service = ClueService()
    auth_url = clue_service.get_authorization_url(user_id)
    
    return jsonify({'authorization_url': auth_url})

@auth_bp.route('/clue/callback', methods=['GET'])
@login_required
def clue_callback():
    """Handle Clue OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        return jsonify({'error': 'Authorization code not provided'}), 400

    user = current_user
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    clue_service = ClueService()
    tokens = clue_service.exchange_code_for_token(code)
    
    integration = Integration.query.filter_by(user_id=user.id, provider='clue').first()
    if integration:
        integration.access_token = tokens['access_token']
        integration.refresh_token = tokens.get('refresh_token')
        integration.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 86400))
        integration.is_active = True
    else:
        integration = Integration(
            user_id=user.id,
            provider='clue',
            access_token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token'),
            token_expires_at=datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 86400)),
            is_active=True
        )
        db.session.add(integration)
    
    db.session.commit()
    
    return redirect('/dashboard?integration=clue&status=success')

# Get user integrations
@auth_bp.route('/integrations', methods=['GET'])
@login_required
def get_integrations():
    """Get all integrations for current user"""
    integrations = Integration.query.filter_by(user_id=current_user.id).all()
    return jsonify([integration.to_dict() for integration in integrations])

# Disconnect integration
@auth_bp.route('/integrations/<int:integration_id>', methods=['DELETE'])
@login_required
def disconnect_integration(integration_id):
    """Disconnect an integration"""
    integration = Integration.query.filter_by(
        id=integration_id,
        user_id=current_user.id
    ).first_or_404()
    integration.is_active = False
    db.session.commit()
    return jsonify({'message': 'Integration disconnected successfully'})

