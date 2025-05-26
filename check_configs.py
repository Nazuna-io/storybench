#!/usr/bin/env python3

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check_config_collections():
    """Check prompts and criteria collections specifically."""
    
    mongodb_uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.storybench
    
    try:
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Check prompts collection
        print("\n" + "="*50)
        print("📝 PROMPTS COLLECTION")
        print("="*50)
        
        prompts_count = await db.prompts.count_documents({})
        print(f"Total prompts configs: {prompts_count}")
        
        if prompts_count > 0:
            async for prompt_doc in db.prompts.find():
                print(f"\n📝 Prompts Config:")
                print(f"   Config Hash: {prompt_doc.get('config_hash', 'N/A')}")
                print(f"   Version: {prompt_doc.get('version', 'N/A')}")
                print(f"   Active: {prompt_doc.get('is_active', 'N/A')}")
                print(f"   Sequences: {list(prompt_doc.get('sequences', {}).keys())}")
        
        # Check evaluation criteria collection  
        print("\n" + "="*50)
        print("🎯 EVALUATION_CRITERIA COLLECTION")
        print("="*50)
        
        criteria_count = await db.evaluation_criteria.count_documents({})
        print(f"Total criteria configs: {criteria_count}")
        
        if criteria_count > 0:
            async for criteria_doc in db.evaluation_criteria.find():
                print(f"\n🎯 Criteria Config:")
                print(f"   Config Hash: {criteria_doc.get('config_hash', 'N/A')}")
                print(f"   Version: {criteria_doc.get('version', 'N/A')}")
                print(f"   Active: {criteria_doc.get('is_active', 'N/A')}")
                print(f"   Criteria: {list(criteria_doc.get('criteria', {}).keys())}")
        
        # Check for sample data from existing evaluations
        print("\n" + "="*50)
        print("🔍 EXISTING EVALUATION DATA ANALYSIS")
        print("="*50)
        
        # Get sample response to see what sequences/criteria were used
        sample_response = await db.responses.find_one()
        if sample_response:
            print(f"Sample response sequence: {sample_response.get('sequence', 'N/A')}")
            print(f"Sample response prompt: {sample_response.get('prompt_name', 'N/A')}")
        
        # Get sample LLM evaluation to see what criteria were used
        sample_eval = await db.response_llm_evaluations.find_one()
        if sample_eval:
            criteria_results = sample_eval.get('criteria_results', [])
            if criteria_results:
                criteria_names = [cr.get('criterion_name') for cr in criteria_results]
                print(f"Sample evaluation criteria: {criteria_names}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_config_collections())
