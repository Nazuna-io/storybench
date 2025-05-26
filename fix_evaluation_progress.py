#!/usr/bin/env python3
"""Fix completed_tasks for existing evaluations."""

import sys
import os
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
from storybench.database.connection import init_database
from storybench.database.services.evaluation_runner import DatabaseEvaluationRunner

load_dotenv()

async def fix_evaluation_progress():
    """Fix completed_tasks for all evaluations."""
    print("🔧 Fixing evaluation progress tracking...")
    
    db = await init_database()
    runner = DatabaseEvaluationRunner(db)
    
    # Get all evaluations
    evaluations = await db['evaluations'].find({}).to_list(None)
    
    for evaluation in evaluations:
        eval_id = evaluation['_id']
        current_completed = evaluation.get('completed_tasks', 0)
        
        # Count actual responses
        actual_count = await db['responses'].count_documents({'evaluation_id': str(eval_id)})
        
        if current_completed != actual_count:
            print(f"Fixing evaluation {eval_id}:")
            print(f"  Before: {current_completed} completed_tasks")
            print(f"  Actual: {actual_count} responses")
            
            # Update the evaluation record
            await db['evaluations'].update_one(
                {'_id': eval_id},
                {'$set': {'completed_tasks': actual_count}}
            )
            
            print(f"  ✅ Updated to {actual_count} completed_tasks")
        else:
            print(f"✅ Evaluation {eval_id} already correct ({actual_count} tasks)")
    
    print("🎉 All evaluations fixed!")

if __name__ == "__main__":
    asyncio.run(fix_evaluation_progress())
