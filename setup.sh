#!/bin/bash

echo "🏥 Health Tracker Setup Script"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

echo "✓ Python 3 found"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo "✓ Node.js found"
echo ""

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your API credentials"
else
    echo "✓ .env file already exists"
fi

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p uploads/blood_tests

# Install frontend dependencies
echo "📥 Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API credentials"
echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
echo "3. Run 'python app.py' to start the backend server"
echo "4. In a new terminal, run 'cd frontend && npm start' to start the frontend"
echo ""
echo "Or use the restart script: ./restart.sh"
echo ""

