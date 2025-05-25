#!/usr/bin/env python3
"""
Simple script to update evaluation criteria with more stringent standards.
"""

import asyncio
import os
import yaml
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from src.storybench.database.repositories.criteria_repo import CriteriaRepository
from src.storybench.database.models import EvaluationCriteria, EvaluationCriterionItem

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
        criteria_repo = CriteriaRepository(database)
        
        print("📝 Loading updated evaluation criteria...")
        
        # Load the updated criteria from YAML
        with open("config/evaluation_criteria.yaml", "r") as f:
            config_data = yaml.safe_load(f)
        
        # Calculate hash
        config_hash = hashlib.md5(yaml.dump(config_data, sort_keys=True).encode()).hexdigest()
        
        # Check if this config already exists
        existing_config = await criteria_repo.find_by_config_hash(config_hash)
        if existing_config:
            print(f"✅ Criteria with this hash already exists and is active")
            return existing_config
        
        # Convert to our EvaluationCriteria structure
        criteria_items = {}
        for criterion_name, criterion_data in config_data.get("criteria", {}).items():
            criterion_item = EvaluationCriterionItem(
                name=criterion_data["name"],
                description=criterion_data["description"],
                scale=criterion_data["scale"]
            )
            criteria_items[criterion_name] = criterion_item
        
        # Deactivate existing criteria
        await criteria_repo.deactivate_all()
        
        # Get next version number
        all_configs = await criteria_repo.find_many({})
        if all_configs:
            max_version = max(c.version for c in all_configs if hasattr(c, 'version'))
            version = max_version + 1
        else:
            version = 1
        
        # Create new criteria document
        criteria_doc = EvaluationCriteria(
            config_hash=config_hash,
            criteria=criteria_items,
            is_active=True,
            version=version
        )
        
        created_doc = await criteria_repo.create(criteria_doc)
        
        print(f"✅ Successfully updated evaluation criteria!")
        print(f"   Version: {created_doc.version}")
        print(f"   Hash: {created_doc.config_hash}")
        print(f"   Criteria: {list(created_doc.criteria.keys())}")
        
        # Show sample of updated criteria
        print(f"\n📋 Sample updated criteria:")
        for name, criterion in list(created_doc.criteria.items())[:2]:
            print(f"\n   {name}:")
            print(f"   {criterion.description}")
        
        print(f"\n🎯 New standards emphasize:")
        print(f"   • Realistic scoring (most responses should be 2-3)")
        print(f"   • Score 4+ only for exceptional quality")
        print(f"   • Score 5 reserved for masterwork-level writing")
        print(f"   • Comparison against professional published fiction")
        
        return created_doc
        
    except Exception as e:
        print(f"❌ Error updating criteria: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()
        print(f"\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())
