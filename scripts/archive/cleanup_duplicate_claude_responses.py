#!/usr/bin/env python3
"""
Clean up duplicate Claude responses to get exactly 45 responses per model
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import init_database, get_database

async def cleanup_duplicate_claude_responses():
    # Load environment variables
    load_dotenv(override=True)
    
    # Initialize database
    await init_database()
    database = await get_database()
    
    print("🔍 Cleaning up duplicate Claude responses...")
    
    # Check responses collection
    responses_collection = database.responses
    
    # Get all Claude responses
    claude_responses = await responses_collection.find({
        "model_name": "Claude-4-Sonnet"
    }).to_list(None)
    
    print(f"📊 Found {len(claude_responses)} Claude responses")
    
    # Group by sequence and prompt to identify duplicates
    sequence_prompt_groups = {}
    
    for response in claude_responses:
        sequence = response.get('sequence_name', 'unknown')
        prompt_name = response.get('prompt_name', 'unknown')
        
        # Create a key for grouping
        key = f"{sequence}_{prompt_name}"
        
        if key not in sequence_prompt_groups:
            sequence_prompt_groups[key] = []
        
        sequence_prompt_groups[key].append(response)
    
    print(f"📋 Found {len(sequence_prompt_groups)} unique sequence-prompt combinations")
    
    # Identify duplicates and responses to delete
    responses_to_delete = []
    
    for key, responses in sequence_prompt_groups.items():
        if len(responses) > 3:  # Should only have 3 runs per sequence-prompt
            print(f"   {key}: {len(responses)} responses (expected: 3)")
            # Keep first 3, mark rest for deletion
            responses_to_delete.extend(responses[3:])
    
    print(f"\n⚠️  Found {len(responses_to_delete)} duplicate responses to delete")
    
    if len(responses_to_delete) == 0:
        print("✅ No duplicates found!")
        return
    
    # Show what will be deleted
    for response in responses_to_delete:
        response_id = str(response['_id'])
        sequence = response.get('sequence_name', 'unknown')
        prompt = response.get('prompt_name', 'unknown')
        print(f"   Delete: {sequence} - {prompt} (ID: {response_id[:12]}...)")
    
    # Confirm deletion
    confirm = input(f"\nProceed with deleting {len(responses_to_delete)} duplicate responses? (yes/no): ").lower().strip()
    
    if confirm != 'yes':
        print("❌ Deletion cancelled")
        return
    
    # Delete the duplicate responses
    response_ids = [response['_id'] for response in responses_to_delete]
    
    # Also delete any evaluations for these responses
    evaluations_collection = database.response_llm_evaluations
    eval_count = await evaluations_collection.count_documents({
        "response_id": {"$in": response_ids}
    })
    
    if eval_count > 0:
        eval_result = await evaluations_collection.delete_many({
            "response_id": {"$in": response_ids}
        })
        print(f"🧠 Deleted {eval_result.deleted_count} evaluations for duplicate responses")
    
    # Delete the responses
    result = await responses_collection.delete_many({
        "_id": {"$in": response_ids}
    })
    
    print(f"📝 Deleted {result.deleted_count} duplicate responses")
    
    # Verify final count
    final_claude_count = await responses_collection.count_documents({
        "model_name": "Claude-4-Sonnet"
    })
    
    print(f"✅ Final Claude response count: {final_claude_count} (expected: 45)")

if __name__ == "__main__":
    asyncio.run(cleanup_duplicate_claude_responses())
