#!/usr/bin/env python3
"""
Check current database state and generate responses + evaluations for DeepSeek-R1-0528.
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import init_database
from storybench.database.repositories.response_repo import ResponseRepository
from storybench.database.repositories.response_llm_evaluation_repository import ResponseLLMEvaluationRepository


async def check_database_state():
    """Check current responses and evaluations in the database."""
    print("Checking current database state...")
    print("=" * 50)
    
    try:
        # Initialize database
        database = await init_database()
        print("✅ Database connected")
        
        # Initialize repositories
        response_repo = ResponseRepository(database)
        evaluation_repo = ResponseLLMEvaluationRepository(database)
        
        # Check responses
        print("\n📄 RESPONSES:")
        all_responses = await response_repo.find_many({})
        print(f"Total responses in database: {len(all_responses)}")
        
        # Group by model
        models = {}
        for response in all_responses:
            model = response.model_name
            if model not in models:
                models[model] = 0
            models[model] += 1
        
        print("Responses by model:")
        for model, count in sorted(models.items()):
            print(f"  - {model}: {count} responses")
            if "DeepSeek-R1" in model:
                print(f"    🎯 DeepSeek model found!")
        
        # Check evaluations
        print("\n📊 EVALUATIONS:")
        try:
            all_evaluations = await evaluation_repo.find_many({})
            print(f"Total evaluations in database: {len(all_evaluations)}")
            
            # Group by model (via response lookup)
            eval_models = {}
            for evaluation in all_evaluations:
                try:
                    response = await response_repo.find_by_id(evaluation.response_id)
                    if response:
                        model = response.model_name
                        if model not in eval_models:
                            eval_models[model] = 0
                        eval_models[model] += 1
                except:
                    pass
            
            print("Evaluations by model:")
            for model, count in sorted(eval_models.items()):
                print(f"  - {model}: {count} evaluations")
                
        except Exception as e:
            print(f"⚠️  Issue reading evaluations: {e}")
        
        # Check specifically for DeepSeek-R1-0528
        print("\n🔍 DEEPSEEK-R1-0528 SPECIFIC CHECK:")
        deepseek_responses = await response_repo.find_many({"model_name": "deepseek-ai/DeepSeek-R1-0528"})
        print(f"DeepSeek-R1-0528 responses: {len(deepseek_responses)}")
        
        if deepseek_responses:
            print("Sample response IDs:")
            for resp in deepseek_responses[:3]:
                print(f"  - {resp.id}: {resp.prompt_name} (length: {len(resp.response_text)} chars)")
        
        return len(deepseek_responses) > 0
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    has_responses = asyncio.run(check_database_state())
    
    if has_responses:
        print("\n✅ DeepSeek-R1-0528 responses found in database")
    else:
        print("\n⚠️  No DeepSeek-R1-0528 responses found - need to generate them")
