#!/usr/bin/env python3
"""
Run missing LLM evaluations for ChatGPT responses
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.evaluators.api_evaluator import APIEvaluator
from storybench.database.models import Response

async def run_missing_evaluations():
    # Load environment variables
    load_dotenv(override=True)
    mongodb_uri = os.getenv("MONGODB_URI")
    
    client = AsyncIOMotorClient(mongodb_uri)
    database = client.storybench
    
    print("🔍 Finding ChatGPT responses without LLM evaluations...")
    
    # Find all ChatGPT responses
    chatgpt_patterns = ["gpt-", "GPT-"]
    chatgpt_responses = []
    
    for pattern in chatgpt_patterns:
        responses = await database.responses.find({"model_name": {"$regex": pattern, "$options": "i"}}).to_list(None)
        chatgpt_responses.extend(responses)
    
    print(f"Found {len(chatgpt_responses)} ChatGPT responses")
    
    # Check which ones don't have LLM evaluations
    responses_without_evals = []
    for response_doc in chatgpt_responses:
        response_id = response_doc['_id']
        existing_eval = await database.response_llm_evaluations.find_one({"response_id": response_id})
        if not existing_eval:
            responses_without_evals.append(response_doc)
    
    print(f"Found {len(responses_without_evals)} responses without LLM evaluations")
    
    if not responses_without_evals:
        print("✅ All ChatGPT responses already have evaluations!")
        return
    
    # Set up the evaluator
    print("🤖 Setting up GPT-4 evaluator...")
    
    # Get API keys
    api_keys = {
        'openai_api_key': os.getenv('OPENAI_API_KEY')
    }
    
    # Create evaluator config
    evaluator_config = {
        'provider': 'openai',
        'model_name': 'gpt-4o-2024-11-20'
    }
    
    evaluator = APIEvaluator("gpt4_evaluator", evaluator_config, api_keys)
    
    # Get evaluation criteria
    criteria_doc = await database.evaluation_criteria.find_one({"version": 2})
    if not criteria_doc:
        print("❌ No evaluation criteria found!")
        return
    
    criteria = criteria_doc['criteria']
    
    # Setup the evaluator
    await evaluator.setup(
        model_name='gpt-4o-2024-11-20',
        provider='openai',
        api_keys=api_keys,
        criteria=criteria
    )
    
    print(f"🚀 Starting evaluation of {len(responses_without_evals)} responses...")
    
    success_count = 0
    error_count = 0
    
    for i, response_doc in enumerate(responses_without_evals):
        try:
            print(f"\n📝 Evaluating response {i+1}/{len(responses_without_evals)} (ID: {str(response_doc['_id'])[:8]}...)")
            print(f"   Model: {response_doc['model_name']}")
            print(f"   Prompt: {response_doc['prompt_name']}")
            
            # Convert to Response object
            response = Response(**response_doc)
            
            # Run the evaluation
            evaluation_result = await evaluator.evaluate_response(response)
            
            # Store the evaluation in the database
            evaluation_doc = {
                "response_id": response_doc['_id'],
                "evaluation_id": response_doc.get('evaluation_id'),
                "response": {
                    "model_name": response_doc['model_name'],
                    "prompt_name": response_doc['prompt_name'],
                    "text": response_doc['text']
                },
                "scores": evaluation_result['scores'],
                "feedback": evaluation_result['feedback'],
                "evaluator_model": 'gpt-4o-2024-11-20',
                "criteria_version": 2,
                "created_at": evaluation_result.get('created_at')
            }
            
            await database.response_llm_evaluations.insert_one(evaluation_doc)
            
            success_count += 1
            print(f"   ✅ Evaluation completed and stored")
            
            # Show scores
            scores = evaluation_result['scores']
            print(f"   📊 Scores: VI={scores['visual_imagery']}, ER={scores['emotional_resonance']}, NC={scores['narrative_coherence']}, CD={scores['character_development']}")
            
        except Exception as e:
            error_count += 1
            print(f"   ❌ Error evaluating response: {e}")
            continue
    
    print(f"\n🎉 Evaluation completed!")
    print(f"   ✅ Successful evaluations: {success_count}")
    print(f"   ❌ Failed evaluations: {error_count}")
    
    # Verify the results
    total_llm_evals = await database.response_llm_evaluations.count_documents({})
    print(f"   📊 Total LLM evaluations in database: {total_llm_evals}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(run_missing_evaluations())
