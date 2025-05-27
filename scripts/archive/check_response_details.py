#!/usr/bin/env python3
"""
Check detailed response breakdown to identify extra responses
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import init_database, get_database

async def check_response_details():
    # Load environment variables
    load_dotenv(override=True)
    
    # Initialize database
    await init_database()
    database = await get_database()
    
    print("🔍 Checking detailed response breakdown...")
    
    # Check responses collection
    responses_collection = database.responses
    
    # Get all responses
    all_responses = await responses_collection.find({}).to_list(None)
    
    print(f"📊 Found {len(all_responses)} total responses")
    
    # Group by model, sequence, and run
    model_details = {}
    
    for response in all_responses:
        model = response.get('model_name', 'unknown')
        sequence = response.get('sequence_name', 'unknown')
        run = response.get('run_number', 'unknown')
        prompt_name = response.get('prompt_name', 'unknown')
        text_len = len(response.get('response_text', ''))
        response_id = str(response['_id'])
        
        if model not in model_details:
            model_details[model] = {}
        
        if sequence not in model_details[model]:
            model_details[model][sequence] = {}
        
        if run not in model_details[model][sequence]:
            model_details[model][sequence][run] = []
        
        model_details[model][sequence][run].append({
            'prompt_name': prompt_name,
            'text_len': text_len,
            'id': response_id
        })
    
    # Print detailed breakdown
    for model, sequences in sorted(model_details.items()):
        print(f"\n📋 {model}:")
        total_responses = 0
        
        for sequence, runs in sorted(sequences.items()):
            print(f"   {sequence}:")
            
            for run, prompts in sorted(runs.items()):
                print(f"      Run {run}: {len(prompts)} prompts")
                total_responses += len(prompts)
                
                for prompt in prompts:
                    print(f"         {prompt['prompt_name']}: {prompt['text_len']} chars (ID: {prompt['id'][:12]}...)")
        
        expected = 45  # 5 sequences × 3 prompts × 3 runs
        print(f"   Total: {total_responses} responses (expected: {expected})")
        
        if total_responses > expected:
            print(f"   ⚠️  {total_responses - expected} extra responses found!")

if __name__ == "__main__":
    asyncio.run(check_response_details())
