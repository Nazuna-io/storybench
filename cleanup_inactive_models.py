#!/usr/bin/env python3
"""
Clean up inactive model configurations to only keep the active one
"""
import asyncio
import os
import sys
sys.path.append('/home/todd/storybench/src')

from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup_inactive_models():
    print("🧹 Cleaning Up Inactive Model Configurations...")
    print("=" * 80)
    
    # Connect to database
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    database = client.storybench
    
    try:
        # Get all model configurations
        configs = await database.models.find({}).to_list(length=None)
        print(f"📊 Found {len(configs)} model configurations")
        
        active_configs = [c for c in configs if c.get("is_active", False)]
        inactive_configs = [c for c in configs if not c.get("is_active", False)]
        
        print(f"  Active: {len(active_configs)}")
        print(f"  Inactive: {len(inactive_configs)}")
        
        if len(active_configs) == 1:
            active_config = active_configs[0]
            print(f"\n✅ Active Configuration:")
            print(f"  ID: {active_config['_id']}")
            print(f"  Models: {len(active_config.get('models', []))}")
            for model in active_config.get('models', []):
                print(f"    - {model.get('name')} ({model.get('provider')}/{model.get('model_name')})")
        
        if inactive_configs:
            print(f"\n🗑️  Removing {len(inactive_configs)} inactive configurations...")
            
            # Delete inactive configurations
            inactive_ids = [c["_id"] for c in inactive_configs]
            result = await database.models.delete_many({"_id": {"$in": inactive_ids}})
            print(f"✅ Deleted {result.deleted_count} inactive model configurations")
            
            # Verify cleanup
            remaining_configs = await database.models.count_documents({})
            print(f"📊 Remaining configurations: {remaining_configs}")
            
        else:
            print("✅ No inactive configurations to clean up")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_inactive_models())
