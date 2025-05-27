#!/usr/bin/env python3
"""
Debug script to test API endpoints directly.
"""
import asyncio
import sys
import os
sys.path.append('/home/todd/storybench/src')

from storybench.database.connection import init_database, get_database
from storybench.database.services.evaluation_runner import DatabaseEvaluationRunner

async def test_api_methods():
    try:
        print("Initializing database...")
        database = await init_database()
        print("Database initialized successfully")
        
        print("Creating evaluation runner...")
        runner = DatabaseEvaluationRunner(database)
        print("Evaluation runner created")
        
        print("Testing find_running_evaluations...")
        running = await runner.find_running_evaluations()
        print(f"Running evaluations: {len(running)}")
        
        print("Testing find_incomplete_evaluations...")
        incomplete = await runner.find_incomplete_evaluations()
        print(f"Incomplete evaluations: {len(incomplete)}")
        
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_methods())
