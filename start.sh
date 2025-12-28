#!/bin/bash
# Railway start script for Health Tracker

echo "🚀 Starting Health Tracker..."

# Start the application directly with Python for testing
PORT=${PORT:-8080}
echo "🌐 Starting with Python on port $PORT..."
exec python3 -c "
import os
os.environ['PORT'] = '$PORT'
from app import app
app.run(host='0.0.0.0', port=int('$PORT'), debug=False)
"
