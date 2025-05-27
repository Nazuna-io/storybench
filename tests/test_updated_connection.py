#!/usr/bin/env python3
"""
Test the updated MongoDB connection string
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

async def test_connection():
    # Test with the new connection string
    new_uri = "mongodb+srv://toddthomas:Qr7wFKFKPKxpWJWe@storybench-cluster0.o0tp9zz.mongodb.net/storybench?retryWrites=true&w=majority"
    
    print("🔗 Testing new MongoDB connection...")
    print(f"URI: {new_uri[:60]}...")
    
    try:
        # Create client with proper connection pool settings
        client = AsyncIOMotorClient(
            new_uri,
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
