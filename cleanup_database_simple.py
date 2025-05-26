#!/usr/bin/env python3
"""Quick cleanup script for Storybench database."""

import sys
import os
import asyncio
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
from storybench.database.connection import init_database

# Load environment variables
load_dotenv()

async def cleanup_database():
    """Delete all evaluation data from the database."""
    print("🧹 Starting database cleanup...")
    
    try:
        db = await init_database()
        
        # Collections to clean up
        collections_to_cleanup = [
            'responses',
            'evaluations', 
            'response_llm_evaluations'
        ]
        
        total_deleted = 0
        
        for collection_name in collections_to_cleanup:
            collection = db[collection_name]
            
            # Count documents before deletion
            count_before = await collection.count_documents({})
            print(f"📊 {collection_name}: {count_before} documents found")
            
            if count_before > 0:
                # Delete all documents
                result = await collection.delete_many({})
                deleted_count = result.deleted_count
                total_deleted += deleted_count
                print(f"🗑️  {collection_name}: Deleted {deleted_count} documents")
            else:
                print(f"✅ {collection_name}: Already empty")
        
        print(f"✅ Database cleanup complete! Total deleted: {total_deleted} documents")
        return True
        
    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(cleanup_database())
