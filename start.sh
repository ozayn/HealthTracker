#!/bin/bash
# Railway start script for Health Tracker

echo "🚀 Starting Health Tracker..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "
import sys
sys.path.append('.')
from app import create_app
app = create_app()
with app.app_context():
    from models import db
    db.create_all()
    print('Database initialized successfully')
" || echo "Database init failed, continuing..."

# Start the application
PORT=${PORT:-8080}
echo "🌐 Starting Gunicorn server on port $PORT..."
echo "Using gunicorn command: gunicorn --chdir . app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 30"
exec gunicorn --chdir . app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 30
