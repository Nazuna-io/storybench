#!/usr/bin/env python3
"""
Run evaluation specifically for DeepSeek-R1-0528 model.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import get_database
from storybench.database.services.directus_evaluation_service import DirectusEvaluationService
from storybench.clients.directus_client import DirectusClient


async def run_deepseek_evaluation():
    """Run evaluation specifically for DeepSeek-R1-0528."""
    print("DeepSeek-R1-0528 Evaluation Runner")
    print("=" * 50)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    deepinfra_key = os.getenv('DEEPINFRA_API_KEY')
    directus_url = os.getenv('DIRECTUS_URL')
    directus_token = os.getenv('DIRECTUS_TOKEN')
    
    if not openai_key:
        print("❌ OPENAI_API_KEY missing")
        return False
        
    if not deepinfra_key:
        print("❌ DEEPINFRA_API_KEY missing")
        return False
        
    print("✅ API keys loaded")
    
    if not directus_url or not directus_token:
        print("⚠️  Using mock Directus mode")
        use_directus = False
    else:
        print("✅ Directus credentials found")
        use_directus = True
    
    try:
        # Initialize database
        print("\nConnecting to database...")
        database = await get_database()
        print("✅ Database connected")
        
        # Initialize Directus client
        directus_client = DirectusClient() if use_directus else None
        
        # Initialize evaluation service
        evaluation_service = DirectusEvaluationService(
            database=database,
            openai_api_key=openai_key,
            directus_client=directus_client
        )
        print("✅ Evaluation service initialized")
        
        # Get current evaluation summary
        print("\nChecking current state...")
        summary = await evaluation_service.get_evaluation_summary()
        print(f"Current evaluations: {summary.get('total_evaluations', 0)}")
        
        # Run evaluations
        print(f"\nRunning evaluations...")
        results = await evaluation_service.evaluate_all_responses()
        
        print(f"\n📊 RESULTS:")
        print(f"   Total responses: {results['total_responses']}")
        print(f"   Unevaluated: {results['unevaluated_responses']}")
        print(f"   New evaluations: {results['evaluations_created']}")
        
        if results['errors']:
            print(f"   Errors: {len(results['errors'])}")
            for error in results['errors'][:3]:
                print(f"     - {error}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_deepseek_evaluation())
    sys.exit(0 if success else 1)
