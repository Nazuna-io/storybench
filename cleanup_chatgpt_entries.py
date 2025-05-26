#!/usr/bin/env python3
"""
Script to remove all ChatGPT model entries from the database.
This will clean up responses, evaluations, and any other related data.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def cleanup_chatgpt_entries():
    """Remove all ChatGPT model entries from the database."""
    
    # Get MongoDB connection
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ MONGODB_URI environment variable not found!")
        return
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_uri)
        db = client.storybench
        
        print("🔍 Searching for ChatGPT model entries...")
        print("=" * 60)
        
        # Define ChatGPT model patterns to search for
        chatgpt_patterns = [
            "chatgpt",
            "ChatGPT",
            "gpt-3.5",
            "gpt-4",
            "GPT-3.5",
            "GPT-4",
            "o1-mini",
            "o1-preview",
            "o1-pro",
            "o3-mini",
            "o4-mini",
            "gpt-4o",
            "GPT-4o"
        ]
        
        # Get collections
        responses_collection = db.responses
        evaluations_collection = db.evaluations
        evaluation_runs_collection = db.evaluation_runs
        
        total_deleted = {
            "responses": 0,
            "evaluations": 0,
            "evaluation_runs": 0
        }
        
        # Search and delete responses
        print("\n📝 Cleaning up responses...")
        for pattern in chatgpt_patterns:
            # Case-insensitive search
            responses = await responses_collection.find({
                "model_name": {"$regex": pattern, "$options": "i"}
            }).to_list(None)
            
            if responses:
                print(f"  Found {len(responses)} responses for pattern '{pattern}'")
                
                # Show sample entries
                for i, response in enumerate(responses[:3]):  # Show first 3
                    print(f"    - {response.get('model_name')} (ID: {response['_id']})")
                if len(responses) > 3:
                    print(f"    ... and {len(responses) - 3} more")
                
                # Delete responses
                response_ids = [resp["_id"] for resp in responses]
                delete_result = await responses_collection.delete_many({
                    "_id": {"$in": response_ids}
                })
                total_deleted["responses"] += delete_result.deleted_count
                print(f"  ✅ Deleted {delete_result.deleted_count} responses")
                
                # Find and delete related evaluations
                response_id_strings = [str(resp["_id"]) for resp in responses]
                evaluations = await evaluations_collection.find({
                    "response_id": {"$in": response_id_strings}
                }).to_list(None)
                
                if evaluations:
                    eval_ids = [eval_doc["_id"] for eval_doc in evaluations]
                    eval_delete_result = await evaluations_collection.delete_many({
                        "_id": {"$in": eval_ids}
                    })
                    total_deleted["evaluations"] += eval_delete_result.deleted_count
                    print(f"  ✅ Deleted {eval_delete_result.deleted_count} related evaluations")
        
        # Search and delete evaluation runs that contain ChatGPT models
        print("\n📊 Cleaning up evaluation runs...")
        eval_runs = await evaluation_runs_collection.find({}).to_list(None)
        
        runs_to_delete = []
        for run in eval_runs:
            models = run.get("models", [])
            # Check if any model in the run matches ChatGPT patterns
            has_chatgpt = False
            for model in models:
                for pattern in chatgpt_patterns:
                    if pattern.lower() in model.lower():
                        has_chatgpt = True
                        break
                if has_chatgpt:
                    break
            
            if has_chatgpt:
                runs_to_delete.append(run)
                print(f"  Found evaluation run with ChatGPT models: {run['_id']}")
                print(f"    Models: {models}")
        
        if runs_to_delete:
            run_ids = [run["_id"] for run in runs_to_delete]
            run_delete_result = await evaluation_runs_collection.delete_many({
                "_id": {"$in": run_ids}
            })
            total_deleted["evaluation_runs"] = run_delete_result.deleted_count
            print(f"  ✅ Deleted {run_delete_result.deleted_count} evaluation runs")
        
        print(f"\n" + "=" * 60)
        print("✅ Cleanup complete!")
        print(f"📊 Total items deleted:")
        print(f"  - Responses: {total_deleted['responses']}")
        print(f"  - Evaluations: {total_deleted['evaluations']}")
        print(f"  - Evaluation Runs: {total_deleted['evaluation_runs']}")
        
        # Final verification - check what's left
        print(f"\n🔍 Verification - checking remaining data...")
        
        # Check remaining models in responses
        remaining_models = await responses_collection.distinct("model_name")
        print(f"📝 Remaining response models: {remaining_models}")
        
        # Check remaining evaluation runs
        remaining_runs = await evaluation_runs_collection.find({}).to_list(None)
        print(f"📊 Remaining evaluation runs: {len(remaining_runs)}")
        for run in remaining_runs:
            print(f"  - Run {run['_id']}: {run.get('models', [])}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_chatgpt_entries())
