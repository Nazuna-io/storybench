#!/usr/bin/env python3
"""
Script to investigate evaluation issues - check responses, evaluations, and status.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from collections import defaultdict

async def investigate_evaluation_issues():
    """Investigate what went wrong with the evaluation."""
    
    # Get MongoDB connection
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ MONGODB_URI environment variable not found!")
        return
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_uri)
        db = client.storybench
        
        print("🔍 Investigating Evaluation Issues...")
        print("=" * 80)
        
        # Get the latest evaluation run
        evaluations_collection = db.evaluations
        latest_eval = await evaluations_collection.find_one(
            {"models": {"$regex": "gpt-", "$options": "i"}},
            sort=[("timestamp", -1)]
        )
        
        if not latest_eval:
            print("❌ No recent ChatGPT evaluation found!")
            return
        
        print(f"📊 Latest Evaluation Run:")
        print(f"  ID: {latest_eval['_id']}")
        print(f"  Models: {latest_eval['models']}")
        print(f"  Status: {latest_eval['status']}")
        print(f"  Total Tasks: {latest_eval['total_tasks']}")
        print(f"  Completed Tasks: {latest_eval['completed_tasks']}")
        print(f"  Started: {latest_eval['started_at']}")
        print(f"  Completed: {latest_eval['completed_at']}")
        print(f"  Current Model: {latest_eval.get('current_model')}")
        print(f"  Current Sequence: {latest_eval.get('current_sequence')}")
        print(f"  Current Run: {latest_eval.get('current_run')}")
        print(f"  Error: {latest_eval.get('error_message')}")
        
        # Check responses generated for this evaluation
        responses_collection = db.responses
        
        print(f"\n📝 Checking Generated Responses...")
        print("-" * 50)
        
        # Get all responses for the models in this evaluation
        model_responses = defaultdict(list)
        total_responses = 0
        
        for model in latest_eval['models']:
            responses = await responses_collection.find({
                "model_name": model,
                "timestamp": {"$gte": latest_eval['started_at']}
            }).to_list(None)
            
            model_responses[model] = responses
            total_responses += len(responses)
            
            print(f"  {model}: {len(responses)} responses")
            
            # Show sample responses
            for i, resp in enumerate(responses[:2]):  # Show first 2
                print(f"    - {resp.get('sequence')} Run {resp.get('run')}: {resp.get('response_text', '')[:100]}...")
        
        print(f"\n📊 Total Responses Generated: {total_responses}")
        
        # Check if LLM evaluations were created
        llm_evaluations_collection = db.llm_evaluations
        
        print(f"\n🧠 Checking LLM Evaluations...")
        print("-" * 50)
        
        # Get response IDs from this evaluation
        response_ids = []
        for model in latest_eval['models']:
            responses = await responses_collection.find({
                "model_name": model,
                "timestamp": {"$gte": latest_eval['started_at']}
            }).to_list(None)
            response_ids.extend([str(resp['_id']) for resp in responses])
        
        print(f"  Looking for evaluations of {len(response_ids)} response IDs...")
        
        # Find LLM evaluations for these responses
        llm_evals = await llm_evaluations_collection.find({
            "response_id": {"$in": response_ids}
        }).to_list(None)
        
        print(f"  Found {len(llm_evals)} LLM evaluations")
        
        if llm_evals:
            # Group by response_id
            eval_by_response = defaultdict(list)
            for eval_doc in llm_evals:
                eval_by_response[eval_doc['response_id']].append(eval_doc)
            
            print(f"  Evaluations cover {len(eval_by_response)} unique responses")
            
            # Show sample evaluations
            for i, (response_id, evals) in enumerate(list(eval_by_response.items())[:3]):
                print(f"    Response {response_id}: {len(evals)} evaluations")
                for eval_doc in evals[:1]:  # Show first eval
                    scores = eval_doc.get('scores', {})
                    print(f"      Scores: {scores}")
        else:
            print("  ❌ No LLM evaluations found for any responses!")
        
        # Check evaluation status progression
        print(f"\n📈 Status Analysis...")
        print("-" * 50)
        
        expected_tasks = len(latest_eval['models']) * 15 * 3  # 6 models × 15 prompts × 3 runs
        actual_responses = total_responses
        
        print(f"  Expected total tasks: {expected_tasks}")
        print(f"  Reported completed tasks: {latest_eval['completed_tasks']}")
        print(f"  Actual responses found: {actual_responses}")
        
        if actual_responses < expected_tasks:
            print(f"  ⚠️  Response generation incomplete: {actual_responses}/{expected_tasks}")
        
        if len(llm_evals) == 0:
            print(f"  ❌ LLM evaluation phase never ran!")
        elif len(llm_evals) < actual_responses:
            print(f"  ⚠️  LLM evaluation incomplete: {len(llm_evals)}/{actual_responses}")
        
        # Check for errors in logs or status
        if latest_eval['status'] == 'completed' and (actual_responses < expected_tasks or len(llm_evals) == 0):
            print(f"  ❌ Status incorrectly marked as 'completed'!")
        
        print(f"\n" + "=" * 80)
        print("🔍 Investigation Summary:")
        print(f"  1. Response Generation: {actual_responses}/{expected_tasks} ({actual_responses/expected_tasks*100:.1f}%)")
        print(f"  2. LLM Evaluation: {len(llm_evals)}/{actual_responses} responses evaluated")
        print(f"  3. Status Accuracy: {'❌ Incorrect' if latest_eval['status'] == 'completed' and (actual_responses < expected_tasks or len(llm_evals) == 0) else '✅ Correct'}")
        
    except Exception as e:
        print(f"❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(investigate_evaluation_issues())
