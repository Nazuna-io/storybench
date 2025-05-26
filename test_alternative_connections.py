#!/usr/bin/env python3
"""
Test alternative MongoDB connection strings
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

async def test_connection(uri_name, uri):
    print(f"\n🔗 Testing {uri_name}...")
    print(f"URI: {uri[:50]}...")
    
    try:
        # Create client with proper connection pool settings
        client = AsyncIOMotorClient(
            uri,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=45000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
        
        print("✅ Client created, testing connection...")
        
        # Test the connection with ping
        result = await client.admin.command('ping')
        print(f"✅ Ping successful: {result}")
        
        # Test database access
        database = client.storybench
        collections = await database.list_collection_names()
        print(f"✅ Database access successful. Collections: {collections}")
        
        await client.close()
        print(f"✅ {uri_name} connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ {uri_name} failed: {type(e).__name__}: {e}")
        return False

async def main():
    # Test different connection strings
    connections = [
        ("Atlas SRV", "mongodb+srv://toddthomas:Qr7wFKFKPKxpWJWe@cluster0.qjgwj.mongodb.net/storybench?retryWrites=true&w=majority"),
        ("Atlas Direct", "mongodb://toddthomas:Qr7wFKFKPKxpWJWe@cluster0-shard-00-00.qjgwj.mongodb.net:27017,cluster0-shard-00-01.qjgwj.mongodb.net:27017,cluster0-shard-00-02.qjgwj.mongodb.net:27017/storybench?ssl=true&replicaSet=atlas-123abc-shard-0&authSource=admin&retryWrites=true&w=majority"),
        ("Alternative Atlas", "mongodb+srv://toddthomas:Qr7wFKFKPKxpWJWe@cluster0.mongodb.net/storybench?retryWrites=true&w=majority"),
    ]
    
    successful_connections = []
    
    for name, uri in connections:
        if await test_connection(name, uri):
            successful_connections.append((name, uri))
    
    print(f"\n📊 Summary:")
    print(f"Successful connections: {len(successful_connections)}")
    for name, uri in successful_connections:
        print(f"✅ {name}: {uri[:50]}...")
    
    if successful_connections:
        print(f"\n🎯 Recommended connection: {successful_connections[0][1]}")
        return successful_connections[0][1]
    else:
        print("\n❌ No successful connections found")
        return None

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
