#!/usr/bin/env python3
"""Test the fixes we've implemented."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.database.connection import init_database

async def test_results_page_data():
    """Test that the results page can now load data properly."""
    print("=== Testing Results Page Data ===")
    
    database = await init_database()
    
    # Import the results service
    from storybench.web.services.database_results_service import DatabaseResultsService
    
    # Create results service
    results_service = DatabaseResultsService(database)
    
    # Get results
    try:
        results = await results_service.get_all_results()
        print(f"✅ Successfully loaded {len(results)} results")
        
        if results:
            # Show sample result
            sample = results[0]
            print(f"Sample result:")
            print(f"  Model: {sample.get('model_name')}")
            print(f"  Status: {sample.get('status')}")
            print(f"  Scores: {sample.get('scores')}")
            print(f"  Progress: {sample.get('progress_percent')}%")
        
        return True
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        return False

async def test_local_model_config():
    """Test that local model configuration can be saved/loaded."""
    print("\n=== Testing Local Model Configuration ===")
    
    database = await init_database()
    
    # Import the local model service
    from storybench.web.services.local_model_service import LocalModelService
    
    # Create local model service
    service = LocalModelService(database)
    
    # Test loading configuration
    try:
        config = await service.load_configuration()
        print(f"✅ Successfully loaded local model configuration")
        print(f"  Generation model: {config.get('generation_model', {}).get('repo_id', 'Not set')}")
        print(f"  Use local evaluator: {config.get('use_local_evaluator', False)}")
        
        # Test saving configuration
        test_config = {
            "generation_model": {
                "repo_id": "test/repo",
                "filename": "test.gguf",
                "subdirectory": ""
            },
            "evaluation_model": {
                "repo_id": "test/eval",
                "filename": "eval.gguf", 
                "subdirectory": ""
            },
            "use_local_evaluator": True,
            "settings": {
                "temperature": 1.0,
                "max_tokens": 4096,
                "num_runs": 2,
                "vram_limit_percent": 70,
                "auto_evaluate": True
            }
        }
        
        await service.save_configuration(test_config)
        print("✅ Successfully saved test configuration")
        
        # Load it back to verify
        loaded_config = await service.load_configuration()
        if loaded_config.get('generation_model', {}).get('repo_id') == 'test/repo':
            print("✅ Configuration persistence working correctly")
        else:
            print("❌ Configuration persistence failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Error with local model configuration: {e}")
        return False

async def run_all_tests():
    """Run all tests."""
    print("🧪 Running Storybench Fix Tests\n")
    
    test1_pass = await test_results_page_data()
    test2_pass = await test_local_model_config()
    
    print(f"\n📊 Test Results:")
    print(f"  Results Page Data: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"  Local Model Config: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    if test1_pass and test2_pass:
        print("\n🎉 All tests passed! The fixes are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
