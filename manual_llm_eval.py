#!/usr/bin/env python3
"""Manually trigger LLM evaluation for the latest responses."""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, '/home/todd/storybench/src')

async def manual_llm_evaluation():
    load_dotenv()
    
    from storybench.database.connection import DatabaseConnection
    from storybench.database.services.sequence_evaluation_service import SequenceEvaluationService
    
    try:
        # Connect to database
        db_conn = DatabaseConnection()
        database = await db_conn.connect(os.getenv('MONGODB_URI'))
        
        print('🔍 MANUAL LLM EVALUATION TEST\n')
        
        # Check OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print('❌ OPENAI_API_KEY not found')
            return
        print('✅ OpenAI API key found')
        
        # Initialize sequence evaluation service
        sequence_eval_service = SequenceEvaluationService(database, openai_api_key)
        
        print('🚀 Starting LLM evaluation...')
        
        # Run the evaluation
        results = await sequence_eval_service.evaluate_all_sequences()
        
        print('\n📊 EVALUATION RESULTS:')
        print(f'   Total sequences: {results.get("total_sequences", 0)}')
        print(f'   Unevaluated sequences: {results.get("unevaluated_sequences", 0)}')
        print(f'   Sequences evaluated: {results.get("sequences_evaluated", 0)}')
        print(f'   Total evaluations created: {results.get("total_evaluations_created", 0)}')
        
        if results.get("errors"):
            print(f'   Errors: {len(results["errors"])}')
            for i, error in enumerate(results["errors"][:3], 1):
                print(f'     {i}. {error}')
        
        # Check if any new evaluations were created
        print('\n🔍 Post-evaluation check...')
        from pymongo import MongoClient
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client.storybench
        
        latest_eval_id = '6833fbbcbb8fd843c182276c'
        latest_responses = list(db.responses.find({'evaluation_id': latest_eval_id}).limit(3))
        
        for i, resp in enumerate(latest_responses, 1):
            resp_id = str(resp['_id'])
            llm_eval = db.response_llm_evaluations.find_one({'response_id': resp_id})
            has_eval = bool(llm_eval)
            print(f'   Response {i}: Has evaluation = {has_eval}')
        
        client.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(manual_llm_evaluation())
