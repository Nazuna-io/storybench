#!/usr/bin/env python3
"""Automated test runner for local models."""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all local model tests."""
    
    # Change to the storybench directory
    os.chdir(Path(__file__).parent)
    
    print("=== Running Local Model Tests ===")
    
    # Run the specific test file
    test_file = "tests/local_models/test_local_model_service.py"
    
    # First run quick tests (without slow integration tests)
    print("\n1. Running quick tests...")
    result = subprocess.run([
        "./venv-storybench/bin/python", "-m", "pytest", 
        test_file,
        "-v",
        "-m", "not slow",  # Skip slow tests
        "--tb=short"
    ], capture_output=True, text=True)
    
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("✅ Quick tests passed!")
    else:
        print("❌ Quick tests failed!")
        return False
    
    # Then run integration tests (marked as slow)
    print("\n2. Running integration tests...")
    result = subprocess.run([
        "./venv-storybench/bin/python", "-m", "pytest", 
        test_file,
        "-v", 
        "-m", "slow",  # Only slow tests
        "--tb=short",
        "-s"  # Don't capture output for integration tests
    ], capture_output=True, text=True)
    
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("✅ Integration tests passed!")
    else:
        print("❌ Integration tests failed!")
        return False
    
    print("\n✅ All local model tests passed!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
