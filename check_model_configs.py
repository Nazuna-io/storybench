#!/usr/bin/env python3
"""
Check model configurations in the database
"""
import asyncio
import os
import sys
sys.path.append('/home/todd/storybench/src')

from motor.motor_asyncio import AsyncIOMotorClient
from storybench.database.repositories.model_repo import ModelRepository

async def check_model_configs():
    print("🔍 Checking Model Configurations...")
    print("=" * 80)
    
    # Connect to database
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    database = client.storybench
    
    try:
        model_repo = ModelRepository(database)
        
        # Get all model configurations
        configs = await model_repo.find_many({})
        print(f"📊 Found {len(configs)} model configurations")
        
        for i, config in enumerate(configs):
            print(f"\n📋 Configuration {i+1}:")
            print(f"  ID: {config.id}")
            print(f"  Active: {config.is_active}")
            print(f"  Created: {config.created_at}")
            print(f"  Models: {len(config.models)}")
            
            for j, model in enumerate(config.models):
                print(f"    {j+1}. {model.name} ({model.provider}/{model.model_name})")
        
        # Get active configuration
        active_config = await model_repo.find_one({"is_active": True})
        if active_config:
            print(f"\n✅ Active Configuration:")
            print(f"  ID: {active_config.id}")
            print(f"  Models: {len(active_config.models)}")
            for model in active_config.models:
                print(f"    - {model.name} ({model.provider}/{model.model_name})")
        else:
            print(f"\n❌ No active configuration found!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_model_configs())
