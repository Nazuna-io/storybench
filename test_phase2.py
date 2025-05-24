"""Test script for Phase 2 validation features."""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.web.services.validation_service import ValidationService
from storybench.web.repositories.file_repository import FileRepository


async def test_validation_service():
    """Test the enhanced validation service."""
    print("🧪 Testing Phase 2 Validation Service...")
    
    # Create service
    repo = FileRepository()
    service = ValidationService(repo)
    
    print("\n1. Testing basic configuration validation...")
    try:
        result = await service.validate_configuration(test_apis=False)
        print(f"✅ Basic validation: {'PASS' if result['valid'] else 'FAIL'}")
        if not result['valid']:
            print(f"   Errors: {result.get('config_errors', [])}")
    except Exception as e:
        print(f"❌ Basic validation failed: {e}")
    
    print("\n2. Testing lightweight API connectivity...")
    try:
        result = await service.validate_configuration(test_apis=True, lightweight_test=True)
        print(f"✅ Lightweight API test completed")
        
        if 'api_tests' in result:
            for provider, api_result in result['api_tests'].items():
                status = "✅ CONNECTED" if api_result.connected else "❌ FAILED"
                latency = f" ({api_result.latency_ms:.1f}ms)" if api_result.latency_ms else ""
                error = f" - {api_result.error}" if api_result.error else ""
                print(f"   {provider}: {status}{latency}{error}")
        
        if 'model_validation' in result:
            print(f"\n   Model validation results:")
            for model_result in result['model_validation']:
                status = "✅ VALID" if model_result.valid else "❌ INVALID"
                print(f"   {model_result.model_name}: {status}")
                if model_result.errors:
                    for error in model_result.errors:
                        print(f"      - {error}")
                        
    except Exception as e:
        print(f"❌ Lightweight API test failed: {e}")
    
    print("\n🎉 Phase 2 validation testing complete!")


if __name__ == "__main__":
    asyncio.run(test_validation_service())
