from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
import os
from config import Config
from models import db, User

def create_app():
    # Configure static folder for different deployment environments
    current_dir = os.path.dirname(__file__)
    possible_static_dirs = [
        'frontend/build',  # Relative to cwd (Railway)
        os.path.join(current_dir, 'frontend', 'build'),  # Relative to app.py
        '/app/frontend/build',  # Absolute path in Railway
        os.path.join(os.getcwd(), 'frontend', 'build'),  # Current working directory
    ]

    static_dir = None
    for path in possible_static_dirs:
        if os.path.exists(path) and os.path.isdir(path):
            static_dir = path
            break

    if not static_dir:
        print("WARNING: No static directory found!")
        static_dir = 'frontend/build'  # Fallback

    app = Flask(__name__, static_folder=static_dir)
    print(f"Static folder configured: {app.static_folder}")
    print(f"Static folder exists: {os.path.exists(app.static_folder)}")
    if os.path.exists(app.static_folder):
        try:
            contents = os.listdir(app.static_folder)
            print(f"Static folder contents: {contents[:5]}...")  # Show first 5 items
        except Exception as e:
            print(f"Error reading static folder: {e}")
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
            redirect_uri=app.config.get('GOOGLE_REDIRECT_URI'),
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

        # Check static files first
        if path and path.startswith('static/'):
            static_path = os.path.join(app.static_folder, path)
            print(f"Static request: {path}")
            print(f"Static folder: {app.static_folder}")
            print(f"Full path: {static_path}")
            print(f"File exists: {os.path.exists(static_path)}")

            if os.path.exists(static_path):
                print(f"✅ Serving static file: {path}")
                return send_from_directory(app.static_folder, path)
            else:
                print(f"❌ Static file not found: {path}")
                print(f"Available in static folder: {os.listdir(app.static_folder) if os.path.exists(app.static_folder) else 'N/A'}")
                return f"Static file not found: {path}", 404

        # For all other routes, serve index.html (SPA routing)
        return send_from_directory(app.static_folder, 'index.html')
    
    # Health check endpoint
    @app.route('/api/health-check')
    def health_check():
        try:
            # Test database connection using SQLAlchemy 2.0 syntax
            with db.engine.connect() as connection:
                connection.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'disconnected: {str(e)}'

        return jsonify({
            'status': 'healthy',
            'message': 'Health Tracker API is running',
            'database': db_status,
            'environment': os.getenv('FLASK_ENV', 'production')
        })

    # Database initialization endpoint
    @app.route('/api/init-db')
    def init_db():
        try:
            with app.app_context():
                db.create_all()
            return jsonify({'status': 'success', 'message': 'Database initialized'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # Make oauth available to routes
    app.oauth = oauth

    return app

# Create app instance for gunicorn
app = create_app()

# Only create tables when running directly (not when imported by gunicorn)
if __name__ == '__main__':
    with app.app_context():
        from models import db
        db.create_all()
        print("Database tables created")

    port = int(os.getenv('PORT', 5007))
    # Run in production-like mode (no auto-restart on file changes)
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

