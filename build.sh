#!/bin/bash
# Railway build script for Health Tracker

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

echo "✅ Build process complete!"
