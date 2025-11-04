#!/bin/bash

# Run script for RAG System
# Starts backend and frontend

set -e

echo "🚀 Starting RAG System..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check if Weaviate is running
echo "Checking Weaviate..."
if ! curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
    echo "❌ Weaviate is not running. Please start it first:"
    echo "   docker start weaviate"
    echo "   # Or if not created yet:"
    echo "   docker run -d --name weaviate -p 8080:8080 -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true cr.weaviate.io/semitechnologies/weaviate:latest"
    exit 1
fi
echo "✓ Weaviate is running"
echo ""

# Start backend in background
echo "Starting backend..."
python backend.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"
echo "  Logs: tail -f backend.log"
echo ""

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Backend is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check backend.log"
        kill $BACKEND_PID
        exit 1
    fi
    sleep 1
done
echo ""

# Start frontend
echo "Starting frontend..."
echo "✓ Frontend will open in your browser"
echo ""
echo "🎉 RAG System is running!"
echo ""
echo "To stop:"
echo "  - Press Ctrl+C to stop frontend"
echo "  - Run: kill $BACKEND_PID (to stop backend)"
echo ""

streamlit run frontend.py

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
