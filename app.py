from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
import os
from config import Config
from models import db, User

def create_app():
    app = Flask(__name__, static_folder='frontend/build')
    app.config.from_object(Config)

    # Enable CORS with credentials support
    CORS(app, resources={r"/api/*": {"origins": "*", "supports_credentials": True}})

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.google_login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize OAuth
    oauth = OAuth(app)

    # Only register Google OAuth if credentials are configured
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        google = oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            authorize_url='https://accounts.google.com/o/oauth2/auth',
            authorize_params=None,
            access_token_url='https://oauth2.googleapis.com/token',
            access_token_params=None,
            jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
    else:
        print("Warning: Google OAuth credentials not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.health_routes import health_bp
    from routes.blood_test_routes import blood_test_bp
    from routes.user_routes import user_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    app.register_blueprint(blood_test_bp, url_prefix='/api/blood-tests')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    
    # Serve React frontend (exclude API routes)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        # Skip API routes - let blueprints handle them
        if path.startswith('api/'):
            from flask import abort
            abort(404)

        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')
    
    # Health check endpoint
    @app.route('/api/health-check')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Health Tracker API is running'})
    
    # Make oauth available to routes
    app.oauth = oauth

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    port = int(os.getenv('PORT', 5007))
    # Run in production-like mode (no auto-restart on file changes)
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

