"""Test the FastAPI validation endpoint."""

import asyncio
import aiohttp
import json


import pytest

@pytest.mark.asyncio
async def test_api_endpoint():
    """Test the validation API endpoint."""
    print("🌐 Testing FastAPI Validation Endpoint...")
    
    # Test data
    validation_request = {
        "test_api_connections": True,
        "validate_local_models": False,
        "lightweight_test": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test validation endpoint
            async with session.post(
                "http://localhost:8081/api/config/validate",
                json=validation_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ API endpoint responded successfully")
                    print(f"   Overall valid: {data.get('valid', False)}")
                    print(f"   Config errors: {len(data.get('config_errors', []))}")
                    print(f"   API tests: {len(data.get('api_validation', {}))}")
                    print(f"   Model validations: {len(data.get('model_validation', []))}")
                    
                    # Show API test results
                    for provider, result in data.get('api_validation', {}).items():
                        status = "✅" if result.get('connected') else "❌"
                        latency = f" ({result.get('latency_ms', 0):.1f}ms)" if result.get('latency_ms') else ""
                        print(f"   {provider}: {status}{latency}")
                        
                else:
                    print(f"❌ API endpoint failed: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    
    except aiohttp.ClientConnectorError:
        print("❌ Could not connect to API server")
        print("   Make sure to run: storybench-web")
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_api_endpoint())
