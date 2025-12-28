#!/bin/bash
# Railway start script for Health Tracker

echo "🚀 Starting Health Tracker..."

# Start the application
PORT=${PORT:-8080}
echo "🌐 Starting with Python main.py on port $PORT..."
exec python3 main.py
