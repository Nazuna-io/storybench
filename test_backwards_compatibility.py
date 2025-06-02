#!/usr/bin/env python3
"""Test backwards compatibility with existing APIEvaluator usage."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test importing as if it were the old APIEvaluator
from storybench.evaluators.api_evaluator_adapter import APIEvaluator


async def test_backwards_compatibility():
    """Test that old APIEvaluator code still works."""
    print("Testing Backwards Compatibility")
    print("=" * 60)
    
    # This is how the old code would create an evaluator
    api_keys = {
        "google": os.getenv("GOOGLE_API_KEY"),
        "gemini": os.getenv("GOOGLE_API_KEY"),
    }
    
    # Old-style configuration
    model_config = {
        "provider": "google",
        "model_name": "gemini-2.5-flash-preview-05-20",
        "temperature": 1.0,
        "context_size": 1000000
    }
    
    print("\n1. Creating evaluator with old APIEvaluator pattern...")
    
    # This should work exactly like before
    evaluator = APIEvaluator(
        name="gemini-flash-generator",
        config=model_config,
        api_keys=api_keys
    )
    
    print("   ✅ Evaluator created successfully")
    
    # Test setup
    print("\n2. Testing setup...")
    setup_success = await evaluator.setup()
    
    if not setup_success:
        print("   ❌ Setup failed")
        return False
    
    print("   ✅ Setup successful")
    
    # Test generation (old code pattern)
    print("\n3. Testing generation with old pattern...")
    
    try:
        result = await evaluator.generate_response(
            prompt="Write a short poem about backwards compatibility",
            temperature=0.7,
            max_tokens=150
        )
        
        print("   ✅ Generation successful!")
        print(f"   Response: {result['response'][:100]}...")
        
        # Check that response format matches old APIEvaluator
        assert "response" in result
        assert "model" in result
        assert "provider" in result
        assert "temperature" in result
        assert "generation_time" in result
        
        print("\n4. Response format check:")
        print("   ✅ All expected fields present")
        
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
        return False
    
    await evaluator.cleanup()
    
    print("\n" + "=" * 60)
    print("✅ Backwards compatibility test PASSED!")
    print("Old APIEvaluator code works with new LiteLLM backend")
    
    return True


async def test_import_patterns():
    """Test various import patterns for backwards compatibility."""
    print("\n\nTesting Import Patterns")
    print("=" * 60)
    
    # Test 1: Direct import
    try:
        from storybench.evaluators.api_evaluator_adapter import APIEvaluator as AE1
        print("✅ Direct import works")
    except ImportError as e:
        print(f"❌ Direct import failed: {e}")
        return False
    
    # Test 2: Import with alias
    try:
        from storybench.evaluators import api_evaluator_adapter
        AE2 = api_evaluator_adapter.APIEvaluator
        print("✅ Module import works")
    except ImportError as e:
        print(f"❌ Module import failed: {e}")
        return False
    
    # Test 3: Factory function
    try:
        from storybench.evaluators.api_evaluator_adapter import create_api_evaluator
        print("✅ Factory function import works")
    except ImportError as e:
        print(f"❌ Factory import failed: {e}")
        return False
    
    # Verify they're all the same class
    assert AE1 == AE2, "Import methods should yield same class"
    
    print("\n✅ All import patterns work correctly")
    return True


async def main():
    """Run backwards compatibility tests."""
    print("StoryBench v1.5 - Backwards Compatibility Tests")
    print("=" * 60)
    
    # Check for required API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Missing GOOGLE_API_KEY in .env file")
        return False
    
    # Run tests
    compat_test = await test_backwards_compatibility()
    import_test = await test_import_patterns()
    
    if compat_test and import_test:
        print("\n🎉 All backwards compatibility tests passed!")
        print("Existing code using APIEvaluator will continue to work.")
        return True
    else:
        print("\n❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
