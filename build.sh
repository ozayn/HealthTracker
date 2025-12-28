#!/bin/bash
# Railway build script for Health Tracker

set -e  # Exit on any error

echo "🚀 Starting Railway build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify frontend build exists (built locally)
echo "🔍 Checking frontend build..."
if [ ! -d "frontend/build" ]; then
    echo "❌ Frontend build directory not found. Please build frontend locally first:"
    echo "   cd frontend && npm install && npm run build"
    exit 1
fi

# Verify key files exist
if [ ! -f "frontend/build/index.html" ]; then
    echo "❌ Frontend index.html not found in build directory"
    exit 1
fi

# Make sync scheduler executable
chmod +x sync_scheduler.py
echo "✅ Sync scheduler configured!"

echo "✅ Frontend build verified!"
echo "✅ Build process complete!"
