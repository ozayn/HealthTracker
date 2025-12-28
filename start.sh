#!/bin/bash
# Railway start script for Health Tracker

echo "🚀 Starting Health Tracker..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Initialize database (without curl since it's not available on Railway)
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
PORT=${PORT:-8080}  # Use PORT env var or default to 8080 for Railway
echo "🌐 Starting Gunicorn server on port $PORT..."
echo "Using gunicorn command: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 30"
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 30
