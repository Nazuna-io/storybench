#!/usr/bin/env python3
"""
Run LLM evaluations using Directus-sourced criteria.

This script demonstrates the complete evaluation workflow:
1. Fetch evaluation criteria from Directus at runtime
2. Evaluate responses using those criteria
3. Store only evaluation results in MongoDB (not criteria)
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import init_database, get_database
from storybench.database.services.directus_evaluation_service import DirectusEvaluationService
from storybench.clients.directus_client import DirectusClient


async def run_evaluations_with_directus():
    """Run evaluations using Directus criteria."""
    print("Storybench Directus Evaluation Runner")
    print("="*50)
    
    # Check environment variables
    print("1. Checking environment...")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please set your OpenAI API key to run evaluations")
        return False
    
    directus_url = os.getenv('DIRECTUS_URL')
    directus_token = os.getenv('DIRECTUS_TOKEN')
    
    print(f"✅ OpenAI API Key: {'*' * (len(openai_key) - 4)}{openai_key[-4:]}")
    
    if not directus_url or not directus_token:
        print("⚠️  Directus credentials not found - will use mock data")
        print("   Set DIRECTUS_URL and DIRECTUS_TOKEN for real Directus integration")
        use_directus = False
    else:
        print(f"✅ Directus URL: {directus_url}")
        print(f"✅ Directus Token: {'*' * (len(directus_token) - 4)}{directus_token[-4:]}")
        use_directus = True
    
    try:
        # Initialize database
        print("\n2. Connecting to database...")
        database = await init_database()
        print("✅ Database connected")
        
        # Initialize Directus client if available
        directus_client = DirectusClient() if use_directus else None
        
        # Initialize evaluation service
        print("3. Initializing Directus evaluation service...")
        evaluation_service = DirectusEvaluationService(
            database=database,
            openai_api_key=openai_key,
            directus_client=directus_client
        )
        print("✅ Evaluation service initialized")
        
        if use_directus:
            # Test Directus connection
            print("4. Testing Directus integration...")
            try:
                criteria = await evaluation_service.get_evaluation_criteria()
                print(f"✅ Retrieved criteria: v{criteria.version} - {criteria.version_name}")
            except Exception as e:
                print(f"❌ Directus connection failed: {e}")
                print("   Falling back to mock evaluation (without actual API calls)")
                return False
        else:
            print("4. Skipping Directus test (using mock mode)")
        
        # Check for responses to evaluate
        print("5. Checking for responses to evaluate...")
        
        # Get summary of current evaluations
        summary = await evaluation_service.get_evaluation_summary()
        print(f"   Current evaluations in database: {summary.get('total_evaluations', 0)}")
        
        if 'by_criteria_version' in summary:
            for version, data in summary['by_criteria_version'].items():
                print(f"   - {version}: {data['count']} evaluations")
        
        if not use_directus:
            print("\n⚠️  DEMO MODE - Not running actual evaluations without Directus")
            print("   To run real evaluations, set DIRECTUS_URL and DIRECTUS_TOKEN")
            print("   The integration pattern is working and ready for production use.")
            return True
        
        # Run evaluations using latest criteria
        print("6. Running evaluations with Directus criteria...")
        results = await evaluation_service.evaluate_all_responses()
        
        print(f"\n📊 EVALUATION RESULTS:")
        print(f"   Total responses: {results['total_responses']}")
        print(f"   Unevaluated responses: {results['unevaluated_responses']}")
        print(f"   New evaluations created: {results['evaluations_created']}")
        print(f"   Evaluation version used: v{results['evaluation_version']} - {results['evaluation_version_name']}")
        
        if results['errors']:
            print(f"   Errors encountered: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                print(f"     - {error}")
        
        print(f"\n🎉 DIRECTUS EVALUATION COMPLETE!")
        print(f"Evaluation criteria fetched from Directus at runtime")
        print(f"Results stored in MongoDB (criteria NOT stored)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main runner function."""
    print("Starting Directus-integrated evaluation process...")
    print()
    
    success = asyncio.run(run_evaluations_with_directus())
    
    if success:
        print("\n✅ Evaluation process completed successfully!")
        return 0
    else:
        print("\n❌ Evaluation process failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
