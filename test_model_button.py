#!/usr/bin/env python3
"""
Test the new model test button functionality
"""
import asyncio
import aiohttp
import json

async def test_model_button():
    print("🧪 Testing Model Test Button Functionality...")
    print("=" * 80)
    
    # Test data for the 6 active models
    test_models = [
        {"provider": "openai", "model_name": "gpt-4o-2024-11-20", "type": "api"},
        {"provider": "openai", "model_name": "gpt-4o-mini-2024-07-18", "type": "api"},
        {"provider": "openai", "model_name": "gpt-4.1-2025-04-14", "type": "api"},
        {"provider": "openai", "model_name": "gpt-4.1-mini-2025-04-10", "type": "api"},
        {"provider": "openai", "model_name": "gpt-4.1-nano-2025-04-10", "type": "api"},
        {"provider": "openai", "model_name": "o3-2025-04-16", "type": "api"},
    ]
    
    async with aiohttp.ClientSession() as session:
        for model in test_models:
            print(f"\n🔍 Testing {model['model_name']}...")
            
            try:
                async with session.post(
                    "http://localhost:8000/api/models/test-model",
                    json=model,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    
                    if result.get("success"):
                        print(f"  ✅ {result.get('message', 'Success')}")
                        if "test_response_length" in result:
                            print(f"     Response length: {result['test_response_length']} chars")
                    else:
                        print(f"  ❌ {result.get('error', 'Unknown error')}")
                        
            except asyncio.TimeoutError:
                print(f"  ⏰ Timeout - API call took too long")
            except Exception as e:
                print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_model_button())
