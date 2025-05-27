#!/usr/bin/env python3
"""
Quick database check to see current state and verify Option B is working.
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment
os.environ["MONGODB_URI"] = "mongodb+srv://todd:FyilOF4jed0bFUxO@storybench-cluster0.o0tp9zz.mongodb.net/?retryWrites=true&w=majority&appName=Storybench-cluster0"

async def check_database():
    from storybench.database.connection import init_database, get_database
    
    await init_database()
    db = await get_database()
    
    eval_count = await db.evaluations.count_documents({})
    response_count = await db.responses.count_documents({})
    
    print(f"Database state: {eval_count} evaluations, {response_count} responses")
    
    if eval_count > 0:
        # Get recent evaluations
        evals = await db.evaluations.find({}).sort("created_at", -1).limit(5).to_list(length=5)
        print(f"\nRecent evaluations:")
        for i, e in enumerate(evals):
            print(f"{i+1}. ID: {str(e['_id'])}")
            print(f"   Status: {e.get('status', 'N/A')}")
            print(f"   Tasks: {e.get('completed_tasks', 0)}/{e.get('total_tasks', 0)}")
            print(f"   Models: {e.get('models', [])}")
            
            # Check how many responses this evaluation has
            eval_responses = await db.responses.count_documents({"evaluation_id": str(e['_id'])})
            print(f"   Responses in DB: {eval_responses}")
            print()
    
    # Look for the classic Option A problem pattern
    small_evals = await db.evaluations.count_documents({"total_tasks": {"$lte": 9}})
    medium_evals = await db.evaluations.count_documents({"total_tasks": {"$gte": 10, "$lte": 20}})
    large_evals = await db.evaluations.count_documents({"total_tasks": {"$gte": 45}})
    
    print(f"Evaluation size distribution:")
    print(f"  Small (≤9 tasks): {small_evals}")
    print(f"  Medium (10-20 tasks): {medium_evals}")  
    print(f"  Large (≥45 tasks): {large_evals}")
    
    if small_evals > large_evals * 2:
        print("  🚨 Many small evaluations - indicates Option A fragmentation problem")
        print("  ✅ Option B fix should consolidate these")
    elif large_evals > 0:
        print("  ✅ Large evaluations present - Option B already working or not needed")
    else:
        print("  📊 Mixed sizes - Option B would improve architecture")

if __name__ == "__main__":
    asyncio.run(check_database())
