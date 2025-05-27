#!/usr/bin/env python3
"""
Test script for sequence-aware evaluation to verify coherence assessment works correctly.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from src.storybench.database.services.sequence_evaluation_service import SequenceEvaluationService

async def main():
    # Load environment variables
    load_dotenv()
    
    mongodb_uri = os.getenv("MONGODB_URI")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not mongodb_uri or not openai_api_key:
        print("❌ Missing environment variables")
        return
    
    print("🧪 Testing sequence-aware evaluation...")
    client = AsyncIOMotorClient(mongodb_uri)
    database = client["storybench"]
    
    sequence_service = SequenceEvaluationService(database, openai_api_key)
    
    try:
        # Get all responses and show sequence structure
        all_responses = await sequence_service.response_repo.find_many({})
        sequence_groups = sequence_service._group_responses_by_sequence(all_responses)
        
        print(f"📊 Found {len(all_responses)} total responses")
        print(f"🧩 Grouped into {len(sequence_groups)} sequences")
        
        # Show first few sequences for verification
        print(f"\n📋 Sample sequence structure:")
        for i, (sequence_key, responses) in enumerate(list(sequence_groups.items())[:3]):
            model_name, sequence_name, run = sequence_key
            print(f"\n   Sequence {i+1}: {model_name} - {sequence_name} - Run {run}")
            print(f"   Responses: {len(responses)}")
            
            for j, response in enumerate(responses):
                print(f"     {j+1}. {response.prompt_name} (index: {response.prompt_index})")
        
        # Test evaluation on one sequence
        if sequence_groups:
            test_sequence_key, test_responses = list(sequence_groups.items())[0]
            model_name, sequence_name, run = test_sequence_key
            
            print(f"\n🔍 Testing evaluation on: {model_name} - {sequence_name} - Run {run}")
            print(f"   This sequence has {len(test_responses)} responses")
            
            # Show the sequence context that will be evaluated
            print(f"\n📖 Sequence context for coherence evaluation:")
            for i, response in enumerate(test_responses):
                print(f"\n   Response {i+1}: {response.prompt_name}")
                print(f"   Prompt: {response.prompt_text[:100]}...")
                print(f"   Response: {response.response[:150]}...")
            
            # Get criteria
            criteria_config = await sequence_service.criteria_repo.find_active()
            if not criteria_config:
                print("❌ No active criteria found")
                return
            
            print(f"\n✅ Found evaluation criteria: {list(criteria_config.criteria.keys())}")
            
            # Test the evaluation
            print(f"\n🚀 Running test evaluation...")
            evaluations = await sequence_service.evaluate_sequence(test_responses, criteria_config)
            
            if evaluations:
                print(f"✅ Successfully created {len(evaluations)} evaluations")
                
                # Show sample results
                for i, evaluation in enumerate(evaluations):
                    response = test_responses[i]
                    print(f"\n   Response {i+1} ({response.prompt_name}) scores:")
                    
                    for criterion_eval in evaluation.criteria_results:
                        score = criterion_eval.score
                        justification = criterion_eval.justification[:100] + "..." if len(criterion_eval.justification) > 100 else criterion_eval.justification
                        print(f"     {criterion_eval.criterion_name}: {score} - {justification}")
                
                # Save test results
                test_results = []
                for i, evaluation in enumerate(evaluations):
                    response = test_responses[i]
                    test_results.append({
                        "response_id": str(evaluation.response_id),
                        "prompt_name": response.prompt_name,
                        "prompt_index": response.prompt_index,
                        "criteria_results": [
                            {
                                "criterion_name": ce.criterion_name,
                                "score": ce.score,
                                "justification": ce.justification
                            }
                            for ce in evaluation.criteria_results
                        ]
                    })
                
                with open("test_sequence_evaluation_results.json", "w") as f:
                    json.dump({
                        "sequence_info": {
                            "model_name": model_name,
                            "sequence_name": sequence_name,
                            "run": run,
                            "total_responses": len(test_responses)
                        },
                        "evaluations": test_results
                    }, f, indent=2)
                
                print(f"\n💾 Test results saved to: test_sequence_evaluation_results.json")
                print(f"\n✅ Sequence evaluation test completed successfully!")
                print(f"   The evaluator now has full context of all {len(test_responses)} related responses")
                print(f"   This enables proper coherence assessment across the sequence")
                
            else:
                print(f"❌ Evaluation failed")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
