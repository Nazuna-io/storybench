#!/usr/bin/env python3
"""
Script to update evaluation criteria with more stringent standards.
"""

import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from src.storybench.database.migrations.config_migration import ConfigMigrationService

async def main():
    # Load environment variables
    load_dotenv()
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ MONGODB_URI environment variable not set")
        return
    
    print("🔗 Connecting to database...")
    client = AsyncIOMotorClient(mongodb_uri)
    database = client["storybench"]
    
    try:
        # Initialize migration service
        migration_service = ConfigMigrationService(database)
        
        print("📝 Updating evaluation criteria with stringent standards...")
        
        # Migrate the updated criteria
        criteria_config = await migration_service.migrate_evaluation_criteria_config()
        
        print(f"✅ Successfully updated evaluation criteria!")
        print(f"   Version: {criteria_config.version}")
        print(f"   Hash: {criteria_config.config_hash}")
        print(f"   Criteria: {list(criteria_config.criteria.keys())}")
        
        # Show sample of updated criteria
        print(f"\n📋 Sample updated criteria:")
        for name, criterion in list(criteria_config.criteria.items())[:2]:
            print(f"\n   {name}:")
            print(f"   {criterion.description[:100]}...")
        
        print(f"\n🎯 New standards emphasize:")
        print(f"   • Realistic scoring (most responses should be 2-3)")
        print(f"   • Score 4+ only for exceptional quality")
        print(f"   • Score 5 reserved for masterwork-level writing")
        print(f"   • Comparison against professional published fiction")
        
    except Exception as e:
        print(f"❌ Error updating criteria: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()
        print(f"\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())
