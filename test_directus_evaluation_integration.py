#!/usr/bin/env python3
"""
Test script to verify Directus evaluation integration.

This script tests:
1. Fetching evaluation criteria from Directus
2. Converting to Storybench format
3. Building evaluation prompts
4. Integration with the evaluation service
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.clients.directus_client import DirectusClient
from storybench.database.services.directus_evaluation_service import DirectusEvaluationService
from storybench.database.connection import get_database
from storybench.database.models import Response


async def test_directus_evaluation_integration():
    """Test the complete Directus evaluation integration."""
    print("Testing Directus Evaluation Integration")
    print("="*50)
    
    try:
        # Initialize Directus client
        print("1. Initializing Directus client...")
        directus_client = DirectusClient()
        
        # Test fetching evaluation criteria
        print("2. Fetching latest evaluation criteria from Directus...")
        evaluation_structure = await directus_client.get_latest_published_evaluation_version()
        
        if not evaluation_structure:
            print("❌ No published evaluation versions found in Directus")
            return False
        
        print(f"✅ Found evaluation version: {evaluation_structure.version_name} (v{evaluation_structure.version_number})")
        
        # Convert to Storybench format
        print("3. Converting to Storybench format...")
        storybench_format = await directus_client.convert_to_storybench_evaluation_format(evaluation_structure)
        
        print(f"✅ Converted successfully:")
        print(f"   Version: {storybench_format.version} - {storybench_format.version_name}")
        print(f"   Criteria: {list(storybench_format.criteria.keys())}")
        print(f"   Scoring guidelines: {len(storybench_format.scoring_guidelines)} characters")
        
        # Test evaluation service initialization
        print("4. Testing evaluation service initialization...")
        
        # Check for OpenAI API key
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            print("⚠️  OPENAI_API_KEY not found - skipping service test")
            print("✅ Directus integration structure test completed successfully")
            return True
        
        # Initialize database and service
        database = get_database()
        evaluation_service = DirectusEvaluationService(
            database=database,
            openai_api_key=openai_key,
            directus_client=directus_client
        )
        
        print("✅ Evaluation service initialized successfully")
        
        # Test getting criteria through service
        print("5. Testing criteria retrieval through service...")
        service_criteria = await evaluation_service.get_evaluation_criteria()
        print(f"✅ Service retrieved criteria: v{service_criteria.version} - {service_criteria.version_name}")
        
        # Test building evaluation prompt with mock response
        print("6. Testing evaluation prompt building...")
        mock_response = Response(
            model_name="test-model",
            prompt_name="Test Prompt",
            sequence="TestSequence", 
            text="This is a test creative writing response for evaluation.",
            responses=["Response 1", "Response 2", "Response 3"],
            evaluation_id="test_eval_id"
        )
        
        prompt = evaluation_service._build_evaluation_prompt(mock_response, service_criteria)
        print(f"✅ Built evaluation prompt ({len(prompt)} characters)")
        print(f"   Includes criteria: {len(service_criteria.criteria)} criteria")
        print(f"   Includes scoring guidelines: {'Yes' if service_criteria.scoring_guidelines else 'No'}")
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("Directus evaluation integration is working correctly")
        print("="*50)
        
        # Display summary of what's ready
        print("\nREADY FOR USE:")
        print(f"📋 Evaluation Criteria: v{service_criteria.version} '{service_criteria.version_name}'")
        print(f"🔍 Available Criteria: {', '.join(service_criteria.criteria.keys())}")
        print(f"📝 Scoring Guidelines: {len(service_criteria.scoring_guidelines)} characters")
        print(f"🔌 Directus Integration: ✅ Connected and working")
        print(f"🤖 LLM Service: ✅ Ready for evaluation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("Directus Evaluation Integration Test")
    print("="*50)
    
    # Check environment
    print("Checking environment...")
    
    directus_url = os.getenv('DIRECTUS_URL')
    directus_token = os.getenv('DIRECTUS_TOKEN')
    
    if not directus_url:
        print("❌ DIRECTUS_URL environment variable not set")
        return 1
    
    if not directus_token:
        print("❌ DIRECTUS_TOKEN environment variable not set")
        return 1
    
    print(f"✅ Directus URL: {directus_url}")
    print(f"✅ Directus Token: {'*' * (len(directus_token) - 4)}{directus_token[-4:]}")
    
    # Run async test
    success = asyncio.run(test_directus_evaluation_integration())
    
    if success:
        print("\n🎉 Integration test completed successfully!")
        print("The evaluation system is ready to use Directus criteria.")
        return 0
    else:
        print("\n❌ Integration test failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
