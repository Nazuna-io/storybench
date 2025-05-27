import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def check_db_connection():
    try:
        # Get MongoDB URI from environment or use default
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        
        # Create a new client and connect to the server
        client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        # List databases
        print("\nDatabases:")
        for db in client.list_database_names():
            print(f"- {db}")
            
        # Check storybench database
        if 'storybench' in client.list_database_names():
            db = client['storybench']
            print("\nCollections in storybench database:")
            for col in db.list_collection_names():
                print(f"- {col} (Count: {db[col].estimated_document_count()})")
        
        return True
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return False

if __name__ == "__main__":
    check_db_connection()
