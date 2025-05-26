#!/usr/bin/env python3
"""
Script to remove evaluation records that reference ChatGPT models.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup_evaluation_records():
    """Remove evaluation records that reference ChatGPT models."""
    
    # Get MongoDB connection
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ MONGODB_URI environment variable not found!")
        return
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_uri)
        db = client.storybench
        
        print("🔍 Cleaning up evaluation records...")
        print("=" * 60)
        
        # Get the evaluations collection
        evaluations_collection = db.evaluations
        
        # Find evaluations that reference ChatGPT models
        chatgpt_patterns = [
            "chatgpt", "gpt-", "GPT-", "o1-", "o3-", "o4-"
        ]
        
        evaluations_to_delete = []
        
        for pattern in chatgpt_patterns:
            evals = await evaluations_collection.find({
                "models": {"$regex": pattern, "$options": "i"}
            }).to_list(None)
            
            if evals:
                print(f"📋 Found {len(evals)} evaluation records matching '{pattern}':")
                for eval_doc in evals:
                    print(f"  - ID: {eval_doc['_id']}")
                    print(f"    Models: {eval_doc.get('models', [])}")
                    print(f"    Status: {eval_doc.get('status')}")
                    print(f"    Started: {eval_doc.get('started_at')}")
                    print(f"    Completed: {eval_doc.get('completed_at')}")
                    print()
                    evaluations_to_delete.append(eval_doc['_id'])
        
        if evaluations_to_delete:
            print(f"🗑️  Deleting {len(evaluations_to_delete)} evaluation records...")
            
            delete_result = await evaluations_collection.delete_many({
                "_id": {"$in": evaluations_to_delete}
            })
            
            print(f"✅ Deleted {delete_result.deleted_count} evaluation records")
        else:
            print("✅ No ChatGPT evaluation records found to delete")
        
        # Final verification
        print(f"\n🔍 Final verification...")
        remaining_evals = await evaluations_collection.find({}).to_list(None)
        print(f"📊 Remaining evaluation records: {len(remaining_evals)}")
        
        for eval_doc in remaining_evals:
            print(f"  - ID: {eval_doc['_id']}")
            print(f"    Models: {eval_doc.get('models', [])}")
            print(f"    Status: {eval_doc.get('status')}")
        
        print(f"\n" + "=" * 60)
        print("✅ Cleanup complete!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_evaluation_records())
