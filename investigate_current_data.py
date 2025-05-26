#!/usr/bin/env python3
"""
Investigate current database state for ChatGPT evaluations and responses
"""
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

async def investigate_data():
    # Load environment variables
    load_dotenv(override=True)
    mongodb_uri = os.getenv("MONGODB_URI")
    
    client = AsyncIOMotorClient(mongodb_uri)
    database = client.storybench
    
    print("🔍 Investigating current database state...")
    print("=" * 80)
    
    # Check evaluations collection
    print("\n📊 EVALUATIONS COLLECTION:")
    evaluations = await database.evaluations.find({}).to_list(None)
    for eval_doc in evaluations:
        eval_id = str(eval_doc.get('_id'))
        model_names = eval_doc.get('model_names', [])
        status = eval_doc.get('status', 'unknown')
        created_at = eval_doc.get('created_at', 'unknown')
        print(f"  Evaluation {eval_id[:8]}...")
        print(f"    Models: {model_names}")
        print(f"    Status: {status}")
        print(f"    Created: {created_at}")
        print()
    
    # Check responses collection by model
    print("\n📝 RESPONSES BY MODEL:")
    pipeline = [
        {"$group": {
            "_id": "$model_name", 
            "count": {"$sum": 1},
            "evaluation_ids": {"$addToSet": "$evaluation_id"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    response_stats = await database.responses.aggregate(pipeline).to_list(None)
    for stat in response_stats:
        model_name = stat['_id']
        count = stat['count']
        eval_ids = [str(eid)[:8] + "..." for eid in stat['evaluation_ids']]
        print(f"  {model_name}: {count} responses")
        print(f"    Evaluation IDs: {eval_ids}")
        print()
    
    # Check response_llm_evaluations collection
    print("\n🎯 LLM EVALUATIONS:")
    llm_eval_pipeline = [
        {"$group": {
            "_id": "$response.model_name", 
            "count": {"$sum": 1},
            "avg_scores": {
                "$push": {
                    "visual_imagery": "$scores.visual_imagery",
                    "emotional_resonance": "$scores.emotional_resonance", 
                    "narrative_coherence": "$scores.narrative_coherence",
                    "character_development": "$scores.character_development"
                }
            }
        }},
        {"$sort": {"count": -1}}
    ]
    
    llm_evals = await database.response_llm_evaluations.aggregate(llm_eval_pipeline).to_list(None)
    for eval_stat in llm_evals:
        model_name = eval_stat['_id']
        count = eval_stat['count']
        print(f"  {model_name}: {count} LLM evaluations")
    
    print(f"\nTotal LLM evaluations: {await database.response_llm_evaluations.count_documents({})}")
    
    # Check for ChatGPT models specifically
    print("\n🤖 CHATGPT MODELS CHECK:")
    chatgpt_patterns = ["gpt-", "GPT-", "o1-", "o3-", "o4-", "chatgpt"]
    
    for pattern in chatgpt_patterns:
        responses = await database.responses.count_documents({"model_name": {"$regex": pattern, "$options": "i"}})
        evaluations = await database.response_llm_evaluations.count_documents({"response.model_name": {"$regex": pattern, "$options": "i"}})
        if responses > 0 or evaluations > 0:
            print(f"  Pattern '{pattern}': {responses} responses, {evaluations} evaluations")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(investigate_data())
