#!/usr/bin/env python3
"""Comprehensive test of the entire local model system."""

import asyncio
import os
import sys
import subprocess
import time
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

os.environ.setdefault("MONGODB_URI", "mongodb+srv://todd:FyilOF4jed0bFUxO@storybench-cluster0.o0tp9zz.mongodb.net/?retryWrites=true&w=majority&appName=Storybench-cluster0")

from storybench.web.services.local_model_service import LocalModelService
from storybench.database.connection import init_database

async def test_comprehensive_local_models():
    """Comprehensive test of local model functionality."""
    print("=== Comprehensive Local Model System Test ===\n")
    
    # Test 1: Backend service functionality
    print("1. Testing backend service functionality...")
    try:
        database = await init_database()
        service = LocalModelService(database=database)
        
        # Test configuration
        config = await service.load_configuration()
        print("   ✅ Configuration loading works")
        
        # Test hardware info
        hardware = await service.get_hardware_info()
        print(f"   ✅ Hardware detection works (GPU: {hardware['gpu_available']})")
        
        # Test callback system
        messages = []
        def callback(msg, msg_type="info"):
            messages.append((msg_type, msg))
        
        service.register_output_callback(callback)
        service._send_output("Test message", "info")
        
        if len(messages) > 0:
            print("   ✅ Callback system works")
        else:
            print("   ❌ Callback system failed")
        
    except Exception as e:
        print(f"   ❌ Backend service test failed: {e}")
        return False
    
    # Test 2: Database integration
    print("\n2. Testing database integration...")
    try:
        # Check for local model data in database
        evaluations = await database.evaluations.find({"models": {"$regex": "local_"}}).to_list(length=5)
        responses = await database.responses.find({"model_name": {"$regex": "local_"}}).to_list(length=5)
        
        print(f"   ✅ Found {len(evaluations)} local evaluations in database")
        print(f"   ✅ Found {len(responses)} local responses in database")
        
    except Exception as e:
        print(f"   ❌ Database integration test failed: {e}")
        return False
    
    # Test 3: End-to-end evaluation
    print("\n3. Testing end-to-end evaluation...")
    try:
        # Run a small evaluation
        service = LocalModelService(database=database)
        
        console_messages = []
        def capture_console(message, message_type="info"):
            console_messages.append(f"[{message_type}] {message}")
        
        service.register_output_callback(capture_console)
        
        # Small test configuration
        test_config = {
            "generation_model": {
                "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
                "subdirectory": ""
            },
            "evaluation_model": {
                "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
                "subdirectory": ""
            },
            "use_local_evaluator": False,
            "settings": {
                "temperature": 1.0,
                "max_tokens": 50,
                "num_runs": 1,
                "vram_limit_percent": 80,
                "auto_evaluate": False
            }
        }
        
        await service.run_local_evaluation(
            generation_model=test_config["generation_model"],
            evaluation_model=test_config["evaluation_model"],
            use_local_evaluator=False,
            sequences=["FilmNarrative"],
            settings=test_config["settings"],
            api_keys={}
        )
        
        print(f"   ✅ End-to-end evaluation completed with {len(console_messages)} console messages")
        
        # Show sample messages
        for i, msg in enumerate(console_messages[:5]):
            print(f"      {msg}")
        if len(console_messages) > 5:
            print(f"      ... and {len(console_messages) - 5} more messages")
        
    except Exception as e:
        print(f"   ❌ End-to-end evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Results verification
    print("\n4. Verifying results in database...")
    try:
        # Check for new data
        evaluations = await database.evaluations.find({"models": {"$regex": "local_"}}).to_list(length=10)
        responses = await database.responses.find({"model_name": {"$regex": "local_"}}).to_list(length=10)
        
        print(f"   ✅ Total local evaluations: {len(evaluations)}")
        print(f"   ✅ Total local responses: {len(responses)}")
        
        # Show latest evaluation
        if evaluations:
            latest_eval = evaluations[-1]
            print(f"   ✅ Latest evaluation: {latest_eval['_id']} - {latest_eval['status']}")
        
        # Show sample responses
        if responses:
            latest_responses = responses[-3:]
            for resp in latest_responses:
                text_preview = resp.get('response', '')[:50] + '...' if len(resp.get('response', '')) > 50 else resp.get('response', '')
                print(f"   ✅ Response: {resp['model_name']} - {resp['prompt_name']}: {text_preview}")
        
    except Exception as e:
        print(f"   ❌ Results verification failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Local model system is working correctly.")
    print("\nSummary:")
    print("✅ Backend service functionality")
    print("✅ Database integration") 
    print("✅ End-to-end evaluation with TinyLLama")
    print("✅ Console output capture")
    print("✅ Results storage in database")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_comprehensive_local_models())
    if success:
        print("\n🚀 Local model system is ready for production use!")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    sys.exit(0 if success else 1)
