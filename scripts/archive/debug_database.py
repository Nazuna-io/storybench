#!/usr/bin/env python3

"""Debug script to check database contents."""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def check_database():
    """Check what's in the database collections."""
    
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ MONGODB_URI not found in environment")
        return
    
    print(f"🔌 Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.storybench
    
    try:
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"\n📂 Available collections: {collections}")
        
        # Check evaluations collection
        print("\n" + "="*50)
        print("📊 EVALUATIONS COLLECTION")
        print("="*50)
        
        evaluation_count = await db.evaluations.count_documents({})
        print(f"Total evaluations: {evaluation_count}")
        
        if evaluation_count > 0:
            # Get all evaluations
            async for eval_doc in db.evaluations.find():
                print(f"\n📋 Evaluation ID: {eval_doc['_id']}")
                print(f"   Config Hash: {eval_doc.get('config_hash', 'N/A')}")
                print(f"   Status: {eval_doc.get('status', 'N/A')}")
                print(f"   Models: {eval_doc.get('models', [])}")
                print(f"   Total Tasks: {eval_doc.get('total_tasks', 0)}")
                print(f"   Completed Tasks: {eval_doc.get('completed_tasks', 0)}")
                print(f"   Started: {eval_doc.get('started_at', 'N/A')}")
                print(f"   Completed: {eval_doc.get('completed_at', 'N/A')}")
        
        # Check responses collection
        print("\n" + "="*50)
        print("🗨️ RESPONSES COLLECTION")
        print("="*50)
        
        response_count = await db.responses.count_documents({})
        print(f"Total responses: {response_count}")
        
        if response_count > 0:
            # Get sample responses
            sample_responses = await db.responses.find().limit(3).to_list(3)
            for i, resp in enumerate(sample_responses):
                print(f"\n📝 Sample Response {i+1}:")
                print(f"   Evaluation ID: {resp.get('evaluation_id', 'N/A')}")
                print(f"   Model: {resp.get('model_name', 'N/A')}")
                print(f"   Sequence: {resp.get('sequence', 'N/A')}")
                print(f"   Run: {resp.get('run', 'N/A')}")
                print(f"   Prompt: {resp.get('prompt_name', 'N/A')}")
                print(f"   Response Length: {len(resp.get('response', ''))}")
        
        # Check evaluation_scores collection
        print("\n" + "="*50)
        print("🎯 EVALUATION_SCORES COLLECTION")
        print("="*50)
        
        scores_count = await db.evaluation_scores.count_documents({})
        print(f"Total evaluation scores: {scores_count}")
        
        if scores_count > 0:
            # Get sample scores
            sample_scores = await db.evaluation_scores.find().limit(3).to_list(3)
            for i, score in enumerate(sample_scores):
                print(f"\n📊 Sample Score {i+1}:")
                print(f"   Evaluation ID: {score.get('evaluation_id', 'N/A')}")
                print(f"   Model: {score.get('model_name', 'N/A')}")
                print(f"   Sequence: {score.get('sequence', 'N/A')}")
                print(f"   Overall Score: {score.get('overall_score', 'N/A')}")
                print(f"   Detailed Scores: {score.get('detailed_scores', {})}")
        
        # Check response_llm_evaluations collection
        print("\n" + "="*50)
        print("🔍 RESPONSE_LLM_EVALUATIONS COLLECTION")
        print("="*50)
        
        llm_eval_count = await db.response_llm_evaluations.count_documents({})
        print(f"Total LLM evaluations: {llm_eval_count}")
        
        if llm_eval_count > 0:
            # Get sample LLM evaluations
            sample_llm_evals = await db.response_llm_evaluations.find().limit(3).to_list(3)
            for i, eval_item in enumerate(sample_llm_evals):
                print(f"\n🤖 Sample LLM Evaluation {i+1}:")
                print(f"   Response ID: {eval_item.get('response_id', 'N/A')}")
                print(f"   Evaluating LLM: {eval_item.get('evaluating_llm_model', 'N/A')}")
                print(f"   Criteria Results: {len(eval_item.get('criteria_results', []))}")
                if eval_item.get('criteria_results'):
                    for criterion in eval_item['criteria_results'][:2]:  # Show first 2 criteria
                        print(f"     - {criterion.get('criterion_name', 'N/A')}: {criterion.get('score', 'N/A')}")
        
        # Check models configuration
        print("\n" + "="*50)
        print("🔧 MODELS CONFIGURATION")
        print("="*50)
        
        models_count = await db.models.count_documents({})
        print(f"Total model configs: {models_count}")
        
        if models_count > 0:
            async for model_config in db.models.find():
                print(f"\n⚙️ Model Config:")
                print(f"   Config Hash: {model_config.get('config_hash', 'N/A')}")
                print(f"   Version: {model_config.get('version', 'N/A')}")
                print(f"   Active: {model_config.get('is_active', 'N/A')}")
                print(f"   Global Settings: {model_config.get('global_settings', {})}")
                print(f"   Models: {[m.get('name', 'N/A') for m in model_config.get('models', [])]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(check_database())
