#!/usr/bin/env python3
"""Check the current status of evaluations in the database."""

import sys
import os
import asyncio
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import DatabaseConnection
from storybench.config.settings import load_env_vars

async def check_evaluation_status():
    """Check the current evaluation status."""
    try:
        # Load environment variables
        load_env_vars()
        
        # Get MongoDB URI from environment
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            print("❌ No MONGODB_URI found in environment")
            return
            
        print("🔍 Checking evaluation status...")
        
        # Connect to database
        db_conn = DatabaseConnection()
        await db_conn.connect(mongodb_uri)
        
        # Check for evaluations
        evaluations = await db_conn.db.evaluations.find({}).to_list(length=None)
        print(f"\n📊 Total evaluations in database: {len(evaluations)}")
        
        if evaluations:
            print("\n📋 Evaluation Details:")
            for i, eval_doc in enumerate(evaluations, 1):
                print(f"\n{i}. Evaluation ID: {eval_doc['_id']}")
                print(f"   Status: {eval_doc.get('status', 'unknown')}")
                print(f"   Models: {eval_doc.get('models', [])}")
                print(f"   Progress: {eval_doc.get('completed_tasks', 0)}/{eval_doc.get('total_tasks', 0)}")
                print(f"   Timestamp: {eval_doc.get('timestamp', 'unknown')}")
                
                # Check if it's currently running
                if eval_doc.get('status') == 'in_progress':
                    print(f"   ⚠️  ACTIVE EVALUATION DETECTED")
        else:
            print("\n✅ No evaluations found in database")
        
        # Check for recent responses
        responses = await db_conn.db.responses.find({}).sort('completed_at', -1).limit(10).to_list(length=None)
        print(f"\n📝 Recent responses: {len(responses)}")
        
        if responses:
            print("\n🔍 Latest responses:")
            for i, resp in enumerate(responses[:5], 1):
                completed_at = resp.get('completed_at', 'unknown')
                if isinstance(completed_at, datetime):
                    completed_at = completed_at.strftime('%Y-%m-%d %H:%M:%S')
                print(f"   {i}. Model: {resp.get('model_name', 'unknown')}")
                print(f"      Sequence: {resp.get('sequence', 'unknown')}")
                print(f"      Completed: {completed_at}")
        
        # Check for LLM evaluations  
        llm_evals = await db_conn.db.response_llm_evaluations.find({}).limit(5).to_list(length=None)
        print(f"\n🧠 LLM evaluations: {len(llm_evals)} (showing up to 5)")
        
        await db_conn.close()
        print("\n✅ Status check complete")
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_evaluation_status())
