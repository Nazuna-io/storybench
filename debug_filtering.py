#!/usr/bin/env python3
"""Debug the sequence filtering logic."""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, '/home/todd/storybench/src')

async def debug_sequence_filtering():
    load_dotenv()
    
    from storybench.database.connection import DatabaseConnection
    from storybench.database.repositories.response_repo import ResponseRepository
    from storybench.database.repositories.response_llm_evaluation_repository import ResponseLLMEvaluationRepository
    
    try:
        # Connect to database
        db_conn = DatabaseConnection()
        database = await db_conn.connect(os.getenv('MONGODB_URI'))
        
        response_repo = ResponseRepository(database)
        evaluation_repo = ResponseLLMEvaluationRepository(database)
        
        print('🔍 DEBUGGING SEQUENCE FILTERING\n')
        
        # Get the latest evaluation responses
        latest_eval_id = '6833fbbcbb8fd843c182276c'
        latest_responses = await response_repo.find_many({'evaluation_id': latest_eval_id})
        
        print(f'Latest evaluation responses: {len(latest_responses)}')
        
        if latest_responses:
            # Test a few responses
            for i, response in enumerate(latest_responses[:3], 1):
                print(f'\n{i}. Response {response.id}:')
                print(f'   Model: {response.model_name}')
                print(f'   Sequence: {response.sequence}')
                print(f'   Run: {response.run}')
                
                # Check what get_evaluations_by_response_id returns
                existing_evals = await evaluation_repo.get_evaluations_by_response_id(response.id)
                print(f'   get_evaluations_by_response_id result: {existing_evals}')
                print(f'   Type: {type(existing_evals)}')
                print(f'   Length: {len(existing_evals) if existing_evals else 0}')
                
                # Also check raw database
                raw_result = await database.response_llm_evaluations.find_one({'response_id': response.id})
                print(f'   Raw DB lookup: {"Found" if raw_result else "Not found"}')
        
        # Now test the grouping logic
        print(f'\n🔍 TESTING GROUPING LOGIC:')
        all_responses = await response_repo.find_many({})
        print(f'Total responses in database: {len(all_responses)}')
        
        # Group responses manually like the service does
        sequence_groups = {}
        for response in all_responses:
            sequence_key = (response.model_name, response.sequence, response.run)
            if sequence_key not in sequence_groups:
                sequence_groups[sequence_key] = []
            sequence_groups[sequence_key].append(response)
        
        print(f'Total sequence groups: {len(sequence_groups)}')
        
        # Check filtering for a few groups
        unevaluated_count = 0
        for i, (sequence_key, responses) in enumerate(list(sequence_groups.items())[:5], 1):
            model, sequence, run = sequence_key
            print(f'\n{i}. Group ({model}, {sequence}, {run}):')
            print(f'   Response count: {len(responses)}')
            
            # Check if any response has evaluations
            has_evaluations = False
            for response in responses:
                existing_evals = await evaluation_repo.get_evaluations_by_response_id(response.id)
                if existing_evals:
                    has_evaluations = True
                    print(f'   Found evaluations for response {response.id}')
                    break
            
            print(f'   Sequence marked as evaluated: {has_evaluations}')
            if not has_evaluations:
                unevaluated_count += 1
        
        print(f'\nUnevaluated sequences found: {unevaluated_count}')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_sequence_filtering())
