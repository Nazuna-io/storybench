#!/usr/bin/env python3
"""
Clean up empty ChatGPT responses with unknown sequence names
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import init_database, get_database

async def cleanup_empty_chatgpt_responses():
    # Load environment variables
    load_dotenv(override=True)
    
    # Initialize database
    await init_database()
    database = await get_database()
    
    print("🔍 Finding empty ChatGPT responses to clean up...")
    
    # Check responses collection
    responses_collection = database.responses
    
    # Find all ChatGPT-related responses that are empty and have unknown sequence
    chatgpt_patterns = [
        {"model_name": {"$regex": "gpt", "$options": "i"}},
        {"model_name": {"$regex": "chatgpt", "$options": "i"}},
        {"model_name": {"$regex": "o1-", "$options": "i"}},
        {"model_name": {"$regex": "o3-", "$options": "i"}},
        {"model_name": {"$regex": "o4-", "$options": "i"}},
    ]
    
    # Find empty responses with unknown sequence names
    empty_query = {
        "$and": [
            {"$or": chatgpt_patterns},
            {"$or": [
                {"response_text": {"$exists": False}},
                {"response_text": ""},
                {"response_text": None}
            ]},
            {"$or": [
                {"sequence_name": "unknown"},
                {"sequence_name": {"$exists": False}},
                {"sequence_name": None}
            ]}
        ]
    }
    
    empty_responses = await responses_collection.find(empty_query).to_list(None)
    
    print(f"📊 Found {len(empty_responses)} empty ChatGPT responses to delete")
    
    if len(empty_responses) == 0:
        print("✅ No empty responses found!")
        return
    
    # Group by model for summary
    model_counts = {}
    response_ids = []
    
    for response in empty_responses:
        model = response.get('model_name', 'unknown')
        model_counts[model] = model_counts.get(model, 0) + 1
        response_ids.append(response['_id'])
    
    print("📋 Breakdown by model:")
    for model, count in sorted(model_counts.items()):
        print(f"   {model}: {count} empty responses")
    
    # Also check if there are any evaluations for these responses that need cleanup
    evaluations_collection = database.response_llm_evaluations
    evaluation_count = await evaluations_collection.count_documents({
        "response_id": {"$in": response_ids}
    })
    
    print(f"🧠 Found {evaluation_count} evaluations for these empty responses")
    
    # Confirm deletion
    print(f"\n⚠️  This will delete:")
    print(f"   📝 {len(empty_responses)} empty responses")
    print(f"   🧠 {evaluation_count} associated evaluations")
    
    confirm = input("\nProceed with deletion? (yes/no): ").lower().strip()
    
    if confirm != 'yes':
        print("❌ Deletion cancelled")
        return
    
    # Delete evaluations first
    if evaluation_count > 0:
        eval_result = await evaluations_collection.delete_many({
            "response_id": {"$in": response_ids}
        })
        print(f"🧠 Deleted {eval_result.deleted_count} evaluations")
    
    # Delete responses
    response_result = await responses_collection.delete_many(empty_query)
    print(f"📝 Deleted {response_result.deleted_count} empty responses")
    
    print(f"\n✅ Cleanup complete!")
    
    # Check what's left
    remaining_chatgpt = await responses_collection.find({"$or": chatgpt_patterns}).to_list(None)
    print(f"📊 Remaining ChatGPT responses: {len(remaining_chatgpt)}")
    
    if remaining_chatgpt:
        print("📋 Remaining responses by model and sequence:")
        model_sequence_counts = {}
        
        for response in remaining_chatgpt:
            model = response.get('model_name', 'unknown')
            sequence = response.get('sequence_name', 'unknown')
            run = response.get('run_number', 'unknown')
            text_len = len(response.get('response_text', ''))
            
            key = f"{model} - {sequence}"
            if key not in model_sequence_counts:
                model_sequence_counts[key] = {'total': 0, 'runs': set(), 'total_chars': 0}
            
            model_sequence_counts[key]['total'] += 1
            model_sequence_counts[key]['runs'].add(run)
            model_sequence_counts[key]['total_chars'] += text_len
        
        for key, stats in sorted(model_sequence_counts.items()):
            runs_list = sorted(list(stats['runs']))
            avg_chars = stats['total_chars'] // stats['total'] if stats['total'] > 0 else 0
            print(f"   {key}: {stats['total']} responses, runs {runs_list}, avg {avg_chars} chars")

if __name__ == "__main__":
    asyncio.run(cleanup_empty_chatgpt_responses())
