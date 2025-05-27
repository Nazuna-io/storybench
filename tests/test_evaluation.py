#!/usr/bin/env python3
"""
Script to test the evaluation system on a small sample of responses.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from src.storybench.database.services.llm_evaluation_service import LLMEvaluationService
from src.storybench.database.repositories.response_repo import ResponseRepository

async def main():
    # Load environment variables
    load_dotenv()
    
    mongodb_uri = os.getenv("MONGODB_URI")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not mongodb_uri or not openai_api_key:
        print("❌ Missing required environment variables")
        return
    
    print("🧪 Testing evaluation system on sample responses...")
    
    client = AsyncIOMotorClient(mongodb_uri)
    database = client["storybench"]
    
    # Initialize services
    evaluation_service = LLMEvaluationService(database, openai_api_key)
    response_repo = ResponseRepository(database)
    
    try:
        # Get a small sample of responses (2 responses - one from each model)
        all_responses = await response_repo.find_many({})
        
        # Get one response from each model
        models_seen = set()
        test_responses = []
        
        for response in all_responses:
            if response.model_name not in models_seen:
                test_responses.append(response)
                models_seen.add(response.model_name)
                if len(test_responses) >= 2:  # Test with 2 responses
                    break
        
        print(f"📝 Testing with {len(test_responses)} responses:")
        for i, response in enumerate(test_responses):
            print(f"   {i+1}. {response.model_name} - {response.sequence} - {response.prompt_name}")
        
        # Test evaluation on these responses
        results = []
        for i, response in enumerate(test_responses):
            print(f"\n🔍 Evaluating response {i+1}/{len(test_responses)}...")
            
            # Get criteria config
            criteria_config = await evaluation_service.criteria_repo.find_active()
            if not criteria_config:
                print("❌ No active criteria configuration found")
                return
            
            # Evaluate the response
            evaluation = await evaluation_service.evaluate_single_response(response, criteria_config)
            
            if evaluation:
                print(f"✅ Successfully evaluated response {response.id}")
                
                # Display results
                print(f"   Criteria results:")
                for criterion_eval in evaluation.criteria_results:
                    score = criterion_eval.score if criterion_eval.score is not None else "N/A"
                    justification = criterion_eval.justification[:100] + "..." if len(criterion_eval.justification) > 100 else criterion_eval.justification
                    print(f"     {criterion_eval.criterion_name}: {score} - {justification}")
                
                results.append({
                    "response_id": str(response.id),
                    "model_name": response.model_name,
                    "sequence": response.sequence,
                    "prompt_name": response.prompt_name,
                    "evaluation_id": str(evaluation.id),
                    "criteria_results": [
                        {
                            "criterion_name": ce.criterion_name,
                            "score": ce.score,
                            "justification": ce.justification
                        }
                        for ce in evaluation.criteria_results
                    ]
                })
            else:
                print(f"❌ Failed to evaluate response {response.id}")
        
        # Save test results
        with open("test_evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Test completed successfully!")
        print(f"   Evaluated {len(results)} responses")
        print(f"   Results saved to: test_evaluation_results.json")
        
        if len(results) > 0:
            print(f"\n🚀 System is working! Ready to run full evaluation with:")
            print(f"   python3 run_evaluations.py")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
