#!/bin/bash

# Restart script for Health Tracker application

echo "Stopping any running instances..."
# Kill any existing python app.py processes
pkill -f "python app.py" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true

# Wait a moment for processes to stop
sleep 2

# Check if port 5007 is still in use and kill processes
PORT_FREE=0
for i in {1..5}; do
    if lsof -i :5007 > /dev/null 2>&1; then
        echo "Port 5007 still in use (attempt $i/5). Finding and killing processes..."
        # Get PIDs using port 5007
        PIDS=$(lsof -ti :5007)
        if [ ! -z "$PIDS" ]; then
            echo "Killing processes: $PIDS"
            kill -9 $PIDS 2>/dev/null || true
        fi
        sleep 2
    else
        echo "Port 5007 is now free."
        PORT_FREE=1
        break
    fi
done

if [ $PORT_FREE -eq 0 ]; then
    echo "ERROR: Could not free port 5007 after 5 attempts. Please manually kill processes using this port."
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Starting application on port 5007..."
python app.py

# Alternative: Use gunicorn for production-like environment
# gunicorn app:app --bind 0.0.0.0:5007 --workers 2 --reload

