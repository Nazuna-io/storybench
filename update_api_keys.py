#!/usr/bin/env python3
"""Update API keys from .env file with proper encryption."""

import sys
import os
import asyncio
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
from storybench.database.connection import init_database
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

async def update_api_keys():
    """Update API keys from .env file with proper encryption."""
    print("🔑 Starting API key updates...")
    
    try:
        db = await init_database()
        api_keys_collection = db['api_keys']
        
        # Get encryption key
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            print("❌ ENCRYPTION_KEY not found in environment variables")
            return False
            
        fernet = Fernet(encryption_key.encode())
        
        # API keys to update
        api_key_configs = [
            {'provider': 'openai', 'name': 'OpenAI API Key', 'env_key': 'OPENAI_API_KEY'},
            {'provider': 'anthropic', 'name': 'Anthropic API Key', 'env_key': 'ANTHROPIC_API_KEY'},
            {'provider': 'google', 'name': 'Google API Key', 'env_key': 'GOOGLE_API_KEY'}
        ]
        
        for config in api_key_configs:
            provider = config['provider']
            name = config['name']
            env_key = config['env_key']
            
            # Get API key from environment
            api_key = os.getenv(env_key)
            if not api_key:
                print(f"⚠️  {env_key} not found in environment variables, skipping {provider}")
                continue
            
            # Encrypt the API key
            encrypted_key = fernet.encrypt(api_key.encode()).decode()
            
            # Update or insert the API key
            filter_query = {'provider': provider}
            update_data = {
                '$set': {
                    'provider': provider,
                    'name': name,
                    'key': encrypted_key,
                    'is_active': True
                }
            }
            
            result = await api_keys_collection.update_one(
                filter_query, 
                update_data, 
                upsert=True
            )
            
            if result.upserted_id:
                print(f"✅ Created new API key for {provider}")
            elif result.modified_count > 0:
                print(f"✅ Updated existing API key for {provider}")
            else:
                print(f"ℹ️  API key for {provider} was already up to date")
        
        print("✅ API key updates complete!")
        return True
        
    except Exception as e:
        print(f"❌ API key update failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(update_api_keys())
