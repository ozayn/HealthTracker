#!/bin/bash
# Railway start script for Health Tracker

echo "🚀 Starting Health Tracker..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
curl -f http://localhost:$PORT/api/init-db || echo "Database init failed, continuing..."

# Start the application
echo "🌐 Starting Gunicorn server..."
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 30
