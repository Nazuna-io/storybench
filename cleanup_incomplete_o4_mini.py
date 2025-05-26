#!/usr/bin/env python3
"""
Script to remove incomplete o4-mini-2025-04-16 model results from the database.
Identifies entries without evaluation data and removes them.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def cleanup_incomplete_o4_mini():
    """Remove incomplete o4-mini-2025-04-16 entries from the database."""
    
    # Get MongoDB connection
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ MONGODB_URI environment variable not found!")
        return
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_uri)
        db = client.storybench
        
        print("🔍 Searching for o4-mini-2025-04-16 model entries...")
        print("=" * 60)
        
        # Find all responses for o4-mini-2025-04-16
        responses_collection = db.responses
        evaluations_collection = db.evaluations
        
        # Search for responses with the model name
        model_name = "o4-mini-2025-04-16"
        responses = await responses_collection.find({"model_name": model_name}).to_list(None)
        
        print(f"📊 Found {len(responses)} responses for {model_name}")
        
        if not responses:
            print("✅ No responses found for o4-mini-2025-04-16")
            return
        
        # Group responses by evaluation_id to see which evaluations they belong to
        evaluation_ids = set()
        response_by_eval = {}
        
        for response in responses:
            eval_id = response.get("evaluation_id")
            if eval_id:
                evaluation_ids.add(eval_id)
                if eval_id not in response_by_eval:
                    response_by_eval[eval_id] = []
                response_by_eval[eval_id].append(response)
        
        print(f"📋 Responses belong to {len(evaluation_ids)} evaluation(s)")
        
        # Check each evaluation to see if it has evaluation data
        for eval_id in evaluation_ids:
            print(f"\n🔍 Checking evaluation {eval_id}:")
            
            # Count responses for this evaluation
            eval_responses = response_by_eval[eval_id]
            print(f"  📝 Responses: {len(eval_responses)}")
            
            # Check if there are evaluations for these responses
            response_ids = [str(resp["_id"]) for resp in eval_responses]
            eval_count = await evaluations_collection.count_documents({
                "response_id": {"$in": response_ids}
            })
            
            print(f"  📊 Evaluations: {eval_count}")
            
            if eval_count == 0:
                print(f"  ❌ No evaluations found - this is incomplete data")
                
                # Ask for confirmation before deletion
                print(f"\n⚠️  About to delete {len(eval_responses)} responses for evaluation {eval_id}")
                print("   These responses have no corresponding evaluations.")
                
                # Show sample response details
                sample_response = eval_responses[0]
                print(f"   Sample response:")
                print(f"   - ID: {sample_response['_id']}")
                print(f"   - Model: {sample_response['model_name']}")
                print(f"   - Sequence: {sample_response.get('sequence', 'N/A')}")
                print(f"   - Run: {sample_response.get('run', 'N/A')}")
                print(f"   - Created: {sample_response.get('created_at', 'N/A')}")
                
                # Delete the responses
                response_ids_obj = [resp["_id"] for resp in eval_responses]
                delete_result = await responses_collection.delete_many({
                    "_id": {"$in": response_ids_obj}
                })
                
                print(f"  ✅ Deleted {delete_result.deleted_count} responses")
                
            else:
                print(f"  ✅ Has {eval_count} evaluations - keeping this data")
        
        print(f"\n" + "=" * 60)
        print("✅ Cleanup complete!")
        
        # Final verification
        remaining_responses = await responses_collection.count_documents({"model_name": model_name})
        print(f"📊 Remaining {model_name} responses: {remaining_responses}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_incomplete_o4_mini())
