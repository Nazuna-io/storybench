#!/usr/bin/env python3
"""
Test MongoDB connection using exact .env credentials
"""
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

async def test_connection():
    # Load environment variables from .env file with override
    load_dotenv(override=True)
    
    mongodb_uri = os.getenv("MONGODB_URI")
    
    if not mongodb_uri:
        print("❌ No MONGODB_URI found in environment variables")
        return False
    
    print("🔗 Testing MongoDB connection from updated .env file...")
    print(f"URI: {mongodb_uri[:80]}...")
    
    try:
        # Create client with proper connection pool settings
        client = AsyncIOMotorClient(
            mongodb_uri,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=45000,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
        )
        
        print("✅ Client created, testing connection...")
        
        # Test the connection with ping
        result = await client.admin.command('ping')
        print(f"✅ Ping successful: {result}")
        
        # Test database access
        database = client.storybench
        collections = await database.list_collection_names()
        print(f"✅ Database access successful. Collections: {collections}")
        
        # Test a simple query
        if 'responses' in collections:
            count = await database.responses.count_documents({})
            print(f"✅ Sample query successful. Response count: {count}")
        
        if 'evaluations' in collections:
            eval_count = await database.evaluations.count_documents({})
            print(f"✅ Evaluation count: {eval_count}")
        
        await client.close()
        print("✅ Connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    exit(0 if result else 1)
