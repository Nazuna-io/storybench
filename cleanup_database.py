#!/usr/bin/env python3
"""Clean up database by removing o4-mini-2025-04-16 evaluations."""

import asyncio
from dotenv import load_dotenv
load_dotenv()

from src.storybench.database.connection import init_database


async def cleanup_database():
    """Remove o4-mini-2025-04-16 evaluations and their responses."""
    
    database = await init_database()
    
    print("🔍 Finding o4-mini-2025-04-16 evaluations to remove...")
    
    # Find evaluations with o4-mini-2025-04-16 model
    o4_evaluations = []
    async for evaluation in database.evaluations.find({"models": {"$in": ["o4-mini-2025-04-16"]}}):
        eval_id = str(evaluation["_id"])
        o4_evaluations.append(eval_id)
        print(f"   Found evaluation {eval_id} - Status: {evaluation.get('status')} - Started: {evaluation.get('started_at')}")
    
    print(f"\n📊 Found {len(o4_evaluations)} o4-mini-2025-04-16 evaluations")
    
    if not o4_evaluations:
        print("✅ No o4-mini-2025-04-16 evaluations found - database is already clean")
        return
    
    # Count responses for these evaluations
    response_count = 0
    for eval_id in o4_evaluations:
        count = await database.responses.count_documents({"evaluation_id": eval_id})
        response_count += count
    
    print(f"📊 Found {response_count} responses to remove")
    
    # Remove responses first
    if response_count > 0:
        delete_responses = await database.responses.delete_many({
            "evaluation_id": {"$in": o4_evaluations}
        })
        print(f"🗑️  Deleted {delete_responses.deleted_count} responses")
    
    # Remove evaluations
    delete_evaluations = await database.evaluations.delete_many({
        "_id": {"$in": [database.evaluations._collection.collection.objects.ObjectId(eid) for eid in o4_evaluations]}
    })
    
    # Actually, let's use the simpler approach
    delete_evaluations = await database.evaluations.delete_many({
        "models": {"$in": ["o4-mini-2025-04-16"]}
    })
    print(f"🗑️  Deleted {delete_evaluations.deleted_count} evaluations")
    
    # Verify remaining evaluations
    print("\n✅ Remaining evaluations:")
    remaining_count = 0
    async for evaluation in database.evaluations.find():
        remaining_count += 1
        models = evaluation.get("models", [])
        status = evaluation.get("status", "unknown")
        started = evaluation.get("started_at", "unknown")
        print(f"   {remaining_count}. Models: {models} - Status: {status} - Started: {started}")
    
    print(f"\n🎯 Database cleanup complete! {remaining_count} evaluations remaining")


if __name__ == "__main__":
    asyncio.run(cleanup_database())
