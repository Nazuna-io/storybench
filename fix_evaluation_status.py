#!/usr/bin/env python3
"""
Fix evaluation status and trigger evaluation for completed responses
"""
import asyncio
import os
import sys
sys.path.append('/home/todd/storybench/src')

from motor.motor_asyncio import AsyncIOMotorClient
from storybench.database.repositories.evaluation_repo import EvaluationRepository
from storybench.database.repositories.response_repo import ResponseRepository
from storybench.database.models import EvaluationStatus

async def fix_evaluation_status():
    print("🔧 Fixing Evaluation Status...")
    print("=" * 80)
    
    # Connect to database
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    database = client.storybench
    
    try:
        eval_repo = EvaluationRepository(database)
        response_repo = ResponseRepository(database)
        
        # Get the latest evaluation
        cursor = database.evaluations.find({}).sort("started_at", -1).limit(1)
        latest_evals = await cursor.to_list(length=1)
        if not latest_evals:
            print("❌ No evaluations found")
            return
            
        from storybench.database.models import Evaluation
        latest_eval = Evaluation(**latest_evals[0])
        print(f"📊 Latest Evaluation: {latest_eval.id}")
        print(f"  Status: {latest_eval.status}")
        print(f"  Models: {latest_eval.models}")
        print(f"  Total Tasks: {latest_eval.total_tasks}")
        print(f"  Completed Tasks: {latest_eval.completed_tasks}")
        
        # Count actual responses
        response_count = await database.responses.count_documents({
            "evaluation_id": str(latest_eval.id)
        })
        print(f"  Actual Responses: {response_count}")
        
        # Determine correct status
        if response_count == 0:
            new_status = EvaluationStatus.FAILED
            print(f"🔄 No responses found - marking as FAILED")
        elif response_count < latest_eval.total_tasks:
            new_status = EvaluationStatus.IN_PROGRESS
            print(f"🔄 Partial responses ({response_count}/{latest_eval.total_tasks}) - marking as IN_PROGRESS")
        else:
            new_status = EvaluationStatus.COMPLETED
            print(f"🔄 All responses complete - marking as COMPLETED")
        
        # Update status
        await eval_repo.update_by_id(
            latest_eval.id,
            {
                "status": new_status,
                "completed_tasks": response_count
            }
        )
        print(f"✅ Updated evaluation status to {new_status}")
        
        # If there are responses but no evaluations, we could trigger evaluation here
        if response_count > 0:
            # Check if LLM evaluations exist
            llm_eval_count = await database.llm_evaluations.count_documents({
                "response_id": {"$in": [str(r["_id"]) for r in await response_repo.find_many({"evaluation_id": str(latest_eval.id)})]}
            })
            print(f"  LLM Evaluations: {llm_eval_count}")
            
            if llm_eval_count == 0:
                print("💡 Consider running LLM evaluation on these responses")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_evaluation_status())
