#!/bin/bash

# Comprehensive Test Runner with Coverage for Storybench Web UI
echo "🧪 Storybench Comprehensive Test Runner"

# Activate virtual environment
if [ -d "venv-storybench" ]; then
    echo "🐍 Activating virtual environment..."
    source venv-storybench/bin/activate
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
else
    echo "⚠️  Virtual environment not found at venv-storybench/"
    echo "   Creating virtual environment..."
    python3 -m venv venv-storybench
    source venv-storybench/bin/activate
    pip install -r src/requirements-dev.txt
fi

export TEST_ENV=true

# Create reports directory
mkdir -p tests/reports/coverage
mkdir -p tests/reports/screenshots

# Function to check server status
check_servers() {
    echo "📡 Checking server status..."
    
    # Check backend
    if ! curl -s http://localhost:8000/api/health > /dev/null; then
        echo "❌ Backend server not running on http://localhost:8000"
        echo "   Start backend with: uvicorn storybench.web.main:app --host 0.0.0.0 --port 8000 --reload"
        return 1
    fi
    
    # Check frontend  
    if ! curl -s http://localhost:5175 > /dev/null; then
        echo "❌ Frontend server not running on http://localhost:5175"
        return 1
    fi
    
    echo "✅ Both servers are running"
    return 0
}

# Function to restart frontend
restart_frontend() {
    echo "🔄 Restarting frontend..."
    
    # Kill existing processes
    pkill -f "vite" 2>/dev/null || true
    sleep 2
    
    # Start frontend
    cd frontend
    npm run dev > ../tests/reports/frontend.log 2>&1 &
    cd ..
    
    # Wait for startup
    echo "⏳ Waiting for frontend..."
    for i in {1..30}; do
        if curl -s http://localhost:5175 > /dev/null; then
            echo "✅ Frontend started"
            return 0
        fi
        sleep 1
    done
    
    echo "❌ Frontend failed to start"
    return 1
}

# Function to run tests with coverage
run_with_coverage() {
    local test_type=$1
    local test_path=$2
    
    echo "📊 Running ${test_type} tests with coverage..."
    
    coverage run \
        --source=src/storybench \
        --data-file="tests/reports/coverage/.coverage_${test_type}" \
        --parallel-mode \
        -m pytest "${test_path}" \
        -v \
        --tb=short \
        --html="tests/reports/${test_type}_report.html" \
        --self-contained-html
        
    return $?
}

# Function to generate coverage report
generate_coverage_report() {
    echo "📈 Generating coverage report..."
    
    cd tests/reports/coverage
    coverage combine .coverage_* 2>/dev/null || true
    
    coverage report --show-missing
    coverage html -d html_report
    
    # Get coverage percentage
    COVERAGE_PERCENT=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//' | head -1)
    
    echo "📊 Total Coverage: ${COVERAGE_PERCENT}%"
    
    if (( $(echo "${COVERAGE_PERCENT:-0} >= 50" | bc -l 2>/dev/null || echo "0") )); then
        echo "✅ Coverage target met (≥50%): ${COVERAGE_PERCENT}%"
    else
        echo "⚠️  Coverage below target (<50%): ${COVERAGE_PERCENT}%"
    fi
    
    cd ../../..
}

# Main script logic
case "${1:-all}" in
    "unit")
        echo "🔍 Running unit tests..."
        run_with_coverage "unit" "tests/test_unit_services.py tests/test_basic.py"
        generate_coverage_report
        ;;
    "api")
        if check_servers; then
            echo "🔍 Running API tests..."
            run_with_coverage "api" "tests/test_api_health.py tests/test_comprehensive_backend.py"
            generate_coverage_report
        else
            exit 1
        fi
        ;;
    "backend")
        echo "🔍 Running backend tests..."
        run_with_coverage "backend" "tests/test_unit_services.py tests/test_api_health.py tests/test_comprehensive_backend.py tests/test_basic.py"
        generate_coverage_report
        ;;
    "frontend")
        echo "🔍 Running frontend tests..."
        if ! check_servers; then
            restart_frontend
        fi
        if check_servers; then
            run_with_coverage "frontend" "tests/frontend/selenium/"
            generate_coverage_report
        else
            echo "❌ Cannot run frontend tests - servers unavailable"
            exit 1
        fi
        ;;
    "fix-frontend")
        restart_frontend
        ;;
    "all")
        echo "🚀 Running comprehensive test suite..."
        
        # Backend tests (don't need servers)
        echo "1️⃣ Backend tests..."
        run_with_coverage "backend" "tests/test_unit_services.py tests/test_basic.py tests/test_cli.py"
        
        # API tests (need backend)
        if check_servers || [ "$2" = "--skip-servers" ]; then
            echo "2️⃣ API tests..."
            run_with_coverage "api" "tests/test_api_health.py tests/test_comprehensive_backend.py"
            
            # Frontend tests
            echo "3️⃣ Frontend tests..."
            run_with_coverage "frontend" "tests/frontend/selenium/"
        else
            echo "⚠️  Skipping server-dependent tests"
        fi
        
        generate_coverage_report
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo "Commands:"
        echo "  unit        - Unit tests only"
        echo "  api         - API tests (needs servers)"
        echo "  backend     - All backend tests"
        echo "  frontend    - Frontend tests (starts frontend if needed)"
        echo "  fix-frontend- Restart frontend server"
        echo "  all         - Complete test suite"
        echo "  help        - Show this help"
        ;;
    *)
        echo "❌ Unknown command. Use 'help' for options."
        exit 1
        ;;
esac

echo "✅ Test run completed!"
echo "📊 Coverage report: tests/reports/coverage/html_report/index.html"
