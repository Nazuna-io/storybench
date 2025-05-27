#!/usr/bin/env python3
"""
Check what responses currently exist in the database
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import init_database, get_database

async def check_current_responses():
    # Load environment variables
    load_dotenv(override=True)
    
    # Initialize database
    await init_database()
    database = await get_database()
    
    print("🔍 Checking all responses in database...")
    
    # Check responses collection
    responses_collection = database.responses
    
    # Get all responses
    all_responses = await responses_collection.find({}).to_list(None)
    
    print(f"📊 Found {len(all_responses)} total responses")
    
    # Group by model and sequence
    model_sequence_counts = {}
    
    for response in all_responses:
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
    
    print("\n📋 All responses by model and sequence:")
    for key, stats in sorted(model_sequence_counts.items()):
        runs_list = sorted(list(stats['runs']))
        avg_chars = stats['total_chars'] // stats['total'] if stats['total'] > 0 else 0
        print(f"   {key}: {stats['total']} responses, runs {runs_list}, avg {avg_chars} chars")
    
    # Check evaluations
    evaluations_collection = database.response_llm_evaluations
    total_evaluations = await evaluations_collection.count_documents({})
    
    print(f"\n🧠 Total evaluations: {total_evaluations}")
    
    # Check for dialogue specifically
    dialogue_responses = [r for r in all_responses if 'dialogue' in r.get('sequence_name', '').lower()]
    print(f"\n💬 Dialogue sequence responses: {len(dialogue_responses)}")
    
    if dialogue_responses:
        for response in dialogue_responses:
            model = response.get('model_name', 'unknown')
            run = response.get('run_number', 'unknown')
            text_len = len(response.get('response_text', ''))
            print(f"   {model} - Run {run}: {text_len} chars")

if __name__ == "__main__":
    asyncio.run(check_current_responses())
