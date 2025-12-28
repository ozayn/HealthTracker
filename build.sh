#!/bin/bash
# Railway build script for Health Tracker

set -e  # Exit on any error

echo "🚀 Starting Railway build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Build the React frontend
echo "⚛️  Building React frontend..."
cd frontend
npm install
npm run build
cd ..

# Verify frontend build exists
if [ ! -d "frontend/build" ]; then
    echo "❌ Frontend build failed - build directory not found"
    exit 1
fi

echo "✅ Build process complete!"
