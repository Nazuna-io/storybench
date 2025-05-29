#!/usr/bin/env python3
"""
Quick Model Name Validation Test
================================
Tests all 13 models from api-models-list.txt to ensure model names are valid
and we can connect to each one before running the full production pipeline.
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.evaluators.api_evaluator import APIEvaluator
from storybench.web.services.lightweight_api_test import LightweightAPITester


async def load_models_from_file() -> List[Dict[str, str]]:
    """Load models from api-models-list.txt."""
    models_file = Path(__file__).parent / "api-models-list.txt"
    if not models_file.exists():
        raise Exception(f"Models file not found: {models_file}")
        
    models = []
    current_provider = None
    
    with open(models_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if line.endswith(':'):
                current_provider = line[:-1].lower()
                # Convert Google to gemini for API provider name
                if current_provider == "google":
                    current_provider = "gemini"
            elif current_provider:
                models.append({
                    "provider": current_provider,
                    "model_name": line
                })
    
    return models


async def check_api_keys() -> Dict[str, str]:
    """Check which API keys are available."""
    api_keys = {}
    
    # Map providers to their environment variable names
    provider_env_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY", 
        "gemini": "GOOGLE_API_KEY",
        "deepinfra": "DEEPINFRA_API_KEY"
    }
    
    print("🔑 CHECKING API KEYS:")
    print("-" * 30)
    
    for provider, env_var in provider_env_map.items():
        api_key = os.getenv(env_var)
        if api_key:
            api_keys[provider] = api_key
            print(f"   ✅ {provider}: {env_var} found")
        else:
            print(f"   ❌ {provider}: {env_var} missing")
    
    return api_keys


async def test_provider_connectivity(api_keys: Dict[str, str]) -> Dict[str, bool]:
    """Test basic connectivity to each provider."""
    print(f"\n🔧 TESTING PROVIDER CONNECTIVITY:")
    print("-" * 40)
    
    connectivity_results = {}
    
    for provider in ["anthropic", "openai", "gemini", "deepinfra"]:
        if provider not in api_keys:
            print(f"   ⏭️  {provider}: Skipped (no API key)")
            connectivity_results[provider] = False
            continue
        
        try:
            connected, error, latency = await LightweightAPITester.test_provider(provider, api_keys[provider])
            if connected:
                print(f"   ✅ {provider}: Connected ({latency:.0f}ms)")
                connectivity_results[provider] = True
            else:
                print(f"   ❌ {provider}: Failed - {error}")
                connectivity_results[provider] = False
        except Exception as e:
            print(f"   ❌ {provider}: Exception - {str(e)}")
            connectivity_results[provider] = False
    
    return connectivity_results


async def validate_individual_models(models: List[Dict[str, str]], api_keys: Dict[str, str], connectivity_results: Dict[str, bool]) -> Dict[str, Tuple[bool, str]]:
    """Test each individual model by attempting a simple generation."""
    print(f"\n🧪 TESTING INDIVIDUAL MODEL NAMES:")
    print("-" * 45)
    
    model_results = {}
    
    for i, model in enumerate(models, 1):
        provider = model["provider"]
        model_name = model["model_name"]
        model_key = f"{provider}/{model_name}"
        
        # Skip if provider isn't connected
        if not connectivity_results.get(provider, False):
            print(f"   [{i:2d}/13] ⏭️  {model_key}: Skipped (provider not connected)")
            model_results[model_key] = (False, "Provider not connected")
            continue
        
        try:
            # Create test configuration
            model_config = {
                "provider": provider,
                "model_name": model_name,
                "temperature": 0.5,
            }
            
            # Provider-specific token parameter handling
            if provider == "openai" and (model_name.startswith("o3") or model_name.startswith("o4")):
                model_config["max_completion_tokens"] = 50
            else:
                model_config["max_tokens"] = 50
            
            # Create and test evaluator
            test_evaluator = APIEvaluator(f"test-{provider}-{model_name}", model_config, api_keys)
            
            # Test setup
            setup_success = await test_evaluator.setup()
            if not setup_success:
                print(f"   [{i:2d}/13] ❌ {model_key}: Setup failed")
                model_results[model_key] = (False, "Setup failed")
                await test_evaluator.cleanup()
                continue
            
            # Test generation with a simple prompt
            test_prompt = "Respond with just the word 'Hello'"
            response_result = await test_evaluator.generate_response(
                prompt=test_prompt,
                temperature=1.0,
                max_tokens=20
            )
            
            if response_result and "response" in response_result:
                response_text = response_result["response"].strip()
                generation_time = response_result.get("generation_time", 0)
                print(f"   [{i:2d}/13] ✅ {model_key}: Valid (response: '{response_text[:20]}...', {generation_time:.2f}s)")
                model_results[model_key] = (True, f"Valid - responded in {generation_time:.2f}s")
            else:
                print(f"   [{i:2d}/13] ❌ {model_key}: No response generated")
                model_results[model_key] = (False, "No response generated")
            
            # Clean up
            await test_evaluator.cleanup()
            
        except Exception as e:
            error_msg = str(e)
            print(f"   [{i:2d}/13] ❌ {model_key}: Error - {error_msg[:60]}...")
            model_results[model_key] = (False, error_msg)
            
            # Try to cleanup if evaluator was created
            try:
                await test_evaluator.cleanup()
            except:
                pass
        
        # Small delay to avoid rate limits
        await asyncio.sleep(1)
    
    return model_results


async def main():
    """Run the quick model validation test."""
    print("\n" + "=" * 60)
    print(" QUICK MODEL VALIDATION TEST")
    print(" Testing all 13 models from api-models-list.txt")
    print("=" * 60)
    
    try:
        # Load models
        models = await load_models_from_file()
        print(f"📋 Loaded {len(models)} models from api-models-list.txt")
        
        # Check API keys
        api_keys = await check_api_keys()
        
        # Test provider connectivity
        connectivity_results = await test_provider_connectivity(api_keys)
        
        # Test individual models
        model_results = await validate_individual_models(models, api_keys, connectivity_results)
        
        # Summary
        print(f"\n📊 VALIDATION SUMMARY:")
        print("-" * 25)
        
        valid_models = [k for k, (valid, _) in model_results.items() if valid]
        invalid_models = [k for k, (valid, _) in model_results.items() if not valid]
        
        print(f"   ✅ Valid models: {len(valid_models)}/13")
        print(f"   ❌ Invalid models: {len(invalid_models)}/13")
        
        if valid_models:
            print(f"\n✅ VALID MODELS ({len(valid_models)}):")
            for model_key in valid_models:
                print(f"   - {model_key}")
        
        if invalid_models:
            print(f"\n❌ INVALID MODELS ({len(invalid_models)}):")
            for model_key in invalid_models:
                _, reason = model_results[model_key]
                print(f"   - {model_key}: {reason}")
        
        # Final recommendation
        if len(valid_models) == 13:
            print(f"\n🎉 ALL MODELS VALIDATED!")
            print("   Ready to run the full production pipeline.")
        elif len(valid_models) >= 10:
            print(f"\n⚠️  MOSTLY READY ({len(valid_models)}/13 models valid)")
            print("   You can run the pipeline with the valid models, or fix the invalid ones first.")
        else:
            print(f"\n❌ SIGNIFICANT ISSUES ({len(valid_models)}/13 models valid)")
            print("   Please fix the model name or API key issues before running the full pipeline.")
        
        print(f"\n📅 Validation completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {str(e)}")
        return False
    
    return len(valid_models) >= 10  # Return True if most models are working


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
