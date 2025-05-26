#!/usr/bin/env python3
"""Test the evaluation process to see where it's failing."""

import asyncio
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.database.connection import init_database
from storybench.database.services.sequence_evaluation_service import SequenceEvaluationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_evaluation_process():
    """Test the evaluation process to debug issues."""
    print("=== Testing Evaluation Process ===")
    
    # Initialize database connection
    database = await init_database()
    
    # Check if we have OpenAI API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY not found in environment")
        return
    
    print(f"OpenAI API key found: {openai_api_key[:10]}...")
    
    # Create sequence evaluation service
    service = SequenceEvaluationService(database, openai_api_key)
    
    # Check if we have active criteria
    criteria = await service.criteria_repo.find_active()
    if not criteria:
        print("ERROR: No active evaluation criteria found")
        return
    
    print(f"Found active criteria: {criteria.version}")
    print(f"Criteria: {list(criteria.criteria.keys())}")
    
    # Check responses in database
    all_responses = await service.response_repo.find_many({})
    print(f"Found {len(all_responses)} responses in database")
    
    if len(all_responses) == 0:
        print("No responses to evaluate")
        return
    
    # Check for existing evaluations
    existing_evals = await database.response_llm_evaluations.find().to_list(None)
    print(f"Found {len(existing_evals)} existing evaluations")
    
    # Try running the evaluation service
    try:
        print("Starting evaluation process...")
        result = await service.evaluate_all_sequences()
        print(f"Evaluation result: {result}")
        
        # Check if evaluations were created
        new_evals = await database.response_llm_evaluations.find().to_list(None)
        print(f"After evaluation: {len(new_evals)} evaluations in database")
        
        if len(new_evals) > len(existing_evals):
            print(f"SUCCESS: Created {len(new_evals) - len(existing_evals)} new evaluations")
            
            # Show a sample evaluation
            sample_eval = new_evals[-1]
            print(f"Sample evaluation:")
            print(f"  Response ID: {sample_eval.get('response_id')}")
            print(f"  Evaluator: {sample_eval.get('evaluating_llm_model')}")
            print(f"  Criteria results: {len(sample_eval.get('criteria_results', []))}")
            if sample_eval.get('criteria_results'):
                first_criterion = sample_eval['criteria_results'][0]
                print(f"  First criterion: {first_criterion.get('criterion_name')} = {first_criterion.get('score')}")
        else:
            print("No new evaluations were created")
            
    except Exception as e:
        print(f"ERROR during evaluation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_evaluation_process())
