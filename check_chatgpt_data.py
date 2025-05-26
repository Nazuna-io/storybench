#!/usr/bin/env python3
"""
Check current ChatGPT data in the database
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import init_database, get_database

async def check_chatgpt_data():
    # Load environment variables
    load_dotenv(override=True)
    
    # Initialize database
    await init_database()
    database = await get_database()
    
    print("🔍 Checking ChatGPT data in database...")
    
    # Check responses collection
    responses_collection = database.responses
    
    # Find all ChatGPT-related responses
    chatgpt_patterns = [
        {"model_name": {"$regex": "gpt", "$options": "i"}},
        {"model_name": {"$regex": "chatgpt", "$options": "i"}},
        {"model_name": {"$regex": "o1-", "$options": "i"}},
        {"model_name": {"$regex": "o3-", "$options": "i"}},
        {"model_name": {"$regex": "o4-", "$options": "i"}},
    ]
    
    chatgpt_query = {"$or": chatgpt_patterns}
    chatgpt_responses = await responses_collection.find(chatgpt_query).to_list(None)
    
    print(f"\n📊 Found {len(chatgpt_responses)} ChatGPT responses:")
    
    # Group by model and sequence
    model_sequence_counts = {}
    empty_responses = []
    
    for response in chatgpt_responses:
        model = response.get('model_name', 'unknown')
        sequence = response.get('sequence_name', 'unknown')
        run = response.get('run_number', 'unknown')
        text = response.get('response_text', '')
        
        key = f"{model} - {sequence}"
        if key not in model_sequence_counts:
            model_sequence_counts[key] = {'total': 0, 'runs': set(), 'empty': 0}
        
        model_sequence_counts[key]['total'] += 1
        model_sequence_counts[key]['runs'].add(run)
        
        if not text or text.strip() == '':
            model_sequence_counts[key]['empty'] += 1
            empty_responses.append({
                'id': str(response['_id']),
                'model': model,
                'sequence': sequence,
                'run': run,
                'text_length': len(text) if text else 0
            })
    
    # Print summary
    for key, stats in sorted(model_sequence_counts.items()):
        runs_list = sorted(list(stats['runs']))
        empty_info = f" ({stats['empty']} empty)" if stats['empty'] > 0 else ""
        print(f"   {key}: {stats['total']} responses, runs {runs_list}{empty_info}")
    
    # Check evaluations collection
    evaluations_collection = database.response_llm_evaluations
    
    # Count evaluations for ChatGPT responses
    chatgpt_response_ids = [response['_id'] for response in chatgpt_responses]
    evaluation_count = await evaluations_collection.count_documents({
        "response_id": {"$in": chatgpt_response_ids}
    })
    
    print(f"\n🧠 Found {evaluation_count} evaluations for ChatGPT responses")
    
    # Show empty responses details
    if empty_responses:
        print(f"\n⚠️  Empty responses found ({len(empty_responses)}):")
        for empty in empty_responses:
            print(f"   ID: {empty['id']} - {empty['model']} - {empty['sequence']} - Run {empty['run']} (length: {empty['text_length']})")
    
    # Check for dialogue sequence specifically
    dialogue_responses = [r for r in chatgpt_responses if 'dialogue' in r.get('sequence_name', '').lower()]
    print(f"\n💬 Dialogue sequence responses: {len(dialogue_responses)}")
    for response in dialogue_responses:
        model = response.get('model_name', 'unknown')
        run = response.get('run_number', 'unknown')
        text_len = len(response.get('response_text', ''))
        print(f"   {model} - Run {run}: {text_len} chars")
    
    return empty_responses

if __name__ == "__main__":
    asyncio.run(check_chatgpt_data())
