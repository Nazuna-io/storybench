#!/usr/bin/env python3
"""
Run missing LLM evaluations for ChatGPT responses using SequenceEvaluationService
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import init_database, get_database
from storybench.database.services.sequence_evaluation_service import SequenceEvaluationService
from storybench.database.repositories.criteria_repo import CriteriaRepository

async def run_missing_evaluations():
    # Load environment variables
    load_dotenv(override=True)
    
    # Initialize database
    await init_database()
    
    # Get database instance
    database = await get_database()
    
    print("🔍 Checking for missing ChatGPT evaluations...")
    
    # Initialize evaluation service
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        return
        
    sequence_eval_service = SequenceEvaluationService(database, openai_api_key)
    
    # Check if we have active criteria
    criteria_repo = CriteriaRepository(database)
    active_criteria = await criteria_repo.find_active()
    
    if not active_criteria:
        print("❌ No active evaluation criteria found!")
        print("   Please run the criteria setup first")
        return
    
    print(f"✅ Using criteria version {active_criteria.version}")
    
    # Run sequence-aware evaluations
    print("🚀 Running sequence-aware evaluations for all sequences...")
    
    try:
        eval_results = await sequence_eval_service.evaluate_all_sequences()
        
        print(f"\n🎉 Evaluation completed!")
        print(f"   ✅ Sequences evaluated: {eval_results['sequences_evaluated']}")
        print(f"   ✅ Total evaluations created: {eval_results['total_evaluations_created']}")
        print(f"   ❌ Errors: {len(eval_results.get('errors', []))}")
        
        if eval_results.get('errors'):
            print(f"   ⚠️  Error details:")
            for error in eval_results['errors'][:5]:  # Show first 5 errors
                print(f"      - {error}")
        
        # Get summary
        print(f"\n📊 Getting updated evaluation summary...")
        summary = await sequence_eval_service.get_evaluation_summary()
        
        print(f"   📝 Total responses: {summary['total_responses']}")
        print(f"   🧠 Total evaluations: {summary['total_evaluations']}")
        print(f"   📊 Evaluation coverage: {summary['evaluation_coverage']:.1%}")
        
        # Show model breakdown
        print(f"\n📈 Evaluation breakdown by model:")
        for model, stats in summary['model_stats'].items():
            coverage = (stats['evaluations'] / stats['responses'] * 100) if stats['responses'] > 0 else 0
            print(f"   {model}: {stats['evaluations']}/{stats['responses']} ({coverage:.1f}%)")
            
    except Exception as e:
        print(f"❌ Error running evaluations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_missing_evaluations())
