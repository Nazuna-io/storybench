#!/usr/bin/env python3
"""Check if local model data is being stored in database correctly."""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variable for database
os.environ.setdefault("MONGODB_URI", "mongodb+srv://todd:FyilOF4jed0bFUxO@storybench-cluster0.o0tp9zz.mongodb.net/?retryWrites=true&w=majority&appName=Storybench-cluster0")

from storybench.database.connection import init_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database_data():
    """Check what data is stored in the database."""
    print("=== Checking Database Data ===")
    
    # Initialize database connection
    database = await init_database()
    
    # Check evaluations collection
    print("\n1. Checking evaluations collection...")
    evaluations = await database.evaluations.find().to_list(length=10)
    print(f"Found {len(evaluations)} evaluations")
    
    for eval_doc in evaluations:
        print(f"  - {eval_doc.get('_id')}: {eval_doc.get('models', [])} ({eval_doc.get('status', 'unknown')})")
    
    # Check responses collection
    print("\n2. Checking responses collection...")
    responses = await database.responses.find().to_list(length=10)
    print(f"Found {len(responses)} responses")
    
    for response in responses:
        print(f"  - {response.get('_id')}: {response.get('model_name')} - {response.get('sequence')} - {response.get('prompt_name')}")
    
    # Check for local model responses specifically
    print("\n3. Checking for local model responses...")
    local_responses = await database.responses.find({"model_name": {"$regex": "local_"}}).to_list(length=10)
    print(f"Found {len(local_responses)} local model responses")
    
    for response in local_responses:
        print(f"  - {response.get('model_name')}: {response.get('sequence')} - {response.get('prompt_name')}")
        print(f"    Response: {response.get('response', '')[:100]}...")
    
    print("\n=== Database Check Complete ===")

if __name__ == "__main__":
    asyncio.run(check_database_data())
