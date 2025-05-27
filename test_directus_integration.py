#!/usr/bin/env python3
"""Test script to verify Directus integration."""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.clients.directus_client import DirectusClient, DirectusClientError


async def test_directus_connection():
    """Test basic Directus connection and data retrieval."""
    print("Testing Directus CMS Integration...")
    print("=" * 50)
    
    try:
        # Initialize client
        client = DirectusClient()
        print(f"Directus URL: {client.base_url}")
        print(f"Timeout: {client.timeout}s")
        print()
        
        # Test connection
        print("Testing connection...")
        is_connected = await client.test_connection()
        print(f"Connection successful: {is_connected}")
        
        if not is_connected:
            print("❌ Unable to connect to Directus")
            return False
        
        print("✅ Connected to Directus successfully")
        print()
        
        # List available versions
        print("Fetching available versions...")
        versions = await client.list_published_versions()
        print(f"Found {len(versions)} published versions:")
        
        for version in versions:
            print(f"  - Version {version.version_number}: {version.version_name}")
            if version.description:
                print(f"    Description: {version.description}")
            print(f"    Created: {version.date_created}")
        print()
        
        # Fetch latest version
        print("Fetching latest published version...")
        prompts = await client.fetch_prompts()
        
        if prompts:
            print(f"✅ Successfully fetched version {prompts.version}")
            print(f"Directus ID: {prompts.directus_id}")
            print(f"Sequences found: {len(prompts.sequences)}")
            
            for seq_name, seq_prompts in prompts.sequences.items():
                print(f"  - {seq_name}: {len(seq_prompts)} prompts")
                for prompt in seq_prompts[:2]:  # Show first 2 prompts
                    print(f"    * {prompt.name}: {prompt.text[:50]}...")
                if len(seq_prompts) > 2:
                    print(f"    ... and {len(seq_prompts) - 2} more")
            
            print()
            print("✅ Directus integration test completed successfully!")
            return True
        else:
            print("❌ No published prompts found")
            return False
            
    except DirectusClientError as e:
        print(f"❌ Directus error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_directus_connection())
    sys.exit(0 if success else 1)
