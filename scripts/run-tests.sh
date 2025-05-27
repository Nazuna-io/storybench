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
    echo "❌ Frontend failed to start after 30 seconds"
    return 1
}

# Function to run tests with coverage
run_with_coverage() {
    local test_type=$1
    local test_path=$2
    local coverage_file="tests/reports/coverage/.coverage_${test_type}"
    
    echo "📊 Running ${test_type} tests with coverage..."
    
    coverage run \
        --source=src/storybench \
        --data-file="${coverage_file}" \
        --parallel-mode \
        -m pytest "${test_path}" \
        -v \
        --tb=short \
        --html=tests/reports/${test_type}_report.html \
        --self-contained-html \
        --junitxml=tests/reports/${test_type}_junit.xml
        
    return $?
}

# Function to generate coverage report
generate_coverage_report() {
    echo "📈 Generating coverage report..."
    
    # Combine coverage data
    cd tests/reports/coverage
    coverage combine .coverage_*
    
    # Generate reports
    coverage report --show-missing
    coverage html -d html_report
    coverage xml -o coverage.xml
    
    # Calculate coverage percentage
    COVERAGE_PERCENT=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
    
    echo "📊 Total Coverage: ${COVERAGE_PERCENT}%"
    
    # Check if we meet minimum coverage
    if (( $(echo "${COVERAGE_PERCENT} >= 50" | bc -l) )); then
        echo "✅ Coverage target met (≥50%): ${COVERAGE_PERCENT}%"
    else
        echo "⚠️  Coverage below target (<50%): ${COVERAGE_PERCENT}%"
        echo "   View detailed report: tests/reports/coverage/html_report/index.html"
    fi
    
    cd ../../..
}

# Function to run comprehensive test suite
run_comprehensive_tests() {
    echo "🚀 Running comprehensive test suite..."
    
    # Track test results
    local test_results=()
    
    # 1. Unit Tests
    echo "1️⃣ Running unit tests..."
    run_with_coverage "unit" "tests/test_unit_services.py tests/test_basic.py tests/test_cli.py"
    test_results+=($?)
    
    # 2. API Tests  
    echo "2️⃣ Running API tests..."
    run_with_coverage "api" "tests/test_api_health.py tests/test_comprehensive_backend.py tests/test_phase5_evaluation.py"
    test_results+=($?)
    
    # 3. Integration Tests
    echo "3️⃣ Running integration tests..."
    run_with_coverage "integration" "tests/test_progress_tracking.py tests/test_evaluators/ tests/test_models/ tests/test_utils/"
    test_results+=($?)
    
    # 4. Frontend Tests (if servers are running)
    if check_servers; then
        echo "4️⃣ Running frontend tests..."
        run_with_coverage "frontend" "tests/frontend/selenium/"
        test_results+=($?)
    else
        echo "⚠️  Skipping frontend tests - servers not available"
        test_results+=(1)
    fi
    
    # Generate coverage report
    generate_coverage_report
    
    # Summary
    echo "📋 Test Summary:"
    echo "   Unit Tests: $([ ${test_results[0]} -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")"
    echo "   API Tests: $([ ${test_results[1]} -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")"
    echo "   Integration Tests: $([ ${test_results[2]} -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")"
    echo "   Frontend Tests: $([ ${test_results[3]} -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")"
    
    # Check overall result
    local overall_result=0
    for result in "${test_results[@]}"; do
        if [ $result -ne 0 ]; then
            overall_result=1
            break
        fi
    done
    
    return $overall_result
}

# Main script logic
case "${1:-all}" in
    "unit")
        echo "🔍 Running unit tests with coverage..."
        run_with_coverage "unit" "tests/test_unit_services.py tests/test_basic.py"
        generate_coverage_report
        ;;
    "api")
        if check_servers; then
            echo "🔍 Running API tests with coverage..."
            run_with_coverage "api" "tests/test_api_health.py tests/test_comprehensive_backend.py"
            generate_coverage_report
        else
            exit 1
        fi
        ;;
    "backend")
        echo "🔍 Running all backend tests with coverage..."
        run_with_coverage "backend" "tests/test_unit_services.py tests/test_api_health.py tests/test_comprehensive_backend.py tests/test_basic.py tests/test_cli.py tests/test_phase5_evaluation.py"
        generate_coverage_report
        ;;
    "frontend")
        if check_servers; then
            echo "🔍 Running frontend tests..."
            run_with_coverage "frontend" "tests/frontend/selenium/"
            generate_coverage_report
        else
            echo "🔄 Attempting to start frontend..."
            if restart_frontend; then
                run_with_coverage "frontend" "tests/frontend/selenium/"
                generate_coverage_report
            else
                echo "❌ Could not start frontend"
                exit 1
            fi
        fi
        ;;
    "selenium")
        if check_servers; then
            echo "🔍 Running Selenium tests..."
            python3 -m pytest tests/frontend/selenium/ -v --tb=short
        else
            restart_frontend
            python3 -m pytest tests/frontend/selenium/ -v --tb=short
        fi
        ;;
    "integration")
        echo "🔍 Running integration tests..."
        run_with_coverage "integration" "tests/test_progress_tracking.py tests/test_evaluators/ tests/test_models/ tests/test_utils/"
        generate_coverage_report
        ;;
    "coverage")
        echo "📊 Generating coverage report from existing data..."
        generate_coverage_report
        ;;
    "fix-frontend")
        echo "🔧 Fixing and restarting frontend..."
        restart_frontend
        ;;
    "all")
        echo "🔍 Running comprehensive test suite..."
        run_comprehensive_tests
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  unit        - Run unit tests with coverage"
        echo "  api         - Run API tests with coverage"
        echo "  backend     - Run all backend tests with coverage"
        echo "  frontend    - Run frontend tests (restart if needed)"
        echo "  selenium    - Run Selenium tests (basic)"
        echo "  integration - Run integration tests with coverage"
        echo "  coverage    - Generate coverage report from existing data"
        echo "  fix-frontend- Restart frontend server"
        echo "  all         - Run comprehensive test suite (default)"
        echo "  help        - Show this help"
        echo ""
        echo "Reports generated in:"
        echo "  tests/reports/coverage/html_report/index.html - Coverage report"
        echo "  tests/reports/*_report.html - Test reports"
        echo "  tests/reports/frontend.log - Frontend server log"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ Tests completed successfully!"
    echo "📊 View coverage report: tests/reports/coverage/html_report/index.html"
else
    echo "❌ Some tests failed. Check reports for details."
    echo "📋 Reports available in: tests/reports/"
fi

exit $exit_code
