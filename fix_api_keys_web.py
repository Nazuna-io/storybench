#!/usr/bin/env python3
"""Fix API keys to use the correct encryption method and field names for web interface."""

import sys
import os
import asyncio
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
from storybench.database.connection import init_database
from storybench.utils.encryption import encryption_service

# Load environment variables
load_dotenv()

async def fix_api_keys():
    """Fix API keys to use the web interface's encryption method."""
    print("🔧 Fixing API keys for web interface compatibility...")
    
    try:
        db = await init_database()
        api_keys_collection = db['api_keys']
        
        # API keys from environment
        api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY'), 
            'google': os.getenv('GOOGLE_API_KEY')
        }
        
        for provider, api_key in api_keys.items():
            if not api_key:
                print(f"⚠️  No API key found for {provider}")
                continue
                
            # Encrypt using the web interface's method
            encrypted_key = encryption_service.encrypt(api_key)
            
            # Update the document with correct field
            result = await api_keys_collection.update_one(
                {'provider': provider},
                {
                    '$set': {
                        'encrypted_key': encrypted_key,
                        'provider': provider,
                        'is_active': True
                    }
                },
                upsert=True
            )
            
            if result.upserted_id:
                print(f"✅ Created new encrypted_key for {provider}")
            elif result.modified_count > 0:
                print(f"✅ Updated encrypted_key for {provider}")
            else:
                print(f"ℹ️  {provider} encrypted_key was already correct")
                
        print("✅ API key fixes complete!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix API keys: {e}")
        return False

async def verify_api_keys():
    """Verify the API keys can be decrypted properly."""
    print("\n🔍 Verifying API key fixes...")
    
    try:
        db = await init_database()
        api_keys_collection = db['api_keys']
        
        async for key_doc in api_keys_collection.find({}):
            provider = key_doc.get('provider')
            encrypted_key = key_doc.get('encrypted_key', '')
            
            if encrypted_key:
                try:
                    decrypted = encryption_service.decrypt(encrypted_key)
                    masked = encryption_service.mask_key(decrypted, 8)
                    print(f"✅ {provider}: {masked}")
                    print(f"   Full key: {decrypted}")  # Show full key for verification
                except Exception as e:
                    print(f"❌ {provider}: Failed to decrypt - {e}")
            else:
                print(f"⚠️  {provider}: No encrypted_key field")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        success1 = await fix_api_keys()
        success2 = await verify_api_keys()
        
        if success1 and success2:
            print("\n🎉 API key fixes completed successfully!")
        else:
            print("\n⚠️  Some issues were encountered during the fix.")
    
    asyncio.run(main())
