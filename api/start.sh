#!/bin/bash

# Reclaim Tasks API Startup Script

echo "🚀 Starting Reclaim Tasks API..."

# Check if RECLAIM_TOKEN is set
if [ -z "$RECLAIM_TOKEN" ]; then
    echo "❌ Error: RECLAIM_TOKEN environment variable is not set"
    echo "Please set your Reclaim API token:"
    echo "export RECLAIM_TOKEN='your_token_here'"
    exit 1
fi

echo "✅ RECLAIM_TOKEN is configured"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the api directory."
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r ../api_requirements.txt

echo "🌐 Starting server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the server
python main.py
