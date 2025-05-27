#!/usr/bin/env python3
"""Clean up empty evaluation records and improve the database state."""

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_empty_evaluations():
    """Clean up empty evaluation records."""
    print("=== Cleaning Up Empty Evaluation Records ===")
    
    # Initialize database connection
    database = await init_database()
    
    # Find all response_llm_evaluations
    all_evals = await database.response_llm_evaluations.find().to_list(None)
    print(f"Found {len(all_evals)} evaluation records")
    
    empty_evals = []
    valid_evals = []
    
    for eval_doc in all_evals:
        criteria_results = eval_doc.get("criteria_results", [])
        
        # Check if this evaluation has actual scores
        has_scores = False
        for criterion in criteria_results:
            if criterion.get("score") is not None:
                has_scores = True
                break
        
        if has_scores:
            valid_evals.append(eval_doc)
        else:
            empty_evals.append(eval_doc)
    
    print(f"Valid evaluations: {len(valid_evals)}")
    print(f"Empty evaluations: {len(empty_evals)}")
    
    if empty_evals:
        print("Removing empty evaluation records...")
        empty_ids = [eval_doc["_id"] for eval_doc in empty_evals]
        
        # Delete empty evaluations
        result = await database.response_llm_evaluations.delete_many({
            "_id": {"$in": empty_ids}
        })
        
        print(f"Deleted {result.deleted_count} empty evaluation records")
    
    print("=== Cleanup Complete ===")

async def check_local_model_responses():
    """Check if local model responses are being saved correctly."""
    print("\n=== Checking Local Model Responses ===")
    
    database = await init_database()
    
    # Check for local model responses
    local_responses = await database.responses.find({
        "model_name": {"$regex": "^local_"}
    }).to_list(None)
    
    print(f"Found {len(local_responses)} local model responses")
    
    # Group by evaluation_id
    eval_groups = {}
    for resp in local_responses:
        eval_id = resp.get("evaluation_id")
        if eval_id not in eval_groups:
            eval_groups[eval_id] = []
        eval_groups[eval_id].append(resp)
    
    print(f"Local responses grouped into {len(eval_groups)} evaluations")
    
    for eval_id, responses in eval_groups.items():
        print(f"  Evaluation {eval_id}: {len(responses)} responses")
        
        # Check if evaluation record exists
        eval_record = await database.evaluations.find_one({"_id": eval_id})
        if eval_record:
            print(f"    Status: {eval_record.get('status')}")
            print(f"    Models: {eval_record.get('models', [])}")
        else:
            print(f"    WARNING: No evaluation record found for {eval_id}")

if __name__ == "__main__":
    asyncio.run(cleanup_empty_evaluations())
    asyncio.run(check_local_model_responses())
