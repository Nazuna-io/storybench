#!/usr/bin/env python3
"""Test LiteLLM integration with LangChain context management."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.evaluators.litellm_evaluator import LiteLLMEvaluator, create_litellm_evaluator
from storybench.config_loader import load_config


async def test_litellm_basic():
    """Test basic LiteLLM functionality."""
    print("Testing LiteLLM Basic Functionality")
    print("=" * 60)
    
    # Load API keys
    api_keys = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "gemini": os.getenv("GOOGLE_API_KEY"),
        "google": os.getenv("GOOGLE_API_KEY"),
        "deepinfra": os.getenv("DEEPINFRA_API_KEY"),
    }
    
    # Test with a simple model (Gemini Flash for speed)
    print("\n1. Testing with Gemini Flash...")
    
    evaluator = create_litellm_evaluator(
        name="test-gemini-flash",
        provider="google",
        model_name="gemini-2.5-flash-preview-05-20",
        api_keys=api_keys,
        context_size=1000000
    )
    
    # Test setup
    print("   Testing setup...")
    setup_success = await evaluator.setup()
    
    if not setup_success:
        print("❌ Setup failed! Check your API keys.")
        return False
    
    print("   ✅ Setup successful!")
    
    # Test generation
    print("\n2. Testing generation...")
    try:
        response = await evaluator.generate_response(
            prompt="Write a haiku about code testing.",
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"   ✅ Generated response:")
        print(f"   {response['response']}")
        print(f"\n   Generation time: {response['generation_time']:.2f}s")
        print(f"   Context stats: {response['context_stats']['estimated_tokens']} tokens")
        
        if 'usage' in response:
            print(f"   Token usage: {response['usage']['prompt_tokens']} prompt, "
                  f"{response['usage']['completion_tokens']} completion")
            if response['usage'].get('cost'):
                print(f"   Cost: ${response['usage']['cost']:.4f}")
    
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False
    
    # Cleanup
    await evaluator.cleanup()
    
    return True


async def test_context_accumulation():
    """Test that context accumulates properly with LangChain."""
    print("\n\nTesting Context Accumulation")
    print("=" * 60)
    
    api_keys = {
        "gemini": os.getenv("GOOGLE_API_KEY"),
        "google": os.getenv("GOOGLE_API_KEY"),
    }
    
    evaluator = create_litellm_evaluator(
        name="test-context",
        provider="google",
        model_name="gemini-2.5-flash-preview-05-20",
        api_keys=api_keys,
        context_size=1000000
    )
    
    if not await evaluator.setup():
        print("❌ Setup failed!")
        return False
    
    # Generate a sequence of responses
    prompts = [
        "My name is Alice and I love programming.",
        "What is my name?",
        "What do I love?"
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n{i}. Prompt: {prompt}")
        
        response = await evaluator.generate_response(
            prompt=prompt,
            temperature=0.3,
            max_tokens=100
        )
        
        print(f"   Response: {response['response']}")
        print(f"   Context size: {response['context_stats']['estimated_tokens']} tokens")
    
    await evaluator.cleanup()
    
    # Check if context was maintained (should remember Alice)
    if "Alice" in response['response'] or "programming" in response['response']:
        print("\n✅ Context maintained across turns!")
        return True
    else:
        print("\n❌ Context not maintained properly")
        return False


async def test_all_providers():
    """Test all configured providers."""
    print("\n\nTesting All Providers")
    print("=" * 60)
    
    # Load configuration
    config = load_config("config/models.yaml")
    api_keys = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "gemini": os.getenv("GOOGLE_API_KEY"),
        "google": os.getenv("GOOGLE_API_KEY"),
        "deepinfra": os.getenv("DEEPINFRA_API_KEY"),
    }
    
    # Test one model from each provider
    test_models = [
        ("anthropic", "claude-3.7-sonnet"),
        ("openai", "gpt-4o"),
        ("google", "gemini-2.5-flash"),
        ("deepinfra", "deepseek-r1")
    ]
    
    results = {}
    
    for provider, model_name in test_models:
        print(f"\nTesting {provider}/{model_name}...")
        
        # Get model config
        model_config = config.get_model(provider, model_name)
        if not model_config:
            print(f"   ❌ Model not found in config")
            results[f"{provider}/{model_name}"] = "Not configured"
            continue
        
        if not model_config.enabled:
            print(f"   ⏭️  Model disabled in config")
            results[f"{provider}/{model_name}"] = "Disabled"
            continue
        
        # Create evaluator
        try:
            evaluator = LiteLLMEvaluator(
                name=f"test-{model_config.name}",
                config={
                    "provider": provider,
                    "model_name": model_config.model_id,
                    "context_size": model_config.max_tokens
                },
                api_keys=api_keys
            )
            
            # Test setup
            if await evaluator.setup():
                # Quick generation test
                response = await evaluator.generate_response(
                    prompt="Say 'Hello from LiteLLM' in exactly 5 words.",
                    temperature=0.1,
                    max_tokens=20
                )
                
                print(f"   ✅ Success! Response: {response['response'][:50]}...")
                results[f"{provider}/{model_name}"] = "Success"
            else:
                print(f"   ❌ Setup failed")
                results[f"{provider}/{model_name}"] = "Setup failed"
            
            await evaluator.cleanup()
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results[f"{provider}/{model_name}"] = f"Error: {str(e)[:50]}"
    
    # Summary
    print("\n" + "=" * 60)
    print("PROVIDER TEST SUMMARY:")
    for model, status in results.items():
        emoji = "✅" if status == "Success" else "❌"
        print(f"  {emoji} {model}: {status}")
    
    success_count = sum(1 for s in results.values() if s == "Success")
    return success_count > 0


async def main():
    """Run all tests."""
    print("StoryBench v1.5 - LiteLLM Integration Tests")
    print("=" * 60)
    
    # Check for API keys
    required_keys = ["GOOGLE_API_KEY"]
    missing_keys = [k for k in required_keys if not os.getenv(k)]
    
    if missing_keys:
        print(f"❌ Missing required API keys: {', '.join(missing_keys)}")
        print("Please set them in your .env file")
        return False
    
    # Run tests
    tests = [
        ("Basic Functionality", test_litellm_basic),
        ("Context Accumulation", test_context_accumulation),
        ("All Providers", test_all_providers)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            results[test_name] = False
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY:")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! LiteLLM integration is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
