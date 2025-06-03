#!/usr/bin/env python3
"""
Test runner for StoryBench v1.5
Runs comprehensive test suite and generates report
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def run_tests():
    """Run the complete test suite."""
    print("🧪 StoryBench v1.5 Test Suite")
    print("=" * 50)
    
    test_files = [
        "tests/test_comprehensive_v15.py",
        "tests/dashboard/test_dashboard_pages.py", 
        "tests/test_integration_v15.py"
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue
            
        print(f"\n🔍 Running {test_file}...")
        print("-" * 30)
        
        try:
            # Run pytest on the specific file
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v", 
                "--tb=short",
                "--disable-warnings"
            ], capture_output=True, text=True, timeout=300)
            
            output = result.stdout + result.stderr
            print(output)
            
            # Parse pytest output to count tests
            lines = output.split('\n')
            for line in lines:
                if " passed" in line or " failed" in line:
                    if "passed" in line:
                        passed = int(line.split()[0]) if line.split()[0].isdigit() else 0
                        passed_tests += passed
                        total_tests += passed
                    if "failed" in line:
                        failed = int(line.split()[0]) if line.split()[0].isdigit() else 0
                        failed_tests += failed
                        total_tests += failed
                        
            if result.returncode == 0:
                print(f"✅ {test_file} - All tests passed")
            else:
                print(f"❌ {test_file} - Some tests failed")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} - Tests timed out after 5 minutes")
            failed_tests += 1
        except Exception as e:
            print(f"💥 {test_file} - Error running tests: {e}")
            failed_tests += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! StoryBench v1.5 is ready for production.")
        return 0
    else:
        print(f"\n⚠️  {failed_tests} tests failed. Please review the output above.")
        return 1

def test_basic_imports():
    """Test that basic imports work."""
    print("🔍 Testing basic imports...")
    
    try:
        # Test configuration system
        from storybench.config_loader import ConfigLoader
        print("✅ ConfigLoader import successful")
        
        # Test LiteLLM evaluator
        from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator
        print("✅ LiteLLMEvaluator import successful")
        
        # Test adapter
        from storybench.evaluators.api_evaluator_adapter import APIEvaluatorAdapter
        print("✅ APIEvaluatorAdapter import successful")
        
        # Test dashboard data service
        sys.path.insert(0, str(Path(__file__).parent / "streamlit_dashboard"))
        from data_service import DataService
        print("✅ DataService import successful")
        
        # Test dashboard pages
        from pages import overview, rankings, criteria, providers, progress, explorer
        print("✅ All dashboard pages import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return False

def check_required_files():
    """Check that all required files exist."""
    print("📁 Checking required files...")
    
    required_files = [
        "config/models.yaml",
        "run_automated_evaluation.py",
        "streamlit_dashboard/app.py",
        "streamlit_dashboard/data_service.py",
        "src/storybench/config_loader.py",
        "src/storybench/evaluators/litellm_evaluator.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  {len(missing_files)} required files are missing!")
        return False
    else:
        print("\n✅ All required files present")
        return True

def main():
    """Main test runner."""
    start_time = time.time()
    
    print("🚀 StoryBench v1.5 - Comprehensive Test Suite")
    print("=" * 60)
    
    # Check files first
    if not check_required_files():
        print("\n💥 Cannot proceed - missing required files")
        return 1
    
    # Test basic imports
    if not test_basic_imports():
        print("\n💥 Cannot proceed - import errors")
        return 1
    
    print("\n✅ Basic checks passed, proceeding with full test suite...")
    
    # Run full test suite
    result = run_tests()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n⏱️  Total test time: {duration:.2f} seconds")
    
    return result

if __name__ == "__main__":
    sys.exit(main())
