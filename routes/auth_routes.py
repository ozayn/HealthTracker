from flask import Blueprint, request, jsonify, redirect, url_for, current_app, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Integration
from datetime import datetime, timedelta
from services.fitbit_service import FitbitService
from services.oura_service import OuraService
from services.clue_service import ClueService
from services.google_drive_service import GoogleDriveService

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

        # Dynamically determine redirect URI based on request origin
        base_url = request.host_url.rstrip('/')
        if 'railway.app' in base_url:
            # Railway subdomain
            redirect_uri = 'https://web-production-3e53e.up.railway.app/api/auth/google/callback'
        elif 'healthtracker.ozayn.com' in base_url:
            # Custom domain
            redirect_uri = 'https://healthtracker.ozayn.com/api/auth/google/callback'
        else:
            # Fallback to configured URI
            redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI')

        if not redirect_uri:
            return jsonify({'error': 'Could not determine redirect URI'}), 500

        print(f"OAuth redirect URI: {redirect_uri} (from {base_url})")
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

    # Dynamically determine redirect URI based on request origin
    base_url = request.host_url.rstrip('/')
    if 'railway.app' in base_url:
        # Railway subdomain
        redirect_uri = 'https://web-production-3e53e.up.railway.app/api/auth/oura/callback'
    elif 'healthtracker.ozayn.com' in base_url:
        # Custom domain
        redirect_uri = 'https://healthtracker.ozayn.com/api/auth/oura/callback'
    else:
        # Fallback to configured URI
        redirect_uri = current_app.config.get('OURA_REDIRECT_URI')

    oura_service = OuraService()
    auth_url = oura_service.get_authorization_url(user_id, redirect_uri)

    print(f"Oura OAuth redirect URI: {redirect_uri} (from {base_url})")
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

# Google Drive Integration for Clue Data Import
@auth_bp.route('/google-drive/authorize', methods=['GET'])
@login_required
def google_drive_authorize():
    """Initiate Google Drive OAuth flow for Clue data import"""
    user_id = current_user.id

    google_drive_service = GoogleDriveService()
    auth_url = google_drive_service.get_authorization_url(user_id)

    if not auth_url:
        return jsonify({'error': 'Google Drive integration not configured. Please check GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET.'}), 500

    return jsonify({'authorization_url': auth_url})

@auth_bp.route('/google-drive/callback', methods=['GET'])
@login_required
def google_drive_callback():
    """Handle Google Drive OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        return jsonify({'error': 'Authorization code not provided'}), 400

    user = current_user

    try:
        google_drive_service = GoogleDriveService()
        tokens = google_drive_service.exchange_code_for_token(code)

        # Save Google Drive integration
        integration = Integration(
            user_id=user.id,
            provider='google_drive',
            access_token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token'),
            token_expires_at=datetime.utcnow() + timedelta(seconds=3600),  # 1 hour default
            is_active=True
        )
        db.session.add(integration)
        db.session.commit()

        return redirect('/dashboard?integration=google_drive&status=success')

    except Exception as e:
        print(f"Google Drive OAuth error: {str(e)}")
        return redirect('/dashboard?integration=google_drive&status=error')

@auth_bp.route('/clue/import-drive', methods=['POST'])
@login_required
def import_clue_from_drive():
    """Import Clue data from Google Drive"""
    user = current_user

    # Get Google Drive integration
    google_drive_integration = Integration.query.filter_by(
        user_id=user.id,
        provider='google_drive',
        is_active=True
    ).first()

    if not google_drive_integration:
        return jsonify({'error': 'Google Drive not connected. Please connect Google Drive first.'}), 400

    try:
        google_drive_service = GoogleDriveService()
        drive_service = google_drive_service.get_drive_service(
            google_drive_integration.access_token,
            google_drive_integration.refresh_token
        )

        # Find Clue folder
        clue_folder_id = google_drive_service.find_clue_folder(drive_service)
        if not clue_folder_id:
            return jsonify({'error': 'Could not find HealthTrackerData/Apps/Clue folder in Google Drive'}), 404

        # List files in Clue folder
        files = google_drive_service.list_clue_files(drive_service, clue_folder_id)

        imported_data = {
            'cycles': 0,
            'symptoms': 0,
            'moods': 0,
            'files_processed': 0
        }

        # Process each file
        for file_info in files:
            if file_info['name'].endswith(('.csv', '.json')):
                folder_path = getattr(file_info, 'folder_path', 'Clue folder')
                print(f"Processing file: {file_info['name']} from {folder_path}")

                df = google_drive_service.download_and_parse_clue_file(
                    drive_service, file_info['id'], file_info['name']
                )

                if df is not None:
                    parsed_data = google_drive_service.parse_clue_cycle_data(df)

                    # Save to database using ClueService
                    clue_service = ClueService()
                    clue_service._save_parsed_data(user.id, parsed_data)

                    imported_data['cycles'] += len(parsed_data['cycles'])
                    imported_data['symptoms'] += len(parsed_data['symptoms'])
                    imported_data['moods'] += len(parsed_data['moods'])
                    imported_data['files_processed'] += 1

                    # Track folder information
                    if folder_path not in imported_data:
                        imported_data[folder_path] = {'files': 0, 'records': 0}
                    imported_data[folder_path]['files'] += 1
                    imported_data[folder_path]['records'] += (
                        len(parsed_data['cycles']) +
                        len(parsed_data['symptoms']) +
                        len(parsed_data['moods'])
                    )

        google_drive_integration.last_sync = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Clue data imported successfully from Google Drive',
            'data': imported_data
        })

    except Exception as e:
        print(f"Error importing Clue data from Google Drive: {str(e)}")
        return jsonify({'error': f'Failed to import Clue data: {str(e)}'}), 500

