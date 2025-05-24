#!/bin/bash

# Development script to run both frontend and backend
echo "🚀 Starting Storybench Development Servers..."

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "❌ Please run this script from the storybench root directory"
    exit 1
fi

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo "📡 Starting FastAPI backend on http://localhost:8000"
cd "$(dirname "$0")"
source venv-storybench/bin/activate
python -m storybench.web.main &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend dev server
echo "🎨 Starting Vue.js frontend on http://localhost:5173"
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Development servers running:"
echo "   🌐 Frontend: http://localhost:5173"
echo "   📡 Backend:  http://localhost:8000"
echo "   📚 API Docs: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for background processes
wait
