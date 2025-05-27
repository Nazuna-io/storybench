#!/usr/bin/env python3
"""
Script to check what data remains in the database after cleanup.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check_remaining_data():
    """Check what data remains in the database."""
    
    # Get MongoDB connection
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ MONGODB_URI environment variable not found!")
        return
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_uri)
        db = client.storybench
        
        print("🔍 Checking remaining data in database...")
        print("=" * 60)
        
        # Check all collections that might contain model data
        collections_to_check = [
            "responses",
            "evaluations", 
            "evaluation_runs",
            "models",
            "prompts"
        ]
        
        for collection_name in collections_to_check:
            collection = db[collection_name]
            count = await collection.count_documents({})
            print(f"📊 {collection_name}: {count} documents")
            
            if count > 0 and count < 20:  # Show details for small collections
                docs = await collection.find({}).to_list(None)
                for doc in docs:
                    if collection_name == "responses":
                        print(f"  - Response: {doc.get('model_name')} | {doc.get('sequence')} | Run {doc.get('run')}")
                    elif collection_name == "evaluations":
                        print(f"  - Evaluation: {doc.get('_id')} | Response: {doc.get('response_id')}")
                    elif collection_name == "evaluation_runs":
                        print(f"  - Run: {doc.get('_id')} | Models: {doc.get('models', [])}")
                    elif collection_name == "models":
                        print(f"  - Model: {doc.get('name')} | Type: {doc.get('type')}")
                    elif collection_name == "prompts":
                        print(f"  - Prompts: {doc.get('_id')} | Active: {doc.get('is_active')}")
        
        # Check for any documents that might still reference ChatGPT
        print(f"\n🔍 Searching for any remaining ChatGPT references...")
        
        chatgpt_patterns = ["chatgpt", "gpt-", "GPT-", "o1-", "o3-", "o4-"]
        
        for collection_name in collections_to_check:
            collection = db[collection_name]
            for pattern in chatgpt_patterns:
                # Search in all text fields
                docs = await collection.find({
                    "$or": [
                        {"model_name": {"$regex": pattern, "$options": "i"}},
                        {"name": {"$regex": pattern, "$options": "i"}},
                        {"models": {"$regex": pattern, "$options": "i"}},
                    ]
                }).to_list(None)
                
                if docs:
                    print(f"  ⚠️  Found {len(docs)} documents in {collection_name} matching '{pattern}'")
                    for doc in docs[:3]:  # Show first 3
                        print(f"    - {doc.get('_id')}: {doc}")
        
        print(f"\n" + "=" * 60)
        print("✅ Database check complete!")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(check_remaining_data())
