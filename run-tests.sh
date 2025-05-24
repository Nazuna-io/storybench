#!/bin/bash

# Test runner script for Storybench Web UI
echo "🧪 Storybench Test Runner"

# Check if servers are running
echo "📡 Checking server status..."

# Check backend
if ! curl -s http://localhost:8000/api/health > /dev/null; then
    echo "❌ Backend server not running on http://localhost:8000"
    echo "   Start backend with: cd /home/todd/storybench && uvicorn storybench.web.main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi

# Check frontend
if ! curl -s http://localhost:5175 > /dev/null; then
    echo "❌ Frontend server not running on http://localhost:5175"
    echo "   Start frontend with: cd /home/todd/storybench/frontend && npm run dev"
    exit 1
fi

echo "✅ Both servers are running"

# Run tests based on argument
case "${1:-all}" in
    "api")
        echo "🔍 Running API tests..."
        python3 -m pytest tests/test_api_health.py -v
        ;;
    "selenium")
        echo "🔍 Running Selenium tests..."
        python3 -m pytest tests/frontend/selenium/ -m selenium -v
        ;;
    "integration")
        echo "🔍 Running integration tests..."
        python3 -m pytest tests/ -m integration -v
        ;;
    "all")
        echo "🔍 Running all tests..."
        python3 -m pytest tests/ -v
        ;;
    *)
        echo "Usage: $0 [api|selenium|integration|all]"
        echo "  api        - Run API health tests only"
        echo "  selenium   - Run Selenium UI tests only"
        echo "  integration- Run integration tests only"
        echo "  all        - Run all tests (default)"
        exit 1
        ;;
esac

echo "✅ Tests completed!"
