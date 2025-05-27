#!/usr/bin/env python3
"""Debug the local model response saving issue."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path('.') / 'src'))

from storybench.database.connection import init_database

async def debug_response_creation():
    """Debug why responses aren't being saved."""
    print("=== Debugging Response Creation ===")
    
    database = await init_database()
    
    # Test creating a simple response manually
    try:
        from storybench.database.repositories.response_repo import ResponseRepository
        from storybench.database.models import Response, ResponseStatus
        from datetime import datetime
        from bson import ObjectId
        
        response_repo = ResponseRepository(database)
        
        # Create a test response
        test_response = Response(
            evaluation_id="test_eval_id",
            model_name="test_model",
            sequence="test_sequence",
            run=1,
            prompt_index=0,
            prompt_name="test_prompt",
            prompt_text="test prompt text",
            response="test response text",
            generation_time=1.0,
            completed_at=datetime.utcnow(),
            status=ResponseStatus.COMPLETED
        )
        
        print("Creating test response...")
        created_response = await response_repo.create(test_response)
        print(f"✅ Test response created: {created_response.id}")
        
        # Now delete it
        await database.responses.delete_one({"_id": ObjectId(created_response.id)})
        print("✅ Test response cleaned up")
        
    except Exception as e:
        print(f"❌ Error creating test response: {e}")
        import traceback
        traceback.print_exc()

async def check_recent_evaluation_details():
    """Check what's wrong with the recent evaluation."""
    print("\n=== Checking Recent Evaluation Details ===")
    
    database = await init_database()
    
    # Get the most recent evaluation that has 0 responses
    problem_eval = await database.evaluations.find_one(
        {"models": {"$regex": "^local_"}},
        sort=[("started_at", -1)]
    )
    
    if problem_eval:
        eval_id = str(problem_eval.get('_id'))
        print(f"Problem evaluation: {eval_id}")
        print(f"  Models: {problem_eval.get('models')}")
        print(f"  Status: {problem_eval.get('status')}")
        print(f"  Total tasks: {problem_eval.get('total_tasks')}")
        print(f"  Completed tasks: {problem_eval.get('completed_tasks')}")
        
        # Check for responses with this evaluation ID
        responses = await database.responses.find({"evaluation_id": eval_id}).to_list(None)
        print(f"  Responses found: {len(responses)}")
        
        # Also check for responses with ObjectId version
        from bson import ObjectId
        try:
            obj_id = ObjectId(eval_id)
            responses_obj = await database.responses.find({"evaluation_id": obj_id}).to_list(None)
            print(f"  Responses with ObjectId: {len(responses_obj)}")
        except:
            print("  Could not convert to ObjectId")

if __name__ == "__main__":
    asyncio.run(debug_response_creation())
    asyncio.run(check_recent_evaluation_details())
