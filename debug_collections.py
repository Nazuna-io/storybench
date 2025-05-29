#!/usr/bin/env python3
"""
Debug MongoDB Collections and Find Missing Evaluations
"""

import asyncio
import os
from datetime import datetime

async def debug_collections():
    """Debug collections and find the evaluation data."""
    
    try:
        import sys
        sys.path.insert(0, '/home/todd/storybench/src')
        
        from dotenv import load_dotenv
        load_dotenv()
        
        from storybench.database.connection import init_database
        
        print("🔗 Connecting to MongoDB...")
        db = await init_database()
        
        print("\n📋 Available Collections:")
        collections = await db.list_collection_names()
        for collection in sorted(collections):
            count = await db[collection].count_documents({})
            print(f"   • {collection}: {count} documents")
        
        # Check response_llm_evaluations specifically
        if 'response_llm_evaluations' in collections:
            print("\n🎯 Checking response_llm_evaluations collection:")
            eval_count = await db['response_llm_evaluations'].count_documents({})
            print(f"   Total evaluations: {eval_count}")
            
            if eval_count > 0:
                # Get sample evaluation
                sample = await db['response_llm_evaluations'].find_one()
                print(f"   Sample evaluation ID: {sample['_id']}")
                print(f"   Response ID: {sample.get('response_id', 'N/A')}")
                print(f"   Test batch: {sample.get('test_batch', 'N/A')}")
                print(f"   Has evaluation text: {'evaluation_text' in sample}")
                
                # Get latest batch
                latest = await db['response_llm_evaluations'].find().sort('created_at', -1).limit(1).to_list(1)
                if latest:
                    batch_id = latest[0].get('test_batch')
                    batch_count = await db['response_llm_evaluations'].count_documents({'test_batch': batch_id})
                    print(f"   Latest batch '{batch_id}': {batch_count} evaluations")
        
        # Check responses collection 
        if 'responses' in collections:
            print("\n📝 Checking responses collection:")
            response_count = await db['responses'].count_documents({})
            print(f"   Total responses: {response_count}")
            
            if response_count > 0:
                # Get sample response
                sample = await db['responses'].find_one()
                print(f"   Sample response ID: {sample['_id']}")
                print(f"   Model: {sample.get('model_name', 'N/A')}")
                print(f"   Test batch: {sample.get('test_batch', 'N/A')}")
                
                # Get latest batch
                latest = await db['responses'].find().sort('created_at', -1).limit(1).to_list(1)
                if latest:
                    batch_id = latest[0].get('test_batch')
                    batch_count = await db['responses'].count_documents({'test_batch': batch_id})
                    print(f"   Latest batch '{batch_id}': {batch_count} responses")
        
        # Check if there's a mismatch
        print("\n🔍 Cross-Reference Check:")
        
        if 'responses' in collections and 'response_llm_evaluations' in collections:
            # Get latest response batch
            latest_response = await db['responses'].find().sort('created_at', -1).limit(1).to_list(1)
            if latest_response:
                latest_batch = latest_response[0].get('test_batch')
                
                response_count = await db['responses'].count_documents({'test_batch': latest_batch})
                eval_count = await db['response_llm_evaluations'].count_documents({'test_batch': latest_batch})
                
                print(f"   Latest batch '{latest_batch}':")
                print(f"   - Responses: {response_count}")
                print(f"   - Evaluations: {eval_count}")
                
                if response_count > 0 and eval_count == 0:
                    print(f"   🚨 CRITICAL BUG CONFIRMED: {response_count} responses but 0 evaluations!")
                elif response_count == eval_count:
                    print(f"   ✅ Data looks consistent")
                else:
                    print(f"   ⚠️  Mismatch: {response_count} responses vs {eval_count} evaluations")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_collections())
